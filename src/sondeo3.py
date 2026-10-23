"""Tercer sondeo: clave pública de Algolia (Ktronix/Alkosto), estructura de Amazon y Homecenter."""
import json
import re
import sys
from pathlib import Path
from urllib.parse import quote, urljoin

from curl_cffi import requests as http

Q = sys.argv[1] if len(sys.argv) > 1 else "audifonos jbl tune 520"
qe = quote(Q)
OUT = Path("data/fragmentos")
OUT.mkdir(parents=True, exist_ok=True)
get = lambda url: http.get(url, impersonate="chrome", timeout=40, verify=False, headers={"Accept-Language": "es-CO,es;q=0.9"})

# 1) Algolia: buscar la clave en los scripts de Ktronix
info = {}
try:
    base = "https://www.ktronix.com"
    html = get(f"{base}/search?text={qe}").text
    srcs = [urljoin(base, s) for s in re.findall(r'<script[^>]+src="([^"]+)"', html)]
    info["scripts"] = len(srcs)
    # también variables en línea
    for m in re.finditer(r"(?i)(algolia[a-z]*(?:key|apikey|searchkey)|searchApiKey|apiKeySearch)[\"']?\s*[:=]\s*[\"']([A-Za-z0-9=+/]{20,})[\"']", html):
        info.setdefault("en_linea", []).append([m.group(1), m.group(2)])
    hallados = []
    for s in srcs[:60]:
        if any(x in s for x in ("google", "facebook", "hotjar", "gtm", "zkcdn")):
            continue
        try:
            js = get(s).text
        except Exception:
            continue
        if "QX5IPS1B1Q" in js or "algolia" in js.lower():
            for m in re.finditer(r"[\"']([a-f0-9]{32})[\"']", js):
                ctx = js[max(0, m.start() - 120): m.end() + 40].replace("\n", " ")
                hallados.append({"script": s[-80:], "clave": m.group(1), "contexto": ctx})
    info["claves"] = hallados[:10]
    # contexto alrededor de applicationId en el HTML
    i = html.find("applicationId")
    info["ctx_html"] = html[max(0, i - 400): i + 600] if i >= 0 else ""
except Exception as e:
    info["error"] = str(e)
(OUT / "algolia.json").write_text(json.dumps(info, ensure_ascii=False, indent=1), encoding="utf-8")

# 2) Amazon: marcadores
try:
    r = get(f"https://www.amazon.com/s?k={qe}")
    t = r.text
    marc = {k: t.count(k) for k in ("s-search-result", "a-price-whole", "a-offscreen", "captcha", "validateCaptcha", "COP", "US$", "data-asin")}
    i = t.find("a-price-whole")
    (OUT / "amazon2.txt").write_text(f"estado={r.status_code} bytes={len(t)} {marc}\n\n" + (t[max(0, i - 6000): i + 1500] if i >= 0 else t[:3000]), encoding="utf-8")
except Exception as e:
    (OUT / "amazon2.txt").write_text(f"ERROR {e}", encoding="utf-8")

# 3) Homecenter: searchProps
try:
    t = get(f"https://www.homecenter.com.co/homecenter-co/search?Ntt={quote('taladro')}").text
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', t, re.S)
    sp = json.loads(m.group(1))["props"]["pageProps"]["searchProps"]
    def resumen(o, prof=0):
        if prof > 3: return "…"
        if isinstance(o, dict): return {k: resumen(v, prof + 1) for k, v in list(o.items())[:25]}
        if isinstance(o, list): return [len(o), resumen(o[0], prof + 1) if o else None]
        return o if not isinstance(o, str) else o[:80]
    (OUT / "homecenter2.json").write_text(json.dumps(resumen(sp), ensure_ascii=False, indent=1), encoding="utf-8")
except Exception as e:
    (OUT / "homecenter2.json").write_text(f"ERROR {e}", encoding="utf-8")
print("ok")
