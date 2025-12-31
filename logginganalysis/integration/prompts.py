"""集成模块的提示词模板。"""

from langchain_core.prompts import ChatPromptTemplate

# 集成阶段的系统提示词
INTEGRATION_SYSTEM_PROMPT = """你是一位资深的系统分析师。你的任务是基于多个日志块的提取结果，生成一份综合分析报告。

请综合分析以下提取结果，并提供：

1. **整体摘要 (overall_summary)**：
   - 系统整体状态的概述
   - 主要问题和趋势
   - 影响范围的评估
   - **重要**：在摘要中描述错误链，展示错误是如何从一个初始问题逐步引发其他问题的

2. **关键发现 (key_findings)**：
   - 按类别组织的重要发现（如数据库、网络、性能、安全等）
   - 每个发现应包含：
     - category: 发现类别
     - description: 详细描述
     - evidence: 支持该发现的证据（引用具体的日志信息）
     - recommendations: 针对性的建议和解决方案

3. **错误链 (error_chain)**：
   - 如果检测到多个相关的错误，构建错误链展示因果关系
   - 应包含：
     - root_cause: 根本原因描述
     - chain: 错误传播链步骤列表，每步包含：
       - step: 步骤编号（从1开始）
       - event: 发生的事件
       - impact: 该事件造成的影响
     - final_outcome: 最终结果
   - 如果没有明显的错误链，返回 null

4. **根因分析 (root_cause_analysis)**：
   - 如果检测到问题，分析可能的根本原因
   - 解释问题之间的关联性
   - 识别问题的来源（如配置错误、代码缺陷、资源限制等）

5. **系统环境 (system_context)**：
   - 推断的系统环境信息，如：
     - 编程语言和框架
     - 数据库类型
     - 部署环境（如容器、云服务）
     - 第三方依赖

6. **置信度评分 (confidence_score)**：
   - 对分析的置信程度（0.0-1.0）
   - 考虑因素：日志完整性、信息清晰度、证据充分性

保持分析客观、准确，基于提供的提取结果，不要添加不存在的信息。"""

# 集成阶段的人类提示词模板
INTEGRATION_HUMAN_PROMPT = """请综合分析以下日志提取结果：

**分析概要**：
- 总日志块数：{chunk_count}
- 总异常数：{total_exceptions}
- 总问题行为数：{total_behaviors}
- 检测到的库：{library_count}

**详细提取结果**：
{extractions_summary}

{format_instructions}

请提供一份综合分析报告，包含整体摘要（描述错误链）、关键发现、错误链详情、根因分析、系统环境推断和置信度评分。"""

# 创建集成提示词模板
integration_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", INTEGRATION_SYSTEM_PROMPT),
        ("human", INTEGRATION_HUMAN_PROMPT),
    ]
)

# 简化版集成提示词
SIMPLE_INTEGRATION_SYSTEM_PROMPT = """你是一位系统分析师。请基于日志提取结果生成综合分析。

重点关注：
1. 整体摘要
2. 关键问题和发现
3. 可能的根本原因
4. 系统环境推断
5. 分析置信度（0-1）"""

simple_integration_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SIMPLE_INTEGRATION_SYSTEM_PROMPT),
        ("human", "分析结果：\n\n{extractions_summary}"),
    ]
)

# 用于格式化提取结果的辅助函数
def format_extractions_for_integration(
    extractions: list,
) -> str:
    """格式化提取结果用于集成分析。

    Args:
        extractions: 提取结果列表

    Returns:
        str: 格式化后的提取结果
    """
    if not extractions:
        return "无提取结果"

    summary_parts = []

    for i, extraction in enumerate(extractions, 1):
        part = f"## 块 {i} (ID: {extraction.get('chunk_id', 'unknown')})\n"
        part += f"摘要: {extraction.get('summary', '无')}\n"

        # 异常
        exceptions = extraction.get("exceptions", [])
        if exceptions:
            part += f"\n异常 ({len(exceptions)}):\n"
            for exc in exceptions:
                part += f"  - {exc.get('type', 'Unknown')}: {exc.get('message', 'No message')}\n"
                if exc.get("occurrence_count", 1) > 1:
                    part += f"    出现次数: {exc['occurrence_count']}\n"

        # 库引用
        libraries = extraction.get("libraries", [])
        if libraries:
            part += f"\n库引用 ({len(libraries)}):\n"
            for lib in libraries:
                version = f" v{lib['version']}" if lib.get('version') else ""
                part += f"  - {lib['name']}{version}\n"

        # 问题行为
        behaviors = extraction.get("problematic_behaviors", [])
        if behaviors:
            part += f"\n问题行为 ({len(behaviors)}):\n"
            for beh in behaviors:
                part += f"  - [{beh.get('severity', 'medium')}] {beh.get('category', 'Unknown')}: {beh.get('description', 'No description')}\n"

        summary_parts.append(part)

    return "\n\n".join(summary_parts)
