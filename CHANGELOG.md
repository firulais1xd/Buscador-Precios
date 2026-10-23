# Historial de cambios

La entrada más reciente va arriba. Cada entrada tiene:

- **Motivo:** por qué se hizo el cambio.
- **Cambios:** qué se modificó y en qué archivos.
- **Cómo verificar:** qué debería notarse.

---

## v0.0.2 — 2026-10-23

**Motivo:** el primer sondeo mostró que responden Éxito, Olímpica, Carulla, Jumbo, Metro y Panamericana (VTEX), además de Falabella, Homecenter, Ktronix y Amazon. Alkosto tardó demasiado, y Mercado Libre bloqueó su API (403) y devolvió una página extraña. Hace falta ver cómo vienen los datos en cada página.

**Cambios:**
- `src/sondeo2.py`: guarda en `data/fragmentos/` partes de cada página: la configuración de Algolia de Ktronix y Alkosto, la estructura de datos de Falabella y Homecenter (`__NEXT_DATA__`), el primer resultado de Amazon y las respuestas de Mercado Libre.
- `.github/workflows/sondeo.yml`: también ejecuta el segundo sondeo.

**Cómo verificar:** después de *Run workflow*, aparece la carpeta `data/fragmentos/`.

---

## v0.0.1 — 2026-10-23

**Motivo:** antes de construir el buscador, comprobar qué tiendas en línea responden a búsquedas automáticas desde GitHub Actions.

**Cambios:**
- `src/sondeo.py`: consulta un producto de prueba en unas 25 formas de búsqueda: VTEX (Éxito, Olímpica, Carulla, Jumbo, Metro, Panamericana, Alkosto, Ktronix, Alkomprar, Homecenter, Falabella y otras), la API y la página de Falabella, la página de búsqueda de Alkosto y Ktronix (donde se buscan claves de Algolia), Mercado Libre (API y página) y Amazon. Guarda el resultado en `data/sondeo.json`.
- `.github/workflows/sondeo.yml`: ejecución manual con el producto de prueba como parámetro.

**Cómo verificar:** *Actions › Sondeo de tiendas › Run workflow*, y luego revisar `data/sondeo.json`.
