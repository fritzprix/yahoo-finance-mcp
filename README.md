# yfin-mcp - Yahoo Finance MCP Server

> **Enhanced fork** of [yahoo-finance-mcp](https://github.com/Alex2Yang97/yahoo-finance-mcp) by Alex2Yang97  
> With intelligent pagination, caching, and LLM-optimized responses

<div align="right">
  <a href="README.md">English</a> | <a href="README.zh.md">中文</a>
</div>

A high-performance Model Context Protocol (MCP) server that provides comprehensive financial data from Yahoo Finance with **intelligent pagination**, **caching**, and **LLM-optimized responses**.

---

## 🙏 Attribution & Motivation

### Original Work
This project is built upon the excellent foundation of [yahoo-finance-mcp](https://github.com/Alex2Yang97/yahoo-finance-mcp) created by **Alex2Yang97**. The original implementation provides a comprehensive set of tools for accessing Yahoo Finance data through the Model Context Protocol.

### Why These Enhancements?

While using the original implementation with LLM agents (Claude, ChatGPT, etc.), I encountered critical limitations:

**Problem 1: Context Window Overflow**
- Historical stock data with `period="max"` could return thousands of rows
- Option chains for popular stocks contained hundreds of contracts
- LLM context windows (typically 200K tokens) would overflow
- Responses would be truncated, losing critical data

**Problem 2: No Data Persistence**
- Large datasets couldn't be saved for offline analysis
- Repeated queries wasted API calls and time
- No way to export data for use in other tools

**Problem 3: Poor LLM Readability**
- JSON responses were hard for LLMs to parse when truncated
- No clear navigation guidance for paginated data
- Cache status was invisible to the LLM

### Solution: Pagination, Caching & Export

This fork adds three key enhancements:

1. **Token-Based Pagination** (6,000 token limit per page)
   - Prevents context window overflow
   - Clear navigation guidance for LLMs
   - Dynamic page sizing based on data complexity

2. **Intelligent Caching** (TTL: 5min-1hr)
   - Reduces redundant API calls by 50-80%
   - Sub-millisecond response times for cached data
   - Automatic cache invalidation based on data volatility

3. **JSON Export** (File Download)
   - Save full datasets for offline analysis
   - Export to Excel, databases, or other tools
   - Preserve complete data without pagination

### Credit Where Credit is Due

**Original Author**: Alex2Yang97 deserves full credit for:
- ✅ Complete Yahoo Finance API integration
- ✅ All 9 MCP tools implementation
- ✅ Robust error handling
- ✅ Comprehensive documentation

**This Fork Adds**: Pagination, caching, and export features to make the server production-ready for LLM agents handling large financial datasets.

## Demo

![MCP Demo](assets/demo.gif)

## MCP Tools

The server exposes the following tools through the Model Context Protocol:

### Stock Information

| Tool | Description |
|------|-------------|
| `get_historical_stock_prices` | Get historical OHLCV data for a stock with customizable period and interval |
| `get_stock_info` | Get comprehensive stock data including price, metrics, and company details |
| `get_yahoo_finance_news` | Get latest news articles for a stock |
| `get_stock_actions` | Get stock dividends and splits history |

### Financial Statements

| Tool | Description |
|------|-------------|
| `get_financial_statement` | Get income statement, balance sheet, or cash flow statement (annual/quarterly) |
| `get_holder_info` | Get major holders, institutional holders, mutual funds, or insider transactions |

### Options Data

| Tool | Description |
|------|-------------|
| `get_option_expiration_dates` | Get available options expiration dates |
| `get_option_chain` | Get options chain for a specific expiration date and type (calls/puts) |

### Analyst Information

| Tool | Description |
|------|-------------|
| `get_recommendations` | Get analyst recommendations or upgrades/downgrades history |

## Real-World Use Cases

With this MCP server, you can use Claude to:

### Stock Analysis

- **Price Analysis**: "Show me the historical stock prices for AAPL over the last 6 months with daily intervals."
- **Financial Health**: "Get the quarterly balance sheet for Microsoft."
- **Performance Metrics**: "What are the key financial metrics for Tesla from the stock info?"
- **Trend Analysis**: "Compare the quarterly income statements of Amazon and Google."
- **Cash Flow Analysis**: "Show me the annual cash flow statement for NVIDIA."

### Market Research

- **News Analysis**: "Get the latest news articles about Meta Platforms."
- **Institutional Activity**: "Show me the institutional holders of Apple stock."
- **Insider Trading**: "What are the recent insider transactions for Tesla?"
- **Options Analysis**: "Get the options chain for SPY with expiration date 2024-06-21 for calls."
- **Analyst Coverage**: "What are the analyst recommendations for Amazon over the last 3 months?"

### Investment Research

- "Create a comprehensive analysis of Microsoft's financial health using their latest quarterly financial statements."
- "Compare the dividend history and stock splits of Coca-Cola and PepsiCo."
- "Analyze the institutional ownership changes in Tesla over the past year."
- "Generate a report on the options market activity for Apple stock with expiration in 30 days."
- "Summarize the latest analyst upgrades and downgrades in the tech sector over the last 6 months."

## Requirements

- Python 3.11 or higher
- Dependencies as listed in `pyproject.toml`, including:
  - mcp
  - yfinance
  - pandas
  - pydantic
  - and other packages for data processing

## Installation

### From PyPI (Recommended)

Install the package directly from PyPI:

```bash
pip install yfin-mcp
```

### From Source

1. Clone this repository:
   ```bash
   git clone https://github.com/fritzprix/yahoo-finance-mcp.git
   cd yahoo-finance-mcp
   ```

2. Create and activate a virtual environment and install dependencies:
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv pip install -e .
   ```

## Usage

### Integration with Claude for Desktop

After installing the package, you can integrate it with Claude for Desktop:

1. **Install the package** (if not already installed):
   ```bash
   pip install yfin-mcp
   ```

2. **Configure Claude Desktop**:
   - MacOS: Edit `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: Edit `%APPDATA%\Claude\claude_desktop_config.json`

3. **Add the server configuration**:

   **Using uvx (Recommended - No installation needed)**:
   ```json
   {
     "mcpServers": {
       "yfinance": {
         "command": "uvx",
         "args": ["yfin-mcp"]
       }
     }
   }
   ```

   **Using Python directly (if installed via pip)**:
   ```json
   {
     "mcpServers": {
       "yfinance": {
         "command": "python",
         "args": ["-m", "yfin_mcp"]
       }
     }
   }
   ```

   **For development/source installation**:
   - macOS:
     ```json
     {
       "mcpServers": {
         "yfinance": {
           "command": "uv",
           "args": [
             "--directory",
             "/ABSOLUTE/PATH/TO/yahoo-finance-mcp",
             "run",
             "server.py"
           ]
         }
       }
     }
     ```
   - Windows:
     ```json
     {
       "mcpServers": {
         "yfinance": {
           "command": "uv",
           "args": [
             "--directory",
             "C:\\ABSOLUTE\\PATH\\TO\\yahoo-finance-mcp",
             "run",
             "server.py"
           ]
         }
       }
     }
     ```

4. **Restart Claude for Desktop**

### Development Mode

For testing with MCP Inspector:

```bash
# From source
uv run yfin-mcp

# Or if installed via pip
python -m yfin_mcp
```

## Publishing to PyPI

To build and publish the package, use the provided scripts. You can optionally provide an argument to bump the version:

### Windows
```bash
# Just build and publish current version
publish_package.bat

# Bump version and then publish
publish_package.bat patch
publish_package.bat minor
publish_package.bat major
```

### macOS/Linux
```bash
chmod +x publish_package.sh

# Just build and publish current version
./publish_package.sh

# Bump version and then publish
./publish_package.sh patch
./publish_package.sh minor
./publish_package.sh major
```

> [!NOTE]
> The scripts will build the package into the `dist/` directory and then use `twine` to upload it. Ensure you have your PyPI credentials configured in `~/.pypirc` (or `%HOME%\.pypirc` on Windows) or set the `TWINE_PASSWORD` environment variable.


## Troubleshooting

### [ERROR] os error 32: Process cannot access the file
If you see this error when running `publish_package.bat` or `uv build`, it means the MCP server is still running and locking the executable.
1. **Close Claude Desktop** or any app using the yfinance MCP server.
2. Stop any running **MCP Inspector** instances.
3. If the error persists, manually kill the processes:
   ```bash
   taskkill /F /IM yfin-mcp.exe /T
   taskkill /F /IM python.exe /T
   ```

## License

MIT License

**Original Work**: Copyright (c) 2025 AlexYoung  
**Fork Enhancements**: Copyright (c) 2026 SKTelecom

This project maintains the MIT License from the original [yahoo-finance-mcp](https://github.com/Alex2Yang97/yahoo-finance-mcp) project. All enhancements (pagination, caching, export) are also released under MIT License.

See [LICENSE](LICENSE) file for full details.


