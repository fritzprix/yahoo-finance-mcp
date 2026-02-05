# Tests Directory

This directory contains test files for the yfin-mcp package.

## Test Files

- **test_pagination.py** - Unit tests for pagination and caching utilities
  - Tests token estimation
  - Tests cache operations (hit/miss)
  - Tests pagination logic
  - Tests JSON export
  - Tests edge cases (empty data)

- **test_e2e.py** - End-to-end tests for all MCP tools (requires yfinance)
  - Tests all tool functions
  - Tests pagination with live data
  - Tests caching behavior
  - Tests JSON export

- **test_manual.py** - Manual testing script for quick verification
  - Simple tests for key functionality
  - Useful for quick smoke testing

## Running Tests

### Unit Tests (Recommended)
```bash
python tests/test_pagination.py
```

### E2E Tests (Requires yfinance and network)
```bash
python tests/test_e2e.py
```

### Manual Tests
```bash
python tests/test_manual.py
```

## Test Coverage

- ✅ Token estimation and pagination
- ✅ Cache operations (LRU, TTL)
- ✅ JSON export functionality
- ✅ Plain text formatting
- ✅ Edge cases (empty data, single page)
- ⚠️ Live API integration (requires manual testing)
