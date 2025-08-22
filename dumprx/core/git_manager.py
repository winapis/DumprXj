import os
import logging
import requests
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List
from git import Repo, GitCommandError

logger = logging.getLogger(__name__)

class GitManager:
    def __init__(self, config_manager):
        self.config_manager = config_manager
    
    def upload_firmware(self, firmware_info: Dict[str, Any], output_dir: Path) -> Optional[str]:
        github_config = self.config_manager.get_git_config('github')
        gitlab_config = self.config_manager.get_git_config('gitlab')
        
        if github_config['token']:
            return self._upload_to_github(firmware_info, output_dir, github_config)
        elif gitlab_config['token']:
            return self._upload_to_gitlab(firmware_info, output_dir, gitlab_config)
        else:
            logger.info("No git provider configured, dumping locally only")
            return None
    
    def _upload_to_github(self, firmware_info: Dict[str, Any], output_dir: Path, config: Dict[str, Any]) -> Optional[str]:
        try:
            org = config['organization'] or self._get_git_username()
            repo_name = self._generate_repo_name(firmware_info)
            branch = firmware_info.get('branch', 'main')
            
            repo_url = f"https://github.com/{org}/{repo_name}"
            
            if self._check_repo_exists_github(org, repo_name, branch, config['token']):
                logger.info(f"Repository {repo_url} already exists")
                return repo_url
            
            self._create_github_repo(org, repo_name, config['token'])
            
            git_url = f"https://{config['token']}@github.com/{org}/{repo_name}.git"
            self._push_to_repository(output_dir, git_url, branch, firmware_info)
            
            return repo_url
            
        except Exception as e:
            logger.error(f"GitHub upload failed: {e}")
            return None
    
    def _upload_to_gitlab(self, firmware_info: Dict[str, Any], output_dir: Path, config: Dict[str, Any]) -> Optional[str]:
        try:
            instance = config['instance']
            group = config['group'] or self._get_git_username()
            repo_name = self._generate_repo_name(firmware_info)
            branch = firmware_info.get('branch', 'main')
            
            gitlab_host = f"https://{instance}"
            repo_url = f"{gitlab_host}/{group}/{repo_name}"
            
            if self._check_repo_exists_gitlab(group, repo_name, branch, config, gitlab_host):
                logger.info(f"Repository {repo_url} already exists")
                return repo_url
            
            project_id = self._create_gitlab_repo(group, repo_name, config, gitlab_host)
            
            git_url = f"git@{instance}:{group}/{repo_name}.git"
            self._push_to_repository(output_dir, git_url, branch, firmware_info)
            
            self._update_gitlab_default_branch(project_id, branch, config, gitlab_host)
            
            return repo_url
            
        except Exception as e:
            logger.error(f"GitLab upload failed: {e}")
            return None
    
    def _generate_repo_name(self, firmware_info: Dict[str, Any]) -> str:
        brand = firmware_info.get('brand', 'unknown').lower()
        device = firmware_info.get('codename', 'unknown').lower()
        return f"{brand}_{device}_dump"
    
    def _get_git_username(self) -> str:
        try:
            result = subprocess.run(['git', 'config', '--get', 'user.name'], 
                                  capture_output=True, text=True)
            return result.stdout.strip() or 'DumprX'
        except Exception:
            return 'DumprX'
    
    def _check_repo_exists_github(self, org: str, repo: str, branch: str, token: str) -> bool:
        try:
            url = f"https://api.github.com/repos/{org}/{repo}/contents/all_files.txt"
            headers = {'Authorization': f'token {token}'}
            params = {'ref': branch}
            
            response = requests.get(url, headers=headers, params=params)
            return response.status_code == 200
        except Exception:
            return False
    
    def _check_repo_exists_gitlab(self, group: str, repo: str, branch: str, config: Dict[str, Any], host: str) -> bool:
        try:
            url = f"{host}/{group}/{repo}/-/raw/{branch}/all_files.txt"
            response = requests.get(url)
            return response.status_code == 200 and 'all_files.txt' in response.text
        except Exception:
            return False
    
    def _create_github_repo(self, org: str, repo_name: str, token: str):
        headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        data = {
            'name': repo_name,
            'private': False,
            'description': f'Firmware dump for {repo_name}'
        }
        
        if org != self._get_git_username():
            url = f"https://api.github.com/orgs/{org}/repos"
        else:
            url = "https://api.github.com/user/repos"
        
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
    
    def _create_gitlab_repo(self, group: str, repo_name: str, config: Dict[str, Any], host: str) -> int:
        headers = {'PRIVATE-TOKEN': config['token']}
        
        group_url = f"{host}/api/v4/groups/{group}"
        group_response = requests.get(group_url, headers=headers)
        
        if group_response.status_code == 404:
            group_data = {
                'name': group,
                'path': group.lower(),
                'visibility': 'public'
            }
            create_group_url = f"{host}/api/v4/groups"
            requests.post(create_group_url, json=group_data, headers=headers)
        
        project_data = {
            'name': repo_name,
            'path': repo_name.lower(),
            'namespace_id': group_response.json().get('id') if group_response.status_code == 200 else None,
            'visibility': 'public'
        }
        
        create_project_url = f"{host}/api/v4/projects"
        project_response = requests.post(create_project_url, json=project_data, headers=headers)
        project_response.raise_for_status()
        
        return project_response.json()['id']
    
    def _push_to_repository(self, output_dir: Path, git_url: str, branch: str, firmware_info: Dict[str, Any]):
        os.chdir(output_dir)
        
        repo = Repo.init()
        
        if not repo.remotes:
            repo.create_remote('origin', git_url)
        
        self._commit_and_push_files(repo, branch, firmware_info)
    
    def _commit_and_push_files(self, repo: Repo, branch: str, firmware_info: Dict[str, Any]):
        description = f"{firmware_info.get('brand', '')} {firmware_info.get('codename', '')}"
        
        dirs_to_commit = [
            'app', 'priv-app', 'system_ext', 'product', 'vendor', 
            'odm', 'oem', 'factory', 'firmware', 'radio'
        ]
        
        apk_files = list(Path('.').glob('**/*.apk'))
        if apk_files:
            repo.index.add([str(f) for f in apk_files])
            repo.index.commit(f"Add apps for {description}")
            repo.remote('origin').push(f"{branch}:{branch}")
        
        for dir_name in dirs_to_commit:
            paths_to_add = []
            for potential_path in [dir_name, f"system/{dir_name}", f"system/system/{dir_name}", f"vendor/{dir_name}"]:
                if Path(potential_path).exists():
                    paths_to_add.append(potential_path)
            
            if paths_to_add:
                repo.index.add(paths_to_add)
                repo.index.commit(f"Add {dir_name} for {description}")
                repo.remote('origin').push(f"{branch}:{branch}")
        
        repo.index.add(['.'])
        repo.index.commit(f"Add extras for {description}")
        repo.remote('origin').push(f"{branch}:{branch}")
    
    def _update_gitlab_default_branch(self, project_id: int, branch: str, config: Dict[str, Any], host: str):
        headers = {'PRIVATE-TOKEN': config['token']}
        url = f"{host}/api/v4/projects/{project_id}"
        data = {'default_branch': branch}
        
        requests.put(url, json=data, headers=headers)