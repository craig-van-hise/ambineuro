from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import AsyncIOOSCUDPServer
import numpy as np
import asyncio

class OSCController:
    def __init__(self, host="0.0.0.0", port=9000):
        self.host = host
        self.port = port
        self.yaw = 0.0
        self.pitch = 0.0
        self.roll = 0.0
        
        self.dispatcher = Dispatcher()
        self.dispatcher.map("/head/orientation", self.orientation_handler)
        self.server = None

    def orientation_handler(self, address, *args):
        # args: [yaw, pitch, roll] in degrees
        if len(args) >= 3:
            y, p, r = self.normalize_angles(args[0], args[1], args[2])
            self.yaw, self.pitch, self.roll = y, p, r
            self.last_msg_time = asyncio.get_event_loop().time()

    def normalize_angles(self, yaw_deg, pitch_deg, roll_deg):
        """Convert degrees to radians."""
        return [
            np.deg2rad(yaw_deg),
            np.deg2rad(pitch_deg),
            np.deg2rad(roll_deg)
        ]

    async def start_server(self):
        self.server = AsyncIOOSCUDPServer((self.host, self.port), self.dispatcher, asyncio.get_event_loop())
        transport, protocol = await self.server.create_serve_endpoint()
        print(f"OSC server started on {self.host}:{self.port}")
        return transport
