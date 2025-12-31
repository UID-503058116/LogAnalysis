import asyncio
import json
from logginganalysis import LogAnalyzer

async def main():
    analyzer = LogAnalyzer()
    with open("tests/test_data/latest.log", "r") as f:
        log_content = f.read()
    report = await analyzer.analyze(log_content)

    print("=" * 60)
    print("整体摘要 (Overall Summary)")
    print("=" * 60)
    print(report.analysis.overall_summary)
    print()

    if report.analysis.error_chain:
        print("=" * 60)
        print("错误链 (Error Chain)")
        print("=" * 60)
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

    # 写入完整报告到文件
    with open("report.md", "w") as f:
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
            f.write(f"```json\n{json.dumps(report.analysis.system_context, ensure_ascii=False, indent=2)}\n```\n\n")

        f.write(f"## 置信度评分\n\n{report.analysis.confidence_score:.2%}\n")

    print("报告已保存到 report.md")

asyncio.run(main())