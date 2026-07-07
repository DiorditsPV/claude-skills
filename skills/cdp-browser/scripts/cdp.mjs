#!/usr/bin/env node
// cdp.mjs — минимальный CDP-клиент поверх встроенного WebSocket (Node 20+/26).
// Подключается к уже запущенному Chrome на --remote-debugging-port.
//
// Как библиотека:
//   import { connect } from './cdp.mjs'
//   const { ev, send, close } = await connect(9222)
//   await send('Page.navigate', { url })
//   const title = await ev('document.title')
//   close()
//
// Как CLI:
//   node cdp.mjs <url> ["<js-expression>"] [--port N]
//   печатает результат вычисления выражения (по умолчанию document.title)

export async function connect(port = 9222, match = t => t.type === 'page') {
  const list = await (await fetch(`http://127.0.0.1:${port}/json`)).json();
  const page = list.find(match) || list.find(t => t.type === 'page');
  if (!page) throw new Error(`нет подходящей вкладки на :${port}`);
  const ws = new WebSocket(page.webSocketDebuggerUrl);
  let id = 0;
  const send = (method, params = {}) => new Promise((res, rej) => {
    const mid = ++id;
    const h = e => {
      const m = JSON.parse(e.data);
      if (m.id === mid) { ws.removeEventListener('message', h); m.error ? rej(new Error(JSON.stringify(m.error))) : res(m.result); }
    };
    ws.addEventListener('message', h);
    ws.send(JSON.stringify({ id: mid, method, params }));
  });
  await new Promise(r => ws.addEventListener('open', r));
  await send('Runtime.enable');
  await send('Page.enable');
  const ev = async (expr) => (await send('Runtime.evaluate', { expression: expr, returnByValue: true, awaitPromise: true })).result.value;
  // навигация с ожиданием загрузки и автоскроллом ленивого контента
  const goto = async (url, settleMs = 3000) => {
    await send('Page.navigate', { url });
    await new Promise(r => setTimeout(r, settleMs));
    await ev(`(async()=>{for(let y=0;y<document.body.scrollHeight;y+=1000){window.scrollTo(0,y);await new Promise(r=>setTimeout(r,60));}window.scrollTo(0,0);})()`);
  };
  return { ws, send, ev, goto, close: () => ws.close() };
}

// --- CLI ---
// сравнение через realpath: иначе запуск по симлинку (argv[1]) не совпадёт с реальным import.meta.url
import { realpathSync } from 'node:fs';
import { pathToFileURL } from 'node:url';
const invokedDirectly = process.argv[1] && pathToFileURL(realpathSync(process.argv[1])).href === import.meta.url;
if (invokedDirectly) {
  const args = process.argv.slice(2);
  let port = 9222, url = null, expr = 'document.title';
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--port') port = +args[++i];
    else if (args[i].startsWith('--port=')) port = +args[i].split('=')[1];
    else if (url === null) url = args[i];
    else expr = args[i];
  }
  const { ev, goto, close } = await connect(port);
  if (url) await goto(url);
  const out = await ev(expr);
  close();
  // дождаться фактического сброса stdout в pipe перед выходом (иначе вывод теряется)
  await new Promise(r => process.stdout.write(String(out) + '\n', r));
}
