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

# Get default prompt from config or use a default value
default_prompt = get_config('default_prompt', "")
revision_prompt = get_config('revision_prompt', "") 

# Get the wrap up cutoff from config
wrap_up_cutoff = get_config('wrap_up_cutoff','')

logging.basicConfig(filename='rig_python39_linux.log', level=logging.INFO)

with open("base_templates/python39_linux/prompt.txt", 'r') as prompt:
    initial_prompt = prompt.read()

def log_message(message):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logging.info(f"{timestamp} - {message}")

def run_script(script_path):
    
    os.chdir(script_path)
    script_path = "./"
    
    git_path = script_path
    batch_file = f"{script_path}source.sh"
    script_file = f"{script_path}source.py"
    requirements_file = f"{script_path}requirements.txt"
    
    prompt_file = f"{script_path}prompt.txt"
    with open(prompt_file, 'r') as prompt:
        initial_prompt = prompt.read()
    
    if not is_git_repo_initialized(git_path):
        log_message("Repository not initialized. Initializing...")
        git_init(git_path)
        log_message("Repository initialized.")
    else:
        log_message("Repository already initialized.")
    
    execution_date = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    
    build_output = ""
    
    with open(script_file, 'r') as file:
        
        original_code = file.read()        
        # Run bash script and capture output
        process = subprocess.Popen(["bash", batch_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        run_error = stderr.decode()
        log_message(run_error)  
               
        if "TODO" in original_code.upper() or "PLACEHOLDER" in original_code.upper() or len(original_code) > wrap_up_cutoff:
            prompt = revision_prompt
        else:
            prompt = default_prompt
            
        if run_error != "":
            message = f"<s>[INST]Here is the original instruction:\n{initial_prompt}\nHere is the current code:\n```\n{original_code}\n```\nHere is the latest error when I try to run the code:\n{run_error}\n\n{prompt}\n\n[/INST]\n"
        elif run_error == "":
            message = f"<s>[INST]Here is the original instruction:\n{initial_prompt}\nHere is the current code:\n```\n{original_code}\n```\n\n{prompt}\n\n[/INST]\n"
                
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
            
            os.remove(script_file)
            
            with open(script_file, 'w') as new_file:
                new_file.write(revised_code)
                
            git_commit(git_path, "Revision done by The Rig")
            log_message("Commit made for code revision")
            
        except Exception as e:
            log_message(f"Error: {e}")
            

    with open(requirements_file, 'r') as file:        
        requirements = file.read()        
        prompt = "Generate ONLY a full revision of this requirements.txt for my current code."
        message = f"<s>[INST]Here is the current code:\n```\n{original_code}\n```\nHere is the current contents of my requirements.txt:\n```\n{requirements}\n```\n\n{prompt}\n\n[/INST]\n"
        data = {
            'prompt': message,
            'fileContents': original_code
        }        
        req = Request(client_url, json.dumps(data).encode(), method="POST")
        req.add_header('Content-Type', 'application/json')
        try:
            response = urlopen(req)
            response_content = response.read()
            new_requirements = response_content.decode()        
            
            os.remove(requirements_file)
            
            with open(requirements_file, 'w') as new_file:
                new_file.write(new_requirements)
                
            git_commit(git_path, "Requirements.txt updated by The Rig")
            log_message("Commit made for requirements.txt")
            
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
    run_script("base_templates/python39_linux/")