<div align="center">

  <h1>DumprX v2.0</h1>

  <h4>Advanced Python-based Firmware Dumping Tool</h4>

</div>


## What this is

DumprX is a complete rewrite of the original firmware dumping toolkit, now fully implemented in Python with a modern CLI interface, enhanced functionality, and improved user experience.

## Major Improvements in v2.0

- [x] **Complete Python rewrite** - All Bash scripts converted to modular Python code
- [x] **Modern CLI interface** - Clean, intuitive command-line interface with rich console output
- [x] **Enhanced firmware detection** - Improved support for multiple firmware formats and manufacturers
- [x] **Modular architecture** - Reusable components for extraction, analysis, and integration
- [x] **Configuration system** - YAML-based configuration with token file support
- [x] **Git integration** - Automatic repository creation and push to GitHub/GitLab
- [x] **Telegram notifications** - Real-time status updates via Telegram bot
- [x] **GitHub Actions workflow** - Automated cloud processing of firmware
- [x] **Progress indicators** - Visual progress bars and status updates
- [x] **Error handling** - Comprehensive error handling and logging

## Installation

### Prerequisites

- Python 3.8 or higher
- Git with LFS support
- Standard Unix tools (available on most Linux distributions)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/YourUsername/DumprX.git
cd DumprX
```

2. Run the setup script:
```bash
chmod +x setup.sh
./setup.sh
```

The setup script will:
- Install system dependencies
- Install Python dependencies
- Configure the environment
- Validate the installation

## Usage

DumprX provides a clean CLI interface with multiple commands:

### Basic Commands

```bash
# Extract and analyze firmware
python3 dumprx.py dump <firmware_file_or_url>

# Download firmware from supported URLs
python3 dumprx.py download <url>

# Detect firmware type and format
python3 dumprx.py detect <file_or_url>

# Show system status and configuration
python3 dumprx.py status

# Show configuration
python3 dumprx.py config-show

# Get help
python3 dumprx.py --help
```

### Examples

```bash
# Extract local firmware file
python3 dumprx.py dump firmware.zip

# Extract firmware from URL
python3 dumprx.py dump 'https://mega.nz/file/example'

# Download only (without extraction)
python3 dumprx.py download 'https://androidfilehost.com/?fid=123456'

# Detect firmware type
python3 dumprx.py detect system.img

# Check tool availability
python3 dumprx.py status --check-tools
```

## Configuration

### Configuration File

Edit `config.yaml` to configure DumprX behavior:

```yaml
# Logging settings
logging:
  level: "INFO"
  file: ""
  max_size: "10MB"
  backup_count: 5

# Git integration
git:
  github:
    token: ""
    organization: ""
  gitlab:
    token: ""
    group: ""
    instance: "gitlab.com"

# Telegram notifications
telegram:
  token: ""
  chat_id: "@DumprXDumps"
  enabled: true

# Download settings
download:
  user_agents:
    default: "Mozilla/5.0 ..."
  chunk_size: 8192
  timeout: 300
```

### Token Files (Alternative)

You can also use individual token files:
- `.github_token` - GitHub personal access token
- `.github_orgname` - GitHub organization name
- `.gitlab_token` - GitLab access token
- `.gitlab_group` - GitLab group name
- `.tg_token` - Telegram bot token
- `.tg_chat` - Telegram chat/channel ID

## Supported Formats

### Firmware Types

- **Android OTA**: payload.bin, system.new.dat, super.img
- **Oplus/OnePlus**: .ozip, .ofp, .ops files
- **LG**: .kdz, .dz files
- **HTC**: RUU .exe files
- **Huawei**: UPDATE.APP files
- **Sony**: .sin files
- **Generic**: .zip, .rar, .7z, .tar archives
- **Raw images**: .img, .bin files

### Download Sources

- **MEGA**: mega.nz, mega.co.nz
- **MediaFire**: mediafire.com
- **Google Drive**: drive.google.com
- **OneDrive**: onedrive.live.com, 1drv.ms
- **AndroidFileHost**: androidfilehost.com
- **Direct URLs**: Any direct download link

## GitHub Actions Workflow

### Setting up the Workflow

1. Go to your repository's Actions tab
2. Select "DumprX Firmware Processing"
3. Click "Run workflow"
4. Fill in the required parameters:
   - **Firmware URL**: URL to the firmware file
   - **Git Provider**: Choose GitHub or GitLab
   - **Tokens**: Provide appropriate access tokens
   - **Telegram** (optional): Bot token and chat ID

### Workflow Parameters

- `firmware_url`: Direct URL to firmware file
- `git_provider`: "github" or "gitlab"
- `github_token`: GitHub personal access token (if using GitHub)
- `github_orgname`: GitHub organization name (optional)
- `gitlab_token`: GitLab access token (if using GitLab)
- `gitlab_group`: GitLab group name (optional)
- `telegram_token`: Telegram bot token (optional)
- `telegram_chat_id`: Telegram chat/channel ID (optional)

## Advanced Features

### Manufacturer-Specific Processing

DumprX includes specialized extraction logic for different manufacturers:

- **Oppo/Realme**: Automatic decryption of encrypted firmware
- **LG**: KDZ and DZ file extraction with partition splitting
- **Sony**: SIN file extraction and processing
- **Huawei**: UPDATE.APP splitting and extraction

### Parallel Processing

- Multi-threaded extraction for large files
- Configurable worker count
- Memory-efficient processing for large firmware files

### Error Recovery

- Automatic retry mechanisms for downloads
- Fallback extraction methods
- Comprehensive error logging

## Development

### Project Structure

```
DumprX/
├── dumprx/                 # Main Python package
│   ├── __init__.py
│   ├── cli.py             # CLI interface
│   ├── config.py          # Configuration management
│   ├── console.py         # Console output and logging
│   ├── detector.py        # Firmware detection
│   ├── downloaders.py     # Download utilities
│   ├── extractors.py      # Extraction engines
│   ├── firmware_analyzer.py # Firmware analysis
│   ├── git_ops.py         # Git operations
│   └── telegram.py        # Telegram integration
├── utils/                 # External utilities and tools
├── config.yaml           # Configuration file
├── dumprx.py             # Main executable
├── requirements.txt      # Python dependencies
└── setup.sh             # Installation script
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the GNU General Public License v3.0 - see the LICENSE file for details.

## Credits

- Original DumprX concept and implementation
- Android dumping tools community
- Various open-source extraction utilities included in the utils/ directory
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
