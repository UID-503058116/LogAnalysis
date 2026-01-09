"""报告格式化器。"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Literal

from logginganalysis.models.report import AnalysisReport


class ReportFormatter(ABC):
    """报告格式化器基类。"""

    @abstractmethod
    def format(self, report: AnalysisReport) -> str:
        """格式化报告。

        Args:
            report: 分析报告

        Returns:
            str: 格式化后的报告
        """
        pass


class MarkdownFormatter(ReportFormatter):
    """Markdown 格式化器。"""

    def format(self, report: AnalysisReport) -> str:
        """将报告格式化为 Markdown。

        Args:
            report: 分析报告

        Returns:
            str: Markdown 格式的报告
        """
        lines = []

        # 标题
        lines.append("# 日志分析报告\n")

        # 元数据
        lines.append("## 分析元数据\n")
        lines.append(f"- **生成时间**: {self._format_datetime(report.generated_at)}")
        if report.metadata.log_source:
            lines.append(f"- **日志来源**: {report.metadata.log_source}")
        lines.append(f"- **日志大小**: {self._format_size(report.metadata.log_size_bytes)}")
        lines.append(f"- **分块数量**: {report.metadata.chunk_count}")
        lines.append(f"- **处理耗时**: {report.metadata.processing_time_seconds:.2f}秒")
        lines.append(f"- **使用模型**: {', '.join(report.metadata.models_used.values())}\n")

        # 整体摘要
        lines.append("## 整体摘要\n")
        lines.append(report.analysis.overall_summary)
        lines.append("")

        # 置信度
        confidence_bar = self._create_confidence_bar(report.analysis.confidence_score)
        lines.append(f"**分析置信度**: {confidence_bar} ({report.analysis.confidence_score:.0%})\n")

        # 系统环境
        if report.analysis.system_context:
            lines.append("## 系统环境\n")
            for key, value in report.analysis.system_context.items():
                lines.append(f"- **{key}**: {value}")
            lines.append("")

        # 关键发现
        if report.analysis.key_findings:
            lines.append("## 关键发现\n")
            for i, finding in enumerate(report.analysis.key_findings, 1):
                lines.append(f"### {i}. {finding.category}\n")
                lines.append(f"{finding.description}\n")

                # 严重程度指示器
                severity = self._infer_severity(finding)
                if severity:
                    lines.append(f"**严重程度**: {severity}\n")

                # 证据
                if finding.evidence:
                    lines.append("**证据**:")
                    for evidence in finding.evidence:
                        lines.append(f"  - {evidence}")
                    lines.append("")

                # 建议
                if finding.recommendations:
                    lines.append("**建议**:")
                    for rec in finding.recommendations:
                        lines.append(f"  1. {rec}")
                    lines.append("")

        # 根因分析
        if report.analysis.root_cause_analysis:
            lines.append("## 根因分析\n")
            lines.append(report.analysis.root_cause_analysis)
            lines.append("")

        # 原始提取摘要
        if report.raw_extractions:
            lines.append("## 各块提取摘要\n")
            for extraction in report.raw_extractions:
                chunk_id = extraction.chunk_id or "unknown"
                chunk_info = f"块 {chunk_id[:8]}..."
                lines.append(f"### {chunk_info}")
                lines.append(f"{extraction.summary}\n")

                if extraction.exceptions:
                    lines.append(f"**异常**: {len(extraction.exceptions)}个")
                if extraction.problematic_behaviors:
                    lines.append(f"**问题行为**: {len(extraction.problematic_behaviors)}个")
                lines.append("")

        # 网页搜索结果
        if report.search_results:
            lines.append("## 相关资源\n")
            for result in report.search_results[:5]:
                title = result.get("title") or "Untitled"
                url = result.get("url") or "#"
                snippet = result.get("snippet") or ""
                lines.append(f"- [{title}]({url})")
                lines.append(f"  {snippet}\n")

        return "\n".join(lines)

    def _format_datetime(self, dt: datetime) -> str:
        """格式化日期时间。"""
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")

    def _format_size(self, size_bytes: int) -> str:
        """格式化文件大小。"""
        size: float = float(size_bytes)
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    def _create_confidence_bar(self, score: float) -> str:
        """创建置信度条。"""
        filled = int(score * 20)
        bar = "█" * filled + "░" * (20 - filled)
        return bar

    def _infer_severity(self, finding: Any) -> str | None:
        """推断发现的严重程度。"""
        from logginganalysis.models.integration import AnalysisInsight

        # 基于类别关键词推断严重程度
        critical_keywords = ["crash", "fatal", "security", "breach", "数据泄露"]
        high_keywords = ["failure", "timeout", "error", "性能"]
        medium_keywords = ["warning", "慢", "延迟"]

        category_lower = (finding.category or "").lower()
        desc_lower = (finding.description or "").lower()

        if any(kw in category_lower or kw in desc_lower for kw in critical_keywords):
            return "🔴 严重"
        elif any(kw in category_lower or kw in desc_lower for kw in high_keywords):
            return "🟠 高"
        elif any(kw in category_lower or kw in desc_lower for kw in medium_keywords):
            return "🟡 中"
        else:
            return "🟢 低"


class JSONFormatter(ReportFormatter):
    """JSON 格式化器。"""

    def format(self, report: AnalysisReport) -> str:
        """将报告格式化为 JSON。

        Args:
            report: 分析报告

        Returns:
            str: JSON 格式的报告
        """
        return report.model_dump_json(indent=2, exclude_none=True)


class TextFormatter(ReportFormatter):
    """纯文本格式化器。"""

    def format(self, report: AnalysisReport) -> str:
        """将报告格式化为纯文本。

        Args:
            report: 分析报告

        Returns:
            str: 纯文本格式的报告
        """
        lines = []

        lines.append("=" * 60)
        lines.append("日志分析报告".center(60))
        lines.append("=" * 60)
        lines.append("")

        # 元数据
        lines.append("[分析元数据]")
        lines.append(f"  生成时间: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        if report.metadata.log_source:
            lines.append(f"  日志来源: {report.metadata.log_source}")
        lines.append(f"  日志大小: {report.metadata.log_size_bytes} 字节")
        lines.append(f"  分块数量: {report.metadata.chunk_count}")
        lines.append(f"  处理耗时: {report.metadata.processing_time_seconds:.2f} 秒")
        lines.append("")

        # 整体摘要
        lines.append("[整体摘要]")
        lines.append(f"  {report.analysis.overall_summary}")
        lines.append("")

        # 置信度
        lines.append(f"  分析置信度: {report.analysis.confidence_score:.0%}")
        lines.append("")

        # 关键发现
        if report.analysis.key_findings:
            lines.append("[关键发现]")
            for i, finding in enumerate(report.analysis.key_findings, 1):
                lines.append(f"  {i}. {finding.category}")
                lines.append(f"     {finding.description}")
                if finding.recommendations:
                    lines.append("     建议:")
                    for rec in finding.recommendations:
                        lines.append(f"       - {rec}")
            lines.append("")

        lines.append("=" * 60)

        return "\n".join(lines)


# 支持的格式类型
OutputFormat = Literal["markdown", "json", "text"]


def get_formatter(format_type: OutputFormat = "markdown") -> ReportFormatter:
    """获取指定类型的格式化器。

    Args:
        format_type: 格式类型

    Returns:
        ReportFormatter: 对应的格式化器
    """
    formatters = {
        "markdown": MarkdownFormatter(),
        "json": JSONFormatter(),
        "text": TextFormatter(),
    }

    formatter = formatters.get(format_type)
    if formatter is None:
        raise ValueError(f"不支持的格式类型: {format_type}")

    return formatter
