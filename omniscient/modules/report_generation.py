import os
import json
from utils.file_handler import load_machine_state
from datetime import datetime

def run(target_name, platform, ip, target_base_path, config):
    print("[📄] Génération du rapport Markdown...")

    root_dir = os.path.join(target_base_path, platform, target_name)
    scan_dir = os.path.join(root_dir, "scans")
    os.makedirs(scan_dir, exist_ok=True)

    report_path = os.path.join(root_dir, "recon_report.md")
    with open(report_path, "w") as f:
        # En-tête
        f.write(f"# 🧠 Rapport de Reconnaissance - {target_name}\n")
        f.write(f"- **IP** : {ip}\n")
        f.write(f"- **Plateforme** : {platform}\n")
        f.write(f"- **Date** : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        # Ports / Services (Nmap)
        state = load_machine_state(root_dir)
        if state:
            f.write("## 🔍 Scan Réseau (Nmap)\n")
            f.write(f"- **Ports TCP ouverts** : {', '.join(map(str, state.get('open_tcp_ports', [])))}\n")
            f.write(f"- **Ports UDP ouverts** : {', '.join(map(str, state.get('open_udp_ports', [])))}\n\n")
            f.write("### Services détectés :\n")
            for svc in state.get("services", []):
                f.write(f"- `{svc['port']}/tcp` → {svc['service']}\n")
            f.write("\n")

        # Recon Web (si dispo)
        web_json = os.path.join(scan_dir, "web-recon.json")
        if os.path.exists(web_json):
            with open(web_json, "r") as wf:
                web_data = json.load(wf)

                f.write("## 🌐 Reconnaissance Web\n")
                for url in web_data.get("urls_tested", []):
                    f.write(f"### {url}\n")

                    # Sécurité : .get() sur whatweb
                    whatweb_info = web_data.get("whatweb", {}).get(url, "Aucune info")
                    f.write("- **WhatWeb** :\n")
                    f.write(f"```\n{whatweb_info}\n```\n")

                    gobuster_path = web_data.get("gobuster", {}).get(url)
                    if gobuster_path and os.path.exists(gobuster_path):
                        f.write("- **Gobuster** (extraits) :\n")
                        with open(gobuster_path, "r") as gb:
                            lines = gb.readlines()
                            top_hits = [line for line in lines if "Status:" in line]
                            for line in top_hits[:10]:
                                f.write(f"  - {line}")
                        if len(top_hits) > 10:
                            f.write("  - ...\n")
                    f.write("\n")

        # Résumé final
        f.write("---\n")
        f.write("_Rapport généré automatiquement par Omniscient_ 🤖\n")

    print(f"[✓] Rapport généré : {report_path}")
