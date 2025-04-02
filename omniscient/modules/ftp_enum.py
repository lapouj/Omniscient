import os
import subprocess
import json
from datetime import datetime
from utils.file_handler import load_machine_state, save_machine_state

def write_header(f, title):
    f.write(f"\n{'=' * 50}\n")
    f.write(f"{title}\n")
    f.write(f"{'=' * 50}\n\n")

def parse_ftp_info(banner_output, anon_result):
    parsed = {
        "banner": None,
        "anonymous_access": False,
        "listed_files": [],
        "can_download": False
    }

    # Parse banner
    for line in banner_output.splitlines():
        if "FTP" in line or "vsftpd" in line or "FileZilla" in line or "ProFTPD" in line:
            parsed["banner"] = line.strip()
            break

    if "230 Anonymous access granted" in anon_result:
        parsed["anonymous_access"] = True

        if "226 Transfer complete" in anon_result or "drwx" in anon_result or "-rw" in anon_result:
            parsed["can_download"] = True

        for line in anon_result.splitlines():
            if line.startswith("drw") or line.startswith("-rw") or line.startswith("lrw"):
                parts = line.split()
                filename = parts[-1] if len(parts) >= 9 else line
                parsed["listed_files"].append(filename)

    return parsed

def run(target_name, platform, ip, target_base_path, config):
    print("[📦] Lancement du module FTPEnum...")

    root_dir = os.path.join(target_base_path, platform, target_name)
    scan_dir = os.path.join(root_dir, "scans")
    os.makedirs(scan_dir, exist_ok=True)

    # Vérifie que le port FTP a été détecté
    state = load_machine_state(root_dir)
    if not state or not state.get("flags", {}).get("has_ftp"):
        print("[i] Aucun port FTP détecté, FTPEnum ignoré.")
        return

    output_path = os.path.join(scan_dir, "ftp_enum.txt")
    with open(output_path, "w") as f:
        f.write(f"# 📦 Résultats FTPEnum - {target_name} ({ip})\n")
        f.write(f"Date : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"IP cible : {ip}\n\n")

        banner_output = ""
        anon_result = ""

        # 1. Banner grabbing via netcat
        write_header(f, "[1] Banner Grabbing (nc)")
        try:
            banner = subprocess.run(["nc", "-nvz", ip, "21"], capture_output=True, text=True, timeout=5)
            banner_output = banner.stderr + banner.stdout
            f.write(banner_output)
        except Exception as e:
            f.write(f"[!] Erreur netcat : {e}\n")

        # 2. Anonymous login test
        write_header(f, "[2] Test de connexion anonyme FTP")
        try:
            cmd = f'echo -e "user anonymous\\npass test@test.com\\nls\\nquit" | ftp -inv {ip}'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
            anon_result = result.stdout
            f.write(anon_result)
        except Exception as e:
            f.write(f"[!] Erreur ftp anonyme : {e}\n")

        # 3. Résumé + parsing
        parsed = parse_ftp_info(banner_output, anon_result)

        f.write("\n---\nRésumé :\n")
        for k, v in parsed.items():
            val = ", ".join(v) if isinstance(v, list) else v
            f.write(f"- {k} : {val}\n")

        # 4. Update machine-state.json
        state["ftp"] = parsed
        state.setdefault("flags", {})["has_ftp_enum"] = True
        save_machine_state(root_dir, state)

        f.write("\n---\n_Rapport généré par Omniscient._\n")

    print(f"[✓] FTPEnum terminé. Résultats dans : {output_path}")
