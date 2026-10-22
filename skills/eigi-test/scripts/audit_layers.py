"""Mechanical LRN structure audit: layer imports, docstrings, logging, frontend boundaries.

Usage (from the repo root, any Python 3.12+, stdlib only)::

    python3 .claude/skills/lrn-test/scripts/audit_layers.py               # vs origin/development
    python3 .claude/skills/lrn-test/scripts/audit_layers.py --base <ref>  # vs another ref
    python3 .claude/skills/lrn-test/scripts/audit_layers.py --all         # whole codebase

Prints one finding per line as ``path:line RULE message`` and exits 1 when any finding is
reported. The rules encode the checkable half of the Eigi backend/frontend standards; the
judgement half (is this business rule in the right layer?) stays with the reviewing agent.
"""

import argparse
import ast
import re
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]

LAYERS = {
    "backend/core/apis/routes/": "route",
    "backend/core/apis/schemas/": "schema",
    "backend/core/controllers/": "controller",
    "backend/core/cruds/": "crud",
    "backend/core/services/": "service",
    "backend/core/models/": "model",
}

# Module prefixes each layer must not import. Exception types (names ending in "Error") from
# core.database are allowed everywhere: controllers translate WriteConflictError into a 409.
FORBIDDEN_IMPORTS = {
    "route": ("core.cruds", "core.database"),
    "schema": ("core.cruds", "core.controllers", "core.services", "core.database", "fastapi"),
    "controller": ("core.apis.routes", "core.database"),
    "crud": ("core.controllers", "core.apis", "fastapi"),
    "service": ("core.controllers", "core.apis.routes"),
    "model": ("core.cruds", "core.controllers", "core.services", "core.apis", "fastapi"),
}
SERVICE_FORBIDDEN_FASTAPI = {"Request", "Depends", "APIRouter", "Security"}

ROUTE_METHODS = {"get", "post", "put", "patch", "delete"}
SENSITIVE = re.compile(r"token|password|secret|otp|api_key|authorization|cookie|answer_key", re.I)
SENSITIVE_OK = re.compile(
    r"token_id|tokens_used|input_tokens|output_tokens|session_version|_count|len\(", re.I
)
DOCSTRING_ROOTS = ("backend/core/", "backend/commons/", "backend/scripts/", "backend/main.py")


def changed_files(base: str) -> list[str]:
    """List added or modified files since the merge base with ``base``, plus untracked files.
    Deleted files are excluded because there is nothing left to audit.

    Args:
        base: Git ref to diff against.

    Raises:
        subprocess.CalledProcessError: If git cannot resolve the ref.

    Returns:
        Repo-relative paths.
    """

    def git(*args: str) -> str:
        """Run git in the repo root and return stdout.
        Raise when git exits non-zero.

        Args:
            args: Git arguments.

        Returns:
            Captured stdout.
        """
        return subprocess.run(
            ["git", *args], cwd=ROOT, check=True, capture_output=True, text=True
        ).stdout

    merge_base = git("merge-base", "HEAD", base).strip()
    tracked = git("diff", "--name-only", "--diff-filter=ACMR", merge_base).split()
    untracked = git("ls-files", "--others", "--exclude-standard").split()
    return sorted(set(tracked + untracked))


def all_files() -> list[str]:
    """List every backend and frontend source file the audit understands.
    Skip virtualenvs, caches, and dependency folders.

    Returns:
        Repo-relative paths.
    """
    found = [*ROOT.glob("backend/**/*.py"), *ROOT.glob("frontend/src/**/*.ts*")]
    skip = (".venv", "__pycache__", "node_modules", ".next")
    return sorted(
        str(p.relative_to(ROOT)) for p in found if not any(part in skip for part in p.parts)
    )


def layer_of(path: str) -> str | None:
    """Map a backend path to its architectural layer.
    Return None for files outside the layered core.

    Args:
        path: Repo-relative path.

    Returns:
        The layer name or None.
    """
    return next((layer for prefix, layer in LAYERS.items() if path.startswith(prefix)), None)


def string_parts(node: ast.AST) -> str:
    """Concatenate the literal text inside a string or f-string node.
    Interpolated expressions contribute nothing.

    Args:
        node: AST node.

    Returns:
        Literal text, or an empty string for non-string nodes.
    """
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        return "".join(string_parts(v) for v in node.values)
    return ""


def own_nodes(func: ast.AST) -> Iterator[ast.AST]:
    """Walk a function body without descending into nested functions or classes.
    Nested definitions are audited on their own.

    Args:
        func: Function node.

    Returns:
        Iterator over the function's own AST nodes.
    """
    stack = list(ast.iter_child_nodes(func))
    while stack:
        node = stack.pop()
        yield node
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            stack.extend(ast.iter_child_nodes(node))


def log_calls(func: ast.AST, level: str | None = None) -> list[ast.Call]:
    """Collect ``logging.<level>(...)`` calls made directly by a function.
    The repo binds its logger helper to the name ``logging``.

    Args:
        func: Function node.
        level: Restrict to one level such as "error"; None matches any level.

    Returns:
        Matching call nodes.
    """
    calls = []
    for node in own_nodes(func):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id in {"logging", "logger", "log"}
            and (level is None or node.func.attr == level)
        ):
            calls.append(node)
    return calls


def is_route_handler(func: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Tell whether a function is registered with ``@<router>.<method>(...)``.
    Only HTTP verb decorators count.

    Args:
        func: Function node.

    Returns:
        True for route handlers.
    """
    for dec in func.decorator_list:
        target = dec.func if isinstance(dec, ast.Call) else dec
        if isinstance(target, ast.Attribute) and target.attr in ROUTE_METHODS:
            return True
    return False


def audit_docstring(path: str, func: ast.FunctionDef | ast.AsyncFunctionDef) -> Iterator[str]:
    """Check one function against the two-line docstring and Args/Raises/Returns rules.
    Sections are required only when the function has parameters, raises, or returns a value.

    Args:
        path: Repo-relative path for the report.
        func: Function node.

    Returns:
        Iterator of finding lines.
    """
    where = f"{path}:{func.lineno}"
    doc = ast.get_docstring(func)
    if not doc:
        yield f"{where} DOC001 {func.name}: missing docstring"
        return
    lines = [line.strip() for line in doc.splitlines() if line.strip()]
    if len(lines) < 2 or lines[1].endswith(":"):
        yield f"{where} DOC002 {func.name}: docstring needs a two-line purpose/behavior summary"
    params = [
        a.arg
        for a in [*func.args.posonlyargs, *func.args.args, *func.args.kwonlyargs]
        if a.arg not in {"self", "cls"}
    ]
    if params and "Args:" not in doc:
        yield f"{where} DOC003 {func.name}: has parameters but no Args section"
    nodes = list(own_nodes(func))
    if any(isinstance(n, ast.Raise) for n in nodes) and "Raises:" not in doc:
        yield f"{where} DOC004 {func.name}: raises but has no Raises section"
    returns_value = any(
        isinstance(n, ast.Return)
        and n.value is not None
        and not (isinstance(n.value, ast.Constant) and n.value.value is None)
        for n in nodes
    )
    if returns_value and "Returns:" not in doc and "Yields:" not in doc:
        yield f"{where} DOC005 {func.name}: returns a value but has no Returns section"


def audit_logging(
    path: str, layer: str | None, func: ast.FunctionDef | ast.AsyncFunctionDef, in_class: bool
) -> Iterator[str]:
    """Check entry/error log conventions and sensitive interpolation for one function.
    Route handlers need a "Calling" entry log and a catch-all except; public controller,
    CRUD and service class methods need an "Executing" entry log (pure module-level helpers do not).

    Args:
        path: Repo-relative path for the report.
        layer: The file's layer, or None outside the layered core.
        func: Function node.
        in_class: Whether the function is a method.

    Returns:
        Iterator of finding lines.
    """
    where = f"{path}:{func.lineno}"
    calls = log_calls(func)
    texts = [string_parts(c.args[0]) for c in calls if c.args]
    if layer == "route" and is_route_handler(func):
        if not any(t.startswith("Calling ") for t in texts):
            yield f'{where} LOG001 {func.name}: no logging.info("Calling METHOD /path endpoint")'
        catches_unknown = any(
            isinstance(n, ast.Try)
            and any(
                h.type is None or (isinstance(h.type, ast.Name) and h.type.id == "Exception")
                for h in n.handlers
            )
            for n in own_nodes(func)
        )
        if not catches_unknown:
            yield f"{where} LOG002 {func.name}: no catch-all except that logs and returns 500"
    public = not func.name.startswith("_")
    needs_entry = layer in {"controller", "crud", "service"} and in_class and public
    if needs_entry and not any(t.startswith("Executing ") for t in texts):
        yield f'{where} LOG003 {func.name}: lacks logging.info("Executing Class.method") entry log'
    for call in calls:
        for arg in call.args:
            if not isinstance(arg, ast.JoinedStr):
                continue
            for value in arg.values:
                if isinstance(value, ast.FormattedValue):
                    expr = ast.unparse(value.value)
                    if SENSITIVE.search(expr) and not SENSITIVE_OK.search(expr):
                        yield f"{path}:{call.lineno} LOG005 logs `{expr}`; secret or answer key?"


def audit_python(path: str) -> Iterator[str]:
    """Audit one backend Python file for layer imports, docstrings, and logging.
    Tests are skipped: they follow their own fixture conventions.

    Args:
        path: Repo-relative path.

    Returns:
        Iterator of finding lines.
    """
    if path.startswith("backend/tests/") or "/.venv/" in path:
        return
    source = (ROOT / path).read_text()
    try:
        tree = ast.parse(source)
    except SyntaxError as error:
        yield f"{path}:{error.lineno} PARSE {error.msg}"
        return
    layer = layer_of(path)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            names = [a.name for a in node.names]
            for prefix in FORBIDDEN_IMPORTS.get(layer or "", ()):
                if node.module == prefix or node.module.startswith(prefix + "."):
                    if prefix == "core.database" and all(n.endswith("Error") for n in names):
                        continue
                    imported = ", ".join(names)
                    yield f"{path}:{node.lineno} LAYER {layer} imports {node.module} ({imported})"
            if layer == "service" and node.module == "fastapi":
                bad = SERVICE_FORBIDDEN_FASTAPI.intersection(names)
                if bad:
                    glue = ", ".join(sorted(bad))
                    yield f"{path}:{node.lineno} LAYER service imports HTTP glue ({glue})"
        elif isinstance(node, ast.Import) and layer:
            for alias in node.names:
                if alias.name == "logging":
                    yield f"{path}:{node.lineno} LOG004 stdlib logging; use core.logger"
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "print"
            and not path.startswith("backend/scripts/")
        ):
            yield f"{path}:{node.lineno} LOG004 print(); use the repo logger"
    check_docs = path.startswith(DOCSTRING_ROOTS)
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if check_docs:
                    yield from audit_docstring(path, child)
                yield from audit_logging(path, layer, child, isinstance(parent, ast.ClassDef))


FRONTEND_RULES = [
    (
        re.compile(r"\bfetch\("),
        "FE001 raw fetch(); call the backend through src/lib/api or a feature api.ts",
        lambda p: not p.startswith("frontend/src/lib/api/"),
    ),
    (re.compile(r"\bconsole\.log\("), "FE002 console.log left in source", lambda p: True),
    (
        re.compile(r"process\.env\.(?!NEXT_PUBLIC_|NODE_ENV)\w+"),
        "FE003 non-public env var read in client code",
        lambda p: True,
    ),
    (
        re.compile(r"lrn_access_token"),
        "FE004 token storage key used outside src/lib/api/token.ts",
        lambda p: p != "frontend/src/lib/api/token.ts",
    ),
]


def audit_frontend(path: str) -> Iterator[str]:
    """Audit one frontend source file for API-layer, logging, env, and token boundaries.
    Line-based regex checks; comments are not excluded, so confirm before reporting.

    Args:
        path: Repo-relative path.

    Returns:
        Iterator of finding lines.
    """
    for lineno, line in enumerate((ROOT / path).read_text().splitlines(), start=1):
        for pattern, message, applies in FRONTEND_RULES:
            if applies(path) and pattern.search(line):
                yield f"{path}:{lineno} {message}"


def main() -> int:
    """Parse arguments, audit the selected files, and print findings.
    Exit 1 when anything is reported so the audit can gate a run.

    Returns:
        Process exit code.
    """
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("--base", default="origin/development", help="ref to diff against")
    parser.add_argument("--all", action="store_true", help="audit the whole codebase")
    args = parser.parse_args()
    files = all_files() if args.all else changed_files(args.base)
    findings: list[str] = []
    for path in files:
        if not (ROOT / path).is_file():
            continue
        if path.startswith("backend/") and path.endswith(".py"):
            findings.extend(audit_python(path))
        elif path.startswith("frontend/src/") and path.endswith((".ts", ".tsx")):
            findings.extend(audit_frontend(path))
    for line in findings:
        print(line)
    scope = "all files" if args.all else f"{len(files)} changed files vs {args.base}"
    print(f"\n{len(findings)} finding(s) across {scope}", file=sys.stderr)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
