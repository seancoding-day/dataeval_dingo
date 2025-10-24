from pydantic import BaseModel


class ResponseResumeQuality(BaseModel):
    """Response model for resume quality evaluation."""
    score: int  # 1 = good quality, 0 = has issues
    type: str  # "Good" or issue category (Privacy/Contact/Format/Structure/Professionalism/Date/Completeness)
    name: str  # Specific error name or "Good"
    reason: str  # Detailed explanation

    class Config:
        extra = "forbid"
        validate_assignment = True

