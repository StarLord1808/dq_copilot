"""Table loader agent for CSV and Parquet files."""

from pathlib import Path
from typing import Tuple, Dict, Any

import pandas as pd


class TableLoaderAgent:
    """Agent responsible for loading tables from various file formats."""
    
    def load(self, file_path: str, table_name: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Load a table from a file path.
        
        Args:
            file_path: Path to the table file (CSV or Parquet)
            table_name: Name of the table for metadata
            
        Returns:
            Tuple of (DataFrame, metadata_dict)
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is unsupported
            Exception: For other loading errors
        """
        path = Path(file_path)
        
        # Check file exists
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Detect format from extension
        suffix = path.suffix.lower()
        
        try:
            if suffix == ".csv":
                df = pd.read_csv(file_path)
                file_format = "csv"
            elif suffix in [".parquet", ".pq"]:
                df = pd.read_parquet(file_path)
                file_format = "parquet"
            else:
                raise ValueError(
                    f"Unsupported file format: {suffix}. "
                    "Supported formats: .csv, .parquet, .pq"
                )
        except pd.errors.EmptyDataError:
            raise ValueError(f"File is empty: {file_path}")
        except pd.errors.ParserError as e:
            raise ValueError(f"Failed to parse file: {str(e)}")
        except Exception as e:
            raise Exception(f"Error loading file: {str(e)}")
        
        # Build metadata
        metadata = {
            "table_name": table_name,
            "file_path": str(path.absolute()),
            "file_format": file_format,
            "file_size_bytes": path.stat().st_size,
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": list(df.columns),
        }
        
        return df, metadata
