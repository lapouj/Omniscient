#!/usr/bin/env python3
import argparse, yaml, os, importlib
from utils.file_handler import load_machine_state

def load_config(config_path):
    with open(config_path, "r") as file:
        return yaml.safe_load(file)

def get_available_modules(config):
    return [k for k, v in config["tools"].items() if v]

def launch_module(module_name, context, config):
    try:
        mod = importlib.import_module(f"modules.{module_name}")
        if hasattr(mod, "run"):
            print(f"[⚙️] Lancement du module : {module_name}")
            mod.run(
                target_name=context["target"],
                platform=context["platform"],
                ip=context["ip"],
                target_base_path=context["base_path"],
                config=config
            )
        else:
            print(f"[!] Le module '{module_name}' n’a pas de fonction 'run()'.")
    except ModuleNotFoundError:
        print(f"[!] Module '{module_name}' introuvable.")
    except Exception as e:
        print(f"[!] Erreur lors de l’exécution du module '{module_name}' : {str(e)}")

def auto_chain_modules(state, config):
    modules = []
    flags = state.get("flags", {})

    if flags.get("has_http") or flags.get("has_https"):
        if config["tools"].get("web_enum"):
            modules.append("web_enum")
    if flags.get("has_smb") and config["tools"].get("smb_enum"):
        modules.append("smb_enum")
    if flags.get("has_ftp") and config["tools"].get("ftp_enum"):
        modules.append("ftp_enum")
    if flags.get("has_ssh") and config["tools"].get("ssh_enum"):
        modules.append("ssh_enum")
    if flags.get("has_ad") and config["tools"].get("ad_enum_base"):
        modules.append("ad_enum_base")
    if config["tools"].get("report_generation"):
        modules.append("report_generation")

    return modules

def main():
    parser = argparse.ArgumentParser(description="🔧 Lanceur de modules Omniscient")
    parser.add_argument("--module", help="Nom du module à lancer (ex: web_enum)")
    parser.add_argument("--mode", choices=["all", "auto"], help="Mode spécial : all = tous les modules, auto = chaining intelligent")
    parser.add_argument("--target", required=True)
    parser.add_argument("--platform", default="HTB")
    parser.add_argument("--ip", required=True)
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

    if args.mode == "all":
        print("[🔁] Mode 'all' : exécution de tous les modules activés.")
        for module_name in get_available_modules(config):
            if module_name != "nmap":
                launch_module(module_name, context, config)
        return

    if args.mode == "auto":
        print("[🧠] Mode 'auto' : chaining intelligent basé sur les services détectés.")
        root_dir = os.path.join(base_path, args.platform, args.target)
        state = load_machine_state(root_dir)
        if not state:
            print("[!] Impossible de charger machine-state.json. Lance d'abord le scan Nmap.")
            return
        modules = auto_chain_modules(state, config)
        if not modules:
            print("[i] Aucun module pertinent détecté.")
            return
        for module in modules:
            launch_module(module, context, config)
        return

    if args.module:
        launch_module(args.module, context, config)
    else:
        print("[!] Tu dois utiliser --module, --mode all ou --mode auto.")

if __name__ == "__main__":
    main()