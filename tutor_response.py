from pydantic import BaseModel

class TutorTurn(BaseModel):
    reply_text: str
    gradable: bool
    answer_correct: bool
    impatience_demand: bool
    stage_complete: bool