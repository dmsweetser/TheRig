import os
import sys
import time
import datetime
import json
import re
import logging
import subprocess
from urllib.request import Request, urlopen
from urllib.error import URLError
from lib.config_manager import *

# Define variables
client_url = get_config("core_url")
logging.basicConfig(filename='finalizer.log', level=logging.INFO)

def log_message(message):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logging.info(f"{timestamp} - {message}")

def run_python_script(git_path, venv_path, python_script_path):
    
    if not is_git_repo_initialized(git_path):
        log_message("Repository not initialized. Initializing...")
        git_init(git_path)
        log_message("Repository initialized.")
    else:
        log_message("Repository already initialized.")
    
    execution_date = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Activate virtual environment
    os.chdir(venv_path)
    os.system("activate")
    
    build_output = ""

    # Run python script and pipe output to a datetime_stamped file
    script_args = [sys.executable, python_script_path]
    script_args += sys.argv[1:]
    
    do_revision = False
    
    with open(python_script_path, 'r') as file:
        original_code = file.read()
        process = subprocess.Popen(script_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        process.wait()
        build_output = process.stderr.read().decode()
        log_message(build_output)
        
        if len(build_output) > 0:
            do_revision = True
        else:
            do_revision = False
            log_message(f"No build errors detected and so no revision will be done")
            
    if do_revision == True:
        
        message = f"<s>[INST]Here is the current code:\nFile {python_script_path}\n```{original_code}\n```\nWhen I run the code, these are my current build errors:\n\n{build_output}\n\nGenerate ONLY a full revision of this code that fixes these build errors.\n[/INST]"
                
        # Get response from web request
        data = {
            'prompt': message,
            'fileContents': original_code
        }
        
        req = Request(client_url, json.dumps(data).encode(), method="POST")
        req.add_header('Content-Type', 'application/json')

        try:
            response = urlopen(req)
            response_content = response.read()
            revised_code = response_content.decode()        
            
            log_message(f"Revised code length: {len(revised_code)}")
            log_message(f"Original code length: {len(original_code)}")
                
            if '''if __name__ == "__main__":''' not in revised_code:
                revised_code = original_code
            
            os.remove(python_script_path)
            
            with open(python_script_path, 'w') as new_file:
                new_file.write(revised_code)
                
            git_commit(git_path, "Revision done by Code Reviser UI via finalizer.py")
            log_message("Commit made")
            
        except Exception as e:
            log_message(f"Error: {e}")

def is_git_repo_initialized(path):
    try:
        output = subprocess.check_output(["git", "rev-parse", "--is-initial-branch", path], stderr=subprocess.STDOUT, universal_newlines=True)
        if output:
            return False
        else:
            return True
    except subprocess.CalledProcessError:
        return False

def git_init(path):
    subprocess.check_call(["git", "init", path])
    
def git_commit(path, message):
    subprocess.check_call(["git", "add", "."], cwd=path)
    subprocess.check_call(["git", "commit", "-m", message, path])

# Run python script and do it again
while True:
    run_python_script(
        "C:\\Files\\source\\unversioned\\snake_game_infinite\\",
        "C:\\Files\\source\\unversioned\\snake_game_infinite\\venv\\scripts",
        "C:\\Files\\source\\unversioned\\snake_game_infinite\\game.py")