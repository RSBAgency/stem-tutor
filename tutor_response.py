from pydantic import BaseModel

# defines the data the tutor will return utilizing a Pydantic model instead of plain text


class TutorTurn(BaseModel):
    # the message shown to the student
    reply_text: str

    # grades the student's last message as a right or wrong answer
    # or as a description in conversation
    gradable: bool

    # meaningful when gradable=True
    # determines whether the attempt was actually correct
    answer_correct: bool

    # did the student demand the final answer, 3 strike rule
    impatience_demand: bool

    # has the current teaching stage fully finished
    stage_complete: bool


# defines the shape the solver will return
# one time call before conversation stage begins, determining the correct answer only
class ProblemSolution(BaseModel):

    # can this problem be solved and does it fit between the 3 types of questions allowed
    solvable: bool

    # the final answer
    locked_answer: str

    # the skill that is being highlighted in the conversation
    # empty string if not solvable
    target_concept: str


# data returned from generate_transfer_problem()
class TransferProblem(BaseModel):
    new_problem_text: str

