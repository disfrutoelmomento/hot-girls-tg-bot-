"""Точка входа для локального запуска. На Railway используется тот же
app.api:app, но напрямую через uvicorn (см. Procfile) — этот файл просто
удобная обёртка для `python -m app.main` при локальной разработке."""

import os

import uvicorn


def main() -> None:
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.api:app", host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
