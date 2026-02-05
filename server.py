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
""",
)
async def get_historical_stock_prices(
    ticker: str,
    period: str = "1mo",
    interval: str = "1d",
    page: int = 1,
    export_path: Optional[str] = None,
) -> str:
    """Get historical stock prices for a given ticker symbol with pagination

    Args:
        ticker: The ticker symbol, e.g. "AAPL"
        period: Valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max (default: "1mo")
        interval: Valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo (default: "1d")
        page: Page number for pagination (default: 1)
        export_path: Optional path to export full data as JSON file
    """
    cache = get_cache()
    cache_key = f"hist_{ticker}_{period}_{interval}"
    
    # Try to get from cache
    hist_data, cache_age = cache.get_or_set(
        cache_key,
        lambda: yf.Ticker(ticker).history(period=period, interval=interval),
        ttl_seconds=300  # 5 minutes for price data
    )
    
    if hist_data is None or hist_data.empty:
        return f"No historical data available for {ticker}"
    
    # Reset index to make Date a column
    hist_data = hist_data.reset_index()
    
    # Export if requested
    if export_path:
        return export_to_json(hist_data, export_path)
    
    # Paginate the response
    result = paginate_by_tokens(
        data=hist_data,
        page=page,
        max_tokens=6000,
        data_type="table",
        title=f"HISTORICAL STOCK PRICES - {ticker} ({period}, {interval})",
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
""",
)
async def get_stock_info(
    ticker: str,
    fields: Optional[list] = None,
    page: int = 1,
    export_path: Optional[str] = None,
) -> str:
    """Get stock information with optional field filtering and pagination"""
    cache = get_cache()
    cache_key = f"info_{ticker}"
    
    info, cache_age = cache.get_or_set(
        cache_key,
        lambda: yf.Ticker(ticker).info,
        ttl_seconds=300
    )
    
    if not info:
        return f"No information available for {ticker}"
    
    # Filter fields if specified
    info_to_display = {k: info.get(k) for k in fields if k in info} if fields else info
    
    if export_path:
        return export_to_json(info_to_display, export_path)
    
    result = paginate_by_tokens(
        data=info_to_display,
        page=page,
        max_tokens=6000,
        data_type="dict",
        title=f"STOCK INFO - {ticker}",
        cache_age=cache_age,
    )
    
    return result.formatted_text


@yfinance_server.tool(
    name="get_yahoo_finance_news",
    description="""Get news for a given ticker symbol from yahoo finance.

Args:
    ticker: str
        The ticker symbol of the stock to get news for, e.g. "AAPL"
""",
)
async def get_yahoo_finance_news(
    ticker: str,
    page: int = 1,
    export_path: Optional[str] = None,
) -> str:
    """Get news for a given ticker symbol with pagination"""
    cache = get_cache()
    cache_key = f"news_{ticker}"
    
    news_data, cache_age = cache.get_or_set(
        cache_key,
        lambda: yf.Ticker(ticker).news,
        ttl_seconds=300  # 5 minutes
    )
    
    if not news_data:
        return f"No news found for {ticker}"
    
    # Convert to structured format
    news_list = []
    for item in news_data:
        if item.get("content", {}).get("contentType", "") == "STORY":
            news_list.append({
                "title": item.get("content", {}).get("title", ""),
                "summary": item.get("content", {}).get("summary", ""),
                "url": item.get("content", {}).get("canonicalUrl", {}).get("url", ""),
                "provider": item.get("content", {}).get("provider", {}).get("displayName", "")
            })
    
    if not news_list:
        return f"No news articles found for {ticker}"
    
    if export_path:
        return export_to_json(news_list, export_path)
    
    result = paginate_by_tokens(
        data=pd.DataFrame(news_list),
        page=page,
        max_tokens=6000,
        data_type="table",
        title=f"YAHOO FINANCE NEWS - {ticker}",
        cache_age=cache_age,
    )
    
    return result.formatted_text


@yfinance_server.tool(
    name="get_stock_actions",
    description="""Get stock dividends and stock splits for a given ticker symbol from yahoo finance.

Args:
    ticker: str
        The ticker symbol of the stock to get stock actions for, e.g. "AAPL"
""",
)
async def get_stock_actions(
    ticker: str,
    page: int = 1,
    export_path: Optional[str] = None,
) -> str:
    """Get stock dividends and splits with pagination"""
    cache = get_cache()
    cache_key = f"actions_{ticker}"
    
    actions_data, cache_age = cache.get_or_set(
        cache_key,
        lambda: yf.Ticker(ticker).actions,
        ttl_seconds=3600  # 1 hour - less volatile
    )
    
    if actions_data is None or actions_data.empty:
        return f"No stock actions available for {ticker}"
    
    actions_data = actions_data.reset_index()
    
    if export_path:
        return export_to_json(actions_data, export_path)
    
    result = paginate_by_tokens(
        data=actions_data,
        page=page,
        max_tokens=6000,
        data_type="table",
        title=f"STOCK ACTIONS - {ticker}",
        cache_age=cache_age,
    )
    
    return result.formatted_text


@yfinance_server.tool(
    name="get_financial_statement",
    description="""Get financial statement for a given ticker symbol from yahoo finance. You can choose from the following financial statement types: income_stmt, quarterly_income_stmt, balance_sheet, quarterly_balance_sheet, cashflow, quarterly_cashflow.

Args:
    ticker: str
        The ticker symbol of the stock to get financial statement for, e.g. "AAPL"
    financial_type: str
        The type of financial statement to get. You can choose from the following financial statement types: income_stmt, quarterly_income_stmt, balance_sheet, quarterly_balance_sheet, cashflow, quarterly_cashflow.
""",
)
async def get_financial_statement(
    ticker: str,
    financial_type: str,
    export_path: Optional[str] = None,
) -> str:
    """Get financial statement with caching and export"""
    cache = get_cache()
    cache_key = f"financial_{ticker}_{financial_type}"
    
    def fetch_statement():
        company = yf.Ticker(ticker)
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
            return None
    
    financial_statement, cache_age = cache.get_or_set(
        cache_key,
        fetch_statement,
        ttl_seconds=3600  # 1 hour
    )
    
    if financial_statement is None or financial_statement.empty:
        return f"No financial statement data available for {ticker} ({financial_type})"
    
    # Convert to list of dicts for export
    result = []
    for column in financial_statement.columns:
        if isinstance(column, pd.Timestamp):
            date_str = column.strftime("%Y-%m-%d")
        else:
            date_str = str(column)
        
        date_obj = {"date": date_str}
        for index, value in financial_statement[column].items():
            date_obj[index] = None if pd.isna(value) else value
        result.append(date_obj)
    
    if export_path:
        return export_to_json(result, export_path)
    
    # Format as plain text table
    df = pd.DataFrame(result)
    result_text = paginate_by_tokens(
        data=df,
        page=1,  # Financial statements are small, no pagination needed
        max_tokens=6000,
        data_type="table",
        title=f"FINANCIAL STATEMENT - {ticker} ({financial_type})",
        cache_age=cache_age,
    )
    
    return result_text.formatted_text


@yfinance_server.tool(
    name="get_holder_info",
    description="""Get holder information for a given ticker symbol from yahoo finance. You can choose from the following holder types: major_holders, institutional_holders, mutualfund_holders, insider_transactions, insider_purchases, insider_roster_holders.

Args:
    ticker: str
        The ticker symbol of the stock to get holder information for, e.g. "AAPL"
    holder_type: str
        The type of holder information to get. You can choose from the following holder types: major_holders, institutional_holders, mutualfund_holders, insider_transactions, insider_purchases, insider_roster_holders.
""",
)
async def get_holder_info(
    ticker: str,
    holder_type: str,
    page: int = 1,
    export_path: Optional[str] = None,
) -> str:
    """Get holder information with pagination"""
    cache = get_cache()
    cache_key = f"holder_{ticker}_{holder_type}"
    
    def fetch_holder_data():
        company = yf.Ticker(ticker)
        if holder_type == HolderType.major_holders:
            return company.major_holders.reset_index(names="metric")
        elif holder_type == HolderType.institutional_holders:
            return company.institutional_holders
        elif holder_type == HolderType.mutualfund_holders:
            return company.mutualfund_holders
        elif holder_type == HolderType.insider_transactions:
            return company.insider_transactions
        elif holder_type == HolderType.insider_purchases:
            return company.insider_purchases
        elif holder_type == HolderType.insider_roster_holders:
            return company.insider_roster_holders
        else:
            return None
    
    holder_data, cache_age = cache.get_or_set(
        cache_key,
        fetch_holder_data,
        ttl_seconds=3600  # 1 hour
    )
    
    if holder_data is None or holder_data.empty:
        return f"No holder information available for {ticker} ({holder_type})"
    
    if export_path:
        return export_to_json(holder_data, export_path)
    
    result = paginate_by_tokens(
        data=holder_data,
        page=page,
        max_tokens=6000,
        data_type="table",
        title=f"HOLDER INFO - {ticker} ({holder_type})",
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
""",
)
async def get_option_chain(
    ticker: str,
    expiration_date: str,
    option_type: str,
    page: int = 1,
    export_path: Optional[str] = None,
) -> str:
    """Fetch option chain with pagination"""
    cache = get_cache()
    cache_key = f"options_{ticker}_{expiration_date}_{option_type}"
    
    def fetch_options():
        company = yf.Ticker(ticker)
        if expiration_date not in company.options:
            raise ValueError(f"No options for date {expiration_date}")
        if option_type not in ["calls", "puts"]:
            raise ValueError("Invalid option type")
        
        option_chain = company.option_chain(expiration_date)
        return option_chain.calls if option_type == "calls" else option_chain.puts
    
    try:
        option_data, cache_age = cache.get_or_set(
            cache_key,
            fetch_options,
            ttl_seconds=300  # 5 minutes - volatile
        )
    except ValueError as e:
        return f"Error: {str(e)}"
    
    if option_data is None or option_data.empty:
        return f"No option chain data available for {ticker}"
    
    if export_path:
        return export_to_json(option_data, export_path)
    
    result = paginate_by_tokens(
        data=option_data,
        page=page,
        max_tokens=6000,
        data_type="table",
        title=f"OPTION CHAIN - {ticker} ({option_type.upper()}, {expiration_date})",
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
""",
)
async def get_recommendations(
    ticker: str,
    recommendation_type: str,
    months_back: int = 12,
    page: int = 1,
    export_path: Optional[str] = None,
) -> str:
    """Get recommendations with pagination"""
    cache = get_cache()
    cache_key = f"recommendations_{ticker}_{recommendation_type}_{months_back}"
    
    def fetch_recommendations():
        company = yf.Ticker(ticker)
        if recommendation_type == RecommendationType.recommendations:
            return company.recommendations
        elif recommendation_type == RecommendationType.upgrades_downgrades:
            upgrades_downgrades = company.upgrades_downgrades.reset_index()
            cutoff_date = pd.Timestamp.now() - pd.DateOffset(months=months_back)
            upgrades_downgrades = upgrades_downgrades[
                upgrades_downgrades["GradeDate"] >= cutoff_date
            ]
            upgrades_downgrades = upgrades_downgrades.sort_values("GradeDate", ascending=False)
            return upgrades_downgrades.drop_duplicates(subset=["Firm"])
        else:
            return None
    
    try:
        rec_data, cache_age = cache.get_or_set(
            cache_key,
            fetch_recommendations,
            ttl_seconds=3600  # 1 hour
        )
    except Exception as e:
        return f"Error: getting recommendations for {ticker}: {e}"
    
    if rec_data is None or rec_data.empty:
        return f"No recommendations available for {ticker}"
    
    if export_path:
        return export_to_json(rec_data, export_path)
    
    result = paginate_by_tokens(
        data=rec_data,
        page=page,
        max_tokens=6000,
        data_type="table",
        title=f"RECOMMENDATIONS - {ticker} ({recommendation_type})",
        cache_age=cache_age,
    )
    
    return result.formatted_text


def main() -> None:
    """Main entry point for the server"""
    print("Starting Yahoo Finance MCP server...")
    yfinance_server.run(transport="stdio")


if __name__ == "__main__":
    main()
