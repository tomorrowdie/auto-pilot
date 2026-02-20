"""
Knowledge Manager — The shared Hub for all data sources.

Generic file/folder CRUD for Markdown insights.
This module has ZERO knowledge of any specific data source (H10, Cerebro, etc.).
Data sources convert their output into Markdown BEFORE calling save_insight().

Twin-File Protocol (Mandatory Standard):
    Every save_insight() call SHOULD include a dataframe parameter.
    This produces a paired MD + CSV output for full traceability:
        {Title}_{YYYY-MM-DD}.md   <- Human-readable insight
        {Title}_{YYYY-MM-DD}.csv  <- Raw evidence data

Storage layout:
    storage/
        0_catalog_insight/   <- Source 0 (Catalog Insight)
        1_keyword_traffic/   <- Source 1 (Keyword Traffic)
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
        subfolder: str,
        filename: str,
        content: str,
        dataframe=None,
    ) -> str:
        """
        Save a Markdown string to storage/<subfolder>/<filename>.

        Twin-File Protocol: if a pandas DataFrame is provided, a CSV file
        is saved alongside the MD file with the same base name.

        Args:
            subfolder: Target subfolder inside storage/ (created if missing).
                       e.g. '0_catalog_insight', '1_keyword_traffic'.
            filename:  File name (e.g. 'Baby_Teether_Strategy_2026-02-08.md').
            content:   Pre-formatted Markdown string.
            dataframe: Optional pandas DataFrame to save as paired CSV.

        Returns:
            The filename that was written.
        """
        dest_dir = os.path.join(_STORAGE_DIR, subfolder)
        os.makedirs(dest_dir, exist_ok=True)

        # Save Markdown
        filepath = os.path.join(dest_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        # Twin-File Protocol: save paired CSV
        if dataframe is not None:
            csv_filename = filename.replace(".md", ".csv")
            csv_path = os.path.join(dest_dir, csv_filename)
            dataframe.to_csv(csv_path, index=False)

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
        """
        Generate a dated, case-preserving filename from a title.

        Twin-File Protocol naming: {Project_Name}_{YYYY-MM-DD}.md
        Example: "Baby Teether Strategy" -> "Baby_Teether_Strategy_2026-02-08.md"
        """
        slug = _title_slug(title)
        date_str = datetime.now().strftime("%Y-%m-%d")
        return f"{slug}_{date_str}.md"

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
    """Convert a title to a lowercase filesystem-safe slug."""
    s = text.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_]+", "_", s)
    return s[:80]


def _title_slug(text: str) -> str:
    """Convert a title to a filesystem-safe slug, preserving original casing."""
    s = text.strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_]+", "_", s)
    return s[:80]
