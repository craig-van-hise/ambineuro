import asyncio
import websockets
import json
import sys
import os
import signal
import numpy as np
import torch
import sounddevice as sd
from audio_utils import RingBuffer, WaveLoader, UnderflowError
from decoder_graph import DecoderGraph
from osc_controller import OSCController

# Add backend directory to path to find decoder_graph
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class AudioEngine:
    def __init__(self, ambisonic_order=4, blocksize=512, samplerate=48000):
        self.running = True
        self.order = ambisonic_order
        self.blocksize = blocksize
        self.samplerate = samplerate
        # Ambisonic input has (order+1)^2 channels
        self.in_channels = (self.order + 1) ** 2
        self.out_channels = 2
        self.ring_buffer = RingBuffer(size=blocksize * 16, channels=self.in_channels)
        self.loader = None
        self.stream = None
        
        # Initialize DecoderGraph
        device = 'mps' if torch.backends.mps.is_available() else 'cpu'
        self.decoder = DecoderGraph(ambisonic_order=self.order, sample_rate=samplerate, device=device)
        
        # Head orientation
        self.osc = OSCController()
        self.osc.last_msg_time = 0
        
        # Playback State
        self.is_playing = False
        self.volume = 1.0
        self.position = 0.0 # in seconds
        self.duration = 0.0 # in seconds
        
        # Clients for broadcasting
        self.clients = set()

    def audio_callback(self, outdata, frames, time, status):
        if status:
            print(f"Audio status: {status}")
        
        if not self.is_playing:
            outdata.fill(0)
            return

        try:
            # 1. Read ambisonic block from ring buffer
            in_data = self.ring_buffer.read(frames)
            
            # 2. Process block via DecoderGraph (Rotation + Decoding)
            in_data_t = in_data.T
            out_data_t = self.decoder.process_block(
                in_data_t, 
                self.osc.yaw, self.osc.pitch, self.osc.roll
            )
            
            # 3. Output stereo data with volume
            outdata[:] = out_data_t.T * self.volume
            
            # Update position
            self.position += frames / self.samplerate
            
        except UnderflowError:
            outdata.fill(0)

    def load_wav(self, filepath):
        print(f"Loading WAV: {filepath}")
        try:
            self.loader = WaveLoader(filepath)
            self.duration = len(self.loader.data) / self.loader.samplerate
            self.position = 0.0
            self.is_playing = True # Auto-play on load
            # Clear ring buffer
            with self.ring_buffer.lock:
                self.ring_buffer.count = 0
                self.ring_buffer.read_ptr = 0
                self.ring_buffer.write_ptr = 0
        except Exception as e:
            print(f"Failed to load WAV: {e}")

    async def fill_buffer_loop(self):
        while self.running:
            if self.is_playing and self.loader and self.ring_buffer.available_write() >= self.blocksize:
                block = self.loader.get_block(self.blocksize)
                try:
                    self.ring_buffer.write(block)
                except OverflowError:
                    pass
            await asyncio.sleep(0.01)

    async def broadcast_state(self):
        while self.running:
            if self.clients:
                now = asyncio.get_event_loop().time()
                state = {
                    'type': 'state',
                    'playing': self.is_playing,
                    'position': self.position,
                    'duration': self.duration,
                    'volume': self.volume,
                    'orientation': {
                        'yaw': float(np.rad2deg(self.osc.yaw)),
                        'pitch': float(np.rad2deg(self.osc.pitch)),
                        'roll': float(np.rad2deg(self.osc.roll))
                    },
                    'osc_active': (now - self.osc.last_msg_time) < 1.0
                }
                message = json.dumps(state)
                for client in list(self.clients):
                    try:
                        await client.send(message)
                    except:
                        if client in self.clients:
                            self.clients.remove(client)
            await asyncio.sleep(0.1)

    async def handle_client(self, websocket):
        print("Client connected")
        self.clients.add(websocket)
        try:
            async for message in websocket:
                data = json.loads(message)
                mtype = data.get('type')
                
                if mtype == 'ping':
                    await websocket.send(json.dumps({'type': 'pong'}))
                
                elif mtype in ['load_wav', 'load_audio']:
                    path = data.get('path')
                    self.load_wav(path)
                
                elif mtype == 'play':
                    self.is_playing = True
                
                elif mtype == 'pause':
                    self.is_playing = False
                
                elif mtype == 'stop':
                    self.is_playing = False
                    self.position = 0.0
                    if self.loader:
                        self.loader.ptr = 0
                    with self.ring_buffer.lock:
                        self.ring_buffer.count = 0
                
                elif mtype == 'seek':
                    pos = data.get('position', 0)
                    self.position = pos
                    if self.loader:
                        self.loader.ptr = int(pos * self.samplerate)
                    with self.ring_buffer.lock:
                        self.ring_buffer.count = 0
                
                elif mtype == 'set_volume':
                    self.volume = data.get('volume', 1.0)

                elif mtype == 'set_orientation':
                    ori = data.get('orientation', {})
                    if 'yaw' in ori: self.osc.yaw = np.deg2rad(ori['yaw'])
                    if 'pitch' in ori: self.osc.pitch = np.deg2rad(ori['pitch'])
                    if 'roll' in ori: self.osc.roll = np.deg2rad(ori['roll'])
                    self.osc.last_msg_time = 0 # Mark as manual override
                
                elif mtype in ['load_sofa', 'load_hrtf']:
                    path = data.get('path')
                    self.decoder.load_custom_hrtf(path)
                
                elif mtype == 'set_decoder':
                    state = data.get('decoder') or data.get('state')
                    self.decoder.set_decoder_state(state)
                
                elif mtype == 'quit':
                    self.running = False
                    break
        except websockets.exceptions.ConnectionClosed:
            print("Client disconnected")
        finally:
            if websocket in self.clients:
                self.clients.remove(websocket)

    def start_audio(self):
        print(f"Starting audio stream on {self.samplerate}Hz...")
        self.stream = sd.OutputStream(
            samplerate=self.samplerate,
            blocksize=self.blocksize,
            channels=self.out_channels,
            callback=self.audio_callback
        )
        self.stream.start()

    def stop_audio(self):
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

    async def start_server(self, host="0.0.0.0", port=8001):
        self.start_audio()
        await self.osc.start_server()
        asyncio.create_task(self.fill_buffer_loop())
        asyncio.create_task(self.broadcast_state())
        
        async with websockets.serve(self.handle_client, host, port):
            print(f"Engine WebSocket server started on ws://{host}:{port}")
            while self.running:
                await asyncio.sleep(0.1)
        
        self.stop_audio()
        print("Engine shutting down...")

def handle_sigterm(*args):
    print("SIGTERM received, shutting down...")
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGTERM, handle_sigterm)
    signal.signal(signal.SIGINT, handle_sigterm)

    engine = AudioEngine()
    try:
        asyncio.run(engine.start_server())
    except KeyboardInterrupt:
        pass
