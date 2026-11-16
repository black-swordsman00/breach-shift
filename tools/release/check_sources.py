"""Audit public files, local documentation links and runtime module reachability."""
import ast
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[2]


def runtime_modules(root):
    modules = {}
    for path in (root / "breach_shift").rglob("*.py"):
        parts = path.relative_to(root).with_suffix("").parts
        name = ".".join(parts[:-1] if parts[-1]=="__init__" else parts)
        modules[name] = path
    reachable = set()
    pending = ["breach_shift.app","breach_shift.__main__"]
    network = {"socket","requests","urllib","http","webbrowser","ftplib","smtplib","subprocess"}
    while pending:
        name = pending.pop()
        if name in reachable:
            continue
        if name not in modules:
            raise ValueError("Missing runtime import: " + name)
        reachable.add(name)
        path = modules[name]
        tree = ast.parse(path.read_text(encoding="utf-8-sig"))
        for node in ast.walk(tree):
            imports = ([item.name for item in node.names] if isinstance(node,ast.Import)
                       else [node.module] if isinstance(node,ast.ImportFrom) and node.module else [])
            for imported in imports:
                if imported.split(".")[0] in network:
                    raise ValueError("Unexpected runtime network/process import: " + name)
                if imported.startswith("breach_shift."):
                    pending.append(imported)
    orphaned = sorted(name for name,path in modules.items()
                      if name not in reachable and path.name!="__init__.py")
    if orphaned:
        raise ValueError("Unreachable runtime modules: " + ", ".join(orphaned))
    return len(modules)


def main():
    listed = subprocess.check_output(["git","ls-files","-z","--cached","--others","--exclude-standard"],cwd=ROOT)
    home = Path.home()
    private = [str(ROOT).encode(),ROOT.as_posix().encode(),str(home).encode(),home.as_posix().encode()]
    # Generic CI account names overlap legitimate game terms such as Runner.
    if len(home.name)>=8 and home.name.lower() not in {"runner","codespace","vscode","ubuntu","defaultuser"}:
        private.append(home.name.encode())
    absolute_private = re.compile(rb"[a-z]:[\\/](?:users|desktop|downloads|temp)[\\/]",re.I)
    count = 0
    for name in sorted(set(listed.decode().split("\0"))):
        path = ROOT / name
        if not name or not path.is_file():
            continue
        raw = path.read_bytes()
        if absolute_private.search(raw) or any(token.lower() in raw.lower() for token in private if len(token)>4):
            raise ValueError("Private local identifier or absolute path in: " + name)
        if path.stat().st_size > 20*1024*1024:
            raise ValueError("Unexpected oversized public file: " + name)
        if name.startswith("breach_shift/") and path.suffix.lower() in {".glb",".blend",".bam",".pz",".env",".obj",".gltf"}:
            raise ValueError("Retired 3D asset in runtime package: " + name)
        if path.suffix==".md":
            for destination in re.findall(r"!?\[[^\]]*\]\(([^)]+)\)",raw.decode("utf-8-sig")):
                destination = destination.strip().strip("<>")
                if urlsplit(destination).scheme or destination.startswith("#"):
                    continue
                linked = (path.parent/unquote(destination.split("#")[0])).resolve()
                if not linked.is_relative_to(ROOT) or not linked.exists():
                    raise ValueError("Broken local documentation link in: " + name + " -> " + destination)
        count += 1
    modules = runtime_modules(ROOT)
    print(f"Source audit passed: {count} public files, {modules} runtime modules; no orphan modules, private paths or runtime network/process imports.")


if __name__=="__main__":
    main()
