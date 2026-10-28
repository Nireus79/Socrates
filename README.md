# Socrates (proof of concept)

Status: proof of concept, not maintained as a product. Latest release on PyPI: `socrates-ai` 0.2.3 (MIT).

This is the earlier Python research prototype of Socratic questioning with several cooperating agents. It asks structured questions about a project (business context, constraints, requirements, priorities), keeps the answers as explicit context, flags conflicts between them, and tracks how mature that understanding is before it writes a specification.

The current products are [Moly](https://nireus79.github.io/Moly/) and [Socrates](https://github.com/Nireus79/Socrates-ai), listed at [nireus79.github.io](https://nireus79.github.io/). Sponsorship tiers or quotas mentioned in older files of this repository are not offered; everything is free.

## What is in the repository

| Folder | Content |
|---|---|
| `socratic_system/` | the Python library |
| `socrates-api/` | the FastAPI service |
| `socrates-cli/` | the command line |
| `socrates-frontend/` | the web interface |
| `deployment/`, `docker-compose.yml` | Docker files |
| `tests/` | tests |

The libraries it was built from are separate PyPI packages: [socratic-nexus](https://pypi.org/project/socratic-nexus/), [socratic-agents](https://pypi.org/project/socratic-agents/), [socratic-morality](https://pypi.org/project/socratic-morality/), [socratic-knowledge](https://pypi.org/project/socratic-knowledge/), [socratic-workflow](https://pypi.org/project/socratic-workflow/), [socratic-conflict](https://pypi.org/project/socratic-conflict/), [socratic-maturity](https://pypi.org/project/socratic-maturity/), [socratic-learning](https://pypi.org/project/socratic-learning/), [socratic-analyzer](https://pypi.org/project/socratic-analyzer/), [socratic-performance](https://pypi.org/project/socratic-performance/), [socratic-docs](https://pypi.org/project/socratic-docs/).

## Use it

```bash
pip install socrates-ai
```

Python 3.8 or newer (`pyproject.toml`). It calls a model provider you choose (Claude, OpenAI, Google or Ollama) with your own key. See [QUICKSTART.md](QUICKSTART.md).

## The earlier README

The original README, with its feature list and claims that were never measured, is kept as [docs/README_ORIGINAL.md](docs/README_ORIGINAL.md) for reference. Treat it as history.

## Development

Written by an independent programmer in Greece, working with AI coding assistants (Claude Code). I design the products, review the code and test it; the tests are in `tests/`.

Contact: Hermes_creative@proton.me
