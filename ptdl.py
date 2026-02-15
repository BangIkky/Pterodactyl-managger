#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import json
import re
import os
import random
import urllib.request
import urllib.error
import ssl
from datetime import datetime

CONFIG_FILE = "config.json"

PANELS = []
RESOURCE_MAP = {
    "1gb": {"ram": 1000, "disk": 1000, "cpu": 40},
    "2gb": {"ram": 2000, "disk": 1000, "cpu": 60},
    "3gb": {"ram": 3000, "disk": 2000, "cpu": 80},
    "4gb": {"ram": 4000, "disk": 2000, "cpu": 100},
    "5gb": {"ram": 5000, "disk": 3000, "cpu": 120},
    "6gb": {"ram": 6000, "disk": 3000, "cpu": 140},
    "7gb": {"ram": 7000, "disk": 4000, "cpu": 160},
    "8gb": {"ram": 8000, "disk": 4000, "cpu": 180},
    "9gb": {"ram": 9000, "disk": 5000, "cpu": 200},
    "10gb": {"ram": 10000, "disk": 5000, "cpu": 220},
    "unlimited": {"ram": 0, "disk": 0, "cpu": 0}
}

SELECTED_PANEL = None
PANEL_DOMAIN = ""
PANEL_PTLA = ""
PANEL_NESTID = ""
PANEL_EGG = ""
PANEL_LOC = ""
PANEL_STATUS = "Nonaktif"

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'
    WHITE = '\033[97m'
    MAGENTA = '\033[35m'

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_current_date():
    now = datetime.now()
    return now.strftime("%d %B %Y")

def press_enter():
    print("")
    input(Colors.YELLOW + "> Tekan Enter untuk melanjutkan..." + Colors.END)

def load_panels():
    global PANELS
    try:
        with open(CONFIG_FILE, 'r') as f:
            PANELS = json.load(f)
    except FileNotFoundError:
        print(Colors.RED + f"File konfigurasi {CONFIG_FILE} tidak ditemukan. Buat file tersebut dengan format yang benar." + Colors.END)
        sys.exit(1)
    except json.JSONDecodeError:
        print(Colors.RED + f"File konfigurasi {CONFIG_FILE} tidak valid JSON." + Colors.END)
        sys.exit(1)

def show_banner():
    global PANEL_STATUS
    current_date = get_current_date()
    panel_display = SELECTED_PANEL["name"] if SELECTED_PANEL else "BELUM DIPILIH"
    status_color = Colors.GREEN if PANEL_STATUS == "AKTIF" else Colors.RED
    print(Colors.CYAN + "╭──────────────────────────────────────────────────" + Colors.END)
    print(Colors.CYAN + "│ " + Colors.WHITE + "Panel" + Colors.CYAN + "   : " + Colors.YELLOW + panel_display + Colors.END)
    print(Colors.CYAN + "│ " + Colors.WHITE + "Status" + Colors.CYAN + "   : " + status_color + PANEL_STATUS + Colors.END)
    print(Colors.CYAN + "│ " + Colors.WHITE + "Domain" + Colors.CYAN + "   : " + Colors.YELLOW + (SELECTED_PANEL["domain"] if SELECTED_PANEL else "-") + Colors.END)
    print(Colors.CYAN + "│ " + Colors.WHITE + "Date" + Colors.CYAN + "    : " + Colors.YELLOW + current_date + Colors.END)
    print(Colors.CYAN + "├──────────────────────────────────────────────────" + Colors.END)
    print(Colors.CYAN + "╰──────────────────────────────────────────────────" + Colors.END)
    print(Colors.CYAN + " .................................................." + Colors.END)
    print("")

def show_panel_menu():
    print(Colors.CYAN + "┏━『 PILIH PANEL 』" + Colors.END)
    for i, panel in enumerate(PANELS, 1):
        num_str = "{:02d}".format(i)
        print(Colors.CYAN + "┃" + Colors.GREEN + "[" + Colors.YELLOW + num_str + Colors.GREEN + "]" + Colors.WHITE + " " + panel["name"] + Colors.END)
    print(Colors.CYAN + "┃" + Colors.RED + "[00]" + Colors.WHITE + " Keluar" + Colors.END)
    print(Colors.CYAN + "┗━━━━━━━◧" + Colors.END)
    while True:
        try:
            choice = int(input(Colors.BOLD + "> Pilih panel [0-%d]: " % len(PANELS) + Colors.END))
            if choice == 0:
                return None
            if 1 <= choice <= len(PANELS):
                return PANELS[choice - 1]
            else:
                print(Colors.RED + "Pilihan tidak valid!" + Colors.END)
        except ValueError:
            print(Colors.RED + "Masukkan angka yang valid!" + Colors.END)

def show_main_menu():
    print(Colors.CYAN + "┏━『 MENU UTAMA 』" + Colors.END)
    print(Colors.CYAN + "┃" + Colors.GREEN + "[1] " + Colors.WHITE + "Buat Akun & Server" + Colors.END)
    print(Colors.CYAN + "┃" + Colors.GREEN + "[2] " + Colors.WHITE + "create admin" + Colors.END)
    print(Colors.CYAN + "┃" + Colors.GREEN + "[3] " + Colors.WHITE + "addserver" + Colors.END)
    print(Colors.CYAN + "┃" + Colors.GREEN + "[4] " + Colors.WHITE + "list server" + Colors.END)
    print(Colors.CYAN + "┃" + Colors.GREEN + "[5] " + Colors.WHITE + "delserver" + Colors.END)
    print(Colors.CYAN + "┃" + Colors.GREEN + "[6] " + Colors.WHITE + "delaccount" + Colors.END)
    print(Colors.CYAN + "┃" + Colors.GREEN + "[7] " + Colors.WHITE + "Ganti Panel" + Colors.END)
    print(Colors.CYAN + "┃" + Colors.RED + "[0] " + Colors.WHITE + "Keluar" + Colors.END)
    print(Colors.CYAN + "┗━━━━━━━◧" + Colors.END)
    print(Colors.WHITE + "powered by ikky" + Colors.END)
    choice = input(Colors.BOLD + "> Pilih menu [0-7]: " + Colors.END)
    return choice

def pterodactyl_request(method, endpoint, data=None):
    url = f"{PANEL_DOMAIN}/api/application/{endpoint}"
    headers = {
        "Authorization": f"Bearer {PANEL_PTLA}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0"
    }
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(url, headers=headers, method=method)
    if data is not None:
        req.data = json.dumps(data).encode('utf-8')
    try:
        with urllib.request.urlopen(req, context=ctx) as response:
            status = response.getcode()
            response_data = response.read()
            if status in [200, 201] and response_data:
                return json.loads(response_data)
            elif status in [204, 200] and not response_data:
                return {"success": True}
            else:
                if response_data:
                    return json.loads(response_data)
                else:
                    return {"success": status < 300}
    except urllib.error.HTTPError as e:
        try:
            error_data = json.loads(e.read())
            return error_data
        except:
            return {"errors": [{"detail": f"HTTP Error {e.code}: {e.reason}"}]}
    except urllib.error.URLError as e:
        return {"errors": [{"detail": f"URL Error: {str(e.reason)}"}]}
    except json.JSONDecodeError:
        return {"success": True}
    except Exception as e:
        return {"errors": [{"detail": f"Error: {str(e)}"}]}

def check_api_connection():
    global PANEL_STATUS
    print(Colors.CYAN + "┏━『 CHECKING CONNECTION 』" + Colors.END)
    result = pterodactyl_request("GET", "users?per_page=1")
    if "errors" not in result:
        print(Colors.CYAN + "┃" + Colors.WHITE + " Koneksi API Pterodactyl: " + Colors.GREEN + "SUCCESS" + Colors.END)
        PANEL_STATUS = "AKTIF"
    else:
        print(Colors.CYAN + "┃" + Colors.WHITE + " Koneksi API Pterodactyl: " + Colors.RED + "FAILED" + Colors.END)
        if "errors" in result:
            for err in result["errors"]:
                print(Colors.CYAN + "┃" + Colors.RED + "  - " + str(err.get('detail', 'Unknown error')) + Colors.END)
        PANEL_STATUS = "Nonaktif"
    print(Colors.CYAN + "┗━━━━━━━◧" + Colors.END)
    print("")
    return PANEL_STATUS == "AKTIF"

def get_all_users_simple():
    all_users = []
    page = 1
    while True:
        result = pterodactyl_request("GET", f"users?page={page}&per_page=100")
        if "errors" in result:
            return None
        data = result.get("data", [])
        if not data:
            break
        for item in data:
            all_users.append(item["attributes"])
        page += 1
    return all_users

def get_user_by_username(username):
    users = get_all_users_simple()
    if users is None:
        return None
    for u in users:
        if u["username"] == username:
            return u
    return None

def get_servers_by_user_id(user_id):
    result = pterodactyl_request("GET", f"users/{user_id}?include=servers")
    if "errors" in result:
        return None
    servers = result.get("attributes", {}).get("relationships", {}).get("servers", {}).get("data", [])
    return [s["attributes"] for s in servers]

def delete_server(server_id):
    result = pterodactyl_request("DELETE", f"servers/{server_id}/force")
    if "errors" in result:
        return False
    return True

def delete_user(user_id):
    result = pterodactyl_request("DELETE", f"users/{user_id}")
    if "errors" in result:
        return False
    return True

def create_user(username, is_admin=False):
    password = f"{username}{random.randint(1, 1000)}"
    email = f"{username}@gmail.com"
    name = username + " Server"
    check_result = pterodactyl_request("GET", f"users?filter[email]={email}")
    if "errors" not in check_result and check_result.get("data") and len(check_result["data"]) > 0:
        return {"error": f'Username "{username}" sudah digunakan. Gunakan nama lain!'}
    payload = {
        "email": email,
        "username": username,
        "first_name": name,
        "last_name": "Bot",
        "language": "en",
        "password": password
    }
    if is_admin:
        payload["root_admin"] = True
    result = pterodactyl_request("POST", "users", payload)
    if "errors" in result:
        error_msg = json.dumps(result["errors"][0], indent=2)
        if "already been taken" in error_msg or "taken" in error_msg or "duplicate" in error_msg:
            return {"error": f'Username "{username}" sudah digunakan. Gunakan nama lain!'}
        return {"error": "Error membuat user:\n" + error_msg}
    user = result.get("attributes")
    if not user:
        return {"error": "Gagal mendapatkan data user"}
    return {"user": user, "password": password}

def get_egg_startup():
    result = pterodactyl_request("GET", f"nests/{PANEL_NESTID}/eggs/{PANEL_EGG}")
    if "errors" in result:
        return None
    attributes = result.get("attributes")
    if attributes and "startup" in attributes:
        return attributes["startup"]
    return None

def create_server(user_id, name, ram, disk, cpu):
    startup_cmd = get_egg_startup()
    if not startup_cmd:
        return {"error": "Gagal mengambil startup command dari egg. Periksa ID egg atau izin API."}
    payload = {
        "name": name,
        "description": datetime.now().strftime("%d/%m/%Y"),
        "user": user_id,
        "egg": int(PANEL_EGG),
        "docker_image": "ghcr.io/parkervcp/yolks:nodejs_20",
        "startup": startup_cmd,
        "environment": {
            "INST": "npm",
            "USER_UPLOAD": "0",
            "AUTO_UPDATE": "0",
            "CMD_RUN": "npm start"
        },
        "limits": {
            "memory": ram,
            "swap": 0,
            "disk": disk,
            "io": 500,
            "cpu": cpu
        },
        "feature_limits": {
            "databases": 5,
            "backups": 5,
            "allocations": 5
        },
        "deploy": {
            "locations": [int(PANEL_LOC)],
            "dedicated_ip": False,
            "port_range": []
        }
    }
    result = pterodactyl_request("POST", "servers", payload)
    if "errors" in result:
        return {"error": "Error saat buat server:\n" + json.dumps(result["errors"][0], indent=2)}
    server = result.get("attributes")
    if not server:
        return {"error": "Gagal mendapatkan data server"}
    return {"server": server}

def format_resource(value, unit):
    if value == 0:
        return "Unlimited"
    elif unit == "MB":
        return f"{value/1000}GB"
    else:
        return f"{value}%"

def get_all_users_with_servers():
    all_users = []
    page = 1
    while True:
        result = pterodactyl_request("GET", f"users?include=servers&per_page=100&page={page}")
        if "errors" in result:
            return None
        data = result.get("data", [])
        if not data:
            break
        all_users.extend(data)
        meta = result.get("meta", {})
        pagination = meta.get("pagination", {})
        total_pages = pagination.get("total_pages", 1)
        if page >= total_pages:
            break
        page += 1
    return all_users

def menu_create(is_admin=False):
    clear_screen()
    show_banner()
    if is_admin:
        print(Colors.CYAN + "   『 create admin 』" + Colors.END)
    else:
        print(Colors.CYAN + "   『 BUAT AKUN & SERVER 』" + Colors.END)
    while True:
        username = input(Colors.YELLOW + "> " + Colors.BOLD + "Masukkan username: " + Colors.END).strip().lower()
        if not username:
            print(Colors.RED + "Username tidak boleh kosong!" + Colors.END)
            continue
        if not re.match(r'^[a-z0-9][a-z0-9_-]*$', username):
            print(Colors.RED + "Username hanya boleh huruf kecil, angka, underscore, dan strip." + Colors.END)
            continue
        break
    resource_key = None
    if not is_admin:
        print(Colors.CYAN + "\nPilih spesifikasi server:" + Colors.END)
        resource_list = list(RESOURCE_MAP.keys())
        for i, key in enumerate(resource_list, 1):
            res = RESOURCE_MAP[key]
            ram_txt = "Unlimited" if res["ram"] == 0 else f"{res['ram']/1000}GB"
            disk_txt = "Unlimited" if res["disk"] == 0 else f"{res['disk']/1000}GB"
            cpu_txt = "Unlimited" if res["cpu"] == 0 else f"{res['cpu']}%"
            print(Colors.GREEN + f" [{i:02d}]" + Colors.WHITE + f" {key.upper()}  RAM: {ram_txt}, DISK: {disk_txt}, CPU: {cpu_txt}" + Colors.END)
        print(Colors.RED + " [00]" + Colors.WHITE + " Batal" + Colors.END)
        while True:
            try:
                choice = input(Colors.YELLOW + "> " + Colors.BOLD + "Pilih resource [01-{:02d}]: ".format(len(resource_list)) + Colors.END)
                if choice == '0' or choice == '00':
                    print(Colors.YELLOW + "Pembuatan dibatalkan." + Colors.END)
                    press_enter()
                    return
                num = int(choice)
                if 1 <= num <= len(resource_list):
                    resource_key = resource_list[num-1]
                    break
                else:
                    print(Colors.RED + f"Pilihan tidak valid! Masukkan 01-{len(resource_list):02d}" + Colors.END)
            except ValueError:
                print(Colors.RED + "Masukkan angka yang valid!" + Colors.END)
    print("\n" + Colors.WHITE + "Ringkasan:" + Colors.END)
    print(Colors.WHITE + "  Username : " + Colors.GREEN + username + Colors.END)
    if is_admin:
        print(Colors.WHITE + "  Tipe     : " + Colors.GREEN + "Admin Panel" + Colors.END)
    else:
        res = RESOURCE_MAP[resource_key]
        ram_txt = "Unlimited" if res["ram"] == 0 else f"{res['ram']/1000}GB"
        disk_txt = "Unlimited" if res["disk"] == 0 else f"{res['disk']/1000}GB"
        cpu_txt = "Unlimited" if res["cpu"] == 0 else f"{res['cpu']}%"
        print(Colors.WHITE + "  Resource : " + Colors.GREEN + f"{resource_key.upper()} (RAM: {ram_txt}, DISK: {disk_txt}, CPU: {cpu_txt})" + Colors.END)
    confirm = input(Colors.YELLOW + "> " + Colors.BOLD + "Konfirmasi pembuatan? (y/N): " + Colors.END).strip().lower()
    if confirm not in ['y', 'yes']:
        print(Colors.YELLOW + "Pembuatan dibatalkan." + Colors.END)
        press_enter()
        return
    print(Colors.WHITE + "Memproses..." + Colors.END)
    user_result = create_user(username, is_admin)
    if "error" in user_result:
        print(Colors.RED + user_result["error"] + Colors.END)
        press_enter()
        return
    user = user_result["user"]
    password = user_result["password"]
    if is_admin:
        teks = f"""
{Colors.GREEN} Admin Panel berhasil dibuat!{Colors.END}

{Colors.WHITE} Username:{Colors.END} {Colors.YELLOW}`{user['username']}`{Colors.END}
{Colors.WHITE} Password:{Colors.END} {Colors.YELLOW}`{password}`{Colors.END}
{Colors.WHITE} Email:{Colors.END} {Colors.YELLOW}{user['email']}{Colors.END}
{Colors.WHITE} Hak Akses:{Colors.END} {Colors.GREEN}Root Administrator{Colors.END}
{Colors.WHITE} Dibuat:{Colors.END} {Colors.YELLOW}{datetime.now().strftime('%d/%m/%Y')}{Colors.END}

{Colors.WHITE} Panel:{Colors.END} {Colors.YELLOW}{PANEL_DOMAIN}{Colors.END}

{Colors.CYAN} Note:{Colors.END}
- Akun ini memiliki hak akses penuh (root admin).
- Gunakan dengan hati‑hati.
- Simpan data dengan aman.
"""
        print(teks)
        press_enter()
        return
    res = RESOURCE_MAP[resource_key]
    ram, disk, cpu = res["ram"], res["disk"], res["cpu"]
    server_result = create_server(user["id"], username + " Server", ram, disk, cpu)
    if "error" in server_result:
        print(Colors.RED + server_result["error"] + Colors.END)
        print(Colors.YELLOW + f"User {username} tetap dibuat, tetapi server gagal. User ID: {user['id']}" + Colors.END)
        press_enter()
        return
    server = server_result["server"]
    teks = f"""
{Colors.GREEN} Panel berhasil dibuat!{Colors.END}

{Colors.WHITE} Server ID:{Colors.END} {Colors.YELLOW}{server['id']}{Colors.END}
{Colors.WHITE} Username:{Colors.END} {Colors.YELLOW}`{user['username']}`{Colors.END}
{Colors.WHITE} Password:{Colors.END} {Colors.YELLOW}`{password}`{Colors.END}
{Colors.WHITE} Aktif:{Colors.END} {Colors.YELLOW}{datetime.now().strftime('%d/%m/%Y')}{Colors.END}

{Colors.WHITE} Spesifikasi{Colors.END}
- RAM : {Colors.YELLOW}{format_resource(ram, 'MB')}{Colors.END}
- DISK: {Colors.YELLOW}{format_resource(disk, 'MB')}{Colors.END}
- CPU : {Colors.YELLOW}{format_resource(cpu, '%')}{Colors.END}
- Panel: {Colors.YELLOW}{PANEL_DOMAIN}{Colors.END}

{Colors.CYAN} Note:{Colors.END}
- Berlaku 30 hari (sesuai kebijakan panel)
- Simpan data dengan aman
"""
    print(teks)
    press_enter()

def menu_add_server_to_user():
    clear_screen()
    show_banner()
    print(Colors.CYAN + "   『 addserver 』" + Colors.END)
    print(Colors.WHITE + "Mengambil daftar user..." + Colors.END)
    users = get_all_users_simple()
    if users is None:
        print(Colors.RED + "Gagal mengambil data user dari API." + Colors.END)
        press_enter()
        return
    if not users:
        print(Colors.RED + "Tidak ada user ditemukan." + Colors.END)
        press_enter()
        return
    print(Colors.CYAN + "\nDaftar user:" + Colors.END)
    for i, u in enumerate(users, 1):
        print(Colors.GREEN + f" [{i:02d}]" + Colors.WHITE + f" {u['username']} (ID: {u['id']}, Email: {u['email']})" + Colors.END)
    print(Colors.RED + " [00]" + Colors.WHITE + " Batal" + Colors.END)
    try:
        choice = input(Colors.YELLOW + "> Pilih nomor user: " + Colors.END)
        if choice == '0' or choice == '00':
            print(Colors.YELLOW + "Dibatalkan." + Colors.END)
            press_enter()
            return
        num = int(choice)
        if 1 <= num <= len(users):
            selected_user = users[num-1]
        else:
            print(Colors.RED + "Pilihan tidak valid." + Colors.END)
            press_enter()
            return
    except ValueError:
        print(Colors.RED + "Masukkan angka yang valid!" + Colors.END)
        press_enter()
        return
    print(Colors.CYAN + "\nPilih spesifikasi server:" + Colors.END)
    resource_list = list(RESOURCE_MAP.keys())
    for i, key in enumerate(resource_list, 1):
        res = RESOURCE_MAP[key]
        ram_txt = "Unlimited" if res["ram"] == 0 else f"{res['ram']/1000}GB"
        disk_txt = "Unlimited" if res["disk"] == 0 else f"{res['disk']/1000}GB"
        cpu_txt = "Unlimited" if res["cpu"] == 0 else f"{res['cpu']}%"
        print(Colors.GREEN + f" [{i:02d}]" + Colors.WHITE + f" {key.upper()}  RAM: {ram_txt}, DISK: {disk_txt}, CPU: {cpu_txt}" + Colors.END)
    print(Colors.RED + " [00]" + Colors.WHITE + " Batal" + Colors.END)
    while True:
        try:
            choice = input(Colors.YELLOW + "> " + Colors.BOLD + "Pilih resource [01-{:02d}]: ".format(len(resource_list)) + Colors.END)
            if choice == '0' or choice == '00':
                print(Colors.YELLOW + "Dibatalkan." + Colors.END)
                press_enter()
                return
            num = int(choice)
            if 1 <= num <= len(resource_list):
                resource_key = resource_list[num-1]
                break
            else:
                print(Colors.RED + f"Pilihan tidak valid! Masukkan 01-{len(resource_list):02d}" + Colors.END)
        except ValueError:
            print(Colors.RED + "Masukkan angka yang valid!" + Colors.END)
    res = RESOURCE_MAP[resource_key]
    ram, disk, cpu = res["ram"], res["disk"], res["cpu"]
    default_name = selected_user['username'] + "-server-" + datetime.now().strftime("%Y%m%d%H%M%S")
    print(Colors.WHITE + "\nNama server (kosongkan untuk nama otomatis):" + Colors.END)
    server_name = input(Colors.YELLOW + "> Nama server: " + Colors.END).strip()
    if not server_name:
        server_name = default_name
    print("\n" + Colors.WHITE + "Ringkasan:" + Colors.END)
    print(Colors.WHITE + "  User     : " + Colors.GREEN + selected_user['username'] + Colors.END)
    print(Colors.WHITE + "  Resource : " + Colors.GREEN + f"{resource_key.upper()} (RAM: {format_resource(ram, 'MB')}, DISK: {format_resource(disk, 'MB')}, CPU: {format_resource(cpu, '%')})" + Colors.END)
    print(Colors.WHITE + "  Nama Server: " + Colors.GREEN + server_name + Colors.END)
    confirm = input(Colors.YELLOW + "> " + Colors.BOLD + "Konfirmasi pembuatan server? (y/N): " + Colors.END).strip().lower()
    if confirm not in ['y', 'yes']:
        print(Colors.YELLOW + "Dibatalkan." + Colors.END)
        press_enter()
        return
    server_result = create_server(selected_user['id'], server_name, ram, disk, cpu)
    if "error" in server_result:
        print(Colors.RED + server_result["error"] + Colors.END)
        press_enter()
        return
    server = server_result["server"]
    print(Colors.GREEN + " Server berhasil dibuat!" + Colors.END)
    print(Colors.WHITE + "Server ID: " + Colors.YELLOW + str(server['id']) + Colors.END)
    print(Colors.WHITE + "Nama Server: " + Colors.YELLOW + server['name'] + Colors.END)
    press_enter()

def menu_list_panel():
    clear_screen()
    show_banner()
    print(Colors.CYAN + "   『 list server 』" + Colors.END)
    print(Colors.WHITE + "Mengambil data..." + Colors.END)
    users_data = get_all_users_with_servers()
    if users_data is None:
        print(Colors.RED + "Gagal mengambil data dari API." + Colors.END)
        press_enter()
        return
    if not users_data:
        print(Colors.YELLOW + "Tidak ada akun panel ditemukan." + Colors.END)
        press_enter()
        return
    result = []
    for u in users_data:
        attrs = u["attributes"]
        username = attrs["username"]
        user_id = attrs["id"]
        email = attrs["email"]
        servers = attrs.get("relationships", {}).get("servers", {}).get("data", [])
        total_servers = len(servers)
        result.append(f" {Colors.YELLOW}{username}{Colors.END} ({email})")
        result.append(f" ID: {user_id}")
        result.append(f" Total Server: {total_servers}")
        for s in servers:
            srv = s["attributes"]
            srv_name = srv["name"]
            srv_id = srv["id"]
            ram = srv["limits"]["memory"]
            disk = srv["limits"]["disk"]
            suspended = srv["suspended"]
            status = "Suspended" if suspended else "Active"
            ram_txt = "Unlimited" if ram == 0 else f"{ram/1000}GB"
            disk_txt = "Unlimited" if disk == 0 else f"{disk/1000}GB"
            result.append(f"   - {Colors.GREEN}{srv_name}{Colors.END}")
            result.append(f"     ID: {srv_id}")
            result.append(f"     RAM: {ram_txt}")
            result.append(f"     Disk: {disk_txt}")
            result.append(f"     Status: {status}")
        result.append("")
    print("\n".join(result))
    print(Colors.CYAN + "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" + Colors.END)
    press_enter()

def menu_delete_server():
    clear_screen()
    show_banner()
    print(Colors.CYAN + "   『 delserver 』" + Colors.END)
    print(Colors.WHITE + "Mengambil daftar user..." + Colors.END)
    users = get_all_users_simple()
    if users is None:
        print(Colors.RED + "Gagal mengambil data user dari API." + Colors.END)
        press_enter()
        return
    if not users:
        print(Colors.RED + "Tidak ada user ditemukan." + Colors.END)
        press_enter()
        return
    print(Colors.CYAN + "\nDaftar user:" + Colors.END)
    for i, u in enumerate(users, 1):
        print(Colors.GREEN + f" [{i:02d}]" + Colors.WHITE + f" {u['username']} (ID: {u['id']}, Email: {u['email']})" + Colors.END)
    print(Colors.RED + " [00]" + Colors.WHITE + " Batal" + Colors.END)
    try:
        choice = input(Colors.YELLOW + "> Pilih nomor user: " + Colors.END)
        if choice == '0' or choice == '00':
            print(Colors.YELLOW + "Dibatalkan." + Colors.END)
            press_enter()
            return
        num = int(choice)
        if 1 <= num <= len(users):
            selected_user = users[num-1]
        else:
            print(Colors.RED + "Pilihan tidak valid." + Colors.END)
            press_enter()
            return
    except ValueError:
        print(Colors.RED + "Masukkan angka yang valid!" + Colors.END)
        press_enter()
        return
    servers = get_servers_by_user_id(selected_user['id'])
    if servers is None:
        print(Colors.RED + "Gagal mengambil server milik user." + Colors.END)
        press_enter()
        return
    if not servers:
        print(Colors.YELLOW + f"User {selected_user['username']} tidak memiliki server." + Colors.END)
        press_enter()
        return
    print(Colors.CYAN + f"\nDaftar server milik {selected_user['username']}:" + Colors.END)
    for i, s in enumerate(servers, 1):
        status = "Suspended" if s['suspended'] else "Active"
        print(Colors.GREEN + f" [{i:02d}]" + Colors.WHITE + f" {s['name']} (ID: {s['id']}, Status: {status})" + Colors.END)
    print(Colors.RED + " [00]" + Colors.WHITE + " Batal" + Colors.END)
    try:
        choice = input(Colors.YELLOW + "> Pilih nomor server yang akan dihapus: " + Colors.END)
        if choice == '0' or choice == '00':
            print(Colors.YELLOW + "Dibatalkan." + Colors.END)
            press_enter()
            return
        num = int(choice)
        if 1 <= num <= len(servers):
            selected_server = servers[num-1]
        else:
            print(Colors.RED + "Pilihan tidak valid." + Colors.END)
            press_enter()
            return
    except ValueError:
        print(Colors.RED + "Masukkan angka yang valid!" + Colors.END)
        press_enter()
        return
    print(Colors.RED + f"Anda akan menghapus server: {selected_server['name']} (ID: {selected_server['id']})" + Colors.END)
    confirm = input(Colors.YELLOW + "> Ketik 'YA' untuk konfirmasi: " + Colors.END).strip().upper()
    if confirm != 'YA':
        print(Colors.YELLOW + "Penghapusan dibatalkan." + Colors.END)
        press_enter()
        return
    if delete_server(selected_server['id']):
        print(Colors.GREEN + f" Server '{selected_server['name']}' berhasil dihapus." + Colors.END)
    else:
        print(Colors.RED + f"Gagal menghapus server." + Colors.END)
    press_enter()

def menu_delete_panel():
    clear_screen()
    show_banner()
    print(Colors.CYAN + "   『 delaccount 』" + Colors.END)
    print(Colors.WHITE + "Mengambil daftar user..." + Colors.END)
    users = get_all_users_simple()
    if users is None:
        print(Colors.RED + "Gagal mengambil data user dari API." + Colors.END)
        press_enter()
        return
    if not users:
        print(Colors.RED + "Tidak ada user ditemukan." + Colors.END)
        press_enter()
        return
    print(Colors.CYAN + "\nDaftar user:" + Colors.END)
    for i, u in enumerate(users, 1):
        print(Colors.GREEN + f" [{i:02d}]" + Colors.WHITE + f" {u['username']} (ID: {u['id']}, Email: {u['email']})" + Colors.END)
    print(Colors.RED + " [00]" + Colors.WHITE + " Batal" + Colors.END)
    try:
        choice = input(Colors.YELLOW + "> Pilih nomor user yang akan dihapus: " + Colors.END)
        if choice == '0' or choice == '00':
            print(Colors.YELLOW + "Dibatalkan." + Colors.END)
            press_enter()
            return
        num = int(choice)
        if 1 <= num <= len(users):
            selected_user = users[num-1]
        else:
            print(Colors.RED + "Pilihan tidak valid." + Colors.END)
            press_enter()
            return
    except ValueError:
        print(Colors.RED + "Masukkan angka yang valid!" + Colors.END)
        press_enter()
        return
    username = selected_user['username']
    user_id = selected_user['id']
    email = selected_user['email']
    servers = get_servers_by_user_id(user_id)
    if servers is None:
        print(Colors.RED + "Gagal mengambil server milik user." + Colors.END)
        press_enter()
        return
    print(Colors.RED + f"Anda akan menghapus akun: {username} ({email})" + Colors.END)
    print(Colors.RED + f"Jumlah server yang akan ikut terhapus: {len(servers)}" + Colors.END)
    confirm = input(Colors.YELLOW + "> Ketik 'YA' untuk konfirmasi: " + Colors.END).strip().upper()
    if confirm != 'YA':
        print(Colors.YELLOW + "Penghapusan dibatalkan." + Colors.END)
        press_enter()
        return
    success = True
    for s in servers:
        server_id = s["id"]
        print(Colors.WHITE + f"Menghapus server ID {server_id}..." + Colors.END)
        if not delete_server(server_id):
            print(Colors.RED + f"Gagal menghapus server {server_id}" + Colors.END)
            success = False
    if success:
        print(Colors.GREEN + "Semua server berhasil dihapus." + Colors.END)
    else:
        print(Colors.YELLOW + "Beberapa server gagal dihapus. Tetap mencoba menghapus user..." + Colors.END)
    if delete_user(user_id):
        print(Colors.GREEN + f" Akun panel '{username}' berhasil dihapus." + Colors.END)
    else:
        print(Colors.RED + f"Gagal menghapus akun '{username}'. Mungkin token tidak memiliki izin." + Colors.END)
    press_enter()

def menu_exit():
    clear_screen()
    show_banner()
    print(Colors.CYAN + "   『 EXIT PROGRAM 』" + Colors.END)
    print(Colors.GREEN + "Terima kasih telah menggunakan Pterodactyl-Managger" + Colors.END)
    print(Colors.WHITE + "powered by ikky" + Colors.END)
    sys.exit(0)

def main():
    global SELECTED_PANEL, PANEL_DOMAIN, PANEL_PTLA, PANEL_NESTID, PANEL_EGG, PANEL_LOC, PANEL_STATUS
    load_panels()
    clear_screen()
    show_banner()
    if not PANELS:
        print(Colors.RED + "Tidak ada panel dalam konfigurasi." + Colors.END)
        sys.exit(0)
    selected = show_panel_menu()
    if selected is None:
        menu_exit()
        return
    SELECTED_PANEL = selected
    PANEL_DOMAIN = selected["domain"]
    PANEL_PTLA = selected["ptla"]
    PANEL_NESTID = selected["nestid"]
    PANEL_EGG = selected["egg"]
    PANEL_LOC = selected["loc"]
    clear_screen()
    show_banner()
    check_api_connection()
    press_enter()
    while True:
        try:
            clear_screen()
            show_banner()
            choice = show_main_menu()
            if choice == '1':
                menu_create(is_admin=False)
            elif choice == '2':
                menu_create(is_admin=True)
            elif choice == '3':
                menu_add_server_to_user()
            elif choice == '4':
                menu_list_panel()
            elif choice == '5':
                menu_delete_server()
            elif choice == '6':
                menu_delete_panel()
            elif choice == '7':
                selected = show_panel_menu()
                if selected is not None:
                    SELECTED_PANEL = selected
                    PANEL_DOMAIN = selected["domain"]
                    PANEL_PTLA = selected["ptla"]
                    PANEL_NESTID = selected["nestid"]
                    PANEL_EGG = selected["egg"]
                    PANEL_LOC = selected["loc"]
                    clear_screen()
                    show_banner()
                    check_api_connection()
                press_enter()
            elif choice == '0':
                menu_exit()
            else:
                print(Colors.RED + "Pilihan tidak valid! Silakan pilih 0-7." + Colors.END)
                press_enter()
        except KeyboardInterrupt:
            print(Colors.YELLOW + "\nProgram dihentikan oleh pengguna." + Colors.END)
            sys.exit(0)
        except Exception as e:
            print(Colors.RED + f"Terjadi kesalahan: {str(e)}" + Colors.END)
            press_enter()

if __name__ == "__main__":
    main()
