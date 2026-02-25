import os
import sys
import subprocess
import json
from datetime import datetime, timedelta, timezone

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


def save_report_to_file(failure_list, entities_count, entities_processed, elapsed_time):
    
    now = datetime.now()

    with open("raport.txt", "a") as f:
        line = f"Raport z dnia {now}"
        f.write(line)
    
        line = f"\nWspolnoty dla ktorych faktury zostaly pobrane {entities_processed}/{entities_count}"
        f.write(line)

        if len(failure_list) > 0:
            print("\nLista wspolnot, których faktury nie zostały pobrane:")
        
            for entity in failure_list:
                line = f"\n{entity}"
                f.write(line)

        else:
            line = "\nSukces! Faktury dla wszystkich wspolnot zostaly pobrane"

        line = f"\nCalkowity czas pracy: {elapsed_time:.2f} sekund\n\n"
        f.write(line)

    print("Report has been prepared.")