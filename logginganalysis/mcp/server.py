"""MCP 服务器实现。

将日志分析功能作为 MCP 工具暴露给 LLM。
"""

import asyncio
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from logginganalysis.config.settings import get_settings
from logginganalysis.models.report import AnalysisReport
from logginganalysis.reporting import get_formatter
from logginganalysis.utils.exceptions import LoggingAnalysisError


# 创建 MCP 服务器实例
mcp_server = Server("logginganalysis")


# 定义可用的工具
AVAILABLE_TOOLS: list[Tool] = [
    Tool(
        name="analyze_log",
        description="分析日志内容并生成综合报告。提取异常、库引用和问题行为，然后生成综合分析。",
        inputSchema={
            "type": "object",
            "properties": {
                "log_content": {
                    "type": "string",
                    "description": "要分析的日志内容",
                },
                "format": {
                    "type": "string",
                    "enum": ["markdown", "json", "text"],
                    "description": "输出格式（默认：markdown）",
                },
                "enable_search": {
                    "type": "boolean",
                    "description": "是否启用网页搜索获取额外上下文（默认：false）",
                },
            },
            "required": ["log_content"],
        },
    ),
    Tool(
        name="extract_log_info",
        description="从日志中快速提取关键信息（异常、库、问题行为），不进行综合分析。",
        inputSchema={
            "type": "object",
            "properties": {
                "log_content": {
                    "type": "string",
                    "description": "要分析的日志内容",
                },
            },
            "required": ["log_content"],
        },
    ),
]


@mcp_server.list_tools()
async def list_tools() -> list[Tool]:
    """列出所有可用的 MCP 工具。"""
    return AVAILABLE_TOOLS


@mcp_server.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """处理 MCP 工具调用。

    Args:
        name: 工具名称
        arguments: 工具参数

    Returns:
        list[TextContent]: 工具执行结果
    """
    try:
        if name == "analyze_log":
            return await _handle_analyze_log(arguments)
        elif name == "extract_log_info":
            return await _handle_extract_log_info(arguments)
        else:
            return [
                TextContent(
                    type="text",
                    text=f"错误：未知的工具 '{name}'",
                )
            ]

    except LoggingAnalysisError as e:
        return [
            TextContent(
                type="text",
                text=f"分析错误: {e.message}",
            )
        ]
    except Exception as e:
        return [
            TextContent(
                type="text",
                text=f"意外错误: {str(e)}",
            )
        ]


async def _handle_analyze_log(arguments: dict) -> list[TextContent]:
    """处理 analyze_log 工具调用。"""
    from logginganalysis import LogAnalyzer

    log_content = arguments.get("log_content", "")
    output_format = arguments.get("format", "markdown")
    enable_search = arguments.get("enable_search", False)

    if not log_content:
        return [TextContent(type="text", text="错误：日志内容不能为空")]

    # 创建分析器
    analyzer = LogAnalyzer()

    # 执行分析
    report = await analyzer.analyze(
        log_content=log_content,
        enable_search=enable_search,
    )

    # 格式化输出
    formatter = get_formatter(output_format)
    formatted_report = formatter.format(report)

    return [TextContent(type="text", text=formatted_report)]


async def _handle_extract_log_info(arguments: dict) -> list[TextContent]:
    """处理 extract_log_info 工具调用。"""
    from logginganalysis.chunking import LogChunker
    from logginganalysis.extraction import LogExtractor
    from logginganalysis.reporting import JSONFormatter

    log_content = arguments.get("log_content", "")

    if not log_content:
        return [TextContent(type="text", text="错误：日志内容不能为空")]

    # 分块
    settings = get_settings()
    chunker = LogChunker(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )
    chunks = chunker.chunk_log(log_content)

    # 提取
    extractor = LogExtractor()
    extractions = await extractor.extract_from_chunks(chunks)

    # 汇总结果
    import json

    summary = {
        "total_chunks": len(chunks.chunks),
        "extractions": [
            {
                "chunk_id": e.chunk_id,
                "summary": e.summary,
                "exceptions": [
                    {"type": exc.type, "message": exc.message, "count": exc.occurrence_count}
                    for exc in e.exceptions
                ],
                "libraries": [
                    {"name": lib.name, "version": lib.version} for lib in e.libraries
                ],
                "problems": [
                    {
                        "category": pb.category,
                        "description": pb.description,
                        "severity": pb.severity,
                    }
                    for pb in e.problematic_behaviors
                ],
            }
            for e in extractions
        ],
    }

    return [TextContent(type="text", text=json.dumps(summary, ensure_ascii=False, indent=2))]


async def main() -> None:
    """启动 MCP 服务器。"""
    settings = get_settings()

    async with stdio_server() as (read_stream, write_stream):
        await mcp_server.run(
            read_stream,
            write_stream,
            mcp_server.create_initialization_options(),
        )


def main_sync() -> None:
    """同步入口点（用于 CLI）。"""
    asyncio.run(main())


if __name__ == "__main__":
    main_sync()
