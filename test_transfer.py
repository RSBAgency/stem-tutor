import os
from openai import OpenAI
from problem_solver import generate_transfer_problem, solve_problem

# testing new problem generator through terminal
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

test_cases = [
    ("x + 4 = 29", "solving a linear equation"),
    ("5x + 3y = 36 and x - y = 4", "solving systems of linear equations by substituiton"),
    ("x^2 - x - 6 = 0", "solving quadratic equations by factoring"),

]

for original, concept in test_cases:
    new_problem = generate_transfer_problem(client, original, concept)
    print(f"Original: {original}")
    print(f"Generated transfer problem: {new_problem}")

    verification = solve_problem(client, new_problem)
    print(f"  Verified solvable={verification.solvable}")
    print(f"  Verified locked_answer={verification.locked_answer!r}")
    print()
