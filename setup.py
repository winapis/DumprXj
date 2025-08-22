from setuptools import setup, find_packages

setup(
    name="dumprx",
    version="2.0.0",
    description="Advanced firmware extraction and analysis toolkit",
    packages=find_packages(),
    install_requires=[
        "PyYAML>=6.0",
        "requests>=2.31.0",
        "click>=8.1.0",
        "rich>=13.0.0",
        "colorama>=0.4.6",
        "tqdm>=4.66.0",
        "gitpython>=3.1.40",
        "python-telegram-bot>=20.7",
        "aiohttp>=3.9.0"
    ],
    entry_points={
        "console_scripts": [
            "dumprx=dumprx.cli:main",
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)