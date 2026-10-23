// Prueba local del Worker con fetch simulado:  node worker/prueba.mjs
import assert from "node:assert";
import { manejar } from "./src/index.js";

const llamadas = [];
globalThis.fetch = async (url, opts) => {
  llamadas.push({ url, body: opts?.body && JSON.parse(opts.body) });
  return new Response(null, { status: url.includes("api.github.com") ? 204 : 200 });
};
const env = { TELEGRAM_TOKEN: "T", TELEGRAM_CHAT_ID: "123", GH_DISPATCH_TOKEN: "G", WEBHOOK_SECRET: "S", GITHUB_REPO: "u/r" };
const req = (texto, chat = 123, secreto = "S") => new Request("https://x", {
  method: "POST", headers: { "X-Telegram-Bot-Api-Secret-Token": secreto },
  body: JSON.stringify({ message: { chat: { id: chat }, text: texto } }),
});

assert.equal((await manejar(req("hola", 123, "malo"), env)).status, 403);           // secreto inválido

llamadas.length = 0; await manejar(req("/buscar  audifonos   jbl 520"), env);
assert.equal(llamadas[0].url, "https://api.github.com/repos/u/r/dispatches");
assert.deepEqual(llamadas[0].body.client_payload, { consulta: "audifonos jbl 520", chat: "123" });
assert.match(llamadas[1].body.text, /Buscando/);

llamadas.length = 0; await manejar(req("nevera samsung"), env);                     // texto sin comando
assert.equal(llamadas[0].body.client_payload.consulta, "nevera samsung");

llamadas.length = 0; await manejar(req("/start"), env);                            // ayuda, sin búsqueda
assert.equal(llamadas.length, 1); assert.match(llamadas[0].body.text, /Buscador de precios/);

llamadas.length = 0; await manejar(req("nevera", 999), env);                       // otro chat
assert.equal(llamadas.length, 1); assert.match(llamadas[0].body.text, /privado/);
console.log("Worker: todas las pruebas pasaron");
