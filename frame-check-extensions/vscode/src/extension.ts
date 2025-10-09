import * as vscode from "vscode";
import {
  LanguageClient,
  LanguageClientOptions,
  ServerOptions,
  TransportKind,
} from "vscode-languageclient/node";

let client: LanguageClient;

export function activate(context: vscode.ExtensionContext) {
  // Get configuration
  const config = vscode.workspace.getConfiguration("frameCheck");

  if (!config.get("enable", true)) {
    return;
  }

  // Server options - point to the frame-check-lsp executable
  const serverCommand = config.get("serverPath", "frame-check-lsp");

  const serverOptions: ServerOptions = {
    command: serverCommand,
    args: [],
    transport: TransportKind.stdio,
    options: {
      env: process.env,
    },
  };

  // Client options
  const clientOptions: LanguageClientOptions = {
    documentSelector: [{ scheme: "file", language: "python" }],
    synchronize: {
      fileEvents: vscode.workspace.createFileSystemWatcher("**/.py"),
    },
    outputChannelName: "Frame Check Language Server",
    traceOutputChannel:
      config.get("trace.server") !== "off"
        ? vscode.window.createOutputChannel("Frame Check Language Server Trace")
        : undefined,
  };

  // Create the language client
  client = new LanguageClient(
    "frameCheckLanguageServer",
    "Frame Check Language Server",
    serverOptions,
    clientOptions,
  );

  // Register restart command
  const restartCommand = vscode.commands.registerCommand(
    "frameCheck.restart",
    async () => {
      if (client) {
        await client.stop();
        await client.start();
        vscode.window.showInformationMessage(
          "Frame Check Language Server restarted",
        );
      }
    },
  );

  context.subscriptions.push(restartCommand);

  // Start the client
  client
    .start()
    .then(() => {
      vscode.window.showInformationMessage(
        "Frame Check Language Server started successfully",
      );
    })
    .catch((error) => {
      vscode.window.showErrorMessage(
        `Failed to start Frame Check Language Server: ${error.message}`,
      );
      console.error("Frame Check LSP Error:", error);
    });

  // Handle configuration changes
  const configChangeListener = vscode.workspace.onDidChangeConfiguration(
    async (event) => {
      if (event.affectsConfiguration("frameCheck")) {
        const newConfig = vscode.workspace.getConfiguration("frameCheck");

        if (!newConfig.get("enable", true)) {
          if (client) {
            await client.stop();
          }
          return;
        }

        // Restart client if server path changed
        if (
          event.affectsConfiguration("frameCheck.serverPath") ||
          event.affectsConfiguration("frameCheck.trace.server")
        ) {
          if (client) {
            await client.stop();
            // Recreate client with new configuration
            activate(context);
          }
        }
      }
    },
  );

  context.subscriptions.push(configChangeListener);
}

export function deactivate(): Thenable<void> | undefined {
  if (!client) {
    return undefined;
  }
  return client.stop();
}
