import unittest
import numpy as np
import torch
from decoder_graph import DecoderGraph, EngineState

class TestDecoderGraph(unittest.TestCase):
    def test_neural_routing(self):
        """Test routing through the neural (A2B) engine."""
        device = 'mps' if torch.backends.mps.is_available() else 'cpu'
        dg = DecoderGraph(ambisonic_order=1, device=device)
        dg.set_decoder_state(EngineState.NEURAL)
        
        # 4 channels for 1st order
        num_channels = (1 + 1) ** 2
        dummy_in = np.random.rand(num_channels, 1024).astype(np.float32)
        
        # Process block
        out = dg.process_block(dummy_in, 0, 0, 0)
        
        # Assertion: output should be (2, 1024)
        self.assertEqual(out.shape, (2, 1024))

    def test_linear_routing(self):
        """Test routing through the linear (SAF) engine."""
        device = 'mps' if torch.backends.mps.is_available() else 'cpu'
        dg = DecoderGraph(ambisonic_order=1, device=device)
        dg.set_decoder_state(EngineState.SAF_MAGLS)
        
        num_channels = (1 + 1) ** 2
        dummy_in = np.random.rand(num_channels, 1024).astype(np.float32)
        
        # Process block
        out = dg.process_block(dummy_in, 0, 0, 0)
        
        # Assertion: output should be (2, 1024)
        self.assertEqual(out.shape, (2, 1024))

if __name__ == '__main__':
    unittest.main()
