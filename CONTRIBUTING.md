# Contributing

Issues and pull requests are more than welcome.

We recommand using [`uv`](https://docs.astral.sh/uv) as project manager for development.

See https://docs.astral.sh/uv/getting-started/installation/ for installation 

### dev install

```bash
git clone https://github.com/cogeotiff/rio-cogeo.git
cd rio-cogeo

uv sync
```

You can then run the tests with the following command:

```sh
uv run pytest --cov rio_cogeo --cov-report term-missing
```

### pre-commit

This repo is set to use `pre-commit` to run *isort*, *flake8*, *pydocstring*, *black* ("uncompromising Python code formatter") and mypy when committing new code.

```bash
uv run pre-commit install
```

### Docs

```bash
git clone https://github.com/cogeotiff/rio-cogeo.git
cd rio-cogeo

uv sync --group docs
```

Hot-reloading docs (from repository root):

uv run mkdocs serve -f docs/mkdocs.yml
```

To manually deploy docs (note you should never need to do this because Github
Actions deploys automatically for new commits.):

```bash
uv run mkdocs gh-deploy -f docs/mkdocs.yml
```
