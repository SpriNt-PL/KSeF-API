import os
import sys
import subprocess
import json

import constants

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

def prepare_statistics():
    with open(constants.DATA_FILE_PATH, 'r') as file:
        supervision_scopes = json.load(file)

    entities_count = 0

    for scope in supervision_scopes:

        for entity in scope['entity']:
            entities_count += 1

    return entities_count

def show_report(failure_list, entities_count, entities_processed):
    print("\nFINAL REPORT")
    print(f"Total number of entities processed {entities_processed}/{entities_count}")
    
    if len(failure_list) > 0:
        print("List of entities that were not fully processed:")

        for entity in failure_list:
            print(entity)

    else:
        print("All entities were processed")

