import unittest
import numpy as np
from audio_utils import RingBuffer

class TestRingBuffer(unittest.TestCase):
    def test_read_write(self):
        """Test basic read/write operations of the RingBuffer."""
        rb = RingBuffer(size=4096, channels=2)
        data = np.random.rand(2048, 2).astype(np.float32)
        
        # Write 2048 samples
        rb.write(data)
        self.assertEqual(rb.available_read(), 2048)
        
        # Read 1024 samples
        read_data = rb.read(1024)
        self.assertEqual(rb.available_read(), 1024)
        self.assertEqual(read_data.shape, (1024, 2))
        np.testing.assert_array_equal(read_data, data[:1024])

    def test_overflow(self):
        """Test that writing more than available space raises an error or handles it."""
        rb = RingBuffer(size=1024, channels=1)
        data = np.random.rand(2048, 1).astype(np.float32)
        with self.assertRaises(OverflowError):
            rb.write(data)

    def test_callback_mock(self):
        """Mock callback and check if it pulls data correctly from the buffer."""
        rb = RingBuffer(size=4096, channels=2)
        test_data = np.random.rand(1024, 2).astype(np.float32)
        rb.write(test_data)
        
        # Mocking what sounddevice callback does
        out_buffer = np.zeros((1024, 2), dtype=np.float32)
        def mock_callback(outdata, frames, time, status):
            data = rb.read(frames)
            outdata[:] = data
        
        mock_callback(out_buffer, 1024, None, None)
        np.testing.assert_array_equal(out_buffer, test_data)
        self.assertEqual(rb.available_read(), 0)

if __name__ == '__main__':
    unittest.main()
