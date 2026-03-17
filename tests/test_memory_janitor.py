import json
import shutil
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from governance_tools.memory_janitor import MemoryJanitor

RUNTIME_ROOT = Path("tests") / "_runtime"
RUNTIME_ROOT.mkdir(exist_ok=True)


def make_memory_root() -> Path:
    root = RUNTIME_ROOT / f"memory_{uuid.uuid4().hex}"
    (root / "memory").mkdir(parents=True, exist_ok=False)
    return root / "memory"


def cleanup_runtime(memory_root: Path) -> None:
    shutil.rmtree(memory_root.parent, ignore_errors=True)


def write_lines(path: Path, count: int, extra: str = "") -> None:
    path.write_text("".join(f"line {i}\n" for i in range(count)) + extra, encoding="utf-8")


def test_check_hot_memory_status_thresholds() -> None:
    memory_root = make_memory_root()
    try:
        janitor = MemoryJanitor(memory_root)
        write_lines(janitor.active_task_file, MemoryJanitor.HOT_MEMORY_SOFT_LIMIT)
        assert janitor.check_hot_memory_status()[1] == "WARNING"
        write_lines(janitor.active_task_file, MemoryJanitor.HOT_MEMORY_HARD_LIMIT)
        assert janitor.check_hot_memory_status()[1] == "CRITICAL"
        write_lines(janitor.active_task_file, MemoryJanitor.HOT_MEMORY_CRITICAL)
        assert janitor.check_hot_memory_status()[1] == "EMERGENCY"
    finally:
        cleanup_runtime(memory_root)


def test_generate_warning_message_safe_empty() -> None:
    memory_root = make_memory_root()
    try:
        janitor = MemoryJanitor(memory_root)
        assert janitor.generate_warning_message(10, "SAFE") == ""
    finally:
        cleanup_runtime(memory_root)


def test_analyze_archivable_content_detects_adr_and_obsolete() -> None:
    memory_root = make_memory_root()
    try:
        janitor = MemoryJanitor(memory_root)
        janitor.active_task_file.write_text("~~old~~\nSee ADR-0001\n", encoding="utf-8")
        result = janitor.analyze_archivable_content()
        assert "ADR-0001" in result["archived_references"]
        assert any("old" in item for item in result["obsolete_decisions"])
    finally:
        cleanup_runtime(memory_root)


def test_find_and_cleanup_generated_artifacts() -> None:
    memory_root = make_memory_root()
    try:
        repo_root = memory_root.parent
        pycache = repo_root / "src" / "__pycache__"
        pycache.mkdir(parents=True)
        (pycache / "x.pyc").write_text("bin", encoding="utf-8")
        render_cache = repo_root / "output" / "render_cache"
        render_cache.mkdir(parents=True)
        (render_cache / "tile.cache").write_text("cache", encoding="utf-8")

        janitor = MemoryJanitor(memory_root)
        found_paths = list(janitor.find_generated_artifacts())
        assert any("__pycache__" in str(p) for p in found_paths)
        assert any("render_cache" in str(p) for p in found_paths)

        result = janitor.cleanup_generated_artifacts(dry_run=False)
        assert len(result.removed_paths) == 2
        assert not pycache.exists()
        assert not render_cache.exists()
    finally:
        cleanup_runtime(memory_root)


def test_execute_cleanup_writes_manifest_and_pointer() -> None:
    memory_root = make_memory_root()
    try:
        janitor = MemoryJanitor(memory_root)
        janitor.active_task_file.write_text("# Task\n\n## Next Steps\n- keep going\n", encoding="utf-8")
        result = janitor.execute_cleanup(dry_run=False)
        assert "cleanup completed" in result
        assert "ARCHIVED" in janitor.active_task_file.read_text(encoding="utf-8")
        manifest = json.loads((janitor.archive_dir / "manifest.json").read_text(encoding="utf-8"))
        assert len(manifest["archives"]) == 1
    finally:
        cleanup_runtime(memory_root)


def test_create_archive_plan_mentions_generated_artifacts() -> None:
    memory_root = make_memory_root()
    try:
        janitor = MemoryJanitor(memory_root)
        cache_dir = memory_root.parent / "output" / "audio_cache"
        cache_dir.mkdir(parents=True)
        report = janitor.create_archive_plan()
        assert "generated_artifacts" in report
        assert "audio_cache" in report
    finally:
        cleanup_runtime(memory_root)
