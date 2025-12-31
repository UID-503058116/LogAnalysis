"""MCP 工具定义。"""

from typing import Any

from mcp.types import Tool

from logginganalysis.mcp.server import AVAILABLE_TOOLS


def get_tools() -> list[Tool]:
    """获取所有可用的 MCP 工具。"""
    return AVAILABLE_TOOLS


def get_tool(name: str) -> Tool | None:
    """根据名称获取工具。"""
    for tool in AVAILABLE_TOOLS:
        if tool.name == name:
            return tool
    return None


def validate_tool_arguments(name: str, arguments: dict[str, Any]) -> tuple[bool, str | None]:
    """验证工具参数。

    Args:
        name: 工具名称
        arguments: 参数字典

    Returns:
        tuple: (是否有效, 错误消息)
    """
    tool = get_tool(name)
    if tool is None:
        return False, f"未知的工具: {name}"

    schema = tool.inputSchema
    if not schema:
        return True, None

    # 检查必需参数
    required = schema.get("required", [])
    for param in required:
        if param not in arguments or not arguments[param]:
            return False, f"缺少必需参数: {param}"

    # 检查参数类型
    properties = schema.get("properties", {})
    for param, value in arguments.items():
        if param in properties:
            param_schema = properties[param]
            param_type = param_schema.get("type")

            # 简单类型检查
            if param_type == "string" and not isinstance(value, str):
                return False, f"参数 {param} 应该是字符串"
            elif param_type == "boolean" and not isinstance(value, bool):
                return False, f"参数 {param} 应该是布尔值"
            elif param_type == "number" and not isinstance(value, (int, float)):
                return False, f"参数 {param} 应该是数字"
            elif param_type == "array" and not isinstance(value, list):
                return False, f"参数 {param} 应该是数组"

            # 检查枚举值
            if "enum" in param_schema and value not in param_schema["enum"]:
                return False, f"参数 {param} 的值无效，允许的值: {param_schema['enum']}"

    return True, None
