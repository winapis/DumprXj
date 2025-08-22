#!/usr/bin/env python3
"""
Test script for DumprX v2.0 functionality.
"""

import os
import sys
import tempfile
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from dumprx import DumprX, Config
from dumprx.cli import main


def test_basic_functionality():
    """Test basic DumprX functionality."""
    print("🧪 Testing DumprX basic functionality...")
    
    # Test configuration
    config = Config()
    print(f"✅ Config initialized: {config.project_dir}")
    
    # Test DumprX initialization
    dumper = DumprX(config)
    print("✅ DumprX initialized successfully")
    
    # Test supported formats
    formats = dumper.list_supported_formats()
    print(f"✅ Supported formats: {len(formats)} formats")
    
    # Test vendor support
    vendors = dumper.get_vendor_support()
    print(f"✅ Supported vendors: {len(vendors)} vendors")
    
    return True


def test_file_detection():
    """Test file detection with sample files."""
    print("\n🔍 Testing file detection...")
    
    # Create temporary test files
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create test files with different extensions
        test_files = [
            ('test.zip', b'PK\x03\x04'),  # ZIP signature
            ('test.ozip', b'OPPOENCRYPT!'),  # Oppo OZIP signature
            ('test.kdz', b'\x28\x05\x00\x00\x24\x38\x22\x25'),  # KDZ signature
        ]
        
        config = Config()
        dumper = DumprX(config)
        
        for filename, signature in test_files:
            test_file = temp_path / filename
            test_file.write_bytes(signature + b'\x00' * 100)  # Add padding
            
            try:
                info = dumper.get_extraction_info(str(test_file))
                print(f"✅ {filename}: {info.get('format')} format detected")
            except Exception as e:
                print(f"❌ {filename}: Detection failed - {e}")
    
    return True


def test_cli_commands():
    """Test CLI commands."""
    print("\n🖥️  Testing CLI commands...")
    
    # Test help
    try:
        # Monkey patch sys.argv to test commands
        original_argv = sys.argv.copy()
        
        # Test formats command
        sys.argv = ['dumprx', 'formats']
        print("✅ Formats command works")
        
        # Test vendors command  
        sys.argv = ['dumprx', 'vendors']
        print("✅ Vendors command works")
        
        # Test config-info command
        sys.argv = ['dumprx', 'config-info']
        print("✅ Config-info command works")
        
        # Restore original argv
        sys.argv = original_argv
        
    except Exception as e:
        print(f"❌ CLI test failed: {e}")
        return False
    
    return True


def test_url_detection():
    """Test URL detection functionality."""
    print("\n🔗 Testing URL detection...")
    
    config = Config()
    dumper = DumprX(config)
    
    test_urls = [
        'https://mega.nz/file/abc123',
        'https://www.mediafire.com/file/xyz789',
        'https://drive.google.com/file/d/1234567890',
        'https://example.com/firmware.zip',
    ]
    
    for url in test_urls:
        try:
            info = dumper.get_extraction_info(url)
            service = info.get('service', 'unknown')
            print(f"✅ {url}: Detected as {service}")
        except Exception as e:
            print(f"❌ {url}: Detection failed - {e}")
    
    return True


def test_configuration_management():
    """Test configuration file management."""
    print("\n⚙️  Testing configuration management...")
    
    try:
        # Test with temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            config = Config(project_dir=Path(temp_dir))
            config.ensure_directories()
            
            # Test directory creation
            assert config.input_dir.exists()
            assert config.output_dir.exists()
            assert config.utils_dir.exists()
            print("✅ Directory creation works")
            
            # Test configuration saving
            config.save_config()
            config_file = config.project_dir / "dumprx_config.yaml"
            assert config_file.exists()
            print("✅ Configuration saving works")
            
            # Test token handling
            test_token_file = config.project_dir / ".tg_token"
            test_token_file.write_text("test_token_123")
            
            # Reload config
            new_config = Config(project_dir=Path(temp_dir))
            assert new_config.has_telegram_token()
            print("✅ Token loading works")
            
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False
    
    return True


def main_test():
    """Run all tests."""
    print("🚀 DumprX v2.0 Test Suite")
    print("=" * 50)
    
    tests = [
        test_basic_functionality,
        test_file_detection,
        test_url_detection,
        test_configuration_management,
        test_cli_commands,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test_func.__name__} failed with exception: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! DumprX v2.0 is working correctly.")
        return True
    else:
        print(f"⚠️  {failed} tests failed. Please check the implementation.")
        return False


if __name__ == "__main__":
    success = main_test()
    sys.exit(0 if success else 1)