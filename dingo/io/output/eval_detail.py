from typing import Optional

from pydantic import BaseModel


class QualityLabel:
    """质量标签常量类"""
    QUALITY_GOOD = "QUALITY_GOOD"  # Indicates pass the quality check
    QUALITY_BAD_PREFIX = "QUALITY_BAD_"  # Indicates not pass the quality check
    REVIEW_EXECUTION_ERROR_PREFIX = "REVIEW_EXECUTION_ERROR."  # 评审执行失败（基础设施错误），非质量问题


class TokenUsage(BaseModel):
    """Token usage returned by an LLM provider for one evaluator call."""

    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    reasoning_tokens: Optional[int] = None
    cached_tokens: Optional[int] = None
    model: Optional[str] = None
    # provider: Optional[str] = None
    calls: int = 1
    source: str = "provider"


class EvalDetail(BaseModel):
    metric: str
    status: bool = False

    score: Optional[float] = None
    label: Optional[list[str]] = None
    reason: Optional[list] = None
    usage: Optional[TokenUsage] = None

    # 评审引擎判定契约（spec §4.2/§7.3）。旧评估器不设时全部回退，行为不变。
    verdict: Optional[str] = None          # "pass" | "warning" | "issue"
    applicable: bool = True                # False = N/A，从聚合分母剔除（spec §15.2）
    rule_id: Optional[str] = None          # decision-table 条款（Task 3）
    rubric_version: Optional[str] = None

    @property
    def effective_verdict(self) -> str:
        if self.verdict is not None:
            return self.verdict
        if not self.applicable:
            return "n/a"
        return "issue" if self.status else "pass"
