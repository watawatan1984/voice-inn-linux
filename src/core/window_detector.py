"""
Active Window Detection Module

Detects the currently active (foreground) window across different operating systems.
Used to provide context-aware prompt optimization for voice transcription.
"""

import platform
import subprocess
import logging
from typing import TypedDict


class WindowInfo(TypedDict):
    title: str
    process: str
    app_name: str


def get_active_window() -> WindowInfo:
    """
    Get information about the currently active window.
    
    Returns:
        WindowInfo dict with keys:
            - title: Full window title
            - process: Process name (Windows only)
            - app_name: Application name
    
    On error, returns empty strings for all fields (fallback to STD mode).
    """
    system = platform.system()
    result: WindowInfo = {"title": "", "process": "", "app_name": ""}
    
    try:
        if system == "Windows":
            result = _get_active_window_windows()
        elif system == "Darwin":
            result = _get_active_window_macos()
        elif system == "Linux":
            result = _get_active_window_linux()
        else:
            logging.warning(f"Unsupported OS for window detection: {system}")
    except Exception as e:
        logging.warning(f"Failed to get active window: {e}")
    
    return result


def _get_active_window_windows() -> WindowInfo:
    """Get active window on Windows using Win32 API."""
    import ctypes
    from ctypes import wintypes
    
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    psapi = ctypes.windll.psapi
    
    # Get foreground window handle
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return {"title": "", "process": "", "app_name": ""}
    
    # Get window title
    length = user32.GetWindowTextLengthW(hwnd)
    buf = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buf, length + 1)
    title = buf.value
    
    # Get process name
    process_name = ""
    try:
        # Get process ID
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        
        # Open process
        PROCESS_QUERY_INFORMATION = 0x0400
        PROCESS_VM_READ = 0x0010
        h_process = kernel32.OpenProcess(
            PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, 
            False, 
            pid.value
        )
        
        if h_process:
            try:
                # Get process name
                exe_buf = ctypes.create_unicode_buffer(260)
                psapi.GetModuleBaseNameW(h_process, None, exe_buf, 260)
                process_name = exe_buf.value
            finally:
                kernel32.CloseHandle(h_process)
    except Exception as e:
        logging.debug(f"Failed to get process name: {e}")
    
    # Extract app name from title or process
    app_name = _extract_app_name(title, process_name)
    
    return {"title": title, "process": process_name, "app_name": app_name}


def _get_active_window_macos() -> WindowInfo:
    """Get active window on macOS using AppleScript."""
    # Get frontmost application name
    script_app = '''
    tell application "System Events"
        set frontApp to name of first application process whose frontmost is true
    end tell
    return frontApp
    '''
    
    # Get window title
    script_title = '''
    tell application "System Events"
        set frontApp to first application process whose frontmost is true
        tell frontApp
            if (count of windows) > 0 then
                return name of front window
            else
                return ""
            end if
        end tell
    end tell
    '''
    
    app_name = ""
    title = ""
    
    try:
        result = subprocess.run(
            ["osascript", "-e", script_app],
            capture_output=True,
            text=True,
            timeout=1
        )
        if result.returncode == 0:
            app_name = result.stdout.strip()
    except Exception as e:
        logging.debug(f"Failed to get macOS app name: {e}")
    
    try:
        result = subprocess.run(
            ["osascript", "-e", script_title],
            capture_output=True,
            text=True,
            timeout=1
        )
        if result.returncode == 0:
            title = result.stdout.strip()
    except Exception as e:
        logging.debug(f"Failed to get macOS window title: {e}")
    
    # Use app name as title if title is empty
    if not title:
        title = app_name
    
    return {"title": title, "process": "", "app_name": app_name}


def _get_active_window_linux() -> WindowInfo:
    """Get active window on Linux using xdotool."""
    title = ""
    
    try:
        # Get active window ID
        result = subprocess.run(
            ["xdotool", "getactivewindow"],
            capture_output=True,
            text=True,
            timeout=1
        )
        if result.returncode != 0:
            return {"title": "", "process": "", "app_name": ""}
        
        window_id = result.stdout.strip()
        
        # Get window name
        result = subprocess.run(
            ["xdotool", "getwindowname", window_id],
            capture_output=True,
            text=True,
            timeout=1
        )
        if result.returncode == 0:
            title = result.stdout.strip()
    except FileNotFoundError:
        logging.warning("xdotool not found. Install with: sudo apt install xdotool")
    except Exception as e:
        logging.debug(f"Failed to get Linux window: {e}")
    
    app_name = _extract_app_name(title, "")
    
    return {"title": title, "process": "", "app_name": app_name}


def _extract_app_name(title: str, process: str) -> str:
    """Extract a clean application name from title or process name."""
    # If process name is available, use it (without extension)
    if process:
        name = process.rsplit(".", 1)[0]  # Remove .exe etc.
        return name
    
    # Try to extract from title (common patterns)
    if not title:
        return ""
    
    # Many apps use " - " as separator (e.g., "main.py - Visual Studio Code")
    if " - " in title:
        parts = title.split(" - ")
        # Usually the app name is at the end
        return parts[-1].strip()
    
    # Some apps use " | " (e.g., "Inbox | Gmail")
    if " | " in title:
        parts = title.split(" | ")
        return parts[-1].strip()
    
    return title
