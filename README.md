<div align="center">

  <h1>DumprX v2.0 🔥</h1>

  <h4>Advanced Firmware Extraction Toolkit - Completely Refactored & Enhanced</h4>
  
  [![GitHub Actions](https://github.com/Eduardob3677/DumprX/workflows/DumprX%20v2.0%20-%20Advanced%20Firmware%20Extraction/badge.svg)](https://github.com/Eduardob3677/DumprX/actions)
  [![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
  [![Version](https://img.shields.io/badge/Version-2.0-green.svg)](https://github.com/Eduardob3677/DumprX/releases)

</div>

## 🚀 What's New in v2.0

DumprX v2.0 is a **complete rewrite** of the original firmware extraction toolkit with modern architecture, enhanced functionality, and improved user experience.

### 🏗️ Complete Architecture Overhaul
- **✨ Modular Design**: Refactored from 1360-line monolithic script to clean modular architecture
- **⚡ Enhanced Performance**: Optimized extraction with parallel processing and better resource management
- **🛡️ Better Error Handling**: Comprehensive error detection, recovery mechanisms, and user feedback
- **🧹 Cleaner Codebase**: Removed dead code, improved maintainability, and added extensive documentation

### 📱 Enhanced Manufacturer Support (12 Manufacturers)
- **Samsung**: TAR.MD5, PIT files, Odin packages
- **Xiaomi**: MIUI packages, Fastboot images, TGZ files
- **OPPO/OnePlus**: OZIP, OFP, OPS decryption and extraction
- **Huawei**: UPDATE.APP, HWOTA packages
- **LG**: KDZ, DZ file extraction
- **HTC**: RUU decryption and extraction
- **Sony**: FTF, SIN file processing
- **And 5 more manufacturers** with intelligent auto-detection

### 🔧 Advanced Boot Image Analysis
- **Multi-Boot Support**: boot.img, vendor_boot.img, init_boot.img, recovery.img, vendor_kernel_boot.img
- **Ramdisk Versions 2/3/4**: Automatic detection and analysis of Android ramdisk formats
- **Compression Support**: gzip, LZ4, XZ, LZMA, Zstandard decompression
- **DTB Extraction**: Device tree blob extraction and DTS conversion
- **Kernel Analysis**: ELF generation, config extraction, version detection

### 🌐 Enhanced Download Services (8 Services)
- **Direct Downloads**: HTTP/HTTPS with resume support
- **Cloud Storage**: Mega.nz, Google Drive, OneDrive, Dropbox
- **File Hosts**: MediaFire, AndroidFileHost
- **Git Repositories**: GitHub/GitLab release downloads
- **Smart Detection**: Automatic service detection and URL normalization

### 🤖 Advanced Telegram Bot Integration
- **Interactive Commands**: Full bot with queue management and real-time updates
- **Beautiful Notifications**: Enhanced formatted messages with device information
- **Progress Tracking**: Real-time extraction progress with detailed status
- **Queue Management**: Multiple extraction requests with intelligent queuing
- **Error Notifications**: Comprehensive error reporting and debugging

### 💻 Enhanced User Interface
- **Beautiful CLI**: Colorized output with emojis and progress indicators
- **Minimalistic Design**: Clean, attractive user interface with better UX
- **Smart Messaging**: Context-aware messages with helpful tips and guidance
- **Progress Visualization**: Real-time progress bars and status updates

## 🛠️ Quick Start

### Prerequisites
- Ubuntu/Debian Linux (18.04+ recommended)
- 8GB+ free disk space
- 4GB+ RAM for large firmware files
- Python 3.8+
- Git and basic build tools

### Installation
```bash
# Clone the repository
git clone https://github.com/Eduardob3677/DumprX.git
cd DumprX

# Run the enhanced setup script
sudo chmod +x setup.sh
./setup.sh

# Make scripts executable
chmod +x dumper_v2.sh telegram_bot.sh
```

### Basic Usage

#### Extract firmware from file
```bash
./dumper_v2.sh firmware.zip
```

#### Extract firmware from URL
```bash
./dumper_v2.sh 'https://example.com/firmware.zip'
```

#### Use legacy dumper (for compatibility)
```bash
./dumper.sh firmware.zip
```

### Advanced Usage

#### Start Telegram Bot
```bash
# Configure bot token
echo "YOUR_BOT_TOKEN" > .tg_token

# Start bot in polling mode
./telegram_bot.sh polling

# Start bot in webhook mode
./telegram_bot.sh webhook https://your-domain.com/webhook
```

#### GitHub Actions Workflow
1. Go to Actions tab in your repository
2. Select "DumprX v2.0 - Advanced Firmware Extraction"
3. Click "Run workflow"
4. Enter firmware URL and configuration
5. Choose between v2.0 or legacy dumper

## 📦 Supported Formats

### Archive Formats
- **ZIP/RAR/7Z**: Standard compressed archives
- **TAR/TGZ**: Unix archive formats
- **TAR.MD5**: Samsung firmware packages

### Manufacturer-Specific Formats
- **OZIP**: OnePlus/OPPO encrypted firmware
- **OFP**: OPPO firmware packages
- **OPS**: OnePlus firmware packages
- **KDZ/DZ**: LG firmware packages
- **RUU**: HTC ROM update utilities
- **UPDATE.APP**: Huawei firmware packages
- **NB0**: Nokia firmware images
- **PAC**: Spreadtrum firmware packages
- **FTF/SIN**: Sony firmware packages

### Image Formats
- **Sparse Images**: Android sparse format
- **Raw Images**: Standard partition images
- **Boot Images**: Android boot/recovery images
- **Super Images**: Dynamic partition images

## 🌐 Supported Download Services

- **Direct Downloads**: Any HTTP/HTTPS link
- **Mega.nz**: File and folder links
- **Google Drive**: Shared file links
- **MediaFire**: Direct download links
- **OneDrive**: Microsoft cloud storage
- **AndroidFileHost**: AFH download links
- **Dropbox**: Shared file links
- **GitHub/GitLab**: Release asset downloads

## 🚀 GitHub Actions Workflow Usage

DumprX v2.0 includes an enhanced GitHub Actions workflow for automated firmware extraction in the cloud.

### Workflow Features
- **10-hour timeout**: For very large firmware files
- **Enhanced logging**: Detailed progress and debug information
- **Dual dumper support**: Choose between v2.0 or legacy dumper
- **Debug mode**: Enable detailed logging for troubleshooting
- **Resource monitoring**: CPU, memory, and disk usage tracking
- **Artifact uploads**: Debug logs and extraction summaries

### Configuration
1. **Fork this repository** to your GitHub account
2. **Configure secrets** (optional but recommended):
   - `GITHUB_TOKEN`: For pushing to GitHub repositories
   - `TELEGRAM_BOT_TOKEN`: For Telegram notifications
3. **Run the workflow** from the Actions tab

### Workflow Inputs
- **firmware_url**: The firmware URL to extract (required)
- **git_provider**: Choose GitHub or GitLab for uploads
- **use_legacy_dumper**: Use original dumper.sh for compatibility
- **enable_debug**: Enable detailed debug logging
- **Telegram settings**: Bot token and chat ID for notifications

## 🤖 Telegram Bot Commands

The integrated Telegram bot provides a complete interface for firmware extraction:

### Bot Commands
- `/start` - Welcome message and bot introduction
- `/help` - Complete command reference
- `/extract <url>` - Extract firmware from URL
- `/status` - Check bot status and system resources
- `/queue` - View extraction queue and progress
- `/cancel` - Cancel current extraction
- `/supported` - List supported formats and services
- `/examples` - Usage examples and tips

### Bot Features
- **Queue Management**: Handle multiple extraction requests
- **Progress Updates**: Real-time extraction progress
- **Error Handling**: Comprehensive error reporting
- **Beautiful Messages**: Formatted output with emojis
- **Smart Detection**: Automatic URL and format detection

## 📁 Project Structure

```
DumprX/
├── lib/                          # Modular library components
│   ├── core/                    # Core functionality
│   │   └── config.sh           # Configuration management
│   ├── messaging/              # User interface and notifications
│   │   ├── ui.sh              # Enhanced CLI interface
│   │   └── telegram.sh        # Telegram bot integration
│   ├── downloaders/           # Download service handlers
│   │   └── services.sh        # Multi-service download support
│   ├── manufacturers/         # Manufacturer-specific handlers
│   │   └── detection.sh       # Auto-detection and extraction
│   ├── extractors/           # Extraction modules
│   │   ├── partitions.sh     # Partition detection and handling
│   │   └── bootimg.sh        # Boot image analysis
│   └── utils/               # Common utilities
│       └── common.sh        # Shared utility functions
├── dumper_v2.sh            # Enhanced main extraction script
├── telegram_bot.sh         # Standalone Telegram bot
├── dumper.sh              # Legacy dumper (compatibility)
├── setup.sh               # Enhanced installation script
├── utils/                 # External tools and utilities
└── .github/workflows/     # Enhanced GitHub Actions
```

For any other UNIX Distributions, please refer to internal [Setup File](setup.sh) and install the required programs via their own package manager.

## Prepare toolkit dependencies / requirements

To prepare for this toolkit, run [Setup File](setup.sh) at first, which is needed only one time. After that, run [Main Script](dumper.sh) with proper argument.

## Usage

Run this toolkit with proper firmware file/folder path or URL

```bash
./dumper.sh 'Firmware File/Extracted Folder -OR- Supported Website Link'
```

Help Context:

```text
  >> Supported Websites:
        1. Directly Accessible Download Link From Any Website
        2. Filehosters like - mega.nz | mediafire | gdrive | onedrive | androidfilehost
         >> Must Wrap Website Link Inside Single-quotes ('')
  >> Supported File Formats For Direct Operation:
         *.zip | *.rar | *.7z | *.tar | *.tar.gz | *.tgz | *.tar.md5
         *.ozip | *.ofp | *.ops | *.kdz | ruu_*exe
         system.new.dat | system.new.dat.br | system.new.dat.xz
         system.new.img | system.img | system-sign.img | UPDATE.APP
         *.emmc.img | *.img.ext4 | system.bin | system-p | payload.bin
         *.nb0 | .*chunk* | *.pac | *super*.img | *system*.sin
```

## GitHub Actions Workflow Usage

You can now use the automated GitHub Actions workflow to dump firmware automatically in the cloud. This workflow allows you to:

- Specify a firmware URL to download and dump
- Choose between GitHub or GitLab as your git provider
- Configure authentication tokens through the workflow interface
- Automatically set up Git LFS for large files

### How to use the workflow:

1. **Go to the Actions tab** in your GitHub repository
2. **Select "Firmware Dump Workflow"** from the workflow list
3. **Click "Run workflow"** button
4. **Fill in the required parameters:**
   - **Firmware URL**: Direct download link to the firmware file
   - **Git Provider**: Choose between `github` or `gitlab`
   - **Authentication tokens**: Based on your provider selection:
     - For GitHub: Provide `github_token` and optionally `github_orgname`
     - For GitLab: Provide `gitlab_token` and optionally `gitlab_group` and `gitlab_instance`
   - **Optional**: Telegram tokens for notifications

### Workflow Features:

- ✅ **Automated dependency installation** using the existing setup.sh script
- ✅ **Git LFS configuration** for handling large firmware files
- ✅ **Disk space optimization** by cleaning up unnecessary packages
- ✅ **8-hour timeout** for large firmware processing
- ✅ **Automatic cleanup** of sensitive authentication data
- ✅ **Debug artifacts** uploaded on failure for troubleshooting

### Environment Variables Configured:

The workflow automatically configures the following based on your selections:
- `PUSH_TO_GITLAB`: Set to `true` when GitLab is selected, `false` for GitHub
- Git configuration with appropriate user email and name
- HTTP buffer settings for large file uploads

### Security Notes:

- All authentication tokens are handled securely through GitHub Actions secrets
- Token files are automatically cleaned up after the workflow completes
- No sensitive data is logged or stored in artifacts

## How to use it to Upload the Dump in GitHub (Local Setup)

- Copy your GITHUB_TOKEN in a file named .github_token and add your GitHub Organization name in another file named .github_orgname inside the project directory.
  - If only Token is given but Organization is not, your Git Username will be used.
- Copy your Telegram Token in a file named .tg_token and Telegram Chat/Channel ID in another file named .tg_chat file if you want to publish the uploading info in Telegram.

## Main Scripture Credit

As mentioned above, this toolkit is entirely focused on improving the Original Firmware Dumper available:  [Dumpyara](https://github.com/AndroidDumps/) [Phoenix Firmware Dumper](https://github.com/DroidDumps)

Credit for those tools goes to everyone whosoever worked hard to put all those programs in one place to make an awesome project.

## Download Utilities Credits

- mega-media-drive_dl.sh (for downloading from mega.nz, mediafire.com, google drive)
  - shell script, most of it's part belongs to badown by @stck-lzm
- afh_dl (for downloading from androidfilehosts.com)
  - python script, by @kade-robertson
- aria2c
- wget

## Internal Utilities Credits

- sdat2img.py (system-dat-to-img v1.2, python script)
  - by @xpirt, @luxi78, @howellzhu
- simg2img (Android sparse-to-raw images converter, binary built from source)
  - by @anestisb
- unsin (Xperia Firmware Unpacker v1.13, binary)
  - by @IgorEisberg
- extract\_android\_ota\_payload.py (OTA Payload Extractor, python script)
  - by @cyxx, with metadata update from [Android's update_engine Git Repository](https://android.googlesource.com/platform/system/update_engine/)
- extract-dtb.py (dtbs extractor v1.3, python script)
  - by @PabloCastellano
- dtc (Device Tree Compiler v1.6, binary built from source)
  - by kernel.org, from their [dtc Git Repository](https://git.kernel.org/pub/scm/utils/dtc/dtc.git)
- vmlinux-to-elf and kallsyms_finder (kernel binary to analyzable ELF converter, python scripts)
  - by @marin-m
- ozipdecrypt.py (Oppo/Oneplus .ozip Firmware decrypter v1.2, python script)
  - by @bkerler
- ofp\_qc\_extract.py and ofp\_mtk\_decrypt.py (Oppo .ofp firmware extractor, python scripts)
  - by @bkerler
- opscrypto.py (OnePlus/Oppo ops firmware extractor, python script)
  - by @bkerler
- lpunpack (OnePlus/Other super.img unpacker, binary built from source)
  - by @LonelyFool
- splituapp.py (UPDATE.APP extractor, python script)
  - by @superr
- pacextractor (Extractor of SpreadTrum firmware files with extension pac. See)
  - by @HemanthJabalpuri
- nb0-extract (Nokia/Sharp/Infocus/Essential nb0-extract, binary built from source)
  - by Heineken @Eddie07 / "FIH mobile"
- kdztools' unkdz.py and undz.py (LG KDZ and DZ Utilities, python scripts)
  - Originally by IOMonster (thecubed on XDA), Modified by @ehem (Elliott Mitchell) and improved by @steadfasterX
- RUU\_Decrypt\_Tool (HTC RUU/ROM Decryption Tool v3.6.8, binary)
  - by @nkk71 and @CaptainThrowback
- extract-ikconfig (.config file extractor from kernel image, shell script)
  - From within linux's source code by @torvalds
- unpackboot.sh (bootimg and ramdisk extractor, modified shell script)
  - Originally by @xiaolu and @carlitros900, stripped to unpack functionallity, by me @rokibhasansagar
- twrpdtgen by @SebaUbuntu
