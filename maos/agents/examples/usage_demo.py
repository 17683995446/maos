"""
MAOS Agents使用示例演示
展示如何使用示例Agents进行数据处理、分析和报告生成
"""

import asyncio
from maos.agents.examples import (
    DataProcessingAgent,
    AnalysisAgent,
    ReportingAgent
)
from maos.core import AgentOptions, AgentMessage


async def demo_data_processing():
    """数据处理Agent演示"""
    print("\n" + "="*60)
    print("演示1: 数据处理Agent")
    print("="*60)

    agent = DataProcessingAgent(AgentOptions(
        name="DataProcessor",
        description="数据清洗和转换Agent",
        capabilities=["data_cleaning", "data_transformation", "data_validation"],
        log_debug_trace=True
    ))

    print(f"\n1. Agent信息: {agent.get_info()}")

    test_records = [
        {"id": "001", "name": "张三", "email": "zhangsan@example.com", "age": 28, "score": 95.5},
        {"id": "002", "name": "李四", "email": "", "age": 24, "score": 88.0},
        {"id": "003", "name": "王五", "email": "wangwu@example.com", "age": 31, "score": None},
        {"id": "004", "name": "", "email": "invalid", "age": 29, "score": 92.0},
    ]

    message = AgentMessage(
        sender="demo",
        receivers=["data-processor"],
        content={"input": test_records}
    )

    print("\n2. 发送数据处理请求...")
    response = await agent.process_message(message)

    print(f"3. 处理状态: {response.content.get('status')}")
    print(f"4. 处理记录数: {response.content.get('records_processed')}")

    schema = {
        'id': {'required': True, 'type': 'string'},
        'name': {'required': True, 'type': 'string'},
        'age': {'required': True, 'type': 'int', 'min': 0, 'max': 150}
    }

    validation_result = agent.validate_data(test_records[0], schema)
    print(f"5. 数据验证: {'通过' if validation_result['valid'] else '失败'}")


async def demo_analysis():
    """分析Agent演示"""
    print("\n" + "="*60)
    print("演示2: 分析Agent")
    print("="*60)

    agent = AnalysisAgent(AgentOptions(
        name="Analyzer",
        description="数据分析Agent",
        capabilities=["data_analysis", "statistical_analysis", "pattern_recognition"],
        log_debug_trace=True
    ))

    test_data = {
        'users': 1000,
        'revenue': 50000.50,
        'active_sessions': 250,
        'conversion_rate': 0.15,
        'avg_order_value': 125.00
    }

    message = AgentMessage(
        sender="demo",
        receivers=["analyzer"],
        content={"input": test_data}
    )

    print("\n1. 发送分析请求...")
    response = await agent.process_message(message)

    print(f"2. 分析状态: {response.content.get('status')}")
    analysis = response.content.get('analysis', {})

    print(f"3. 分析类型: {analysis.get('analysis_type')}")
    print(f"4. 总字段数: {analysis.get('total_fields')}")
    print(f"5. 数值字段: {analysis.get('field_types', {}).get('numeric', [])}")
    print(f"6. 检测到的模式: {list(analysis.get('patterns_detected', {}).keys())}")

    numeric_data = [95.5, 88.0, 92.0, 78.5, 99.0, 85.5]
    stats = agent.calculate_statistics(numeric_data)
    print(f"7. 数值统计: 均值={stats.get('mean'):.2f}, "
          f"最小={stats.get('min')}, 最大={stats.get('max')}")


async def demo_reporting():
    """报告生成Agent演示"""
    print("\n" + "="*60)
    print("演示3: 报告生成Agent")
    print("="*60)

    agent = ReportingAgent(AgentOptions(
        name="Reporter",
        description="报告生成Agent",
        capabilities=["report_generation", "format_conversion", "data_visualization"],
        log_debug_trace=True
    ))

    sales_data = {
        'total_sales': 150000,
        'orders': 450,
        'top_product': 'Widget A',
        'avg_rating': 4.5,
        'returns': 15
    }

    for format_type in ['summary', 'text', 'detailed']:
        message = AgentMessage(
            sender="demo",
            receivers=["reporter"],
            content={
                "input": sales_data,
                "format": format_type,
                "title": f"Sales Report ({format_type})"
            }
        )

        print(f"\n生成 {format_type} 格式报告...")
        response = await agent.process_message(message)

        print(f"  状态: {response.content.get('status')}")
        print(f"  格式: {response.content.get('format')}")

        if format_type == 'summary':
            content = response.content.get('report', {}).get('content', {})
            print(f"  摘要键: {list(content.keys())}")
        elif format_type == 'text':
            content = response.content.get('report', {}).get('content', '')
            print(f"  报告长度: {len(content)} 字符")


async def demo_workflow():
    """完整工作流演示"""
    print("\n" + "="*60)
    print("演示4: 完整工作流（数据处理 -> 分析 -> 报告）")
    print("="*60)

    data_agent = DataProcessingAgent(AgentOptions(name="DataProcessor"))
    analysis_agent = AnalysisAgent(AgentOptions(name="Analyzer"))
    reporting_agent = ReportingAgent(AgentOptions(name="Reporter"))

    print("\n1. 原始数据...")
    raw_data = [
        {"id": "001", "name": "产品A", "price": 99.99, "quantity": 10},
        {"id": "002", "name": "产品B", "price": "", "quantity": 5},
        {"id": "003", "name": "产品C", "price": 149.99, "quantity": 8},
        {"id": "004", "name": "", "price": 79.99, "quantity": 12},
    ]
    print(f"  记录数: {len(raw_data)}")

    print("\n2. 数据处理阶段...")
    data_msg = AgentMessage(sender="workflow", receivers=["data-processor"],
                            content={"input": raw_data})
    data_response = await data_agent.process_message(data_msg)
    processed_data = data_response.content.get('processed_data', [])
    print(f"  处理后记录数: {len(processed_data)}")

    print("\n3. 数据分析阶段...")
    analysis_msg = AgentMessage(sender="workflow", receivers=["analyzer"],
                                content={"input": processed_data})
    analysis_response = await analysis_agent.process_message(analysis_msg)
    analysis_result = analysis_response.content.get('analysis', {})
    print(f"  分析类型: {analysis_result.get('analysis_type')}")

    print("\n4. 报告生成阶段...")
    report_msg = AgentMessage(sender="workflow", receivers=["reporter"],
                              content={
                                  "input": {
                                      "processed_records": processed_data,
                                      "analysis": analysis_result
                                  },
                                  "format": "detailed",
                                  "title": "数据处理完整报告"
                              })
    report_response = await reporting_agent.process_message(report_msg)
    print(f"  报告状态: {report_response.content.get('status')}")
    print(f"  报告格式: {report_response.content.get('format')}")


async def main():
    """运行所有演示"""
    print("\n" + "="*60)
    print("MAOS Agents使用示例演示")
    print("="*60)

    await demo_data_processing()
    await demo_analysis()
    await demo_reporting()
    await demo_workflow()

    print("\n" + "="*60)
    print("所有演示完成！")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
