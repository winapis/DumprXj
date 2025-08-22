<div align="center">

  <h1>DumprX v2.0</h1>

  <h4>Advanced Firmware Extraction Toolkit with Python Architecture</h4>
  
  [![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
  [![License](https://img.shields.io/badge/License-GPL%20v3-green.svg)](LICENSE)
  [![Manufacturers](https://img.shields.io/badge/Manufacturers-12+-orange.svg)](#supported-manufacturers)

</div>

## 🚀 What's New in v2.0

DumprX v2.0 is a complete rewrite in Python with enhanced features, better architecture, and improved user experience while maintaining full backward compatibility.

### ✨ Key Features

- **🏭 12+ Manufacturer Support** with intelligent auto-detection
- **🥾 Enhanced Boot Image Analysis** with multi-boot support  
- **🌐 Advanced Download Services** with resume capability
- **🤖 Telegram Bot Integration** with queue management
- **💻 Beautiful CLI Interface** with progress tracking
- **🔄 Dual Dumper Support** - Choose between v2.0 (Python) or legacy (Shell)
- **⚡ 10-hour GitHub Actions** workflow timeout for large files

### 🏭 Supported Manufacturers

| Manufacturer | Formats | Features |
|-------------|---------|----------|
| **Samsung** | TAR.MD5, PIT files | MD5 verification, PIT parsing |
| **Xiaomi** | MIUI packages, Fastboot images | Payload extraction, sparse conversion |
| **OPPO/OnePlus** | OZIP, OFP, OPS decryption | Encryption handling, type detection |
| **Huawei** | UPDATE.APP packages | Complete package extraction |
| **LG** | KDZ/DZ extraction | Modern firmware support |
| **HTC** | RUU decryption | System/firmware partitions |
| **Sony** | FTF/SIN processing | SIN file extraction |
| **Generic** | All standard formats | Fallback extraction |

### 🥾 Enhanced Boot Image Analysis

- **Multi-boot support**: `boot.img`, `vendor_boot.img`, `init_boot.img`, `recovery.img`, `vendor_kernel_boot.img`
- **Ramdisk detection**: Automatic detection of Android ramdisk formats v2, v3, and v4
- **Compression support**: gzip, LZ4, XZ, LZMA, Zstandard decompression
- **DTB extraction**: Device tree blob extraction and DTS conversion
- **Kernel analysis**: ELF generation, config extraction, version detection

### 🌐 Download Services

Enhanced download support for 8+ services with intelligent URL detection:

- **Direct HTTP/HTTPS** downloads with resume support
- **Cloud storage**: Mega.nz, Google Drive, OneDrive, Dropbox  
- **File hosts**: MediaFire, AndroidFileHost
- **Git repositories**: GitHub/GitLab release downloads

## 🛠️ Installation & Setup

### Quick Start (Recommended)

```bash
# Clone the repository
git clone https://github.com/winapis/DumprXj.git
cd DumprXj

# Setup Python environment (v2.0)
./setup_v2.py

# Or setup legacy environment
./setup.sh
```

### Manual Installation

```bash
# Install system dependencies
sudo apt update
sudo apt install -y python3-pip unrar p7zip-full brotli git-lfs

# Install Python dependencies
pip3 install -r requirements.txt

# Make executable
chmod +x dumper_v2.py
```

## 📖 Usage

### DumprX v2.0 (Python) - Recommended

```bash
# Extract firmware file
./dumper_v2.py firmware.zip

# Extract from URL
./dumper_v2.py 'https://example.com/firmware.zip'

# Specify output directory
./dumper_v2.py -o /path/to/output firmware.zip

# Enable verbose logging
./dumper_v2.py -v firmware.zip

# Enable debug mode
./dumper_v2.py --debug firmware.zip

# Show help
./dumper_v2.py --help
```

### Legacy Dumper (Shell) - Backward Compatibility

```bash
# Use legacy dumper
./dumper.sh firmware.zip
```

### 🎯 Supported Input Types

**Firmware Files:**
- Archives: `.zip`, `.rar`, `.7z`, `.tar`, `.tar.gz`, `.tar.md5`
- Manufacturer-specific: `.ozip`, `.ofp`, `.ops`, `.kdz`, `.dz`
- System images: `system.img`, `boot.img`, `recovery.img`, `super.img`
- Special formats: `UPDATE.APP`, `payload.bin`, `*.pac`, `*.sin`, `*.ftf`
- RUU files: `ruu_*.exe`

**Download URLs:**
- Direct links: Any HTTP/HTTPS URL
- Mega.nz: `https://mega.nz/file/...`
- Google Drive: `https://drive.google.com/file/d/...`
- MediaFire: `https://www.mediafire.com/file/...`
- AndroidFileHost: `https://androidfilehost.com/?fid=...`

## 🤖 GitHub Actions Workflow

Enhanced workflow with dual dumper support:

1. Go to **Actions** tab in your fork
2. Select **Firmware Dump Workflow**
3. Click **Run workflow**
4. Fill in the parameters:
   - **Firmware URL**: Direct link or supported service URL
   - **Dumper Version**: Choose v2.0 (Python) or legacy (Shell)
   - **Git Provider**: GitHub or GitLab
   - **Debug Mode**: Enable for troubleshooting
5. Click **Run workflow** to start

### 🔧 Workflow Features

- **10-hour timeout** for very large firmware files
- **Dual dumper support** with version selection
- **Debug mode** for detailed logging
- **Enhanced error handling** and artifact upload
- **Automatic cleanup** of sensitive files

## 🏗️ Architecture

### Python Package Structure

```
src/dumprx/
├── core/
│   ├── dumper.py      # Main extraction engine
│   ├── config.py      # Configuration management
│   └── logger.py      # Enhanced logging
├── manufacturers/
│   ├── samsung.py     # Samsung extractor
│   ├── xiaomi.py      # Xiaomi extractor
│   ├── oppo.py        # OPPO/OnePlus extractor
│   └── ...           # Other manufacturer extractors
├── downloaders/       # Download service modules
├── boot/             # Boot image analysis
├── utils/            # Utility modules
└── telegram/         # Bot integration (future)
```

### 🔄 Backward Compatibility

This refactoring maintains **full backward compatibility**:

- All existing workflows continue to work
- Legacy mode available in GitHub Actions workflow
- Original `dumper.sh` remains functional
- Existing tool dependencies preserved

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
