# Omniscient

**Automated Offensive Recon Framework**  
Projet perso cyber – Reconnaissance, Enumération & Reporting

---

## 🚀 Présentation

**Omniscient** est un outil modulaire de reconnaissance automatisée, conçu pour assister les phases de **pentest** et de **CTF**.  
Il permet de lancer rapidement une suite cohérente de scans, d’enrichir dynamiquement la cartographie d’une cible, et de produire un rapport clair et exploitable.

Le projet est en **en cours de développement** et amené à évoluer vers une solution complète avec interface graphique, smart chaining (enchainement des outils selons résultats précédents), analyse de vulnérabilités, dockerisation et plus.

L'objectif final est d'avoir un outil complet, éducatif et intelligent avec une intégration d'un LLM en Model Context Protocol afin d'orienter l'exploitation post-reconnaissance.

---

## ⚙️ Fonctionnalités actuelles

- [x] **Scan Nmap** (TCP, UDP, vulnérabilités, parsing avancé)
- [x] **Reconnaissance Web** (WhatWeb, Gobuster, support HTTPS)
- [x] **Enum SMB / FTP / SSH** (bannières, partages, accès invité, bruteforce léger)
- [x] **Machine-state.json** centralisé (état machine enrichi dynamiquement)
- [x] **Smart chaining** automatique de modules en fonction des services détectés
- [x] **Rapport Markdown** généré automatiquement (à travailler)
- [x] Structure organisée et évolutive (modules isolés et indépendants, config YAML)

---

## 📁 Arborescence

# Omniscient :

Omniscient/
├── omniscient/
│   ├── __init__.py
│   ├── main.py                     ← Lancement principal
│   ├── module_launcher.py          ← Lancement modulaire (auto, all, etc.)
│   ├── config.yaml                 ← Configuration centrale
│   ├── utils/
│   │   └── file_handler.py         ← Fonctions I/O (machine-state, etc.)
│   └── modules/
│       ├── nmap_scan.py            ← Scan réseau (TCP/UDP/Deep + parsing)
│       ├── web_enum.py             ← WhatWeb + Gobuster
│       ├── smb_enum.py             ← Enum SMB
│       ├── ftp_enum.py             ← Enum FTP
│       ├── ssh_enum.py             ← Fingerprint + bruteforce SSH
│       └── report_generation.py    ← Rapport markdown auto
├── requirements.txt                ← Dépendances Python (PyYAML)
├── README.md                       ← Présentation GitHub
└── .gitignore                      ← (à ajouter au dépôt GitHub)


# Arboresence d'environnement pentest :

~/Pentest/
├── 01_tools/
│   └── SecLists/
│       └── Discovery/Web-Content/  ← Wordlists pour Gobuster
├── 02_targets/
│   └── HTB/
│       └── Code/                   ← Machine en cours
│           ├── scans/
│           │   ├── quick_tcp.txt
│           │   ├── udp.txt
│           │   ├── deep_scan.txt
│           │   ├── gobuster_http.txt (si lancé)
│           │   ├── web-recon.json
│           │   ├── smb_enum.txt
│           │   ├── ftp_enum.txt
│           │   ├── ssh_enum.txt
│           │   └── nmap_results.json
│           ├── recon_report.md     ← Rapport central
│           └── machine-state.json  ← Données de reco globales (pour chaining)
├── 03_notes/
├── 04_reports/
├── 05_scripts/
├── 06_vuln-db/
└── 07_wordlists/
└── 08_tmp/

Pour créer l'arbo d'environnement Pentest : 
mkdir -p ~/pentest/{01_tools,02_targets/HTB,02_targets/TryHackMe,03_notes/cheatsheets,04_reports,05_scripts,06_vuln-db,07_wordlists,08_tmp}


---

## 🧠 Utilisation

### Lancement principal :
sudo -E python3 ~/Omniscient/omniscient/main.py --target <NomMachine> --platform <HTB> --ip <IP>

# Mode auto (smart chaining)
sudo -E python3 ~/Omniscient/omniscient/module_launcher.py --mode auto --target <NomMachine> --platform <HTB> --ip <IP>

# Mode all (tout exécuter sauf nmap)
sudo -E python3 ~/Omniscient/omniscient/module_launcher.py --mode all --target <NomMachine> --platform <HTB> --ip <IP>

# Module unique
python3 ~/Omniscient/omniscient/module_launcher.py --module <NomModule> --target <NomMachine> --platform <HTB> --ip <IP>


---

## ⚡ Pré-requis

- Python 3.8+
- nmap, whatweb, gobuster, enum4linux, smbmap, ftp, sshpass, nc 
- SecLists installé dans ~/Pentest/01_tools/
- OS Linux (distro offensive recommandée)

Pour installer les outils :
sudo apt install -y $(cat apt-packages.txt)

---

## 🤝 Contribuer

Le projet est en cours de développement.
Toute idée, retour, contribution ou collaboration est bienvenue.

N'hésitez pas à me contacter via LinkedIn.

