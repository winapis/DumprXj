# DumprX v2.0 Workflow Configuration Template

This file shows examples of the parameters you can use with the GitHub Actions workflow and the new Python CLI.

## Local CLI Usage Examples:

### Basic Usage:
```bash
./dumprx.py firmware.zip                    # Extract local firmware
./dumprx.py 'https://example.com/fw.zip'    # Download and extract
./dumprx.py --validate                      # Validate setup
./dumprx.py --config custom.yaml firmware   # Use custom config
./dumprx.py --verbose firmware.zip          # Enable debug logging
./dumprx.py --no-upload firmware.zip        # Skip git upload
```

### Configuration File (config.yaml):
```yaml
git:
  github:
    token: "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    organization: "YourOrgName"
  gitlab:
    token: "glpat-xxxxxxxxxxxxxxxxxxxx"
    group: "YourGroupName"
    instance: "gitlab.com"

telegram:
  token: "1234567890:XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
  chat_id: "@YourChannel"
  enabled: true

download:
  timeout: 300
  retry_attempts: 3
  chunk_size: 8192
```

## GitHub Provider Example:
- **Firmware URL**: `https://example.com/firmware.zip`
- **Git Provider**: `github`
- **GitHub Token**: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
- **GitHub Organization**: `YourOrgName` (optional)
- **Telegram Token**: `1234567890:XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX` (optional)
- **Telegram Chat ID**: `-1001234567890` (optional)

## GitLab Provider Example:
- **Firmware URL**: `https://example.com/firmware.zip`
- **Git Provider**: `gitlab`
- **GitLab Token**: `glpat-xxxxxxxxxxxxxxxxxxxx`
- **GitLab Group**: `YourGroupName` (optional)
- **GitLab Instance**: `gitlab.com` (default, or your custom instance)
- **Telegram Token**: `1234567890:XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX` (optional)
- **Telegram Chat ID**: `-1001234567890` (optional)

## Supported Firmware Sources:
- Direct download links from any website
- Mega.nz links
- MediaFire links
- Google Drive links
- OneDrive links
- AndroidFileHost links

## Note:
- Wrap URLs with special characters in single quotes when using the command line
- For the workflow, just paste the URL directly in the input field
- All authentication tokens are handled securely through GitHub Actions
- The workflow automatically configures Git LFS for large files (>100MB)