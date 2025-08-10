import platform
chrome_driver = "./chromedrivers"
def detect_os():
    os_name = platform.system().lower()

    if 'windows' in os_name:
        return "Windows"
    elif 'linux' in os_name:
        return "Linux"
    elif 'darwin' in os_name:
        return "macOS"
    elif 'unix' in os_name or os.name == 'posix':
        return "Unix-like (POSIX)"
    else:
        return f"Unknown OS: {os_name}"


detected_os = detect_os()
print(f"Detected Operating System: {detected_os}")