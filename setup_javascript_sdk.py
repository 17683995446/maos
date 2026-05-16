"""
MAOS v7.0 - SDK for JavaScript/TypeScript
Browser和Node.js兼容
"""

sdk_code = """
/**
 * MAOS v7.0 JavaScript SDK
 * Browser and Node.js compatible
 */

class MAOSClient {
    constructor(options = {}) {
        this.baseUrl = options.baseUrl || 'http://localhost:8000';
        this.wsUrl = options.wsUrl || 'ws://localhost:8000/ws';
        this.taskManager = new TaskManager(this);
        this.metrics = new MetricsManager(this);
        this.websocket = null;
        this.subscriptions = new Map();
    }

    // HTTP Requests
    async request(method, endpoint, data = null) {
        const url = `${this.baseUrl}${endpoint}`;
        const options = {
            method,
            headers: { 'Content-Type': 'application/json' }
        };
        
        if (data) {
            options.body = JSON.stringify(data);
        }
        
        const response = await fetch(url, options);
        return response.json();
    }

    // System API
    async getSystemInfo() {
        return this.request('GET', '/api/v1/system/info');
    }

    async getStatistics() {
        return this.request('GET', '/api/v1/system/statistics');
    }

    // WebSocket
    async connect() {
        return new Promise((resolve, reject) => {
            this.websocket = new WebSocket(this.wsUrl);
            
            this.websocket.onopen = () => {
                console.log('Connected to MAOS');
                resolve();
            };
            
            this.websocket.onerror = (error) => {
                console.error('WebSocket error:', error);
                reject(error);
            };
            
            this.websocket.onmessage = (event) => {
                const message = JSON.parse(event.data);
                this._handleMessage(message);
            };
        });
    }

    _handleMessage(message) {
        const handlers = this.subscriptions.get(message.event_type);
        if (handlers) {
            handlers.forEach(handler => handler(message.data));
        }
    }

    subscribe(eventType, handler) {
        if (!this.subscriptions.has(eventType)) {
            this.subscriptions.set(eventType, []);
        }
        this.subscriptions.get(eventType).push(handler);
    }

    unsubscribe(eventType, handler) {
        const handlers = this.subscriptions.get(eventType);
        if (handlers) {
            const index = handlers.indexOf(handler);
            if (index > -1) {
                handlers.splice(index, 1);
            }
        }
    }

    async sendEvent(eventType, data) {
        if (!this.websocket || this.websocket.readyState !== WebSocket.OPEN) {
            throw new Error('WebSocket not connected');
        }
        
        const message = {
            event_type: eventType,
            data,
            timestamp: new Date().toISOString(),
            message_id: this._generateId()
        };
        
        this.websocket.send(JSON.stringify(message));
    }

    _generateId() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }

    disconnect() {
        if (this.websocket) {
            this.websocket.close();
            this.websocket = null;
        }
    }
}

// Task Manager
class TaskManager {
    constructor(client) {
        this.client = client;
    }

    async create(task) {
        return this.client.request('POST', '/api/v1/tasks', task);
    }

    async list(status = null) {
        const endpoint = status ? `/api/v1/tasks?status=${status}` : '/api/v1/tasks';
        return this.client.request('GET', endpoint);
    }

    async get(taskId) {
        return this.client.request('GET', `/api/v1/tasks/${taskId}`);
    }

    async update(taskId, updates) {
        return this.client.request('PATCH', `/api/v1/tasks/${taskId}`, updates);
    }

    async delete(taskId) {
        return this.client.request('DELETE', `/api/v1/tasks/${taskId}`);
    }
}

// Metrics Manager
class MetricsManager {
    constructor(client) {
        this.client = client;
    }

    async record(name, value, type = 'gauge') {
        return this.client.request('POST', '/api/v1/metrics', {
            name, value, metric_type: type
        });
    }

    async get(limit = 100) {
        return this.client.request('GET', `/api/v1/metrics?limit=${limit}`);
    }
}

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { MAOSClient, TaskManager, MetricsManager };
}
"""

import os

# 创建JavaScript SDK文件
sdk_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'sdk', 'javascript')
os.makedirs(sdk_dir, exist_ok=True)

# 写入SDK代码
sdk_file = os.path.join(sdk_dir, 'maos-sdk.js')
with open(sdk_file, 'w', encoding='utf-8') as f:
    f.write(sdk_code)

print(f"✅ JavaScript SDK created: {sdk_file}")

# 创建README
readme_content = """# MAOS JavaScript SDK

Browser和Node.js兼容的MAOS客户端SDK

## 安装

```bash
# npm
npm install maos-sdk

# yarn
yarn add maos-sdk

# 直接引入
<script src="maos-sdk.js"></script>
```

## 使用

```javascript
import { MAOSClient } from 'maos-sdk';

// 创建客户端
const client = new MAOSClient({
    baseUrl: 'http://localhost:8000',
    wsUrl: 'ws://localhost:8000/ws'
});

// 获取系统信息
const info = await client.getSystemInfo();
console.log(info);

// 创建任务
const task = await client.taskManager.create({
    name: 'My Task',
    requirements: ['data_processing']
});

// WebSocket实时更新
await client.connect();
client.subscribe('task:created', (data) => {
    console.log('New task:', data);
});
```

## API

### MAOSClient

- `getSystemInfo()` - 获取系统信息
- `getStatistics()` - 获取统计信息
- `connect()` - 连接WebSocket
- `disconnect()` - 断开连接
- `subscribe(eventType, handler)` - 订阅事件
- `unsubscribe(eventType, handler)` - 取消订阅

### TaskManager

- `create(task)` - 创建任务
- `list(status)` - 列出任务
- `get(taskId)` - 获取任务详情
- `update(taskId, updates)` - 更新任务
- `delete(taskId)` - 删除任务

### MetricsManager

- `record(name, value, type)` - 记录指标
- `get(limit)` - 获取指标

## 示例

见 `examples/` 目录
"""

readme_file = os.path.join(sdk_dir, 'README.md')
with open(readme_file, 'w', encoding='utf-8') as f:
    f.write(readme_content)

print(f"✅ README created: {readme_file}")
