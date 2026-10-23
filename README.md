# 🔎 Buscador de Precios

Le escribes a tu bot de Telegram lo que quieres comprar y en **1 minuto aprox.** te responde con los precios ordenados de menor a mayor en **11 tiendas**:

Éxito · Olímpica · Carulla · Jumbo · Panamericana · Falabella · Homecenter · Alkosto · Ktronix · Alkomprar · Amazon

```
tú:   audifonos jbl tune 520
bot:  🔎 Buscando audifonos jbl tune 520 en 11 tiendas…
bot:  🏆 Más baratos
      1. $99.900 · Panamericana — Audífonos JBL Tune 520C
      2. $119.900 · Olímpica — JBL Tune 520C …
      🏬 Mejor precio por tienda …
```

## Cómo funciona

1. **Telegram → Cloudflare Worker** (`worker/`): recibe tu mensaje, responde al instante "Buscando…" y le pide a GitHub que haga la búsqueda. Solo atiende tu chat.
2. **GitHub Actions** (`src/`): busca en todas las tiendas en paralelo, filtra los resultados que no corresponden (otros modelos, accesorios, precios absurdos) y te envía el resultado.

Las tiendas bloquean las consultas que llegan directo desde Cloudflare; desde GitHub sí responden. Por eso la búsqueda se hace allá.

## Configuración (una sola vez)

Secretos en *Settings › Secrets and variables › Actions* de este repo:

| Secreto | De dónde sale |
|---|---|
| `TELEGRAM_TOKEN` | El mismo de tus otros repos (@BotFather) |
| `TELEGRAM_CHAT_ID` | El mismo de tus otros repos |
| `CLOUDFLARE_ACCOUNT_ID` | Cloudflare › Workers & Pages › columna derecha "Account ID" |
| `CLOUDFLARE_API_TOKEN` | Cloudflare › My Profile › API Tokens › Create Token › plantilla **Edit Cloudflare Workers** |
| `GH_DISPATCH_TOKEN` | GitHub › Settings › Developer settings › Fine-grained tokens. Solo el repo Buscador-Precios, permiso **Contents: Read and write** |

Después: *Actions › Desplegar bot › Run workflow*. Publica el Worker y conecta el bot.

También se puede buscar sin el bot: *Actions › Buscar producto › Run workflow*.

## Limitaciones

- **Amazon:** precio en dólares convertido con la TRM del día. **No incluye envío ni impuestos de importación**, que pueden sumar 20–40 %.
- **Mercado Libre** no está incluido: su API exige autorización y su página pide verificación de cuenta.
- Revisa siempre que sea exactamente el mismo modelo antes de comprar.
- `GH_DISPATCH_TOKEN` vence según la fecha que elijas al crearlo. Cuando venza, el bot avisará que no pudo iniciar la búsqueda.

Historial de cambios: [CHANGELOG.md](CHANGELOG.md)
