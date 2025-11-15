# WebSocket实时音频检测服务

本文档说明如何使用WebSocket服务进行实时音频深度伪造检测。

## 📋 目录

1. [概述](#概述)
2. [服务器端](#服务器端)
3. [客户端](#客户端)
4. [协议说明](#协议说明)
5. [部署指南](#部署指南)

---

## 🎯 概述

WebSocket服务允许移动设备或客户端应用实时发送音频片段到HPC服务器进行深度伪造检测。系统支持：

- ✅ 实时音频流处理
- ✅ 多客户端并发连接
- ✅ 自动音频缓冲和分块处理
- ✅ 低延迟检测结果返回
- ✅ 连接管理和统计

---

## 🖥️ 服务器端

### 启动服务器

#### 方式1: 通过配置文件

修改 `config/main.yaml`:

```yaml
model_name: df_arena
load_type: websocket  # 使用websocket模式
websocket_host: 0.0.0.0
websocket_port: 8765
```

然后运行:

```bash
python core.py
```

#### 方式2: 直接启动

```bash
python websocket_server.py
```

或指定端口:

```python
from websocket_server import launch_websocket_server
launch_websocket_server(host="0.0.0.0", port=8765)
```

### 服务器端点

- **WebSocket**: `ws://host:port/ws/detect` - 音频检测端点
- **健康检查**: `http://host:port/health` - 服务器健康状态
- **统计信息**: `http://host:port/stats` - 连接和性能统计

### 服务器配置

服务器会自动：
1. 加载模型配置
2. 初始化检测模型
3. 管理WebSocket连接
4. 缓冲和处理音频流

---

## 📱 客户端

### Python客户端

使用 `client_example.py` 作为参考：

```python
from client_example import AudioDetectionClient
import asyncio

async def main():
    client = AudioDetectionClient("ws://your-server:8765/ws/detect")
    
    # 连接
    await client.connect()
    
    # 发送音频文件
    await client.send_audio_file("audio.wav")
    
    # 或发送音频块
    import numpy as np
    audio_chunk = np.random.randn(16000).astype(np.float32)
    result = await client.send_audio_chunk(audio_chunk, sample_rate=16000)
    print(f"Result: {result}")
    
    # 断开连接
    await client.disconnect()

asyncio.run(main())
```

### JavaScript/移动端客户端

使用 `mobile_client_example.js` 作为参考：

```javascript
const client = new AudioDetectionClient('ws://your-server:8765/ws/detect');

// 设置事件处理器
client.onDetectionResult = (result) => {
    console.log('Detection:', result.label, result.score);
    // 更新UI
};

// 连接
await client.connect();

// 发送音频块
const audioBuffer = ...; // 从麦克风或文件获取
await client.sendAudioChunk(audioBuffer, 16000, 'json');
```

### React Native示例

```javascript
import { AudioDetectionClient } from './mobile_client_example';

// 在组件中使用
const [client, setClient] = useState(null);

useEffect(() => {
    const wsClient = new AudioDetectionClient('ws://your-server:8765/ws/detect');
    wsClient.onDetectionResult = (result) => {
        setDetectionResult(result);
    };
    wsClient.connect().then(() => {
        setClient(wsClient);
    });
    
    return () => {
        wsClient.disconnect();
    };
}, []);

// 发送音频
const sendAudio = async (audioData) => {
    if (client) {
        await client.sendAudioChunk(audioData, 16000);
    }
};
```

---

## 📡 协议说明

### 客户端 -> 服务器消息格式

#### 连接消息
```json
{
    "type": "connect",
    "client_id": "unique_client_id",
    "timestamp": 1234567890.123
}
```

#### 音频块消息
```json
{
    "type": "audio_chunk",
    "client_id": "unique_client_id",
    "audio_data": "base64_encoded_data" | [audio_array],
    "sample_rate": 16000,
    "encoding": "base64" | "json",
    "timestamp": 1234567890.123
}
```

#### 配置更新
```json
{
    "type": "config",
    "sample_rate": 16000,
    "chunk_duration": 1.0,
    "timestamp": 1234567890.123
}
```

#### 心跳
```json
{
    "type": "ping",
    "timestamp": 1234567890.123
}
```

#### 统计请求
```json
{
    "type": "stats",
    "timestamp": 1234567890.123
}
```

### 服务器 -> 客户端消息格式

#### 连接确认
```json
{
    "type": "connected",
    "client_id": "unique_client_id",
    "timestamp": 1234567890.123
}
```

#### 检测结果
```json
{
    "type": "detection_result",
    "result": {
        "label": "spoof" | "bonafide",
        "score": 0.95,
        "is_spoof": true,
        "all_scores": {
            "spoof": 0.95,
            "bonafide": 0.05
        },
        "logits": [...]
    },
    "timestamp": 1234567890.123,
    "processing_time_ms": 123.45
}
```

#### 错误消息
```json
{
    "type": "error",
    "message": "Error description",
    "timestamp": 1234567890.123
}
```

#### 心跳响应
```json
{
    "type": "pong",
    "timestamp": 1234567890.123
}
```

#### 统计信息
```json
{
    "type": "stats",
    "stats": {
        "connected_at": 1234567890.123,
        "total_messages": 100,
        "total_detections": 50,
        "buffer_size": 16000,
        "buffer_duration": 1.0
    },
    "timestamp": 1234567890.123
}
```

---

## 🚀 部署指南

### HPC服务器部署

1. **安装依赖**:
```bash
pip install -r requirement.txt
```

2. **配置防火墙**:
```bash
# 开放WebSocket端口
sudo ufw allow 8765/tcp
```

3. **使用systemd服务** (可选):
```ini
[Unit]
Description=Deepfake Detection WebSocket Server
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/deepfake_detect
ExecStart=/usr/bin/python3 websocket_server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

4. **使用Nginx反向代理** (推荐):
```nginx
map $http_upgrade $connection_upgrade {
    default upgrade;
    '' close;
}

server {
    listen 80;
    server_name your-domain.com;

    location /ws/ {
        proxy_pass http://127.0.0.1:8765;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 86400;
    }
}
```

### 移动端集成

#### iOS (Swift)
```swift
import Starscream

class AudioDetectionClient {
    var socket: WebSocket?
    
    func connect() {
        let url = URL(string: "ws://your-server:8765/ws/detect")!
        socket = WebSocket(request: URLRequest(url: url))
        socket?.connect()
    }
    
    func sendAudioChunk(_ audioData: Data, sampleRate: Int) {
        let base64 = audioData.base64EncodedString()
        let message: [String: Any] = [
            "type": "audio_chunk",
            "client_id": clientId,
            "audio_data": base64,
            "sample_rate": sampleRate,
            "encoding": "base64",
            "timestamp": Date().timeIntervalSince1970
        ]
        socket?.write(string: jsonString)
    }
}
```

#### Android (Kotlin)
```kotlin
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.WebSocket

class AudioDetectionClient {
    private var webSocket: WebSocket? = null
    
    fun connect() {
        val client = OkHttpClient()
        val request = Request.Builder()
            .url("ws://your-server:8765/ws/detect")
            .build()
        webSocket = client.newWebSocket(request, object : WebSocketListener() {
            override fun onMessage(webSocket: WebSocket, text: String) {
                // Handle message
            }
        })
    }
    
    fun sendAudioChunk(audioData: ByteArray, sampleRate: Int) {
        val base64 = Base64.encodeToString(audioData, Base64.NO_WRAP)
        val message = JSONObject().apply {
            put("type", "audio_chunk")
            put("client_id", clientId)
            put("audio_data", base64)
            put("sample_rate", sampleRate)
            put("encoding", "base64")
            put("timestamp", System.currentTimeMillis() / 1000.0)
        }
        webSocket?.send(message.toString())
    }
}
```

---

## 🔧 性能优化

### 服务器端

1. **批处理**: 调整 `chunk_duration` 和 `overlap_duration`
2. **模型优化**: 使用量化模型或ONNX Runtime
3. **GPU加速**: 确保模型在GPU上运行
4. **连接池**: 限制最大并发连接数

### 客户端

1. **音频压缩**: 使用合适的编码格式
2. **采样率**: 使用16kHz采样率（模型要求）
3. **块大小**: 优化音频块大小以平衡延迟和效率
4. **重连机制**: 实现自动重连和错误恢复

---

## 🐛 故障排除

### 连接问题

- 检查防火墙设置
- 验证服务器地址和端口
- 检查网络连接

### 音频处理问题

- 确保采样率为16kHz
- 检查音频数据格式（float32）
- 验证编码方式（base64或json）

### 性能问题

- 监控服务器资源使用
- 检查模型推理时间
- 优化音频块大小

---

## 📞 支持

如有问题，请查看：
- 服务器日志: `logs/` 目录
- 健康检查: `http://server:8765/health`
- 统计信息: `http://server:8765/stats`

