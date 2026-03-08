import torch
import numpy as np
import safpy
import logging

# Mock versions implemented previously
from a2b_model import A2BModel 
from spatial_math import WignerDRotation

class EngineState:
    NEURAL = 'A2B'
    SAF_MAGLS = 'SAF-MagLS'
    SAF_TA = 'SAF-TA'
    SAF_LS = 'SAF-LS'
    SAF_SPR = 'SAF-SPR'

class DecoderGraph:
    def __init__(self, ambisonic_order=4, sample_rate=48000, device='cpu'):
        self.order = ambisonic_order
        self.sample_rate = sample_rate
        self.device = device
        self.num_channels = (self.order + 1) ** 2
        
        # 1. Initialize Neural Path (A2B)
        self.a2b_model = A2BModel(order=self.order).to(self.device)
        self.rotation_engine = WignerDRotation(order=self.order).to(self.device)
        
        # 2. Initialize Linear Path (SAF)
        self.saf_renderer = safpy.binaural.BinauralRenderer(
            order=self.order, 
            fs=self.sample_rate
        )
        
        self.current_state = EngineState.NEURAL
        logging.info(f"DecoderGraph initialized on {self.device}. State: {self.current_state}")

    def set_decoder_state(self, new_state: str):
        """Hot-swaps the active decoding engine."""
        valid_states = [getattr(EngineState, attr) for attr in dir(EngineState) if not attr.startswith("__")]
        if new_state in valid_states:
            self.current_state = new_state
            logging.info(f"Switched decoder state to: {self.current_state}")
        else:
            logging.error(f"Invalid state requested: {new_state}")

    def load_custom_hrtf(self, sofa_path: str):
        """Updates the SAF renderer with custom HRTF data."""
        logging.info(f"Loading custom SOFA into SAF: {sofa_path}")
        self.saf_renderer.load_sofa(sofa_path)

    def process_block(self, input_block: np.ndarray, yaw: float, pitch: float, roll: float) -> np.ndarray:
        """
        Routes the input Ambisonic block through the active processing chain.
        input_block: (Channels, Samples) numpy array
        Returns: (2, Samples) numpy array
        """
        # Convert to Torch tensor for rotation/neural path
        audio_tensor = torch.from_numpy(input_block).to(self.device).unsqueeze(0) # (1, Ch, Time)
        
        # 1. Apply Spatial Rotation (Common to both paths)
        rotated_tensor = self.rotation_engine(audio_tensor, yaw, pitch, roll)
        
        if self.current_state == EngineState.NEURAL:
            # 2a. Neural Decoding
            output_tensor = self.a2b_model(rotated_tensor)
            return output_tensor.squeeze(0).cpu().detach().numpy()
            
        else:
            # 2b. Linear/DSP Decoding (SAF)
            # Convert back to CPU numpy for SAF
            rotated_cpu_array = rotated_tensor.squeeze(0).cpu().detach().numpy()
            
            # Map frontend state to SAF method string if needed
            saf_method = self.current_state.split('-')[-1] if '-' in self.current_state else 'LS'
            
            # Perform traditional DSP binaural rendering
            stereo_array = self.saf_renderer.apply(
                rotated_cpu_array, 
                method=saf_method
            )
            
            return stereo_array
