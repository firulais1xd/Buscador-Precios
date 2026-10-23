"""Busca un producto en todas las tiendas y envía el resultado a Telegram.

Uso:  python -m src.buscar "audifonos jbl tune 520"
Variables: TELEGRAM_TOKEN, TELEGRAM_CHAT_ID (secretos)
"""
import json
import os
import re
import statistics
import sys
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

from . import fuentes

RAIZ = Path(__file__).resolve().parent.parent
VACIAS = {"de", "del", "para", "con", "el", "la", "los", "las", "y", "en", "un", "una", "por", "a"}
ACCESORIOS = {"funda", "forro", "estuche", "case", "protector", "vidrio", "templado", "repuesto", "repuestos",
              "almohadillas", "cable", "adaptador", "soporte", "sticker", "skin", "correa", "manual", "cargador"}


def normalizar(t: str) -> str:
    t = unicodedata.normalize("NFKD", str(t).lower())
    return "".join(c for c in t if not unicodedata.combining(c))


def palabras(t: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", normalizar(t))


def _coincide(q: str, w: str) -> bool:
    if w.startswith(q) or (len(w) >= 3 and q.startswith(w)):
        return True
    return len(q) >= 5 and len(w) >= 5 and q[:5] == w[:5]          # audifono / audifonos / audífonos


def relevancia(consulta: list[str], nombre: str) -> float:
    ws = palabras(nombre)
    if not consulta:
        return 0
    return sum(any(_coincide(q, w) for w in ws) for q in consulta) / len(consulta)


def filtrar(resultados, q):
    consulta = [w for w in palabras(q) if w not in VACIAS]
    pide_accesorio = any(w in ACCESORIOS for w in consulta)
    minimo = 1.0 if len(consulta) <= 2 else 0.75
    buenos = []
    for r in resultados:
        r["relevancia"] = relevancia(consulta, r["nombre"])
        if r["relevancia"] < minimo or r["precio"] <= 0:
            continue
        if not pide_accesorio and any(w in ACCESORIOS for w in palabras(r["nombre"])):
            continue
        buenos.append(r)
    # descarta precios absurdamente bajos frente al resto (casi siempre accesorios o repuestos)
    if len(buenos) >= 4:
        mediana = statistics.median(r["precio"] for r in buenos)
        buenos = [r for r in buenos if r["precio"] >= 0.25 * mediana]
    # quita duplicados (misma tienda, mismo nombre)
    vistos, unicos = set(), []
    for r in sorted(buenos, key=lambda r: r["precio"]):
        k = (r["tienda"], normalizar(r["nombre"]))
        if k not in vistos:
            vistos.add(k)
            unicos.append(r)
    return unicos


def buscar_todo(q: str):
    tareas = {f"vtex:{t}": (fuentes.vtex, t, q) for t in fuentes.VTEX}
    tareas |= {f"algolia:{t}": (fuentes.algolia, t, q) for t in fuentes.ALGOLIA}
    tareas |= {"Falabella": (fuentes.falabella, q), "Homecenter": (fuentes.homecenter, q)}
    estado, resultados = {}, []
    tasa = None
    try:
        tasa = fuentes.trm()
        tareas["Amazon"] = (fuentes.amazon, q, tasa)
    except Exception as e:
        estado["Amazon"] = f"sin TRM: {e}"[:120]
    with ThreadPoolExecutor(max_workers=12) as ex:
        futuros = {ex.submit(f, *args): nombre for nombre, (f, *args) in tareas.items()}
        for fut in as_completed(futuros):
            nombre = futuros[fut].split(":")[-1]
            try:
                res = fut.result()
                resultados += res
                estado[nombre] = len(res)
            except Exception as e:
                estado[nombre] = f"error: {e}"[:120]
    return resultados, estado, tasa


def pesos(x: float) -> str:
    return "$" + f"{x:,.0f}".replace(",", ".")


def esc(t: str) -> str:
    return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def mensaje(q, buenos, estado, segundos):
    tiendas_ok = [t for t, v in estado.items() if isinstance(v, int)]
    if not buenos:
        return (f"🔎 <b>{esc(q)}</b>\nNo encontré resultados que coincidan en {len(tiendas_ok)} tiendas.\n"
                "Prueba con menos palabras o con la marca y el modelo (ej. <i>jbl tune 520</i>).")
    lineas = [f"🔎 <b>{esc(q)}</b> — {len(buenos)} resultados en {len({r['tienda'] for r in buenos})} tiendas ({segundos:.0f} s)\n",
              "🏆 <b>Más baratos</b>"]
    for i, r in enumerate(buenos[:8], 1):
        desc = f" <s>{pesos(r['precio_antes'])}</s>" if r["precio_antes"] > r["precio"] * 1.02 else ""
        nota = f"\n     <i>{esc(r['nota'])}</i>" if r["nota"] else ""
        lineas.append(f"{i}. <b>{pesos(r['precio'])}</b>{desc} · {r['tienda']}\n     <a href=\"{r['url']}\">{esc(r['nombre'][:70])}</a>{nota}")
    mejor_por_tienda = {}
    for r in buenos:
        mejor_por_tienda.setdefault(r["tienda"], r)
    lineas.append("\n🏬 <b>Mejor precio por tienda</b>")
    for t, r in sorted(mejor_por_tienda.items(), key=lambda x: x[1]["precio"]):
        lineas.append(f"• {t}: <a href=\"{r['url']}\">{pesos(r['precio'])}</a>")
    fallas = [t for t, v in estado.items() if not isinstance(v, int)]
    if fallas:
        lineas.append(f"\n⚠️ No respondieron: {', '.join(fallas)}")
    lineas.append("\nℹ️ Revisa que sea exactamente el mismo modelo antes de comprar.")
    return "\n".join(lineas)


def enviar_telegram(texto: str, chat: str):
    token = os.getenv("TELEGRAM_TOKEN", "").strip()
    if not token or not chat:
        print("Sin TELEGRAM_TOKEN o chat: no se envía.\n" + texto)
        return
    r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage", timeout=20, data={
        "chat_id": chat, "text": texto[:4000], "parse_mode": "HTML", "disable_web_page_preview": "true"})
    print("Telegram:", r.status_code, r.text[:200] if not r.ok else "ok")


def main():
    q = " ".join(sys.argv[1:]).strip() or os.getenv("CONSULTA", "").strip()
    if not q:
        sys.exit("Falta el producto a buscar.")
    chat = os.getenv("CHAT_DESTINO", "").strip() or os.getenv("TELEGRAM_CHAT_ID", "").strip()
    permitido = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    if permitido and chat != permitido:
        sys.exit("Chat no autorizado.")
    inicio = time.time()
    resultados, estado, tasa = buscar_todo(q)
    buenos = filtrar(resultados, q)
    texto = mensaje(q, buenos, estado, time.time() - inicio)
    print(texto)
    enviar_telegram(texto, chat)
    (RAIZ / "data").mkdir(exist_ok=True)
    (RAIZ / "data" / "ultima_busqueda.json").write_text(json.dumps({
        "consulta": q, "trm": tasa, "estado_tiendas": estado, "total_crudo": len(resultados),
        "resultados": [{k: r[k] for k in ("tienda", "nombre", "precio", "precio_antes", "nota", "url", "relevancia")} for r in buenos[:40]],
        "muestra_algolia": fuentes.muestra_algolia,
    }, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
