import torch
import torch.nn as nn

class A2BModel(nn.Module):
    def __init__(self, order: int):
        super().__init__()
        self.order = order
        self.num_input_channels = (order + 1) ** 2
        # Mock linear layer to simulate processing
        self.fc = nn.Linear(self.num_input_channels, 2)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x shape: (Batch, Channels, Time)
        # We want to return (Batch, 2, Time)
        batch, channels, time = x.shape
        # Permute to (Batch, Time, Channels) for Linear layer
        x = x.permute(0, 2, 1)
        # Apply mock processing
        x = self.fc(x)
        # Permute back to (Batch, 2, Time)
        x = x.permute(0, 2, 1)
        return x
