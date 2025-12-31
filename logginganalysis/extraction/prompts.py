"""提取模块的提示词模板。"""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# 提取阶段的系统提示词
EXTRACTION_SYSTEM_PROMPT = """你是一位专业的日志分析专家。你的任务是从日志块中提取关键信息。

请从给定的日志块中提取以下信息：

1. **异常信息 (exceptions)**：
   - type: 异常类型（如 ConnectionError, ValueError）
   - message: 异常消息
   - stack_trace: 堆栈跟踪信息（单个字符串，不是列表）
   - occurrence_count: 出现次数（默认1）
   - severity: 严重程度（可选：low, medium, high, critical）

2. **库引用 (libraries)**：
   - name: 库、框架或工具名称（必填）
   - version: 版本信息（可选）
   - context: 引用上下文信息（可选）
   - path: 库路径（可选）
   - type: 库类型（可选，如 mod, framework, library）
   - source: 来源信息（可选）

3. **问题行为 (problematic_behaviors)**：
   - category: 问题类别（可选，如：database、network、memory、performance、native_library、security、launch_tweaking）
   - description: 问题描述（必填）
   - severity: 严重程度（仅限以下值：low, medium, high, critical；默认medium）
   - details: 详细信息（可选）
   - context: 上下文信息（可选）
   - occurrences: 相关的日志行列表（可选）

4. **摘要 (summary)**：
   - 用1-2句话总结该日志块的主要内容（必填）

重要提示：
- stack_trace 必须是字符串类型，如果是多行堆栈请用换行符连接
- 不要包含 chunk_id 字段（该字段由系统自动填充）
- 如果没有找到某类信息，请返回空列表
- 保持客观，不要添加不存在的信息"""

# 提取阶段的人类提示词模板
EXTRACTION_HUMAN_PROMPT = """请分析以下日志块并提取关键信息：

```
{log_chunk}
```

{format_instructions}

请提供结构化的输出，包含：
- exceptions: 异常列表
- libraries: 库引用列表
- problematic_behaviors: 问题行为列表
- summary: 简要摘要（1-2句话）"""

# 创建提取提示词模板
extraction_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", EXTRACTION_SYSTEM_PROMPT),
        ("human", EXTRACTION_HUMAN_PROMPT),
    ]
)

# 简化版提示词（用于较小的日志块）
SIMPLE_EXTRACTION_SYSTEM_PROMPT = """你是一位日志分析助手。请从日志中提取：
1. 异常（类型和消息）
2. 提到的库或框架
3. 任何问题或错误行为

如果没有某类信息，请返回空列表。保持简洁。"""

simple_extraction_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SIMPLE_EXTRACTION_SYSTEM_PROMPT),
        ("human", "分析日志：\n\n{log_chunk}"),
    ]
)

# 用于带格式的输出（JSON结构）
STRUCTURED_OUTPUT_INSTRUCTIONS = """请以JSON格式输出，包含以下字段：
{
  "exceptions": [
    {
      "type": "异常类型",
      "message": "异常消息",
      "stack_trace": "堆栈跟踪（字符串格式，多行用\\n连接）",
      "occurrence_count": 出现次数（默认1）,
      "severity": "严重程度（可选：low, medium, high, critical）"
    }
  ],
  "libraries": [
    {
      "name": "库名称",
      "version": "版本（可选）",
      "context": "上下文信息（可选）",
      "path": "路径（可选）",
      "type": "类型（可选）",
      "source": "来源（可选）"
    }
  ],
  "problematic_behaviors": [
    {
      "category": "类别（可选：database, network, performance, native_library, security, launch_tweaking）",
      "description": "问题描述",
      "severity": "严重程度（仅限：low, medium, high, critical）",
      "details": "详细信息（可选）",
      "context": "上下文（可选）",
      "occurrences": ["相关的日志行"]
    }
  ],
  "summary": "简要摘要"
}

注意：不要包含 chunk_id 字段。"""
