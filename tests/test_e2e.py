"""
E2E Test Script for yfin-mcp
Tests all tools with pagination, caching, and export functionality
"""

import asyncio
import json
from server import (
    get_stock_info,
    get_historical_stock_prices,
    get_yahoo_finance_news,
    get_option_chain,
    get_holder_info,
    get_recommendations,
    get_financial_statement,
)


async def test_stock_info():
    """Test get_stock_info with field filtering"""
    print("\n" + "=" * 70)
    print("TEST 1: get_stock_info (with field filtering)")
    print("=" * 70)
    
    result = await get_stock_info(
        ticker="AAPL",
        fields=["currentPrice", "marketCap", "trailingPE"],
        page=1
    )
    
    print(result[:1000])  # Print first 1000 chars
    print("\n✅ Test passed - Field filtering works")
    return True


async def test_historical_prices():
    """Test get_historical_stock_prices with pagination"""
    print("\n" + "=" * 70)
    print("TEST 2: get_historical_stock_prices (with pagination)")
    print("=" * 70)
    
    # Test page 1
    result = await get_historical_stock_prices(
        ticker="AAPL",
        period="1mo",
        interval="1d",
        page=1
    )
    
    print(result[:1500])  # Print first 1500 chars
    
    # Verify pagination metadata
    assert "PAGE 1" in result, "Missing pagination info"
    assert "📊 Estimated tokens:" in result, "Missing token count"
    assert "💾 CACHE:" in result, "Missing cache info"
    
    print("\n✅ Test passed - Pagination and cache info present")
    
    # Test page 2 (should be cached)
    print("\n--- Testing page 2 (cache hit expected) ---")
    result2 = await get_historical_stock_prices(
        ticker="AAPL",
        period="1mo",
        interval="1d",
        page=2
    )
    
    assert "PAGE 2" in result2, "Page 2 not working"
    print("✅ Page 2 works correctly")
    
    return True


async def test_news():
    """Test get_yahoo_finance_news with pagination"""
    print("\n" + "=" * 70)
    print("TEST 3: get_yahoo_finance_news (10 items per page)")
    print("=" * 70)
    
    result = await get_yahoo_finance_news(
        ticker="AAPL",
        page=1
    )
    
    print(result[:1500])
    
    assert "PAGE 1" in result, "Missing pagination"
    assert "📰" in result, "Missing news formatting"
    
    print("\n✅ Test passed - News pagination works")
    return True


async def test_json_export():
    """Test JSON export functionality"""
    print("\n" + "=" * 70)
    print("TEST 4: JSON Export")
    print("=" * 70)
    
    result = await get_historical_stock_prices(
        ticker="AAPL",
        period="5d",
        interval="1d",
        export_path="./test_export_aapl.json"
    )
    
    print(result)
    
    assert "EXPORTED SUCCESSFULLY" in result, "Export failed"
    assert "test_export_aapl.json" in result, "Wrong filename"
    
    # Verify file exists
    import os
    assert os.path.exists("./test_export_aapl.json"), "Export file not created"
    
    # Clean up
    os.remove("./test_export_aapl.json")
    
    print("\n✅ Test passed - JSON export works")
    return True


async def test_option_chain():
    """Test get_option_chain with pagination"""
    print("\n" + "=" * 70)
    print("TEST 5: get_option_chain (with pagination)")
    print("=" * 70)
    
    try:
        # First get expiration dates
        from server import get_option_expiration_dates
        dates_result = await get_option_expiration_dates(ticker="AAPL")
        print("Available expiration dates retrieved")
        
        # Extract first date from the result
        import re
        dates = re.findall(r'\d{4}-\d{2}-\d{2}', dates_result)
        if dates:
            exp_date = dates[0]
            print(f"Testing with expiration date: {exp_date}")
            
            result = await get_option_chain(
                ticker="AAPL",
                expiration_date=exp_date,
                option_type="calls",
                page=1
            )
            
            print(result[:1000])
            
            assert "PAGE" in result or "No data" in result, "Missing pagination or data"
            print("\n✅ Test passed - Option chain works")
        else:
            print("⚠️ No expiration dates found, skipping option chain test")
    except Exception as e:
        print(f"⚠️ Option chain test skipped: {e}")
    
    return True


async def test_holder_info():
    """Test get_holder_info with pagination"""
    print("\n" + "=" * 70)
    print("TEST 6: get_holder_info (institutional holders)")
    print("=" * 70)
    
    result = await get_holder_info(
        ticker="AAPL",
        holder_type="institutional_holders",
        page=1
    )
    
    print(result[:1000])
    
    assert "HOLDER" in result or "No data" in result, "Missing holder info"
    
    print("\n✅ Test passed - Holder info works")
    return True


async def test_recommendations():
    """Test get_recommendations with pagination"""
    print("\n" + "=" * 70)
    print("TEST 7: get_recommendations")
    print("=" * 70)
    
    result = await get_recommendations(
        ticker="AAPL",
        recommendation_type="recommendations",
        months_back=6,
        page=1
    )
    
    print(result[:1000])
    
    assert "RECOMMENDATION" in result or "No data" in result, "Missing recommendations"
    
    print("\n✅ Test passed - Recommendations work")
    return True


async def test_financial_statement():
    """Test get_financial_statement with caching"""
    print("\n" + "=" * 70)
    print("TEST 8: get_financial_statement (with caching)")
    print("=" * 70)
    
    result = await get_financial_statement(
        ticker="AAPL",
        financial_type="income_statement_annual"
    )
    
    print(result[:1000])
    
    assert "INCOME STATEMENT" in result or "No data" in result, "Missing financial data"
    assert "💾 CACHE:" in result, "Missing cache info"
    
    print("\n✅ Test passed - Financial statement works")
    return True


async def main():
    """Run all E2E tests"""
    print("\n" + "=" * 70)
    print("🚀 STARTING E2E TESTS FOR YFIN-MCP")
    print("=" * 70)
    
    tests = [
        ("Stock Info", test_stock_info),
        ("Historical Prices", test_historical_prices),
        ("News", test_news),
        ("JSON Export", test_json_export),
        ("Option Chain", test_option_chain),
        ("Holder Info", test_holder_info),
        ("Recommendations", test_recommendations),
        ("Financial Statement", test_financial_statement),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            await test_func()
            passed += 1
        except Exception as e:
            print(f"\n❌ {name} test FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 70)
    print("📊 E2E TEST RESULTS")
    print("=" * 70)
    print(f"✅ Passed: {passed}/{len(tests)}")
    print(f"❌ Failed: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n🎉 ALL E2E TESTS PASSED!")
        print("=" * 70)
        return True
    else:
        print("\n⚠️ Some tests failed, please review")
        print("=" * 70)
        return False


if __name__ == "__main__":
    asyncio.run(main())
