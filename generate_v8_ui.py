"""
MAOS v8.0 - 增强的实时监控可视化
集成Mermaid图表和实时数据展示
"""

import os
from datetime import datetime


def generate_enhanced_dashboard():
    """生成增强的监控看板HTML"""
    
    html_content = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MAOS v8.0 - AI驱动的智能监控</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        header {
            background: rgba(255,255,255,0.95);
            padding: 25px;
            border-radius: 15px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        h1 {
            color: #2d3748;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        .subtitle {
            color: #718096;
            font-size: 1.1em;
        }
        .version-badge {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
            display: inline-block;
            margin-left: 10px;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .card {
            background: rgba(255,255,255,0.95);
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .card h3 {
            color: #2d3748;
            margin-bottom: 15px;
            font-size: 1.3em;
        }
        .stat-value {
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
        }
        .stat-label {
            color: #718096;
            margin-top: 5px;
        }
        .chart-container {
            height: 300px;
            margin-top: 15px;
        }
        .diagram-container {
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-top: 15px;
        }
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
            animation: pulse 2s infinite;
        }
        .status-good {
            background: #48bb78;
        }
        .status-warning {
            background: #ed8936;
        }
        .status-error {
            background: #f56565;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        .tab {
            background: white;
            border: none;
            padding: 12px 24px;
            border-radius: 10px;
            cursor: pointer;
            font-weight: 600;
            color: #4a5568;
            transition: all 0.3s;
        }
        .tab.active {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .tab-content {
            display: none;
        }
        .tab-content.active {
            display: block;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>
                🚀 MAOS v8.0 
                <span class="version-badge">v8.0 (AI)</span>
            </h1>
            <div class="subtitle">
                <span class="status-indicator status-good"></span>
                AI驱动的多Agent编排系统 - 实时监控中心
            </div>
            <div id="current-time" style="margin-top: 10px; color: #718096;"></div>
        </header>

        <div class="tabs">
            <button class="tab active" onclick="showTab('overview')">📊 概览</button>
            <button class="tab" onclick="showTab('ai')">🤖 AI调度</button>
            <button class="tab" onclick="showTab('collaboration')">🤝 Agent协作</button>
            <button class="tab" onclick="showTab('architecture')">🏗️ 架构</button>
        </div>

        <!-- 概览 -->
        <div id="overview" class="tab-content active">
            <div class="grid">
                <div class="card">
                    <h3>📋 任务统计</h3>
                    <div class="stat-value" id="total-tasks">1,234</div>
                    <div class="stat-label">总任务数</div>
                    <div class="stat-value" style="color: #48bb78; font-size: 1.5em; margin-top: 15px;" id="completed-tasks">987</div>
                    <div class="stat-label">已完成</div>
                </div>
                <div class="card">
                    <h3>🤖 活跃Agent</h3>
                    <div class="stat-value" id="active-agents">15</div>
                    <div class="stat-label">在线</div>
                    <div class="stat-value" style="color: #667eea; font-size: 1.5em; margin-top: 15px;" id="ai-decisions">4,521</div>
                    <div class="stat-label">AI决策次数</div>
                </div>
                <div class="card">
                    <h3>⚡ 性能</h3>
                    <div class="stat-value" id="throughput">8,234</div>
                    <div class="stat-label">吞吐量 (tasks/s)</div>
                    <div class="stat-value" style="color: #48bb78; font-size: 1.5em; margin-top: 15px;" id="success-rate">98.5%</div>
                    <div class="stat-label">成功率</div>
                </div>
                <div class="card">
                    <h3>🔌 插件</h3>
                    <div class="stat-value" id="plugin-count">8</div>
                    <div class="stat-label">已安装</div>
                    <div class="stat-value" style="color: #667eea; font-size: 1.5em; margin-top: 15px;" id="active-plugins">6</div>
                    <div class="stat-label">活跃</div>
                </div>
            </div>

            <div class="grid">
                <div class="card">
                    <h3>📈 性能趋势</h3>
                    <div class="chart-container">
                        <canvas id="performance-chart"></canvas>
                    </div>
                </div>
                <div class="card">
                    <h3>🏷️ 任务状态</h3>
                    <div class="chart-container">
                        <canvas id="status-chart"></canvas>
                    </div>
                </div>
            </div>
        </div>

        <!-- AI调度 -->
        <div id="ai" class="tab-content">
            <div class="grid">
                <div class="card">
                    <h3>🧠 AI调度状态</h3>
                    <p style="color: #48bb78; font-size: 1.2em; margin: 15px 0;">
                        <span class="status-indicator status-good"></span> 正常运行
                    </p>
                    <p><strong>策略:</strong> Predictive (预测性调度)</p>
                    <p><strong>调度准确率:</strong> 94%</p>
                    <p><strong>优化次数:</strong> 128</p>
                </div>
                <div class="card">
                    <h3>🎯 Agent分配</h3>
                    <div class="chart-container">
                        <canvas id="agent-chart"></canvas>
                    </div>
                </div>
            </div>
            <div class="card">
                <h3>🧠 AI调度器架构</h3>
                <div class="diagram-container">
                    <pre class="mermaid">
graph TD
    A[用户请求] --> B[AI调度器]
    B --> C[Agent选择<br/>基于历史数据]
    B --> D[任务预测<br/>基于学习]
    B --> E[负载均衡]
    C --> F[Agent 1]
    C --> G[Agent 2]
    C --> H[Agent 3]
    I[性能数据] --> D
    D --> B
    style B fill:#667eea,color:#fff
    style I fill:#48bb78,color:#fff
                    </pre>
                </div>
            </div>
        </div>

        <!-- Agent协作 -->
        <div id="collaboration" class="tab-content">
            <div class="card">
                <h3>🤝 协作流程</h3>
                <div class="diagram-container">
                    <pre class="mermaid">
sequenceDiagram
    participant C as Coordinator
    participant A1 as Agent 1
    participant A2 as Agent 2
    participant A3 as Agent 3
    
    C->>A1: 任务公告
    A1->>C: 竞标
    C->>A2: 任务公告
    A2->>C: 竞标
    C->>A3: 任务公告
    A3->>C: 竞标
    
    Note over C: AI选择最优组合
    C->>A1: 接受 (role_1)
    C->>A2: 接受 (role_2)
    
    A1->>A2: 数据共享
    A2->>A1: 状态同步
    A1->>C: 结果1
    A2->>C: 结果2
                    </pre>
                </div>
            </div>
            <div class="grid">
                <div class="card">
                    <h3>📊 协作统计</h3>
                    <p><strong>活跃协作:</strong> 5</p>
                    <p><strong>总消息:</strong> 1,234</p>
                    <p><strong>平均响应:</strong> 25ms</p>
                </div>
                <div class="card">
                    <h3>📊 总线状态</h3>
                    <p><strong>注册Agent:</strong> 8</p>
                    <p><strong>广播消息:</strong> 456</p>
                    <p><strong>直连消息:</strong> 778</p>
                </div>
            </div>
        </div>

        <!-- 架构 -->
        <div id="architecture" class="tab-content">
            <div class="card">
                <h3>🏗️ MAOS v8.0 架构</h3>
                <div class="diagram-container">
                    <pre class="mermaid">
graph TB
    subgraph "用户界面层"
        UI[Web UI]
        API[REST API]
        WS[WebSocket]
    end
    
    subgraph "AI智能层"
        AIS[AI调度器]
        PRED[预测引擎]
        OPT[优化器]
    end
    
    subgraph "协作层"
        BUS[协作总线]
        AG[Agent团队]
    end
    
    subgraph "插件系统"
        PM[插件管理器]
        REG[插件注册表]
        EXTS[扩展]
    end
    
    subgraph "核心服务"
        ORCH[编排器]
        TM[任务管理]
        CACHE[缓存]
    end
    
    subgraph "数据层"
        DB[(存储)]
        MET[指标]
    end
    
    UI --> API
    UI --> WS
    API --> AIS
    WS --> BUS
    AIS --> ORCH
    AIS --> AG
    BUS --> AG
    PM --> REG
    ORCH --> TM
    ORCH --> CACHE
    TM --> DB
    CACHE --> DB
    TM --> MET
    </pre>
                </div>
            </div>
            
            <div class="grid">
                <div class="card">
                    <h3>🚀 核心服务状态</h3>
                    <p><span class="status-indicator status-good"></span> 编排器: 正常</p>
                    <p><span class="status-indicator status-good"></span> 任务管理: 正常</p>
                    <p><span class="status-indicator status-good"></span> 缓存系统: 正常</p>
                    <p><span class="status-indicator status-good"></span> AI调度器: 正常</p>
                </div>
                <div class="card">
                    <h3>📚 版本信息</h3>
                    <p><strong>MAOS:</strong> v8.0.0</p>
                    <p><strong>Python:</strong> 3.9+</p>
                    <p><strong>API:</strong> v2.0</p>
                    <p><strong>SDK:</strong> 1.0</p>
                </div>
            </div>
        </div>
    </div>

    <script>
        // 初始化Mermaid
        mermaid.initialize({ startOnLoad: true, theme: 'default' });
        
        // 更新时间
        function updateTime() {
            const now = new Date();
            document.getElementById('current-time').textContent = '当前时间: ' + now.toLocaleString('zh-CN');
        }
        updateTime();
        setInterval(updateTime, 1000);
        
        // Tab切换
        function showTab(tabName) {
            const contents = document.querySelectorAll('.tab-content');
            const tabs = document.querySelectorAll('.tab');
            contents.forEach(c => c.classList.remove('active'));
            tabs.forEach(t => t.classList.remove('active'));
            
            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');
            
            // 重新渲染Mermaid图表
            mermaid.init();
        }
        
        // 性能图表
        const perfCtx = document.getElementById('performance-chart').getContext('2d');
        new Chart(perfCtx, {
            type: 'line',
            data: {
                labels: ['10:00', '10:05', '10:10', '10:15', '10:20', '10:25'],
                datasets: [{
                    label: '吞吐量',
                    data: [7500, 7800, 8000, 8200, 8100, 8234],
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: { responsive: true, maintainAspectRatio: false }
        });
        
        // 状态图表
        const statusCtx = document.getElementById('status-chart').getContext('2d');
        new Chart(statusCtx, {
            type: 'doughnut',
            data: {
                labels: ['完成', '运行中', '等待', '失败'],
                datasets: [{
                    data: [987, 124, 89, 34],
                    backgroundColor: ['#48bb78', '#667eea', '#ed8936', '#f56565']
                }]
            },
            options: { responsive: true, maintainAspectRatio: false }
        });
        
        // Agent图表
        const agentCtx = document.getElementById('agent-chart').getContext('2d');
        new Chart(agentCtx, {
            type: 'bar',
            data: {
                labels: ['Agent 1', 'Agent 2', 'Agent 3', 'Agent 4', 'Agent 5'],
                datasets: [{
                    label: '已分配任务',
                    data: [25, 18, 22, 15, 18],
                    backgroundColor: '#667eea'
                }]
            },
            options: { responsive: true, maintainAspectRatio: false }
        });
        
        // 模拟实时更新
        setInterval(() => {
            const totalTasks = document.getElementById('total-tasks');
            const current = parseInt(totalTasks.textContent.replace(',', ''));
            totalTasks.textContent = (current + Math.floor(Math.random() * 3)).toLocaleString();
        }, 5000);
    </script>
</body>
</html>
"""
    
    # 保存文件
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "maos_v8_dashboard.html")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"✅ 增强的监控看板已生成: {file_path}")
    return file_path


if __name__ == "__main__":
    generate_enhanced_dashboard()
