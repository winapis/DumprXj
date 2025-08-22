from rich.console import Console
from rich.text import Text
import time


console = Console()


def show_banner():
    banner_text = """
	██████╗░██╗░░░██╗███╗░░░███╗██████╗░██████╗░██╗░░██╗
	██╔══██╗██║░░░██║████╗░████║██╔══██╗██╔══██╗╚██╗██╔╝
	██║░░██║██║░░░██║██╔████╔██║██████╔╝██████╔╝░╚███╔╝░
	██║░░██║██║░░░██║██║╚██╔╝██║██╔═══╝░██╔══██╗░██╔██╗░
	██████╔╝╚██████╔╝██║░╚═╝░██║██║░░░░░██║░░██║██╔╝╚██╗
	╚═════╝░░╚═════╝░╚═╝░░░░░╚═╝╚═╝░░░░░╚═╝░░╚═╝╚═╝░░╚═╝
	"""
    console.print(banner_text, style="green")


def show_usage():
    console.print("\n  ✰ Usage: dumprx <Firmware File/Extracted Folder -OR- Supported Website Link>", style="bold green")
    console.print("\t -> Firmware File: The .zip/.rar/.7z/.tar/.bin/.ozip/.kdz etc. file", style="green")
    console.print()
    time.sleep(0.5)
    console.print(" >> Supported Websites:", style="bold blue")
    console.print("\t1. Directly Accessible Download Link From Any Website", style="cyan")
    console.print("\t2. Filehosters like - mega.nz | mediafire | gdrive | onedrive | androidfilehost", style="cyan")
    console.print("\t >> Must Wrap Website Link Inside Single-quotes ('')", style="yellow")
    time.sleep(0.2)
    console.print(" >> Supported File Formats For Direct Operation:", style="bold blue")
    console.print("\t *.zip | *.rar | *.7z | *.tar | *.tar.gz | *.tgz | *.tar.md5", style="cyan")
    console.print("\t *.ozip | *.ofp | *.ops | *.kdz | ruu_*exe", style="cyan")
    console.print("\t system.new.dat | system.new.dat.br | system.new.dat.xz", style="cyan")
    console.print("\t system.new.img | system.img | system-sign.img | UPDATE.APP", style="cyan")
    console.print("\t *.emmc.img | *.img.ext4 | system.bin | system-p | payload.bin", style="cyan")
    console.print("\t *.nb0 | .*chunk* | *.pac | *super*.img | *system*.sin", style="cyan")
    console.print()


def print_error(message: str):
    console.print(f"\n  ☠ Error: {message}", style="bold red on black")


def print_warning(message: str):
    console.print(f"⚠ Warning: {message}", style="bold yellow")


def print_info(message: str):
    console.print(message, style="cyan")


def print_success(message: str):
    console.print(f"✅ {message}", style="bold green")