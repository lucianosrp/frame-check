import ast
import contextlib
import logging
import sys

from frame_check_core import FrameChecker
from frame_check_core._models import Diagnostic
from lsprotocol import types
from pygls.cli import start_server
from pygls.lsp.server import LanguageServer

server = LanguageServer("frame-check-lsp", "v0.1")
fc = FrameChecker()
logger = logging.getLogger(__name__)


async def _get_code_action(diagnostic: Diagnostic, uri: str) -> types.CodeAction:
    assert diagnostic.name_suggestion, "No name suggestion available"
    logger.info(
        f"Generating code action for diagnostic {diagnostic.column_name} => {diagnostic.name_suggestion}"
    )
    range_ = types.Range(
        start=types.Position(line=diagnostic.location[0] + 1, character=0),
        end=types.Position(
            line=diagnostic.location[0] + 1,
            character=len(diagnostic.column_name) - 1,
        ),
    )
    text_edit = types.TextEdit(range=range_, new_text=diagnostic.name_suggestion)

    return types.CodeAction(
        title=f"Rename to {diagnostic.name_suggestion}",
        kind=types.CodeActionKind.QuickFix,
        edit=types.WorkspaceEdit(changes={uri: [text_edit]}),
    )


# Somehow this doesn't work (?)
# FIXME
@server.feature(
    types.TEXT_DOCUMENT_CODE_ACTION,
    types.CodeActionOptions(code_action_kinds=[types.CodeActionKind.QuickFix]),
)
async def code_actions(params: types.CodeActionParams):
    items: list[types.CodeAction] = []
    for diagnostic in fc.diagnostics:
        if diagnostic.name_suggestion is not None:
            items.append(await _get_code_action(diagnostic, params.text_document.uri))


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

    logger.info("Processing diagnostics for URI: %s", params.text_document.uri)

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
                        diagnostic.location[0] - 1,
                        diagnostic.location[1] + diagnostic.underline_length,
                    ),
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
                # Hint at DataFrame creation site
                creation_hint_msg = "\n".join(diagnostic.hint)
                ls_diagnostics.append(
                    types.Diagnostic(
                        range=types.Range(
                            start=types.Position(
                                diagnostic.definition_location[0] - 1, 0
                            ),
                            end=types.Position(
                                diagnostic.definition_location[0] - 1, 80
                            ),
                        ),
                        message=creation_hint_msg,
                        source="Frame Checker",
                        severity=types.DiagnosticSeverity.Hint,
                    )
                )

                # Optional hint at data definition site
                if (
                    diagnostic.data_source_location is not None
                    and len(diagnostic.hint) > 1
                ):
                    data_hint_msg = "Data defined here with columns:\n" + "\n".join(
                        diagnostic.hint[1:]
                    )
                    ls_diagnostics.append(
                        types.Diagnostic(
                            range=types.Range(
                                start=types.Position(
                                    diagnostic.data_source_location[0] - 1, 0
                                ),
                                end=types.Position(
                                    diagnostic.data_source_location[0] - 1, 80
                                ),
                            ),
                            message=data_hint_msg,
                            source="Frame Checker",
                            severity=types.DiagnosticSeverity.Hint,
                        )
                    )
                elif diagnostic.data_source_location is not None:
                    # Fallback if no separate columns list
                    data_hint_msg = "\n".join(diagnostic.hint)
                    ls_diagnostics.append(
                        types.Diagnostic(
                            range=types.Range(
                                start=types.Position(
                                    diagnostic.data_source_location[0] - 1, 0
                                ),
                                end=types.Position(
                                    diagnostic.data_source_location[0] - 1, 80
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

        logger.info(
            "Published %d diagnostics for URI: %s",
            len(ls_diagnostics),
            params.text_document.uri,
        )


def main():
    logger.info("Starting frame-check-lsp server")
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
