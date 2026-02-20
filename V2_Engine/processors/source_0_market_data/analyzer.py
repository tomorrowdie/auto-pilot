"""
Market Analyzer — The single entry point for Source 0 business intelligence.

Orchestrates all metric modules and returns a consolidated
"Market Snapshot" dictionary that any downstream consumer
(API, CLI, AI agent) can use directly.
"""

from __future__ import annotations

import pandas as pd

from .metrics.sales import calculate_sales_metrics
from .metrics.pricing import calculate_pricing_metrics
from .metrics.performance import calculate_performance_metrics
from .metrics.characteristics import calculate_characteristics_metrics
from .metrics.sellers import calculate_seller_metrics
from .metrics.brands import calculate_brand_metrics


class MarketAnalyzer:
    """
    Takes a cleaned DataFrame and produces structured market intelligence.

    Usage:
        analyzer = MarketAnalyzer()
        snapshot = analyzer.analyze(df)
    """

    def analyze(
        self,
        df: pd.DataFrame,
        rank_column: str = "Sales Rank (ALL)",
    ) -> dict:
        """
        Run all available metric calculations and return a Market Snapshot.

        Args:
            df:          Cleaned, ranked DataFrame (output of H10Ingestor).
            rank_column: Which rank column to bucket by.

        Returns:
            {
              "meta":            { "total_rows": 982, "rank_column": "..." },
              "sales":           { ... },   # from metrics.sales
              "pricing":         { ... },   # from metrics.pricing
              "performance":     { ... },   # from metrics.performance
              "characteristics": { ... },   # from metrics.characteristics
              "sellers":         { ... },   # from metrics.sellers
              "brands":          { ... },   # from metrics.brands
            }
        """
        snapshot: dict = {
            "meta": {
                "total_rows": len(df),
                "rank_column": rank_column,
                "columns_available": list(df.columns),
            },
            "sales": calculate_sales_metrics(df, rank_column),
            "pricing": calculate_pricing_metrics(df, rank_column),
            "performance": calculate_performance_metrics(df, rank_column),
            "characteristics": calculate_characteristics_metrics(df, rank_column),
            "sellers": calculate_seller_metrics(df),
            "brands": calculate_brand_metrics(df),
        }

        return snapshot
