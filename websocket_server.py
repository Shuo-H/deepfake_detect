"""
WebSocket server for real-time audio deepfake detection.

This module provides a WebSocket-based server that receives audio chunks
from mobile devices and performs real-time deepfake detection.
"""
import asyncio
import base64
import json
import logging
import time
from collections import deque
from typing import Dict, Optional, Set
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from core import initialize_model, load_config
from logger import setup_logging
from exceptions import AudioFormatError, AudioProcessingError, DetectionError

logger = logging.getLogger(__name__)


class AudioStreamBuffer:
    """
    Buffer for accumulating audio chunks from WebSocket stream.
    
    Maintains a sliding window of audio data for real-time processing.
    """
    
    def __init__(
        self,
        sample_rate: int = 16000,
        chunk_duration: float = 1.0,
        overlap_duration: float = 0.5,
        min_duration: float = 0.5
    ):
        """
        Initialize audio stream buffer.
        
        Args:
            sample_rate: Audio sample rate in Hz
            chunk_duration: Duration of each processing chunk in seconds
            overlap_duration: Overlap between chunks in seconds
            min_duration: Minimum audio duration before processing
        """
        self.sample_rate = sample_rate
        self.chunk_duration = chunk_duration
        self.overlap_duration = overlap_duration
        self.min_duration = min_duration
        
        # Buffer for accumulating audio
        self.buffer: deque = deque(maxlen=int(sample_rate * 10))  # Max 10 seconds
        self.last_process_time = 0.0
        self.process_interval = chunk_duration - overlap_duration
        
        # Statistics
        self.total_chunks_received = 0
        self.total_chunks_processed = 0
    
    def add_chunk(self, audio_data: np.ndarray) -> None:
        """
        Add audio chunk to buffer.
        
        Args:
            audio_data: Audio data as numpy array
        """
        if len(audio_data) > 0:
            self.buffer.extend(audio_data.tolist())
            self.total_chunks_received += 1
    
    def get_processing_chunk(self) -> Optional[np.ndarray]:
        """
        Get audio chunk for processing if enough data accumulated.
        
        Returns:
            Audio chunk as numpy array, or None if not enough data
        """
        current_time = time.time()
        
        # Check if enough time has passed since last processing
        if current_time - self.last_process_time < self.process_interval:
            return None
        
        # Check if we have enough audio data
        min_samples = int(self.sample_rate * self.min_duration)
        if len(self.buffer) < min_samples:
            return None
        
        # Get chunk for processing
        chunk_samples = int(self.sample_rate * self.chunk_duration)
        chunk_samples = min(chunk_samples, len(self.buffer))
        
        # Extract chunk (keep overlap in buffer)
        chunk = np.array(list(self.buffer)[:chunk_samples], dtype=np.float32)
        
        # Update last process time
        self.last_process_time = current_time
        self.total_chunks_processed += 1
        
        return chunk
    
    def clear(self) -> None:
        """Clear the buffer."""
        self.buffer.clear()
        self.last_process_time = 0.0
    
    def get_stats(self) -> Dict:
        """Get buffer statistics."""
        return {
            'buffer_size': len(self.buffer),
            'buffer_duration': len(self.buffer) / self.sample_rate,
            'total_chunks_received': self.total_chunks_received,
            'total_chunks_processed': self.total_chunks_processed
        }


class WebSocketConnectionManager:
    """Manages WebSocket connections and audio streams."""
    
    def __init__(self, model):
        """
        Initialize connection manager.
        
        Args:
            model: Initialized detector model
        """
        self.model = model
        self.active_connections: Dict[str, WebSocket] = {}
        self.stream_buffers: Dict[str, AudioStreamBuffer] = {}
        self.connection_metadata: Dict[str, Dict] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        """
        Accept a new WebSocket connection.
        
        Args:
            websocket: WebSocket connection
            client_id: Unique client identifier
        """
        await websocket.accept()
        self.active_connections[client_id] = websocket
        
        # Initialize stream buffer for this client
        self.stream_buffers[client_id] = AudioStreamBuffer(
            sample_rate=16000,  # Default, can be updated from client
            chunk_duration=1.0,
            overlap_duration=0.5
        )
        
        self.connection_metadata[client_id] = {
            'connected_at': time.time(),
            'total_messages': 0,
            'total_detections': 0
        }
        
        logger.info(f"Client {client_id} connected")
    
    def disconnect(self, client_id: str) -> None:
        """
        Remove a WebSocket connection.
        
        Args:
            client_id: Unique client identifier
        """
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.stream_buffers:
            del self.stream_buffers[client_id]
        if client_id in self.connection_metadata:
            del self.connection_metadata[client_id]
        
        logger.info(f"Client {client_id} disconnected")
    
    async def send_message(self, client_id: str, message: Dict) -> bool:
        """
        Send message to a specific client.
        
        Args:
            client_id: Client identifier
            message: Message dictionary to send
            
        Returns:
            True if sent successfully, False otherwise
        """
        if client_id not in self.active_connections:
            return False
        
        try:
            websocket = self.active_connections[client_id]
            await websocket.send_json(message)
            return True
        except Exception as e:
            logger.error(f"Error sending message to {client_id}: {e}")
            return False
    
    async def process_audio_chunk(
        self,
        client_id: str,
        audio_data: np.ndarray,
        sample_rate: int
    ) -> Optional[Dict]:
        """
        Process an audio chunk for a client.
        
        Args:
            client_id: Client identifier
            audio_data: Audio data as numpy array
            sample_rate: Sample rate of the audio
            
        Returns:
            Detection result dictionary or None
        """
        if client_id not in self.stream_buffers:
            return None
        
        buffer = self.stream_buffers[client_id]
        buffer.sample_rate = sample_rate
        buffer.add_chunk(audio_data)
        
        # Get chunk for processing
        processing_chunk = buffer.get_processing_chunk()
        if processing_chunk is None:
            return None
        
        try:
            # Run detection
            result = self.model.detect(processing_chunk, sample_rate)
            
            # Update metadata
            if client_id in self.connection_metadata:
                self.connection_metadata[client_id]['total_detections'] += 1
            
            return result
        except Exception as e:
            logger.error(f"Error processing audio for {client_id}: {e}", exc_info=True)
            raise DetectionError(f"Detection failed: {e}") from e
    
    def get_connection_stats(self, client_id: str) -> Optional[Dict]:
        """Get statistics for a connection."""
        if client_id not in self.connection_metadata:
            return None
        
        stats = self.connection_metadata[client_id].copy()
        if client_id in self.stream_buffers:
            stats.update(self.stream_buffers[client_id].get_stats())
        
        return stats


# Global connection manager
connection_manager: Optional[WebSocketConnectionManager] = None

# FastAPI app
app = FastAPI(title="Deepfake Detection WebSocket Server")

# CORS middleware for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def decode_audio_data(data: str, encoding: str = "base64") -> np.ndarray:
    """
    Decode audio data from various encodings.
    
    Args:
        data: Encoded audio data string
        encoding: Encoding type ('base64', 'json')
        
    Returns:
        Audio data as numpy array
    """
    if encoding == "base64":
        # Decode base64 to bytes, then to numpy array
        audio_bytes = base64.b64decode(data)
        audio_data = np.frombuffer(audio_bytes, dtype=np.float32)
    elif encoding == "json":
        # Parse JSON array
        audio_list = json.loads(data)
        audio_data = np.array(audio_list, dtype=np.float32)
    else:
        raise ValueError(f"Unsupported encoding: {encoding}")
    
    return audio_data


@app.on_event("startup")
async def startup_event():
    """Initialize model on server startup."""
    global connection_manager
    
    logger.info("Starting WebSocket server...")
    
    # Load configuration
    cfg = load_config("config/main.yaml")
    model_name = cfg.get('model_name', 'df_arena')
    model_yaml_path = f"config/{model_name}.yaml"
    model_cfg = load_config(model_yaml_path)
    
    # Initialize model
    logger.info(f"Initializing model: {model_cfg.get('model_class')}")
    model = initialize_model(model_cfg)
    logger.info("Model initialized successfully")
    
    # Initialize connection manager
    connection_manager = WebSocketConnectionManager(model)
    logger.info("WebSocket server ready")


@app.websocket("/ws/detect")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time audio detection.
    
    Message format (client -> server):
    {
        "type": "audio_chunk" | "config" | "ping",
        "client_id": "unique_client_id",
        "audio_data": "base64_encoded_audio" | [audio_array],
        "sample_rate": 16000,
        "encoding": "base64" | "json",
        "timestamp": 1234567890.123
    }
    
    Message format (server -> client):
    {
        "type": "detection_result" | "error" | "pong" | "stats",
        "result": {...},
        "timestamp": 1234567890.123,
        "processing_time_ms": 123.45
    }
    """
    client_id = None
    
    try:
        # Wait for initial connection message with client_id
        initial_message = await websocket.receive_json()
        client_id = initial_message.get('client_id')
        
        if not client_id:
            # Generate client ID if not provided
            import uuid
            client_id = str(uuid.uuid4())
            logger.warning(f"No client_id provided, generated: {client_id}")
        
        # Connect client
        await connection_manager.connect(websocket, client_id)
        
        # Send connection confirmation
        await websocket.send_json({
            "type": "connected",
            "client_id": client_id,
            "timestamp": time.time()
        })
        
        # Process messages
        while True:
            try:
                # Receive message
                message = await websocket.receive_json()
                message_type = message.get('type', 'unknown')
                
                # Update metadata
                if client_id in connection_manager.connection_metadata:
                    connection_manager.connection_metadata[client_id]['total_messages'] += 1
                
                if message_type == "audio_chunk":
                    # Process audio chunk
                    audio_data_str = message.get('audio_data')
                    sample_rate = message.get('sample_rate', 16000)
                    encoding = message.get('encoding', 'base64')
                    
                    if not audio_data_str:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Missing audio_data",
                            "timestamp": time.time()
                        })
                        continue
                    
                    try:
                        # Decode audio data
                        audio_data = decode_audio_data(audio_data_str, encoding)
                        
                        # Process audio
                        start_time = time.time()
                        result = await connection_manager.process_audio_chunk(
                            client_id, audio_data, sample_rate
                        )
                        processing_time = (time.time() - start_time) * 1000
                        
                        # Send result if available
                        if result:
                            await websocket.send_json({
                                "type": "detection_result",
                                "result": result,
                                "timestamp": time.time(),
                                "processing_time_ms": processing_time
                            })
                        
                    except Exception as e:
                        logger.error(f"Error processing audio: {e}", exc_info=True)
                        await websocket.send_json({
                            "type": "error",
                            "message": str(e),
                            "timestamp": time.time()
                        })
                
                elif message_type == "config":
                    # Update client configuration
                    sample_rate = message.get('sample_rate')
                    chunk_duration = message.get('chunk_duration')
                    if client_id in connection_manager.stream_buffers:
                        buffer = connection_manager.stream_buffers[client_id]
                        if sample_rate:
                            buffer.sample_rate = sample_rate
                        if chunk_duration:
                            buffer.chunk_duration = chunk_duration
                    
                    await websocket.send_json({
                        "type": "config_updated",
                        "timestamp": time.time()
                    })
                
                elif message_type == "ping":
                    # Heartbeat
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": time.time()
                    })
                
                elif message_type == "stats":
                    # Get connection statistics
                    stats = connection_manager.get_connection_stats(client_id)
                    await websocket.send_json({
                        "type": "stats",
                        "stats": stats,
                        "timestamp": time.time()
                    })
                
                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Unknown message type: {message_type}",
                        "timestamp": time.time()
                    })
            
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error processing message: {e}", exc_info=True)
                try:
                    await websocket.send_json({
                        "type": "error",
                        "message": str(e),
                        "timestamp": time.time()
                    })
                except:
                    break
    
    except WebSocketDisconnect:
        logger.info(f"Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
    finally:
        if client_id:
            connection_manager.disconnect(client_id)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    if connection_manager is None:
        return {
            "status": "initializing",
            "active_connections": 0,
            "timestamp": time.time()
        }
    return {
        "status": "healthy",
        "active_connections": len(connection_manager.active_connections),
        "timestamp": time.time()
    }


@app.get("/stats")
async def get_stats():
    """Get server statistics."""
    if not connection_manager:
        return {"error": "Server not initialized"}
    
    stats = {
        "active_connections": len(connection_manager.active_connections),
        "connections": {}
    }
    
    for client_id in connection_manager.active_connections.keys():
        stats["connections"][client_id] = connection_manager.get_connection_stats(client_id)
    
    return stats


def launch_websocket_server(
    host: str = "0.0.0.0",
    port: int = 8765,
    log_level: int = logging.INFO
):
    """
    Launch the WebSocket server.
    
    Args:
        host: Server host address
        port: Server port
        log_level: Logging level
    """
    # Setup logging
    setup_logging(log_dir="logs", log_level=log_level)
    logger = logging.getLogger(__name__)
    
    logger.info(f"Starting WebSocket server on {host}:{port}")
    
    import uvicorn
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level=log_level
    )


if __name__ == "__main__":
    launch_websocket_server()

