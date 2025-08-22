use ruff_python_ast::{Alias, Stmt};
use ruff_python_parser::parse_module;
use std::{fs::File, io::Read};

#[derive(Default, Debug)]
struct Context<'a> {
    library: &'a str,
    import: Option<&'a Alias>,
    assignements: Vec<&'a Stmt>,
}

impl<'a> Context<'a> {
    fn new(library: &'a str) -> Self {
        Context {
            library,
            import: None,
            assignements: Vec::new(),
        }
    }

    fn get_import_as_name(&self) -> Option<String> {
        self.import
            .and_then(|alias| alias.asname.as_ref().map(|name| name.id().to_string()))
    }

    fn try_set_import(&mut self, import: &'a Stmt) {
        self.import = import
            .as_import_stmt()
            .and_then(|s| s.names.iter().find(|i| i.name.id() == self.library));
    }
}

fn main() {
    let mut ctx = Context::new("polars");

    let mut buf = String::new();
    File::open("test.py")
        .expect("Failed to open file")
        .read_to_string(&mut buf)
        .expect("Failed to read file");

    let module = parse_module(&buf).unwrap();
    for stmt in module.syntax().body.iter() {
        dbg!(&stmt);
        match stmt {
            Stmt::Import(_) => {
                ctx.try_set_import(stmt);
            }
            Stmt::Assign(_) => (),
            _ => (),
        }
    }

    dbg!(ctx.get_import_as_name());
}
