from pydantic import BaseModel
from typing import List


class EvaluationResponse(BaseModel):
    overall_score: int
    technical_accuracy: int
    clarity: int
    completeness: int
    strengths: List[str]
    weaknesses: List[str]
    improvements: List[str]
    ideal_answer: str