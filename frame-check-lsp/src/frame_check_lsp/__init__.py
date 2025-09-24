import ast
import contextlib

from frame_check_core import FrameChecker
from lsprotocol import types
from pygls.cli import start_server
from pygls.lsp.server import LanguageServer

server = LanguageServer("frame-check-lsp", "v0.1")


@server.feature(types.TEXT_DOCUMENT_DID_CHANGE)
@server.feature(types.TEXT_DOCUMENT_DID_OPEN)
@server.feature(types.TEXT_DOCUMENT_DID_SAVE)
async def frame_diagnostics(
    ls: LanguageServer, params: types.DidOpenTextDocumentParams
):
    text_doc = ls.workspace.get_text_document(params.text_document.uri)
    contents = text_doc.source

    with contextlib.suppress(SyntaxError):
        tree = ast.parse(contents)
        fc = FrameChecker()
        fc.visit(tree)
        diagnostics = []
        for access in fc.column_accesses.values():
            if access.id not in access.frame.columns:
                error_message = f"TypeError: Column '{access.id}' not found in frame '{access.frame.id}' defined at {access.frame.lineno}"
                details = (
                    f"With data defined at {access.frame.data_arg.get('lineno').val}"
                )

                diagnostic = types.Diagnostic(
                    range=types.Range(
                        start=types.Position(access.lineno - 1, 0),
                        end=types.Position(
                            access.lineno - 1, 80
                        ),  # Assuming 80 chars as line length
                    ),
                    message=f"{error_message}\n{details}",
                    source="Frame Checker",
                    severity=types.DiagnosticSeverity.Error,
                )

                diagnostics.append(diagnostic)

                if data_defined_ln := access.frame.data_arg.get("lineno").val:
                    diagnostics.append(
                        types.Diagnostic(
                            range=types.Range(
                                start=types.Position(data_defined_ln - 1, 0),
                                end=types.Position(
                                    data_defined_ln - 1, 80
                                ),  # Assuming 80 chars as line length
                            ),
                            message="Data defined here",
                            source="Frame Checker",
                            severity=types.DiagnosticSeverity.Hint,
                        )
                    )
        # Send diagnostics (moved outside the loop to always run, even with empty diagnostics)
        ls.text_document_publish_diagnostics(
            types.PublishDiagnosticsParams(uri=text_doc.uri, diagnostics=diagnostics)
        )


def main():
    start_server(server)


if __name__ == "__main__":
    main()
