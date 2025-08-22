import subprocess
import asyncio
from typing import List, Optional, Dict, Any
from pathlib import Path

async def run_command(
    cmd: List[str], 
    cwd: Optional[Path] = None,
    capture_output: bool = True,
    timeout: Optional[int] = None
) -> subprocess.CompletedProcess:
    process = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=cwd,
        stdout=asyncio.subprocess.PIPE if capture_output else None,
        stderr=asyncio.subprocess.PIPE if capture_output else None
    )
    
    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
        return subprocess.CompletedProcess(
            args=cmd,
            returncode=process.returncode,
            stdout=stdout,
            stderr=stderr
        )
    except asyncio.TimeoutError:
        process.kill()
        await process.wait()
        raise

def run_sync_command(
    cmd: List[str],
    cwd: Optional[Path] = None,
    capture_output: bool = True,
    timeout: Optional[int] = None
) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=capture_output,
        text=True,
        timeout=timeout
    )