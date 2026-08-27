import json

# read sessions.json directly and reports session data
# computes real numbers from saved session data - research

with open("sessions.json", "r") as f:
    sessions = json.load(f)

total = len(sessions)
print(f"Total Sessions: {total}\n")

# completion rate: session reached final tracked stage
completed = [s for s in sessions if s["final_stage"] == "transfer_check"]
print(f"Reached transfer_check (final stage): {len(completed)}/{total} "
      f"({100 * len(completed) / total:.0f}%)")


# teaching fallback rate for the descent rule direct teach step
def teaching_fallback(session):
    consecutive_wrong = 0
    for turn in session["turn_log"]:
        if turn["gradable"]:
            if not turn["answer_correct"]:
                consecutive_wrong += 1
                if consecutive_wrong >= 2:
                    return True

            else:
                consecutive_wrong = 0
    return False


fallback_sessions = [s for s in sessions if teaching_fallback(s)]
print(f"Required teaching fallback (2+ wrong in a row): {len(fallback_sessions)}/{total} "
      f"({100 * len(fallback_sessions) / total:.0f}%)")

# Transfer check outcome
attempted = [s for s in sessions if s.get("transfer_outcome", {}).get("attempted")]
passed = [s for s in attempted if s["transfer_outcome"]["passed"]]
failed = [s for s in attempted if s["transfer_outcome"]["passed"] is False]
declined = [s for s in sessions
            if s ["final_stage"] == "transfer_check"
            and not s.get("transfer_outcome", {}).get("attempted")]
print(f"\nTransfer check reached: {len(completed)}")
print(f"   Attempted: {len(attempted)}")
print(f"     Passed:  {len(passed)}")
print(f"     Failed:  {len(failed)}")
print(f"   Declined:  {len(declined)}")