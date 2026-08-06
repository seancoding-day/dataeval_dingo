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
    provider: Optional[str] = None
    calls: int = 1
    source: str = "provider"


class EvalDetail(BaseModel):
    metric: str
    status: bool = False

    score: Optional[float] = None
    label: Optional[list[str]] = None
    reason: Optional[list] = None
    usage: Optional[TokenUsage] = None
