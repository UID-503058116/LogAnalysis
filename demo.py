import sys
import json
import asyncio
import argparse
from pathlib import Path
from logginganalysis import LogAnalyzer
from logginganalysis.chunking import LogChunker
from logginganalysis.utils.logging_config import setup_logging


def progress_callback(update):
    """进度回调函数。"""
    step = update.get("step", "unknown")
    message = update.get("message", "")
    progress = update.get("progress", "")

    if step == "extraction" and "chunk_index" in update:
        chunk_idx = update.get("chunk_index", 0)
        total = update.get("total_chunks", 0)
        status = update.get("status", "processing")

        if status == "completed":
            exceptions = update.get("exceptions_found", 0)
            behaviors = update.get("behaviors_found", 0)
            libraries = update.get("libraries_found", 0)
            print(
                f"\r  [{chunk_idx}/{total}] {progress} - "
                f"发现: {exceptions} 异常, {behaviors} 行为, {libraries} 库",
                end="",
                flush=True,
            )
        elif status == "failed":
            error = update.get("error", "未知错误")
            print(f"\n  ❌ [{chunk_idx}/{total}] 处理失败: {error}")
        else:
            print(f"\r  [{chunk_idx}/{total}] {progress} - 处理中...", end="", flush=True)
    elif progress:
        print(f"\n  ▶ {step.upper()}: {message} ({progress})")
    else:
        print(f"\n  ▶ {step.upper()}: {message}")


async def main():
    print("=" * 60)
    print("日志分析演示 - LoggingAnalysis Demo")
    print("=" * 60)

    # 配置日志系统
    print("\n[配置] 初始化日志系统...")
    setup_logging(level="INFO")
    print("[配置] 日志系统已就绪 (级别: INFO)")

    # 解析命令行参数
    parser = argparse.ArgumentParser()
    parser.add_argument("--log-file", type=Path, help="日志文件路径", required=True)
    parser.add_argument("--output-file", type=Path, help="报告文件路径", required=True)
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=4000,
        help="每个chunk的最大字符数（默认: 4000）",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=200,
        help="相邻chunk之间的重叠字符数（默认: 200）",
    )
    args = parser.parse_args()
    assert Path(args.log_file).exists(), f"日志文件 {args.log_file} 不存在"
    assert not Path(args.output_file).exists(), f"报告文件 {args.output_file} 已存在"

    # 进度跟踪
    progress_updates = []

    def wrapped_callback(update):
        progress_updates.append(update)
        progress_callback(update)

    # 创建分析器
    print("\n[初始化] 创建日志分析器...")
    print(f"[初始化] Chunk大小: {args.chunk_size} 字符, 重叠: {args.chunk_overlap} 字符")

    # 创建自定义chunker
    chunker = LogChunker(
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
    )

    analyzer = LogAnalyzer(chunker=chunker, progress_callback=wrapped_callback)
    print("[初始化] 分析器已就绪\n")

    # 读取日志文件
    log_file = str(args.log_file)
    print(f"[读取] 加载日志文件: {log_file}")
    try:
        with open(log_file, "r") as f:
            log_content = f.read()
        print(f"[读取] 成功读取 {len(log_content)} 字节\n")
    except FileNotFoundError:
        print(f"\n❌ 错误: 找不到日志文件 {log_file}")
        print("请确保文件存在后再运行此演示脚本。")
        sys.exit(1)

    # 开始分析
    print("=" * 60)
    print("开始分析")
    print("=" * 60)

    try:
        report = await analyzer.analyze(
            log_content=log_content, log_source=log_file, enable_search=False
        )
    except Exception as e:
        print(f"\n\n❌ 分析失败: {e}", file=sys.stderr)
        raise

    print("\n" + "=" * 60)
    print("分析完成!")
    print("=" * 60)

    # 显示进度统计
    print(f"\n📊 进度统计:")
    print(f"  总进度更新次数: {len(progress_updates)}")

    steps = {}
    for update in progress_updates:
        step = update.get("step", "unknown")
        steps[step] = steps.get(step, 0) + 1

    print(f"  各步骤更新次数:")
    for step, count in sorted(steps.items()):
        print(f"    - {step}: {count}")

    # 显示分析结果
    print("\n" + "=" * 60)
    print("分析结果 (Analysis Results)")
    print("=" * 60)

    print(f"\n📝 整体摘要 (Overall Summary)")
    print("-" * 60)
    print(report.analysis.overall_summary)
    print()

    if report.analysis.error_chain:
        print(f"\n🔗 错误链 (Error Chain)")
        print("-" * 60)
        print(f"根本原因: {report.analysis.error_chain.root_cause}")
        print()
        print("错误传播链:")
        for step in report.analysis.error_chain.chain:
            print(f"  步骤 {step.get('step')}:")
            print(f"    事件: {step.get('event')}")
            print(f"    影响: {step.get('impact')}")
        print()
        print(f"最终结果: {report.analysis.error_chain.final_outcome}")
        print()

    if report.analysis.key_findings:
        print(f"\n💡 关键发现 (Key Findings)")
        print("-" * 60)
        for finding in report.analysis.key_findings:
            print(f"\n【{finding.category}】")
            print(f"{finding.description}")
            if finding.evidence:
                print(f"  证据:")
                for e in finding.evidence:
                    print(f"    - {e}")
            if finding.recommendations:
                print(f"  建议:")
                for r in finding.recommendations:
                    print(f"    • {r}")
        print()

    if report.analysis.root_cause_analysis:
        print(f"\n🔍 根因分析 (Root Cause Analysis)")
        print("-" * 60)
        print(report.analysis.root_cause_analysis)
        print()

    if report.analysis.system_context:
        print(f"\n🖥️  系统环境 (System Context)")
        print("-" * 60)
        print(
            f"```json\n{json.dumps(report.analysis.system_context, ensure_ascii=False, indent=2)}\n```"
        )
        print()

    print(f"\n📈 置信度评分 (Confidence Score)")
    print("-" * 60)
    confidence = report.analysis.confidence_score
    bar_length = 20
    filled = int(bar_length * confidence)
    bar = "█" * filled + "░" * (bar_length - filled)
    print(f"[{bar}] {confidence:.2%}")

    # 写入完整报告到文件
    output_file = str(args.output_file)
    print(f"\n💾 正在保存报告到 {output_file}...")

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"# 日志分析报告\n\n")
        f.write(f"## 整体摘要\n\n{report.analysis.overall_summary}\n\n")

        if report.analysis.error_chain:
            f.write(f"## 错误链\n\n")
            f.write(f"**根本原因**: {report.analysis.error_chain.root_cause}\n\n")
            f.write(f"**错误传播链**:\n\n")
            for step in report.analysis.error_chain.chain:
                f.write(f"{step.get('step')}. **{step.get('event')}** → {step.get('impact')}\n")
            f.write(f"\n**最终结果**: {report.analysis.error_chain.final_outcome}\n\n")

        if report.analysis.key_findings:
            f.write(f"## 关键发现\n\n")
            for finding in report.analysis.key_findings:
                f.write(f"### {finding.category}\n")
                f.write(f"{finding.description}\n\n")
                if finding.evidence:
                    f.write(f"**证据**:\n")
                    for e in finding.evidence:
                        f.write(f"- {e}\n")
                    f.write("\n")
                if finding.recommendations:
                    f.write(f"**建议**:\n")
                    for r in finding.recommendations:
                        f.write(f"- {r}\n")
                    f.write("\n")

        if report.analysis.root_cause_analysis:
            f.write(f"## 根因分析\n\n{report.analysis.root_cause_analysis}\n\n")

        if report.analysis.system_context:
            f.write(f"## 系统环境\n\n")
            f.write(
                f"```json\n{json.dumps(report.analysis.system_context, ensure_ascii=False, indent=2)}\n```\n\n"
            )

        f.write(f"## 置信度评分\n\n{confidence:.2%}\n")

    print(f"✅ 报告已保存到 {output_file}")

    # 显示元数据
    print(f"\n📊 处理元数据 (Processing Metadata)")
    print("-" * 60)
    print(f"  日志来源: {report.metadata.log_source or 'N/A'}")
    print(f"  日志大小: {report.metadata.log_size_bytes:,} 字节")
    print(f"  Chunk数量: {report.metadata.chunk_count}")
    print(f"  处理时间: {report.metadata.processing_time_seconds:.2f} 秒")

    print(f"\n  使用的模型:")
    for key, model in report.metadata.models_used.items():
        print(f"    - {key}: {model}")

    print("\n" + "=" * 60)
    print("演示完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
