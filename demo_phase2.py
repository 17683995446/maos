#!/usr/bin/env python3
"""
MAOS v6.0 - 错误处理和容错演示
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asyncio


def print_header(title: str):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


async def demo_circuit_breaker():
    """演示断路器"""
    from maos.resilience import CircuitBreaker, CircuitBreakerConfig, CircuitBreakerOpen, CircuitState
    
    print_header("1. Circuit Breaker Demo")
    
    config = CircuitBreakerConfig(
        failure_threshold=3,
        success_threshold=2,
        timeout=5.0
    )
    breaker = CircuitBreaker("test-service", config)
    
    print("\n📋 Testing Circuit Breaker...")
    
    # 模拟失败
    async def failing_function():
        raise Exception("Service unavailable")
    
    for i in range(5):
        try:
            await breaker.call(failing_function)
            print(f"   Attempt {i+1}: Success")
        except CircuitBreakerOpen:
            print(f"   Attempt {i+1}: Circuit OPEN")
        except Exception as e:
            status = breaker.get_status()
            print(f"   Attempt {i+1}: Failed - State: {status['state']}, Failures: {status['failure_count']}")
    
    # 等待超时
    print("\n⏰ Waiting for timeout (5s)...")
    await asyncio.sleep(5.5)
    
    # 模拟成功
    async def success_function():
        return "Success!"
    
    print("\n📋 Testing recovery...")
    for i in range(4):
        try:
            result = await breaker.call(success_function)
            status = breaker.get_status()
            print(f"   Attempt {i+1}: {result} - State: {status['state']}")
        except Exception as e:
            print(f"   Attempt {i+1}: {e}")
    
    print(f"\n✅ Final State: {breaker.get_status()['state']}")


async def demo_retry():
    """演示重试机制"""
    from maos.resilience import Retry, RetryConfig, RetryStrategy, RetryExhausted
    
    print_header("2. Retry Mechanism Demo")
    
    retry_instance = Retry(RetryConfig(
        max_attempts=3,
        initial_delay=0.5,
        strategy=RetryStrategy.EXPONENTIAL,
        jitter=True
    ))
    
    attempt_count = 0
    
    async def flaky_function():
        nonlocal attempt_count
        attempt_count += 1
        
        if attempt_count < 3:
            raise Exception(f"Attempt {attempt_count} failed")
        
        return f"Success on attempt {attempt_count}"
    
    print(f"\n📋 Testing retry with exponential backoff...")
    print(f"   Max attempts: 3")
    print(f"   Initial delay: 0.5s")
    print(f"   Strategy: Exponential")
    
    try:
        result = await retry_instance.execute(flaky_function)
        print(f"\n   ✅ Result: {result}")
        print(f"   📊 Total attempts: {retry_instance.attempts}")
    except RetryExhausted as e:
        print(f"\n   ❌ Retry exhausted: {e}")


async def demo_error_handler():
    """演示错误处理器"""
    from maos.resilience import ErrorHandler, ErrorCategory
    
    print_header("3. Error Handler Demo")
    
    handler = ErrorHandler()
    
    # 模拟各种错误
    errors = [
        Exception("Connection timeout"),
        Exception("Memory allocation failed"),
        Exception("Authentication failed"),
        Exception("Rate limit exceeded"),
        Exception("Invalid configuration"),
        Exception("Unexpected null pointer")
    ]
    
    print("\n📋 Processing errors...")
    
    for i, error in enumerate(errors, 1):
        maos_error = handler.handle(error, {'context': f'task_{i}'})
        print(f"   Error {i}:")
        print(f"      Code: {maos_error.code}")
        print(f"      Category: {maos_error.category.value}")
    
    # 显示摘要
    summary = handler.get_error_summary()
    print(f"\n📊 Error Summary:")
    print(f"   Total Errors: {summary['total_errors']}")
    print(f"   By Category:")
    for category, count in summary['by_category'].items():
        print(f"      {category}: {count}")


async def demo_resilience():
    """演示综合弹性"""
    from maos.resilience import CircuitBreaker, Retry, RetryConfig, ErrorHandler
    from maos.resilience import CircuitBreakerConfig, RetryStrategy
    
    print_header("4. Combined Resilience Demo")
    
    circuit_breaker = CircuitBreaker("resilient-service", CircuitBreakerConfig(
        failure_threshold=2,
        timeout=3.0
    ))
    
    retry = Retry(RetryConfig(
        max_attempts=2,
        initial_delay=0.3,
        strategy=RetryStrategy.LINEAR
    ))
    
    handler = ErrorHandler()
    
    attempt = 0
    
    async def resilient_operation():
        nonlocal attempt
        attempt += 1
        
        # 模拟不稳定的服务
        if attempt in [1, 2]:
            raise Exception("Transient failure")
        return f"Operation succeeded on attempt {attempt}"
    
    print("\n📋 Running resilient operation...")
    
    for i in range(5):
        attempt = 0
        try:
            result = await circuit_breaker.call(
                retry.execute,
                resilient_operation
            )
            print(f"   Run {i+1}: ✅ {result}")
        except Exception as e:
            maos_error = handler.handle(e, {'run': i+1})
            print(f"   Run {i+1}: ❌ {maos_error.category.value} - {maos_error.message}")
    
    print(f"\n📊 Final Circuit Breaker State: {circuit_breaker.get_status()['state']}")


async def main():
    """主函数"""
    print("")
    print("╔══════════════════════════════════════════════════════════════════════════╗")
    print("║    MAOS v6.0 - Error Handling & Fault Tolerance Demo                  ║")
    print("╚══════════════════════════════════════════════════════════════════════════╝")
    
    await demo_circuit_breaker()
    await demo_retry()
    await demo_error_handler()
    await demo_resilience()
    
    print("\n" + "=" * 80)
    print("  🎉 Resilience Demo Complete!")
    print("=" * 80)
    print("\n📚 Key Features:")
    print("   ✅ Circuit Breaker - Prevent cascading failures")
    print("   ✅ Retry Mechanism - Handle transient errors")
    print("   ✅ Error Classification - Organized error handling")
    print("   ✅ Error Handler - Centralized error management")
    print("\n📝 Implementation: maos/resilience.py")


if __name__ == "__main__":
    asyncio.run(main())
