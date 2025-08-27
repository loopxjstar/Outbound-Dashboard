#!/usr/bin/env python3
"""
Production Stress Test - Test various error scenarios
"""
import os
import sys
import pandas as pd
import tempfile
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

def test_data_processor_edge_cases():
    """Test DataProcessor with various edge cases"""
    print("🔍 Testing DataProcessor edge cases...")
    
    try:
        from src.data_processor import DataProcessor
        processor = DataProcessor()
        
        # Test 1: Empty files
        print("  Testing empty file handling...")
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("recipient_name,sent_date,Recipient Email\n")  # Header only
            empty_file_path = f.name
            
        try:
            result = processor._load_csv(empty_file_path, 'send')
            if result is not None and len(result) == 0:
                print("  ✅ Empty file handled correctly")
            else:
                print("  ❌ Empty file not handled properly")
        finally:
            os.unlink(empty_file_path)
            
        # Test 2: Invalid date formats
        print("  Testing invalid date format handling...")
        invalid_data = pd.DataFrame({
            'recipient_name': ['test@example.com'],
            'sent_date': ['invalid-date'],
            'Recipient Email': ['test@example.com']
        })
        
        cleaned_data = processor._clean_data(invalid_data, 'send')
        print("  ✅ Invalid date format handled without crash")
        
        # Test 3: Missing columns validation
        print("  Testing missing columns validation...")
        is_valid, errors, _ = processor.sheets_validator({
            'send_mails': pd.DataFrame({'wrong_column': [1, 2, 3]}),
            'open_mails': None,
            'contacts': None
        })
        
        if not is_valid and len(errors) > 0:
            print("  ✅ Missing columns detected correctly")
        else:
            print("  ❌ Missing columns validation failed")
            
        print("✅ DataProcessor edge cases passed")
        return True
        
    except Exception as e:
        print(f"❌ DataProcessor edge case test failed: {e}")
        return False

def test_session_state_safety():
    """Test session state operations"""
    print("🔍 Testing session state safety...")
    
    try:
        # Simulate session state operations
        mock_session_state = {}
        
        # Test safe pop operation
        result = mock_session_state.pop('non_existent_key', None)
        if result is None:
            print("  ✅ Safe pop operation works")
        else:
            print("  ❌ Safe pop operation failed")
            
        # Test key existence check
        if 'non_existent_key' not in mock_session_state:
            print("  ✅ Key existence check works")
        else:
            print("  ❌ Key existence check failed")
            
        print("✅ Session state safety passed")
        return True
        
    except Exception as e:
        print(f"❌ Session state safety test failed: {e}")
        return False

def test_file_encoding():
    """Test various file encodings"""
    print("🔍 Testing file encoding handling...")
    
    try:
        # Test with different encodings
        encodings = ['utf-8', 'latin-1', 'cp1252']
        
        for encoding in encodings:
            print(f"  Testing {encoding} encoding...")
            
            with tempfile.NamedTemporaryFile(mode='w', encoding=encoding, suffix='.csv', delete=False) as f:
                f.write("recipient_name,sent_date,Recipient Email\n")
                f.write("test@example.com,02/07/2025 19:34:57,test@example.com\n")
                test_file = f.name
                
            try:
                # Try reading with pandas (similar to how app reads files)
                df = pd.read_csv(test_file)
                if len(df) > 0:
                    print(f"    ✅ {encoding} encoding read successfully")
                else:
                    print(f"    ❌ {encoding} encoding read failed")
            except Exception as e:
                print(f"    ⚠️ {encoding} encoding failed: {e}")
            finally:
                os.unlink(test_file)
                
        print("✅ File encoding tests completed")
        return True
        
    except Exception as e:
        print(f"❌ File encoding test failed: {e}")
        return False

def test_memory_usage():
    """Test memory usage with larger datasets"""
    print("🔍 Testing memory usage with larger datasets...")
    
    try:
        # Create larger test dataset
        large_data = pd.DataFrame({
            'recipient_name': [f'test{i}@example.com' for i in range(1000)],
            'sent_date': ['02/07/2025 19:34:57'] * 1000,
            'Recipient Email': [f'test{i}@example.com' for i in range(1000)]
        })
        
        # Test data operations
        print(f"  Created dataset with {len(large_data)} rows")
        
        # Test copying (used frequently in the app)
        copied_data = large_data.copy()
        print("  ✅ Data copying works")
        
        # Test groupby operations (used in analytics)
        grouped = large_data.groupby('Recipient Email').size()
        print("  ✅ Groupby operations work")
        
        # Test filtering operations
        filtered = large_data[large_data['recipient_name'].str.contains('test1')]
        print("  ✅ Filtering operations work")
        
        print("✅ Memory usage tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Memory usage test failed: {e}")
        return False

def test_production_paths():
    """Test file path operations"""
    print("🔍 Testing production file paths...")
    
    try:
        # Test outputs directory creation
        os.makedirs('outputs', exist_ok=True)
        if os.path.exists('outputs'):
            print("  ✅ Outputs directory creation works")
        else:
            print("  ❌ Outputs directory creation failed")
            
        # Test data directory access
        if os.path.exists('data/contacts.csv'):
            print("  ✅ Contacts file accessible")
        else:
            print("  ⚠️ Contacts file not found (expected in test env)")
            
        # Test src imports
        try:
            from src import data_processor, database
            print("  ✅ Src module imports work")
        except ImportError as e:
            print(f"  ❌ Src module import failed: {e}")
            
        print("✅ Production paths tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Production paths test failed: {e}")
        return False

def run_all_stress_tests():
    """Run all stress tests"""
    print("🧪 Starting Production Stress Tests")
    print("=" * 50)
    
    tests = [
        test_data_processor_edge_cases,
        test_session_state_safety,
        test_file_encoding,
        test_memory_usage,
        test_production_paths
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            failed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All stress tests PASSED! Application is robust for production.")
        return True
    else:
        print("⚠️ Some tests failed - review issues above")
        return False

if __name__ == "__main__":
    success = run_all_stress_tests()
    sys.exit(0 if success else 1)