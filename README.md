<div align="center">

  <h1>DumprX</h1>

  <h4>Based Upon Phoenix Firmware Dumper from DroidDumps, with some Changes and Improvements</h4>

</div>


## What this really is

You might've used firmware extractor via dumpyara from https://github.com/AndroidDumps/. This toolkit is revamped edition of the tools with some improvements and feature additions.

## The improvements over dumpyara

- [x] dumpyara's and firmware_extractor's scripts are merged with handpicked shellcheck-ed and pylint-ed improvements
- [x] The script can download and dump firmware from different filehosters such as Mega.NZ, Mediafire.com, AndroidFileHost.com and from Google Drive URLs
- [x] File as-well-as Folder as an input is processed thoroughly to check all kinds of supported firmware types
- [x] All the external tools are now inherited into one place and unnesessary files removed
- [x] Binary tools are updated to latest available source
- [x] LG KDZ utilities are updated to support latest firmwares
- [x] Installation requirements are narrowed down to minimal for playing with this toolkit
- [x] Recovery Dump is made too
- [x] **NEW: Complete Python refactoring** with modular architecture and enhanced features
- [x] **NEW: YAML configuration system** for user customization
- [x] **NEW: Enhanced manufacturer support** with intelligent auto-detection

## Recommendations before Playing with Firmware Dumper

This toolkit can run in any Debian/Ubuntu distribution, Ubuntu Bionic and Focal would be best, other versions are not tested.

Support for Alpine Linux is added and tested. You can give it a try.

For any other UNIX Distributions, please refer to internal [Setup File](setup.sh) and install the required programs via their own package manager.

## Prepare toolkit dependencies / requirements

To prepare for this toolkit, run [Setup File](setup.sh) at first, which is needed only one time. After that, run [Main Script](dumper.py) with proper argument.

```bash
# Install dependencies
./setup.sh

# Extract firmware using the new Python dumper
./dumper.py 'Firmware File/Extracted Folder -OR- Supported Website Link'
```

## Usage

Run this toolkit with proper firmware file/folder path or URL

```bash
./dumper.py 'Firmware File/Extracted Folder -OR- Supported Website Link'
```

### Command Line Options

```bash
./dumper.py [OPTIONS] INPUT_PATH

Options:
  -o, --output PATH    Output directory
  -v, --verbose        Enable verbose logging  
  --debug             Enable debug logging
  --version           Show version information
  --help              Show this message and exit
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

## Configuration

The toolkit now uses a YAML configuration file (`config.yaml`) that allows users to customize:

- Directory paths for input, output, utilities, and temporary files
- External tool repositories and versions
- Supported partitions and file mappings
- Logging preferences
- Download settings
- Telegram bot integration (optional)

You can modify `config.yaml` to adapt the toolkit to your specific needs.

## Manufacturer Support

The Python refactoring provides enhanced support for:

- **Samsung**: TAR.MD5 and PIT files with MD5 verification
- **Xiaomi**: MIUI packages and Fastboot images with payload extraction
- **OPPO/OnePlus**: OZIP, OFP, OPS decryption with auto-detection
- **Huawei**: UPDATE.APP packages with complete extraction
- **LG**: KDZ/DZ files with modern firmware support
- **HTC**: RUU decryption for system and firmware partitions
- **Sony**: FTF/SIN processing with automatic conversion
- **Generic**: Fallback extraction for unknown formats

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
- ✅ **10-hour timeout** for large firmware processing
- ✅ **Automatic cleanup** of sensitive authentication data
- ✅ **Debug artifacts** uploaded on failure for troubleshooting

### Environment Variables Configured:

The workflow automatically configures the following based on your selections:
- `PUSH_TO_GITLAB`: Set to `true` when GitLab is selected, `false` for GitHub
- Git configuration with appropriate user email and name
- HTTP buffer settings for large file uploads

### Security Notes:

- All authentication tokens are handled securely through GitHub's secrets mechanism
- Tokens are automatically cleared from the environment after use
- The workflow includes cleanup steps to prevent token leakage

## Architecture

The toolkit has been refactored into a modular Python architecture:

```
src/dumprx/
├── core/          # Main extraction engine, config, logging
├── manufacturers/ # Manufacturer-specific extraction modules
├── downloaders/   # Download service implementations
├── boot/          # Boot image analysis capabilities
├── utils/         # File and archive utilities
└── telegram/      # Future bot integration support
```

This modular design allows for easy extension and maintenance while providing a clean API for firmware extraction operations.

## Requirements

### System Requirements
- Python 3.8 or higher
- Debian/Ubuntu-based Linux distribution (recommended)
- At least 20GB free disk space for large firmware files

### Python Dependencies
- Click (for CLI interface)
- PyYAML (for configuration management)
- Requests (for download functionality)
- Additional dependencies as listed in `requirements.txt`

### System Packages
The setup script will install required system packages including:
- Archive extraction tools (7zip, unrar, etc.)
- Python development tools
- Build essentials for compiling utilities
- Device tree compiler and other firmware tools

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests to improve the toolkit.

## License

This project is licensed under the GPL v3 License - see the [LICENSE](LICENSE) file for details.