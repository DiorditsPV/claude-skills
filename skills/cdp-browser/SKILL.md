---
name: cdp-browser
description: Поднимает «чистый» Chrome с CDP-портом (navigator.webdriver=false) для скрейпинга и автоматизации сайтов, которые блокируют автоматизацию (детект WebDriver, заглушки/капчи). Использовать, когда нужно прочитать/обойти сайт с анти-бот-защитой, «поднять CDP-браузер», работать через MCP chrome-devtools на чистом профиле, или скрейпить каталог через Chrome DevTools Protocol. Драйв по умолчанию — прямой CDP (без рестарта Claude Code).
allowed-tools:
  - Bash
  - Read
---

Скилл гарантирует запущенный «чистый» Chrome на CDP-порту и даёт инструменты для работы с ним.
Подробный разбор почему так — `~/dev/docs/claude/guides/mcp-devtools-browser-setup.md`.

## Когда применять
Сайт пускает обычный браузер, но банит автоматизацию (Server error / «Отключите VPN» / капча),
либо нужно программно обойти страницы по характеристикам. Дефолтный `chrome-devtools` MCP стартует
Chrome с automation-флагами (`navigator.webdriver=true`) и палится — поэтому работаем с браузером,
поднятым вручную без этих флагов.

## Процедура

1. **Гарантировать браузер** (идемпотентно — если порт жив, повторно не запускает):
   Пути без кавычек (в них нет пробелов) — иначе `~` не раскроется:
   ```bash
   bash ~/.claude/skills/cdp-browser/scripts/ensure.sh                 # эфемерный профиль /tmp/chrome-cdp
   bash ~/.claude/skills/cdp-browser/scripts/ensure.sh --persist       # стабильный ~/.cache/chrome-cdp-profile (cookies сохраняются)
   bash ~/.claude/skills/cdp-browser/scripts/ensure.sh --persist "https://target.example/page/"   # сразу открыть URL
   ```
   Скрипт сам ждёт подъёма порта и печатает `/json/version`.

2. **Проверить чистоту** (должно быть `false`):
   ```bash
   node ~/.claude/skills/cdp-browser/scripts/cdp.mjs "https://target.example/page/" "navigator.webdriver"
   ```

3. **Драйвить страницу** одним из способов:
   - **Прямой CDP (по умолчанию, без рестарта сессии).** CLI для быстрой проверки:
     ```bash
     node ~/.claude/skills/cdp-browser/scripts/cdp.mjs "<url>" "document.title"
     ```
     Для обхода многих страниц — импортируй хелпер в свой скрипт (динамический import,
     т.к. `~` в пути не раскрывается — берём абсолютный через `$HOME`):
     ```js
     const { connect } = await import(`${process.env.HOME}/.claude/skills/cdp-browser/scripts/cdp.mjs`);
     const { ev, goto, close } = await connect(9222);
     await goto('<url>');                 // навигация + ожидание + автоскролл ленивого контента
     const title = await ev('document.title');
     close();
     ```
   - **MCP `chrome-devtools`** — только если сервер заранее настроен с `--browser-url=http://127.0.0.1:9222`
     **и** браузер был поднят до старта сессии. Иначе MCP поднимет свой automation-Chrome — не используй
     этот путь без предварительной настройки (см. гайд, §4).

## Практические заметки (при скрейпинге)
- **Инкрементальная запись** — сохраняй результат в файл после *каждой* страницы (таймаут не обнулит прогресс).
- **Ленивый контент** — `goto()` уже скроллит; если данные всё равно не подгрузились, увеличь `settleMs`.
- **Парсинг по DOM**, а не по `innerText`-границам (структурная строка label|value надёжнее).
- **`\b` и кириллица** — в JS-регексе `\b` не считает кириллицу словом; убирай `\b` в границах секций.
- **JSON-LD** — `<script type="application/ld+json">` часто содержит готовые поля (`Product` и т.п.).

## Ограничения
- Скилл **не может** перезапустить Claude Code или перечитать аргументы MCP-сервера — поэтому MCP-native
  путь требует ручной предварительной настройки, а дефолт здесь — прямой CDP.
- macOS-путь к Chrome зашит в `ensure.sh`; переопределяется через `CHROME_BIN`.

## Завершение
Служебный браузер можно оставить (следующий вызов переиспользует порт) или закрыть:
```bash
pkill -f "remote-debugging-port=9222"
```
