"""命令行入口点。"""

import argparse
import asyncio
import sys
from pathlib import Path

from logginganalysis import LogAnalyzer
from logginganalysis.utils.exceptions import LoggingAnalysisError


async def main() -> None:
    """主入口函数。"""
    parser = argparse.ArgumentParser(
        description="LoggingAnalysis - AI驱动的日志分析工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "log_file",
        type=str,
        nargs="?",
        help="要分析的日志文件路径",
    )
    parser.add_argument(
        "-f",
        "--format",
        type=str,
        choices=["markdown", "json", "text"],
        default="markdown",
        help="输出格式（默认：markdown）",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="输出文件路径（默认：标准输出）",
    )
    parser.add_argument(
        "-s",
        "--enable-search",
        action="store_true",
        help="启用网页搜索获取额外上下文",
    )
    parser.add_argument(
        "--mcp",
        action="store_true",
        help="以 MCP 服务器模式运行",
    )

    args = parser.parse_args()

    # MCP 模式
    if args.mcp:
        from logginganalysis.mcp import main_sync

        main_sync()
        return

    # 检查是否提供了日志文件
    if not args.log_file:
        parser.print_help()
        print("\n错误：需要指定日志文件路径或使用 --mcp 启动 MCP 服务器")
        sys.exit(1)

    # 分析模式
    log_path = Path(args.log_file)
    if not log_path.exists():
        print(f"错误：文件不存在: {log_path}", file=sys.stderr)
        sys.exit(1)

    try:
        # 创建分析器
        analyzer = LogAnalyzer()

        # 分析日志
        print(f"正在分析日志文件: {log_path}", file=sys.stderr)

        result = await analyzer.analyze_file_to_string(
            file_path=str(log_path),
            enable_search=args.enable_search,
            output_format=args.format,
        )

        # 输出结果
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(result, encoding="utf-8")
            print(f"报告已保存到: {output_path}", file=sys.stderr)
        else:
            print(result)

    except LoggingAnalysisError as e:
        print(f"分析失败: {e.message}", file=sys.stderr)
        if e.details:
            print(f"详情: {e.details}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"意外错误: {e}", file=sys.stderr)
        sys.exit(1)


def main_sync() -> None:
    """同步入口点（用于 CLI）。"""
    asyncio.run(main())


if __name__ == "__main__":
    main_sync()
