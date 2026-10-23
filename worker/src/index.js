/**
 * Puente entre el bot de Telegram y GitHub Actions.
 * Telegram envía cada mensaje aquí (webhook). Si viene del chat autorizado, responde al instante
 * "Buscando…" y lanza el workflow "Buscar producto" en GitHub, que envía el resultado al chat.
 *
 * Secretos (los sube el workflow desplegar-bot.yml): TELEGRAM_TOKEN, TELEGRAM_CHAT_ID,
 * GH_DISPATCH_TOKEN, WEBHOOK_SECRET.   Variable: GITHUB_REPO.
 */
const AYUDA =
  "🛒 <b>Buscador de precios</b>\n\n" +
  "Escríbeme lo que quieres comprar y lo busco en Éxito, Olímpica, Carulla, Jumbo, Panamericana, " +
  "Falabella, Homecenter, Alkosto, Ktronix, Alkomprar y Amazon.\n\n" +
  "Ejemplos:\n• <code>audifonos jbl tune 520</code>\n• <code>/buscar nevera samsung 236 litros</code>\n• <code>freidora de aire oster</code>\n\n" +
  "Consejo: incluye marca y modelo para resultados más precisos.";

const esc = (t) => String(t).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

async function enviar(env, chat, texto) {
  await fetch(`https://api.telegram.org/bot${env.TELEGRAM_TOKEN}/sendMessage`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ chat_id: chat, text: texto, parse_mode: "HTML", disable_web_page_preview: true }),
  });
}

export async function manejar(request, env) {
  if (request.method !== "POST") return new Response("Buscador de precios: activo");
  if (request.headers.get("X-Telegram-Bot-Api-Secret-Token") !== env.WEBHOOK_SECRET) {
    return new Response("no autorizado", { status: 403 });
  }
  const update = await request.json();
  const msg = update.message || update.edited_message;
  if (!msg || typeof msg.text !== "string") return new Response("ok");

  const chat = String(msg.chat.id);
  if (chat !== String(env.TELEGRAM_CHAT_ID)) {
    await enviar(env, chat, "Este bot es privado.");
    return new Response("ok");
  }

  let texto = msg.text.trim();
  if (/^\/(start|ayuda|help)\b/i.test(texto)) {
    await enviar(env, chat, AYUDA);
    return new Response("ok");
  }
  if (/^\/buscar\b/i.test(texto)) texto = texto.replace(/^\/buscar(@\w+)?/i, "").trim();
  else if (texto.startsWith("/")) {
    await enviar(env, chat, AYUDA);
    return new Response("ok");
  }
  if (texto.length < 2) {
    await enviar(env, chat, "Dime qué buscar, por ejemplo: <code>/buscar audifonos jbl tune 520</code>");
    return new Response("ok");
  }
  texto = texto.replace(/\s+/g, " ").slice(0, 80);

  const r = await fetch(`https://api.github.com/repos/${env.GITHUB_REPO}/dispatches`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${env.GH_DISPATCH_TOKEN}`,
      Accept: "application/vnd.github+json",
      "User-Agent": "buscador-precios-bot",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ event_type: "buscar", client_payload: { consulta: texto, chat } }),
  });
  if (r.status === 204) {
    await enviar(env, chat, `🔎 Buscando <b>${esc(texto)}</b> en 11 tiendas… te respondo en 1 minuto aprox.`);
  } else {
    await enviar(env, chat, `⚠️ No pude iniciar la búsqueda (GitHub respondió ${r.status}). Revisa el token GH_DISPATCH_TOKEN.`);
  }
  return new Response("ok");
}

export default { fetch: manejar };
