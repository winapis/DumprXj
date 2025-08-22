#!/usr/bin/env python3

import os
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Optional, Tuple

from dumprx.console import info, warning, error, step, success
from dumprx.config import config


class GitManager:
    
    def __init__(self):
        self.github_token = config.get('git', 'github', 'token')
        self.github_org = config.get('git', 'github', 'organization')
        self.gitlab_token = config.get('git', 'gitlab', 'token')
        self.gitlab_group = config.get('git', 'gitlab', 'group')
        self.gitlab_instance = config.get('git', 'gitlab', 'instance', default='gitlab.com')
    
    def has_github_config(self) -> bool:
        return bool(self.github_token)
    
    def has_gitlab_config(self) -> bool:
        return bool(self.gitlab_token)
    
    def create_and_push_repo(self, firmware_info: Dict, output_dir: str) -> Optional[Dict]:
        if self.has_github_config():
            return self._create_github_repo(firmware_info, output_dir)
        elif self.has_gitlab_config():
            return self._create_gitlab_repo(firmware_info, output_dir)
        else:
            error("No Git configuration found")
            return None
    
    def _create_github_repo(self, firmware_info: Dict, output_dir: str) -> Optional[Dict]:
        step("Creating GitHub repository and pushing files")
        
        try:
            codename = firmware_info.get('device', 'unknown')
            brand = firmware_info.get('brand', 'unknown')
            repo_name = f"{brand}_{codename}"
            
            org = self.github_org or self._get_github_username()
            if not org:
                error("Could not determine GitHub organization/username")
                return None
            
            repo_exists = self._check_github_repo_exists(org, repo_name)
            if not repo_exists:
                if not self._create_github_repository(org, repo_name, firmware_info):
                    return None
            
            branch = f"{brand}-{codename}"
            repo_url = f"https://github.com/{org}/{repo_name}"
            
            if not self._setup_git_repo(output_dir, repo_url, branch, firmware_info):
                return None
            
            success(f"Repository created and pushed: {repo_url}")
            
            return {
                'organization': org,
                'name': repo_name,
                'branch': branch,
                'url': repo_url
            }
            
        except Exception as e:
            error(f"GitHub repository creation failed: {str(e)}")
            return None
    
    def _create_gitlab_repo(self, firmware_info: Dict, output_dir: str) -> Optional[Dict]:
        step("Creating GitLab repository and pushing files")
        
        try:
            codename = firmware_info.get('device', 'unknown')
            brand = firmware_info.get('brand', 'unknown')
            repo_name = f"{brand}_{codename}"
            
            group = self.gitlab_group or self._get_gitlab_username()
            if not group:
                error("Could not determine GitLab group/username")
                return None
            
            project_id = self._get_or_create_gitlab_project(group, repo_name, firmware_info)
            if not project_id:
                return None
            
            branch = f"{brand}-{codename}"
            repo_url = f"https://{self.gitlab_instance}/{group}/{repo_name}"
            
            if not self._setup_git_repo(output_dir, repo_url, branch, firmware_info, gitlab=True):
                return None
            
            self._set_gitlab_default_branch(project_id, branch)
            
            success(f"Repository created and pushed: {repo_url}")
            
            return {
                'organization': group,
                'name': repo_name,
                'branch': branch,
                'url': repo_url
            }
            
        except Exception as e:
            error(f"GitLab repository creation failed: {str(e)}")
            return None
    
    def _get_github_username(self) -> Optional[str]:
        try:
            cmd = ['curl', '-s', '-H', f'Authorization: token {self.github_token}', 
                   'https://api.github.com/user']
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return data.get('login')
        except:
            pass
        return None
    
    def _get_gitlab_username(self) -> Optional[str]:
        try:
            cmd = ['curl', '-s', '--header', f'PRIVATE-TOKEN: {self.gitlab_token}',
                   f'https://{self.gitlab_instance}/api/v4/user']
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return data.get('username')
        except:
            pass
        return None
    
    def _check_github_repo_exists(self, org: str, repo_name: str) -> bool:
        try:
            cmd = ['curl', '-s', '-H', f'Authorization: token {self.github_token}',
                   f'https://api.github.com/repos/{org}/{repo_name}']
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return result.returncode == 0
        except:
            return False
    
    def _create_github_repository(self, org: str, repo_name: str, firmware_info: Dict) -> bool:
        try:
            brand = firmware_info.get('brand', 'Unknown')
            device = firmware_info.get('device', 'Unknown')
            description = f"Firmware dump for {brand} {device}"
            
            data = {
                'name': repo_name,
                'description': description,
                'private': False,
                'has_issues': True,
                'has_projects': False,
                'has_wiki': False
            }
            
            if org != self._get_github_username():
                url = f'https://api.github.com/orgs/{org}/repos'
            else:
                url = 'https://api.github.com/user/repos'
            
            cmd = ['curl', '-s', '-X', 'POST', '-H', f'Authorization: token {self.github_token}',
                   '-H', 'Content-Type: application/json', '-d', json.dumps(data), url]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return result.returncode == 0
            
        except Exception as e:
            error(f"Failed to create GitHub repository: {str(e)}")
            return False
    
    def _get_or_create_gitlab_project(self, group: str, repo_name: str, firmware_info: Dict) -> Optional[str]:
        try:
            group_id = self._get_gitlab_group_id(group)
            if not group_id:
                error(f"GitLab group '{group}' not found")
                return None
            
            project_id = self._get_gitlab_project_id(group_id, repo_name)
            if project_id:
                return project_id
            
            return self._create_gitlab_project(group_id, repo_name, firmware_info)
            
        except Exception as e:
            error(f"Failed to get/create GitLab project: {str(e)}")
            return None
    
    def _get_gitlab_group_id(self, group: str) -> Optional[str]:
        try:
            cmd = ['curl', '-s', '--header', f'PRIVATE-TOKEN: {self.gitlab_token}',
                   f'https://{self.gitlab_instance}/api/v4/groups/{group}']
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return str(data.get('id'))
        except:
            pass
        return None
    
    def _get_gitlab_project_id(self, group_id: str, project_name: str) -> Optional[str]:
        try:
            cmd = ['curl', '-s', '--header', f'PRIVATE-TOKEN: {self.gitlab_token}',
                   f'https://{self.gitlab_instance}/api/v4/groups/{group_id}/projects']
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                projects = json.loads(result.stdout)
                for project in projects:
                    if project.get('path') == project_name:
                        return str(project.get('id'))
        except:
            pass
        return None
    
    def _create_gitlab_project(self, group_id: str, repo_name: str, firmware_info: Dict) -> Optional[str]:
        try:
            brand = firmware_info.get('brand', 'Unknown')
            device = firmware_info.get('device', 'Unknown')
            description = f"Firmware dump for {brand} {device}"
            
            data = {
                'name': repo_name,
                'path': repo_name,
                'description': description,
                'namespace_id': group_id,
                'visibility': 'public'
            }
            
            cmd = ['curl', '-s', '-X', 'POST', '--header', f'PRIVATE-TOKEN: {self.gitlab_token}',
                   '--header', 'Content-Type: application/json',
                   '--data', json.dumps(data),
                   f'https://{self.gitlab_instance}/api/v4/projects']
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return str(data.get('id'))
            
        except Exception as e:
            error(f"Failed to create GitLab project: {str(e)}")
        
        return None
    
    def _set_gitlab_default_branch(self, project_id: str, branch: str):
        try:
            data = {'default_branch': branch}
            
            cmd = ['curl', '-s', '-X', 'PUT', '--header', f'PRIVATE-TOKEN: {self.gitlab_token}',
                   '--header', 'Content-Type: application/json',
                   '--data', json.dumps(data),
                   f'https://{self.gitlab_instance}/api/v4/projects/{project_id}']
            
            subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
        except Exception as e:
            warning(f"Failed to set GitLab default branch: {str(e)}")
    
    def _setup_git_repo(self, output_dir: str, repo_url: str, branch: str, 
                       firmware_info: Dict, gitlab: bool = False) -> bool:
        try:
            os.chdir(output_dir)
            
            subprocess.run(['git', 'init'], check=True, capture_output=True)
            subprocess.run(['git', 'lfs', 'install'], check=True, capture_output=True)
            subprocess.run(['git', 'lfs', 'track', '*.img', '*.bin', '*.gz', '*.zip'], 
                          check=True, capture_output=True)
            
            subprocess.run(['git', 'config', 'user.name', 'DumprX'], check=True, capture_output=True)
            subprocess.run(['git', 'config', 'user.email', 'dumprx@github.com'], check=True, capture_output=True)
            
            subprocess.run(['git', 'add', '.'], check=True, capture_output=True)
            
            commit_message = self._generate_commit_message(firmware_info)
            subprocess.run(['git', 'commit', '-m', commit_message], check=True, capture_output=True)
            
            subprocess.run(['git', 'branch', '-M', branch], check=True, capture_output=True)
            
            if gitlab:
                auth_url = repo_url.replace('https://', f'https://gitlab-ci-token:{self.gitlab_token}@')
            else:
                auth_url = repo_url.replace('https://', f'https://{self.github_token}@')
            
            subprocess.run(['git', 'remote', 'add', 'origin', auth_url], check=True, capture_output=True)
            subprocess.run(['git', 'push', '-u', 'origin', branch], check=True, capture_output=True)
            
            return True
            
        except subprocess.CalledProcessError as e:
            error(f"Git operation failed: {str(e)}")
            return False
        except Exception as e:
            error(f"Git setup failed: {str(e)}")
            return False
    
    def _generate_commit_message(self, firmware_info: Dict) -> str:
        brand = firmware_info.get('brand', 'Unknown')
        device = firmware_info.get('device', 'Unknown')
        android_version = firmware_info.get('android_version', 'Unknown')
        
        return f"{brand}: {device} - Android {android_version}"


git_manager = GitManager()