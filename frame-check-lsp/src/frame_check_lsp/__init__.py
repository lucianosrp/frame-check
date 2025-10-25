import ast
import contextlib
import sys

from frame_check_core import FrameChecker
from lsprotocol import types
from pygls.cli import start_server
from pygls.lsp.server import LanguageServer

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
    ls_diagnostics: list[types.Diagnostic] = []

    with contextlib.suppress(SyntaxError):
        tree = ast.parse(contents)
        fc = fc.check(tree)
        for diagnostic in fc.diagnostics:
            ls_diagnostic = types.Diagnostic(
                range=types.Range(
                    start=types.Position(*diagnostic.region.start.as_lsp_position()),
                    end=types.Position(*diagnostic.region.end.as_lsp_position()),
                ),
                message=diagnostic.message,
                source="Frame Checker",
                severity=types.DiagnosticSeverity.Error,
            )

            ls_diagnostics.append(ls_diagnostic)

            if diagnostic.hint is not None and diagnostic.definition_region is not None:
                # Hint at DataFrame creation site
                creation_hint_msg = "\n".join(diagnostic.hint)
                ls_diagnostics.append(
                    types.Diagnostic(
                        range=types.Range(
                            start=types.Position(
                                *diagnostic.definition_region.start.as_lsp_position()
                            ),
                            end=types.Position(
                                *diagnostic.definition_region.end.as_lsp_position()
                            ),
                        ),
                        message=creation_hint_msg,
                        source="Frame Checker",
                        severity=types.DiagnosticSeverity.Hint,
                    )
                )

                # Optional hint at data definition site
                if diagnostic.data_src_region is not None and len(diagnostic.hint) > 1:
                    data_hint_msg = "Data defined here with columns:\n" + "\n".join(
                        diagnostic.hint[1:]
                    )
                    ls_diagnostics.append(
                        types.Diagnostic(
                            range=types.Range(
                                start=types.Position(
                                    *diagnostic.data_src_region.start.as_lsp_position()
                                ),
                                end=types.Position(
                                    *diagnostic.data_src_region.end.as_lsp_position()
                                ),
                            ),
                            message=data_hint_msg,
                            source="Frame Checker",
                            severity=types.DiagnosticSeverity.Hint,
                        )
                    )
                elif diagnostic.data_src_region is not None:
                    # Fallback if no separate columns list
                    data_hint_msg = "\n".join(diagnostic.hint)
                    ls_diagnostics.append(
                        types.Diagnostic(
                            range=types.Range(
                                start=types.Position(
                                    *diagnostic.data_src_region.start.as_lsp_position()
                                ),
                                end=types.Position(
                                    *diagnostic.data_src_region.end.as_lsp_position()
                                ),
                            ),
                            message=data_hint_msg,
                            source="Frame Checker",
                            severity=types.DiagnosticSeverity.Hint,
                        )
                    )
        # Send diagnostics (moved outside the loop to always run, even with empty diagnostics)
        ls.text_document_publish_diagnostics(
            types.PublishDiagnosticsParams(uri=text_doc.uri, diagnostics=ls_diagnostics)
        )


def main():
    # Remove --stdio argument if present, as pygls handles stdio by default
    args = [arg for arg in sys.argv[1:] if arg != "--stdio"]

    # Temporarily replace sys.argv to remove --stdio
    original_argv = sys.argv
    sys.argv = [sys.argv[0]] + args

    try:
        start_server(server)
    finally:
        # Restore original argv
        sys.argv = original_argv


if __name__ == "__main__":
    main()
