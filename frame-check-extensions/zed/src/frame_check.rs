use zed_extension_api::{
    Command, Extension, LanguageServerId, Result, Worktree, register_extension,
};

struct Frame;

impl Extension for Frame {
    fn language_server_command(
        &mut self,
        language_server_id: &LanguageServerId,
        worktree: &Worktree,
    ) -> Result<Command> {
        let _ = language_server_id;
        Ok(Command {
            command: "frame-check-lsp".to_string(),
            args: vec![],
            env: worktree.shell_env(),
        })
    }

    fn new() -> Self
    where
        Self: Sized,
    {
        Self {}
    }
}

register_extension!(Frame);
