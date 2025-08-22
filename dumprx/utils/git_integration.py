"""
Git integration utilities
"""

import os
import subprocess
import json
from pathlib import Path
from typing import Optional, Dict, Any
import git
import requests

from dumprx.core.config import Config
from dumprx.utils.console import DumprXConsole


class GitIntegration:
    """Handles git operations for firmware uploads"""
    
    def __init__(self, config: Config, console: DumprXConsole):
        self.config = config
        self.console = console
        
    def upload_firmware(self, output_dir: Path, firmware_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Upload firmware to git repository
        
        Args:
            output_dir: Directory containing extracted firmware
            firmware_info: Information about the firmware
            
        Returns:
            Dictionary with upload results or None if failed
        """
        try:
            # Determine which git service to use
            if self.config.git.github.token:
                return self._upload_to_github(output_dir, firmware_info)
            elif self.config.git.gitlab.token:
                return self._upload_to_gitlab(output_dir, firmware_info)
            else:
                self.console.error("No git credentials configured")
                return None
                
        except Exception as e:
            self.console.error(f"Error during git upload: {e}")
            return None
            
    def _upload_to_github(self, output_dir: Path, firmware_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Upload firmware to GitHub"""
        try:
            self.console.step("Uploading to GitHub...")
            
            # Get device info for repository name
            device_name = firmware_info.get('device_name', 'unknown_device')
            brand = firmware_info.get('brand', 'unknown')
            repo_name = f"android_dump_{brand}_{device_name}".lower()
            
            # Create or get repository
            repo_url = self._create_github_repo(repo_name, firmware_info)
            if not repo_url:
                return None
                
            # Initialize git repository in output directory
            repo = self._init_git_repo(output_dir, repo_url)
            if not repo:
                return None
                
            # Add files and commit
            self._commit_firmware_files(repo, firmware_info)
            
            # Push to GitHub
            self._push_to_remote(repo, "main")
            
            github_url = f"https://github.com/{self.config.git.github.organization or 'user'}/{repo_name}"
            
            self.console.success(f"Successfully uploaded to GitHub: {github_url}")
            
            return {
                'service': 'github',
                'url': github_url,
                'repository': repo_name,
                'branch': 'main'
            }
            
        except Exception as e:
            self.console.error(f"GitHub upload failed: {e}")
            return None
            
    def _upload_to_gitlab(self, output_dir: Path, firmware_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Upload firmware to GitLab"""
        try:
            self.console.step("Uploading to GitLab...")
            
            # Get device info for repository name
            device_name = firmware_info.get('device_name', 'unknown_device')
            brand = firmware_info.get('brand', 'unknown')
            repo_name = f"android_dump_{brand}_{device_name}".lower()
            
            # Create or get repository
            repo_url = self._create_gitlab_repo(repo_name, firmware_info)
            if not repo_url:
                return None
                
            # Initialize git repository in output directory
            repo = self._init_git_repo(output_dir, repo_url)
            if not repo:
                return None
                
            # Add files and commit
            self._commit_firmware_files(repo, firmware_info)
            
            # Push to GitLab
            self._push_to_remote(repo, "main")
            
            gitlab_instance = self.config.git.gitlab.instance
            gitlab_url = f"https://{gitlab_instance}/{self.config.git.gitlab.group or 'user'}/{repo_name}"
            
            self.console.success(f"Successfully uploaded to GitLab: {gitlab_url}")
            
            return {
                'service': 'gitlab',
                'url': gitlab_url,
                'repository': repo_name,
                'branch': 'main'
            }
            
        except Exception as e:
            self.console.error(f"GitLab upload failed: {e}")
            return None
            
    def _create_github_repo(self, repo_name: str, firmware_info: Dict[str, Any]) -> Optional[str]:
        """Create GitHub repository"""
        try:
            headers = {
                'Authorization': f'token {self.config.git.github.token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            # Check if repository already exists
            org = self.config.git.github.organization
            if org:
                check_url = f"https://api.github.com/repos/{org}/{repo_name}"
            else:
                check_url = f"https://api.github.com/repos/{self._get_github_username()}/{repo_name}"
                
            response = requests.get(check_url, headers=headers)
            
            if response.status_code == 200:
                # Repository exists
                repo_data = response.json()
                return repo_data['clone_url'].replace('https://', f'https://{self.config.git.github.token}@')
                
            # Create new repository
            description = f"Firmware dump for {firmware_info.get('brand', 'Unknown')} {firmware_info.get('model', 'Unknown')}"
            
            repo_data = {
                'name': repo_name,
                'description': description,
                'private': False,
                'auto_init': False
            }
            
            if org:
                create_url = f"https://api.github.com/orgs/{org}/repos"
            else:
                create_url = "https://api.github.com/user/repos"
                
            response = requests.post(create_url, headers=headers, json=repo_data)
            
            if response.status_code == 201:
                repo_info = response.json()
                return repo_info['clone_url'].replace('https://', f'https://{self.config.git.github.token}@')
            else:
                self.console.error(f"Failed to create GitHub repository: {response.text}")
                return None
                
        except Exception as e:
            self.console.error(f"Error creating GitHub repository: {e}")
            return None
            
    def _create_gitlab_repo(self, repo_name: str, firmware_info: Dict[str, Any]) -> Optional[str]:
        """Create GitLab repository"""
        try:
            headers = {
                'PRIVATE-TOKEN': self.config.git.gitlab.token,
                'Content-Type': 'application/json'
            }
            
            gitlab_instance = self.config.git.gitlab.instance
            base_url = f"https://{gitlab_instance}/api/v4"
            
            # Check if repository already exists
            group = self.config.git.gitlab.group
            if group:
                # Get group ID
                group_url = f"{base_url}/groups/{group}"
                group_response = requests.get(group_url, headers=headers)
                
                if group_response.status_code == 200:
                    group_id = group_response.json()['id']
                    
                    # Check if project exists in group
                    projects_url = f"{base_url}/groups/{group_id}/projects"
                    projects_response = requests.get(projects_url, headers=headers)
                    
                    if projects_response.status_code == 200:
                        for project in projects_response.json():
                            if project['name'] == repo_name:
                                # Repository exists
                                clone_url = project['http_url_to_repo']
                                token_url = clone_url.replace('https://', f'https://oauth2:{self.config.git.gitlab.token}@')
                                return token_url
                                
            # Create new repository
            description = f"Firmware dump for {firmware_info.get('brand', 'Unknown')} {firmware_info.get('model', 'Unknown')}"
            
            project_data = {
                'name': repo_name,
                'description': description,
                'visibility': 'public'
            }
            
            if group:
                project_data['namespace_id'] = group_id
                
            create_url = f"{base_url}/projects"
            response = requests.post(create_url, headers=headers, json=project_data)
            
            if response.status_code == 201:
                project_info = response.json()
                clone_url = project_info['http_url_to_repo']
                token_url = clone_url.replace('https://', f'https://oauth2:{self.config.git.gitlab.token}@')
                return token_url
            else:
                self.console.error(f"Failed to create GitLab repository: {response.text}")
                return None
                
        except Exception as e:
            self.console.error(f"Error creating GitLab repository: {e}")
            return None
            
    def _get_github_username(self) -> str:
        """Get GitHub username from API"""
        try:
            headers = {
                'Authorization': f'token {self.config.git.github.token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            response = requests.get('https://api.github.com/user', headers=headers)
            
            if response.status_code == 200:
                return response.json()['login']
            else:
                return 'user'
                
        except Exception:
            return 'user'
            
    def _init_git_repo(self, repo_dir: Path, remote_url: str) -> Optional[git.Repo]:
        """Initialize git repository"""
        try:
            # Initialize repo
            repo = git.Repo.init(repo_dir)
            
            # Configure git
            repo.config_writer().set_value("user", "name", "DumprX Bot").release()
            repo.config_writer().set_value("user", "email", "dumprx@noreply.github.com").release()
            repo.config_writer().set_value("http", "postBuffer", "524288000").release()
            
            # Add remote
            try:
                origin = repo.create_remote('origin', remote_url)
            except git.exc.GitCommandError:
                # Remote might already exist
                origin = repo.remote('origin')
                origin.set_url(remote_url)
                
            return repo
            
        except Exception as e:
            self.console.error(f"Error initializing git repository: {e}")
            return None
            
    def _commit_firmware_files(self, repo: git.Repo, firmware_info: Dict[str, Any]) -> None:
        """Add and commit firmware files"""
        try:
            # Add all files
            repo.git.add('.')
            
            # Create commit message
            brand = firmware_info.get('brand', 'Unknown')
            model = firmware_info.get('model', 'Unknown')
            android_version = firmware_info.get('android_version', 'Unknown')
            fingerprint = firmware_info.get('build_fingerprint', 'Unknown')
            
            commit_message = f"""Add {brand} {model} firmware dump

Brand: {brand}
Device: {model}
Android Version: {android_version}
Build Fingerprint: {fingerprint}

Extracted using DumprX v2.0.0
"""
            
            # Commit changes
            repo.index.commit(commit_message)
            
        except Exception as e:
            self.console.error(f"Error committing files: {e}")
            raise
            
    def _push_to_remote(self, repo: git.Repo, branch: str) -> None:
        """Push to remote repository"""
        try:
            # Set default branch
            repo.git.branch('-M', branch)
            
            # Push to remote
            origin = repo.remote('origin')
            origin.push(refspec=f'{branch}:{branch}')
            
        except Exception as e:
            self.console.error(f"Error pushing to remote: {e}")
            raise