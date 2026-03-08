import numpy as np
import safpy

def test_binaural():
    print("Initializing BinauralRenderer (Order 4, 48000Hz)...")
    renderer = safpy.binaural.BinauralRenderer(order=4, fs=48000)
    
    print("Testing MagLS Matrix computation...")
    mtx = renderer._get_matrix('MagLS')
    print(f"Matrix computed. Shape: {mtx.shape}")
    
    print("Testing audio block processing...")
    # 25 channels (4th order), 512 samples
    dummy_input = np.random.rand(25, 512).astype(np.float32)
    output = renderer.apply(dummy_input, 'MagLS')
    print(f"Processing successful. Output shape: {output.shape}")

if __name__ == '__main__':
    test_binaural()
