# Installation

## Prerequisites

- Python 3.10+
- [Poetry](https://python-poetry.org/) — used to manage dependencies and the virtual environment.

Install Poetry with pipx (recommended):

```bash
pipx install poetry
```

!!! tip "Why pipx?"
    [pipx](https://pipx.pypa.io/stable/) installs CLI tools in isolated environments so they don't interfere with your project dependencies.

---
## Install JUB Client
Please note that Jub Client is under active development and may not be available on PyPI yet. To install the latest version, you can use the Test PyPI repository:

```bash
pip install -i https://test.pypi.org/simple/ jub
```

⚠️ Always try to use the latest version available on https://test.pypi.org/project/jub/ to ensure you have the latest features and bug fixes.

---

## Clone the repository

```bash
git clone https://github.com/jub-ecosystem/jub-client
cd jub-client
```

---

## Install dependencies

```bash
poetry install
```

Activate the virtual environment:

```bash
poetry self add poetry-plugin-shell
poetry shell
```

---

## Configure environment variables

Copy the example environment file and fill in your values:

```bash
cp .env.dev .env
```

| Variable | Default | Description |
|---|---|---|
| `JUB_API_URL` | `http://localhost:5000` | Base URL of the JUB API |
| `JUB_USERNAME` | — | Login username |
| `JUB_PASSWORD` | — | Login password |
| `JUB_CLIENT_LOG_PATH` | `/log` | Directory for JSON log files |
| `JUB_CLIENT_OBSERVATORY_ID_SIZE` | `12` | Length of generated observatory IDs |

---

## Run the tests

Make sure the API is running (see [Deployment](deployment.md)), then:

```bash
coverage run -m pytest tests/
coverage report
```
