# Testing Guide

This guide explains how to test the Yahoo Finance MCP server using the MCP Inspector.

## Quick Start

### Windows
```bash
run_inspector.bat
```

### macOS/Linux
```bash
./run_inspector.sh
```

### Production Testing (via uvx)

If you have published the package or want to test the `uvx` entry point:

#### Windows
```bash
run_inspector_prod.bat
```

#### macOS/Linux
```bash
chmod +x run_inspector_prod.sh
./run_inspector_prod.sh
```

The MCP Inspector will start on **http://localhost:6274**

---

## What is MCP Inspector?

MCP Inspector is a web-based tool for testing Model Context Protocol servers. It provides:
- Interactive UI to call MCP tools
- Real-time response viewing
- Parameter input forms
- Error debugging

---

## Testing Workflow

### 1. Start the Inspector

Run the appropriate script for your OS (see Quick Start above).

### 2. Open in Browser

Navigate to **http://localhost:6274** in your web browser.

### 3. Test Tools

The inspector will show all available tools. Try these tests:

#### Test 1: Basic Stock Info
- Tool: `get_stock_info`
- Parameters:
  ```json
  {
    "ticker": "AAPL",
    "fields": ["currentPrice", "marketCap", "trailingPE"]
  }
  ```
- Expected: Only 3 fields returned with cache status

#### Test 2: Pagination
- Tool: `get_historical_stock_prices`
- Parameters:
  ```json
  {
    "ticker": "AAPL",
    "period": "1mo",
    "interval": "1d",
    "page": 1
  }
  ```
- Expected: Paginated response with navigation guidance

#### Test 3: Cache Behavior
- Run the same query twice
- First call: "Fresh data (not cached)"
- Second call: "Data cached (age: X seconds)"

#### Test 4: JSON Export
- Tool: `get_historical_stock_prices`
- Parameters:
  ```json
  {
    "ticker": "AAPL",
    "period": "5d",
    "interval": "1d",
    "export_path": "./test_export.json"
  }
  ```
- Expected: Export success message and file created

---

## Troubleshooting

### Inspector won't start
- Make sure Node.js is installed: `node --version`
- Install npx: `npm install -g npx`
- Check if port 6274 is available

### Server errors
- Verify Python 3.11+ is installed
- Install dependencies: `uv sync` or `pip install -e .`
- Check yfinance is working: `python -c "import yfinance; print(yfinance.__version__)"`

### Browser can't connect
- Ensure firewall allows localhost:6274
- Try 127.0.0.1:6274 instead of localhost
- Check server logs for errors

---

## Advanced Testing

### Test All Tools

See [manual_testing_guide.md](C:\Users\SKTelecom\.gemini\antigravity\brain\d0950c1d-b04a-415d-ab2c-bcbdf1b6730e\manual_testing_guide.md) for comprehensive test cases.

### Automated Tests

Run unit tests:
```bash
python tests/test_pagination.py
```

### Performance Testing

Monitor cache hit rates and response times in the inspector output.

---

## Stopping the Inspector

Press **Ctrl+C** in the terminal to stop the server.

---

## Next Steps

After testing:
1. Verify all tools work correctly
2. Check pagination appears on large datasets
3. Confirm cache behavior
4. Test JSON export functionality
5. Ready for production use!
