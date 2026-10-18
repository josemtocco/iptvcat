#!/usr/bin/env python3
"""
Gera lista M3U otimizada para SS IPTV a partir de iptvcat.com/brazil__10/
- Mantém canais que ainda funcionam
- Remove só após 3 falhas consecutivas
- Categorias em português
"""

import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup

# ============== CONFIG ==============
BASE_URLS = [
    "https://iptvcat.com/brazil__10/",
    "https://iptvcat.com/brazil__10/2",
]
STATE_FILE = Path("state.json")
OUTPUT_M3U = Path("brazil_ssiptv.m3u")
MAX_FAILS = 3
TIMEOUT = 12
MAX_WORKERS = 10
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

HEADERS = {"User-Agent": USER_AGENT}

def categorize(name: str) -> str:
    n = name.lower()
    if any(x in n for x in ["news", "notícia", "record news", "bandnews", "cnn", "bbc"]):
        return "Notícias"
    if any(x in n for x in ["sport", "esporte", "fifa", "futebol", "nba", "ufc"]):
        return "Esportes"
    if any(x in n for x in ["kids", "infantil", "gloob", "nickelodeon", "cartoon", "disney"]):
        return "Infantil"
    if any(x in n for x in ["gospel", "igreja", "religi", "canção nova", "boas novas", "iurd", "rit", "cancao nova"]):
        return "Religiosos"
    if any(x in n for x in ["filme", "cinema", "movie", "série", "pluto tv cine", "series"]):
        return "Filmes & Séries"
    if any(x in n for x in ["música", "music", "mtv", "kpop"]):
        return "Música"
    return "Geral / Variedades"

def fetch_page(url: str) -> list:
    print(f"Scraping: {url}")
    r = requests.get(url, headers=HEADERS, timeout=25)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "lxml")

    channels = []
    for a in soup.select('a[href*="list.iptvcat.com/my_list"]'):
        href = a.get("href")
        if not href or not href.endswith(".m3u8"):
            continue
        channels.append({"mini_m3u": href})
    return channels

def parse_mini_m3u(url: str) -> dict | None:
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        if r.status_code != 200:
            return None
        content = r.text
        m = re.search(r'#EXTINF:.*?,(.*?)\n(https?://[^\s]+)', content, re.DOTALL)
        if not m:
            return None
        name = m.group(1).strip()
        stream = m.group(2).strip()
        logo_m = re.search(r'tvg-logo="([^"]+)"', content)
        logo = logo_m.group(1) if logo_m else ""
        return {"name": name, "url": stream, "logo": logo}
    except Exception:
        return None

def is_alive(url: str) -> bool:
    try:
        r = requests.head(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
        if r.status_code in (200, 206, 302, 301, 307, 308):
            return True
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT, stream=True)
        if r.status_code in (200, 206):
            next(r.iter_content(1024), None)
            return True
        return False
    except Exception:
        return False

def load_state() -> dict:
    if STATE_FILE.exists():
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_state(state: dict):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def generate_m3u(channels: list) -> str:
    lines = ["#EXTM3U"]
    channels.sort(key=lambda c: (c["category"], c["name"].lower()))

    for ch in channels:
        logo = f' tvg-logo="{ch["logo"]}"' if ch.get("logo") else ""
        lines.append(
            f'#EXTINF:-1 group-title="{ch["category"]}"{logo},{ch["name"]}'
        )
        lines.append(ch["url"])
    return "\n".join(lines) + "\n"

def main():
    print(f"[{datetime.now(timezone.utc).isoformat()}] Iniciando atualização...")

    all_mini = []
    for url in BASE_URLS:
        try:
            all_mini.extend(fetch_page(url))
            time.sleep(1.5)
        except Exception as e:
            print(f"Erro ao scrapar {url}: {e}")

    # Remove duplicates
    seen_mini = set()
    unique_mini = []
    for item in all_mini:
        if item["mini_m3u"] not in seen_mini:
            seen_mini.add(item["mini_m3u"])
            unique_mini.append(item)

    print(f"Encontrados {len(unique_mini)} links de download únicos")

    parsed = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(parse_mini_m3u, item["mini_m3u"]): item for item in unique_mini}
        for fut in as_completed(futures):
            result = fut.result()
            if result:
                result["category"] = categorize(result["name"])
                parsed.append(result)

    print(f"Mini-M3Us válidos: {len(parsed)}")

    state = load_state()
    new_state = {}
    alive_channels = []

    def check_one(ch):
        url = ch["url"]
        ok = is_alive(url)
        return ch, ok

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(check_one, ch): ch for ch in parsed}
        for fut in as_completed(futures):
            ch, ok = fut.result()
            url = ch["url"]
            prev = state.get(url, {"fail_count": 0})

            if ok:
                fail = 0
                alive_channels.append(ch)
            else:
                fail = prev.get("fail_count", 0) + 1

            if fail < MAX_FAILS:
                new_state[url] = {
                    "name": ch["name"],
                    "logo": ch.get("logo", ""),
                    "category": ch["category"],
                    "fail_count": fail,
                    "last_checked": datetime.now(timezone.utc).isoformat(),
                }
                if fail > 0:
                    alive_channels.append(ch)

    # Mantém canais antigos que ainda não chegaram a 3 falhas
    for url, data in state.items():
        if url not in new_state and data.get("fail_count", 0) < MAX_FAILS:
            data["fail_count"] = data.get("fail_count", 0) + 1
            if data["fail_count"] < MAX_FAILS:
                new_state[url] = data
                alive_channels.append({
                    "name": data["name"],
                    "url": url,
                    "logo": data.get("logo", ""),
                    "category": data.get("category", "Geral / Variedades"),
                })

    seen = set()
    unique = []
    for ch in alive_channels:
        if ch["url"] not in seen:
            seen.add(ch["url"])
            unique.append(ch)

    print(f"Canais finais na lista: {len(unique)}")

    m3u_content = generate_m3u(unique)
    OUTPUT_M3U.write_text(m3u_content, encoding="utf-8")
    print(f"M3U gerado: {OUTPUT_M3U} ({len(m3u_content)} bytes)")

    save_state(new_state)
    print("Estado salvo.")

    fails = sum(1 for v in new_state.values() if v.get("fail_count", 0) > 0)
    print(f"Canais com falhas acumuladas: {fails}")

if __name__ == "__main__":
    main()
