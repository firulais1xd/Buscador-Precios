"""Lectores de cada tienda. Cada función recibe el texto buscado y devuelve una lista de resultados:
{"tienda", "nombre", "precio", "precio_antes", "nota", "url"}   (precios en COP)
"""
import json
import re
from urllib.parse import quote

from curl_cffi import requests as http

TIEMPO = 40
CABECERAS = {"Accept-Language": "es-CO,es;q=0.9"}


def _get(url, **kw):
    return http.get(url, impersonate="chrome", timeout=TIEMPO, verify=False, headers=CABECERAS, **kw)


def _num(texto) -> float:
    """'$ 1.299.900' -> 1299900.0"""
    if isinstance(texto, (int, float)):
        return float(texto)
    dig = re.sub(r"[^\d]", "", str(texto))
    return float(dig) if dig else 0.0


# ─── VTEX: Éxito, Olímpica, Carulla, Jumbo, Panamericana ────────────────────────────────────────────
VTEX = {
    "Éxito": "https://www.exito.com",
    "Olímpica": "https://www.olimpica.com",
    "Carulla": "https://www.carulla.com",
    "Jumbo": "https://www.tiendasjumbo.co",
    "Panamericana": "https://www.panamericana.com.co",
}


def vtex(tienda: str, q: str) -> list[dict]:
    base = VTEX[tienda]
    r = _get(f"{base}/api/catalog_system/pub/products/search?ft={quote(q)}&_from=0&_to=29")
    out = []
    for p in r.json() or []:
        for item in p.get("items", [])[:1]:
            ofertas = [s.get("commertialOffer") or {} for s in item.get("sellers", [])]
            ofertas = [o for o in ofertas if (o.get("Price") or 0) > 0 and (o.get("AvailableQuantity", 0) > 0 or o.get("IsAvailable"))]
            if not ofertas:
                continue
            o = min(ofertas, key=lambda o: o["Price"])
            link = p.get("link") or ""
            out.append({"tienda": tienda, "nombre": p.get("productName", ""), "precio": float(o["Price"]),
                        "precio_antes": float(o.get("ListPrice") or o["Price"]), "nota": "",
                        "url": link if link.startswith("http") else base + link})
    return out


# ─── Falabella y Homecenter (datos dentro de la página, __NEXT_DATA__) ──────────────────────────────
def _falabella_resultados(html: str):
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
    if not m:
        return []
    pp = json.loads(m.group(1)).get("props", {}).get("pageProps", {})
    return pp.get("results") or (pp.get("searchProps", {}).get("searchData", {}) or {}).get("results") or []


def _falabella_generico(tienda: str, url: str) -> list[dict]:
    out = []
    for p in _falabella_resultados(_get(url).text):
        precios = p.get("prices") or []
        normales = [_num(x["price"][0]) for x in precios if x.get("price") and not x.get("crossed") and x.get("type") != "cmrPrice"]
        tachados = [_num(x["price"][0]) for x in precios if x.get("price") and x.get("crossed")]
        cmr = [_num(x["price"][0]) for x in precios if x.get("price") and x.get("type") == "cmrPrice"]
        if not normales and not cmr:
            continue
        precio = min(normales) if normales else min(cmr)
        nota = f"con tarjeta CMR: ${min(cmr):,.0f}".replace(",", ".") if cmr and normales and min(cmr) < precio else ""
        out.append({"tienda": tienda, "nombre": f"{p.get('brand', '')} {p.get('displayName', '')}".strip(),
                    "precio": precio, "precio_antes": max(tachados) if tachados else precio, "nota": nota,
                    "url": p.get("url", "")})
    return out


def falabella(q: str) -> list[dict]:
    return _falabella_generico("Falabella", f"https://www.falabella.com.co/falabella-co/search?Ntt={quote(q)}")


def homecenter(q: str) -> list[dict]:
    return _falabella_generico("Homecenter", f"https://www.homecenter.com.co/homecenter-co/search?Ntt={quote(q)}")


# ─── Algolia: Ktronix, Alkosto, Alkomprar (la clave pública se lee de su página en cada búsqueda) ───
ALGOLIA = {
    "Ktronix": "https://www.ktronix.com",
    "Alkosto": "https://www.alkosto.com",
    "Alkomprar": "https://www.alkomprar.com",
}
muestra_algolia = {}   # un resultado de ejemplo por tienda, para depurar nombres de campos


def _campo(hit: dict, *patrones):
    for pat in patrones:
        for k, v in hit.items():
            if re.fullmatch(pat, k) and v not in (None, "", []):
                return v
    return None


def algolia(tienda: str, q: str) -> list[dict]:
    base = ALGOLIA[tienda]
    html = _get(f"{base}/search?text={quote(q)}").text
    app = re.search(r"applicationId\s*:\s*['\"]([A-Z0-9]+)['\"]", html)
    key = re.search(r"apiKey\s*:\s*['\"]([A-Za-z0-9=+/]{20,})['\"]", html)
    idx = re.search(r"indexName\s*:\s*['\"]([\w-]+)['\"]", html)
    if not (app and key and idx):
        raise RuntimeError("no se encontró la configuración de Algolia en la página")
    app, key, idx = app.group(1), key.group(1), idx.group(1)
    r = http.post(f"https://{app.lower()}-dsn.algolia.net/1/indexes/{idx}/query", impersonate="chrome", timeout=TIEMPO,
                  headers={"X-Algolia-Application-Id": app, "X-Algolia-API-Key": key, "Content-Type": "application/json",
                           "Origin": base, "Referer": base + "/"},
                  data=json.dumps({"params": f"query={quote(q)}&hitsPerPage=30"}))
    hits = r.json().get("hits", [])
    if hits:
        muestra_algolia[tienda] = {k: (v if not isinstance(v, (list, dict)) else str(v)[:80]) for k, v in list(hits[0].items())[:60]}
    out = []
    for h in hits:
        nombre = _campo(h, r"name_text_es", r"name.*_es.*", r"name.*", r"title.*")
        precio = _campo(h, r"pricevalue_cop_double", r"lowestprice_double", r"price.*cop.*double", r"price.*double")
        antes = _campo(h, r"baseprice_cop_string", r"baseprice.*", r"listprice.*")
        url = _campo(h, r"url_es_string", r"url.*")
        stock = _campo(h, r"instock.*", r"stock.*boolean")
        if not nombre or not precio or stock is False:
            continue
        precio = _num(precio)
        out.append({"tienda": tienda, "nombre": str(nombre), "precio": precio,
                    "precio_antes": _num(antes) if antes else precio, "nota": "",
                    "url": (base + url) if url and str(url).startswith("/") else (url or base)})
    return out


# ─── Amazon (precios en dólares, se convierten a pesos con la TRM) ──────────────────────────────────
def trm() -> float:
    """Tasa representativa del mercado (COP por USD)."""
    try:
        d = _get("https://www.datos.gov.co/resource/32sa-8pi3.json?$limit=1&$order=vigenciadesde%20DESC").json()
        return float(d[0]["valor"])
    except Exception:
        d = _get("https://open.er-api.com/v6/latest/USD").json()
        return float(d["rates"]["COP"])


def amazon(q: str, tasa: float) -> list[dict]:
    html = _get(f"https://www.amazon.com/s?k={quote(q)}").text
    if "validateCaptcha" in html or "captcha" in html.lower()[:20000]:
        raise RuntimeError("Amazon pidió captcha")
    out = []
    for bloque in html.split('data-component-type="s-search-result"')[1:31]:
        asin = re.search(r'data-asin="(\w{10})"', bloque) or re.search(r"/dp/(\w{10})", bloque)
        titulo = (re.search(r'<h2[^>]*aria-label="([^"]+)"', bloque)
                  or re.search(r'<span class="a-size-[\w-]+ a-color-base a-text-normal"[^>]*>([^<]+)</span>', bloque)
                  or re.search(r'<h2[^>]*>.*?<span[^>]*>([^<]+)</span>', bloque, re.S))
        precio = re.search(r'<span class="a-offscreen">\s*(?:US)?\$\s?([\d,]+\.?\d*)', bloque)
        if not (asin and titulo and precio):
            continue
        usd = float(precio.group(1).replace(",", ""))
        nombre = re.sub(r"\s+", " ", titulo.group(1)).replace("&amp;", "&").replace("&quot;", '"').strip()
        nombre = re.sub(r"^Anuncio patrocinado\s*[–-]\s*", "", nombre)
        out.append({"tienda": "Amazon", "nombre": nombre, "precio": round(usd * tasa), "precio_antes": round(usd * tasa),
                    "nota": f"US${usd:,.2f} · sin envío ni impuestos", "url": f"https://www.amazon.com/dp/{asin.group(1)}"})
    return out
