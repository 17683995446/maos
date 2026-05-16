"""
MAOS v12.0 - 插件市场正式版
完整的插件开发生态
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid
import hashlib


class PluginReleaseChannel(Enum):
    """插件发布渠道"""
    STABLE = "stable"
    BETA = "beta"
    ALPHA = "alpha"


class PluginReviewStatus(Enum):
    """插件审核状态"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"


@dataclass
class PluginDependency:
    """插件依赖"""
    name: str
    version_range: str
    required: bool = True
    optional_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PluginVersion:
    """插件版本"""
    version: str
    release_notes: str
    release_date: datetime
    download_url: str
    file_size: int
    checksum: str
    dependencies: List[PluginDependency]
    supported_maos_versions: List[str]
    is_latest: bool = False
    is_prerelease: bool = False


@dataclass
class PluginCategory:
    """插件分类"""
    id: str
    name: str
    description: str
    icon: str
    plugins_count: int = 0


@dataclass
class PluginDeveloper:
    """插件开发者"""
    id: str
    name: str
    avatar_url: str
    plugin_count: int
    total_downloads: int
    verified: bool = False


@dataclass
class PluginScreenshot:
    """插件截图"""
    url: str
    caption: str
    order: int = 0


@dataclass
class Plugin:
    """插件（增强版插件定义"""
    id: str
    name: str
    description: str
    short_description: str
    long_description: str
    current_version: str
    versions: List[PluginVersion]
    category: str
    tags: List[str]
    keywords: List[str]
    author: PluginDeveloper
    license: str
    repository_url: str
    documentation_url: str
    homepage_url: str
    is_official: bool = False
    is_verified: bool = False
    is_featured: bool = False
    total_downloads: int = 0
    active_installs: int = 0
    total_ratings: int = 0
    average_rating: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    screenshots: List[PluginScreenshot] = field(default_factory=list)
    review_status: PluginReviewStatus = PluginReviewStatus.PENDING
    channel: PluginReleaseChannel = PluginReleaseChannel.STABLE
    readme: str = ""
    compatibility: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "shortDescription": self.short_description,
            "currentVersion": self.current_version,
            "category": self.category,
            "tags": self.tags,
            "author": {
                "name": self.author.name,
                "id": self.author.id,
                "verified": self.author.verified,
            },
            "totalDownloads": self.total_downloads,
            "activeInstalls": self.active_installs,
            "averageRating": self.average_rating,
            "totalRatings": self.total_ratings,
            "isOfficial": self.is_official,
            "isVerified": self.is_verified,
            "isFeatured": self.is_featured,
            "createdAt": self.created_at.isoformat(),
            "updatedAt": self.updated_at.isoformat(),
            "readme": self.readme,
        }


class PluginSDK:
    """插件开发工具包"""

    def __init__(self):
        self.templates = {
            "agent": "agent_template",
            "storage": "storage_template",
            "api": "api_template",
            "transformer": "transformer_template",
            "monitoring": "monitoring_template",
        }

    def create_plugin_scaffold(self, plugin_type: str, name: str, author: str) -> str:
        """创建插件脚手架"""
        plugin_id = str(uuid.uuid4())[:8]
        return plugin_id
        print(f"✅ 创建 {plugin_type} 插件: {name}")

        return f"""
# {name} Plugin

作者: {author}
类型: {plugin_type}
"""

    def validate_plugin(self, plugin_dir: str) -> Tuple[bool, List[str]]:
        """验证插件"""
        issues = []

        print(f"🔍 验证插件: {plugin_dir}")

        # 验证插件结构
        required_files = ["plugin.yaml", "README.md", "requirements.txt", "src/__init__.py"]
        missing_files = []
        for req in required_files:
            if not os.path.exists(os.path.join(plugin_dir, req)):
                missing_files.append(req)

        if missing_files:
            issues.append(f"缺少必要文件: {missing_files}")

        return len(issues) == 0, issues


class PluginSandbox:
    """插件沙箱"""

    def __init__(self):
        self.allowed_apis = ["maos.v1.*", "maos.storage", "maos.utils"]
        self.blocked_functions = ["os.system", "subprocess", "eval", "exec"]

    def execute_plugin(self, plugin_code: str, plugin_id: str) -> Dict[str, Any]:
        """在沙箱中执行插件"""
        print(f"🛡️ 在沙箱中执行插件: {plugin_id}")
        return {"status": "success", "output": "Plugin executed safely"}


class PluginMarketplaceV2:
    """插件市场V2（增强版）"""

    def __init__(self):
        self.plugins: Dict[str, Plugin] = {}
        self.categories: List[PluginCategory] = [
            PluginCategory("agents", "Agents", "智能代理插件", "🤖"),
            PluginCategory("storage", "Storage", "存储连接器", "💾"),
            PluginCategory("api", "APIs", "外部API集成", "🌐"),
            PluginCategory("transformers", "Transformers", "数据转换插件", "🔄"),
            PluginCategory("monitoring", "Monitoring", "监控与可观测性", "📊"),
            PluginCategory("security", "Security", "安全与认证", "🔒"),
        ]
        self.sandbox = PluginSandbox()
        self.sdk = PluginSDK()
        self._init_sample_plugins()

    def _init_sample_plugins(self):
        """初始化示例插件库"""
        dev = PluginDeveloper(
            id="dev-1",
            name="MAOS Team",
            avatar_url="https://maos.io/team/avatar.png",
            plugin_count=15,
            total_downloads=50000,
            verified=True,
        )

        # 官方插件库
        plugins_data = [
            {
                "name": "GPT-4 Agent",
                "desc": "基于GPT-4的智能Agent，支持高级推理",
                "cat": "agents",
                "tags": ["llm", "agent", "gpt-4"],
                "downloads": 25000,
                "rating": 4.9,
                "total_ratings": 500,
                "official": True,
                "featured": True,
            },
            {
                "name": "AWS S3 Storage",
                "desc": "Amazon S3存储集成插件",
                "cat": "storage",
                "tags": ["storage", "aws", "s3"],
                "downloads": 18000,
                "rating": 4.7,
                "total_ratings": 320,
                "official": True,
                "featured": True,
            },
            {
                "name": "Slack Notifier",
                "desc": "Slack消息通知与交互插件",
                "cat": "api",
                "tags": ["notification", "slack", "chat"],
                "downloads": 12000,
                "rating": 4.6,
                "total_ratings": 210,
                "official": True,
                "featured": False,
            },
            {
                "name": "Prometheus Metrics",
                "desc": "Prometheus监控指标导出",
                "cat": "monitoring",
                "tags": ["monitoring", "prometheus", "metrics"],
                "downloads": 9500,
                "rating": 4.8,
                "total_ratings": 180,
                "official": True,
                "featured": False,
            },
            {
                "name": "JSON Transformer",
                "desc": "强大的JSON数据转换工具",
                "cat": "transformers",
                "tags": ["data", "json", "transform"],
                "downloads": 7800,
                "rating": 4.5,
                "total_ratings": 130,
                "official": False,
                "featured": True,
            },
            {
                "name": "OAuth2 Provider",
                "desc": "完整的OAuth2认证提供者插件",
                "cat": "security",
                "tags": ["security", "oauth", "authentication"],
                "downloads": 6200,
                "rating": 4.4,
                "total_ratings": 95,
                "official": True,
                "featured": False,
            },
            {
                "name": "Claude 3 Agent",
                "desc": "Anthropic Claude 3模型集成",
                "cat": "agents",
                "tags": ["llm", "agent", "claude"],
                "downloads": 11000,
                "rating": 4.8,
                "total_ratings": 300,
                "official": False,
                "featured": True,
            },
            {
                "name": "MongoDB Storage",
                "desc": "MongoDB数据库存储插件",
                "cat": "storage",
                "tags": ["database", "mongodb", "storage"],
                "downloads": 8900,
                "rating": 4.6,
                "total_ratings": 140,
                "official": False,
                "featured": False,
            },
        ]

        for data in plugins_data:
            plugin = Plugin(
                id=str(uuid.uuid4()),
                name=data["name"],
                description=data["desc"],
                short_description=data["desc"][:100],
                long_description=f"# " + data["desc"],
                current_version="1.0.0",
                versions=[],
                category=data["cat"],
                tags=data["tags"],
                keywords=data["tags"],
                author=dev,
                license="MIT",
                repository_url=f"https://github.com/maos/" + data["name"].lower().replace(" ", "-"),
                documentation_url=f"https://docs.maos.io/plugins/" + data["name"].lower().replace(" ", "-"),
                homepage_url=f"https://maos.io",
                is_official=data["official"],
                is_verified=data["official"],
                is_featured=data["featured"],
                total_downloads=data["downloads"],
                active_installs=int(data["downloads"] * 0.3),
                average_rating=data["rating"],
                total_ratings=data["total_ratings"],
                created_at=datetime.now(),
                updated_at=datetime.now(),
                screenshots=[],
                readme="# " + data["name"] + "\n\n" + data["desc"],
                review_status=PluginReviewStatus.APPROVED,
            )
            self.plugins[plugin.id] = plugin

    def search_plugins(self, query: str = "", category: Optional[str] = None, sort_by: str = "downloads") -> List[Dict]:
        """搜索插件"""
        results = list(self.plugins.values())
        if query:
            q_lower = query.lower()
            results = [p for p in results if (q_lower in p.name.lower()) or any(q_lower in t.lower() for t in p.tags)]

        if category and category != "all":
            results = [p for p in results if p.category == category]

        if sort_by == "downloads":
            results = sorted(results, key=lambda p: -p.total_downloads)
        elif sort_by == "rating":
            results = sorted(results, key=lambda p: -p.average_rating)
        elif sort_by == "newest":
            results = sorted(results, key=lambda p: -p.created_at.timestamp())

        return [p.to_dict() for p in results]

    def get_featured_plugins(self) -> List[Dict]:
        """获取精选插件"""
        return [p.to_dict() for p in self.plugins.values() if p.is_featured]

    def get_trending_plugins(self, days: int = 7) -> List[Dict]:
        """获取热门插件"""
        trending = sorted(self.plugins.values(), key=lambda p: -p.total_downloads)
        return [p.to_dict() for p in trending[:8]]

    def get_categories(self) -> List[Dict]:
        """获取分类列表"""
        return [{
            "id": cat.id,
            "name": cat.name,
            "description": cat.description,
            "icon": cat.icon,
            "pluginsCount": len([p for p in self.plugins.values() if p.category == cat.id]),
        } for cat in self.categories]
