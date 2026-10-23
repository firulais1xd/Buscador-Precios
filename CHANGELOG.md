# Historial de cambios

La entrada más reciente va arriba. Cada entrada tiene:

- **Motivo:** por qué se hizo el cambio.
- **Cambios:** qué se modificó y en qué archivos.
- **Cómo verificar:** qué debería notarse.

---

## v0.0.1 — 2026-10-23

**Motivo:** antes de construir el buscador, comprobar qué tiendas en línea responden a búsquedas automáticas desde GitHub Actions.

**Cambios:**
- `src/sondeo.py`: consulta un producto de prueba en unas 25 formas de búsqueda: VTEX (Éxito, Olímpica, Carulla, Jumbo, Metro, Panamericana, Alkosto, Ktronix, Alkomprar, Homecenter, Falabella y otras), la API y la página de Falabella, la página de búsqueda de Alkosto y Ktronix (donde se buscan claves de Algolia), Mercado Libre (API y página) y Amazon. Guarda el resultado en `data/sondeo.json`.
- `.github/workflows/sondeo.yml`: ejecución manual con el producto de prueba como parámetro.

**Cómo verificar:** *Actions › Sondeo de tiendas › Run workflow*, y luego revisar `data/sondeo.json`.
