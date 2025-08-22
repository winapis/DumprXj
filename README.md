<div align="center">

  <h1>DumprX v2.0</h1>

  <h4>🚀 Completely Refactored Firmware Dumping Toolkit</h4>
  <h5>Modular • Modern • Maintainable</h5>

</div>

---

## ✨ What's New in v2.0

DumprX has been **completely refactored** from the ground up with a modern, modular architecture that makes it more maintainable, extensible, and user-friendly.

### 🏗️ **Complete Modular Refactoring**
- **Modular Architecture**: Code split into reusable modules in the `lib/` directory
- **Consistent UI**: Modern message system with emojis and color-coded output
- **Error Handling**: Improved error handling and user feedback
- **Clean Code**: Eliminated code duplication and dead code

### 📦 **New Module System**
- `lib/ui.sh` - Modern user interface and messaging
- `lib/utils.sh` - Common utilities and file operations
- `lib/git.sh` - Git operations and repository management
- `lib/downloader.sh` - Download functionality for various sources
- `lib/extractors.sh` - Firmware extraction for different formats
- `lib/metadata.sh` - Device metadata extraction
- `lib/setup.sh` - System setup and dependency management
- `lib/loader.sh` - Centralized module loading system

### 🛠️ **Enhanced Functionality**
- **Interactive Cleanup**: New `cleanup.sh` utility for workspace management
- **Better Validation**: Enhanced `validate-workflow.sh` with comprehensive checks
- **Improved Setup**: More robust dependency installation across different Linux distributions
- **Smart Detection**: Better firmware format detection and processing

---

## 🚀 Quick Start

### 1. **Setup Dependencies**
```bash
./setup.sh
```

### 2. **Run Firmware Extraction**
```bash
./dumper.sh 'Firmware File/Extracted Folder -OR- Supported Website Link'
```

### 3. **Clean Workspace (Optional)**
```bash
./cleanup.sh --help  # See cleanup options
```

---

## 🔧 **What this really is**

You might've used firmware extractor via dumpyara from https://github.com/AndroidDumps/. This toolkit is a **completely refactored** edition with significant improvements and modern architecture.

## 📈 **Improvements over dumpyara**

### **v2.0 Refactoring Benefits**
- [x] **Modular Architecture**: Complete code restructuring with reusable modules
- [x] **Modern UI**: Emoji-based messages with consistent color coding
- [x] **Better Error Handling**: Comprehensive error checking and user feedback
- [x] **Code Quality**: Eliminated duplication, improved maintainability
- [x] **Enhanced Functionality**: New utilities and improved workflows

### **Original Improvements (Still Included)**
- [x] dumpyara's and firmware_extractor's scripts are merged with handpicked shellcheck-ed and pylint-ed improvements
- [x] The script can download and dump firmware from different filehosters such as Mega.NZ, Mediafire.com, AndroidFileHost.com and from Google Drive URLs
- [x] File as-well-as Folder as an input is processed thoroughly to check all kinds of supported firmware types
- [x] All the external tools are now inherited into one place and unnecessary files removed
- [x] Binary tools are updated to latest available source
- [x] LG KDZ utilities are updated to support latest firmwares
- [x] Installation requirements are narrowed down to minimal for playing with this toolkit
- [x] Recovery Dump is made too

---

## 🔧 **System Requirements & Setup**

This toolkit supports multiple Linux distributions and has been tested on:

### **Supported Systems**
- **Ubuntu/Debian** (18.04+)
- **Fedora** (30+)
- **RHEL/CentOS** (7+)
- **Arch Linux**
- **openSUSE**
- **Alpine Linux**
- **macOS** (with Homebrew)

### **Automated Setup**
The setup script automatically detects your system and installs the required dependencies:

```bash
./setup.sh
```

### **Manual Requirements**
If you prefer manual installation, you'll need:
- `unrar`, `zip`, `unzip`, `p7zip`
- `python3`, `git`, `aria2`, `wget`
- `brotli`, `lz4`, `xz`
- `device-tree-compiler` (dtc)
- `git-lfs` for large file support

---

## 📖 **Usage Guide**

### **Basic Usage**
```bash
./dumper.sh 'Firmware File/Extracted Folder -OR- Supported Website Link'
```

### **Examples**
```bash
# Local firmware file
./dumper.sh /path/to/firmware.zip

# Direct download URL
./dumper.sh 'https://example.com/firmware.zip'

# Mega.nz link
./dumper.sh 'https://mega.nz/file/...'

# AndroidFileHost link
./dumper.sh 'https://androidfilehost.com/?fid=...'
```

### **Additional Utilities**

#### **Cleanup Workspace**
```bash
./cleanup.sh --help     # See all cleanup options
./cleanup.sh --all      # Full cleanup
./cleanup.sh            # Interactive mode
```

#### **Validate Workflow**
```bash
./validate-workflow.sh  # Check GitHub Actions setup
```

---

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
