import numpy as np

class BinauralRenderer:
    def __init__(self, order: int, fs: int):
        self.order = order
        self.fs = fs

    def load_sofa(self, sofa_file_path: str):
        print(f"Mock loading SOFA: {sofa_file_path}")

    def apply(self, rotated_cpu_array: np.ndarray, method: str) -> np.ndarray:
        num_samples = rotated_cpu_array.shape[1]
        stereo = np.zeros((2, num_samples), dtype=np.float32)
        if rotated_cpu_array.shape[0] >= 2:
            stereo[0, :] = rotated_cpu_array[0, :]
            stereo[1, :] = rotated_cpu_array[1, :]
        return stereo
