import torch
import unittest

class TestEnvironment(unittest.TestCase):
    def test_mps_available(self):
        """Assert that MPS (Metal Performance Shaders) is available for Apple Silicon."""
        self.assertTrue(torch.backends.mps.is_available(), "MPS is NOT available. This project requires macOS with Apple Silicon or similar GPU acceleration.")

    def test_safpy_import(self):
        """Assert that safpy can be imported without errors."""
        try:
            import safpy
            print(f"safpy imported successfully. Version: {getattr(safpy, '__version__', 'unknown')}")
        except ImportError as e:
            self.fail(f"safpy import failed: {e}")

if __name__ == '__main__':
    unittest.main()
