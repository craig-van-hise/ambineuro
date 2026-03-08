import torch
import numpy as np
import safpy
import logging

# Hypothetical import for the A2B neural model and Wigner-D rotation
from a2b_model import A2BModel 
from spatial_math import WignerDRotation

class EngineState:
    NEURAL = "A2B"
    SAF_MAGLS = "SAF_MagLS"
    SAF_TA = "SAF_TA"
    SAF_LS = "SAF_LS"
    SAF_SPR = "SAF_SPR"

class DecoderGraph:
    def __init__(self, ambisonic_order: int, sample_rate: int = 48000, device: str = 'mps'):
        """
        Initializes the dual-engine routing matrix.
        """
        self.order = ambisonic_order
        self.num_channels = (self.order + 1) ** 2  # e.g., 25 channels for 4th order [cite: 20]
        self.sample_rate = sample_rate
        self.device = torch.device(device) # Targets Apple Silicon MPS [cite: 190]
        
        # 1. Initialize Neural Path (A2B)
        self.a2b_model = A2BModel(order=self.order).to(self.device)
        self.a2b_model.eval() # Set to inference mode
        
        # 2. Initialize Linear Path (SAF)
        # safpy typically requires initializing a binaural renderer instance
        self.saf_renderer = safpy.binaural.BinauralRenderer(
            order=self.order, 
            fs=self.sample_rate
        )
        
        # 3. Initialize GPU Spatial Rotation Engine
        self.rotator = WignerDRotation(order=self.order).to(self.device)
        
        # Default State
        self.current_state = EngineState.NEURAL
        self.hrtf_loaded = False
        
        logging.info(f"DecoderGraph initialized on {self.device}. State: {self.current_state}")

    def set_decoder_state(self, new_state: str):
        """Hot-swaps the active decoding engine."""
        valid_states = [getattr(EngineState, attr) for attr in dir(EngineState) if not attr.startswith("__")]
        if new_state in valid_states:
            self.current_state = new_state
            logging.info(f"Switched decoder state to: {self.current_state}")
        else:
            logging.error(f"Invalid state requested: {new_state}")

    def load_custom_hrtf(self, sofa_file_path: str):
        """Loads a custom .sofa file into the SAF renderer via the frontend dropzone."""
        try:
            # SAF natively handles SOFA file parsing and HRIR interpolation
            self.saf_renderer.load_sofa(sofa_file_path)
            self.hrtf_loaded = True
            logging.info(f"Successfully loaded custom HRTF: {sofa_file_path}")
        except Exception as e:
            logging.error(f"Failed to load SOFA file: {e}")

    def _adapt_channels(self, audio_tensor: torch.Tensor) -> torch.Tensor:
        """
        Adapts the input tensor to the expected channel count via zero-padding or truncation[cite: 114, 119].
        Input shape: (Batch, Channels, Time) [cite: 36, 38]
        """
        current_channels = audio_tensor.shape[1]
        
        if current_channels < self.num_channels:
            # Zero-pad higher order channels (simulates up-sampling) [cite: 114, 115, 116]
            padding = torch.zeros(
                (audio_tensor.shape[0], self.num_channels - current_channels, audio_tensor.shape[2]), 
                device=self.device
            )
            return torch.cat((audio_tensor, padding), dim=1)
        elif current_channels > self.num_channels:
            # Truncate to the maximum supported channels (loss of spatial detail) [cite: 119, 120]
            return audio_tensor[:, :self.num_channels, :]
        return audio_tensor

    @torch.no_grad()
    def process_block(self, audio_block: np.ndarray, yaw: float, pitch: float, roll: float) -> np.ndarray:
        """
        The main high-priority callback function. 
        Takes an Ambisonic numpy array, rotates it, routes it, and returns a stereo numpy array.
        """
        # 1. Transfer to GPU and adapt channels
        # audio_block expected shape: (Channels, Samples) -> Convert to (Batch, Channels, Time)
        tensor_in = torch.from_numpy(audio_block).unsqueeze(0).to(self.device, dtype=torch.float32)
        tensor_adapted = self._adapt_channels(tensor_in)
        
        # 2. Apply Wigner-D Matrix Rotation for head tracking [cite: 91, 92]
        # Calculates R(alpha, beta, gamma) * s_input [cite: 93, 94]
        tensor_rotated = self.rotator(tensor_adapted, yaw, pitch, roll) 
        
        # 3. The Routing Matrix
        if self.current_state == EngineState.NEURAL:
            # --- PATH A: A2B Neural Inference ---
            # Stays entirely on the MPS device for low latency 
            stereo_tensor = self.a2b_model(tensor_rotated)
            
            # Pull back to CPU for the hardware audio buffer
            return stereo_tensor.squeeze(0).cpu().numpy()
            
        else:
            # --- PATH B: SAF Linear Decoding ---
            # SAF is a C/C++ library, so we must pull the rotated signal back to CPU/Numpy
            rotated_cpu_array = tensor_rotated.squeeze(0).cpu().numpy()
            
            # Map the string state to the specific SAF decoding enum/method
            saf_method = self.current_state.split('_')[1] # Extracts "MagLS", "TA", etc.
            
            # Perform traditional DSP binaural rendering
            stereo_array = self.saf_renderer.apply(
                rotated_cpu_array, 
                method=saf_method
            )
            
            return stereo_array