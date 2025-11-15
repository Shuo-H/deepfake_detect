/**
 * JavaScript WebSocket client example for mobile applications.
 * 
 * This can be used in React Native, Ionic, or web-based mobile apps.
 * 
 * Usage:
 *   const client = new AudioDetectionClient('ws://your-hpc-server:8765/ws/detect');
 *   await client.connect();
 *   await client.sendAudioChunk(audioBuffer, sampleRate);
 */

class AudioDetectionClient {
    /**
     * Initialize the WebSocket client.
     * @param {string} serverUrl - WebSocket server URL
     */
    constructor(serverUrl) {
        this.serverUrl = serverUrl;
        this.ws = null;
        this.clientId = this.generateClientId();
        this.connected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
    }

    /**
     * Generate a unique client ID.
     * @returns {string} Client ID
     */
    generateClientId() {
        return 'client_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    /**
     * Connect to the WebSocket server.
     * @returns {Promise<boolean>} True if connected successfully
     */
    async connect() {
        return new Promise((resolve, reject) => {
            try {
                this.ws = new WebSocket(this.serverUrl);

                this.ws.onopen = () => {
                    console.log('WebSocket connected');
                    this.connected = true;
                    this.reconnectAttempts = 0;

                    // Send initial connection message
                    this.ws.send(JSON.stringify({
                        type: 'connect',
                        client_id: this.clientId,
                        timestamp: Date.now() / 1000
                    }));

                    resolve(true);
                };

                this.ws.onmessage = (event) => {
                    const data = JSON.parse(event.data);
                    this.handleMessage(data);
                };

                this.ws.onerror = (error) => {
                    console.error('WebSocket error:', error);
                    this.connected = false;
                    reject(error);
                };

                this.ws.onclose = () => {
                    console.log('WebSocket closed');
                    this.connected = false;
                    this.attemptReconnect();
                };

            } catch (error) {
                console.error('Connection error:', error);
                reject(error);
            }
        });
    }

    /**
     * Handle incoming messages from server.
     * @param {Object} data - Message data
     */
    handleMessage(data) {
        switch (data.type) {
            case 'connected':
                console.log('Server confirmed connection:', data.client_id);
                if (this.onConnected) {
                    this.onConnected(data);
                }
                break;

            case 'detection_result':
                console.log('Detection result:', data.result);
                if (this.onDetectionResult) {
                    this.onDetectionResult(data.result, data);
                }
                break;

            case 'error':
                console.error('Server error:', data.message);
                if (this.onError) {
                    this.onError(data.message);
                }
                break;

            case 'pong':
                if (this.onPong) {
                    this.onPong();
                }
                break;

            case 'stats':
                if (this.onStats) {
                    this.onStats(data.stats);
                }
                break;

            default:
                console.log('Unknown message type:', data.type);
        }
    }

    /**
     * Attempt to reconnect to the server.
     */
    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
            
            setTimeout(() => {
                this.connect().catch(err => {
                    console.error('Reconnection failed:', err);
                });
            }, this.reconnectDelay * this.reconnectAttempts);
        }
    }

    /**
     * Convert AudioBuffer to base64 encoded string.
     * @param {AudioBuffer} audioBuffer - Audio buffer
     * @returns {string} Base64 encoded audio data
     */
    audioBufferToBase64(audioBuffer) {
        const float32Array = audioBuffer.getChannelData(0); // Get first channel
        const bytes = new Uint8Array(float32Array.buffer);
        
        // Convert to base64
        let binary = '';
        for (let i = 0; i < bytes.length; i++) {
            binary += String.fromCharCode(bytes[i]);
        }
        return btoa(binary);
    }

    /**
     * Convert AudioBuffer to JSON array.
     * @param {AudioBuffer} audioBuffer - Audio buffer
     * @returns {Array} Audio data as array
     */
    audioBufferToArray(audioBuffer) {
        const float32Array = audioBuffer.getChannelData(0);
        return Array.from(float32Array);
    }

    /**
     * Send an audio chunk for detection.
     * @param {AudioBuffer|Float32Array|Array} audioData - Audio data
     * @param {number} sampleRate - Sample rate in Hz
     * @param {string} encoding - Encoding method ('base64' or 'json')
     * @returns {Promise<Object|null>} Detection result or null
     */
    async sendAudioChunk(audioData, sampleRate = 16000, encoding = 'json') {
        if (!this.connected || !this.ws) {
            console.error('Not connected to server');
            return null;
        }

        return new Promise((resolve, reject) => {
            try {
                // Convert audio data to string
                let audioDataStr;
                if (audioData instanceof AudioBuffer) {
                    if (encoding === 'base64') {
                        audioDataStr = this.audioBufferToBase64(audioData);
                    } else {
                        audioDataStr = this.audioBufferToArray(audioData);
                    }
                } else if (audioData instanceof Float32Array) {
                    if (encoding === 'base64') {
                        const bytes = new Uint8Array(audioData.buffer);
                        let binary = '';
                        for (let i = 0; i < bytes.length; i++) {
                            binary += String.fromCharCode(bytes[i]);
                        }
                        audioDataStr = btoa(binary);
                    } else {
                        audioDataStr = Array.from(audioData);
                    }
                } else if (Array.isArray(audioData)) {
                    audioDataStr = audioData;
                } else {
                    throw new Error('Unsupported audio data type');
                }

                // Create message
                const message = {
                    type: 'audio_chunk',
                    client_id: this.clientId,
                    audio_data: audioDataStr,
                    sample_rate: sampleRate,
                    encoding: encoding,
                    timestamp: Date.now() / 1000
                };

                // Set up one-time result handler
                const originalHandler = this.onDetectionResult;
                this.onDetectionResult = (result, fullData) => {
                    if (originalHandler) {
                        originalHandler(result, fullData);
                    }
                    resolve(result);
                    this.onDetectionResult = originalHandler;
                };

                // Set timeout
                setTimeout(() => {
                    if (this.onDetectionResult === originalHandler) {
                        this.onDetectionResult = originalHandler;
                        resolve(null);
                    }
                }, 10000); // 10 second timeout

                // Send message
                this.ws.send(JSON.stringify(message));

            } catch (error) {
                console.error('Error sending audio chunk:', error);
                reject(error);
            }
        });
    }

    /**
     * Send ping to server.
     * @returns {Promise<boolean>} True if pong received
     */
    async ping() {
        if (!this.connected || !this.ws) {
            return false;
        }

        return new Promise((resolve) => {
            const originalHandler = this.onPong;
            this.onPong = () => {
                if (originalHandler) {
                    originalHandler();
                }
                resolve(true);
                this.onPong = originalHandler;
            };

            this.ws.send(JSON.stringify({
                type: 'ping',
                timestamp: Date.now() / 1000
            }));

            // Timeout after 2 seconds
            setTimeout(() => {
                if (this.onPong === originalHandler) {
                    this.onPong = originalHandler;
                    resolve(false);
                }
            }, 2000);
        });
    }

    /**
     * Request connection statistics.
     */
    requestStats() {
        if (!this.connected || !this.ws) {
            return;
        }

        this.ws.send(JSON.stringify({
            type: 'stats',
            timestamp: Date.now() / 1000
        }));
    }

    /**
     * Update client configuration.
     * @param {Object} config - Configuration object
     */
    updateConfig(config) {
        if (!this.connected || !this.ws) {
            return;
        }

        this.ws.send(JSON.stringify({
            type: 'config',
            ...config,
            timestamp: Date.now() / 1000
        }));
    }

    /**
     * Disconnect from server.
     */
    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        this.connected = false;
        console.log('Disconnected from server');
    }
}

// Example usage for React Native or mobile web app
async function exampleUsage() {
    const client = new AudioDetectionClient('ws://your-hpc-server:8765/ws/detect');

    // Set up event handlers
    client.onConnected = (data) => {
        console.log('Connected:', data);
    };

    client.onDetectionResult = (result, fullData) => {
        console.log('Detection:', result.label, 'Confidence:', result.score);
        // Update UI with result
        updateUI(result);
    };

    client.onError = (error) => {
        console.error('Error:', error);
    };

    // Connect
    await client.connect();

    // Example: Capture audio from microphone and send chunks
    // This would be implemented using Web Audio API or React Native audio libraries
    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
            const audioContext = new AudioContext({ sampleRate: 16000 });
            const source = audioContext.createMediaStreamSource(stream);
            const processor = audioContext.createScriptProcessor(4096, 1, 1);

            processor.onaudioprocess = async (e) => {
                const inputBuffer = e.inputBuffer;
                const audioData = inputBuffer.getChannelData(0);

                // Send chunk for detection
                await client.sendAudioChunk(audioData, 16000, 'json');
            };

            source.connect(processor);
            processor.connect(audioContext.destination);
        })
        .catch(err => {
            console.error('Error accessing microphone:', err);
        });
}

// Export for use in modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AudioDetectionClient;
}

