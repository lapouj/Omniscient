import os
import subprocess
import json
from datetime import datetime
from utils.file_handler import load_machine_state, save_machine_state

def write_header(f, title):
    f.write(f"\n{'=' * 50}\n")
    f.write(f"{title}\n")
    f.write(f"{'=' * 50}\n\n")

def get_ssh_banner(ip):
    try:
        result = subprocess.run(["nc", "-vz", ip, "22"], capture_output=True, text=True, timeout=5)
        return result.stderr + result.stdout
    except Exception as e:
        return f"[!] Erreur de bannière SSH : {e}"

def attempt_login(ip, username, password):
    try:
        result = subprocess.run(
            ["sshpass", "-p", password, "ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=5",
             f"{username}@{ip}", "exit"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return result.returncode == 0
    except Exception:
        return False

def extract_version(banner):
    if "OpenSSH" in banner:
        try:
            start = banner.index("OpenSSH") + len("OpenSSH ")
            end = banner.index(" ", start)
            return banner[start:end]
        except:
            return None
    return None

def run(target_name, platform, ip, target_base_path, config):
    print("[🔐] Lancement du module SSHEnum...")

    root_dir = os.path.join(target_base_path, platform, target_name)
    state = load_machine_state(root_dir)
    if not state or not state.get("flags", {}).get("has_ssh"):
        print("[i] Aucun port SSH détecté, SSHEnum ignoré.")
        return

    scan_dir = os.path.join(root_dir, "scans")
    os.makedirs(scan_dir, exist_ok=True)

    output_path = os.path.join(scan_dir, "ssh_enum.txt")
    ssh_config = config.get("ssh_enum", {})
    enable_brute = ssh_config.get("enable_bruteforce", False)
    usernames = ssh_config.get("usernames", [])
    password = ssh_config.get("password", "toor")

    results = {
        "banner": None,
        "version": None,
        "login_tested": enable_brute,
        "login_success": False,
        "accounts_tried": [],
        "successful_account": None
    }

    with open(output_path, "w") as f:
        f.write(f"# 🔐 Résultats SSHEnum - {target_name} ({ip})\n")
        f.write(f"Date : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        write_header(f, "[1] Bannière SSH")
        banner = get_ssh_banner(ip)
        f.write(banner)
        results["banner"] = banner.strip()
        version = extract_version(banner)
        if version:
            f.write(f"\n[+] Version OpenSSH détectée : {version}\n")
            results["version"] = version

        if enable_brute and usernames:
            write_header(f, "[2] Bruteforce SSH ciblé (user/pass)")
            for user in usernames:
                f.write(f"[-] Tentative avec {user}:{password}...\n")
                if attempt_login(ip, user, password):
                    f.write(f"[+] Connexion réussie avec {user}:{password} !\n")
                    results["login_success"] = True
                    results["successful_account"] = user
                    break
                results["accounts_tried"].append(user)
            if not results["login_success"]:
                f.write("[i] Aucun compte trouvé avec les credentials fournis.\n")
        else:
            f.write("[i] Bruteforce désactivé dans config.yaml\n")

        write_header(f, "Résumé SSHEnum")
        for k, v in results.items():
            val = ", ".join(v) if isinstance(v, list) else v
            f.write(f"- {k} : {val}\n")

    state = load_machine_state(root_dir) or {}
    state["ssh"] = results
    state.setdefault("flags", {})["has_ssh_enum"] = True
    save_machine_state(root_dir, state)

    print(f"[✓] SSHEnum terminé. Résultats dans : {output_path}")
