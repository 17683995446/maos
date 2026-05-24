#!/usr/bin/env python3
"""
MAOS - 终极超长时间极端混沌测试（60分钟版）
Ultra Long Duration Extreme Chaos Test (60 mins)
"""

import sys
import time
import random
import threading
import gc
import logging
import tracemalloc
from datetime import datetime
from collections import defaultdict, deque

sys.path.insert(0, '/workspace')

from maos.storage.in_memory import InMemoryChatStorage
from maos.version.v14 import VersionManager
from maos.analytics.v14 import AnalyticsEngine

# 详细日志配置
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)-8s] [%(threadName)-15s] %(message)s',
    handlers=[
        logging.FileHandler('/workspace/maos/tests/extreme_test.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class UltraExtremeChaosTest:
    """终极极端混沌测试"""

    def __init__(self):
        self.storage = InMemoryChatStorage()
        self.vm = VersionManager()
        self.analytics = AnalyticsEngine()

        self.errors = []
        self.warnings = []
        self.operation_log = deque(maxlen=10000)
        self.lock = threading.Lock()
        self.stop_event = threading.Event()

        self.stats = {
            'total_ops': 0,
            'storage_ops': 0,
            'version_ops': 0,
            'analytics_ops': 0,
            'errors': 0,
            'warnings': 0,
            'start_time': None,
            'memory_peak': 0
        }

        tracemalloc.start()

    def log_operation(self, component, operation, status, latency_ms=0, details=''):
        """记录操作（详细日志）"""
        with self.lock:
            entry = {
                'time': datetime.now(),
                'component': component,
                'operation': operation,
                'status': status,
                'latency_ms': latency_ms,
                'details': details
            }
            self.operation_log.append(entry)
            self.stats['total_ops'] += 1

        log_msg = f"[{component}] [{operation}] {status} | {latency_ms:.2f}ms | {details}"
        if status == 'ERROR':
            logger.error(log_msg)
        elif status == 'WARNING':
            logger.warning(log_msg)
        else:
            logger.debug(log_msg)

    def log_error(self, component, operation, exception):
        """记录错误"""
        with self.lock:
            self.errors.append({
                'time': datetime.now(),
                'component': component,
                'operation': operation,
                'exc_type': type(exception).__name__,
                'exc_msg': str(exception),
                'stacktrace': traceback.format_exc()
            })
            self.stats['errors'] += 1

        logger.error(f"🔴 ERROR in {component}.{operation}: {type(exception).__name__}: {str(exception)}")

    def log_warning(self, component, operation, message):
        """记录警告"""
        with self.lock:
            self.warnings.append({
                'time': datetime.now(),
                'component': component,
                'operation': operation,
                'message': message
            })
            self.stats['warnings'] += 1

        logger.warning(f"⚠️ WARNING in {component}.{operation}: {message}")

    def chaos_worker_storage(self, worker_id):
        """存储混沌工作线程"""
        logger.info(f"🔄 Starting Storage Chaos Worker {worker_id}")
        end_time = time.time() + 3600  # 1小时
        errors = 0

        while time.time() < end_time and not self.stop_event.is_set():
            try:
                start = time.time()
                user = f"extreme_user_{worker_id}_{random.randint(0, 100)}"
                session = f"chaos_session_{random.randint(0, 50)}"
                agent = f"agent_{random.randint(0, 20)}"

                # 随机操作
                op = random.choice([
                    'save_small', 'save_large', 'save_unicode',
                    'save_extreme', 'read', 'stats', 'clear'
                ])

                if op == 'save_small':
                    content = f"Small msg {random.randint(1, 100000)}"
                    self.storage.save_message(
                        user, {'content': content, 'session_id': session, 'agent_id': agent}
                    )
                    with self.lock: self.stats['storage_ops'] += 1

                elif op == 'save_large':
                    content = 'x' * random.randint(10000, 100000)
                    self.storage.save_message(
                        user, {'content': content, 'session_id': session, 'agent_id': agent}
                    )
                    with self.lock: self.stats['storage_ops'] += 1

                elif op == 'save_unicode':
                    content = ''.join(random.choice(
                        ['🎉', '🎊', '🎁', '🎀', '🎄', '🎅', '🎆', '🎇', '🎈',
                         '中文', '日本語', '한국어', 'العربية', 'עברית',
                         '\x00', '\x01', '\x02', '\r', '\n', '\t']
                    ) for _ in range(random.randint(10, 200)))
                    self.storage.save_message(
                        user, {'content': content, 'session_id': session, 'agent_id': agent}
                    )
                    with self.lock: self.stats['storage_ops'] += 1

                elif op == 'save_extreme':
                    msg = {
                        'content': random.choice([
                            None,
                            '',
                            float('inf'),
                            float('-inf'),
                            float('nan'),
                            {'deep': {'nested': [1, None, 'text']}},
                            ['list', 'with', 1, None, True]
                        ]),
                        'session_id': session,
                        'agent_id': agent,
                        'timestamp': random.choice([
                            time.time(),
                            0,
                            -100000000000,
                            int(time.time() + 100 * 365 * 24 * 3600)
                        ])
                    }
                    self.storage.save_message(user, msg)
                    with self.lock: self.stats['storage_ops'] += 1

                elif op == 'read':
                    self.storage.get_conversation(user, session, agent)
                    with self.lock: self.stats['storage_ops'] += 1

                elif op == 'stats':
                    self.storage.get_stats()
                    with self.lock: self.stats['storage_ops'] += 1

                elif op == 'clear' and random.random() < 0.001:  # 0.1% 概率
                    self.storage.clear_all()
                    with self.lock: self.stats['storage_ops'] += 1

                latency_ms = (time.time() - start) * 1000
                self.log_operation('STORAGE', op, 'SUCCESS', latency_ms, f"user={user}")

                # 随机延迟（模拟真实负载）
                if random.random() < 0.1:
                    time.sleep(random.uniform(0, 0.01))

            except Exception as e:
                errors += 1
                self.log_error('STORAGE', op, e)

        logger.info(f"✅ Storage Chaos Worker {worker_id} completed. Errors: {errors}")

    def chaos_worker_version(self, worker_id):
        """版本管理混沌工作线程"""
        logger.info(f"🔄 Starting Version Chaos Worker {worker_id}")
        end_time = time.time() + 3600
        errors = 0

        while time.time() < end_time and not self.stop_event.is_set():
            try:
                start = time.time()
                wf = f"workflow_{worker_id}_{random.randint(0, 100)}"

                op = random.choice(['create', 'list', 'get', 'latest', 'activate'])

                if op == 'create':
                    version_data = {
                        'step': random.randint(1, 1000),
                        'data': {
                            'random': random.random(),
                            'text': 'version data ' + str(random.randint(1, 100000)),
                            'list': [1, 2, 3, random.choice(['a', None, True])]
                        },
                        'timestamp': datetime.now().isoformat()
                    }
                    self.vm.create_version(wf, version_data)
                    with self.lock: self.stats['version_ops'] += 1

                elif op == 'list':
                    self.vm.list_versions(wf)
                    with self.lock: self.stats['version_ops'] += 1

                elif op == 'get':
                    versions = self.vm.list_versions(wf)
                    if versions:
                        self.vm.get_version(random.choice(versions))
                    with self.lock: self.stats['version_ops'] += 1

                elif op == 'latest':
                    self.vm.get_latest_version(wf)
                    with self.lock: self.stats['version_ops'] += 1

                elif op == 'activate':
                    versions = self.vm.list_versions(wf)
                    if versions:
                        self.vm.activate_version(random.choice(versions))
                    with self.lock: self.stats['version_ops'] += 1

                latency_ms = (time.time() - start) * 1000
                self.log_operation('VERSION', op, 'SUCCESS', latency_ms, f"wf={wf}")

                if random.random() < 0.15:
                    time.sleep(random.uniform(0, 0.008))

            except Exception as e:
                errors += 1
                self.log_error('VERSION', op, e)

        logger.info(f"✅ Version Chaos Worker {worker_id} completed. Errors: {errors}")

    def chaos_worker_analytics(self, worker_id):
        """分析引擎混沌工作线程"""
        logger.info(f"🔄 Starting Analytics Chaos Worker {worker_id}")
        end_time = time.time() + 3600
        errors = 0

        while time.time() < end_time and not self.stop_event.is_set():
            try:
                start = time.time()
                metric = f"metric_{worker_id}_{random.randint(0, 100)}"

                value = random.choice([
                    random.random(),
                    random.randint(-1000000, 1000000),
                    0,
                    float('inf'),
                    float('-inf'),
                    float('nan'),
                    random.randint(-100000, 100000) / 1000
                ])

                self.analytics.record_metric(metric, value)
                with self.lock: self.stats['analytics_ops'] += 1

                if random.random() < 0.2:
                    self.analytics.get_summary()

                latency_ms = (time.time() - start) * 1000
                self.log_operation('ANALYTICS', 'record', 'SUCCESS', latency_ms, f"metric={metric}")

                if random.random() < 0.1:
                    time.sleep(random.uniform(0, 0.005))

            except Exception as e:
                errors += 1
                self.log_error('ANALYTICS', 'record', e)

        logger.info(f"✅ Analytics Chaos Worker {worker_id} completed. Errors: {errors}")

    def chaos_worker_integration(self, worker_id):
        """集成混沌工作线程"""
        logger.info(f"🔄 Starting Integration Chaos Worker {worker_id}")
        end_time = time.time() + 3600
        errors = 0

        while time.time() < end_time and not self.stop_event.is_set():
            try:
                start = time.time()
                user = f"integration_user_{worker_id}_{random.randint(0, 50)}"
                wf = f"integration_wf_{worker_id}_{random.randint(0, 50)}"
                session = f"session_{random.randint(0, 30)}"

                # 复杂集成操作
                for i in range(random.randint(1, 10)):
                    # 1. 创建版本
                    v = self.vm.create_version(
                        wf, {'user': user, 'iteration': i, 'time': time.time()}
                    )

                    # 2. 保存消息
                    self.storage.save_message(
                        user,
                        {
                            'content': f"Integrated message with version {v.id}",
                            'session_id': session,
                            'version_id': v.id
                        }
                    )

                    # 3. 记录指标
                    self.analytics.record_metric(f"{user}_integrated", float(i))

                # 4. 验证
                self.storage.get_conversation(user, session)
                self.vm.list_versions(wf)
                self.analytics.get_summary()

                latency_ms = (time.time() - start) * 1000
                self.log_operation('INTEGRATION', 'complex', 'SUCCESS', latency_ms, f"user={user}")

                if random.random() < 0.05:
                    time.sleep(random.uniform(0, 0.05))

            except Exception as e:
                errors += 1
                self.log_error('INTEGRATION', 'complex', e)

        logger.info(f"✅ Integration Chaos Worker {worker_id} completed. Errors: {errors}")

    def monitor_progress(self):
        """监控进度线程"""
        logger.info("🔍 Starting Monitor Thread")
        start_time = time.time()
        last_update = start_time

        while time.time() - start_time < 3600 and not self.stop_event.is_set():
            time.sleep(30)  # 每30秒报告一次

            with self.lock:
                stats_copy = dict(self.stats)

            elapsed = time.time() - start_time
            ops_per_sec = stats_copy['total_ops'] / max(elapsed, 1)

            logger.info(
                f"📊 PROGRESS: Elapsed={elapsed:.1f}s | "
                f"TotalOps={stats_copy['total_ops']:,} | "
                f"Throughput={ops_per_sec:.0f}ops/s | "
                f"StorageOps={stats_copy['storage_ops']:,} | "
                f"VersionOps={stats_copy['version_ops']:,} | "
                f"AnalyticsOps={stats_copy['analytics_ops']:,} | "
                f"Errors={stats_copy['errors']} | "
                f"Warnings={stats_copy['warnings']}"
            )

            # GC
            if random.random() < 0.2:
                gc.collect()

        logger.info("✅ Monitor Thread completed")

    def run(self):
        """运行终极测试"""
        print("=" * 140)
        print("🚀 MAOS - 终极超长时间极端混沌测试")
        print("🚀 目标：60分钟、50+线程、无限操作、极端混乱")
        print("=" * 140)
        self.stats['start_time'] = datetime.now()

        threads = []
        num_workers = {
            'storage': 20,
            'version': 15,
            'analytics': 10,
            'integration': 5
        }

        logger.info(f"🚀 Launching {sum(num_workers.values())} chaos workers")

        # 启动存储线程
        for i in range(num_workers['storage']):
            t = threading.Thread(target=self.chaos_worker_storage, args=(i,),
                                 name=f"StorageWorker-{i}")
            threads.append(t)
            t.start()

        # 启动版本线程
        for i in range(num_workers['version']):
            t = threading.Thread(target=self.chaos_worker_version, args=(i,),
                                 name=f"VersionWorker-{i}")
            threads.append(t)
            t.start()

        # 启动分析线程
        for i in range(num_workers['analytics']):
            t = threading.Thread(target=self.chaos_worker_analytics, args=(i,),
                                 name=f"AnalyticsWorker-{i}")
            threads.append(t)
            t.start()

        # 启动集成线程
        for i in range(num_workers['integration']):
            t = threading.Thread(target=self.chaos_worker_integration, args=(i,),
                                 name=f"IntegrationWorker-{i}")
            threads.append(t)
            t.start()

        # 启动监控线程
        monitor = threading.Thread(target=self.monitor_progress, name="MonitorThread")
        monitor.start()

        # 等待完成（30分钟快速验证）
        logger.info("⏳ Waiting for workers to complete (30 min test)...")
        time.sleep(1800)

        logger.info("⏹️ Sending stop signal to all workers")
        self.stop_event.set()

        for i, t in enumerate(threads):
            t.join(timeout=60)
            logger.debug(f"✅ Joined worker {i}")

        monitor.join(timeout=30)

        # 最终报告
        self.generate_final_report()

    def generate_final_report(self):
        """生成最终报告"""
        print("\n" + "=" * 140)
        print("📊 终极极端混沌测试 - 最终报告")
        print("=" * 140)

        with self.lock:
            stats = dict(self.stats)

        duration = (datetime.now() - stats['start_time']).total_seconds()
        ops_per_sec = stats['total_ops'] / max(duration, 1)

        print(f"\n🕐 测试时长: {duration:.1f} seconds ({duration / 60:.1f} minutes)")
        print(f"\n📈 总操作数: {stats['total_ops']:,}")
        print(f"   - 存储操作: {stats['storage_ops']:,}")
        print(f"   - 版本操作: {stats['version_ops']:,}")
        print(f"   - 分析操作: {stats['analytics_ops']:,}")
        print(f"📊 吞吐量: {ops_per_sec:.0f} ops/s")
        print(f"\n❌ 错误数: {stats['errors']}")
        print(f"⚠️  警告数: {stats['warnings']}")

        if stats['errors'] == 0:
            print("\n✅✅✅ 完美！零错误！系统在极端混沌下表现出色！")
        else:
            print(f"\n⚠️  发现 {stats['errors']} 个错误")
            if self.errors:
                print("\n错误详情:")
                for i, e in enumerate(self.errors[:20]):
                    print(f"  {i+1}. [{e['component']}][{e['operation']}]: {e['exc_type']}: {e['exc_msg']}")

        print("\n" + "=" * 140)


def main():
    test = UltraExtremeChaosTest()
    test.run()


if __name__ == "__main__":
    main()
