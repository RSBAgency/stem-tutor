from tutor_response import ProblemSolution, TransferProblem
# this module only focuses on correctness
# it is separate from the tutor's logic and is never shown to the student
# it is called once per problem before tutoring
# all rules were added as a response to a system failure found in testing

SOLVER_SYSTEM_PROMPT = """You are a rigorous algebra solver, used internally to determine the correct answer to a
problem before any tutoring begins. The student will NEVER see this response directly, it is only used internally to
check the student's later answers.

Solve the given problem completely and precisely. Double check your work before answering, a wrong answer here would
cause an entire tutoring session to teach the wrong thing.

The problem must be exactly one of these types: a single linear equation in one variable, a system of two linear
equations in two variables, or a basic quadratic equation in one variable. Nothing else counts, even if you know how to
solve it. Calculus (derivatives, integrals, limits), problems with more unknowns than independent equations or one
equation with two variables, inequalities, and anything outside these three types must be marked solvable=false. Being 
able to solve something is NOT enough to mark it solvable - it must also match one of these three exact types.

Additionally, if a quadratic equation's discriminant (b^2 - 4ac) is negative, meaning the solutions would be complex or
imaginary numbers, mark solvable=false. This solver only handles quadratics with real number solutions.

Before answering, check yourself: does this problem have exactly one correct, fully determined answer or a clearly
stated no solution/ infinite solution result for a single variable equation? If there are more unknowns than equations,
or the topic isn't algebra, solvable MUST be false, even if you could technically produce a formula or a correct answer
for it.

Return:
- solvable: true only if this is a well formed problem of the allowed types that you can solve with certainty, false
otherwise.
- locked_answer: the final answer(s), written plainly. Leave as an empty string if solvable is false.
- target_concept: a short phrase naming the skill being taught (i.e. "solving systems of linear equations by 
substitution"). Leave as an empty string if solvable is false.
"""


def solve_problem(client, problem_text):
    # called once per problem at the start of the session
    completion = client.chat.completions.parse(
        model="gpt-5-mini",
        messages=[
            {"role": "system", "content": SOLVER_SYSTEM_PROMPT},
            {"role": "user", "content": problem_text},
        ],
        # response is return in ProblemSolution shape instead of text for reliability
        response_format=ProblemSolution
    )
    # parsed only when validated
    return completion.choices[0].message.parsed


# generate a transfer check problem
# passed through solve_problem()
TRANSFER_GENERATOR_PROMPT = """You generate a single NEW practice problem that tests the SAME underlying concept as a
given original problem, but it is NOT solvable by simply copying the original problem's steps with the same numbers. It
must require applying the concept fresh.

The new problem must be the SAME type as the original (linear equation, system of two equations, quadratic) just with
different numbers or a different surface context.

Return only the new problem's text, written in plain text, as something a student could type directly into this app to
work on.
"""


# transfer problem generator
def generate_transfer_problem(client, original_problem_text, target_concept):
    completion = client.chat.completions.parse(
        model="gpt-5-mini",
        messages=[
            {"role": "system", "content": TRANSFER_GENERATOR_PROMPT},
            {"role": "user", "content": f"Original problem: {original_problem_text}\n" 
                                        f"Concept being tested: {target_concept}"},
        ],
        response_format=TransferProblem,


    )
    return completion.choices[0].message.parsed.new_problem_text

