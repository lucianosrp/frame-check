alias t := test

test *args:
    uv run pytest {{ args }}

alias d := docs

docs *cmd="":
    uv run zensical {{ cmd }}

lsp-code:
    cd frame-check-extensions/vscode && ./install-dev.sh

alias m := mypy

mypy *args:
    uv run mypy . --check-untyped-defs {{ args }}
