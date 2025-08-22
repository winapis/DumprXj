# DumprX v2.0 - Advanced Android Firmware Extraction Toolkit

🚀 **Complete Python Rewrite** - DumprX has been completely rewritten in Python with a modern, modular architecture.

## What's New in v2.0

### 🔄 Complete Python Refactoring
- ✅ **Unified CLI Interface** - Single `dumprx` command for all operations
- ✅ **Modular Architecture** - Clean, maintainable, and extensible codebase
- ✅ **Enhanced File Detection** - Improved support for various firmware formats
- ✅ **Better Error Handling** - Robust error handling and recovery
- ✅ **Rich Console Output** - Beautiful, informative console interface

### 🔧 Enhanced Features
- 🔍 **Advanced Detection** - Improved vendor and format detection
- 📱 **Enhanced Telegram Integration** - Better notifications and bot support
- 🔗 **Improved Download Support** - Better handling of various file hosting services
- 🏭 **Vendor-Specific Processing** - Enhanced manufacturer-specific functionality
- 🥾 **Advanced Boot Analysis** - Support for ramdisk versions 2, 3, and 4

### 🏗️ Modern Architecture
- 📦 **Proper Python Packaging** - Standard Python project structure
- 🧩 **Modular Design** - Reusable components and clear separation of concerns
- 🔄 **Async Support** - Asynchronous operations for better performance
- 🎯 **Type Hints** - Full type annotation support
- 🧪 **Testing Framework** - Built-in testing infrastructure

## Quick Start

### Installation & Setup

```bash
# Clone the repository
git clone https://github.com/Eduardob3677/DumprX.git
cd DumprX

# Run setup (installs dependencies)
./setup.sh

# The dumprx command is ready to use!
./dumprx --help
```

### Basic Usage

```bash
# Extract a firmware file
./dumprx extract firmware.zip

# Extract from a URL
./dumprx extract 'https://mega.nz/file/...'

# Get information about a file
./dumprx info firmware.zip

# List supported formats
./dumprx formats

# Show current configuration
./dumprx config-info
```

### Set Up Integrations

```bash
# Set up Telegram notifications
./dumprx setup-telegram

# Set up Git integration (GitHub/GitLab)
./dumprx setup-git
```

## Supported Features

### 📋 Supported Formats
- **Archives**: ZIP, RAR, 7Z, TAR, TAR.GZ, TGZ, TAR.MD5
- **Encrypted**: OZIP (Oppo/Realme), OPS (OnePlus), KDZ (LG)
- **Firmware**: OFP, NB0, PAC, SIN, RUU, UPDATE.APP
- **Images**: IMG, BIN, Super Images, Payload.bin
- **And many more...**

### 🏭 Supported Vendors
- **Oppo/Realme** - OZIP, OPS decryption
- **OnePlus** - OPS extraction, Fastboot images
- **LG** - KDZ/DZ extraction
- **Samsung** - TAR.MD5, Odin packages
- **Xiaomi** - Fastboot packages, MIUI
- **HTC** - RUU decryption
- **Sony** - SIN files, Xperia firmware
- **And more...**

### 🌐 Download Support
- **Mega.nz** - Direct download with megatools
- **MediaFire** - Automatic link extraction
- **Google Drive** - Large file support
- **OneDrive** - Microsoft cloud storage
- **AndroidFileHost** - AFH integration
- **WeTransfer** - Transfer link support
- **Direct URLs** - Any direct download link

## Advanced Usage

### Configuration
DumprX automatically creates configuration files in your project directory:
- `.tg_token` - Telegram bot token
- `.tg_chat` - Telegram chat ID
- `.github_token` - GitHub access token
- `.gitlab_token` - GitLab access token
- `dumprx_config.yaml` - Main configuration file

### Command Line Interface

```bash
# Basic extraction
./dumprx extract <input> [options]

# Available options:
  --output, -o          Custom output directory
  --no-git             Skip Git upload
  --no-telegram        Skip Telegram notification
  --config-dir         Custom config directory

# Examples:
./dumprx extract firmware.zip --output /custom/path
./dumprx extract 'https://example.com/firmware.zip' --no-git
./dumprx extract /path/to/firmware/ --no-telegram
```

### Python API
DumprX can also be used as a Python library:

```python
from dumprx import DumprX, Config

# Initialize with custom config
config = Config(project_dir='/path/to/project')
dumper = DumprX(config)

# Extract firmware
result = dumper.extract_firmware(
    input_path='firmware.zip',
    upload_to_git=True,
    send_telegram=True
)

print(f"Extraction successful: {result['success']}")
```

## Migration from v1.x

The Python rewrite maintains full compatibility with v1.x functionality while providing significant improvements:

### What's Different
- 🔄 **Single Command** - Use `./dumprx` instead of `./dumper.sh`
- 🎨 **Better Output** - Rich console interface with progress indicators
- ⚡ **Faster Operation** - Improved performance and parallel processing
- 🛠️ **Better Error Messages** - Clear, actionable error messages

### What's the Same
- ✅ **All File Formats** - Same comprehensive format support
- ✅ **All Vendors** - Same vendor-specific functionality
- ✅ **Git Integration** - Same GitHub/GitLab upload capability
- ✅ **Telegram Support** - Same notification system
- ✅ **External Tools** - Same trusted extraction utilities

## Development

### Project Structure
```
DumprX/
├── src/dumprx/           # Main Python package
│   ├── core/            # Core functionality
│   ├── modules/         # Feature modules
│   └── cli/             # Command line interface
├── utils/               # External tools and utilities
├── tests/               # Test suite
├── dumprx               # CLI wrapper script
└── pyproject.toml       # Python project configuration
```

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## Legacy Support

The original bash scripts are preserved for reference but are no longer actively maintained. All new development focuses on the Python implementation.

## Credits

DumprX v2.0 maintains compatibility with all the excellent tools and libraries that made v1.x possible, while adding modern Python tooling and architecture.

### Original Tools Credits
- See the original README for comprehensive credits to all tool authors
- Special thanks to the Android development community
- All original tool licenses and attributions remain intact

## License

GPL-3.0 License - see LICENSE file for details.

---

🚀 **Ready to extract firmware like never before? Try DumprX v2.0 today!**