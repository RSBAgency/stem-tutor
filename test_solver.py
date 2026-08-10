import os
from openai import OpenAI
from problem_solver import solve_problem

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

test_problems = [
    "x + 1 = x + 2",
    "2x + 4 = 2(x + 2)",
    "4x = 6",
    "x^2 - 2 = 0",
    "3x + 2y = 12",
    "Sarah has twice as many apples as Tom. Together they have 12 apples. How many apples does Tom have?",
    "what is the derivative of x^2 + 3x",
]

for problem in test_problems:
    result = solve_problem(client, problem)
    print(f"Problem: {problem}")
    print(f"  solvable={result.solvable}")
    print(f"  locked_answer={result.locked_answer!r}")
    print(f"  target_concept={result.target_concept!r}")
    print()