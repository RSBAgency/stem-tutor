import json
import os
from datetime import datetime, timezone

# saved sessions are stored in a flat JSON file for simplicity for a single user system

history_file = "sessions.json"


def save_session(state, messages):
    # called when a session ends, either from completion or "New Problem"

    if state is None:
        return  # nothing to save

    record = {
        # how far a session got
        # reorganize system messages before saving
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "problem_text": state["problem"]["text"],
        "target_concept": state["problem"]["target_concept"],
        "final_stage": state["stage"],
        "messages": [m for m in messages if m["role"] != "system"],
        "turn_log": state["log"],
    }

    # reads what is saved and add to new record
    # write list back
    sessions = load_all_sessions()
    sessions.append(record)

    with open(history_file, "w") as f:
        json.dump(sessions, f, indent=2)


def load_all_sessions():
    # return saved sessions oldest first
    if not os.path.exists(history_file):
        return[]  # no history yet/ first session

    with open(history_file, "r") as f:
        return json.load(f)
