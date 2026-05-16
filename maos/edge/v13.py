"""
MAOS v13.0 - Global CDN & Edge Computing Optimization
全球CDN与边缘计算优化
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import random


class Region(Enum):
    """区域"""
    US_EAST = "us-east-1"  # 美国东部
    US_WEST = "us-west-2"  # 美国西部
    EU_WEST = "eu-west-1"  # 欧洲西部
    AP_SOUTHEAST = "ap-southeast-1"  # 亚太东南部
    AP_NORTHEAST = "ap-northeast-1"  # 亚太东北部


class EdgeProvider(Enum):
    """边缘计算提供商"""
    CLOUDFLARE = "cloudflare"
    AWS_LAMBDA_EDGE = "aws_lambda_edge"
    FASTLY = "fastly"
    AZURE_EDGE = "azure_edge"


@dataclass
class RegionConfig:
    """区域配置"""
    region: Region
    name: str
    lat: float
    lon: float
    capacity: int = 1000
    enabled: bool = True


# 区域配置
REGION_CONFIGS = {
    Region.US_EAST: RegionConfig(
        region=Region.US_EAST,
        name="US East (Virginia)",
        lat=37.9269,
        lon=-75.5274,
        capacity=2000
    ),
    Region.US_WEST: RegionConfig(
        region=Region.US_WEST,
        name="US West (Oregon)",
        lat=43.8041,
        lon=-120.5542,
        capacity=1500
    ),
    Region.EU_WEST: RegionConfig(
        region=Region.EU_WEST,
        name="EU West (Ireland)",
        lat=53.3498,
        lon=-6.2603,
        capacity=1800
    ),
    Region.AP_SOUTHEAST: RegionConfig(
        region=Region.AP_SOUTHEAST,
        name="Asia Pacific (Singapore)",
        lat=1.3521,
        lon=103.8198,
        capacity=1500
    ),
    Region.AP_NORTHEAST: RegionConfig(
        region=Region.AP_NORTHEAST,
        name="Asia Pacific (Tokyo)",
        lat=35.6762,
        lon=139.6503,
        capacity=1600
    )
}


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    ttl_seconds: int = 3600
    created_at: datetime = field(default_factory=datetime.now)
    hit_count: int = 0

    def is_expired(self) -> bool:
        """检查是否过期"""
        return (datetime.now() - self.created_at).total_seconds() > self.ttl_seconds


@dataclass
class EdgeFunction:
    """边缘函数"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    code: str = ""
    provider: EdgeProvider = EdgeProvider.CLOUDFLARE
    region: Optional[Region] = None
    deployed: bool = False
    created_at: datetime = field(default_factory=datetime.now)


class EdgeCache:
    """边缘缓存"""

    def __init__(self, region: Region, max_size: int = 10000):
        self.region = region
        self.max_size = max_size
        self._cache: Dict[str, CacheEntry] = {}

    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        entry = self._cache.get(key)
        if entry and not entry.is_expired():
            entry.hit_count += 1
            return entry.value
        if entry and entry.is_expired():
            del self._cache[key]
        return None

    def set(self, key: str, value: Any, ttl_seconds: int = 3600) -> bool:
        """设置缓存"""
        if len(self._cache) >= self.max_size:
            self._evict()
        self._cache[key] = CacheEntry(key=key, value=value, ttl_seconds=ttl_seconds)
        return True

    def invalidate(self, key: str) -> bool:
        """失效缓存"""
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def invalidate_all(self) -> None:
        """失效所有缓存"""
        self._cache.clear()

    def _evict(self) -> None:
        """淘汰缓存（LRU简化版）"""
        if not self._cache:
            return
        oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k].created_at)
        del self._cache[oldest_key]

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        hits = sum(e.hit_count for e in self._cache.values())
        return {
            "region": self.region.value,
            "size": len(self._cache),
            "max_size": self.max_size,
            "total_hits": hits
        }


class GeoRouter:
    """地理位置路由器"""

    def __init__(self):
        self.region_configs = REGION_CONFIGS

    def get_closest_region(self, user_lat: float, user_lon: float) -> Region:
        """获取最近的区域"""
        min_distance = float('inf')
        closest_region = Region.US_EAST
        
        for region, config in self.region_configs.items():
            if not config.enabled:
                continue
            distance = self._haversine(user_lat, user_lon, config.lat, config.lon)
            if distance < min_distance:
                min_distance = distance
                closest_region = region
        
        return closest_region

    def _haversine(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """计算两点之间的距离（Haversine公式）"""
        import math
        R = 6371.0  # 地球半径（公里）
        
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = math.sin(dlat / 2) ** 2 + \
            math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
            math.sin(dlon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c


class GlobalTrafficManager:
    """全球流量管理器"""

    def __init__(self):
        self.geo_router = GeoRouter()
        self._region_load: Dict[Region, int] = {r: 0 for r in Region}
        self._caches: Dict[Region, EdgeCache] = {r: EdgeCache(r) for r in Region}

    def route_request(self, user_lat: float, user_lon: float, request_type: str = "workflow") -> Dict[str, Any]:
        """路由请求"""
        target_region = self.geo_router.get_closest_region(user_lat, user_lon)
        
        config = REGION_CONFIGS[target_region]
        current_load = self._region_load[target_region]
        
        if current_load >= config.capacity:
            # 负载过高，尝试其他区域
            for region in REGION_CONFIGS:
                if region != target_region and REGION_CONFIGS[region].enabled:
                    if self._region_load[region] < REGION_CONFIGS[region].capacity:
                        target_region = region
                        break
        
        self._region_load[target_region] += 1
        
        return {
            "region": target_region.value,
            "region_name": config.name,
            "load": current_load,
            "capacity": config.capacity,
            "routed_at": datetime.now().isoformat()
        }

    def get_cache(self, region: Region) -> EdgeCache:
        """获取区域缓存"""
        return self._caches[region]

    def get_global_stats(self) -> Dict[str, Any]:
        """获取全局统计"""
        region_stats = {}
        total_load = 0
        total_capacity = 0
        
        for region, config in REGION_CONFIGS.items():
            load = self._region_load[region]
            total_load += load
            total_capacity += config.capacity
            cache_stats = self._caches[region].get_stats()
            region_stats[region.value] = {
                "name": config.name,
                "load": load,
                "capacity": config.capacity,
                "utilization": (load / config.capacity * 100) if config.capacity > 0 else 0,
                "cache": cache_stats
            }
        
        return {
            "regions": region_stats,
            "total_load": total_load,
            "total_capacity": total_capacity,
            "global_utilization": (total_load / total_capacity * 100) if total_capacity > 0 else 0
        }


class EdgeFunctionManager:
    """边缘函数管理器"""

    def __init__(self, traffic_manager: GlobalTrafficManager):
        self.traffic_manager = traffic_manager
        self._functions: Dict[str, EdgeFunction] = {}

    def deploy_function(self, name: str, code: str, provider: EdgeProvider = EdgeProvider.CLOUDFLARE, region: Region = None) -> EdgeFunction:
        """部署边缘函数"""
        function = EdgeFunction(
            name=name,
            code=code,
            provider=provider,
            region=region,
            deployed=True
        )
        self._functions[function.id] = function
        print(f"🚀 Edge function '{name}' deployed to {provider.value} {region.value if region else 'global'}")
        return function

    def invoke_function(self, function_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """调用边缘函数"""
        function = self._functions.get(function_id)
        if not function:
            return {"error": "Function not found"}
        if not function.deployed:
            return {"error": "Function not deployed"}
        
        # 模拟边缘函数执行
        execution_time = random.uniform(0.01, 0.1)
        return {
            "function_id": function_id,
            "function_name": function.name,
            "status": "success",
            "execution_time_ms": execution_time * 1000,
            "result": {"message": "Function executed successfully", "input": input_data},
            "executed_at": datetime.now().isoformat()
        }


class CDNManager:
    """CDN管理器"""

    def __init__(self, traffic_manager: GlobalTrafficManager):
        self.traffic_manager = traffic_manager

    def cache_content(self, key: str, content: Any, region: Region = None, ttl: int = 3600) -> bool:
        """缓存内容"""
        if region:
            cache = self.traffic_manager.get_cache(region)
            return cache.set(key, content, ttl)
        else:
            # 缓存到所有区域
            success = True
            for r in Region:
                cache = self.traffic_manager.get_cache(r)
                if not cache.set(key, content, ttl):
                    success = False
            return success

    def get_content(self, key: str, user_lat: float, user_lon: float) -> Optional[Any]:
        """获取内容（从最近区域）"""
        region = self.traffic_manager.geo_router.get_closest_region(user_lat, user_lon)
        cache = self.traffic_manager.get_cache(region)
        return cache.get(key)

    def invalidate_content(self, key: str, region: Region = None) -> None:
        """失效内容"""
        if region:
            cache = self.traffic_manager.get_cache(region)
            cache.invalidate(key)
        else:
            # 失效所有区域
            for r in Region:
                cache = self.traffic_manager.get_cache(r)
                cache.invalidate(key)
        print(f"🗑️ Content '{key}' invalidated {'globally' if not region else f'in {region.value}'}")
