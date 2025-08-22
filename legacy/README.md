# DumprX Legacy Scripts

This directory contains the original bash scripts from DumprX v1.x for reference and compatibility purposes.

## Contents

- `dumper.sh` - Original main firmware extraction script (1360+ lines)
- `setup.sh` - Original dependency installation script  
- `validate-workflow.sh` - Original workflow validation script
- `mega-media-drive_dl.sh` - Original download script for Mega/MediaFire/Google Drive
- `unpackboot.sh` - Original boot image extraction script

## Migration Status

All functionality from these scripts has been migrated to Python in DumprX v2.0.0:

| Legacy Script | Python Replacement | Status |
|---------------|-------------------|--------|
| `dumper.sh` | `dumprx dump` command | ✅ Fully migrated |
| `setup.sh` | `setup.py` and `dumprx setup` | ✅ Fully migrated |
| `mega-media-drive_dl.sh` | `dumprx/downloaders/` modules | ✅ Fully migrated |
| `unpackboot.sh` | `dumprx/extractors/image.py` | ✅ Fully migrated |
| `validate-workflow.sh` | `dumprx test` command | ✅ Fully migrated |

## Compatibility

### When to Use Legacy Scripts

- **Emergency fallback** if Python version has issues
- **Reference** for understanding original implementation
- **Custom integrations** that haven't been updated yet

### How to Use Legacy Scripts

```bash
# Run from the legacy directory
cd legacy
./dumper.sh firmware.zip

# Or from project root
legacy/dumper.sh firmware.zip
```

### Deprecation Notice

⚠️ **These scripts are deprecated and will be removed in a future version.**

**Please migrate to the Python CLI:**
```bash
# Instead of: ./dumper.sh firmware.zip
dumprx dump firmware.zip

# Instead of: ./setup.sh  
python3 setup.py
```

## Migration Help

See the main `MIGRATION.md` file for detailed migration instructions and troubleshooting.

## Preservation

These scripts are preserved for:
- Historical reference
- Understanding original implementation
- Emergency compatibility
- Educational purposes

---

**Use the new Python CLI for the best experience!** 🚀