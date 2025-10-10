alias t := test

test component:
    uv run --directory frame-check-{{ component }} pytest -v

alias d := docs

docs *cmd="":
    uv run mkdocs {{ cmd }} {{ if cmd == "serve" { "-a localhost:8811" } else { "" } }}

lsp-code:
    cd frame-check-extensions/vscode && ./install-dev.sh
