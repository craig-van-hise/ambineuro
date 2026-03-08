import asyncio
import websockets
import json
import unittest
import subprocess
import time
import os
import signal

class TestEngineIPC(unittest.TestCase):
    async def ping_pong(self):
        uri = "ws://127.0.0.1:8001"
        async with websockets.connect(uri) as websocket:
            await websocket.send(json.dumps({'type': 'ping'}))
            response = await websocket.recv()
            data = json.loads(response)
            self.assertEqual(data.get('type'), 'pong')

    def test_websocket_ping_pong(self):
        """Test that the engine responds to ping with pong via WebSocket."""
        # Start engine.py in a separate process
        env = os.environ.copy()
        engine_proc = subprocess.Popen(
            ["./venv/bin/python", "engine.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env
        )
        
        # Give it a moment to start
        time.sleep(5)
        
        try:
            asyncio.run(self.ping_pong())
        finally:
            engine_proc.terminate()
            engine_proc.wait(timeout=5)

    def test_lifecycle_termination(self):
        """Test that the engine terminates when SIGTERM is received (simulating Electron quit)."""
        engine_proc = subprocess.Popen(
            ["./venv/bin/python", "engine.py"]
        )
        time.sleep(2)
        self.assertIsNone(engine_proc.poll(), "Engine should be running")
        
        engine_proc.terminate()
        time.sleep(1)
        self.assertIsNotNone(engine_proc.poll(), "Engine should have terminated")

from unittest.mock import MagicMock
import numpy as np
from engine import AudioEngine

class TestEngineIntegration(unittest.TestCase):
    def test_decoder_call(self):
        """Assert that the audio callback calls DecoderGraph.process_block."""
        # Initialize AudioEngine with mocked DecoderGraph
        ae = AudioEngine(ambisonic_order=1)
        ae.decoder = MagicMock()
        
        # Prepare dummy input in ring buffer (4 channels for 1st order)
        num_channels = (1 + 1) ** 2
        dummy_in = np.random.rand(512, num_channels).astype(np.float32)
        ae.ring_buffer.write(dummy_in)
        
        # Mock callback output
        outdata = np.zeros((512, 2), dtype=np.float32)
        
        # Simulated return value from decoder (2, 512)
        ae.decoder.process_block.return_value = np.zeros((2, 512), dtype=np.float32)
        
        # Run callback
        ae.audio_callback(outdata, 512, None, None)
        
        # Assertions
        ae.decoder.process_block.assert_called_once()
        self.assertEqual(ae.ring_buffer.available_read(), 0)

if __name__ == '__main__':
    unittest.main()
