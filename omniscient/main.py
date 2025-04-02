#!/usr/bin/env python3

import argparse
import yaml
import os
from module_launcher import launch_module
from utils.file_handler import load_machine_state

def load_config(config_path):
    with open(config_path, "r") as file:
        return yaml.safe_load(file)

def main():
    parser = argparse.ArgumentParser(description="🚀 Lancement de la reconnaissance complète avec Omniscient")
    parser.add_argument("--target", required=True, help="Nom de la machine")
    parser.add_argument("--platform", default="HTB", help="Plateforme/envrionnement (HTB, THM, Local, etc.)")
    parser.add_argument("--ip", required=True, help="Adresse IP de la machine")
    args = parser.parse_args()

    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    config = load_config(config_path)
    base_path = os.path.expanduser(config["paths"]["target_dir"])

    context = {
        "target": args.target,
        "platform": args.platform,
        "ip": args.ip,
        "base_path": base_path
    }

    print(f"[+] Omniscient lancé pour {args.target} ({args.ip}) - Plateforme/environnement : {args.platform}")
    print("[i] Modules activés :", ', '.join([k for k, v in config["tools"].items() if v]))

    print(f"[i] Résultats seront stockés dans : {base_path}/{args.platform}/{args.target}\n")

    # 🎯 Appel des modules via module_launcher
    for module in config["tools"]:
        if config["tools"][module]:
            launch_module(module, context, config)

if __name__ == "__main__":
    main()
