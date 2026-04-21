from dataclasses import dataclass, field
from typing import Any, List, Optional


# Base node — line is always optional (keyword-only style via default)
class Node:
    line: int = 0


@dataclass
class Program:
    decls: List[Any] = field(default_factory=list)
    line: int = 0


@dataclass
class ScopeDecl:
    """GLOBAL or MODULE variable declaration at file level"""
    scope: str  # 'global' or 'module'
    type_: str
    name: str
    dims: List[Any] = field(default_factory=list)
    default: Any = None
    line: int = 0


@dataclass
class FunctionDecl:
    return_type: Optional[str]  # None = void
    name: str
    params: List[Any] = field(default_factory=list)
    var_decls: List[Any] = field(default_factory=list)
    body: List[Any] = field(default_factory=list)
    line: int = 0


@dataclass
class Param:
    type_: str
    name: str
    dims: List[Any] = field(default_factory=list)
    line: int = 0


@dataclass
class VarDecl:
    type_: str
    name: str
    dims: List[Any] = field(default_factory=list)
    default: Any = None
    line: int = 0


@dataclass
class AssignStmt:
    target: Any  # LValue
    value: Any
    line: int = 0


@dataclass
class LValue:
    name: str
    indices: List[Any] = field(default_factory=list)
    line: int = 0


@dataclass
class FuncCallStmt:
    name: str
    args: List[Any] = field(default_factory=list)
    line: int = 0


@dataclass
class IfStmt:
    condition: Any
    then_body: List[Any] = field(default_factory=list)
    elseif_clauses: List[Any] = field(default_factory=list)  # list of (cond, body)
    else_body: List[Any] = field(default_factory=list)
    line: int = 0


@dataclass
class WhileStmt:
    condition: Any
    body: List[Any] = field(default_factory=list)
    line: int = 0


@dataclass
class ForStmt:
    var: str
    start: Any
    end: Any
    step: Any = None
    body: List[Any] = field(default_factory=list)
    line: int = 0


@dataclass
class SelectStmt:
    expr: Any
    cases: List[Any] = field(default_factory=list)
    else_body: List[Any] = field(default_factory=list)
    line: int = 0


@dataclass
class CaseClause:
    values: List[Any]
    body: List[Any] = field(default_factory=list)
    line: int = 0


@dataclass
class ReturnStmt:
    value: Any = None
    line: int = 0


@dataclass
class NopStmt:
    line: int = 0


@dataclass
class BinaryOp:
    op: str
    left: Any
    right: Any
    line: int = 0


@dataclass
class UnaryOp:
    op: str
    operand: Any
    line: int = 0


@dataclass
class FuncCallExpr:
    name: str
    args: List[Any] = field(default_factory=list)
    line: int = 0


@dataclass
class VarRef:
    name: str
    indices: List[Any] = field(default_factory=list)
    line: int = 0


@dataclass
class IntLit:
    value: int
    line: int = 0


@dataclass
class RealLit:
    value: float
    line: int = 0


@dataclass
class StringLit:
    value: str
    line: int = 0
