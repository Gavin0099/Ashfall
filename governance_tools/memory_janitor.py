#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class ArtifactCleanupResult:
    removed_paths: list[str]
    skipped_paths: list[str]


class MemoryJanitor:
    """Manage hot-memory pressure and generated runtime artifacts."""

    HOT_MEMORY_SOFT_LIMIT = 180
    HOT_MEMORY_HARD_LIMIT = 200
    HOT_MEMORY_CRITICAL = 250

    GENERATED_CACHE_DIRS = (
        Path("output/render_cache"),
        Path("output/audio_cache"),
        Path("output/cache"),
        Path("render_cache"),
    )

    def __init__(self, memory_root: Path):
        self.memory_root = Path(memory_root)
        self.repo_root = self.memory_root.parent
        self.active_task_file = self.memory_root / "01_active_task.md"
        self.archive_dir = self.memory_root / "archive"
        self.archive_dir.mkdir(parents=True, exist_ok=True)

    def check_hot_memory_status(self) -> tuple[int, str]:
        if not self.active_task_file.exists():
            return 0, "SAFE"

        line_count = len(self.active_task_file.read_text(encoding="utf-8").splitlines())
        if line_count >= self.HOT_MEMORY_CRITICAL:
            return line_count, "EMERGENCY"
        if line_count >= self.HOT_MEMORY_HARD_LIMIT:
            return line_count, "CRITICAL"
        if line_count >= self.HOT_MEMORY_SOFT_LIMIT:
            return line_count, "WARNING"
        return line_count, "SAFE"

    def generate_warning_message(self, line_count: int, status: str) -> str:
        if status == "WARNING":
            return f"警告：active_task 熱記憶接近上限（{line_count}/200 行），請準備清理。"
        if status == "CRITICAL":
            return (
                f"警告：active_task 已達 CRITICAL（{line_count}/200 行）。"
                " 建議執行 `python governance_tools/memory_janitor.py --plan`。"
            )
        if status == "EMERGENCY":
            return (
                f"停止：active_task 已達 EMERGENCY（{line_count}/200 行）。"
                " 必須先清理熱記憶後再繼續。"
            )
        return ""

    def analyze_archivable_content(self) -> dict[str, list[str]]:
        if not self.active_task_file.exists():
            return {"completed_tasks": [], "obsolete_decisions": [], "archived_references": []}

        content = self.active_task_file.read_text(encoding="utf-8")
        completed_tasks = re.findall(r"##\s+.*?\n(?:.*\n)*?- \[x\].*?(?=\n##|\Z)", content, re.DOTALL)
        obsolete_decisions = re.findall(r"~~.*?~~|\(Superseded.*?\)", content)
        archived_references = sorted(set(re.findall(r"ADR-\d{4}", content)))
        return {
            "completed_tasks": completed_tasks,
            "obsolete_decisions": obsolete_decisions,
            "archived_references": archived_references,
        }

    def find_generated_artifacts(self) -> list[Path]:
        candidates: list[Path] = []
        for path in self.repo_root.rglob("__pycache__"):
            if path.is_dir():
                candidates.append(path)
        for relative in self.GENERATED_CACHE_DIRS:
            path = self.repo_root / relative
            if path.exists():
                candidates.append(path)
        unique: list[Path] = []
        seen: set[str] = set()
        for path in candidates:
            key = str(path.resolve())
            if key not in seen:
                seen.add(key)
                unique.append(path)
        return unique

    def cleanup_generated_artifacts(self, dry_run: bool = True) -> ArtifactCleanupResult:
        removed: list[str] = []
        skipped: list[str] = []
        for path in self.find_generated_artifacts():
            if dry_run:
                skipped.append(str(path))
                continue
            try:
                shutil.rmtree(path)
                removed.append(str(path))
            except FileNotFoundError:
                continue
            except OSError:
                skipped.append(str(path))
        return ArtifactCleanupResult(removed_paths=removed, skipped_paths=skipped)

    def create_archive_plan(self) -> str:
        line_count, status = self.check_hot_memory_status()
        archivable = self.analyze_archivable_content()
        artifacts = self.find_generated_artifacts()
        lines = [
            "# Memory Janitor Plan",
            f"- status: {status}",
            f"- line_count: {line_count}",
            f"- completed_task_blocks: {len(archivable['completed_tasks'])}",
            f"- obsolete_decisions: {len(archivable['obsolete_decisions'])}",
            f"- adr_references: {len(archivable['archived_references'])}",
            f"- generated_artifacts: {len(artifacts)}",
        ]
        if artifacts:
            lines.append("- removable_artifacts:")
            lines.extend(f"  - {path}" for path in artifacts[:10])
        if status == "EMERGENCY":
            lines.append("- recommendation: stop_and_clean_now")
        elif status == "CRITICAL":
            lines.append("- recommendation: execute_cleanup")
        elif status == "WARNING":
            lines.append("- recommendation: schedule_cleanup")
        else:
            lines.append("- recommendation: no_memory_cleanup_needed")
        return "\n".join(lines)

    def _load_manifest(self) -> dict[str, Any]:
        manifest_path = self.archive_dir / "manifest.json"
        if not manifest_path.exists():
            return {"version": "1.0", "archives": []}
        try:
            return json.loads(manifest_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {"version": "1.0", "archives": []}

    def _save_manifest(self, manifest: dict[str, Any]) -> None:
        manifest_path = self.archive_dir / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    def execute_cleanup(self, dry_run: bool = True) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_file = self.archive_dir / f"active_task_{timestamp}.md"
        artifact_result = self.cleanup_generated_artifacts(dry_run=dry_run)

        if not self.active_task_file.exists():
            if dry_run:
                return (
                    "[dry-run] active_task 不存在；僅檢查生成物。\n"
                    f"  generated_artifacts={len(artifact_result.skipped_paths)}"
                )
            return (
                "active_task 不存在；未執行熱記憶封存。\n"
                f"  removed_generated_artifacts={len(artifact_result.removed_paths)}"
            )

        content = self.active_task_file.read_text(encoding="utf-8")
        original_lines = len(content.splitlines())

        if dry_run:
            return (
                "[dry-run] 將封存 active_task 並清理生成物。\n"
                f"  archive_target={archive_file}\n"
                f"  generated_artifacts={len(artifact_result.skipped_paths)}"
            )

        archive_file.write_text(content, encoding="utf-8")
        next_steps_match = re.search(r"##\s+Next Steps.*?(?=\n##|\Z)", content, re.DOTALL)
        next_steps = next_steps_match.group(0).strip() if next_steps_match else "## Next Steps\n- Review archive and resume work"
        header_lines = content.splitlines()[:20]
        pointer = (
            f"<!-- ARCHIVED: {archive_file.name} -->\n"
            f"> 已封存至 `memory/archive/{archive_file.name}`\n\n"
        )
        new_content = pointer + "\n".join(header_lines).strip() + "\n\n---\n\n" + next_steps + "\n"
        self.active_task_file.write_text(new_content, encoding="utf-8")

        manifest = self._load_manifest()
        manifest["archives"].append(
            {
                "timestamp": timestamp,
                "datetime": datetime.now().isoformat(timespec="seconds"),
                "archive_file": f"archive/{archive_file.name}",
                "source_file": str(self.active_task_file),
                "original_lines": original_lines,
                "new_lines": len(new_content.splitlines()),
                "reason": "memory cleanup",
                "removed_generated_artifacts": artifact_result.removed_paths,
                "skipped_generated_artifacts": artifact_result.skipped_paths,
            }
        )
        self._save_manifest(manifest)
        return (
            "cleanup completed\n"
            f"  archive={archive_file}\n"
            f"  removed_generated_artifacts={len(artifact_result.removed_paths)}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage memory pressure and generated cache cleanup.")
    parser.add_argument("--memory-root", default="./memory")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--plan", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--manifest", action="store_true")
    parser.add_argument("--format", choices=["human", "json"], default="human")
    parser.add_argument("--clean-generated", action="store_true", help="Only clean generated artifacts such as __pycache__ and render caches.")
    args = parser.parse_args()

    janitor = MemoryJanitor(Path(args.memory_root))

    if args.clean_generated:
        result = janitor.cleanup_generated_artifacts(dry_run=args.dry_run)
        payload = {
            "removed_paths": result.removed_paths,
            "skipped_paths": result.skipped_paths,
        }
        if args.format == "json":
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(f"removed={len(result.removed_paths)} skipped={len(result.skipped_paths)}")
            for path in result.removed_paths:
                print(f"  removed: {path}")
            for path in result.skipped_paths:
                print(f"  skipped: {path}")
        return 0

    if args.check:
        line_count, status = janitor.check_hot_memory_status()
        payload = {
            "status": status,
            "line_count": line_count,
            "soft_limit": janitor.HOT_MEMORY_SOFT_LIMIT,
            "hard_limit": janitor.HOT_MEMORY_HARD_LIMIT,
            "critical": janitor.HOT_MEMORY_CRITICAL,
        }
        if args.format == "json":
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(f"status={status} line_count={line_count}")
            warning = janitor.generate_warning_message(line_count, status)
            if warning:
                print(warning)
        return 0

    if args.plan:
        if args.format == "json":
            line_count, status = janitor.check_hot_memory_status()
            archivable = janitor.analyze_archivable_content()
            payload = {
                "status": status,
                "line_count": line_count,
                "completed_task_blocks": len(archivable["completed_tasks"]),
                "obsolete_decisions": len(archivable["obsolete_decisions"]),
                "archived_references": len(archivable["archived_references"]),
                "generated_artifacts": [str(path) for path in janitor.find_generated_artifacts()],
            }
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(janitor.create_archive_plan())
        return 0

    if args.execute:
        print(janitor.execute_cleanup(dry_run=args.dry_run))
        return 0

    if args.manifest:
        manifest = janitor._load_manifest()
        print(json.dumps(manifest, ensure_ascii=False, indent=2) if args.format == "json" else manifest)
        return 0

    line_count, status = janitor.check_hot_memory_status()
    print(f"status={status} line_count={line_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
