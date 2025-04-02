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

    # Check Active Directory
    ad_ports = [88, 135, 139, 389, 445, 464, 3268, 9389]
    if any(p in results["open_tcp_ports"] for p in ad_ports):
        results["flags"]["has_ad"] = True

    # 5. Sauvegarde JSON
    with open(os.path.join(scan_dir, "nmap_results.json"), "w") as f:
        json.dump(results, f, indent=4)

    # 6. Écriture machine-state.json
    with open(os.path.join(root_dir, "machine-state.json"), "w") as f:
        json.dump(results, f, indent=4)

    # 7. Rapport Markdown
    md_path = os.path.join(root_dir, "recon_report.md")
    with open(md_path, "w") as f:
        f.write(f"# 🔎 Reconnaissance - {target_name}\n")
        f.write(f"- IP : {ip}\n")
        f.write(f"- Plateforme : {platform}\n")
        f.write(f"- Date : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("## 🧠 Résumé des ports ouverts\n")
        f.write(f"**TCP :** {', '.join(map(str, results['open_tcp_ports']))}\n\n")
        f.write(f"**UDP :** {', '.join(map(str, results['open_udp_ports']))}\n\n")
        f.write("## ⚙️ Services détectés\n")
        for svc in results["services"]:
            f.write(f"- {svc['port']}/tcp → {svc['service']}\n")
        f.write("\n## 🚩 Indicateurs activés\n")
        for k, v in results["flags"].items():
            if v:
                f.write(f"- {k}\n")

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
