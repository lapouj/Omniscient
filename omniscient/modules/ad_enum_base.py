import os
import subprocess
import json
from datetime import datetime
from utils.file_handler import load_machine_state, save_machine_state

def write_header(f, title):
    f.write(f"\n{'=' * 60}\n")
    f.write(f"{title}\n")
    f.write(f"{'=' * 60}\n\n")

def run(target_name, platform, ip, target_base_path, config):
    print("[🏢] Lancement du module ADEnumBase...")

    root_dir = os.path.join(target_base_path, platform, target_name)
    scan_dir = os.path.join(root_dir, "scans")
    os.makedirs(scan_dir, exist_ok=True)

    state = load_machine_state(root_dir)
    if not state or not state.get("flags", {}).get("has_ad"):
        print("[i] Aucun indicateur AD détecté, ADEnum ignoré.")
        return

    output_path = os.path.join(scan_dir, "ad_enum_base.txt")
    results = {
        "rpcclient_info": [],
        "nmap_ldap_scripts": "",
        "cme_info": ""
    }

    with open(output_path, "w") as f:
        f.write(f"# 🏢 Résultats ADEnumBase - {target_name} ({ip})\n")
        f.write(f"Date : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        # Section 1 : Infos avec rpcclient
        write_header(f, "[1] rpcclient -l")
        try:
            rpc = subprocess.run(
                ["rpcclient", "-U", "", ip, "-c", "srvinfo"],
                capture_output=True, text=True, timeout=10
            )
            output = rpc.stdout.strip()
            f.write(output + "\n")
            results["rpcclient_info"].append(output)
        except Exception as e:
            f.write(f"[!] Erreur rpcclient : {e}\n")

        # Section 2 : Nmap LDAP Scripts
        write_header(f, "[2] Nmap – Scripts LDAP")
        try:
            ldap_nmap = subprocess.run(
                ["nmap", "-Pn", "-p389", "--script", "ldap*", "-T4", ip],
                capture_output=True, text=True, timeout=30
            )
            output = ldap_nmap.stdout.strip()
            f.write(output + "\n")
            results["nmap_ldap_scripts"] = output
        except Exception as e:
            f.write(f"[!] Erreur nmap LDAP : {e}\n")

        # Section 3 : CrackMapExec
        write_header(f, "[3] CrackMapExec (RPC/SMB/LDAP anonymes)")
        try:
            cme = subprocess.run(
                ["crackmapexec", "ldap", ip],
                capture_output=True, text=True, timeout=10
            )
            output = cme.stdout.strip()
            f.write(output + "\n")
            results["cme_info"] = output
        except FileNotFoundError:
            f.write("[!] CrackMapExec non installé.\n")
        except Exception as e:
            f.write(f"[!] Erreur CME : {e}\n")

        f.write("\n---\n_Rapport généré par Omniscient._\n")

    # Mise à jour machine-state.json
    state.setdefault("ad", {})["enum_base"] = True
    state.setdefault("flags", {})["has_ad_enum"] = True
    state["ad"]["base_results"] = results
    save_machine_state(root_dir, state)

    print(f"[✓] ADEnumBase terminé. Résultats dans : {output_path}")
