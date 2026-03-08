import unittest
import numpy as np
from osc_controller import OSCController

class TestOSCController(unittest.TestCase):
    def test_angle_normalization(self):
        """Test that degrees are correctly converted to radians."""
        controller = OSCController()
        radians = controller.normalize_angles(90.0, 0.0, 0.0)
        np.testing.assert_almost_equal(radians, [np.pi/2, 0.0, 0.0], decimal=2)

    def test_concurrency(self):
        """Simulate concurrent access to angles."""
        import threading
        controller = OSCController()
        def write_loop():
            for i in range(1000):
                controller.orientation_handler("/head/orientation", i*0.1, 0, 0)
        
        def read_loop():
            for i in range(1000):
                y, p, r = controller.yaw, controller.pitch, controller.roll
                self.assertIsInstance(y, float)
        
        t1 = threading.Thread(target=write_loop)
        t2 = threading.Thread(target=read_loop)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

if __name__ == '__main__':
    unittest.main()
