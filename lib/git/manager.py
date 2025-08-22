import asyncio
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any
from lib.core.logger import logger
from lib.core.config import config
from lib.core.exceptions import GitOperationError
from lib.utils.command import run_command

class GitManager:
    def __init__(self):
        self.github_token = self._get_token_from_file('.github_token')
        self.github_org = self._get_token_from_file('.github_orgname')
        self.gitlab_token = self._get_token_from_file('.gitlab_token')
        self.gitlab_group = self._get_token_from_file('.gitlab_group')
        self.gitlab_instance = self._get_token_from_file('.gitlab_instance') or 'gitlab.com'
        
        self.use_gitlab = bool(self.gitlab_token)
    
    def _get_token_from_file(self, filename: str) -> Optional[str]:
        try:
            with open(filename, 'r') as f:
                return f.read().strip()
        except FileNotFoundError:
            return None
    
    async def upload_results(self, output_path: Path) -> None:
        if not self.github_token and not self.gitlab_token:
            logger.warning("No git tokens configured, skipping upload")
            return
        
        if self.use_gitlab:
            await self._upload_to_gitlab(output_path)
        else:
            await self._upload_to_github(output_path)
    
    async def _upload_to_github(self, output_path: Path) -> None:
        logger.processing("Uploading results to GitHub")
        
        try:
            await self._setup_git_config()
            
            result = await run_command(['git', 'status', '--porcelain'], cwd=output_path.parent)
            if not result.stdout.strip():
                logger.info("No changes to commit")
                return
            
            device_info = await self._extract_device_info(output_path)
            commit_message = f"Add firmware dump for {device_info.get('codename', 'unknown')}"
            
            await run_command(['git', 'add', '.'], cwd=output_path.parent)
            await run_command(['git', 'commit', '-m', commit_message], cwd=output_path.parent)
            
            if self.github_org:
                remote_url = f"https://{self.github_token}@github.com/{self.github_org}/dumps.git"
            else:
                username = await self._get_github_username()
                remote_url = f"https://{self.github_token}@github.com/{username}/dumps.git"
            
            await run_command(['git', 'remote', 'set-url', 'origin', remote_url], cwd=output_path.parent)
            await run_command(['git', 'push', 'origin', 'main'], cwd=output_path.parent)
            
            logger.success("Successfully uploaded to GitHub")
            
        except Exception as e:
            raise GitOperationError(f"GitHub upload failed: {e}")
    
    async def _upload_to_gitlab(self, output_path: Path) -> None:
        logger.processing("Uploading results to GitLab")
        
        try:
            await self._setup_git_config()
            
            device_info = await self._extract_device_info(output_path)
            commit_message = f"Add firmware dump for {device_info.get('codename', 'unknown')}"
            
            await run_command(['git', 'add', '.'], cwd=output_path.parent)
            await run_command(['git', 'commit', '-m', commit_message], cwd=output_path.parent)
            
            if self.gitlab_group:
                remote_url = f"https://oauth2:{self.gitlab_token}@{self.gitlab_instance}/{self.gitlab_group}/dumps.git"
            else:
                username = await self._get_gitlab_username()
                remote_url = f"https://oauth2:{self.gitlab_token}@{self.gitlab_instance}/{username}/dumps.git"
            
            await run_command(['git', 'remote', 'set-url', 'origin', remote_url], cwd=output_path.parent)
            await run_command(['git', 'push', 'origin', 'main'], cwd=output_path.parent)
            
            logger.success("Successfully uploaded to GitLab")
            
        except Exception as e:
            raise GitOperationError(f"GitLab upload failed: {e}")
    
    async def _setup_git_config(self) -> None:
        await run_command(['git', 'config', 'user.name', 'DumprX Bot'])
        await run_command(['git', 'config', 'user.email', 'dumprx@example.com'])
        await run_command(['git', 'config', 'http.postBuffer', '1048576000'])
    
    async def _get_github_username(self) -> str:
        try:
            import requests
            headers = {'Authorization': f'token {self.github_token}'}
            response = requests.get('https://api.github.com/user', headers=headers)
            return response.json()['login']
        except:
            return 'dumprx-user'
    
    async def _get_gitlab_username(self) -> str:
        try:
            import requests
            headers = {'Private-Token': self.gitlab_token}
            response = requests.get(f'https://{self.gitlab_instance}/api/v4/user', headers=headers)
            return response.json()['username']
        except:
            return 'dumprx-user'
    
    async def _extract_device_info(self, output_path: Path) -> Dict[str, Any]:
        info = {}
        
        prop_files = list(output_path.glob('**/build.prop'))
        if prop_files:
            with open(prop_files[0]) as f:
                for line in f:
                    if 'ro.product.device=' in line:
                        info['codename'] = line.split('=')[1].strip()
                    elif 'ro.build.version.release=' in line:
                        info['android_version'] = line.split('=')[1].strip()
        
        return info