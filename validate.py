#!/usr/bin/env python3

import sys
import asyncio
from lib.core.validator import WorkflowValidator

async def main():
    validator = WorkflowValidator()
    return await validator.validate_all()

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("Validation cancelled by user")
        sys.exit(130)