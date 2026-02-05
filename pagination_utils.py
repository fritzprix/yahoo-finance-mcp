"""Pagination utilities with token-based limits and plain text formatting."""

import json
from dataclasses import dataclass
from typing import Any, List, Optional, Union
import pandas as pd


@dataclass
class PaginationResult:
    """Result of pagination operation."""
    formatted_text: str
    current_page: int
    total_pages: int
    total_items: int
    items_on_page: int
    estimated_tokens: int


def estimate_tokens(text: str) -> int:
    """Estimate token count from text.
    
    Uses rough approximation: ~4 characters per token.
    
    Args:
        text: Text to estimate
        
    Returns:
        Estimated token count
    """
    return len(text) // 4


def format_table_row(values: List[str], widths: List[int]) -> str:
    """Format a single table row with aligned columns.
    
    Args:
        values: Column values
        widths: Column widths
        
    Returns:
        Formatted row string
    """
    formatted = []
    for value, width in zip(values, widths):
        formatted.append(str(value).ljust(width))
    return " | ".join(formatted)


def format_dataframe_as_table(df: pd.DataFrame, max_col_width: int = 15) -> str:
    """Format DataFrame as plain text table.
    
    Args:
        df: DataFrame to format
        max_col_width: Maximum column width
        
    Returns:
        Formatted table string
    """
    if df.empty:
        return "No data available"
    
    # Calculate column widths
    widths = []
    headers = []
    
    for col in df.columns:
        col_str = str(col)
        headers.append(col_str)
        max_width = max(
            len(col_str),
            df[col].astype(str).str.len().max() if len(df) > 0 else 0
        )
        widths.append(min(max_width, max_col_width))
    
    # Build table
    lines = []
    
    # Header
    lines.append(format_table_row(headers, widths))
    lines.append(format_table_row(["-" * w for w in widths], widths))
    
    # Rows
    for _, row in df.iterrows():
        values = []
        for col, width in zip(df.columns, widths):
            val = str(row[col])
            if len(val) > width:
                val = val[:width-3] + "..."
            values.append(val)
        lines.append(format_table_row(values, widths))
    
    return "\n".join(lines)


def format_dict_as_text(data: dict, indent: int = 0) -> str:
    """Format dictionary as readable text.
    
    Args:
        data: Dictionary to format
        indent: Indentation level
        
    Returns:
        Formatted text
    """
    lines = []
    prefix = "  " * indent
    
    for key, value in data.items():
        if isinstance(value, dict):
            lines.append(f"{prefix}{key}:")
            lines.append(format_dict_as_text(value, indent + 1))
        elif isinstance(value, list):
            lines.append(f"{prefix}{key}: [{len(value)} items]")
        else:
            lines.append(f"{prefix}{key}: {value}")
    
    return "\n".join(lines)


def paginate_by_tokens(
    data: Union[pd.DataFrame, List[dict], dict],
    page: int,
    max_tokens: int = 6000,
    data_type: str = "table",
    title: str = "DATA",
    cache_age: Optional[float] = None,
) -> PaginationResult:
    """Paginate data based on token limit.
    
    Args:
        data: Data to paginate (DataFrame, list of dicts, or dict)
        page: Page number (1-indexed)
        max_tokens: Maximum tokens per page
        data_type: Type of data formatting ("table", "list", "dict")
        title: Title for the output
        cache_age: Age of cached data in seconds
        
    Returns:
        PaginationResult with formatted text and metadata
    """
    # Convert to DataFrame if needed
    if isinstance(data, list):
        if not data:
            return _create_empty_result(title)
        df = pd.DataFrame(data)
    elif isinstance(data, dict):
        if data_type == "dict":
            # Format as key-value pairs
            return _paginate_dict(data, page, max_tokens, title, cache_age)
        df = pd.DataFrame([data])
    elif isinstance(data, pd.DataFrame):
        df = data
    else:
        raise ValueError(f"Unsupported data type: {type(data)}")
    
    if df.empty:
        return _create_empty_result(title)
    
    # Paginate by estimating tokens per row
    total_items = len(df)
    
    # Estimate tokens for header and footer (roughly 500 tokens)
    overhead_tokens = 500
    available_tokens = max_tokens - overhead_tokens
    
    # Sample first row to estimate tokens per row
    sample_text = format_dataframe_as_table(df.head(1))
    tokens_per_row = estimate_tokens(sample_text)
    
    # Calculate items per page
    items_per_page = max(1, available_tokens // max(tokens_per_row, 1))
    
    # Calculate pagination
    total_pages = (total_items + items_per_page - 1) // items_per_page
    page = max(1, min(page, total_pages))  # Clamp to valid range
    
    start_idx = (page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, total_items)
    
    # Get page data
    page_df = df.iloc[start_idx:end_idx]
    
    # Format output
    table_text = format_dataframe_as_table(page_df)
    
    # Build complete output
    output_lines = [
        "═" * 70,
        f"📊 {title}",
        "═" * 70,
        "",
        table_text,
        "",
        "─" * 70,
        f"📄 PAGE {page} of {total_pages} | Showing items {start_idx + 1}-{end_idx} of {total_items} total",
    ]
    
    # Add token estimate
    full_text = "\n".join(output_lines)
    token_count = estimate_tokens(full_text)
    output_lines.append(f"📊 Estimated tokens: {token_count:,} / {max_tokens:,} max")
    output_lines.append("─" * 70)
    output_lines.append("")
    
    # Add navigation
    nav_lines = ["🔍 NAVIGATION:"]
    if page < total_pages:
        next_start = end_idx + 1
        next_end = min(end_idx + items_per_page, total_items)
        nav_lines.append(f"  • Next page: Use page={page + 1} to see items {next_start}-{next_end}")
    if page > 1:
        prev_start = max(1, start_idx - items_per_page + 1)
        prev_end = start_idx
        nav_lines.append(f"  • Previous page: Use page={page - 1} to see items {prev_start}-{prev_end}")
    nav_lines.append(f'  • Export all data: Add export_path="./data.json"')
    
    output_lines.extend(nav_lines)
    output_lines.append("")
    
    # Add cache info
    if cache_age is not None:
        output_lines.append(f"💾 CACHE: Data cached (age: {cache_age:.0f} seconds)")
    else:
        output_lines.append("💾 CACHE: Fresh data (not cached)")
    
    output_lines.append("═" * 70)
    
    final_text = "\n".join(output_lines)
    final_tokens = estimate_tokens(final_text)
    
    return PaginationResult(
        formatted_text=final_text,
        current_page=page,
        total_pages=total_pages,
        total_items=total_items,
        items_on_page=len(page_df),
        estimated_tokens=final_tokens,
    )


def _paginate_dict(
    data: dict,
    page: int,
    max_tokens: int,
    title: str,
    cache_age: Optional[float],
) -> PaginationResult:
    """Paginate dictionary data."""
    # Convert dict to list of key-value pairs for pagination
    items = list(data.items())
    total_items = len(items)
    
    if total_items == 0:
        return _create_empty_result(title)
    
    # Estimate items per page
    overhead_tokens = 500
    available_tokens = max_tokens - overhead_tokens
    
    # Rough estimate: 50 tokens per key-value pair
    items_per_page = max(1, available_tokens // 50)
    
    total_pages = (total_items + items_per_page - 1) // items_per_page
    page = max(1, min(page, total_pages))
    
    start_idx = (page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, total_items)
    
    page_items = dict(items[start_idx:end_idx])
    
    # Format as text
    content = format_dict_as_text(page_items)
    
    output_lines = [
        "═" * 70,
        f"📊 {title}",
        "═" * 70,
        "",
        content,
        "",
        "─" * 70,
        f"📄 PAGE {page} of {total_pages} | Showing items {start_idx + 1}-{end_idx} of {total_items} total",
    ]
    
    full_text = "\n".join(output_lines)
    token_count = estimate_tokens(full_text)
    output_lines.append(f"📊 Estimated tokens: {token_count:,} / {max_tokens:,} max")
    output_lines.append("─" * 70)
    
    if cache_age is not None:
        output_lines.append(f"💾 CACHE: Data cached (age: {cache_age:.0f} seconds)")
    
    output_lines.append("═" * 70)
    
    final_text = "\n".join(output_lines)
    
    return PaginationResult(
        formatted_text=final_text,
        current_page=page,
        total_pages=total_pages,
        total_items=total_items,
        items_on_page=len(page_items),
        estimated_tokens=estimate_tokens(final_text),
    )


def _create_empty_result(title: str) -> PaginationResult:
    """Create result for empty data."""
    text = f"""
═══════════════════════════════════════════════════════════════════
📊 {title}
═══════════════════════════════════════════════════════════════════

No data available

═══════════════════════════════════════════════════════════════════
""".strip()
    
    return PaginationResult(
        formatted_text=text,
        current_page=1,
        total_pages=1,
        total_items=0,
        items_on_page=0,
        estimated_tokens=estimate_tokens(text),
    )


def export_to_json(data: Any, filepath: str) -> str:
    """Export data to JSON file.
    
    Args:
        data: Data to export (DataFrame, list, or dict)
        filepath: Path to save JSON file
        
    Returns:
        Success message with file path and size
    """
    # Convert DataFrame to dict
    if isinstance(data, pd.DataFrame):
        data_dict = data.to_dict(orient="records")
    else:
        data_dict = data
    
    # Write to file
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data_dict, f, indent=2, default=str)
    
    # Get file size
    import os
    file_size = os.path.getsize(filepath)
    size_kb = file_size / 1024
    
    return f"""
═══════════════════════════════════════════════════════════════════
✅ DATA EXPORTED SUCCESSFULLY
═══════════════════════════════════════════════════════════════════

📁 File: {filepath}
📊 Size: {size_kb:.2f} KB
📝 Items: {len(data_dict) if isinstance(data_dict, list) else 1}

The complete dataset has been saved to the specified file.
═══════════════════════════════════════════════════════════════════
""".strip()
