import json
import os
from datetime import datetime, timezone

history_file = "sessions.json"

def save_session(state, messages):

    if state is None:
        return # nothing to save

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "problem_text": state["problem"]["text"],
        "target_concept": state["problem"]["target_concept"],
        "final_stage": state["stage"],
        "messages": [m for m in messages if m["role"] != "system"],
    }

    sessions = load_all_sessions()
    sessions.append(record)

    with open(history_file, "w") as f:
        json.dump(sessions, f, indent=2)

def load_all_sessions():
    if not os.path.exists(history_file):
        return[]

    with open(history_file, "r") as f:
        return json.load(f)