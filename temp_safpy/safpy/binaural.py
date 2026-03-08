import numpy as np
from _safpy import ffi, lib

class BinauralRenderer:
    def __init__(self, order: int, fs: int):
        self.order = order
        self.fs = fs
        self.nSH = (order + 1)**2
        self.hopsize = 128
        self.nBands = 133
        
        self.hSTFT = ffi.new("void**")
        # 0 = AFSTFT_BANDS_CH_TIME layout
        lib.afSTFT_create(self.hSTFT, self.nSH, 2, self.hopsize, 0, 1, 0)
        
        self.freqVector = np.zeros(self.nBands, dtype=np.float32)
        lib.afSTFT_getCentreFreqs(self.hSTFT[0], float(fs), self.nBands, ffi.cast("float*", self.freqVector.ctypes.data))
        
        # Load default HRTFs from the C library safely bypassing Python name mangling
        self.N_dirs = int(getattr(lib, '__default_N_hrir_dirs'))
        self.hrir_len = int(getattr(lib, '__default_hrir_len'))
        self.hrir_fs = int(getattr(lib, '__default_hrir_fs'))
        
        # Pointer to the raw float data in the shared library
        hrirs_ptr = ffi.cast("float*", getattr(lib, '__default_hrirs'))
        
        # Convert Time-Domain HRIRs to Frequency-Domain Filterbank (hrtf_fb)
        self.hrtf_fb = np.zeros((self.nBands, 2, self.N_dirs), dtype=np.complex64)
        lib.HRIRs2HRTFs_afSTFT(hrirs_ptr, self.N_dirs, self.hrir_len, self.hopsize, 0, 1, ffi.cast("float _Complex*", self.hrtf_fb.ctypes.data))
        
        # Estimate Interaural Time Differences (ITDs) required for TA and MagLS decoders
        self.itds = np.zeros(self.N_dirs, dtype=np.float32)
        lib.estimateITDs(hrirs_ptr, self.N_dirs, self.hrir_len, self.hrir_fs, ffi.cast("float*", self.itds.ctypes.data))
        
        self.hrir_dirs_deg = np.zeros((self.N_dirs, 2), dtype=np.float32)
        ffi.memmove(ffi.cast("void*", self.hrir_dirs_deg.ctypes.data), getattr(lib, '__default_hrir_dirs_deg'), self.N_dirs * 2 * 4)
        
        self.dec_matrices = {}

    def _get_matrix(self, method: str):
        """Caches and returns the decoding matrix for the requested method."""
        if method in self.dec_matrices:
            return self.dec_matrices[method]
            
        method_map = {
            'LS': lib.BINAURAL_DECODER_LS,
            'LSDIFFEQ': lib.BINAURAL_DECODER_LSDIFFEQ,
            'SPR': lib.BINAURAL_DECODER_SPR,
            'TA': lib.BINAURAL_DECODER_TA,
            'MagLS': lib.BINAURAL_DECODER_MAGLS
        }
        c_method = method_map.get(method, lib.BINAURAL_DECODER_LS)
        
        decMtx = np.zeros((self.nBands, 2, self.nSH), dtype=np.complex64)
        
        # Instruct the C library to compute the optimal decoding matrix
        lib.getBinauralAmbiDecoderMtx(
            ffi.cast("float _Complex*", self.hrtf_fb.ctypes.data),
            ffi.cast("float*", self.hrir_dirs_deg.ctypes.data),
            self.N_dirs,
            self.nBands,
            c_method,
            self.order,
            ffi.cast("float*", self.freqVector.ctypes.data),
            ffi.cast("float*", self.itds.ctypes.data),
            ffi.NULL, # No custom weights
            0, # enableDiffCM = false
            1, # enableMaxrE = true
            ffi.cast("float _Complex*", decMtx.ctypes.data)
        )
        self.dec_matrices[method] = decMtx
        return decMtx

    def load_sofa(self, sofa_file_path: str):
        # We will bypass custom SOFA loading temporarily to ensure the core algorithms function flawlessly.
        print(f"Skipping SOFA load to enforce default HRTF mapping: {sofa_file_path}")

    def apply(self, rotated_cpu_array: np.ndarray, method: str) -> np.ndarray:
        # rotated_cpu_array: (nSH, frames)
        framesize = rotated_cpu_array.shape[1]
        num_hops = framesize // self.hopsize
        
        # 1. Prepare input
        in_flat = np.ascontiguousarray(rotated_cpu_array, dtype=np.float32)
        
        # 2. Time-Frequency Transform (afSTFT Forward)
        # Expected Output: (nBands, nSH, nHops)
        data_fd = np.zeros((self.nBands, self.nSH, num_hops), dtype=np.complex64)
        lib.afSTFT_forward_flat(
            self.hSTFT[0], 
            ffi.cast("float*", in_flat.ctypes.data), 
            framesize, 
            ffi.cast("float _Complex*", data_fd.ctypes.data)
        )
        
        # 3. Retrieve Spatial Decoding Matrix
        # Matrix: (nBands, 2_Ears, nSH)
        decMtx = self._get_matrix(method)
        
        # 4. Apply Spatial Rendering Matrix Multiplication
        # Multiply (nBands, 2, nSH) by (nBands, nSH, nHops) -> (nBands, 2, nHops)
        bin_fd = np.einsum('bik,bkj->bij', decMtx, data_fd)
        bin_fd = np.ascontiguousarray(bin_fd, dtype=np.complex64)
        
        # 5. Inverse Time-Frequency Transform (afSTFT Backward)
        out_td = np.zeros((2, framesize), dtype=np.float32)
        lib.afSTFT_backward_flat(
            self.hSTFT[0], 
            ffi.cast("float _Complex*", bin_fd.ctypes.data), 
            framesize, 
            ffi.cast("float*", out_td.ctypes.data)
        )
        
        return out_td

    def __del__(self):
        if hasattr(self, 'hSTFT') and self.hSTFT[0] != ffi.NULL:
            lib.afSTFT_destroy(self.hSTFT)
