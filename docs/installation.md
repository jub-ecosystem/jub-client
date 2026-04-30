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

JUB Client is under active development and is currently published on **[TestPyPI](https://test.pypi.org/project/jub/)** as a pre-release alpha. Install the latest version with:

```bash
pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ jub==0.1.0a2
```

The `--extra-index-url` flag ensures that standard dependencies (such as `pydantic`, `httpx`, and `option`) are resolved from the main PyPI index, while `jub` itself is pulled from TestPyPI.

!!! warning "Always pin the version"
    Use an explicit version pin (`==0.1.0a2`) to avoid accidentally installing a broken pre-release. Check the [release history](https://test.pypi.org/project/jub/#history) for the latest available version.

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
