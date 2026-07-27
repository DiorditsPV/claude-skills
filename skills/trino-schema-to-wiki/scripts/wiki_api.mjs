// REST-хелпер confluence.example.internal через CDP-браузер с SSO (фолбэк, когда Confluence MCP
// лежит, и единственный путь для вложений). Браузер поднимает скилл cdp-browser:
//   bash ~/.claude/skills/cdp-browser/scripts/ensure.sh --persist "https://confluence.example.internal/"
// Если открыт только service worker — вкладку создаёт ensureTab().
//
// Использование в ad-hoc скрипте:
//   const w = await import(`${process.env.HOME}/.claude/skills/trino-schema-to-wiki/scripts/wiki_api.mjs`);
//   const { api, getPage, createPage, updatePage, uploadAttachment, close } = await w.open();
//   const p = await createPage({space: '~User.Name', title: 'T', storage: '<p>…</p>', parentId: 123});

import { readFileSync } from 'node:fs';

const CDP = `${process.env.HOME}/.claude/skills/cdp-browser/scripts/cdp.mjs`;

export async function open(port = 9222) {
  const { connect } = await import(CDP);
  let conn;
  try {
    conn = await connect(port, t => t.type === 'page' && /wiki\.x5\.ru/.test(t.url));
  } catch {
    await fetch(`http://127.0.0.1:${port}/json/new?https://confluence.example.internal/`, { method: 'PUT' });
    await new Promise(r => setTimeout(r, 3000));
    conn = await connect(port, t => t.type === 'page' && /wiki\.x5\.ru/.test(t.url));
  }
  const { ev, close } = conn;

  async function api(method, path, payload) {
    const res = await ev(`(async () => {
      const r = await fetch(${JSON.stringify('/rest/api' + path)}, {
        method: ${JSON.stringify(method)}, credentials: "include",
        headers: {"Content-Type": "application/json", "Accept": "application/json", "X-Atlassian-Token": "nocheck"},
        ${payload ? `body: ${JSON.stringify(JSON.stringify(payload))},` : ''}
      });
      return JSON.stringify({status: r.status, body: await r.text()});
    })()`);
    const { status, body } = JSON.parse(res);
    let json;
    try { json = JSON.parse(body); } catch { json = null; }
    return { status, json, body };
  }

  const getPage = (id) => api('GET', `/content/${id}?expand=body.storage,version,ancestors`);

  async function createPage({ space, title, storage, parentId }) {
    return api('POST', '/content', {
      type: 'page', title, space: { key: space },
      ...(parentId ? { ancestors: [{ id: Number(parentId) }] } : {}),
      body: { storage: { representation: 'storage', value: storage } },
    });
  }

  async function updatePage(id, mutate) {
    const cur = await getPage(id);
    if (cur.status !== 200) return cur;
    const body = mutate(cur.json.body.storage.value, cur.json);
    return api('PUT', `/content/${id}`, {
      id: String(id), type: 'page', title: cur.json.title,
      version: { number: cur.json.version.number + 1 },
      body: { storage: { representation: 'storage', value: body } },
    });
  }

  async function uploadAttachment(pageId, filePath, fileName, mime = 'application/octet-stream') {
    const b64 = readFileSync(filePath).toString('base64');
    const res = await ev(`(async () => {
      const bin = Uint8Array.from(atob(${JSON.stringify(b64)}), c => c.charCodeAt(0));
      const fd = new FormData();
      fd.append("file", new Blob([bin], {type: ${JSON.stringify(mime)}}), ${JSON.stringify(fileName)});
      fd.append("minorEdit", "true");
      const r = await fetch("/rest/api/content/" + ${JSON.stringify(String(pageId))} + "/child/attachment", {
        method: "POST", credentials: "include", headers: {"X-Atlassian-Token": "nocheck"}, body: fd
      });
      return JSON.stringify({status: r.status, body: (await r.text()).slice(0, 500)});
    })()`);
    return JSON.parse(res);
  }

  return { api, getPage, createPage, updatePage, uploadAttachment, close };
}

// Экранирование содержимого для CDATA code-макросов.
export const cdata = (s) => s.replace(/\]\]>/g, ']] >');
