#!/usr/bin/env python3
"""
版本管理并发Bug诊断
"""

import sys
import time
import random
import threading
import traceback

sys.path.insert(0, '/workspace')

from maos.version.v14 import VersionManager


def diagnose_concurrent_versions():
    """诊断并发版本管理问题"""
    print("="*80)
    print("诊断: 并发版本管理 AttributeError")
    print("="*80)
    
    vm = VersionManager()
    errors = []
    lock = threading.Lock()
    
    def version_spammer(i):
        for j in range(100):
            try:
                op = random.choice(['create', 'get', 'list', 'delete'])
                
                wf_id = f"spam_wf_{i % 10}"
                
                if op == 'create':
                    v = vm.create_version(wf_id, {"spam": f"{i}_{j}"})
                elif op == 'get':
                    versions = vm.list_versions(wf_id)
                    if versions:
                        v = vm.get_version(random.choice(versions).id)
                elif op == 'list':
                    vm.list_versions(wf_id)
                else:  # delete
                    versions = vm.list_versions(wf_id)
                    if versions:
                        vm.delete_version(random.choice(versions).id)
                        
            except Exception as e:
                with lock:
                    tb = traceback.format_exc()
                    errors.append({
                        'thread': i,
                        'op': op,
                        'error': f"{type(e).__name__}: {str(e)}",
                        'traceback': tb
                    })
    
    print("启动并发测试...")
    threads = []
    for i in range(200):
        t = threading.Thread(target=version_spammer, args=(i,))
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    print(f"\n发现 {len(errors)} 个错误")
    
    if errors:
        # 按错误类型分组
        by_error = {}
        for err in errors:
            key = err['error']
            if key not in by_error:
                by_error[key] = []
            by_error[key].append(err)
        
        print("\n错误统计:")
        for error, errs in by_error.items():
            print(f"  {error}: {len(errs)}次")
        
        print("\n第一个错误的详细信息:")
        first = errors[0]
        print(f"线程: {first['thread']}")
        print(f"操作: {first['op']}")
        print(f"错误: {first['error']}")
        print("\n完整堆栈:")
        print(first['traceback'])


if __name__ == "__main__":
    diagnose_concurrent_versions()
