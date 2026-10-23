"""Segundo sondeo: guarda fragmentos de las páginas para entender su estructura (data/fragmentos/)."""
import json
import re
import sys
from pathlib import Path
from urllib.parse import quote

from curl_cffi import requests as http

Q = sys.argv[1] if len(sys.argv) > 1 else "audifonos jbl tune 520"
qe = quote(Q)
OUT = Path("data/fragmentos")
OUT.mkdir(parents=True, exist_ok=True)


def get(url, **kw):
    return http.get(url, impersonate="chrome", timeout=40, verify=False,
                    headers={"Accept-Language": "es-CO,es;q=0.9"}, **kw)


def guardar(nombre, texto):
    (OUT / nombre).write_text(texto[:60000], encoding="utf-8")


# Ktronix y Alkosto: contexto alrededor de "algolia"
for tienda in ("ktronix", "alkosto"):
    try:
        t = get(f"https://www.{tienda}.com/search?text={qe}").text
        frag = []
        for m in re.finditer(r"(?i)algolia", t):
            frag.append(t[max(0, m.start() - 300): m.end() + 300].replace("\n", " "))
            if len(frag) >= 25:
                break
        guardar(f"{tienda}_algolia.txt", "\n----\n".join(frag) or "(sin coincidencias)")
    except Exception as e:
        guardar(f"{tienda}_algolia.txt", f"ERROR {e}")

# Falabella y Homecenter: estructura de __NEXT_DATA__
for tienda, url in (("falabella", f"https://www.falabella.com.co/falabella-co/search?Ntt={qe}"),
                    ("homecenter", f"https://www.homecenter.com.co/homecenter-co/search?Ntt={qe}")):
    try:
        t = get(url).text
        m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', t, re.S)
        if not m:
            guardar(f"{tienda}_next.txt", "sin __NEXT_DATA__")
            continue
        d = json.loads(m.group(1))
        res = d.get("props", {}).get("pageProps", {}).get("results")
        resumen = {"pageProps_claves": list(d.get("props", {}).get("pageProps", {}))[:40],
                   "n_results": len(res) if isinstance(res, list) else None,
                   "primero": res[0] if isinstance(res, list) and res else None}
        guardar(f"{tienda}_next.json", json.dumps(resumen, ensure_ascii=False, indent=1))
    except Exception as e:
        guardar(f"{tienda}_next.json", f"ERROR {e}")

# Amazon: primer resultado de búsqueda
try:
    t = get(f"https://www.amazon.com/s?k={qe}").text
    items = re.findall(r'(<div[^>]+data-component-type="s-search-result".*?)(?=<div[^>]+data-component-type="s-search-result"|$)', t, re.S)
    guardar("amazon.txt", f"items={len(items)}\n" + (items[0][:15000] if items else t[:5000]))
except Exception as e:
    guardar("amazon.txt", f"ERROR {e}")

# Mercado Libre: página de listado (con y sin filtro de tiendas oficiales)
for nombre, url in (("ml_listado", f"https://listado.mercadolibre.com.co/{Q.replace(' ', '-')}"),
                    ("ml_oficiales", f"https://listado.mercadolibre.com.co/{Q.replace(' ', '-')}_Tienda_all"),
                    ("ml_api", f"https://api.mercadolibre.com/sites/MCO/search?q={qe}")):
    try:
        r = get(url, allow_redirects=True)
        guardar(f"{nombre}.txt", f"estado={r.status_code} url_final={r.url}\n" + r.text[:20000])
    except Exception as e:
        guardar(f"{nombre}.txt", f"ERROR {e}")
print("ok")
