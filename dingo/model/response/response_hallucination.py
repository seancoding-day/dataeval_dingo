from typing import List, Literal

from pydantic import BaseModel


class HallucinationVerdict(BaseModel):
    """Single verdict for hallucination detection"""
    verdict: Literal["yes", "no"]
    reason: str


class HallucinationVerdicts(BaseModel):
    """Container for all verdicts"""
    verdicts: List[HallucinationVerdict]


class HallucinationScoreReason(BaseModel):
    """Final score and reason for hallucination assessment"""
    score: float
    reason: str
