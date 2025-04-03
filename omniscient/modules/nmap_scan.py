import subprocess
import os
import re
import json
from datetime import datetime

def run(target_name, platform, ip, target_base_path, config):
    scan_dir = os.path.join(target_base_path, platform, target_name, "scans")
    os.makedirs(scan_dir, exist_ok=True)
    root_dir = os.path.join(target_base_path, platform, target_name)

    results = {
        "target": target_name,
        "ip": ip,
        "open_tcp_ports": [],
        "open_udp_ports": [],
        "http_ports": [],
        "https_ports": [],
        "services": [],
        "flags": {
            "has_http": False,
            "has_https": False,
            "has_ftp": False,
            "has_smb": False,
            "has_dns": False,
            "has_ssh": False,
            "has_ad": False
        },
        "error": None
    }

    # 1. PING CHECK
    if not config.get("skip_ping_check", False):
        print("[1] 🔎 Ping check...")
        try:
            subprocess.run(["ping", "-c", "1", ip], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            print("[✓] Hôte en ligne.")
        except subprocess.CalledProcessError:
            results["error"] = "Hôte injoignable (ping KO)"
            return results

    # 2. QUICK TCP SCAN
    print("[2] 🚀 Scan rapide TCP...")
    quick_tcp_file = os.path.join(scan_dir, "quick_tcp.txt")
    try:
        subprocess.run(["nmap", "-Pn", "-T4", "--min-rate", "1000", "-p-", "-oN", quick_tcp_file, ip], check=True)
        with open(quick_tcp_file, "r") as f:
            ports = re.findall(r"^(\d+)/tcp\s+open", f.read(), re.MULTILINE)
            results["open_tcp_ports"] = sorted([int(p) for p in ports])
    except Exception as e:
        results["error"] = f"Erreur quick scan : {str(e)}"
        return results

    # 3. UDP SCAN
    print("[3] 🌊 Scan UDP (top 50)...")
    udp_file = os.path.join(scan_dir, "udp.txt")
    try:
        subprocess.run(["nmap", "-Pn", "-sU", "--top-ports", "50", "--open", "-oN", udp_file, ip], check=True)
        with open(udp_file, "r") as f:
            udp_ports = re.findall(r"^(\d+)/udp\s+open", f.read(), re.MULTILINE)
            results["open_udp_ports"] = sorted([int(p) for p in udp_ports])
    except Exception as e:
        results["error"] = f"Erreur UDP scan : {str(e)}"

    # 4. DEEP SCAN
    if results["open_tcp_ports"]:
        ports_str = ",".join(str(p) for p in results["open_tcp_ports"])
        deep_file = os.path.join(scan_dir, "deep_scan.txt")
        print(f"[4] 🧠 Scan approfondi (ports : {ports_str})...")
        try:
            subprocess.run([
                "nmap", "-Pn", "-sC", "-sV", "--script", "vuln",
                "-p", ports_str, "-oN", deep_file, ip
            ], check=True)

            with open(deep_file, "r") as f:
                content = f.read()
                matches = re.findall(r"^(\d+)/tcp\s+open\s+(\S+)", content, re.MULTILINE)
                for port, service in matches:
                    port = int(port)
                    results["services"].append({
                        "port": port,
                        "protocol": "tcp",
                        "service": service
                    })
                    if service in ["http", "http-alt", "proxy"]:
                        results["flags"]["has_http"] = True
                        results["http_ports"].append(port)
                    if service == "https":
                        results["flags"]["has_https"] = True
                        results["https_ports"].append(port)
                    if service == "ftp":
                        results["flags"]["has_ftp"] = True
                    if service in ["microsoft-ds", "netbios-ssn", "smb"]:
                        results["flags"]["has_smb"] = True
                    if service == "domain":
                        results["flags"]["has_dns"] = True
                    if service == "ssh":
                        results["flags"]["has_ssh"] = True

        except Exception as e:
            results["error"] = f"Erreur deep scan : {str(e)}"

    # 5. Check AD ports
    ad_ports = [88, 135, 139, 389, 445, 464, 3268, 9389]
    if any(p in results["open_tcp_ports"] for p in ad_ports):
        results["flags"]["has_ad"] = True

    # 6. Sauvegarde JSON
    with open(os.path.join(scan_dir, "nmap_results.json"), "w") as f:
        json.dump(results, f, indent=4)

    with open(os.path.join(root_dir, "machine-state.json"), "w") as f:
        json.dump(results, f, indent=4)

    # 7. Rapport Markdown à retravailler
    md_path = os.path.join(root_dir, "recon_report.md")
    generate_markdown_report(results, md_path, target_name, platform, ip)

    print("[✓] Analyse terminée. Résultats stockés.")

    print("\n📁 Fichiers générés :")
    print(f" - 🔍 Scan TCP rapide     : {quick_tcp_file}")
    if os.path.exists(udp_file):
        print(f" - 🌊 Scan UDP top 50      : {udp_file}")
    print(f" - 🧠 Scan approfondi      : {deep_file}")
    print(f" - 📄 Rapport Markdown     : {md_path}")
    print(f" - 📦 Résultats JSON       : {os.path.join(scan_dir, 'nmap_results.json')}")
    print(f" - 🧠 machine-state.json   : {os.path.join(root_dir, 'machine-state.json')}")

    return results


def generate_markdown_report(results, output_path, target_name, platform, ip):
    SERVICE_DESCRIPTIONS = {
        "http": "Serveur Web (HTTP)",
        "https": "Serveur Web sécurisé (HTTPS)",
        "ftp": "Serveur FTP (fichiers)",
        "ssh": "Connexion distante SSH",
        "domain": "Service DNS",
        "netbios-ssn": "Partage réseau (NetBIOS)",
        "microsoft-ds": "Partage de fichiers Windows (SMB)",
        "kerberos-sec": "Kerberos (AD)",
        "ldap": "Service LDAP (annuaire)",
        "rpc": "Remote Procedure Call",
        "kpasswd5": "Changement de mot de passe Kerberos",
        "globalcatLDAP": "Catalogue global LDAP (AD)",
        "adws": "Active Directory Web Services",
    }

    with open(output_path, "w") as f:
        f.write(f"# 🔎 Rapport de reconnaissance - {target_name}\n")
        f.write(f"- **IP** : {ip}\n")
        f.write(f"- **Plateforme** : {platform}\n")
        f.write(f"- **Date** : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        f.write("## 🧠 Ports ouverts\n")
        f.write("### TCP\n")
        for port in results["open_tcp_ports"]:
            f.write(f"- {port}/tcp\n")
        f.write("\n### UDP\n")
        for port in results["open_udp_ports"]:
            f.write(f"- {port}/udp\n")
        f.write("\n")

        f.write("## ⚙️ Services détectés\n")
        for svc in results["services"]:
            desc = SERVICE_DESCRIPTIONS.get(svc["service"], "Service inconnu ou générique")
            f.write(f"- **{svc['port']}/tcp ({svc['service']})** → {desc}\n")
        f.write("\n")

        f.write("## 🚩 Indicateurs activés\n")
        for k, v in results["flags"].items():
            if v:
                f.write(f"- ✅ `{k}` activé\n")
        f.write("\n")

        f.write("## ✅ Modules suggérés\n")
        if results["flags"].get("has_http") or results["flags"].get("has_https"):
            f.write("- [x] `web_enum`\n")
        if results["flags"].get("has_smb"):
            f.write("- [x] `smb_enum`\n")
        if results["flags"].get("has_ftp"):
            f.write("- [x] `ftp_enum`\n")
        if results["flags"].get("has_ssh"):
            f.write("- [x] `ssh_enum`\n")
        if results["flags"].get("has_ad"):
            f.write("- [x] `ad_enum_base`\n")
        f.write("- [x] `report_generation`\n")

        f.write("\n## 📁 Fichiers générés\n")
        f.write("- `quick_tcp.txt`, `udp.txt`, `deep_scan.txt`\n")
        f.write("- `nmap_results.json`, `machine-state.json`\n")
        f.write("- `recon_report.md` (ce fichier)\n")

        f.write("\n---\n_Généré automatiquement par **Omniscient**_\n")

