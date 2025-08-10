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

def build_chromedriver_path(os_arch):
    filename = 'chromedriver.exe' if 'win' in os_arch else 'chromedriver'
    return os.path.join('chromedrivers', f'chromedriver-{os_arch}', filename)

def ask_headless(timeout=10):
    """
    Prompt the user whether to run in headless mode, with a timeout.
    Defaults to False (non-headless).
    """
    result = {"headless": False}

    def get_input():
        val = input("Would you like to run in headless mode? (y/N, default N): ")
        result["headless"] = val.strip().lower() == "y"

    thread = threading.Thread(target=get_input)
    thread.daemon = True
    thread.start()
    thread.join(timeout)
    return result["headless"]


os_arch = detect_os_arch()
print(f"OS: {os_arch}")
time.sleep(2)
chromedriver_path = build_chromedriver_path(os_arch) if os_arch else None
headless = ask_headless()
time.sleep(1.5)
print(f"Chrome Driver: {chromedriver_path}")
time.sleep(2)

if not os.path.isfile(chromedriver_path):
    raise FileNotFoundError(f"ChromeDriver not found at: {chromedriver_path}")
