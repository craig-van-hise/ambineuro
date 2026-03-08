import torch
import torch.nn as nn
import numpy as np

class WignerDRotation(nn.Module):
    def __init__(self, order: int):
        super().__init__()
        self.order = order

    def forward(self, x: torch.Tensor, yaw: float, pitch: float, roll: float) -> torch.Tensor:
        """
        Apply spatial rotation.
        x: (Batch, Channels, Time)
        Angles in degrees.
        """
        # Batch size 1 assumed for now
        batch, channels, time = x.shape
        if channels < 4:
            return x
            
        # Convert degrees to radians
        ay = np.deg2rad(yaw)
        ap = np.deg2rad(pitch)
        ar = np.deg2rad(roll)
        
        # 1st order rotation matrix (standard ZYX intrinsic)
        # Note: SAF uses ACN (0:W, 1:Y, 2:Z, 3:X)
        # We'll just implement a simple 1st order rotation for now
        # W is omni (ch 0), no rotation.
        # Y (ch 1), Z (ch 2), X (ch 3)
        
        # Rotation Matrix R
        cy, sy = np.cos(ay), np.sin(ay)
        cp, sp = np.cos(ap), np.sin(ap)
        cr, sr = np.cos(ar), np.sin(ar)
        
        # Simplified rotation for demonstration
        # In a real app, we'd use the full 3x3 rotation matrix for the dipoles
        # and higher order Wigner-D for n > 1.
        
        # For now, let's just use the Yaw to rotate X and Y
        # ACN: Y is ch 1, X is ch 3.
        y_rotated = x[:, 1, :] * cy - x[:, 3, :] * sy
        x_rotated = x[:, 1, :] * sy + x[:, 3, :] * cy
        
        out = x.clone()
        out[:, 1, :] = y_rotated
        out[:, 3, :] = x_rotated
        
        return out
