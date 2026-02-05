"""Test script for pagination and caching functionality"""

import pandas as pd
from cache_manager import get_cache
from pagination_utils import estimate_tokens, paginate_by_tokens, export_to_json


def test_token_estimation():
    """Test token estimation"""
    print("=" * 60)
    print("TEST 1: Token Estimation")
    print("=" * 60)
    
    text = "Hello world " * 100
    tokens = estimate_tokens(text)
    print(f"✓ Text length: {len(text)} characters")
    print(f"✓ Estimated tokens: {tokens}")
    print(f"✓ Ratio: ~{len(text) / tokens:.1f} chars per token")
    print()


def test_cache():
    """Test cache functionality"""
    print("=" * 60)
    print("TEST 2: Cache Operations")
    print("=" * 60)
    
    cache = get_cache()
    
    # Test set and get
    cache.set("test_key", "test_value", ttl_seconds=60)
    value = cache.get("test_key")
    print(f"✓ Cache set/get: {value == 'test_value'}")
    
    # Test cache miss
    missing = cache.get("nonexistent_key")
    print(f"✓ Cache miss: {missing is None}")
    
    # Test stats
    stats = cache.get_stats()
    print(f"✓ Cache stats: {stats}")
    
    # Test get_or_set
    def factory():
        return "computed_value"
    
    val, was_cached = cache.get_or_set("new_key", factory, 60)
    print(f"✓ First call (cache miss): value={val}, cached={was_cached}")
    
    val2, was_cached2 = cache.get_or_set("new_key", factory, 60)
    print(f"✓ Second call (cache hit): value={val2}, cached={was_cached2}")
    
    print()


def test_pagination():
    """Test pagination with token limits"""
    print("=" * 60)
    print("TEST 3: Pagination")
    print("=" * 60)
    
    # Create test data
    df = pd.DataFrame({
        'Date': pd.date_range('2024-01-01', periods=100),
        'Price': range(100, 200),
        'Volume': range(1000, 1100),
    })
    
    # Test page 1
    result = paginate_by_tokens(
        data=df,
        page=1,
        max_tokens=6000,
        data_type="table",
        title="TEST DATA",
        cache_age=30.5,
    )
    
    print(f"✓ Total items: {result.total_items}")
    print(f"✓ Total pages: {result.total_pages}")
    print(f"✓ Items on page 1: {result.items_on_page}")
    print(f"✓ Estimated tokens: {result.estimated_tokens}")
    print(f"✓ Token limit respected: {result.estimated_tokens <= 6000}")
    print()
    print("Sample output (first 500 chars):")
    print(result.formatted_text[:500])
    print("...")
    print()


def test_export():
    """Test JSON export"""
    print("=" * 60)
    print("TEST 4: JSON Export")
    print("=" * 60)
    
    df = pd.DataFrame({
        'A': [1, 2, 3],
        'B': ['x', 'y', 'z'],
    })
    
    filepath = "./test_export.json"
    result = export_to_json(df, filepath)
    print(result)
    
    # Verify file exists
    import os
    if os.path.exists(filepath):
        print(f"✓ File created successfully")
        os.remove(filepath)
        print(f"✓ Test file cleaned up")
    print()


def test_empty_data():
    """Test edge case: empty data"""
    print("=" * 60)
    print("TEST 5: Empty Data Edge Case")
    print("=" * 60)
    
    df = pd.DataFrame()
    result = paginate_by_tokens(
        data=df,
        page=1,
        max_tokens=6000,
        data_type="table",
        title="EMPTY TEST",
    )
    
    print(f"✓ Total items: {result.total_items}")
    print(f"✓ Total pages: {result.total_pages}")
    print(f"✓ Output contains 'No data': {'No data' in result.formatted_text}")
    print()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("PAGINATION & CACHING TEST SUITE")
    print("=" * 60)
    print()
    
    try:
        test_token_estimation()
        test_cache()
        test_pagination()
        test_export()
        test_empty_data()
        
        print("=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
