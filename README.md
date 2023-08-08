# Attack Defense COMPFEST Platform

Uses [poetry](https://python-poetry.org/) for dependency management. This is required during development.

## Running:

- Install with `pip install .` (Use `poetry install` for development)
- Copy `.env.example` to `.env` and fill in
- `flask run`

## Structure

Inside `and_platform`, there are a few folders and files, each folder are the modules (think of it like Django app) except `static`.

```
|
|--- core (Shared code between modules)
|
|--- and_platform (Website backend for AnD)
|    |
|    |------- models (Database models)
|    |------- routes (App routes)
|    |------- app.py (App definition)
|    |------- extensions.py (Flask extensions)
|
|--- checker (Checker code)
|    |------- main.py (Entrypoint)
```
