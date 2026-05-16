"""
MAOS v8.0 - 插件系统
可扩展的插件架构和插件市场基础
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import importlib.util
import time
from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import hashlib
import json


class PluginType(Enum):
    """插件类型"""
    AGENT = "agent"
    TASK_PROCESSOR = "task_processor"
    STORAGE = "storage"
    AUTHENTICATION = "authentication"
    INTEGRATION = "integration"
    UI_COMPONENT = "ui_component"
    METRICS = "metrics"
    HOOK = "hook"


@dataclass
class PluginMetadata:
    """插件元数据"""
    name: str
    version: str
    author: str
    description: str
    type: PluginType
    dependencies: List[str] = field(default_factory=list)
    compatible_versions: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "version": self.version,
            "author": self.author,
            "description": self.description,
            "type": self.type.value,
            "dependencies": self.dependencies,
            "tags": self.tags
        }


@dataclass
class PluginContext:
    """插件执行上下文"""
    plugin_id: str
    config: Dict[str, Any] = field(default_factory=dict)
    permissions: Set[str] = field(default_factory=set)
    api_endpoints: Dict[str, Any] = field(default_factory=dict)


class Plugin:
    """插件基类"""
    
    def __init__(self, metadata: PluginMetadata, context: PluginContext):
        self.metadata = metadata
        self.context = context
        self.initialized = False
    
    def initialize(self):
        """初始化插件"""
        print(f"🔌 Initializing plugin: {self.metadata.name} v{self.metadata.version}")
        self.initialized = True
    
    def activate(self):
        """激活插件"""
        print(f"✨ Activating plugin: {self.metadata.name}")
    
    def deactivate(self):
        """停用插件"""
        print(f"🛑 Deactivating plugin: {self.metadata.name}")
    
    def cleanup(self):
        """清理插件资源"""
        print(f"🧹 Cleaning up plugin: {self.metadata.name}")


class PluginRegistry:
    """插件注册表"""
    
    def __init__(self):
        self.plugins: Dict[str, Plugin] = {}
        self.metadata_store: Dict[str, PluginMetadata] = {}
        self.installation_log: List[Dict] = []
        self.plugin_search_index: Dict[str, List[str]] = defaultdict(list)
    
    def register_plugin(self, plugin: Plugin):
        """注册插件"""
        plugin_id = self._generate_plugin_id(plugin.metadata)
        self.plugins[plugin_id] = plugin
        self.metadata_store[plugin_id] = plugin.metadata
        
        # 更新搜索索引
        for tag in plugin.metadata.tags:
            self.plugin_search_index[tag].append(plugin_id)
        
        # 记录安装
        self.installation_log.append({
            "plugin_id": plugin_id,
            "name": plugin.metadata.name,
            "version": plugin.metadata.version,
            "timestamp": time.time(),
            "action": "installed"
        })
        
        print(f"✅ Plugin registered: {plugin.metadata.name} ({plugin_id})")
        return plugin_id
    
    def unregister_plugin(self, plugin_id: str) -> bool:
        """卸载插件"""
        if plugin_id not in self.plugins:
            return False
        
        plugin = self.plugins[plugin_id]
        
        # 停用
        plugin.deactivate()
        plugin.cleanup()
        
        # 移除
        del self.plugins[plugin_id]
        del self.metadata_store[plugin_id]
        
        # 更新索引
        for tag in list(self.plugin_search_index.keys()):
            if plugin_id in self.plugin_search_index[tag]:
                self.plugin_search_index[tag].remove(plugin_id)
        
        # 记录卸载
        self.installation_log.append({
            "plugin_id": plugin_id,
            "name": plugin.metadata.name,
            "version": plugin.metadata.version,
            "timestamp": time.time(),
            "action": "uninstalled"
        })
        
        print(f"❌ Plugin unregistered: {plugin.metadata.name}")
        return True
    
    def get_plugin(self, plugin_id: str) -> Optional[Plugin]:
        """获取插件"""
        return self.plugins.get(plugin_id)
    
    def search_plugins(self, query: str) -> List[Dict]:
        """搜索插件"""
        results = []
        query_lower = query.lower()
        
        for plugin_id, metadata in self.metadata_store.items():
            if (query_lower in metadata.name.lower() or 
                query_lower in metadata.description.lower() or
                any(query_lower in tag.lower() for tag in metadata.tags)):
                results.append({
                    "plugin_id": plugin_id,
                    "metadata": metadata.to_dict()
                })
        
        return results
    
    def list_plugins(self) -> List[Dict]:
        """列出所有插件"""
        return [
            {
                "plugin_id": pid,
                "metadata": metadata.to_dict()
            }
            for pid, metadata in self.metadata_store.items()
        ]
    
    def _generate_plugin_id(self, metadata: PluginMetadata) -> str:
        """生成插件ID"""
        unique_str = f"{metadata.name}:{metadata.version}:{metadata.author}"
        return hashlib.md5(unique_str.encode()).hexdigest()[:16]


class PluginManager:
    """插件管理器"""
    
    def __init__(self, plugins_dir: str = "plugins"):
        self.registry = PluginRegistry()
        self.plugins_dir = Path(plugins_dir)
        self.plugins_dir.mkdir(exist_ok=True)
        self.active_plugins: Set[str] = set()
        
        # 扫描插件目录
        self._scan_plugin_directory()
    
    def _scan_plugin_directory(self):
        """扫描插件目录"""
        print(f"🔍 Scanning plugin directory: {self.plugins_dir}")
        
        # 目前为空，等待真实插件
        # 实际应用会扫描并加载真实插件
        print("   Plugin directory is empty (ready for plugins)")
    
    def load_plugin(self, plugin_path: str) -> Optional[str]:
        """加载插件（简化版）"""
        print(f"📦 Loading plugin from: {plugin_path}")
        # 简化版：实际会真正加载Python模块
        return None
    
    def activate_plugin(self, plugin_id: str) -> bool:
        """激活插件"""
        plugin = self.registry.get_plugin(plugin_id)
        if not plugin:
            return False
        
        if plugin_id in self.active_plugins:
            return True
        
        if not plugin.initialized:
            plugin.initialize()
        
        plugin.activate()
        self.active_plugins.add(plugin_id)
        return True
    
    def deactivate_plugin(self, plugin_id: str) -> bool:
        """停用插件"""
        plugin = self.registry.get_plugin(plugin_id)
        if not plugin:
            return False
        
        if plugin_id not in self.active_plugins:
            return True
        
        plugin.deactivate()
        self.active_plugins.discard(plugin_id)
        return True
    
    def get_status(self) -> Dict:
        """获取插件系统状态"""
        return {
            "total_plugins": len(self.registry.plugins),
            "active_plugins": len(self.active_plugins),
            "registry_size": len(self.registry.metadata_store),
            "installation_logs": len(self.registry.installation_log)
        }


def create_sample_plugin():
    """创建示例插件"""
    metadata = PluginMetadata(
        name="sample_agent_plugin",
        version="1.0.0",
        author="MAOS Team",
        description="A sample Agent plugin for demonstration",
        type=PluginType.AGENT,
        tags=["sample", "agent", "demo"]
    )
    
    context = PluginContext(
        plugin_id="sample_001",
        config={"sample_config": "value"}
    )
    
    return Plugin(metadata, context)
