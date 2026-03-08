import numpy as np
import threading

class RingBuffer:
    """
    A multi-threaded ring buffer for audio data.
    Uses numpy for storage and provides thread-safe access to read/write.
    """
    def __init__(self, size: int, channels: int):
        self.size = size
        self.channels = channels
        self.buffer = np.zeros((size, channels), dtype=np.float32)
        self.read_ptr = 0
        self.write_ptr = 0
        self.count = 0
        self.lock = threading.Lock()

    def available_read(self) -> int:
        with self.lock:
            return self.count

    def available_write(self) -> int:
        with self.lock:
            return self.size - self.count

    def write(self, data: np.ndarray):
        num_samples = data.shape[0]
        with self.lock:
            if num_samples > (self.size - self.count):
                raise OverflowError("RingBuffer overflow")
            
            # Write in one or two chunks
            end_ptr = (self.write_ptr + num_samples) % self.size
            if end_ptr > self.write_ptr:
                self.buffer[self.write_ptr:self.write_ptr + num_samples] = data
            else:
                chunk1_size = self.size - self.write_ptr
                self.buffer[self.write_ptr:] = data[:chunk1_size]
                self.buffer[:num_samples - chunk1_size] = data[chunk1_size:]
            
            self.write_ptr = end_ptr
            self.count += num_samples

    def read(self, num_samples: int) -> np.ndarray:
        with self.lock:
            if num_samples > self.count:
                # Provide what we have, filled with zeros or raise error?
                # For audio callback, we usually want to return whatever is available
                # but for this test we'll be strict.
                raise UnderflowError("RingBuffer underflow")
            
            out = np.zeros((num_samples, self.channels), dtype=np.float32)
            
            # Read in one or two chunks
            end_ptr = (self.read_ptr + num_samples) % self.size
            if end_ptr > self.read_ptr:
                out = self.buffer[self.read_ptr:self.read_ptr + num_samples].copy()
            else:
                chunk1_size = self.size - self.read_ptr
                out[:chunk1_size] = self.buffer[self.read_ptr:]
                out[chunk1_size:] = self.buffer[:num_samples - chunk1_size]
            
            self.read_ptr = end_ptr
            self.count -= num_samples
            return out

class UnderflowError(Exception):
    pass

import soundfile as sf

class WaveLoader:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.data, self.samplerate = sf.read(filepath, dtype='float32')
        self.channels = self.data.shape[1] if len(self.data.shape) > 1 else 1
        self.ptr = 0

    def get_block(self, blocksize: int) -> np.ndarray:
        if self.ptr >= len(self.data):
            return np.zeros((blocksize, self.channels), dtype=np.float32)
        
        end = min(self.ptr + blocksize, len(self.data))
        block = self.data[self.ptr:end]
        
        # Zero pad if shorter than blocksize
        if len(block) < blocksize:
            padded = np.zeros((blocksize, self.channels), dtype=np.float32)
            padded[:len(block)] = block
            block = padded
            
        self.ptr = end
        return block

    def is_finished(self) -> bool:
        return self.ptr >= len(self.data)
