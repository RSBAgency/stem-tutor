from session_state import create_session_state
from session_history import save_session, load_all_sessions

# terminal testing for session_history.py
state = create_session_state(
    problem_text="x^2 - x - 6 = 0",
    answer="x = 3 or x = -2",
    target_concept="solving quadratic equations by factoring",
)
state["stage"] = "completion"

messages = [
    {"role": "system", "content": "irrelevant prompt text"},
    {"role": "user", "content": "I need help solving x^2 - x - 6 = 0"},
    {"role": "assistant", "content": "Before we start, what do you know about factoring?"},
    {"role": "user", "content": "I have used it before but I am rusty"},

]

save_session(state, messages)

sessions = load_all_sessions()
print(f"Total saved sessions: {len(sessions)}")
print(sessions[-1])