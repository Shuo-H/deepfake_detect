# WebSocket实时检测快速启动指南

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirement.txt
```

### 2. 配置服务器

编辑 `config/main.yaml`:

```yaml
model_name: df_arena
load_type: websocket
websocket_host: 0.0.0.0
websocket_port: 8765
```

### 3. 启动服务器

```bash
python core.py
```

或直接启动:

```bash
python websocket_server.py
```

服务器将在 `ws://0.0.0.0:8765/ws/detect` 上监听连接。

### 4. 测试连接

#### Python客户端测试

```bash
python client_example.py
```

#### 使用curl测试健康检查

```bash
curl http://localhost:8765/health
```

---

## 📱 移动端集成示例

### JavaScript/Web

```javascript
const client = new AudioDetectionClient('ws://your-server:8765/ws/detect');

client.onDetectionResult = (result) => {
    console.log('检测结果:', result.label, result.score);
};

await client.connect();

// 发送音频块
await client.sendAudioChunk(audioBuffer, 16000);
```

### React Native

```javascript
import { AudioDetectionClient } from './mobile_client_example';

const client = new AudioDetectionClient('ws://your-server:8765/ws/detect');
await client.connect();

// 从麦克风捕获音频并发送
// ... 使用react-native-audio或类似库
```

---

## 🔧 关键配置

### 音频要求

- **采样率**: 16kHz (推荐)
- **格式**: float32数组
- **编码**: base64 或 JSON数组
- **块大小**: 建议1-2秒的音频

### 服务器参数

- **chunk_duration**: 每次处理的音频时长（秒）
- **overlap_duration**: 块之间的重叠时长（秒）
- **min_duration**: 开始处理前的最小音频时长（秒）

---

## 📊 监控

### 健康检查

```bash
curl http://localhost:8765/health
```

### 统计信息

```bash
curl http://localhost:8765/stats
```

---

## 🐛 常见问题

### 连接失败

- 检查防火墙设置
- 确认服务器地址和端口
- 查看服务器日志: `logs/` 目录

### 音频处理失败

- 确保采样率为16kHz
- 检查音频数据格式（float32）
- 验证编码方式

### 性能问题

- 调整音频块大小
- 检查模型是否在GPU上运行
- 监控服务器资源使用

---

## 📚 更多信息

详细文档请参考: `README_WEBSOCKET.md`

