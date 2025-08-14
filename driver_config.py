import os
import platform
import threading
import time


def detect_os_arch():
    system = platform.system().lower()
    machine = platform.machine().lower()

    if 'windows' in system:
        return 'win64' if '64' in machine else 'win32'
    elif 'darwin' in system:
        return 'mac-arm64' if 'arm' in machine or 'aarch64' in machine else 'mac-x64'
    elif 'linux' in system:
        return 'linux64'
    else:
        return None


def build_chromedriver_path(os_arch, headless=False):
    filename = 'chromedriver.exe' if 'win' in os_arch else 'chromedriver'
    driver_name = f'chromedriver-{os_arch}'
    if headless:
        filename = "chrome-headless-shell.exe" if 'win' in os_arch else 'chrome-headless-shell'
        driver_name = f'chrome-headless-shell-{os_arch}'

    return os.path.join('chromedrivers', driver_name, filename)


def ask_headless(timeout=10):
    """
    Prompt the user whether to run in headless mode, with a timeout.
    Defaults to True (headless).
    """
    result = {"headless": True}

    def get_input():
        val = input("Would you like to run in headless mode? (y/N, default y): ").strip().lower()
        result["headless"] = val in ["y", '']

    thread = threading.Thread(target=get_input)
    thread.daemon = True
    thread.start()
    thread.join(timeout)
    return result["headless"]


def ask_disable_js(timeout=10):
    """
    Prompt user to disable JavaScript, with timeout; defaults to True.
    """
    result = {"disable_js": True}

    def get_input():
        val = input("Disable JavaScript? (y/N, default y): ").strip().lower()
        result["disable_js"] = val in ['y', '']

    thread = threading.Thread(target=get_input, daemon=True)
    thread.start()
    thread.join(timeout)
    return result["disable_js"]


os_arch = detect_os_arch()
print(f"OS: {os_arch}")
time.sleep(2)
headless = ask_headless()
chromedriver_path = build_chromedriver_path(os_arch, headless) if os_arch else None
time.sleep(1.5)
print(f"Chrome Driver: {chromedriver_path}")
time.sleep(2)

if not os.path.isfile(chromedriver_path):
    raise FileNotFoundError(f"ChromeDriver not found at: {chromedriver_path}")
