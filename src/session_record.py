import json
import os
import subprocess
from datetime import datetime


CATEGORIES =  ["delegated_result", "human_input", "exposure", "runtime"]

def code_version():
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        changes = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=no"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        return {"commit": commit, "uncommitted_changes": changes != ""}
    except (OSError, subprocess.CalledProcessError):
        return {"commit": None, "uncommitted_changes": None}

def start_session(folder="sessions"):
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    session = {
        "session_id": session_id,
        "code_version": code_version(),
        "path": os.path.join(folder, "session_" + session_id + ".json"),
        "events": [],
        "enabled": True,
    }

    try:
        os.makedirs(folder, exist_ok=True)
    except OSError as error:
        session["enabled"] = False
        print(f"WARNING: session folder could not be created ({error}). This session will not be saved.")

    return session


def record(session, category, event, **data):
    if category not in CATEGORIES:
        raise ValueError(f"Unknown event category: {category}")
    
    session["events"].append({
        "order": len(session["events"]) + 1,
        "time": datetime.now().isoformat(timespec="seconds"),
        "category": category,
        "event": event,
        "data": data,
    })

    if not session["enabled"]:
        return False

    temporary_path = session["path"] + ".tmp"
    content = {"session_id": session["session_id"], "code_version": session["code_version"], "events": session["events"]}
    
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
    saved = record(session, "human_input", "evidence_received", mode="2", text="Example evidence.")
    record(session, "human_input", "formulation_confirmed", formulation="Example formulation")
    print("Saved: " + str(saved) + " | " + session["path"])