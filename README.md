# yfin-mcp - Yahoo Finance MCP Server

<div align="right">
  <a href="README.md">English</a> | <a href="README.zh.md">中文</a>
</div>

A high-performance Model Context Protocol (MCP) server that provides comprehensive financial data from Yahoo Finance with **intelligent pagination**, **caching**, and **LLM-optimized responses**.

## ✨ Key Features

- 🚀 **Intelligent Caching**: Reduces API calls by 50-80% with smart TTL-based caching
- 📄 **Token-Based Pagination**: Prevents context window overflow with 6K token limit per page
- 🤖 **LLM-Friendly Format**: Human-readable plain text output (resilient to truncation)
- 📥 **JSON Export**: Export full datasets for offline analysis
- ⚡ **High Performance**: Sub-millisecond response times for cached data
- 🔍 **Clear Navigation**: Intuitive pagination guidance for LLM agents

## 🆕 What's New in v1.0.0

- **Token-based pagination** prevents LLM context window overflow
- **Intelligent caching** with configurable TTL (5min-1hr)
- **Plain text formatting** with visual separators for better readability
- **JSON export** capability for all data endpoints
- **Field filtering** for stock info to reduce response size
- **Cache statistics** and age tracking

## Demo

![MCP Demo](assets/demo.gif)

## 📊 MCP Tools

The server exposes the following tools through the Model Context Protocol:

### Stock Information

| Tool | Description | Pagination | Cache TTL |
|------|-------------|------------|-----------|
| `get_historical_stock_prices` | Get historical OHLCV data with customizable period/interval | ✅ | 5 min |
| `get_stock_info` | Get comprehensive stock data with optional field filtering | ✅ | 5 min |
| `get_yahoo_finance_news` | Get latest news articles (10 per page) | ✅ | 5 min |
| `get_stock_actions` | Get stock dividends and splits history | ❌ | None |

### Financial Statements

| Tool | Description | Pagination | Cache TTL |
|------|-------------|------------|-----------|
| `get_financial_statement` | Get income statement, balance sheet, or cash flow | ❌ | 1 hour |
| `get_holder_info` | Get major holders, institutional holders, or insider transactions | ✅ | 1 hour |

### Options Data

| Tool | Description | Pagination | Cache TTL |
|------|-------------|------------|-----------|
| `get_option_expiration_dates` | Get available options expiration dates | ❌ | None |
| `get_option_chain` | Get options chain for specific expiration and type | ✅ | 5 min |

### Analyst Information

| Tool | Description | Pagination | Cache TTL |
|------|-------------|------------|-----------|
| `get_recommendations` | Get analyst recommendations or upgrades/downgrades | ✅ | 1 hour |

## 🎯 Real-World Use Cases

### Stock Analysis

- **Price Analysis**: "Show me AAPL historical prices for the last year with pagination"
- **Financial Health**: "Get Microsoft's quarterly balance sheet"
- **Performance Metrics**: "What are Tesla's key financial metrics? Filter to show only currentPrice, marketCap, and trailingPE"
- **Trend Analysis**: "Compare quarterly income statements of Amazon and Google"

### Market Research

- **News Analysis**: "Get the latest news about Meta (paginated, 10 per page)"
- **Institutional Activity**: "Show institutional holders of Apple stock with pagination"
- **Options Analysis**: "Get SPY call options expiring 2024-06-21, page 1"
- **Analyst Coverage**: "What are analyst recommendations for Amazon in the last 3 months?"

### Data Export

- **Full Dataset Export**: "Export all AAPL historical data from the last 5 years to aapl_5y.json"
- **Batch Analysis**: "Export institutional holders of MSFT to msft_holders.json"

## 🔧 Requirements

- Python 3.11 or higher
- Dependencies:
  - `mcp[cli]>=1.6.0`
  - `yfinance>=0.2.62`
  - `pandas`

## 📦 Installation

### Option 1: Install from PyPI (Recommended)

```bash
pip install yfin-mcp
```

### Option 2: Install with uvx (No installation required)

```bash
uvx yfin-mcp
```

### Option 3: Install from Source

```bash
git clone https://github.com/YOUR_USERNAME/yfin-mcp.git
cd yfin-mcp
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .
```

## 🚀 Usage

### Running the Server

```bash
# If installed from PyPI
python -m yfin_mcp.server

# Or with uvx
uvx yfin-mcp

# Or from source
uv run server.py
```

### Integration with Claude for Desktop

1. Install Claude for Desktop

2. Install `uv` if not already installed:
   ```bash
   # macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Windows
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

3. Open Claude for Desktop config:
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

4. **Option A: Using PyPI Package (Recommended)**

   ```json
   {
     "mcpServers": {
       "yfin": {
         "command": "uvx",
         "args": ["yfin-mcp"]
       }
     }
   }
   ```

5. **Option B: Using Local Source**

   - macOS/Linux:
     ```json
     {
       "mcpServers": {
         "yfin": {
           "command": "uv",
           "args": [
             "--directory",
             "/ABSOLUTE/PATH/TO/yfin-mcp",
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
         "yfin": {
           "command": "uv",
           "args": [
             "--directory",
             "C:\\ABSOLUTE\\PATH\\TO\\yfin-mcp",
             "run",
             "server.py"
           ]
         }
       }
     }
     ```

6. Restart Claude for Desktop

## 💡 Usage Examples

### Basic Pagination

```
Get historical stock prices for AAPL with period=max and page=1
```

**Response** (truncated):
```
═══════════════════════════════════════════════════════════════════
📊 HISTORICAL STOCK PRICES - AAPL (max, 1d)
═══════════════════════════════════════════════════════════════════

Date       | Open    | High    | Low     | Close   | Volume
-----------|---------|---------|---------|---------|------------
2024-01-02 | 184.35  | 186.40  | 183.92  | 185.64  | 82,488,200
...

───────────────────────────────────────────────────────────────────
📄 PAGE 1 of 10 | Showing items 1-50 of 487 total
📊 Estimated tokens: 5,234 / 6,000 max
───────────────────────────────────────────────────────────────────

🔍 NAVIGATION:
  • Next page: Use page=2 to see items 51-100
  • Export all data: Add export_path="./aapl_data.json"

💾 CACHE: Fresh data (not cached)
═══════════════════════════════════════════════════════════════════
```

### Field Filtering

```
Get stock info for AAPL with fields=["currentPrice", "marketCap", "trailingPE"]
```

### JSON Export

```
Get historical stock prices for AAPL with period=1y and export_path="./aapl_2024.json"
```

**Response**:
```
═══════════════════════════════════════════════════════════════════
✅ DATA EXPORTED SUCCESSFULLY
═══════════════════════════════════════════════════════════════════

📁 File: ./aapl_2024.json
📊 Size: 45.23 KB
📝 Items: 252

The complete dataset has been saved to the specified file.
═══════════════════════════════════════════════════════════════════
```

## 🏗️ Architecture

### Caching Strategy

- **Real-time data** (prices, options, news): 5-minute TTL
- **Fundamental data** (financials, holders, recommendations): 1-hour TTL
- **LRU eviction**: Max 100 cache entries
- **Thread-safe**: Concurrent access supported

### Pagination Algorithm

1. Estimate tokens per row from sample
2. Calculate items per page based on 6K token limit
3. Extract page slice from cached dataset
4. Format with headers, navigation, and metadata

## 📝 License

MIT

## 🙏 Acknowledgments

This project builds upon the original [yahoo-finance-mcp](https://github.com/Alex2Yang97/yahoo-finance-mcp) by Alex2Yang97, with significant enhancements for production use with LLM agents.

