# DumprX v2.0.0 - Advanced Firmware Dumper & Extractor 🚀

**DumprX** is a modern, Python-based firmware dumping and extraction toolkit designed for Android firmware analysis. This is a complete rewrite of the original bash-based dumper with enhanced features, better reliability, and a modern CLI interface.

## ✨ Key Features

### 🔗 **Universal Download Support**
- **Mega.nz** - Full encryption support
- **MediaFire** - Direct link extraction
- **Google Drive** - Large file handling with confirmation tokens
- **AndroidFileHost** - Mirror selection and API integration
- **OneDrive** - Share link conversion
- **Direct HTTP/HTTPS** - With resume support and progress tracking

### 📦 **Comprehensive Firmware Support**
- **Archives**: ZIP, RAR, 7Z, TAR (all variants)
- **Firmware Packages**: OZIP, OFP, OPS, KDZ, NB0, PAC, RUU
- **Image Files**: Boot images, system images, super images, sparse images
- **Manufacturer-Specific**: Oppo, OnePlus, LG, HTC, Nokia, SpreadTrum support

### 🔧 **Advanced Extraction**
- **Automatic Format Detection** - File signature analysis
- **Ramdisk Extraction** - Multiple compression format support (gzip, lzma, lz4, xz, lzop, bzip2)
- **Partition Extraction** - System, vendor, product, boot, recovery, and more
- **Super Image Support** - Dynamic partition extraction
- **Build.prop Analysis** - Automatic device information extraction

### 🌐 **Git Integration**
- **GitHub Support** - Automatic repository creation and push
- **GitLab Support** - Custom instance and group support
- **Smart Naming** - Repositories named by brand/device/model
- **Rich Commits** - Detailed firmware information in commit messages

### 📱 **Telegram Bot**
- **Rich Notifications** - HTML-formatted messages with device info
- **Error Reporting** - Automatic error notifications
- **Status Updates** - Real-time operation progress
- **Download Links** - Direct links to extracted firmware

## 🚀 Quick Start

### Installation

#### Option 1: Automatic Setup (Recommended)
```bash
# Clone the repository
git clone https://github.com/Eduardob3677/DumprX.git
cd DumprX

# Run setup script (Ubuntu/Debian/Alpine/macOS)
python3 setup.py
```

#### Option 2: Manual Setup
```bash
# Install system dependencies (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install python3 python3-pip unzip p7zip-full git git-lfs

# Install DumprX
pip install -e .
```

### Basic Usage

```bash
# Extract firmware from a file
dumprx dump firmware.zip

# Download and extract firmware
dumprx dump https://mega.nz/file/...

# Download only (without extraction)
dumprx download https://mediafire.com/file/...

# Show configuration
dumprx config show

# Test integrations
dumprx test

# Get help
dumprx --help
```

## ⚙️ Configuration

DumprX uses a YAML configuration file (`config.yaml`) for settings. The configuration supports:

### Directory Settings
```yaml
directories:
  input: "input"          # Download directory
  output: "out"           # Extraction output directory
  utils: "utils"          # Tools directory
  temp: "out/tmp"         # Temporary files
```

### Git Integration
```yaml
git:
  github:
    token: ""             # GitHub token
    organization: ""      # GitHub organization
  gitlab:
    token: ""             # GitLab token
    group: ""             # GitLab group
    instance: "gitlab.com" # GitLab instance
```

### Telegram Bot
```yaml
telegram:
  token: ""               # Telegram bot token
  chat_id: "@channel"     # Chat or channel ID
  enabled: true           # Enable notifications
```

### Legacy Token Files
DumprX maintains backward compatibility with token files:
- `.github_token` - GitHub token
- `.github_orgname` - GitHub organization
- `.gitlab_token` - GitLab token
- `.tg_token` - Telegram bot token
- `.tg_chat` - Telegram chat ID

## 🎯 Supported Sources

### Direct Download Links
Any direct HTTP/HTTPS download link with proper headers.

### Cloud Storage
- **Mega.nz**: `https://mega.nz/file/...` or `https://mega.nz/#!...`
- **MediaFire**: `https://mediafire.com/file/...`
- **Google Drive**: `https://drive.google.com/file/d/...`
- **OneDrive**: `https://1drv.ms/...` or `https://onedrive.live.com/...`

### Android-Specific
- **AndroidFileHost**: `https://androidfilehost.com/?fid=...`

## 📱 Supported Firmware Types

### Archive Formats
- **.zip** - Standard ZIP archives
- **.rar** - WinRAR archives
- **.7z** - 7-Zip archives
- **.tar, .tar.gz, .tgz** - Tape archives

### Firmware Packages
- **.ozip** - Oppo/Realme encrypted ZIP
- **.ofp** - Oppo firmware package
- **.ops** - OnePlus/Oppo firmware
- **.kdz** - LG firmware package
- **.nb0** - Nokia/Sharp/Infocus firmware
- **.pac** - SpreadTrum firmware
- **ruu_*.exe** - HTC RUU files

### Image Files
- **.img** - Android image files (boot, system, etc.)
- **.bin** - Binary image files
- **.sin** - Sony firmware files
- **system.new.dat** - Android DAT images
- **super.img** - Dynamic partition images

## 🔧 Advanced Features

### Automatic Device Detection
DumprX automatically detects device information from firmware:
- Device brand and model
- Android version
- Build fingerprint
- Available partitions

### Intelligent Extraction
- **Format Detection**: Automatic detection by file signature and extension
- **Manufacturer Logic**: Specific handling for different manufacturers
- **Partition Analysis**: Automatic discovery and extraction of all partitions
- **Ramdisk Processing**: Multi-format ramdisk extraction with compression detection

### Progress Tracking
- Real-time download progress bars
- Extraction progress with file counts
- Rich console output with colors and emoji
- Detailed logging with configurable levels

## 🤖 GitHub Actions Integration

DumprX includes an updated GitHub Actions workflow for automated firmware processing:

```yaml
name: Extract Firmware
on:
  workflow_dispatch:
    inputs:
      firmware_url:
        description: 'Firmware URL'
        required: true
      git_provider:
        description: 'Git provider (github/gitlab)'
        default: 'github'
```

The workflow automatically:
1. Sets up the environment
2. Installs DumprX
3. Downloads and extracts firmware
4. Uploads to the specified git provider
5. Sends Telegram notifications

## 📋 Migration from v1.x

### Key Changes
- **Python CLI** instead of bash scripts
- **Modular architecture** with separate packages
- **Enhanced configuration** with YAML support
- **Improved error handling** and logging
- **Better progress tracking** and user feedback

### Migration Steps
1. **Backup your configuration** (token files will still work)
2. **Run the new setup**: `python3 setup.py`
3. **Test the installation**: `dumprx test`
4. **Update your workflows** to use `dumprx` commands

### Compatibility
- All original functionality is preserved
- Token files (`.github_token`, etc.) still work
- GitHub Actions inputs remain the same
- Output directory structure is unchanged

## 🛠️ Development

### Project Structure
```
dumprx/
├── core/           # Core functionality
├── downloaders/    # Download implementations
├── extractors/     # Extraction implementations
├── utils/          # Utility functions
└── cli.py          # Command-line interface
```

### Running Tests
```bash
# Test integrations
dumprx test

# Test with sample firmware
dumprx dump test_firmware.zip --force

# Test downloads
dumprx download https://example.com/firmware.zip
```

## 🆘 Troubleshooting

### Common Issues

**Command not found: dumprx**
```bash
# Reinstall the package
pip install -e .

# Or use module syntax
python3 -m dumprx.cli --help
```

**Permission denied errors**
```bash
# Fix directory permissions
sudo chown -R $USER:$USER .

# Or run setup again
python3 setup.py
```

**Git upload fails**
```bash
# Check credentials
dumprx test

# Verify token permissions
# GitHub: repo, user scopes
# GitLab: api, read_user, write_repository scopes
```

### Debug Mode
```bash
# Enable verbose output
dumprx --verbose dump firmware.zip

# Or set debug level in config
dumprx config show
```

## 📜 License

DumprX is licensed under the GNU General Public License v3.0. See [LICENSE](LICENSE) for details.

## 🙏 Credits

### Original Project
Based on the excellent work from:
- [AndroidDumps/dumpyara](https://github.com/AndroidDumps/dumpyara)
- [DroidDumps/phoenix](https://github.com/DroidDumps/phoenix)

### External Tools
DumprX integrates many excellent tools:
- **LG KDZ Tools** by @steadfasterX, @ehem, and IOMonster
- **Oppo Tools** by @bkerler (ozipdecrypt, ofp tools, opscrypto)
- **VMLinux Tools** by @marin-m
- **Boot Tools** by @xiaolu and @carlitros900
- **And many more** - see source code for complete attribution

### Contributors
- **@Eduardob3677** - Project maintainer and Python rewrite
- **Community contributors** - Bug reports, features, and improvements

## 🔗 Links

- **Repository**: https://github.com/Eduardob3677/DumprX
- **Issues**: https://github.com/Eduardob3677/DumprX/issues
- **Releases**: https://github.com/Eduardob3677/DumprX/releases
- **Documentation**: https://github.com/Eduardob3677/DumprX/wiki

---

**DumprX v2.0.0** - Making firmware analysis accessible, reliable, and modern. 🚀