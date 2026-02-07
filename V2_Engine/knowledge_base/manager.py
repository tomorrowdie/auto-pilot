"""
Knowledge Manager — The shared Hub for all data sources.

Generic file/folder CRUD for Markdown insights.
This module has ZERO knowledge of any specific data source (H10, Cerebro, etc.).
Data sources convert their output into Markdown BEFORE calling save_insight().

Storage layout:
    storage/
        0_catalog_insight/   <- Source 0
        1_traffic/           <- Source 1
        ...
        99_uncategorized/    <- Legacy / uncategorized
"""

from __future__ import annotations

import os
import re
import shutil
from datetime import datetime

_STORAGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "storage")
_DEFAULT_CATEGORY = "99_uncategorized"


class KnowledgeManager:
    """
    Generic Hub — manages folders (categories) and Markdown files.

    No business logic. Accepts pre-formatted Markdown strings.
    """

    def __init__(self):
        os.makedirs(_STORAGE_DIR, exist_ok=True)
        self._migrate_root_files()

    # ------------------------------------------------------------------
    # Category (folder) management
    # ------------------------------------------------------------------

    def list_categories(self) -> list[str]:
        """Return sorted list of category folder names."""
        return sorted(
            entry for entry in os.listdir(_STORAGE_DIR)
            if os.path.isdir(os.path.join(_STORAGE_DIR, entry))
        )

    def create_category(self, name: str) -> bool:
        """
        Create a new category folder. Returns True if created.

        Sanitizes the name to be filesystem-safe.
        """
        safe = _slugify(name)
        if not safe:
            return False
        cat_dir = os.path.join(_STORAGE_DIR, safe)
        if os.path.exists(cat_dir):
            return False
        os.makedirs(cat_dir)
        return True

    def rename_category(self, old_name: str, new_name: str) -> bool:
        """Rename a category folder. Returns True if renamed."""
        old_dir = os.path.join(_STORAGE_DIR, old_name)
        safe_new = _slugify(new_name)
        if not safe_new or not os.path.isdir(old_dir):
            return False
        new_dir = os.path.join(_STORAGE_DIR, safe_new)
        if os.path.exists(new_dir):
            return False
        os.rename(old_dir, new_dir)
        return True

    # ------------------------------------------------------------------
    # Insight (file) management
    # ------------------------------------------------------------------

    def save_insight(
        self,
        category: str,
        filename: str,
        content: str,
    ) -> str:
        """
        Save a Markdown string to storage/<category>/<filename>.

        Args:
            category: Folder name (created if missing).
            filename: File name (e.g. '2026-02-07_garlic_press.md').
            content:  Pre-formatted Markdown string.

        Returns:
            The filename that was written.
        """
        cat_dir = os.path.join(_STORAGE_DIR, category)
        os.makedirs(cat_dir, exist_ok=True)

        filepath = os.path.join(cat_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        return filename

    def list_insights(self) -> dict[str, list[dict]]:
        """
        Return all saved insights grouped by category.

        Returns:
            {
              '0_catalog_insight': [
                {'filename': '...', 'size_bytes': 1234, 'modified': '...'},
              ],
            }

        Empty categories are included as empty lists.
        """
        grouped: dict[str, list[dict]] = {}

        for entry in sorted(os.listdir(_STORAGE_DIR)):
            cat_dir = os.path.join(_STORAGE_DIR, entry)
            if not os.path.isdir(cat_dir):
                continue

            files: list[dict] = []
            for fname in sorted(os.listdir(cat_dir), reverse=True):
                if not fname.endswith(".md"):
                    continue
                fpath = os.path.join(cat_dir, fname)
                stat = os.stat(fpath)
                files.append({
                    "filename": fname,
                    "size_bytes": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).strftime(
                        "%Y-%m-%d %H:%M"
                    ),
                })

            grouped[entry] = files

        return grouped

    def get_insight(self, category: str, filename: str) -> str:
        """Read and return the Markdown content of a saved insight."""
        fpath = os.path.join(_STORAGE_DIR, category, filename)
        with open(fpath, "r", encoding="utf-8") as f:
            return f.read()

    def delete_insight(self, category: str, filename: str) -> bool:
        """Delete a saved insight. Returns True if removed."""
        fpath = os.path.join(_STORAGE_DIR, category, filename)
        if os.path.exists(fpath):
            os.remove(fpath)
            return True
        return False

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def make_filename(title: str) -> str:
        """Generate a dated, slugified filename from a title."""
        slug = _slugify(title)
        date_str = datetime.now().strftime("%Y-%m-%d")
        return f"{date_str}_{slug}.md"

    # ------------------------------------------------------------------
    # Migration — one-time move of root-level .md files
    # ------------------------------------------------------------------

    def _migrate_root_files(self) -> None:
        """Move any .md files sitting in the root storage/ into 99_uncategorized/."""
        root_mds = [
            f for f in os.listdir(_STORAGE_DIR)
            if f.endswith(".md") and os.path.isfile(os.path.join(_STORAGE_DIR, f))
        ]
        if not root_mds:
            return

        dest = os.path.join(_STORAGE_DIR, _DEFAULT_CATEGORY)
        os.makedirs(dest, exist_ok=True)

        for fname in root_mds:
            src = os.path.join(_STORAGE_DIR, fname)
            dst = os.path.join(dest, fname)
            shutil.move(src, dst)


# ------------------------------------------------------------------
# Module-level helpers
# ------------------------------------------------------------------

def _slugify(text: str) -> str:
    """Convert a title to a filesystem-safe slug."""
    s = text.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_]+", "_", s)
    return s[:80]
