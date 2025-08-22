import os
import subprocess
import asyncio
import tempfile
import shutil
from typing import Dict, List, Optional, Any
from pathlib import Path
import aiohttp
import json

from .ui import UI, ProgressBar
from .logging import get_logger

logger = get_logger()


class GitError(Exception):
    pass


class GitHubIntegration:
    def __init__(self, token: str, organization: str, username: Optional[str] = None):
        self.token = token
        self.organization = organization
        self.username = username
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }

    async def create_repository(self, repo_name: str, description: str = "") -> Dict[str, Any]:
        url = f"{self.base_url}/orgs/{self.organization}/repos"
        
        data = {
            "name": repo_name,
            "description": description,
            "private": False,
            "has_issues": True,
            "has_projects": False,
            "has_wiki": False
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=self.headers, json=data) as response:
                if response.status == 201:
                    return await response.json()
                elif response.status == 422:
                    logger.info(f"Repository {repo_name} already exists")
                    return await self.get_repository(repo_name)
                else:
                    raise GitError(f"Failed to create repository: {response.status}")

    async def get_repository(self, repo_name: str) -> Dict[str, Any]:
        url = f"{self.base_url}/repos/{self.organization}/{repo_name}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise GitError(f"Repository not found: {repo_name}")

    def get_clone_url(self, repo_name: str, use_ssh: bool = False) -> str:
        if use_ssh:
            return f"git@github.com:{self.organization}/{repo_name}.git"
        else:
            return f"https://github.com/{self.organization}/{repo_name}.git"


class GitLabIntegration:
    def __init__(self, token: str, group: str, instance: str = "gitlab.com"):
        self.token = token
        self.group = group
        self.instance = instance
        self.base_url = f"https://{instance}/api/v4"
        self.headers = {
            "Private-Token": token,
            "Content-Type": "application/json"
        }

    async def create_repository(self, repo_name: str, description: str = "") -> Dict[str, Any]:
        group_id = await self.get_group_id()
        
        url = f"{self.base_url}/projects"
        data = {
            "name": repo_name,
            "namespace_id": group_id,
            "description": description,
            "visibility": "public",
            "issues_enabled": True,
            "merge_requests_enabled": False,
            "wiki_enabled": False
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=self.headers, json=data) as response:
                if response.status == 201:
                    return await response.json()
                elif response.status == 400:
                    logger.info(f"Repository {repo_name} already exists")
                    return await self.get_repository(repo_name)
                else:
                    raise GitError(f"Failed to create repository: {response.status}")

    async def get_group_id(self) -> int:
        url = f"{self.base_url}/groups/{self.group}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as response:
                if response.status == 200:
                    group_data = await response.json()
                    return group_data["id"]
                else:
                    raise GitError(f"Group not found: {self.group}")

    async def get_repository(self, repo_name: str) -> Dict[str, Any]:
        projects_url = f"{self.base_url}/groups/{self.group}/projects"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(projects_url, headers=self.headers) as response:
                if response.status == 200:
                    projects = await response.json()
                    for project in projects:
                        if project["name"] == repo_name:
                            return project
                    raise GitError(f"Repository not found: {repo_name}")
                else:
                    raise GitError(f"Failed to get projects: {response.status}")

    async def set_repository_visibility(self, project_id: int, visibility: str = "public") -> None:
        url = f"{self.base_url}/projects/{project_id}"
        data = {"visibility": visibility}
        
        async with aiohttp.ClientSession() as session:
            async with session.put(url, headers=self.headers, json=data) as response:
                if response.status != 200:
                    logger.warning(f"Failed to set repository visibility: {response.status}")

    async def set_default_branch(self, project_id: int, branch: str) -> None:
        url = f"{self.base_url}/projects/{project_id}"
        data = {"default_branch": branch}
        
        async with aiohttp.ClientSession() as session:
            async with session.put(url, headers=self.headers, json=data) as response:
                if response.status != 200:
                    logger.warning(f"Failed to set default branch: {response.status}")

    def get_clone_url(self, repo_name: str, use_ssh: bool = True) -> str:
        if use_ssh:
            return f"git@{self.instance}:{self.group}/{repo_name}.git"
        else:
            return f"https://{self.instance}/{self.group}/{repo_name}.git"


class GitManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.github_config = config.get('github', {})
        self.gitlab_config = config.get('gitlab', {})
        
        self.github = None
        self.gitlab = None
        
        if self.github_config.get('token'):
            self.github = GitHubIntegration(
                self.github_config['token'],
                self.github_config.get('organization', ''),
                self.github_config.get('username')
            )
        
        if self.gitlab_config.get('token'):
            self.gitlab = GitLabIntegration(
                self.gitlab_config['token'],
                self.gitlab_config.get('group', ''),
                self.gitlab_config.get('instance', 'gitlab.com')
            )

    async def setup_repository(self, repo_name: str, output_dir: str, 
                             use_gitlab: bool = False) -> str:
        if use_gitlab and self.gitlab:
            return await self._setup_gitlab_repository(repo_name, output_dir)
        elif not use_gitlab and self.github:
            return await self._setup_github_repository(repo_name, output_dir)
        else:
            raise GitError("No git provider configured")

    async def _setup_github_repository(self, repo_name: str, output_dir: str) -> str:
        UI.print_info(f"Creating GitHub repository: {repo_name}")
        
        await self.github.create_repository(repo_name, "Firmware dump extracted by DumprX")
        clone_url = self.github.get_clone_url(repo_name)
        
        await self._setup_git_repo(output_dir, clone_url)
        return clone_url

    async def _setup_gitlab_repository(self, repo_name: str, output_dir: str) -> str:
        UI.print_info(f"Creating GitLab repository: {repo_name}")
        
        repo_data = await self.gitlab.create_repository(repo_name, "Firmware dump extracted by DumprX")
        clone_url = self.gitlab.get_clone_url(repo_name, use_ssh=True)
        
        await self._setup_git_repo(output_dir, clone_url)
        return clone_url

    async def _setup_git_repo(self, repo_dir: str, remote_url: str) -> None:
        commands = [
            ['git', 'init'],
            ['git', 'config', 'http.postBuffer', '524288000'],
            ['git', 'lfs', 'install'],
            ['git', 'remote', 'add', 'origin', remote_url]
        ]

        for cmd in commands:
            await self._run_git_command(cmd, repo_dir)

    async def commit_and_push(self, repo_dir: str, branch: str = "main", 
                            message: str = "Add firmware dump") -> None:
        UI.print_info("Preparing files for commit")
        
        await self._setup_git_lfs(repo_dir)
        await self._create_gitignore(repo_dir)
        
        commands = [
            ['git', 'checkout', '-b', branch],
            ['git', 'add', '.'],
            ['git', 'commit', '-m', message],
            ['git', 'push', '-u', 'origin', branch]
        ]

        for cmd in commands:
            try:
                await self._run_git_command(cmd, repo_dir)
            except GitError as e:
                if 'already exists' in str(e) and 'checkout' in cmd:
                    await self._run_git_command(['git', 'checkout', branch], repo_dir)
                else:
                    raise

    async def _setup_git_lfs(self, repo_dir: str) -> None:
        gitattributes_path = os.path.join(repo_dir, '.gitattributes')
        
        if not os.path.exists(gitattributes_path):
            large_files = []
            for root, dirs, files in os.walk(repo_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    if os.path.getsize(file_path) > 100 * 1024 * 1024:  # 100MB
                        rel_path = os.path.relpath(file_path, repo_dir)
                        large_files.append(rel_path)
            
            if large_files:
                with open(gitattributes_path, 'w') as f:
                    for file_path in large_files:
                        f.write(f"{file_path} filter=lfs diff=lfs merge=lfs -text\n")
                
                await self._run_git_command(['git', 'add', '.gitattributes'], repo_dir)
                await self._run_git_command(['git', 'commit', '-m', 'Setup Git LFS'], repo_dir)

    async def _create_gitignore(self, repo_dir: str) -> None:
        gitignore_path = os.path.join(repo_dir, '.gitignore')
        
        ignore_patterns = []
        for root, dirs, files in os.walk(repo_dir):
            for file in files:
                if 'sensetime' in file.lower() or file.endswith('.lic'):
                    rel_path = os.path.relpath(os.path.join(root, file), repo_dir)
                    ignore_patterns.append(rel_path)
        
        if ignore_patterns:
            with open(gitignore_path, 'w') as f:
                for pattern in ignore_patterns:
                    f.write(f"{pattern}\n")

    async def _run_git_command(self, cmd: List[str], cwd: str) -> str:
        process = await asyncio.create_subprocess_exec(
            *cmd, cwd=cwd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error_msg = stderr.decode().strip()
            raise GitError(f"Git command failed: {' '.join(cmd)}\n{error_msg}")
        
        return stdout.decode().strip()

    def generate_readme(self, firmware_info: Dict[str, Any], partitions: List[str], 
                       output_dir: str) -> None:
        readme_content = self._generate_readme_content(firmware_info, partitions)
        
        readme_path = os.path.join(output_dir, 'README.md')
        with open(readme_path, 'w') as f:
            f.write(readme_content)

    def _generate_readme_content(self, firmware_info: Dict[str, Any], 
                                partitions: List[str]) -> str:
        info = firmware_info.get('firmware_info')
        if not info:
            info = type('obj', (object,), {
                'brand': 'Unknown', 'model': 'Unknown', 'version': 'Unknown',
                'build_id': 'Unknown', 'fingerprint': 'Unknown', 'platform': 'Unknown'
            })()

        readme = f"""# {info.brand} {info.model} Firmware Dump

## Device Information
- **Brand**: {info.brand or 'Unknown'}
- **Model**: {info.model or 'Unknown'}
- **Android Version**: {info.version or 'Unknown'}
- **Build ID**: {info.build_id or 'Unknown'}
- **Platform**: {info.platform or 'Unknown'}
- **Fingerprint**: {info.fingerprint or 'Unknown'}

## Extracted Partitions
"""
        
        for partition in sorted(partitions):
            readme += f"- {partition}.img\n"
        
        readme += f"""
## Extraction Information
- **Extracted with**: DumprX v2.0
- **Extraction Date**: {self._get_current_date()}
- **Total Partitions**: {len(partitions)}

## File Structure
```
.
├── README.md           # This file
├── all_files.txt      # List of all extracted files
├── all_files.sha1     # SHA1 checksums
"""
        
        for partition in sorted(partitions):
            readme += f"├── {partition}.img\n"
        
        readme += """└── ...
```

---
*Generated by DumprX - Advanced Firmware Extraction Tool*
"""
        
        return readme

    def _get_current_date(self) -> str:
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

    def generate_file_list(self, output_dir: str) -> None:
        all_files = []
        
        for root, dirs, files in os.walk(output_dir):
            for file in files:
                if not file.startswith('.git'):
                    rel_path = os.path.relpath(os.path.join(root, file), output_dir)
                    all_files.append(rel_path)
        
        all_files.sort()
        
        with open(os.path.join(output_dir, 'all_files.txt'), 'w') as f:
            for file_path in all_files:
                f.write(f"{file_path}\n")

    def generate_checksums(self, output_dir: str) -> None:
        import hashlib
        
        checksums = []
        
        for root, dirs, files in os.walk(output_dir):
            for file in files:
                if file.startswith('.git') or file == 'all_files.sha1':
                    continue
                
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, output_dir)
                
                try:
                    with open(file_path, 'rb') as f:
                        sha1_hash = hashlib.sha1()
                        for chunk in iter(lambda: f.read(4096), b""):
                            sha1_hash.update(chunk)
                        
                        checksums.append(f"{sha1_hash.hexdigest()}  {rel_path}")
                except Exception as e:
                    logger.warning(f"Failed to calculate checksum for {rel_path}: {e}")
        
        checksums.sort()
        
        with open(os.path.join(output_dir, 'all_files.sha1'), 'w') as f:
            for checksum in checksums:
                f.write(f"{checksum}\n")