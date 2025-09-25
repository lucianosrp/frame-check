import ast
from operator import getitem
from typing import Any, Literal, overload

SupportedNode = (
    ast.Call
    | list[ast.Name]
    | list[ast.keyword]
    | ast.Assign
    | str
    | ast.arg
    | ast.Name
    | ast.keyword
    | ast.Dict
    | list[ast.Constant]
    | ast.FunctionDef
    | ast.Attribute
    | ast.Subscript
    | ast.Constant
    | ast.Compare
    | list[ast.Name | ast.Dict]
    | int
)


class WrappedNode[T: SupportedNode | None]:
    """
    A generic wrapper class for AST nodes that provides safe attribute access.

    This class wraps AST nodes and provides type-safe access to their attributes
    through the get() method. If an attribute doesn't exist, it returns an empty
    WrappedNode instead of raising an AttributeError. This allows for method chaining.


    Type parameter:
        T: The type of the wrapped value


    Example
    ---

    >>> node = WrappedNode(ast.Call(ast.Name("print"), [ast.Constant(42)]))
    >>> node.get("func").get("id")
    WrappedNode("print")

    >>> node = WrappedNode(ast.Call(func=ast.Name(id="print", ctx=ast.Load()), args=[], keywords=[]))
    >>> node.get("nonexistent_attr").get("another_attr")
    WrappedNode(None)
    """

    def __init__(self, val: Any | None = None):
        """
        Initialize a WrappedNode with the given value.

        Args:
            value: The value to wrap. Defaults to None.
        """
        self.val: T | None = val

    def __repr__(self) -> str:
        """
        Return a string representation of the wrapped node.

        Returns:
            A string in the format WrappedNode(value)
        """
        return f"WrappedNode({repr(self.val)})"

    @overload
    def get(
        self, attr: Literal["args"]
    ) -> "WrappedNode[list[ast.Name | ast.Dict]]": ...

    @overload
    def get(self, attr: Literal["keywords"]) -> "WrappedNode[list[ast.keyword]]": ...

    @overload
    def get(
        self: "WrappedNode[ast.Call]", attr: Literal["value"]
    ) -> "WrappedNode[ast.Name]": ...

    @overload
    def get(
        self: "WrappedNode[ast.Assign]", attr: Literal["value"]
    ) -> "WrappedNode[SupportedNode]": ...

    @overload
    def get(self, attr: Literal["func"]) -> "WrappedNode[ast.Call]": ...

    @overload
    def get(self, attr: Literal["id"]) -> "WrappedNode[str]": ...

    @overload
    def get(self, attr: Literal["attr"]) -> "WrappedNode[str]": ...

    @overload
    def get(
        self: "WrappedNode[ast.arg]", attr: Literal["keys"]
    ) -> "WrappedNode[list[ast.Constant]]": ...

    @overload
    def get(
        self: "WrappedNode[ast.Dict | None]", attr: Literal["keys"]
    ) -> "WrappedNode[list[ast.Constant]]": ...

    @overload
    def get(
        self: "WrappedNode[ast.Subscript]", attr: Literal["value"]
    ) -> "WrappedNode[ast.Name | ast.Call]": ...

    @overload
    def get(
        self: "WrappedNode[ast.Subscript]", attr: Literal["slice"]
    ) -> "WrappedNode[ast.Constant | ast.Compare]": ...

    @overload
    def get(self: "WrappedNode", attr: Literal["lineno"]) -> "WrappedNode[int]": ...

    def get(
        self,
        attr: Literal[
            "value", "args", "keywords", "id", "func", "attr", "keys", "slice", "lineno"
        ],
    ) -> "WrappedNode":
        """
        Safely get an attribute from the wrapped value.

        If the attribute doesn't exist or the wrapped value is None,
        returns an empty WrappedNode instead of raising an AttributeError.

        Args:
            attr: The attribute name to access, must be one of "value", "args",
                  "keywords", or "id"

        Returns:
            A new WrappedNode containing the attribute value, or an empty WrappedNode
            if the attribute doesn't exist
        """
        return WrappedNode(getattr(self.val, attr, None))

    def __getitem__[V: ast.Dict | ast.Name](
        self: "WrappedNode[list[V]]", index: int
    ) -> "WrappedNode[V]":
        return WrappedNode(getitem(self.val or [None] * index, index))

    @property
    def targets(self):
        tar = getattr(self.val, "targets", None)
        return [WrappedNode(v) for v in tar] if tar else []
