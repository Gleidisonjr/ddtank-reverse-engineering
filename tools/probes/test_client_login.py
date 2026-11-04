#!/usr/bin/env python3
"""
District 187 - Test Client Launch, Screenshot & Automated Login Verification
"""
import ctypes
import os
import subprocess
import sys
import time
import win32con
import win32gui
from PIL import ImageGrab

user32 = ctypes.windll.user32

def send_key(vk):
    user32.keybd_event(vk, 0, 0, 0)
    time.sleep(0.05)
    user32.keybd_event(vk, 0, win32con.KEYEVENTF_KEYUP, 0)
    time.sleep(0.05)

def type_string(s):
    for char in s:
        vk = user32.VkKeyScanW(ord(char)) & 0xFF
        send_key(vk)

def main():
    client_dir = r"C:\Users\dopamine\Desktop\Projetos\Reverse Engineering\targets\district-187\client\S2"
    exe_path = os.path.join(client_dir, "TheRaw.exe")
    
    env = os.environ.copy()
    env["__COMPAT_LAYER"] = "RunAsInvoker"
    
    cmd = [exe_path, "-arch", "game", "-windowtitle", "D187"]
    print(f"[*] Launching {exe_path}...")
    proc = subprocess.Popen(cmd, cwd=client_dir, env=env)
    print(f"[+] Started PID {proc.pid}. Waiting for game window...")
    
    hwnd = 0
    for _ in range(20):
        time.sleep(1)
        hwnd = win32gui.FindWindow(None, "D187")
        if hwnd and win32gui.IsWindowVisible(hwnd):
            print(f"[+] Found D187 window (HWND: {hex(hwnd)})")
            break
            
    if not hwnd:
        print("[-] Could not find D187 window.")
        proc.terminate()
        return

    # Wait a bit for Scaleform UI to load
    print("[*] Waiting 6 seconds for Scaleform Flash UI to initialize...")
    time.sleep(6)
    
    # Bring to foreground
    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    win32gui.SetForegroundWindow(hwnd)
    time.sleep(1)
    
    # Capture initial screenshot
    rect = win32gui.GetWindowRect(hwnd)
    print(f"[*] Window rect: {rect}")
    os.makedirs(r"targets\district-187\traffic", exist_ok=True)
    
    screenshot_1 = ImageGrab.grab(bbox=rect)
    screenshot_path1 = r"targets\district-187\traffic\screen_1_login.png"
    screenshot_1.save(screenshot_path1)
    print(f"[+] Saved initial screenshot to: {screenshot_path1}")
    
    # Click in the middle of window or press TAB to focus login field
    # In 1024x768, login box is roughly at center or we click near input fields
    cx = (rect[0] + rect[2]) // 2
    cy = (rect[1] + rect[3]) // 2
    
    print(f"[*] Focusing and entering credentials (admin / admin)...")
    # Click on the username area (center-ish, slightly up)
    user32.SetCursorPos(cx, cy - 20)
    user32.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.05)
    user32.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    time.sleep(0.5)
    
    # Select all and type admin
    send_key(win32con.VK_TAB)
    type_string("admin")
    time.sleep(0.3)
    
    # Tab to password
    send_key(win32con.VK_TAB)
    time.sleep(0.3)
    type_string("admin123")
    time.sleep(0.3)
    
    # Press Enter to submit
    print("[*] Submitting login form (Enter)...")
    send_key(win32con.VK_RETURN)
    
    # Wait for handshake
    print("[*] Waiting 4 seconds for network response and transition...")
    time.sleep(4)
    
    screenshot_2 = ImageGrab.grab(bbox=rect)
    screenshot_path2 = r"targets\district-187\traffic\screen_2_after_login.png"
    screenshot_2.save(screenshot_path2)
    print(f"[+] Saved post-login screenshot to: {screenshot_path2}")
    
    print("[*] Leaving game running for user inspection or checking PID...")

if __name__ == "__main__":
    main()
