import os
import subprocess
import json
from utils.file_handler import load_machine_state, save_machine_state
from datetime import datetime

def write_header(f, title):
    f.write(f"\n{'=' * 50}\n")
    f.write(f"{title}\n")
    f.write(f"{'=' * 50}\n\n")

def parse_info_from_outputs(smbclient_output, enum_output, smbmap_output):
    parsed = {
        "netbios_name": None,
        "domain": None,
        "server_os": None,
        "guest_access": False
    }

    for line in enum_output.splitlines():
        if "OS:" in line and not parsed["server_os"]:
            parsed["server_os"] = line.split(":", 1)[1].strip()
        if "Workgroup" in line and not parsed["domain"]:
            parsed["domain"] = line.split(":", 1)[-1].strip()
        if "NetBIOS name:" in line and not parsed["netbios_name"]:
            parsed["netbios_name"] = line.split(":", 1)[-1].strip()

    if "READ" in smbmap_output or "WRITE" in smbmap_output:
        parsed["guest_access"] = True

    return parsed

def run(target_name, platform, ip, target_base_path, config):
    print("[🧱] Lancement du module SMBEnum...")

    root_dir = os.path.join(target_base_path, platform, target_name)
    state = load_machine_state(root_dir)
    if not state or not state.get("flags", {}).get("has_smb"):
        print("[i] Aucun port SMB détecté, SMBEnum ignoré.")
        return

    scan_dir = os.path.join(root_dir, "scans")
    os.makedirs(scan_dir, exist_ok=True)
    output_path = os.path.join(scan_dir, "smb_enum.txt")

    with open(output_path, "w") as f:
        f.write(f"# 🔐 Résultats SMBEnum - {target_name} ({ip})\n")
        f.write(f"Date : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"IP cible : {ip}\n\n")

        smbclient_output, enum_output, smbmap_output = "", "", ""

        write_header(f, "[1] Enumération des partages (smbclient -L)")
        try:
            result = subprocess.run(["smbclient", "-L", ip, "-N"], capture_output=True, text=True, timeout=15)
            smbclient_output = result.stdout
            f.write(smbclient_output)
        except Exception as e:
            f.write(f"[!] Erreur smbclient : {e}\n")

        write_header(f, "[2] Enum4linux - Recherche avancée")
        try:
            cmd = ["enum4linux-ng", "-A", ip] if shutil.which("enum4linux-ng") else ["enum4linux", "-a", ip]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
            enum_output = result.stdout
            f.write(enum_output)
        except Exception as e:
            f.write(f"[!] Erreur enum4linux : {e}\n")

        write_header(f, "[3] Test accès invité (smbmap)")
        try:
            result = subprocess.run(["smbmap", "-H", ip, "-u", "", "-p", ""], capture_output=True, text=True, timeout=10)
            smbmap_output = result.stdout
            f.write(smbmap_output)
        except Exception as e:
            f.write(f"[!] Erreur smbmap : {e}\n")

        parsed = parse_info_from_outputs(smbclient_output, enum_output, smbmap_output)

        f.write("\n---\nRésumé :\n")
        for k, v in parsed.items():
            f.write(f"- {k} : {v}\n")

        state = load_machine_state(root_dir) or {}
        state["smb"] = parsed
        state.setdefault("flags", {})["has_smb_enum"] = True
        save_machine_state(root_dir, state)

        f.write("\n---\n_Rapport généré par Omniscient._\n")

    print(f"[✓] SMBEnum terminé. Résultats dans : {output_path}")
