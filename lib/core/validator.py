import asyncio
import sys
from pathlib import Path
from typing import Dict, List
from lib.core.logger import logger
from lib.core.config import config
from lib.utils.command import run_command

class WorkflowValidator:
    def __init__(self):
        self.checks = [
            self._check_workflow_file,
            self._check_setup_script,
            self._check_main_script,
            self._check_git_lfs,
            self._check_configuration,
            self._check_dependencies
        ]
    
    async def validate_all(self) -> int:
        logger.processing("Validating DumprX workflow components")
        
        passed = 0
        failed = 0
        
        for check in self.checks:
            try:
                result = await check()
                if result:
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                logger.error(f"Check failed with exception: {e}")
                failed += 1
        
        total = passed + failed
        logger.info(f"Validation complete: {passed}/{total} checks passed")
        
        if failed == 0:
            logger.success("All validation checks passed!")
            self._show_usage_instructions()
            return 0
        else:
            logger.error(f"{failed} validation checks failed")
            return 1
    
    async def _check_workflow_file(self) -> bool:
        logger.info("Checking workflow file")
        
        workflow_file = Path(".github/workflows/firmware-dump.yml")
        if not workflow_file.exists():
            logger.error("Workflow file not found")
            return False
        
        logger.success("Workflow file exists")
        
        try:
            import yaml
            with open(workflow_file) as f:
                yaml.safe_load(f)
            logger.success("Workflow YAML syntax is valid")
            return True
        except Exception as e:
            logger.error(f"Workflow YAML syntax is invalid: {e}")
            return False
    
    async def _check_setup_script(self) -> bool:
        logger.info("Checking setup script")
        
        setup_script = Path("setup.sh")
        if not setup_script.exists() or not setup_script.is_file():
            logger.error("Setup script not found or not executable")
            return False
        
        logger.success("Setup script exists and is accessible")
        return True
    
    async def _check_main_script(self) -> bool:
        logger.info("Checking main script")
        
        main_script = Path("dumprx.py")
        if not main_script.exists():
            logger.error("Main script (dumprx.py) not found")
            return False
        
        logger.success("Main script exists")
        return True
    
    async def _check_git_lfs(self) -> bool:
        logger.info("Checking Git LFS")
        
        try:
            result = await run_command(["git-lfs", "--version"])
            if result.returncode == 0:
                logger.success("Git LFS is available")
                return True
            else:
                logger.error("Git LFS not working properly")
                return False
        except FileNotFoundError:
            logger.error("Git LFS not found")
            return False
    
    async def _check_configuration(self) -> bool:
        logger.info("Checking configuration")
        
        config_file = Path("config.yaml")
        if not config_file.exists():
            logger.error("Configuration file not found")
            return False
        
        try:
            config.load()
            logger.success("Configuration file is valid")
            return True
        except Exception as e:
            logger.error(f"Configuration file is invalid: {e}")
            return False
    
    async def _check_dependencies(self) -> bool:
        logger.info("Checking dependencies")
        
        required_commands = ["python3", "7zz", "aria2c"]
        missing = []
        
        for cmd in required_commands:
            try:
                result = await run_command([cmd, "--version"])
                if result.returncode != 0:
                    missing.append(cmd)
            except FileNotFoundError:
                missing.append(cmd)
        
        if missing:
            logger.warning(f"Missing optional dependencies: {', '.join(missing)}")
            logger.info("Run setup.sh to install missing dependencies")
        else:
            logger.success("All dependencies are available")
        
        return True
    
    def _show_usage_instructions(self) -> None:
        logger.info("")
        logger.info("Your DumprX repository is ready!")
        logger.info("")
        logger.info("To use the workflow:")
        logger.info("1. Go to the Actions tab in your GitHub repository")
        logger.info("2. Select 'Firmware Dump Workflow'")
        logger.info("3. Click 'Run workflow'")
        logger.info("4. Fill in the required parameters")
        logger.info("")
        logger.info("To use locally:")
        logger.info("python3 dumprx.py <firmware_file_or_url>")