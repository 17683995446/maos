# MAOS v3.0.0 系统架构可视化仪表板

## 📊 概述

这是一个交互式的MAOS系统可视化仪表板，展示：
- 系统架构图
- 任务流程图
- Agent交互时序图
- 类关系图
- 项目状态和性能指标
- 测试结果展示
- 文件修改历史

## 🚀 快速开始

### 方式一：直接打开HTML文件

```bash
# 在浏览器中直接打开
open /workspace/maos_dashboard.html
```

### 方式二：使用Python启动本地服务器（推荐）

```bash
# 简单HTTP服务器
cd /workspace
python3 -m http.server 8000

# 然后访问:
# http://localhost:8000/maos_dashboard.html
```

### 方式三：使用启动脚本

```bash
# 赋予执行权限
chmod +x /workspace/start_dashboard.sh

# 启动
/workspace/start_dashboard.sh
```

### 方式四：使用文件监控脚本（自动更新）

```bash
# 赋予执行权限
chmod +x /workspace/watch_and_serve.py

# 启动监控和服务器
python3 /workspace/watch_and_serve.py
```

## 📈 包含的图表

### 1. 架构图
展示MAOS系统的完整分层架构：
- 用户层 (Client, Web UI)
- API层 (FastAPI, WebSocket)
- 编排层 (Orchestrator, TaskManager, Workflow)
- Agent层 (各种Agent实现)
- 核心层 (基类、回调、事件)
- 基础设施层 (存储、分析、多租户、指标)

### 2. 流程图
展示任务从创建到完成的完整流程：
- 任务创建和验证
- Agent选择和分配
- 任务执行和流式响应
- 状态更新和指标记录

### 3. 时序图
展示系统各组件之间的交互序列：
- 客户端请求
- Orchestrator处理
- Agent任务执行
- 存储和指标记录

### 4. 类图
展示核心类和它们之间的关系：
- Agent基类和具体实现
- OrchestratorService
- TaskManager
- AnalyticsEngine
- 存储接口等

## 🎨 特性

- **Mermaid图表**: 使用Mermaid JS库绘制专业的UML图表
- **Chart.js**: 展示性能指标雷达图
- **响应式设计**: 支持各种屏幕尺寸
- **标签页切换**: 快速切换不同图表
- **实时更新**: 显示最后更新时间
- **刷新按钮**: 手动刷新数据

## 📁 文件结构

```
/workspace/
├── maos_dashboard.html          # 主仪表板页面
├── start_dashboard.sh           # 快速启动脚本
├── watch_and_serve.py           # 文件监控和自动更新脚本
├── maos/                        # MAOS包
│   ├── core/                    # 核心模块
│   ├── orchestration/           # 编排模块
│   ├── agents/                  # Agent实现
│   ├── storage/                 # 存储模块
│   ├── analytics/               # 分析模块
│   └── multi_tenancy/           # 多租户模块
└── legacy/                      # Legacy版本
```

## 🔧 技术栈

- HTML5
- CSS3 (渐变、动画、响应式)
- JavaScript (ES6+)
- Mermaid v10 (UML图表)
- Chart.js (数据可视化)

## 📊 监控功能

### 文件监控脚本 (watch_and_serve.py)

- 监控`/workspace/maos/`、`/workspace/legacy/`等目录
- 检测文件变化自动更新
- 启动本地HTTP服务器
- 每2秒检查一次文件变化

### 手动刷新

- 点击页面右下角的刷新按钮
- 页面会自动更新最后更新时间

## 🎯 使用场景

1. **系统设计**: 了解MAOS整体架构
2. **开发调试**: 查看类关系和交互流程
3. **代码审查**: 了解模块依赖关系
4. **文档编写**: 参考架构图和流程图
5. **演示展示**: 向团队展示系统架构

## 📝 注意事项

- 需要网络连接加载CDN库 (Mermaid, Chart.js)
- 推荐使用现代浏览器 (Chrome, Firefox, Safari, Edge)
- 本地服务器需要在8000端口（可修改）

## 🔄 自动更新机制

每次修改以下文件时，重新刷新网页即可看到更新：
- `/workspace/maos/` 下的任何文件
- `/workspace/maos_dashboard.html` 本身
- 其他项目源文件

## 📞 支持

如有问题，请查看：
- [MAOS_V3_IMPROVEMENT_REPORT.md](MAOS_V3_IMPROVEMENT_REPORT.md) - v3改进报告
- [REAL_PROJECT_TESTING_REPORT.md](REAL_PROJECT_TESTING_REPORT.md) - 真实项目测试报告

---

**版本**: v3.0.0  
**最后更新**: 2026-05-15
