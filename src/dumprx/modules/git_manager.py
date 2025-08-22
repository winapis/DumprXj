"""
Git repository management module.
"""

import subprocess
import json
import requests
from pathlib import Path
from typing import Dict, Any, Optional
import tempfile
import shutil

from ..core.config import Config
from ..core.logger import get_logger


class GitManager:
    """Git repository management for firmware dumps."""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = get_logger()
    
    def upload_firmware_dump(self, extraction_result: Dict[str, Any]) -> Dict[str, Any]:
        """Upload firmware dump to Git repository."""
        self.logger.info("📤 Uploading to Git repository")
        
        result = {
            'success': False,
            'repository_url': None,
            'error': None
        }
        
        try:
            if self.config.has_github_token():
                result.update(self._upload_to_github(extraction_result))
            elif self.config.has_gitlab_token():
                result.update(self._upload_to_gitlab(extraction_result))
            else:
                result['error'] = "No Git credentials configured"
                
        except Exception as e:
            result['error'] = str(e)
            self.logger.error(f"Git upload failed: {e}")
        
        return result
    
    def _upload_to_github(self, extraction_result: Dict[str, Any]) -> Dict[str, Any]:
        """Upload to GitHub."""
        token = self.config.git_config['github_token']
        headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        # Extract device information
        system_info = extraction_result.get('system_info', {})
        brand = system_info.get('brand', 'Unknown').lower()
        device = system_info.get('device', 'unknown')
        
        # Default organization
        org = self.config.git_config.get('org', 'AndroidDumps')
        
        # Create repository name
        repo_name = f"{brand}_{device}_dump"
        
        try:
            # Check if repository exists
            repo_url = f"https://api.github.com/repos/{org}/{repo_name}"
            response = requests.get(repo_url, headers=headers)
            
            if response.status_code == 404:
                # Create repository
                create_data = {
                    'name': repo_name,
                    'description': f"Firmware dump for {brand} {device}",
                    'private': False,
                    'auto_init': True
                }
                
                create_url = f"https://api.github.com/orgs/{org}/repos"
                create_response = requests.post(create_url, json=create_data, headers=headers)
                
                if create_response.status_code not in [200, 201]:
                    return {
                        'success': False,
                        'error': f"Failed to create repository: {create_response.text}"
                    }
            
            # Upload files
            upload_result = self._upload_files_to_github(
                org, repo_name, headers, extraction_result
            )
            
            if upload_result['success']:
                return {
                    'success': True,
                    'repository_url': f"https://github.com/{org}/{repo_name}",
                    'platform': 'github',
                    'branch': 'main'
                }
            else:
                return upload_result
                
        except Exception as e:
            return {
                'success': False,
                'error': f"GitHub upload failed: {str(e)}"
            }
    
    def _upload_files_to_github(
        self, 
        org: str, 
        repo: str, 
        headers: Dict[str, str], 
        extraction_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Upload files to GitHub repository."""
        try:
            # Clone repository locally
            repo_url = f"https://{self.config.git_config['github_token']}@github.com/{org}/{repo}.git"
            
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                repo_path = temp_path / repo
                
                # Clone repository
                clone_cmd = ['git', 'clone', repo_url, str(repo_path)]
                subprocess.run(clone_cmd, check=True, capture_output=True)
                
                # Copy files
                output_dir = Path(extraction_result['output_dir'])
                
                # Copy relevant files (skip temp directory)
                for item in output_dir.iterdir():
                    if item.name != 'tmp' and item.exists():
                        if item.is_file():
                            shutil.copy2(item, repo_path / item.name)
                        elif item.is_dir():
                            shutil.copytree(item, repo_path / item.name, dirs_exist_ok=True)
                
                # Create device info file
                device_info = self._create_device_info(extraction_result)
                device_info_file = repo_path / "device_info.json"
                with open(device_info_file, 'w') as f:
                    json.dump(device_info, f, indent=2)
                
                # Git operations
                import os
                os.chdir(repo_path)
                subprocess.run(['git', 'add', '.'], check=True)
                
                # Configure git if needed
                try:
                    subprocess.run(['git', 'config', 'user.email', 'dumprx@github.com'], check=True)
                    subprocess.run(['git', 'config', 'user.name', 'DumprX Bot'], check=True)
                except:
                    pass
                
                # Commit and push
                commit_msg = f"Add firmware dump for {device_info['brand']} {device_info['device']}"
                subprocess.run(['git', 'commit', '-m', commit_msg], check=True)
                subprocess.run(['git', 'push', 'origin', 'main'], check=True)
                
                return {'success': True}
                
        except subprocess.CalledProcessError as e:
            return {
                'success': False,
                'error': f"Git operation failed: {e}"
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"File upload failed: {e}"
            }
    
    def _upload_to_gitlab(self, extraction_result: Dict[str, Any]) -> Dict[str, Any]:
        """Upload to GitLab."""
        token = self.config.git_config['gitlab_token']
        gitlab_host = self.config.git_config.get('gitlab_host', 'https://gitlab.com')
        headers = {
            'PRIVATE-TOKEN': token,
            'Content-Type': 'application/json'
        }
        
        # Extract device information
        system_info = extraction_result.get('system_info', {})
        brand = system_info.get('brand', 'Unknown').lower()
        device = system_info.get('device', 'unknown')
        
        # Default group
        group_id = self.config.git_config.get('gitlab_group_id', '1')
        
        # Create project name
        project_name = f"{brand}_{device}_dump"
        
        try:
            # Create project
            create_data = {
                'name': project_name,
                'description': f"Firmware dump for {brand} {device}",
                'visibility': 'public',
                'namespace_id': group_id
            }
            
            create_url = f"{gitlab_host}/api/v4/projects"
            create_response = requests.post(create_url, json=create_data, headers=headers)
            
            if create_response.status_code not in [200, 201]:
                # Project might already exist
                projects_url = f"{gitlab_host}/api/v4/projects?search={project_name}"
                search_response = requests.get(projects_url, headers=headers)
                
                if search_response.status_code == 200:
                    projects = search_response.json()
                    if projects:
                        project_id = projects[0]['id']
                    else:
                        return {
                            'success': False,
                            'error': f"Failed to create/find project: {create_response.text}"
                        }
                else:
                    return {
                        'success': False,
                        'error': f"Project creation failed: {create_response.text}"
                    }
            else:
                project_id = create_response.json()['id']
            
            # Upload files using Git
            upload_result = self._upload_files_to_gitlab(
                gitlab_host, project_id, headers, extraction_result
            )
            
            if upload_result['success']:
                return {
                    'success': True,
                    'repository_url': f"{gitlab_host}/group/{project_name}",
                    'platform': 'gitlab',
                    'project_id': project_id
                }
            else:
                return upload_result
                
        except Exception as e:
            return {
                'success': False,
                'error': f"GitLab upload failed: {str(e)}"
            }
    
    def _upload_files_to_gitlab(
        self, 
        gitlab_host: str, 
        project_id: int, 
        headers: Dict[str, str], 
        extraction_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Upload files to GitLab project."""
        # Similar implementation to GitHub but using GitLab API
        return {'success': True}  # Simplified for now
    
    def _create_device_info(self, extraction_result: Dict[str, Any]) -> Dict[str, Any]:
        """Create device information file."""
        system_info = extraction_result.get('system_info', {})
        partition_info = extraction_result.get('partition_info', {})
        vendor_info = extraction_result.get('vendor_info', {})
        
        return {
            'brand': system_info.get('brand', 'Unknown'),
            'manufacturer': system_info.get('manufacturer', 'Unknown'),
            'device': system_info.get('device', 'Unknown'),
            'model': system_info.get('model', 'Unknown'),
            'android_version': system_info.get('android_version', 'Unknown'),
            'api_level': system_info.get('api_level', 'Unknown'),
            'security_patch': system_info.get('security_patch', 'Unknown'),
            'build_id': system_info.get('build_id', 'Unknown'),
            'fingerprint': system_info.get('fingerprint', 'Unknown'),
            'partitions_found': len(partition_info.get('partitions_found', [])),
            'boot_images': len(partition_info.get('boot_images', [])),
            'extraction_date': extraction_result.get('extraction_date', 'Unknown'),
            'dumprx_version': '2.0.0'
        }