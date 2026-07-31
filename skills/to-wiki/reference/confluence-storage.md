# Storage-разметка Confluence: готовые куски

Сырая storage-разметка проходит через markdown-конвертер MCP насквозь — вставляй эти
блоки прямо в markdown-контент страницы, переписывать всю страницу в storage не нужно.

Внутри `rich-text-body` markdown **не** конвертируется: только XHTML (`<p>`, `<ul>`,
`<li>`, `<code>`, `<strong>`, `<em>`, `<br/>`).

## Плашки

`warning` — то, что требует решения или ломает работу. `note` — важное, но не срочное.
`info` — контекст. `tip` — совет. Разметка одинаковая, меняется только `ac:name`.

```xml
<ac:structured-macro ac:name="warning"><ac:parameter ac:name="title">Заголовок</ac:parameter><ac:rich-text-body><p>Текст абзаца.</p><ul><li>пункт</li><li>пункт</li></ul></ac:rich-text-body></ac:structured-macro>
```

## Сворачиваемый блок

```xml
<ac:structured-macro ac:name="expand"><ac:parameter ac:name="title">Что внутри</ac:parameter><ac:rich-text-body><p>Содержимое.</p></ac:rich-text-body></ac:structured-macro>
```

## Сэмпл данных: expand + code

Выровненную markdown-таблицу кладут в `code`-макрос внутри `expand`, чтобы она не
разъезжалась и не растягивала страницу.

```xml
<ac:structured-macro ac:name="expand"><ac:parameter ac:name="title">Сэмпл 15 строк из снапшота 2026-07-31</ac:parameter><ac:rich-text-body><ac:structured-macro ac:name="code"><ac:parameter ac:name="language">markdown</ac:parameter><ac:plain-text-body><![CDATA[
| col_a | col_b |
|-------|-------|
| 1     | текст |
]]></ac:plain-text-body></ac:structured-macro></ac:rich-text-body></ac:structured-macro>
```

Внутри CDATA последовательность `]]>` закрывает секцию досрочно и рвёт страницу —
экранируй её (в `scripts/wiki_api.mjs` это делает `cdata()`).

## Вложенный список

Markdown-конвертер схлопывает вложенные списки в верхний уровень. Если иерархия
«пункт → подпункты» обязана сохраниться, пиши этот фрагмент storage-разметкой.

```xml
<ul><li>верхний пункт<ul><li>подпункт</li><li>подпункт</li></ul></li><li>второй верхний</li></ul>
```

## Проверка, что макрос распознан

Перечитай опубликованную страницу с `convert_to_markdown: false`. Если сервер присвоил
`ac:macro-id` — макрос разобран:

```xml
<ac:structured-macro ac:macro-id="0363a2c0-…" ac:name="warning" ac:schema-version="1">
```

Если вместо этого в storage лежит экранированный текст с `&lt;ac:structured-macro` —
разметка не прошла, и её надо публиковать через REST в storage-формате.
