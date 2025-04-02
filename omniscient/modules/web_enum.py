import subprocess
import os
import json
from utils.file_handler import load_machine_state

def ask_for_wordlist():
    print("\n[?] Choisis une wordlist :")
    print("1) common.txt")
    print("2) directory-list-2.3-small.txt")
    print("3) directory-list-2.3-medium.txt")
    print("4) directory-list-2.3-big.txt (⚠️ peut prendre plusieurs minutes)")
    print("5) Chemin personnalisé")
    
    base_path = os.path.expanduser("~/Pentest/01_tools/SecLists/Discovery/Web-Content")
    choice = input(">> ").strip()

    wordlist_map = {
        "1": "common.txt",
        "2": "directory-list-2.3-small.txt",
        "3": "directory-list-2.3-medium.txt",
        "4": "directory-list-2.3-big.txt"
    }

    if choice in wordlist_map:
        return os.path.join(base_path, wordlist_map[choice])
    elif choice == "5":
        custom = input("Chemin complet vers la wordlist : ").strip()
        if os.path.exists(custom):
            return custom
        else:
            print("[!] Fichier introuvable. Abandon.")
    else:
        print("[!] Choix invalide.")
    return None

def parse_whatweb_output(raw_output):
    info = {
        "server": None,
        "php": None,
        "cms": None,
        "os": None,
        "technologies": [],
        "others": []
    }

    known_keys = (
        "Apache", "nginx", "Microsoft-IIS",
        "PHP", "WordPress", "Drupal", "Joomla",
        "Ubuntu", "Debian", "CentOS"
    )

    parts = raw_output.strip().split(", ")
    for p in parts:
        p = p.strip()
        info["technologies"].append(p)

        if p.startswith("Apache") or p.startswith("nginx") or p.startswith("Microsoft-IIS"):
            info["server"] = p
        elif p.startswith("PHP"):
            info["php"] = p.replace("PHP/", "PHP ")
        elif "WordPress" in p or "Drupal" in p or "Joomla" in p:
            info["cms"] = p
        elif "Ubuntu" in p or "Debian" in p or "CentOS" in p:
            info["os"] = p
        elif not p.startswith("Country") and not any(k in p for k in known_keys):
            info["others"].append(p)

    return info

def run(target_name, platform, ip, target_base_path, config):
    print("[🌐] Module WebEnum lancé...")

    root_dir = os.path.join(target_base_path, platform, target_name)
    state = load_machine_state(root_dir)
    if not state:
        print("[!] État machine introuvable, WebEnum annulé.")
        return

    flags = state.get("flags", {})
    if not flags.get("has_http") and not flags.get("has_https"):
        print("[i] Aucun service HTTP/HTTPS détecté. WebEnum ignoré.")
        return

    scan_dir = os.path.join(root_dir, "scans")
    os.makedirs(scan_dir, exist_ok=True)

    web_config = config.get("web_enum", {})
    threads = str(web_config.get("gobuster_threads", 50))
    timeout = str(web_config.get("timeout", 10)) + "s"
    extensions = web_config.get("extensions", "")

    wordlist = ask_for_wordlist()
    if not wordlist:
        return

    results = {
        "urls_tested": [],
        "gobuster": {},
        "whatweb_raw": {},
        "whatweb_parsed": {}
    }

    urls = []

    for port in state.get("http_ports", []):
        url = f"http://{ip}" if port == 80 else f"http://{ip}:{port}"
        urls.append((url, port))
    for port in state.get("https_ports", []):
        url = f"https://{ip}" if port == 443 else f"https://{ip}:{port}"
        urls.append((url, port))

    for url, port in urls:
        proto = "https" if url.startswith("https") else "http"
        output_file = os.path.join(scan_dir, f"gobuster_{proto}_{port}.txt")

        # Gobuster
        print(f"\n[→] Gobuster sur {url} avec {os.path.basename(wordlist)}...")
        cmd = [
            "gobuster", "dir",
            "-u", url,
            "-w", wordlist,
            "-t", threads,
            "--timeout", timeout,
            "-o", output_file
        ]
        if extensions:
            cmd.extend(["-x", extensions])
        try:
            subprocess.run(cmd, check=True)
            print(f"[✓] Résultats : {output_file}")
            results["gobuster"][url] = output_file
        except Exception as e:
            print(f"[!] Erreur Gobuster : {str(e)}")

        # WhatWeb
        print(f"[→] WhatWeb pour {url}...")
        try:
            ww = subprocess.check_output(["whatweb", url], stderr=subprocess.DEVNULL).decode()
            parsed = parse_whatweb_output(ww)
            results["whatweb_raw"][url] = ww.strip()
            results["whatweb_parsed"][url] = parsed
        except Exception as e:
            results["whatweb_raw"][url] = f"[!] Erreur WhatWeb : {str(e)}"
            results["whatweb_parsed"][url] = {}

        results["urls_tested"].append(url)

    json_path = os.path.join(scan_dir, "web-recon.json")
    with open(json_path, "w") as f:
        json.dump(results, f, indent=4)

    print(f"\n[✓] WebEnum terminé. Résumé sauvegardé dans : {json_path}")
