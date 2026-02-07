"""
H10 Ingestor — Clean port of the legacy Helium 10 Xray data processor.

Ported from: V1_Legacy/data_sample/data_source_4_amazon_catalog/
             catalog_program/view/amazon_data_process_h10.py

All Streamlit UI code has been removed. This is pure data logic.

Refactored: Now delegates cleaning and ranking to core/ modules
            instead of duplicating that logic inline.
"""

import os
from datetime import datetime
from typing import BinaryIO, Union

import pandas as pd

from .core.cleaning import clean_currency
from .core.ranking import calculate_ranks
from .core.columns import ColumnResolver


class H10Ingestor:
    """
    Ingests one or more Helium 10 Xray CSV exports,
    cleans numeric columns, classifies Organic vs Ads,
    assigns ranking columns, and splits into sub-frames.
    """

    def __init__(self):
        self._combined: pd.DataFrame | None = None
        self._ads: pd.DataFrame | None = None
        self._organic: pd.DataFrame | None = None
        self._date_str: str = ""
        self._week_number: int = 0
        self._file_info: list[dict] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def ingest(
        self, csv_inputs: list[Union[str, BinaryIO]]
    ) -> pd.DataFrame:
        """
        Full pipeline: combine -> clean -> rank -> split.

        Args:
            csv_inputs: List of file paths (str) OR file-like objects
                        (e.g. FastAPI UploadFile, BytesIO).

        Returns:
            The cleaned, ranked DataFrame (combined).
        """
        combined, date_str, week_number, file_info = self._combine_files(csv_inputs)
        self._date_str = date_str
        self._week_number = week_number
        self._file_info = file_info

        # Ensure Source Files column exists
        if "Source Files" not in combined.columns:
            combined["Source Files"] = "Unknown"

        # Clean numeric columns (strip $, commas, coerce to numeric)
        cleaned = clean_currency(combined)

        # Classify Organic/Ads and assign rank columns
        ranked = calculate_ranks(cleaned)

        self._split_by_type(ranked)
        self._combined = ranked
        return ranked

    @property
    def combined(self) -> pd.DataFrame | None:
        return self._combined

    @property
    def ads(self) -> pd.DataFrame | None:
        return self._ads

    @property
    def organic(self) -> pd.DataFrame | None:
        return self._organic

    @property
    def date_str(self) -> str:
        return self._date_str

    @property
    def week_number(self) -> int:
        return self._week_number

    @property
    def file_info(self) -> list[dict]:
        return self._file_info

    def important_columns(self, df: pd.DataFrame) -> list[str]:
        """Return only the priority columns that exist in *df*."""
        return ColumnResolver.priority_columns(df)

    # ------------------------------------------------------------------
    # Internal: Combine
    # ------------------------------------------------------------------

    def _combine_files(self, csv_inputs: list[Union[str, BinaryIO]]):
        """
        Combine multiple CSV sources into one DataFrame.

        Each item can be a file path (str) or a file-like object
        (BytesIO, SpooledTemporaryFile, etc.).

        Preserves the sequential Display Order across files and
        tags each row with its source filename.
        """
        all_frames: list[pd.DataFrame] = []
        file_info: list[dict] = []
        current_display_order = 1

        # Extract filenames for date detection
        filenames: list[str] = []
        for i, src in enumerate(csv_inputs):
            if isinstance(src, str):
                filenames.append(os.path.basename(src))
            else:
                filenames.append(getattr(src, "name", f"upload_{i}.csv"))
        date_str, week_number = self._detect_date_from_filenames(filenames)

        for i, src in enumerate(csv_inputs):
            if isinstance(src, str):
                fname = os.path.basename(src)
            else:
                fname = getattr(src, "name", f"upload_{i}.csv")

            try:
                df = pd.read_csv(src)
            except Exception as exc:
                print(f"  [WARN] Skipping {fname}: {exc}")
                continue

            # Re-number Display Order sequentially across files
            if "Display Order" in df.columns:
                df["Display Order"] = range(
                    current_display_order,
                    current_display_order + len(df),
                )
                current_display_order += len(df)

            df["Source Files"] = fname
            all_frames.append(df)
            file_info.append({
                "filename": fname,
                "rows": len(df),
                "columns": len(df.columns),
            })

        if not all_frames:
            raise ValueError("No CSV files could be processed successfully.")

        combined = pd.concat(all_frames, ignore_index=True)
        return combined, date_str, week_number, file_info

    # ------------------------------------------------------------------
    # Internal: Date detection
    # ------------------------------------------------------------------

    @staticmethod
    def _detect_date_from_filenames(filenames: list[str]) -> tuple[str, int]:
        """
        Extract date and ISO week number from H10 Xray filenames.
        Falls back to today's date if no pattern matches.
        """
        for fname in filenames:
            if "Helium_10_Xray_" not in fname:
                continue
            parts = fname.split("_")
            if len(parts) < 4:
                continue

            # Pattern 1: YYYY-MM-DD
            date_part = parts[3]
            date_only = date_part.split("-", 3)[:3]
            try:
                d = datetime.strptime("-".join(date_only), "%Y-%m-%d")
                return d.strftime("%Y-%m-%d"), d.isocalendar()[1]
            except ValueError:
                pass

            # Pattern 2: YYYYMMDD
            try:
                d = datetime.strptime(date_part[:8], "%Y%m%d")
                return d.strftime("%Y-%m-%d"), d.isocalendar()[1]
            except ValueError:
                pass

        today = datetime.now()
        return today.strftime("%Y-%m-%d"), today.isocalendar()[1]

    # ------------------------------------------------------------------
    # Internal: Split
    # ------------------------------------------------------------------

    def _split_by_type(self, df: pd.DataFrame) -> None:
        """Split into ads / organic sub-frames."""
        if "Organic VS Ads" not in df.columns:
            self._ads = pd.DataFrame()
            self._organic = df.copy()
            return

        self._ads = df[df["Organic VS Ads"] == "Ads"].copy()
        self._organic = df[df["Organic VS Ads"] == "Organic"].copy()
