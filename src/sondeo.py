"""Prueba qué tiendas responden a búsquedas automáticas desde GitHub Actions.
Guarda el resultado en data/sondeo.json (sin datos personales)."""
import json
import re
import sys
from pathlib import Path
from urllib.parse import quote

from curl_cffi import requests as http

Q = sys.argv[1] if len(sys.argv) > 1 else "audifonos jbl"
qe = quote(Q)

PRUEBAS = {
    # Plataforma VTEX (la misma del comparador de mercado)
    **{f"vtex:{d}": f"https://www.{d}/api/catalog_system/pub/products/search?ft={qe}&_from=0&_to=4" for d in [
        "exito.com", "olimpica.com", "carulla.com", "tiendasjumbo.co", "tiendasmetro.co", "panamericana.com.co",
        "alkosto.com", "ktronix.com", "alkomprar.com", "homecenter.com.co", "falabella.com.co", "flamingo.com.co",
        "lacuracao.com.co", "pepeganga.com", "tiendasd1.com", "makro.com.co",
    ]},
    # Falabella / Homecenter (API propia)
    "falabella:browse": f"https://www.falabella.com.co/s/browse/v1/search/co?q={qe}&page=1",
    "falabella:html": f"https://www.falabella.com.co/falabella-co/search?Ntt={qe}",
    "homecenter:html": f"https://www.homecenter.com.co/homecenter-co/search?Ntt={qe}",
    # Alkosto / Ktronix / Alkomprar (página de búsqueda; se buscan claves de Algolia)
    "alkosto:html": f"https://www.alkosto.com/search?text={qe}",
    "ktronix:html": f"https://www.ktronix.com/search?text={qe}",
    # Mercado Libre
    "mercadolibre:api": f"https://api.mercadolibre.com/sites/MCO/search?q={qe}&limit=5",
    "mercadolibre:html": f"https://listado.mercadolibre.com.co/{qe.replace('%20', '-')}",
    # Amazon
    "amazon:com": f"https://www.amazon.com/s?k={qe}",
}

MARCAS = {
    "algolia_app": r"""(?i)algolia[^"']{0,40}["']([A-Z0-9]{10})["']""",
    "algolia_key": r"""(?i)(?:apiKey|searchKey|algoliaKey)["']?\s*[:=]\s*["']([a-f0-9]{32})["']""",
    "precio_html": r"(?i)(price|precio)[^<]{0,40}\$\s?[\d.]{4,}",
    "captcha": r"(?i)captcha|robot check|are you a human|verify you are human",
    "next_data": r"__NEXT_DATA__",
    "poly_price": r"andes-money-amount__fraction",
}


def probar(nombre, url):
    try:
        r = http.get(url, impersonate="chrome", timeout=25, verify=False,
                     headers={"Accept-Language": "es-CO,es;q=0.9"})
        txt = r.text or ""
        info = {"estado": r.status_code, "bytes": len(txt), "tipo": r.headers.get("content-type", "")[:40]}
        try:
            j = r.json()
            info["json"] = True
            if isinstance(j, list):
                info["resultados"] = len(j)
                if j and isinstance(j[0], dict):
                    info["ejemplo"] = (j[0].get("productName") or "")[:80]
            elif isinstance(j, dict):
                info["claves"] = list(j)[:12]
                if "results" in j:
                    info["resultados"] = len(j["results"])
                    if j["results"]:
                        info["ejemplo"] = str(j["results"][0].get("title", ""))[:80]
                if "data" in j and isinstance(j["data"], dict) and "results" in j["data"]:
                    info["resultados"] = len(j["data"]["results"])
                    if j["data"]["results"]:
                        info["ejemplo"] = str(j["data"]["results"][0].get("displayName", ""))[:80]
        except Exception:
            info["json"] = False
            for k, pat in MARCAS.items():
                m = re.search(pat, txt)
                if m:
                    info[k] = m.group(1) if m.groups() else True
            t = re.search(r"<title>(.*?)</title>", txt, re.S)
            info["titulo"] = (t.group(1).strip()[:80] if t else "")
        return info
    except Exception as e:
        return {"error": str(e)[:150]}


resultado = {"busqueda": Q, "pruebas": {}}
for nombre, url in PRUEBAS.items():
    resultado["pruebas"][nombre] = probar(nombre, url)
    print(nombre, resultado["pruebas"][nombre])
Path("data").mkdir(exist_ok=True)
Path("data/sondeo.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=1), encoding="utf-8")
