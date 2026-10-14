#!/usr/bin/env python3
"""MODSTORE fetcher (Appteka API, sirf Python stdlib).

  python3 appteka_fetch.py --seed purani.json            # purane JSON se app ids import
  python3 appteka_fetch.py --add --index apps --count 200 # sitemap se naye app ids add
  python3 appteka_fetch.py --refresh                      # sab ids ka fresh info -> data/apps.json

download_link / icon / screenshots ko BADLA nahi jaata: token wale asli links save hote hain.
State: data/ids.json  ({"ids":[...], "gone":[...]})   Output: data/apps.json
"""
import argparse, gzip, json, os, random, re, sys, threading, time, urllib.error, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

HOST = "https://appteka.store"; BASE = HOST + "/api/1"
IDS = "data/ids.json"; OUT = "data/apps.json"
CANARY = ["16cr329192", "abar4", "8ecr329195"]
ID_RE = re.compile(r"/(?:app|apps)/([0-9a-z]+)", re.I)
_lock = threading.Lock(); _next = [0.0]

def headers(locale="en"):
    dev = os.environ.get("DEVICE_ID") or "".join(random.choice("0123456789abcdef") for _ in range(16))
    now = datetime.now().astimezone(); lt = now.strftime("%Y-%m-%dT%H:%M:%S%z"); lt = lt[:-2] + ":" + lt[-2:]
    return {"User-Agent": f"Appteka/24.0.1175 (Android; sdk:33; com.tomclaw.appsend; en-US)",
            "X-Device-ID": dev, "X-App-Package": "com.tomclaw.appsend", "X-App-Version-Name": "24.0",
            "X-App-Version-Code": "1175", "X-App-Signature": "unknown", "X-Android-Version": "33",
            "X-Android-Release": "13", "X-Device-Manufacturer": "Android", "X-Device-Model": "Android",
            "X-Locale": "en-US", "X-Theme": "dark", "X-Timezone": "UTC", "X-Local-Time": lt,
            "Accept": "application/json", "Accept-Encoding": "gzip"}
H = headers()

def get(url, rate=4.0, retries=3):
    """(status, bytes). Rate-limited, retries on 429/5xx."""
    for i in range(retries):
        with _lock:
            t = max(time.monotonic(), _next[0]); _next[0] = t + 1.0 / rate
        time.sleep(max(0.0, t - time.monotonic()))
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=H), timeout=30) as r:
                d = r.read()
                return r.status, (gzip.decompress(d) if d[:2] == b"\x1f\x8b" else d)
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and i < retries - 1:
                time.sleep(2 * (i + 1)); continue
            return e.code, b""
        except Exception:
            if i == retries - 1: return 0, b""
            time.sleep(2 * (i + 1))
    return 0, b""

def info(aid):
    st, d = get(BASE + "/app/info?" + urllib.parse.urlencode({"app_id": aid, "locale": "en"}))
    if st != 200: return st, None
    try: return 200, (json.loads(d.decode("utf-8", "replace")).get("result") or {})
    except Exception: return 0, None

def extract(aid, d):
    i = d.get("info") or {}; m = d.get("meta") or {}; pkg = i.get("package"); sh = m.get("screenshots") or []
    size = i.get("size") or 0; c = m.get("category")
    cat = (c.get("name") or {}).get("en") if isinstance(c, dict) and isinstance(c.get("name"), dict) else None
    return {"app_id": i.get("app_id") or aid, "name": i.get("label"), "package": pkg, "play_store_id": pkg,
            "play_store_url": f"https://play.google.com/store/apps/details?id={pkg}" if pkg else None,
            "icon": i.get("icon"), "description": m.get("description"), "whats_new": m.get("whats_new"),
            "images": [s.get("original") for s in sh if s.get("original")],
            "screenshots": [{"original": s.get("original"), "preview": s.get("preview"), "width": s.get("width"), "height": s.get("height")} for s in sh],
            "download_link": d.get("link"),            # token ke saath, as-is
            "version": i.get("ver_name"), "version_code": i.get("ver_code"), "size": size,
            "size_mb": round(size / 1024 / 1024, 2) if size else 0, "downloads": i.get("downloads"),
            "rating": m.get("rating"), "category": cat, "author": (i.get("author") or {}).get("name"),
            "source_url": m.get("source_url") or "", "security": (d.get("security") or {}).get("verdict"),
            "page_url": d.get("url") or f"{HOST}/app/{aid}"}

def load():
    try: s = json.load(open(IDS, encoding="utf-8"))
    except Exception: s = {}
    return {"ids": list(s.get("ids", [])), "gone": list(s.get("gone", []))}

def save(s):
    os.makedirs(os.path.dirname(IDS), exist_ok=True)
    json.dump(s, open(IDS, "w", encoding="utf-8"), indent=0)

def locs(xml):
    return [e.text.strip() for e in ET.fromstring(xml).iter() if e.tag.split("}")[-1] == "loc" and e.text]

def seed(path):
    j = json.load(open(path, encoding="utf-8")); lst = j["apps"] if isinstance(j, dict) else j
    s = load(); have = set(s["ids"]); new = [a["app_id"] for a in lst if a.get("app_id") and a["app_id"] not in have]
    s["ids"] += new; save(s); print(f"seed: +{len(new)} ids (total {len(s['ids'])})")

def add(index, count):
    s = load(); have = set(s["ids"]) | set(s["gone"])
    st, d = get(HOST + "/sitemap.xml")
    if st != 200: sys.exit(f"sitemap index HTTP {st}")
    kids = locs(d)
    if index.isdigit() and 1 <= int(index) <= len(kids): pick = [kids[int(index) - 1]]
    else: pick = [k for k in kids if index.lower() in ("all", "a", "*") or index.lower() in k.lower()]
    if not pick: sys.exit("is naam ka sitemap nahi mila: " + ", ".join(k.rsplit("/", 1)[-1] for k in kids))
    found = {}
    for u in pick:
        st, d = get(u)
        if st != 200: print("  skip", u, st); continue
        for l in locs(d):
            m = ID_RE.search(l)
            if m: found.setdefault(m.group(1), 1)
    new = [a for a in found if a not in have]
    take = new if str(count).lower() in ("all", "a") else new[:int(count)]
    s["ids"] += take; save(s)
    print(f"add: sitemap me {len(found)} ids, naye {len(new)}, add kiye {len(take)}, total {len(s['ids'])}")

def refresh():
    s = load(); ids = [i for i in s["ids"] if i not in set(s["gone"])]
    if not ids: sys.exit("data/ids.json khali hai. Pehle --seed ya --add chalao.")
    def one(aid):
        st, d = info(aid)
        return aid, (extract(aid, d) if st == 200 and d and d.get("info") else None), st
    with ThreadPoolExecutor(max_workers=6) as ex: res = list(ex.map(one, ids))
    ok = [r[1] for r in res if r[1]]; dead = [r[0] for r in res if r[1] is None and r[2] == 500]
    print(f"refresh: {len(ok)}/{len(ids)} ok, {len(dead)} dead(500), {len(ids) - len(ok) - len(dead)} failed")
    if dead and not any(info(c)[0] == 200 for c in CANARY):   # canary fail = server block, apps dead nahi
        sys.exit("Canary check fail: server block/down lagta hai. Site update nahi ki.")
    if not ok or len(ok) < 0.8 * (len(ids) - len(dead)):      # bahut kam apps -> deploy mat karo
        sys.exit("Bahut kam apps mile (<80%). Shayad block/rate-limit. Site update nahi ki.")
    if dead: s["gone"] = sorted(set(s["gone"]) | set(dead)); save(s)
    os.makedirs("data", exist_ok=True)
    json.dump({"generated_at": datetime.now().astimezone().isoformat(timespec="seconds"), "count": len(ok), "apps": ok},
              open(OUT + ".tmp", "w", encoding="utf-8"), ensure_ascii=False)
    os.replace(OUT + ".tmp", OUT); print("saved", OUT)

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--seed"); p.add_argument("--add", action="store_true"); p.add_argument("--refresh", action="store_true")
    p.add_argument("--index"); p.add_argument("--count"); a = p.parse_args()
    if a.seed: seed(a.seed)
    elif a.add:
        add(a.index or input("Sitemap (number ya naam jaise 'apps'): ").strip(), a.count or input("Kitne naye apps (number/all): ").strip())
    elif a.refresh: refresh()
    else: p.print_help()
