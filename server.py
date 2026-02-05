import json
from enum import Enum
from typing import Optional

import pandas as pd
import yfinance as yf
from mcp.server.fastmcp import FastMCP

from cache_manager import get_cache
from pagination_utils import paginate_by_tokens, export_to_json


# Define an enum for the type of financial statement
class FinancialType(str, Enum):
    income_stmt = "income_stmt"
    quarterly_income_stmt = "quarterly_income_stmt"
    balance_sheet = "balance_sheet"
    quarterly_balance_sheet = "quarterly_balance_sheet"
    cashflow = "cashflow"
    quarterly_cashflow = "quarterly_cashflow"


class HolderType(str, Enum):
    major_holders = "major_holders"
    institutional_holders = "institutional_holders"
    mutualfund_holders = "mutualfund_holders"
    insider_transactions = "insider_transactions"
    insider_purchases = "insider_purchases"
    insider_roster_holders = "insider_roster_holders"


class RecommendationType(str, Enum):
    recommendations = "recommendations"
    upgrades_downgrades = "upgrades_downgrades"


# Initialize FastMCP server
yfinance_server = FastMCP(
    "yfinance",
    instructions="""
# Yahoo Finance MCP Server

This server is used to get information about a given ticker symbol from yahoo finance.

Available tools:
- get_historical_stock_prices: Get historical stock prices for a given ticker symbol from yahoo finance. Include the following information: Date, Open, High, Low, Close, Volume, Adj Close.
- get_stock_info: Get stock information for a given ticker symbol from yahoo finance. Include the following information: Stock Price & Trading Info, Company Information, Financial Metrics, Earnings & Revenue, Margins & Returns, Dividends, Balance Sheet, Ownership, Analyst Coverage, Risk Metrics, Other.
- get_yahoo_finance_news: Get news for a given ticker symbol from yahoo finance.
- get_stock_actions: Get stock dividends and stock splits for a given ticker symbol from yahoo finance.
- get_financial_statement: Get financial statement for a given ticker symbol from yahoo finance. You can choose from the following financial statement types: income_stmt, quarterly_income_stmt, balance_sheet, quarterly_balance_sheet, cashflow, quarterly_cashflow.
- get_holder_info: Get holder information for a given ticker symbol from yahoo finance. You can choose from the following holder types: major_holders, institutional_holders, mutualfund_holders, insider_transactions, insider_purchases, insider_roster_holders.
- get_option_expiration_dates: Fetch the available options expiration dates for a given ticker symbol.
- get_option_chain: Fetch the option chain for a given ticker symbol, expiration date, and option type.
- get_recommendations: Get recommendations or upgrades/downgrades for a given ticker symbol from yahoo finance. You can also specify the number of months back to get upgrades/downgrades for, default is 12.
""",
)


@yfinance_server.tool(
    name="get_historical_stock_prices",
    description="""Get historical stock prices for a given ticker symbol from yahoo finance. Include the following information: Date, Open, High, Low, Close, Volume, Adj Close.
Args:
    ticker: str
        The ticker symbol of the stock to get historical prices for, e.g. "AAPL"
    period : str
        Valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
        Either Use period parameter or use start and end
        Default is "1mo"
    interval : str
        Valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo
        Intraday data cannot extend last 60 days
        Default is "1d"
    page : int
        Page number for pagination (1-indexed). Default is 1
    export_path : str (optional)
        If provided, exports the full dataset to JSON file at this path and returns confirmation message
""",
)
async def get_historical_stock_prices(
    ticker: str, 
    period: str = "1mo", 
    interval: str = "1d",
    page: int = 1,
    export_path: Optional[str] = None,
) -> str:
    """Get historical stock prices for a given ticker symbol

    Args:
        ticker: str
            The ticker symbol of the stock to get historical prices for, e.g. "AAPL"
        period : str
            Valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
            Either Use period parameter or use start and end
            Default is "1mo"
        interval : str
            Valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo
            Intraday data cannot extend last 60 days
            Default is "1d"
        page : int
            Page number for pagination (1-indexed)
        export_path : str (optional)
            If provided, exports the full dataset to JSON file
    """
    cache = get_cache()
    cache_key = cache._generate_key(
        "get_historical_stock_prices",
        ticker=ticker,
        period=period,
        interval=interval,
    )
    
    # Try to get from cache
    def fetch_data():
        company = yf.Ticker(ticker)
        try:
            if company.isin is None:
                print(f"Company ticker {ticker} not found.")
                return None
        except Exception as e:
            print(f"Error: getting historical stock prices for {ticker}: {e}")
            return None

        # If the company is found, get the historical data
        hist_data = company.history(period=period, interval=interval)
        hist_data = hist_data.reset_index(names="Date")
        return hist_data
    
    # Get data (from cache or fetch)
    hist_data, was_cached = cache.get_or_set(
        cache_key,
        fetch_data,
        ttl_seconds=300  # 5 minutes for price data
    )
    
    if hist_data is None:
        return f"Company ticker {ticker} not found."
    
    if hist_data.empty:
        return f"No historical data found for {ticker} with period={period}, interval={interval}"
    
    # Handle export
    if export_path:
        return export_to_json(hist_data, export_path)
    
    # Get cache age
    cache_age = cache.get_age(cache_key)
    
    # Paginate and format
    title = f"HISTORICAL STOCK PRICES - {ticker.upper()} ({period}, {interval})"
    result = paginate_by_tokens(
        data=hist_data,
        page=page,
        max_tokens=6000,
        data_type="table",
        title=title,
        cache_age=cache_age,
    )
    
    return result.formatted_text


@yfinance_server.tool(
    name="get_stock_info",
    description="""Get stock information for a given ticker symbol from yahoo finance. Include the following information:
Stock Price & Trading Info, Company Information, Financial Metrics, Earnings & Revenue, Margins & Returns, Dividends, Balance Sheet, Ownership, Analyst Coverage, Risk Metrics, Other.

Args:
    ticker: str
        The ticker symbol of the stock to get information for, e.g. "AAPL"
    fields: list of str (optional)
        Specific fields to return. If not provided, returns all fields. Common fields: currentPrice, marketCap, volume, previousClose, open, dayHigh, dayLow, fiftyTwoWeekHigh, fiftyTwoWeekLow, dividendYield, trailingPE, forwardPE, beta, etc.
    page : int
        Page number for pagination (1-indexed). Default is 1. Only used when fields is not specified.
    export_path : str (optional)
        If provided, exports the full dataset to JSON file at this path
""",
)
async def get_stock_info(
    ticker: str,
    fields: Optional[list] = None,
    page: int = 1,
    export_path: Optional[str] = None,
) -> str:
    """Get stock information for a given ticker symbol"""
    
    cache = get_cache()
    cache_key = cache._generate_key(
        "get_stock_info",
        ticker=ticker,
    )

    def fetch_data():
        company = yf.Ticker(ticker)
        try:
            if company.isin is None:
                print(f"Company ticker {ticker} not found.")
                return None
        except Exception as e:
            print(f"Error: getting stock information for {ticker}: {e}")
            return None
        return company.info
    
    # Get data (from cache or fetch)
    info, was_cached = cache.get_or_set(
        cache_key,
        fetch_data,
        ttl_seconds=300  # 5 minutes for stock info
    )
    
    if info is None:
        return f"Company ticker {ticker} not found."
    
    # Filter fields if specified
    if fields:
        filtered_info = {k: info.get(k, "N/A") for k in fields}
        info_to_display = filtered_info
    else:
        info_to_display = info
    
    # Handle export
    if export_path:
        return export_to_json(info_to_display, export_path)
    
    # Get cache age
    cache_age = cache.get_age(cache_key)
    
    # Format as plain text
    title = f"STOCK INFORMATION - {ticker.upper()}"
    if fields:
        title += f" (Filtered: {len(fields)} fields)"
    
    result = paginate_by_tokens(
        data=info_to_display,
        page=page,
        max_tokens=6000,
        data_type="dict",
        title=title,
        cache_age=cache_age,
    )
    
    return result.formatted_text


@yfinance_server.tool(
    name="get_yahoo_finance_news",
    description="""Get news for a given ticker symbol from yahoo finance.

Args:
    ticker: str
        The ticker symbol of the stock to get news for, e.g. "AAPL"
    page : int
        Page number for pagination (1-indexed). Default is 1
    export_path : str (optional)
        If provided, exports the full dataset to JSON file at this path
""",
)
async def get_yahoo_finance_news(
    ticker: str,
    page: int = 1,
    export_path: Optional[str] = None,
) -> str:
    """Get news for a given ticker symbol

    Args:
        ticker: str
            The ticker symbol of the stock to get news for, e.g. "AAPL"
        page: Page number for pagination
        export_path: Optional path to export full data as JSON
    """
    cache = get_cache()
    cache_key = cache._generate_key(
        "get_yahoo_finance_news",
        ticker=ticker,
    )

    def fetch_data():
        company = yf.Ticker(ticker)
        try:
            if company.isin is None:
                print(f"Company ticker {ticker} not found.")
                return None
        except Exception as e:
            print(f"Error: getting news for {ticker}: {e}")
            return None

        # If the company is found, get the news
        try:
            news = company.news
        except Exception as e:
            print(f"Error: getting news for {ticker}: {e}")
            return None

        news_list = []
        for news_item in news:
            if news_item.get("content", {}).get("contentType", "") == "STORY":
                title = news_item.get("content", {}).get("title", "")
                summary = news_item.get("content", {}).get("summary", "")
                description = news_item.get("content", {}).get("description", "")
                url = news_item.get("content", {}).get("canonicalUrl", {}).get("url", "")
                news_list.append({
                    "title": title,
                    "summary": summary,
                    "description": description,
                    "url": url,
                })
        return news_list
    
    # Get data (from cache or fetch)
    news_list, was_cached = cache.get_or_set(
        cache_key,
        fetch_data,
        ttl_seconds=300  # 5 minutes for news
    )
    
    if news_list is None:
        return f"Company ticker {ticker} not found."
    
    if not news_list:
        return f"No news found for company that searched with {ticker} ticker."
    
    # Handle export
    if export_path:
        return export_to_json(news_list, export_path)
    
    # Get cache age
    cache_age = cache.get_age(cache_key)
    
    # Format news items as text (custom formatting for readability)
    output_lines = [
        "═" * 70,
        f"📰 YAHOO FINANCE NEWS - {ticker.upper()}",
        "═" * 70,
        "",
    ]
    
    # Calculate items for this page (10 per page for news)
    items_per_page = 10
    total_items = len(news_list)
    total_pages = (total_items + items_per_page - 1) // items_per_page
    page = max(1, min(page, total_pages))
    
    start_idx = (page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, total_items)
    
    page_news = news_list[start_idx:end_idx]
    
    for i, news_item in enumerate(page_news, start=start_idx + 1):
        output_lines.append(f"[{i}] {news_item['title']}")
        if news_item['summary']:
            output_lines.append(f"    Summary: {news_item['summary']}")
        if news_item['description']:
            output_lines.append(f"    Description: {news_item['description']}")
        output_lines.append(f"    URL: {news_item['url']}")
        output_lines.append("")
    
    # Add pagination info
    output_lines.append("─" * 70)
    output_lines.append(f"📄 PAGE {page} of {total_pages} | Showing items {start_idx + 1}-{end_idx} of {total_items} total")
    
    full_text = "\n".join(output_lines)
    from pagination_utils import estimate_tokens
    token_count = estimate_tokens(full_text)
    output_lines.append(f"📊 Estimated tokens: {token_count:,} / 6,000 max")
    output_lines.append("─" * 70)
    output_lines.append("")
    
    # Add navigation
    if page < total_pages:
        output_lines.append(f"🔍 Next page: Use page={page + 1}")
    if page > 1:
        output_lines.append(f"🔍 Previous page: Use page={page - 1}")
    output_lines.append('📥 Export all: Add export_path="./news.json"')
    output_lines.append("")
    
    # Add cache info
    if cache_age is not None:
        output_lines.append(f"💾 CACHE: Data cached (age: {cache_age:.0f} seconds)")
    else:
        output_lines.append("💾 CACHE: Fresh data (not cached)")
    
    output_lines.append("═" * 70)
    
    return "\n".join(output_lines)


@yfinance_server.tool(
    name="get_stock_actions",
    description="""Get stock dividends and stock splits for a given ticker symbol from yahoo finance.

Args:
    ticker: str
        The ticker symbol of the stock to get stock actions for, e.g. "AAPL"
""",
)
async def get_stock_actions(ticker: str) -> str:
    """Get stock dividends and stock splits for a given ticker symbol"""
    try:
        company = yf.Ticker(ticker)
    except Exception as e:
        print(f"Error: getting stock actions for {ticker}: {e}")
        return f"Error: getting stock actions for {ticker}: {e}"
    actions_df = company.actions
    actions_df = actions_df.reset_index(names="Date")
    return actions_df.to_json(orient="records", date_format="iso")


@yfinance_server.tool(
    name="get_financial_statement",
    description="""Get financial statement for a given ticker symbol from yahoo finance. You can choose from the following financial statement types: income_stmt, quarterly_income_stmt, balance_sheet, quarterly_balance_sheet, cashflow, quarterly_cashflow.

Args:
    ticker: str
        The ticker symbol of the stock to get financial statement for, e.g. "AAPL"
    financial_type: str
        The type of financial statement to get. You can choose from the following financial statement types: income_stmt, quarterly_income_stmt, balance_sheet, quarterly_balance_sheet, cashflow, quarterly_cashflow.
    export_path : str (optional)
        If provided, exports the full dataset to JSON file at this path
""",
)
async def get_financial_statement(
    ticker: str, 
    financial_type: str,
    export_path: Optional[str] = None,
) -> str:
    """Get financial statement for a given ticker symbol"""

    cache = get_cache()
    cache_key = cache._generate_key(
        "get_financial_statement",
        ticker=ticker,
        financial_type=financial_type,
    )

    def fetch_data():
        company = yf.Ticker(ticker)
        try:
            if company.isin is None:
                print(f"Company ticker {ticker} not found.")
                return None
        except Exception as e:
            print(f"Error: getting financial statement for {ticker}: {e}")
            return None

        if financial_type == FinancialType.income_stmt:
            return company.income_stmt
        elif financial_type == FinancialType.quarterly_income_stmt:
            return company.quarterly_income_stmt
        elif financial_type == FinancialType.balance_sheet:
            return company.balance_sheet
        elif financial_type == FinancialType.quarterly_balance_sheet:
            return company.quarterly_balance_sheet
        elif financial_type == FinancialType.cashflow:
            return company.cashflow
        elif financial_type == FinancialType.quarterly_cashflow:
            return company.quarterly_cashflow
        else:
            return "INVALID_TYPE"
    
    # Get data (from cache or fetch)
    financial_statement, was_cached = cache.get_or_set(
        cache_key,
        fetch_data,
        ttl_seconds=3600  # 1 hour for financial statements
    )
    
    if financial_statement is None:
        return f"Company ticker {ticker} not found."
    
    if financial_statement == "INVALID_TYPE":
        return f"Error: invalid financial type {financial_type}. Please use one of the following: {FinancialType.income_stmt}, {FinancialType.quarterly_income_stmt}, {FinancialType.balance_sheet}, {FinancialType.quarterly_balance_sheet}, {FinancialType.cashflow}, {FinancialType.quarterly_cashflow}."

    # Create a list to store all the json objects
    result = []

    # Loop through each column (date)
    for column in financial_statement.columns:
        if isinstance(column, pd.Timestamp):
            date_str = column.strftime("%Y-%m-%d")  # Format as YYYY-MM-DD
        else:
            date_str = str(column)

        # Create a dictionary for each date
        date_obj = {"date": date_str}

        # Add each metric as a key-value pair
        for index, value in financial_statement[column].items():
            # Add the value, handling NaN values
            date_obj[index] = None if pd.isna(value) else value

        result.append(date_obj)

    # Handle export
    if export_path:
        return export_to_json(result, export_path)
    
    # Get cache age
    cache_age = cache.get_age(cache_key)
    
    # Format as plain text (financial statements are typically small, no pagination needed)
    title = f"FINANCIAL STATEMENT - {ticker.upper()} ({financial_type})"
    from pagination_utils import paginate_by_tokens
    formatted_result = paginate_by_tokens(
        data=result,
        page=1,
        max_tokens=6000,
        data_type="table",
        title=title,
        cache_age=cache_age,
    )
    
    return formatted_result.formatted_text


@yfinance_server.tool(
    name="get_holder_info",
    description="""Get holder information for a given ticker symbol from yahoo finance. You can choose from the following holder types: major_holders, institutional_holders, mutualfund_holders, insider_transactions, insider_purchases, insider_roster_holders.

Args:
    ticker: str
        The ticker symbol of the stock to get holder information for, e.g. "AAPL"
    holder_type: str
        The type of holder information to get. You can choose from the following holder types: major_holders, institutional_holders, mutualfund_holders, insider_transactions, insider_purchases, insider_roster_holders.
    page : int
        Page number for pagination (1-indexed). Default is 1. Only applies to institutional_holders, insider_transactions, and insider_purchases.
    export_path : str (optional)
        If provided, exports the full dataset to JSON file at this path
""",
)
async def get_holder_info(
    ticker: str, 
    holder_type: str,
    page: int = 1,
    export_path: Optional[str] = None,
) -> str:
    """Get holder information for a given ticker symbol"""

    cache = get_cache()
    cache_key = cache._generate_key(
        "get_holder_info",
        ticker=ticker,
        holder_type=holder_type,
    )

    def fetch_data():
        company = yf.Ticker(ticker)
        try:
            if company.isin is None:
                print(f"Company ticker {ticker} not found.")
                return None
        except Exception as e:
            print(f"Error: getting holder info for {ticker}: {e}")
            return None

        if holder_type == HolderType.major_holders:
            return ("major_holders", company.major_holders.reset_index(names="metric"))
        elif holder_type == HolderType.institutional_holders:
            return ("institutional_holders", company.institutional_holders)
        elif holder_type == HolderType.mutualfund_holders:
            return ("mutualfund_holders", company.mutualfund_holders)
        elif holder_type == HolderType.insider_transactions:
            return ("insider_transactions", company.insider_transactions)
        elif holder_type == HolderType.insider_purchases:
            return ("insider_purchases", company.insider_purchases)
        elif holder_type == HolderType.insider_roster_holders:
            return ("insider_roster_holders", company.insider_roster_holders)
        else:
            return "INVALID_TYPE"
    
    # Get data (from cache or fetch)
    holder_data, was_cached = cache.get_or_set(
        cache_key,
        fetch_data,
        ttl_seconds=3600  # 1 hour for holder data (changes slowly)
    )
    
    if holder_data is None:
        return f"Company ticker {ticker} not found."
    
    if holder_data == "INVALID_TYPE":
        return f"Error: invalid holder type {holder_type}. Please use one of the following: {HolderType.major_holders}, {HolderType.institutional_holders}, {HolderType.mutualfund_holders}, {HolderType.insider_transactions}, {HolderType.insider_purchases}, {HolderType.insider_roster_holders}."
    
    holder_type_name, df = holder_data
    
    if df is None or df.empty:
        return f"No {holder_type} data found for {ticker}"
    
    # Handle export
    if export_path:
        return export_to_json(df, export_path)
    
    # Get cache age
    cache_age = cache.get_age(cache_key)
    
    # For major_holders, always show all (it's small)
    if holder_type == HolderType.major_holders:
        title = f"MAJOR HOLDERS - {ticker.upper()}"
        result = paginate_by_tokens(
            data=df,
            page=1,
            max_tokens=6000,
            data_type="table",
            title=title,
            cache_age=cache_age,
        )
        return result.formatted_text
    
    # For other types, use pagination
    title = f"{holder_type_name.upper().replace('_', ' ')} - {ticker.upper()}"
    result = paginate_by_tokens(
        data=df,
        page=page,
        max_tokens=6000,
        data_type="table",
        title=title,
        cache_age=cache_age,
    )
    
    return result.formatted_text


@yfinance_server.tool(
    name="get_option_expiration_dates",
    description="""Fetch the available options expiration dates for a given ticker symbol.

Args:
    ticker: str
        The ticker symbol of the stock to get option expiration dates for, e.g. "AAPL"
""",
)
async def get_option_expiration_dates(ticker: str) -> str:
    """Fetch the available options expiration dates for a given ticker symbol."""

    company = yf.Ticker(ticker)
    try:
        if company.isin is None:
            print(f"Company ticker {ticker} not found.")
            return f"Company ticker {ticker} not found."
    except Exception as e:
        print(f"Error: getting option expiration dates for {ticker}: {e}")
        return f"Error: getting option expiration dates for {ticker}: {e}"
    return json.dumps(company.options)


@yfinance_server.tool(
    name="get_option_chain",
    description="""Fetch the option chain for a given ticker symbol, expiration date, and option type.

Args:
    ticker: str
        The ticker symbol of the stock to get option chain for, e.g. "AAPL"
    expiration_date: str
        The expiration date for the options chain (format: 'YYYY-MM-DD')
    option_type: str
        The type of option to fetch ('calls' or 'puts')
    page : int
        Page number for pagination (1-indexed). Default is 1
    export_path : str (optional)
        If provided, exports the full dataset to JSON file at this path
""",
)
async def get_option_chain(
    ticker: str, 
    expiration_date: str, 
    option_type: str,
    page: int = 1,
    export_path: Optional[str] = None,
) -> str:
    """Fetch the option chain for a given ticker symbol, expiration date, and option type.

    Args:
        ticker: The ticker symbol of the stock
        expiration_date: The expiration date for the options chain (format: 'YYYY-MM-DD')
        option_type: The type of option to fetch ('calls' or 'puts')
        page: Page number for pagination
        export_path: Optional path to export full data as JSON

    Returns:
        str: Formatted plain text containing the option chain data
    """
    cache = get_cache()
    cache_key = cache._generate_key(
        "get_option_chain",
        ticker=ticker,
        expiration_date=expiration_date,
        option_type=option_type,
    )

    def fetch_data():
        company = yf.Ticker(ticker)
        try:
            if company.isin is None:
                print(f"Company ticker {ticker} not found.")
                return None
        except Exception as e:
            print(f"Error: getting option chain for {ticker}: {e}")
            return None

        # Check if the expiration date is valid
        if expiration_date not in company.options:
            return "INVALID_DATE"

        # Check if the option type is valid
        if option_type not in ["calls", "puts"]:
            return "INVALID_TYPE"

        # Get the option chain
        option_chain = company.option_chain(expiration_date)
        if option_type == "calls":
            return option_chain.calls
        else:
            return option_chain.puts
    
    # Get data (from cache or fetch)
    option_data, was_cached = cache.get_or_set(
        cache_key,
        fetch_data,
        ttl_seconds=300  # 5 minutes for options data
    )
    
    if option_data is None:
        return f"Company ticker {ticker} not found."
    
    if option_data == "INVALID_DATE":
        return f"Error: No options available for the date {expiration_date}. You can use `get_option_expiration_dates` to get the available expiration dates."
    
    if option_data == "INVALID_TYPE":
        return "Error: Invalid option type. Please use 'calls' or 'puts'."
    
    if option_data.empty:
        return f"No {option_type} options found for {ticker} expiring on {expiration_date}"
    
    # Handle export
    if export_path:
        return export_to_json(option_data, export_path)
    
    # Get cache age
    cache_age = cache.get_age(cache_key)
    
    # Paginate and format
    title = f"OPTION CHAIN - {ticker.upper()} {option_type.upper()} (Exp: {expiration_date})"
    result = paginate_by_tokens(
        data=option_data,
        page=page,
        max_tokens=6000,
        data_type="table",
        title=title,
        cache_age=cache_age,
    )
    
    return result.formatted_text


@yfinance_server.tool(
    name="get_recommendations",
    description="""Get recommendations or upgrades/downgrades for a given ticker symbol from yahoo finance. You can also specify the number of months back to get upgrades/downgrades for, default is 12.

Args:
    ticker: str
        The ticker symbol of the stock to get recommendations for, e.g. "AAPL"
    recommendation_type: str
        The type of recommendation to get. You can choose from the following recommendation types: recommendations, upgrades_downgrades.
    months_back: int
        The number of months back to get upgrades/downgrades for, default is 12.
    page : int
        Page number for pagination (1-indexed). Default is 1
    export_path : str (optional)
        If provided, exports the full dataset to JSON file at this path
""",
)
async def get_recommendations(
    ticker: str, 
    recommendation_type: str, 
    months_back: int = 12,
    page: int = 1,
    export_path: Optional[str] = None,
) -> str:
    """Get recommendations or upgrades/downgrades for a given ticker symbol"""
    
    cache = get_cache()
    cache_key = cache._generate_key(
        "get_recommendations",
        ticker=ticker,
        recommendation_type=recommendation_type,
        months_back=months_back,
    )

    def fetch_data():
        company = yf.Ticker(ticker)
        try:
            if company.isin is None:
                print(f"Company ticker {ticker} not found.")
                return None
        except Exception as e:
            print(f"Error: getting recommendations for {ticker}: {e}")
            return None
        
        try:
            if recommendation_type == RecommendationType.recommendations:
                return ("recommendations", company.recommendations)
            elif recommendation_type == RecommendationType.upgrades_downgrades:
                # Get the upgrades/downgrades based on the cutoff date
                upgrades_downgrades = company.upgrades_downgrades.reset_index()
                cutoff_date = pd.Timestamp.now() - pd.DateOffset(months=months_back)
                upgrades_downgrades = upgrades_downgrades[
                    upgrades_downgrades["GradeDate"] >= cutoff_date
                ]
                upgrades_downgrades = upgrades_downgrades.sort_values("GradeDate", ascending=False)
                # Get the first occurrence (most recent) for each firm
                latest_by_firm = upgrades_downgrades.drop_duplicates(subset=["Firm"])
                return ("upgrades_downgrades", latest_by_firm)
            else:
                return "INVALID_TYPE"
        except Exception as e:
            print(f"Error: getting recommendations for {ticker}: {e}")
            return None
    
    # Get data (from cache or fetch)
    rec_data, was_cached = cache.get_or_set(
        cache_key,
        fetch_data,
        ttl_seconds=3600  # 1 hour for recommendations (changes slowly)
    )
    
    if rec_data is None:
        return f"Company ticker {ticker} not found or no recommendation data available."
    
    if rec_data == "INVALID_TYPE":
        return f"Error: invalid recommendation type {recommendation_type}. Please use one of the following: {RecommendationType.recommendations}, {RecommendationType.upgrades_downgrades}."
    
    rec_type_name, df = rec_data
    
    if df is None or df.empty:
        return f"No {recommendation_type} data found for {ticker}"
    
    # Handle export
    if export_path:
        return export_to_json(df, export_path)
    
    # Get cache age
    cache_age = cache.get_age(cache_key)
    
    # Paginate and format
    title = f"{rec_type_name.upper().replace('_', ' ')} - {ticker.upper()}"
    if recommendation_type == RecommendationType.upgrades_downgrades:
        title += f" (Last {months_back} months)"
    
    result = paginate_by_tokens(
        data=df,
        page=page,
        max_tokens=6000,
        data_type="table",
        title=title,
        cache_age=cache_age,
    )
    
    return result.formatted_text


def main() -> None:
    """Main entry point for the server"""
    print("Starting Yahoo Finance MCP server...")
    yfinance_server.run(transport="stdio")


if __name__ == "__main__":
    main()
