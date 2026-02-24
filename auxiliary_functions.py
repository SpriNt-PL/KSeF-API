import os
import sys
import subprocess

def get_base_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))
    

def prepare_playwright():
    browsers_path = os.path.join(os.path.expanduser("~"), "AppData", "Local", "ms-playwright")
    os.environ['PLAYWRIGHT_BROWSERS_PATH'] = browsers_path

    if not os.path.exists(browsers_path) or not os.listdir(browsers_path):
        print("Downloading browser engine. It may take a while...")
        try:
            subprocess.run([sys.executable, "install-browsers"], check=True)
            print("Browser engine installed successfully")
        except Exception as e:
            print(f"Installation error: {e}")
            sys.exit(1)
    else:
        print("Browser engine found. Starting the program.")