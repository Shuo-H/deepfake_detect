"""
Example WebSocket client for sending audio chunks to the detection server.

This can be adapted for mobile applications (iOS/Android) or Python clients.
"""
import asyncio
import base64
import json
import time
import numpy as np
import soundfile as sf
from typing import Optional
import websockets
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AudioDetectionClient:
    """Client for connecting to the deepfake detection WebSocket server."""
    
    def __init__(self, server_url: str = "ws://localhost:8765/ws/detect"):
        """
        Initialize the client.
        
        Args:
            server_url: WebSocket server URL
        """
        self.server_url = server_url
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.client_id: Optional[str] = None
        self.connected = False
    
    async def connect(self, client_id: Optional[str] = None) -> bool:
        """
        Connect to the WebSocket server.
        
        Args:
            client_id: Optional client identifier
            
        Returns:
            True if connected successfully
        """
        try:
            if client_id is None:
                import uuid
                client_id = str(uuid.uuid4())
            
            self.client_id = client_id
            
            # Connect to server
            self.websocket = await websockets.connect(self.server_url)
            self.connected = True
            
            # Send initial connection message
            await self.websocket.send(json.dumps({
                "type": "connect",
                "client_id": self.client_id,
                "timestamp": time.time()
            }))
            
            # Wait for connection confirmation
            response = await self.websocket.recv()
            data = json.loads(response)
            
            if data.get("type") == "connected":
                logger.info(f"Connected to server with client_id: {self.client_id}")
                return True
            else:
                logger.error(f"Connection failed: {data}")
                return False
        
        except Exception as e:
            logger.error(f"Error connecting to server: {e}")
            self.connected = False
            return False
    
    async def send_audio_chunk(
        self,
        audio_data: np.ndarray,
        sample_rate: int = 16000,
        encoding: str = "base64"
    ) -> Optional[dict]:
        """
        Send an audio chunk for detection.
        
        Args:
            audio_data: Audio data as numpy array
            sample_rate: Sample rate of the audio
            encoding: Encoding method ('base64' or 'json')
            
        Returns:
            Detection result dictionary or None
        """
        if not self.connected or not self.websocket:
            logger.error("Not connected to server")
            return None
        
        try:
            # Encode audio data
            if encoding == "base64":
                audio_bytes = audio_data.astype(np.float32).tobytes()
                audio_data_str = base64.b64encode(audio_bytes).decode('utf-8')
            elif encoding == "json":
                audio_data_str = audio_data.tolist()
            else:
                raise ValueError(f"Unsupported encoding: {encoding}")
            
            # Send message
            message = {
                "type": "audio_chunk",
                "client_id": self.client_id,
                "audio_data": audio_data_str,
                "sample_rate": sample_rate,
                "encoding": encoding,
                "timestamp": time.time()
            }
            
            await self.websocket.send(json.dumps(message))
            
            # Wait for response (with timeout)
            try:
                response = await asyncio.wait_for(self.websocket.recv(), timeout=5.0)
                data = json.loads(response)
                
                if data.get("type") == "detection_result":
                    return data.get("result")
                elif data.get("type") == "error":
                    logger.error(f"Server error: {data.get('message')}")
                    return None
                else:
                    return None
            
            except asyncio.TimeoutError:
                logger.warning("Timeout waiting for detection result")
                return None
        
        except Exception as e:
            logger.error(f"Error sending audio chunk: {e}")
            return None
    
    async def send_audio_file(
        self,
        file_path: str,
        chunk_duration: float = 1.0,
        sample_rate: int = 16000
    ):
        """
        Send an audio file in chunks.
        
        Args:
            file_path: Path to audio file
            chunk_duration: Duration of each chunk in seconds
            sample_rate: Target sample rate
        """
        try:
            # Load audio file
            audio_data, original_sr = sf.read(file_path)
            
            # Resample if needed (simplified - use librosa in production)
            if original_sr != sample_rate:
                logger.warning(f"Resampling from {original_sr} to {sample_rate} Hz")
                # In production, use proper resampling library
            
            # Convert to mono if stereo
            if len(audio_data.shape) > 1:
                audio_data = np.mean(audio_data, axis=1)
            
            # Normalize to float32
            audio_data = audio_data.astype(np.float32)
            
            # Split into chunks
            chunk_samples = int(sample_rate * chunk_duration)
            num_chunks = len(audio_data) // chunk_samples
            
            logger.info(f"Sending {num_chunks} chunks from {file_path}")
            
            for i in range(num_chunks):
                start_idx = i * chunk_samples
                end_idx = start_idx + chunk_samples
                chunk = audio_data[start_idx:end_idx]
                
                result = await self.send_audio_chunk(chunk, sample_rate)
                if result:
                    logger.info(f"Chunk {i+1}/{num_chunks}: {result.get('label')} "
                              f"(confidence: {result.get('score', 0):.2%})")
                
                # Small delay between chunks
                await asyncio.sleep(0.1)
        
        except Exception as e:
            logger.error(f"Error sending audio file: {e}")
    
    async def ping(self) -> bool:
        """Send ping to server."""
        if not self.connected or not self.websocket:
            return False
        
        try:
            await self.websocket.send(json.dumps({
                "type": "ping",
                "timestamp": time.time()
            }))
            
            response = await asyncio.wait_for(self.websocket.recv(), timeout=2.0)
            data = json.loads(response)
            return data.get("type") == "pong"
        
        except Exception as e:
            logger.error(f"Ping failed: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from server."""
        if self.websocket:
            await self.websocket.close()
        self.connected = False
        logger.info("Disconnected from server")


async def example_usage():
    """Example usage of the client."""
    client = AudioDetectionClient(server_url="ws://localhost:8765/ws/detect")
    
    # Connect
    if await client.connect():
        # Example 1: Send audio file
        await client.send_audio_file("samples/E_0000418769.flac")
        
        # Example 2: Send individual chunks
        # Generate dummy audio
        dummy_audio = np.random.randn(16000).astype(np.float32)
        result = await client.send_audio_chunk(dummy_audio, sample_rate=16000)
        if result:
            print(f"Detection result: {result}")
        
        # Disconnect
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(example_usage())

