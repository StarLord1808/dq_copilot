"""Profiler agent for computing table and column statistics."""

from typing import Dict, Any, List
import pandas as pd
import numpy as np


class ProfilerAgent:
    """Agent responsible for profiling tables and computing statistics."""
    
    def profile(self, df: pd.DataFrame, table_name: str) -> Dict[str, Any]:
        """
        Profile a DataFrame and compute comprehensive statistics.
        
        Args:
            df: DataFrame to profile
            table_name: Name of the table
            
        Returns:
            Dictionary containing table and column-level statistics
        """
        profile = {
            "table_name": table_name,
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": [],
        }
        
        for col in df.columns:
            col_stats = self._profile_column(df, col)
            profile["columns"].append(col_stats)
        
        return profile
    
    def _profile_column(self, df: pd.DataFrame, col_name: str) -> Dict[str, Any]:
        """
        Profile a single column.
        
        Args:
            df: DataFrame containing the column
            col_name: Name of the column to profile
            
        Returns:
            Dictionary of column statistics
        """
        series = df[col_name]
        total_rows = len(df)
        
        stats = {
            "name": col_name,
            "dtype": str(series.dtype),
            "null_count": int(series.isna().sum()),
            "null_pct": float(series.isna().sum() / total_rows) if total_rows > 0 else 0.0,
            "distinct_count": int(series.nunique()),
            "distinct_pct": float(series.nunique() / total_rows) if total_rows > 0 else 0.0,
        }
        
        # Add min/max for numeric columns
        if pd.api.types.is_numeric_dtype(series):
            non_null = series.dropna()
            if len(non_null) > 0:
                stats["min"] = float(non_null.min())
                stats["max"] = float(non_null.max())
                stats["mean"] = float(non_null.mean())
                stats["median"] = float(non_null.median())
                stats["std"] = float(non_null.std()) if len(non_null) > 1 else 0.0
        
        # Add example values (up to 5 unique non-null values)
        non_null_values = series.dropna().unique()
        example_count = min(5, len(non_null_values))
        if example_count > 0:
            examples = non_null_values[:example_count].tolist()
            # Convert to native Python types for JSON serialization
            stats["example_values"] = [
                self._convert_to_native_type(val) for val in examples
            ]
        else:
            stats["example_values"] = []
        
        return stats
    
    def _convert_to_native_type(self, val: Any) -> Any:
        """
        Convert numpy/pandas types to native Python types for JSON serialization.
        
        Args:
            val: Value to convert
            
        Returns:
            Native Python type
        """
        if pd.isna(val):
            return None
        elif isinstance(val, (np.integer, np.int64, np.int32)):
            return int(val)
        elif isinstance(val, (np.floating, np.float64, np.float32)):
            return float(val)
        elif isinstance(val, np.bool_):
            return bool(val)
        elif isinstance(val, (np.datetime64, pd.Timestamp)):
            return str(val)
        else:
            return val
