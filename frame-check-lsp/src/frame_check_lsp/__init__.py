import re

from lsprotocol import types
from pygls.cli import start_server
from pygls.lsp.server import LanguageServer

ADDITION = re.compile(r"^\s*(\d+)\s*\+\s*(\d+)\s*=(?=\s*$)")
server = LanguageServer("code-action-server", "v0.1")


@server.feature(
    types.TEXT_DOCUMENT_CODE_ACTION,
    types.CodeActionOptions(code_action_kinds=[types.CodeActionKind.QuickFix]),
)
def code_actions(params: types.CodeActionParams):
    items = []
    document_uri = params.text_document.uri
    document = server.workspace.get_text_document(document_uri)

    start_line = params.range.start.line
    end_line = params.range.end.line

    lines = document.lines[start_line : end_line + 1]
    for idx, line in enumerate(lines):
        match = ADDITION.match(line)
        if match is not None:
            range_ = types.Range(
                start=types.Position(line=start_line + idx, character=0),
                end=types.Position(line=start_line + idx, character=len(line) - 1),
            )

            left = int(match.group(1))
            right = int(match.group(2))
            answer = left + right

            text_edit = types.TextEdit(
                range=range_, new_text=f"{line.strip()} {answer}!"
            )

            action = types.CodeAction(
                title=f"Evaluate: '{match.group(0)}'",
                kind=types.CodeActionKind.QuickFix,
                edit=types.WorkspaceEdit(changes={document_uri: [text_edit]}),
            )
            items.append(action)

    return items


def main():
    start_server(server)


if __name__ == "__main__":
    main()
