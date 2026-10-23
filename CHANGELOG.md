# Historial de cambios

La entrada más reciente va arriba. Cada entrada tiene:

- **Motivo:** por qué se hizo el cambio.
- **Cambios:** qué se modificó y en qué archivos.
- **Cómo verificar:** qué debería notarse.

---

## v0.1.0 — 2026-10-23

**Motivo:** con los tres sondeos se confirmaron 11 tiendas consultables. Se construye el buscador.

**Cambios:**
- `src/fuentes.py`: lectores por tienda.
  - VTEX: Éxito, Olímpica, Carulla, Jumbo y Panamericana.
  - Falabella y Homecenter: datos `__NEXT_DATA__` de la página, con precio normal, precio tachado y precio con tarjeta CMR.
  - Algolia: Ktronix, Alkosto y Alkomprar. La clave pública se lee de su página en cada búsqueda, para no romperse si la cambian.
  - Amazon: precio en dólares convertido a pesos con la TRM del día (datos.gov.co, con open.er-api.com de respaldo). No incluye envío ni impuestos.
  - Metro se omite porque repite el catálogo de Jumbo.
- `src/buscar.py`: consulta todas las tiendas en paralelo. Filtra por relevancia (palabras de la búsqueda en el nombre, tolerando plurales y sufijos de modelo como "520BT"), quita accesorios no pedidos, precios absurdos (menos del 25 % de la mediana) y duplicados. Arma el mensaje de Telegram con los 8 más baratos y el mejor precio por tienda, y guarda `data/ultima_busqueda.json` para diagnóstico.
- `.github/workflows/buscar.yml`: se activa por `repository_dispatch` (desde el bot) o a mano. Solo responde al chat autorizado (`TELEGRAM_CHAT_ID`).
- `tests/test_buscar.py`: pruebas de relevancia, filtros y lectura de precios.
- Mercado Libre queda pendiente: su API pide autorización (403) y su página exige verificación de cuenta.

**Cómo verificar:** *Actions › Buscar producto › Run workflow* con un producto. El resultado llega a Telegram y queda en `data/ultima_busqueda.json`.

---

## v0.0.3 — 2026-10-23

**Motivo:** el segundo sondeo confirmó que Falabella entrega 56 resultados con precio normal y precio con tarjeta CMR. También mostró que Ktronix y Alkosto usan Algolia (app `QX5IPS1B1Q`, índices `ktronixIndexAlgoliaPRD` y `alkostoIndexAlgoliaPRD`), pero su clave pública de búsqueda no está en el HTML. Mercado Libre redirige a una "verificación de cuenta" y su API responde 403. Amazon y Homecenter necesitan otro análisis.

**Cambios:**
- `src/sondeo3.py`: busca la clave pública de Algolia en los scripts de Ktronix, cuenta los marcadores de la página de Amazon (resultados, precios, captcha) y resume la estructura de búsqueda de Homecenter.
- `.github/workflows/sondeo.yml`: también ejecuta el tercer sondeo.

**Cómo verificar:** aparecen `data/fragmentos/algolia.json`, `amazon2.txt` y `homecenter2.json`.

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
