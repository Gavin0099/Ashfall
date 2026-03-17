import shutil
import uuid
from pathlib import Path
from dataclasses import dataclass
from governance_tools.memory_janitor import MemoryJanitor, CleanupResult

RUNTIME_ROOT = Path("tests") / "_runtime"
RUNTIME_ROOT.mkdir(exist_ok=True, parents=True)

root = RUNTIME_ROOT / f"diag_memory_{uuid.uuid4().hex}"
memory_root = root / "memory"
memory_root.mkdir(parents=True)

repo_root = memory_root.parent
pycache = repo_root / "src" / "__pycache__"
pycache.mkdir(parents=True)
(pycache / "x.pyc").write_text("bin", encoding="utf-8")

janitor = MemoryJanitor(memory_root)
found = janitor.find_generated_artifacts()
print(f"Found: {[str(p) for p in found]}")

result = janitor.cleanup_generated_artifacts(dry_run=False)
print(f"Removed: {result.removed_paths}")
print(f"Errors: {result.errors}")

shutil.rmtree(root, ignore_errors=True)
