# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-02-05

### Added

- **Token-based pagination** with 6,000 token limit per page to prevent LLM context window overflow
- **Intelligent caching system** with TTL support (5min for real-time data, 1hr for fundamental data)
- **Plain text formatting** with visual separators and table formatting for better readability
- **JSON export capability** for all data endpoints via `export_path` parameter
- **Field filtering** for `get_stock_info` to reduce response size
- **Cache statistics** and age tracking displayed in responses
- **LRU cache eviction** with max 100 entries
- **Thread-safe cache** implementation for concurrent access

### Changed

- **Package name** from `yahoo-finance-mcp` to `yfin-mcp`
- **Response format** from JSON to human-readable plain text with pagination metadata
- **All high-risk tools** now include pagination support:
  - `get_historical_stock_prices`
  - `get_option_chain`
  - `get_holder_info`
  - `get_recommendations`
  - `get_stock_info`
  - `get_yahoo_finance_news`
  - `get_financial_statement`

### Improved

- **Performance**: 50-80% reduction in API calls through caching
- **Reliability**: Prevents context window overflow with token-based limits
- **Usability**: Clear navigation guidance for LLM agents
- **Resilience**: Plain text format survives truncation better than JSON

### Technical Details

- Added `cache_manager.py` with LRU cache and TTL support
- Added `pagination_utils.py` with token estimation and formatting
- Updated all tool functions with caching and pagination logic
- Comprehensive test suite in `test_pagination.py`

## [0.1.0] - Previous

### Initial Release

- Basic Yahoo Finance data retrieval
- Stock prices, info, news, and actions
- Financial statements and holder information
- Options data and analyst recommendations
- MCP server implementation
