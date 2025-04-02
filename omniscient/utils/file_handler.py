import os
import json

def load_machine_state(root_dir):
    try:
        state_path = os.path.join(root_dir, "machine-state.json")
        with open(state_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print("[!] machine-state.json introuvable.")
    except json.JSONDecodeError:
        print("[!] Erreur de format dans machine-state.json.")
    return None

def save_machine_state(root_dir, data):
    state_path = os.path.join(root_dir, "machine-state.json")
    with open(state_path, "w") as f:
        json.dump(data, f, indent=4)
