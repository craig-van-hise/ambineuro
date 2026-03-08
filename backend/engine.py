import asyncio
import websockets
import json
import sys
import os
import signal
import numpy as np
import torch
import sounddevice as sd
import logging

# Configure logging to file
log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "engine.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_path),
        logging.StreamHandler(sys.stdout)
    ]
)

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from audio_utils import RingBuffer, WaveLoader, UnderflowError
from decoder_graph import DecoderGraph
from osc_controller import OSCController

class AudioEngine:
    def __init__(self, ambisonic_order=4, blocksize=512, samplerate=48000):
        logging.info("Initializing AudioEngine...")
        self.running = True
        self.order = ambisonic_order
        self.blocksize = blocksize
        self.samplerate = samplerate
        self.in_channels = (self.order + 1) ** 2
        self.out_channels = 2
        self.ring_buffer = RingBuffer(size=blocksize * 64, channels=self.in_channels)
        self.loader = None
        self.stream = None
        
        try:
            device = 'mps' if torch.backends.mps.is_available() else 'cpu'
            logging.info(f"Initializing DecoderGraph on {device}...")
            self.decoder = DecoderGraph(ambisonic_order=self.order, sample_rate=samplerate, device=device)
        except Exception as e:
            logging.error(f"Failed to initialize DecoderGraph: {e}")
            raise

        self.osc = OSCController()
        self.osc.last_msg_time = 0
        
        self.is_playing = False
        self.volume = 1.0
        self.position = 0.0
        self.duration = 0.0
        self.clients = set()

    def audio_callback(self, outdata, frames, time, status):
        if status:
            logging.warning(f"Audio status: {status}")
        
        if not self.is_playing or not self.loader:
            outdata.fill(0)
            return

        try:
            in_data = self.ring_buffer.read(frames)
            in_data_t = in_data.T
            out_data_t = self.decoder.process_block(
                in_data_t, 
                self.osc.yaw, self.osc.pitch, self.osc.roll
            )
            outdata[:] = out_data_t.T * self.volume
            self.position += frames / self.samplerate
        except UnderflowError:
            outdata.fill(0)
        except Exception as e:
            logging.error(f"Callback error: {e}")
            outdata.fill(0)

    def _adapt_block_channels(self, block: np.ndarray) -> np.ndarray:
        curr_ch = block.shape[1]
        if curr_ch == self.in_channels:
            return block
        adapted = np.zeros((block.shape[0], self.in_channels), dtype=np.float32)
        take_ch = min(curr_ch, self.in_channels)
        adapted[:, :take_ch] = block[:, :take_ch]
        return adapted

    def load_wav(self, filepath):
        logging.info(f"Loading WAV: {filepath}")
        if not filepath:
            logging.error("Load WAV received empty path")
            return
        try:
            self.loader = WaveLoader(filepath)
            self.duration = len(self.loader.data) / self.loader.samplerate
            self.position = 0.0
            with self.ring_buffer.lock:
                self.ring_buffer.count = 0
                self.ring_buffer.read_ptr = 0
                self.ring_buffer.write_ptr = 0
            self.is_playing = True
            logging.info(f"Successfully loaded WAV. Duration: {self.duration:.2f}s")
        except Exception as e:
            logging.error(f"Failed to load WAV: {e}")

    async def fill_buffer_loop(self):
        logging.info("Starting buffer fill loop")
        while self.running:
            try:
                if self.is_playing and self.loader and self.ring_buffer.available_write() >= self.blocksize:
                    block = self.loader.get_block(self.blocksize)
                    adapted_block = self._adapt_block_channels(block)
                    self.ring_buffer.write(adapted_block)
            except Exception as e:
                logging.error(f"Fill buffer error: {e}")
            await asyncio.sleep(0.001)

    async def broadcast_state(self):
        logging.info("Starting broadcast loop")
        while self.running:
            if self.clients:
                try:
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
                    disconnected = []
                    for client in list(self.clients):
                        try:
                            await client.send(message)
                        except:
                            disconnected.append(client)
                    for c in disconnected:
                        self.clients.remove(c)
                except Exception as e:
                    logging.error(f"Broadcast error: {e}")
            await asyncio.sleep(0.1)

    async def handle_client(self, websocket):
        logging.info(f"Client connected from {websocket.remote_address}")
        self.clients.add(websocket)
        try:
            async for message in websocket:
                data = json.loads(message)
                mtype = data.get('type')
                if mtype == 'ping':
                    await websocket.send(json.dumps({'type': 'pong'}))
                elif mtype in ['load_wav', 'load_audio']:
                    self.load_wav(data.get('path'))
                elif mtype == 'play':
                    self.is_playing = True
                    logging.info("Playback resumed")
                elif mtype == 'pause':
                    self.is_playing = False
                    logging.info("Playback paused")
                elif mtype == 'stop':
                    self.is_playing = False
                    self.position = 0.0
                    if self.loader: self.loader.ptr = 0
                    with self.ring_buffer.lock: self.ring_buffer.count = 0
                    logging.info("Playback stopped")
                elif mtype == 'seek':
                    pos = data.get('position', 0)
                    self.position = pos
                    if self.loader: self.loader.ptr = int(pos * self.samplerate)
                    with self.ring_buffer.lock: self.ring_buffer.count = 0
                elif mtype == 'set_volume':
                    self.volume = data.get('volume', 1.0)
                elif mtype == 'set_orientation':
                    ori = data.get('orientation', {})
                    if 'yaw' in ori: self.osc.yaw = np.deg2rad(ori['yaw'])
                    if 'pitch' in ori: self.osc.pitch = np.deg2rad(ori['pitch'])
                    if 'roll' in ori: self.osc.roll = np.deg2rad(ori['roll'])
                    self.osc.last_msg_time = 0
                elif mtype in ['load_sofa', 'load_hrtf']:
                    self.decoder.load_custom_hrtf(data.get('path'))
                elif mtype == 'set_decoder':
                    self.decoder.set_decoder_state(data.get('decoder') or data.get('state'))
                elif mtype == 'quit':
                    self.running = False
                    break
        except websockets.exceptions.ConnectionClosed:
            logging.info("Client disconnected")
        finally:
            if websocket in self.clients:
                self.clients.remove(websocket)

    def start_audio(self):
        try:
            logging.info(f"Starting audio stream on {self.samplerate}Hz...")
            self.stream = sd.OutputStream(
                samplerate=self.samplerate,
                blocksize=self.blocksize,
                channels=self.out_channels,
                callback=self.audio_callback
            )
            self.stream.start()
            logging.info("Audio stream started.")
        except Exception as e:
            logging.error(f"Failed to start audio: {e}")

    def stop_audio(self):
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
            logging.info("Audio stream stopped.")

    async def start_server(self, host="0.0.0.0", port=8002):
        self.start_audio()
        await self.osc.start_server()
        asyncio.create_task(self.fill_buffer_loop())
        asyncio.create_task(self.broadcast_state())
        
        logging.info(f"Engine WebSocket server starting on ws://{host}:{port}")
        async with websockets.serve(self.handle_client, host, port):
            while self.running:
                await asyncio.sleep(0.1)
        
        self.stop_audio()
        logging.info("Engine shut down.")

def handle_sigterm(*args):
    logging.info("SIGTERM received")
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGTERM, handle_sigterm)
    signal.signal(signal.SIGINT, handle_sigterm)
    engine = AudioEngine()
    try:
        asyncio.run(engine.start_server())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logging.fatal(f"Uncaught exception: {e}")
