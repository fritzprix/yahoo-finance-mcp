"""Simple manual test for key functionality"""
import asyncio
import sys
sys.path.insert(0, '.')

# Import server module
import server

async def quick_test():
    print("=" * 70)
    print("QUICK VERIFICATION TEST")
    print("=" * 70)
    
    # Test 1: Stock info with field filtering
    print("\n1. Testing get_stock_info with field filtering...")
    try:
        result = await server.get_stock_info("AAPL", fields=["currentPrice", "marketCap"])
        print("✅ Stock info works")
        print(f"   Output length: {len(result)} chars")
        print(f"   Has cache info: {'CACHE' in result}")
        print(f"   Sample: {result[:200]}...")
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    # Test 2: Historical prices with pagination
    print("\n2. Testing get_historical_stock_prices with pagination...")
    try:
        result = await server.get_historical_stock_prices("AAPL", period="5d", page=1)
        print("✅ Historical prices work")
        print(f"   Output length: {len(result)} chars")
        print(f"   Has pagination: {'PAGE' in result}")
        print(f"   Has token count: {'tokens:' in result}")
        print(f"   Has cache info: {'CACHE' in result}")
        print(f"   Sample: {result[:300]}...")
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    # Test 3: News with pagination
    print("\n3. Testing get_yahoo_finance_news...")
    try:
        result = await server.get_yahoo_finance_news("AAPL", page=1)
        print("✅ News works")
        print(f"   Output length: {len(result)} chars")
        print(f"   Has pagination: {'PAGE' in result}")
        print(f"   Sample: {result[:200]}...")
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    # Test 4: Cache functionality
    print("\n4. Testing cache (second call should be cached)...")
    try:
        result1 = await server.get_stock_info("MSFT", fields=["currentPrice"])
        is_cached1 = "cached" in result1.lower()
        
        result2 = await server.get_stock_info("MSFT", fields=["currentPrice"])
        is_cached2 = "cached" in result2.lower()
        
        print(f"   First call cached: {is_cached1}")
        print(f"   Second call cached: {is_cached2}")
        print(f"   ✅ Cache working: {not is_cached1 and is_cached2}")
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    print("\n" + "=" * 70)
    print("VERIFICATION COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(quick_test())
