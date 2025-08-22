import sys
from typing import Optional, List
import time
from colorama import Fore, Back, Style, init

init(autoreset=True)


class UI:
    EMOJIS = {
        'info': 'ℹ️',
        'success': '✅',
        'warning': '⚠️',
        'error': '❌',
        'processing': '🔄',
        'download': '📥',
        'extract': '📋',
        'upload': '📤',
        'firmware': '📱',
        'partition': '💾',
        'git': '🔗',
        'telegram': '📢'
    }

    COLORS = {
        'primary': Fore.CYAN,
        'success': Fore.GREEN, 
        'warning': Fore.YELLOW,
        'error': Fore.RED,
        'info': Fore.BLUE,
        'accent': Fore.MAGENTA,
        'dim': Fore.WHITE + Style.DIM
    }

    @staticmethod
    def banner() -> None:
        banner_text = f"""
{Fore.GREEN}{Style.BRIGHT}
██████╗░██╗░░░██╗███╗░░░███╗██████╗░██████╗░██╗░░██╗
██╔══██╗██║░░░██║████╗░████║██╔══██╗██╔══██╗╚██╗██╔╝
██║░░██║██║░░░██║██╔████╔██║██████╔╝██████╔╝░╚███╔╝░
██║░░██║██║░░░██║██║╚██╔╝██║██╔═══╝░██╔══██╗░██╔██╗░
██████╔╝╚██████╔╝██║░╚═╝░██║██║░░░░░██║░░██║██╔╝╚██╗
╚═════╝░░╚═════╝░╚═╝░░░░░╚═╝╚═╝░░░░░╚═╝░░╚═╝╚═╝░░╚═╝
{Style.RESET_ALL}
{Fore.CYAN}Advanced Firmware Extraction & Analysis Tool v2.0{Style.RESET_ALL}
{Fore.WHITE + Style.DIM}Modernized Python Edition{Style.RESET_ALL}
"""
        print(banner_text)

    @staticmethod
    def print_info(message: str) -> None:
        print(f"{UI.EMOJIS['info']} {UI.COLORS['info']}{message}{Style.RESET_ALL}")

    @staticmethod
    def print_success(message: str) -> None:
        print(f"{UI.EMOJIS['success']} {UI.COLORS['success']}{message}{Style.RESET_ALL}")

    @staticmethod
    def print_warning(message: str) -> None:
        print(f"{UI.EMOJIS['warning']} {UI.COLORS['warning']}{message}{Style.RESET_ALL}")

    @staticmethod
    def print_error(message: str) -> None:
        print(f"{UI.EMOJIS['error']} {UI.COLORS['error']}{message}{Style.RESET_ALL}")

    @staticmethod
    def print_processing(message: str) -> None:
        print(f"{UI.EMOJIS['processing']} {UI.COLORS['primary']}{message}{Style.RESET_ALL}")

    @staticmethod
    def print_step(step: int, total: int, message: str) -> None:
        print(f"{UI.EMOJIS['extract']} {UI.COLORS['primary']}Step {step}/{total}: {message}{Style.RESET_ALL}")

    @staticmethod
    def print_firmware_detected(firmware_type: str) -> None:
        print(f"{UI.EMOJIS['firmware']} {UI.COLORS['success']}Firmware detected (Type: {firmware_type}){Style.RESET_ALL}")

    @staticmethod
    def print_download_start(url: str) -> None:
        print(f"{UI.EMOJIS['download']} {UI.COLORS['primary']}Starting download from: {url}{Style.RESET_ALL}")

    @staticmethod
    def print_extraction_complete(file_count: int, output_dir: str) -> None:
        print(f"{UI.EMOJIS['success']} {UI.COLORS['success']}Extraction completed (Files: {file_count}){Style.RESET_ALL}")
        print(f"{UI.EMOJIS['info']} {UI.COLORS['info']}Output directory: {output_dir}{Style.RESET_ALL}")

    @staticmethod
    def section_header(title: str) -> None:
        print(f"\n{UI.COLORS['accent']}{'=' * 60}{Style.RESET_ALL}")
        print(f"{UI.COLORS['accent']}{title.center(60)}{Style.RESET_ALL}")
        print(f"{UI.COLORS['accent']}{'=' * 60}{Style.RESET_ALL}\n")

    @staticmethod
    def subsection_header(title: str) -> None:
        print(f"\n{UI.COLORS['primary']}{'-' * 40}{Style.RESET_ALL}")
        print(f"{UI.COLORS['primary']}{title}{Style.RESET_ALL}")
        print(f"{UI.COLORS['primary']}{'-' * 40}{Style.RESET_ALL}")


class ProgressBar:
    def __init__(self, total: int, description: str = "", width: int = 50):
        self.total = total
        self.current = 0
        self.description = description
        self.width = width
        self.start_time = time.time()

    def update(self, increment: int = 1) -> None:
        self.current = min(self.current + increment, self.total)
        self._display()

    def set_progress(self, current: int) -> None:
        self.current = min(current, self.total)
        self._display()

    def _display(self) -> None:
        if self.total == 0:
            return

        percent = self.current / self.total
        filled_width = int(self.width * percent)
        bar = '█' * filled_width + '░' * (self.width - filled_width)
        
        elapsed = time.time() - self.start_time
        if self.current > 0:
            eta = elapsed * (self.total - self.current) / self.current
            eta_str = f"ETA: {int(eta)}s"
        else:
            eta_str = "ETA: --"

        percent_str = f"{percent:.1%}"
        
        sys.stdout.write(f"\r{UI.COLORS['primary']}{self.description} {bar} {percent_str} {eta_str}{Style.RESET_ALL}")
        sys.stdout.flush()

        if self.current >= self.total:
            print()

    def finish(self) -> None:
        self.set_progress(self.total)


class Spinner:
    def __init__(self, message: str = "Processing..."):
        self.message = message
        self.spinning = False
        self.spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        self.current_char = 0

    def start(self) -> None:
        self.spinning = True
        self._spin()

    def stop(self) -> None:
        self.spinning = False
        sys.stdout.write('\r' + ' ' * (len(self.message) + 10) + '\r')
        sys.stdout.flush()

    def _spin(self) -> None:
        if not self.spinning:
            return
            
        char = self.spinner_chars[self.current_char]
        sys.stdout.write(f'\r{UI.COLORS["primary"]}{char} {self.message}{Style.RESET_ALL}')
        sys.stdout.flush()
        
        self.current_char = (self.current_char + 1) % len(self.spinner_chars)
        
        if self.spinning:
            import threading
            timer = threading.Timer(0.1, self._spin)
            timer.start()


def print_usage() -> None:
    usage_text = f"""
{UI.COLORS['primary']}Usage:{Style.RESET_ALL} dumprx [OPTIONS] <firmware_path_or_url>

{UI.COLORS['info']}Supported Sources:{Style.RESET_ALL}
  • Direct download URLs
  • Mega.nz links  
  • MediaFire links
  • Google Drive links
  • OneDrive links
  • AndroidFileHost links

{UI.COLORS['info']}Supported Formats:{Style.RESET_ALL}
  • Archive files: .zip, .rar, .7z, .tar, .tar.gz, .tgz
  • Firmware files: .kdz, .ozip, .ofp, .ops, .nb0, .pac
  • System images: system.img, system.new.dat, payload.bin
  • Super partitions: super.img, system_*.sin

{UI.COLORS['info']}Options:{Style.RESET_ALL}
  --config PATH     Use custom configuration file
  --verbose        Enable debug logging
  --help           Show this help message

{UI.COLORS['warning']}Note:{Style.RESET_ALL} URLs must be wrapped in quotes
"""
    print(usage_text)