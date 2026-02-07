"""
Pagination utilities for Yahoo Finance MCP server.
Provides token-based pagination and plain text formatting for LLM-friendly responses.
"""

import json
from dataclasses import dataclass
from typing import Any, List, Optional, Union

import pandas as pd


@dataclass
class PaginationResult:
    """Result of pagination operation."""
    formatted_text: str
    page: int
    total_pages: int
    total_items: int
    items_on_page: int


def estimate_tokens(text: str) -> int:
    """
    Estimate token count for text.
    Uses conservative estimate of ~4 characters per token.
    
    Args:
        text: Text to estimate tokens for
        
    Returns:
        Estimated token count
    """
    return len(text) // 4


def format_dataframe_as_table(df: pd.DataFrame, max_col_width: int = 15) -> str:
    """
    Format DataFrame as plain text table with fixed-width columns.
    
    Args:
        df: DataFrame to format
        max_col_width: Maximum column width
        
    Returns:
        Formatted table string
    """
    if df.empty:
        return "No data available"
    
    # Convert all columns to string and truncate
    formatted_data = []
    for _, row in df.iterrows():
        formatted_row = []
        for val in row:
            str_val = str(val)
            if len(str_val) > max_col_width:
                str_val = str_val[:max_col_width-2] + ".."
            formatted_row.append(str_val)
        formatted_data.append(formatted_row)
    
    # Get column names
    columns = [str(col)[:max_col_width] for col in df.columns]
    
    # Build table
    lines = []
    
    # Header
    header = " | ".join(f"{col:<{max_col_width}}" for col in columns)
    lines.append(header)
    lines.append("-" * len(header))
    
    # Rows
    for row in formatted_data:
        row_str = " | ".join(f"{val:<{max_col_width}}" for val in row)
        lines.append(row_str)
    
    return "\n".join(lines)


def format_dict_as_text(data: dict, indent: int = 0) -> str:
    """
    Format dictionary as plain text with key-value pairs.
    
    Args:
        data: Dictionary to format
        indent: Indentation level
        
    Returns:
        Formatted text string
    """
    lines = []
    indent_str = "  " * indent
    
    for key, value in data.items():
        if isinstance(value, dict):
            lines.append(f"{indent_str}{key}:")
            lines.append(format_dict_as_text(value, indent + 1))
        elif isinstance(value, list):
            lines.append(f"{indent_str}{key}: {len(value)} items")
        else:
            lines.append(f"{indent_str}{key}: {value}")
    
    return "\n".join(lines)


def paginate_by_tokens(
    data: Union[pd.DataFrame, List[dict], dict],
    page: int,
    max_tokens: int = 6000,
    data_type: str = "table",
    title: Optional[str] = None,
    cache_age: Optional[float] = None,
) -> PaginationResult:
    """
    Paginate data based on token limit.
    
    Args:
        data: Data to paginate (DataFrame, list of dicts, or dict)
        page: Page number (1-indexed)
        max_tokens: Maximum tokens per page
        data_type: Type of data ("table" or "dict")
        title: Optional title for the page
        cache_age: Optional cache age in seconds
        
    Returns:
        PaginationResult with formatted text and metadata
    """
    # Convert data to list of items for pagination
    if isinstance(data, pd.DataFrame):
        total_items = len(data)
        items = data
    elif isinstance(data, list):
        total_items = len(data)
        items = data
    elif isinstance(data, dict):
        total_items = len(data)
        items = data
    else:
        raise ValueError(f"Unsupported data type: {type(data)}")
    
    if total_items == 0:
        return PaginationResult(
            formatted_text="No data available",
            page=1,
            total_pages=1,
            total_items=0,
            items_on_page=0
        )
    
    # Calculate items per page dynamically
    # Start with all items and reduce until under token limit
    items_per_page = total_items
    test_data = items
    
    while items_per_page > 0:
        # Get subset for this page size
        if isinstance(data, pd.DataFrame):
            test_data = data.iloc[:items_per_page]
            test_text = format_dataframe_as_table(test_data)
        elif isinstance(data, dict):
            test_items = dict(list(data.items())[:items_per_page])
            test_text = format_dict_as_text(test_items)
        else:
            test_items = data[:items_per_page]
            test_text = "\n".join(str(item) for item in test_items)
        
        # Check token count
        if estimate_tokens(test_text) <= max_tokens * 0.8:  # Leave 20% margin
            break
        
        # Reduce page size
        items_per_page = max(1, items_per_page // 2)
    
    # Calculate pagination
    total_pages = (total_items + items_per_page - 1) // items_per_page
    page = max(1, min(page, total_pages))  # Clamp page number
    
    start_idx = (page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, total_items)
    
    # Get page data
    if isinstance(data, pd.DataFrame):
        page_data = data.iloc[start_idx:end_idx]
        content = format_dataframe_as_table(page_data)
    elif isinstance(data, dict):
        page_items = dict(list(data.items())[start_idx:end_idx])
        content = format_dict_as_text(page_items)
    else:
        page_items = data[start_idx:end_idx]
        content = "\n".join(str(item) for item in page_items)
    
    # Build formatted output
    lines = []
    lines.append("=" * 70)
    if title:
        lines.append(f"📊 {title}")
        lines.append("=" * 70)
    lines.append("")
    lines.append(content)
    lines.append("")
    lines.append("─" * 70)
    lines.append(f"📄 PAGE {page} of {total_pages} | Showing items {start_idx + 1}-{end_idx} of {total_items} total")
    lines.append(f"📊 Estimated tokens: {estimate_tokens(content)} / {max_tokens} max")
    lines.append("─" * 70)
    lines.append("")
    
    # Navigation guidance
    if total_pages > 1:
        lines.append("🔍 NAVIGATION:")
        if page < total_pages:
            lines.append(f"  • Next page: Use page={page + 1} to see items {end_idx + 1}-{min(end_idx + items_per_page, total_items)}")
        if page > 1:
            lines.append(f"  • Previous page: Use page={page - 1}")
        lines.append(f"  • Export all data: Add export_path=\"./data.json\"")
        lines.append("")
    
    # Cache info
    if cache_age is not None:
        if cache_age == 0 or cache_age is None:
            lines.append("💾 CACHE: Fresh data (not cached)")
        else:
            lines.append(f"💾 CACHE: Data cached (age: {cache_age:.1f} seconds)")
    
    lines.append("=" * 70)
    
    formatted_text = "\n".join(lines)
    
    return PaginationResult(
        formatted_text=formatted_text,
        page=page,
        total_pages=total_pages,
        total_items=total_items,
        items_on_page=end_idx - start_idx
    )


def export_to_json(data: Union[pd.DataFrame, List[dict], dict], file_path: str) -> str:
    """
    Export data to JSON file.
    
    Args:
        data: Data to export
        file_path: Path to save JSON file
        
    Returns:
        Success message with file info
    """
    import os

    # Resolve absolute path
    abs_file_path = os.path.abspath(file_path)

    # Convert DataFrame to dict
    if isinstance(data, pd.DataFrame):
        export_data = data.to_dict(orient="records")
    else:
        export_data = data
    
    # Write to file
    with open(abs_file_path, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, default=str)
    
    # Get file size
    file_size = os.path.getsize(abs_file_path)
    size_kb = file_size / 1024
    
    # Count items
    if isinstance(export_data, list):
        item_count = len(export_data)
    elif isinstance(export_data, dict):
        item_count = len(export_data)
    else:
        item_count = 1
    
    # Build response
    lines = []
    lines.append("=" * 70)
    lines.append("✅ DATA EXPORTED SUCCESSFULLY")
    lines.append("=" * 70)
    lines.append("")
    lines.append(f"📁 File: {abs_file_path}")
    lines.append(f"📊 Size: {size_kb:.2f} KB")
    lines.append(f"📝 Items: {item_count}")
    lines.append("")
    lines.append("The complete dataset has been saved to the specified file.")
    lines.append("=" * 70)
    
    return "\n".join(lines)
