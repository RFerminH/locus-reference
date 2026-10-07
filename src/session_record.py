import json
import os
from datetime import datetime


def start_session(folder="sessions"):
    os.makedirs(folder, exist_ok=True)
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    return {
        "session_id": session_id,
        "path": os.path.join(folder, "session_" + session_id + ".json"),
        "events": [],
    }


def record(session, event, **data):
    session["events"].append({
        "order": len(session["events"]) + 1,
        "time": datetime.now().isoformat(timespec="seconds"),
        "event": event,
        "data": data,
    })

    temporary_path = session["path"] + ".tmp"
    content = {"session_id": session["session_id"], "events": session["events"]}

    try:
        with open(temporary_path, "w", encoding="utf-8") as f:
            json.dump(content, f, indent=2, ensure_ascii=False)
        os.replace(temporary_path, session["path"])
        return True
    except (OSError, TypeError) as error:
        print(f"WARNING: session record could not be saved ({error}). Work continues unsaved.")
        return False


if __name__ == "__main__":
    session = start_session()
    record(session, "input_received", mode="2", text="Example evidence.")
    record(session, "formulation_confirmed", formulation="Example formulation")
    print("Saved to " + session["path"])