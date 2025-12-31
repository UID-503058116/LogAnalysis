"""MCP 工具测试。"""

import pytest

from logginganalysis.mcp.tools import get_tool, get_tools, validate_tool_arguments


class TestMCPTools:
    """MCP 工具测试。"""

    def test_get_tools_returns_list(self):
        """测试获取工具列表。"""
        tools = get_tools()
        assert isinstance(tools, list)
        assert len(tools) > 0

    def test_get_tools_has_required_tools(self):
        """测试工具列表包含必需的工具。"""
        tools = get_tools()
        tool_names = [tool.name for tool in tools]

        assert "analyze_log" in tool_names
        assert "extract_log_info" in tool_names

    def test_get_tool_by_name(self):
        """测试通过名称获取工具。"""
        tool = get_tool("analyze_log")
        assert tool is not None
        assert tool.name == "analyze_log"
        assert tool.description is not None
        assert tool.inputSchema is not None

    def test_get_nonexistent_tool(self):
        """测试获取不存在的工具。"""
        tool = get_tool("nonexistent_tool")
        assert tool is None

    def test_validate_analyze_log_arguments_valid(self):
        """测试验证有效的 analyze_log 参数。"""
        valid, error = validate_tool_arguments(
            "analyze_log",
            {"log_content": "Sample log content", "format": "markdown"},
        )
        assert valid is True
        assert error is None

    def test_validate_analyze_log_missing_required(self):
        """测试验证缺少必需参数。"""
        valid, error = validate_tool_arguments("analyze_log", {})
        assert valid is False
        assert "log_content" in error

    def test_validate_analyze_log_invalid_format(self):
        """测试验证无效的格式参数。"""
        valid, error = validate_tool_arguments(
            "analyze_log", {"log_content": "test", "format": "invalid_format"}
        )
        assert valid is False
        assert "format" in error.lower()

    def test_validate_analyze_log_valid_formats(self):
        """测试验证所有有效的格式。"""
        formats = ["markdown", "json", "text"]
        for fmt in formats:
            valid, error = validate_tool_arguments(
                "analyze_log", {"log_content": "test", "format": fmt}
            )
            assert valid is True, f"Format {fmt} should be valid"

    def test_validate_extract_log_info_valid(self):
        """测试验证有效的 extract_log_info 参数。"""
        valid, error = validate_tool_arguments(
            "extract_log_info", {"log_content": "Sample log"}
        )
        assert valid is True
        assert error is None

    def test_validate_extract_log_info_missing_content(self):
        """测试验证缺少日志内容。"""
        valid, error = validate_tool_arguments("extract_log_info", {})
        assert valid is False
        assert "log_content" in error

    def test_validate_unknown_tool(self):
        """测试验证未知工具。"""
        valid, error = validate_tool_arguments("unknown_tool", {})
        assert valid is False
        assert "unknown" in error.lower()

    def test_analyze_log_input_schema(self):
        """测试 analyze_log 的输入模式。"""
        tool = get_tool("analyze_log")
        schema = tool.inputSchema

        assert schema["type"] == "object"
        assert "properties" in schema
        assert "log_content" in schema["properties"]
        assert "format" in schema["properties"]
        assert "required" in schema
        assert "log_content" in schema["required"]

    def test_extract_log_info_input_schema(self):
        """测试 extract_log_info 的输入模式。"""
        tool = get_tool("extract_log_info")
        schema = tool.inputSchema

        assert schema["type"] == "object"
        assert "properties" in schema
        assert "log_content" in schema["properties"]

    def test_analyze_log_format_enum(self):
        """测试 analyze_log 格式枚举。"""
        tool = get_tool("analyze_log")
        format_property = tool.inputSchema["properties"]["format"]

        assert format_property["type"] == "string"
        assert "enum" in format_property
        assert set(format_property["enum"]) == {"markdown", "json", "text"}

    def test_analyze_log_enable_search_boolean(self):
        """测试 analyze_log enable_search 参数类型。"""
        tool = get_tool("analyze_log")
        search_property = tool.inputSchema["properties"]["enable_search"]

        assert search_property["type"] == "boolean"

    def test_tool_descriptions_not_empty(self):
        """测试工具描述不为空。"""
        tools = get_tools()
        for tool in tools:
            assert tool.description
            assert len(tool.description) > 0
