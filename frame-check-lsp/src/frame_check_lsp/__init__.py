import ast
import contextlib

from lsprotocol import types
from pygls.cli import start_server
from pygls.lsp.server import LanguageServer

from frame_check_core import FrameChecker

server = LanguageServer("frame-check-lsp", "v0.1")
fc = FrameChecker()


@server.feature(types.TEXT_DOCUMENT_DID_CHANGE)
@server.feature(types.TEXT_DOCUMENT_DID_OPEN)
@server.feature(types.TEXT_DOCUMENT_DID_SAVE)
async def frame_diagnostics(
    ls: LanguageServer, params: types.DidOpenTextDocumentParams
):
    global fc
    text_doc = ls.workspace.get_text_document(params.text_document.uri)
    contents = text_doc.source
    ls_diagnostics = []

    with contextlib.suppress(SyntaxError):
        tree = ast.parse(contents)
        fc = fc.check(tree)
        for diagnostic in fc.diagnostics:
            ls_diagnostic = types.Diagnostic(
                range=types.Range(
                    start=types.Position(
                        diagnostic.location[0] - 1, diagnostic.location[1]
                    ),
                    end=types.Position(
                        diagnostic.location[0] - 1, 80
                    ),  # Assuming 80 chars as line length
                ),
                message=diagnostic.message,
                source="Frame Checker",
                severity=types.DiagnosticSeverity.Error,
            )

            ls_diagnostics.append(ls_diagnostic)

            if (
                diagnostic.hint is not None
                and diagnostic.definition_location is not None
            ):
                ls_diagnostics.append(
                    types.Diagnostic(
                        range=types.Range(
                            start=types.Position(
                                diagnostic.definition_location[0] - 1,
                                diagnostic.definition_location[1],
                            ),
                            end=types.Position(
                                diagnostic.definition_location[0] - 1, 80
                            ),  # Assuming 80 chars as line length
                        ),
                        message=diagnostic.hint,
                        source="Frame Checker",
                        severity=types.DiagnosticSeverity.Hint,
                    )
                )
        # Send diagnostics (moved outside the loop to always run, even with empty diagnostics)
        ls.text_document_publish_diagnostics(
            types.PublishDiagnosticsParams(uri=text_doc.uri, diagnostics=ls_diagnostics)
        )


def main():
    start_server(server)


if __name__ == "__main__":
    main()
