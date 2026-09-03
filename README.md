# diordits-skills

Личные Claude-скиллы (нерабочие) как plugin-marketplace + пилот **skill-first**-подхода:
скилл = процесс с накапливающимися данными (по мотивам доклада Krestnikov
«Скиллы на базе git — новая память AI-агентов», https://youtu.be/a-NIeMB-Hj8).

## Скиллы

| Скилл | Что делает | Data-skill |
|---|---|---|
| [youtube-breakdown](skills/youtube-breakdown/SKILL.md) | Разбор YouTube-роликов по субтитрам; накапливает разборы и отвечает по ним | да |
| [cdp-browser](skills/cdp-browser/SKILL.md) | «Чистый» Chrome с CDP-портом для сайтов с анти-бот-защитой ([разбор устройства](skills/cdp-browser/reference/chrome-cdp-setup.md)) | нет |
| [skill-new](skills/skill-new/SKILL.md) | Создание нового скилла по канону (компактный SKILL.md, сильный description) | нет |
| [present-html](skills/present-html/SKILL.md) | Презентация/разбор как пара md + самодостаточный html | нет |
| [curator](skills/curator/SKILL.md) | Обслуживание библиотеки скиллов: статистика использования, архив, консолидация | да |
| [to-wiki](skills/to-wiki/SKILL.md) | Документирование существующего в Confluence: фактура из первоисточника, разделы по предмету, публикация страницей ([storage-разметка](skills/to-wiki/reference/confluence-storage.md)) | нет |
| [grill-me](skills/grill-me/SKILL.md) | Жёсткое интервью по плану/дизайну до общего понимания (адаптация промпта mattpokock) | нет |
| [product-lead](skills/product-lead/SKILL.md) | Ведёт личный продукт как продакт-лид: concept (Concept Brief от продуктовой модели), release (описание релизной версии: фичи под монетизацию, free/paid, DoD), v1 (аудит, гэп-лист, план, гейты, ручной прогон, тег) ([методология](skills/product-lead/reference/methodology.md), [шаблоны](skills/product-lead/templates/)) | нет |

## Агенты

| Агент | Что делает |
|---|---|
| [technical-writer](agents/technical-writer.md) | Пишет и редактирует понятную документацию: код, репозиторий, статья, гайд, справочник |

## Устройство: код публичный, данные приватные

- **`main`** — только код скиллов (`SKILL.md`, `scripts/`), директории `skills/*/data/` пустые (`.gitkeep`). Пушится в публичный `origin`.
- **`data`** — рабочая ветка: код + данные в `skills/*/data/`. Пушится **только** в приватный remote `private`.
- Поток изменений односторонний: код правится на `main`, затем `git merge main` в `data`. `data → main` не сливается никогда.
- Хуки в `.githooks/` защищают схему механически:
  - `pre-commit` — на `data` коммитятся только `skills/*/data/**`; на остальных ветках данные не коммитятся;
  - `pre-push` — ветка `data` в `origin` не уходит.

## Установка

Как plugin (только код, данные копятся локально):

```
/plugin marketplace add DiorditsPV/claude-skills
/plugin install diordits-skills@diordits-skills
```

Как личная рабочая копия (со своей веткой данных):

```bash
git clone git@github.com:DiorditsPV/claude-skills.git ~/dev/claude-skills
cd ~/dev/claude-skills
git config core.hooksPath .githooks         # обязательно: хуки не подтягиваются сами
git remote add private git@github.com:DiorditsPV/claude-skills-data.git
git fetch private && git checkout data
ln -s ~/dev/claude-skills/skills/youtube-breakdown ~/.claude/skills/youtube-breakdown
```

## Документы

- [Дизайн пилота skill-first](docs/specs/2026-07-07-skill-repo-pilot-design.md)
