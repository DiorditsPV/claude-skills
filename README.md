# diordits-skills

Личные Claude-скиллы (нерабочие) как plugin-marketplace + пилот **skill-first**-подхода:
скилл = процесс с накапливающимися данными (по мотивам доклада Krestnikov
«Скиллы на базе git — новая память AI-агентов», https://youtu.be/a-NIeMB-Hj8).

## Скиллы

| Скилл | Что делает | Data-skill |
|---|---|---|
| [youtube-breakdown](skills/youtube-breakdown/SKILL.md) | Разбор YouTube-роликов по субтитрам; накапливает разборы и отвечает по ним | да |
| [cdp-browser](skills/cdp-browser/SKILL.md) | «Чистый» Chrome с CDP-портом для сайтов с анти-бот-защитой | нет |
| [skill-new](skills/skill-new/SKILL.md) | Создание нового скилла по канону (компактный SKILL.md, сильный description) | нет |
| [skill-audit](skills/skill-audit/SKILL.md) | Аудит существующего скилла на best practices | нет |

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
