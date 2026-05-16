"""
MAOS v11.0 - 插件市场2.0
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid


class PluginRating(Enum):
    """插件评分"""
    ONE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5


@dataclass
class PluginReview:
    """插件评价"""
    id: str
    user_id: str
    user_name: str
    rating: PluginRating
    comment: str
    created_at: datetime


@dataclass
class Plugin:
    """插件定义"""
    id: str
    name: str
    description: str
    version: str
    author: str
    author_url: str
    category: str
    tags: List[str]
    thumbnail_url: Optional[str]
    readme: str
    downloads: int
    ratings_count: int
    average_rating: float
    reviews: List[PluginReview]
    created_at: datetime
    updated_at: datetime
    is_verified: bool
    is_active: bool

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "author": self.author,
            "authorUrl": self.author_url,
            "category": self.category,
            "tags": self.tags,
            "downloads": self.downloads,
            "ratingsCount": self.ratings_count,
            "averageRating": self.average_rating,
            "createdAt": self.created_at.isoformat(),
            "updatedAt": self.updated_at.isoformat(),
            "isVerified": self.is_verified,
            "isActive": self.is_active,
        }


class PluginMarketplace:
    """插件市场"""

    def __init__(self):
        self.plugins: Dict[str, Plugin] = {}
        self.categories = [
            "agents",
            "storage",
            "api",
            "monitoring",
            "security",
            "visualization",
            "transformers",
            "utilities",
        ]
        self._init_sample_plugins()

    def _init_sample_plugins(self):
        """初始化示例插件"""

        samples = [
            Plugin(
                id="plugin-gpt-4",
                name="GPT-4 Agent",
                description="基于GPT-4的智能Agent，支持文本生成和推理",
                version="1.2.0",
                author="OpenAI",
                author_url="https://openai.com",
                category="agents",
                tags=["agent", "llm", "gpt-4"],
                readme="# GPT-4 Agent\n\n基于GPT-4的智能Agent",
                downloads=10543,
                ratings_count=248,
                average_rating=4.8,
                is_verified=True,
                is_active=True,
            ),
            Plugin(
                id="plugin-s3-storage",
                name="S3 Storage",
                description="支持Amazon S3的存储插件",
                version="2.0.1",
                author="AWS",
                author_url="https://aws.amazon.com",
                category="storage",
                tags=["storage", "aws", "s3"],
                readme="# S3 Storage",
                downloads=8765,
                ratings_count=189,
                average_rating=4.5,
                is_verified=True,
                is_active=True,
            ),
            Plugin(
                id="plugin-slack",
                name="Slack Integration",
                description="Slack消息通知插件",
                version="1.1.5",
                author="Slack",
                author_url="https://slack.com",
                category="api",
                tags=["notification", "slack", "chat"],
                readme="# Slack Integration",
                downloads=6543,
                ratings_count=156,
                average_rating=4.3,
                is_verified=True,
                is_active=True,
            ),
            Plugin(
                id="plugin-prometheus",
                name="Prometheus Metrics",
                description="Prometheus监控指标导出",
                version="1.0.3",
                author="Prometheus",
                author_url="https://prometheus.io",
                category="monitoring",
                tags=["monitoring", "metrics", "prometheus"],
                readme="# Prometheus Metrics",
                downloads=4321,
                ratings_count=98,
                average_rating=4.6,
                is_verified=True,
                is_active=True,
            ),
            Plugin(
                id="plugin-json-transform",
                name="JSON Transformer",
                description="JSON数据转换插件",
                version="0.8.2",
                author="Community",
                author_url="https://github.com",
                category="transformers",
                tags=["data", "json", "transform"],
                readme="# JSON Transformer",
                downloads=2345,
                ratings_count=78,
                average_rating=4.2,
                is_verified=False,
                is_active=True,
            ),
        ]

        for plugin in samples:
            self.plugins[plugin.id] = plugin

    def search_plugins(self, query: str = "", category: Optional[str] = None,
                      sort_by: str = "downloads") -> List[Dict]:
        """搜索插件"""
        results = list(self.plugins.values())

        if query:
            q_lower = query.lower()
            results = [
                p for p in results
                if (q_lower in p.name.lower()
                    or q_lower in p.description.lower()
                    or any(q_lower in t.lower() for t in p.tags))
            ]

        if category:
            results = [p for p in results if p.category == category]

        if sort_by == "downloads":
            results.sort(key=lambda p: -p.downloads)
        elif sort_by == "rating":
            results.sort(key=lambda p: -p.average_rating)
        elif sort_by == "newest":
            results.sort(key=lambda p: -p.created_at.timestamp())

        return [p.to_dict() for p in results]

    def get_plugin(self, plugin_id: str) -> Optional[Plugin]:
        """获取插件"""
        return self.plugins.get(plugin_id)

    def install_plugin(self, plugin_id: str, user_id: str) -> bool:
        """安装插件"""
        plugin = self.plugins.get(plugin_id)
        if not plugin:
            return False
        plugin.downloads += 1
        return True

    def list_categories(self) -> List[Dict]:
        """列出分类"""
        return [
            {"id": cat, "name": cat.replace("-", " ").title()}
            for cat in self.categories
        ]

    def get_featured_plugins(self) -> List[Dict]:
        """获取精选插件"""
        sorted_plugins = sorted(self.plugins.values(),
                               key=lambda p: -p.downloads * p.average_rating)
        return [p.to_dict() for p in sorted_plugins[:4]]

    def get_trending_plugins(self) -> List[Dict]:
        """获取热门插件"""
        return [p.to_dict() for p in
               sorted(self.plugins.values(), key=lambda p: -p.downloads)[:8]]
