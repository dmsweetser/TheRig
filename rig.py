import os
import datetime
import json
import logging
import subprocess
from urllib.request import Request, urlopen
from lib.config_manager import *
import time


def log_message(message):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logging.info(f"{timestamp} - {message}")

def run_rig(script_path, log_filename, program_filename, requirements_key, requirements_filename):
        
    # Define variables
    client_url = get_config("core_url")

    # Get default prompt from config or use a default value
    default_prompt = get_config('default_prompt', "")
    revision_prompt = get_config('revision_prompt', "") 
    requirements_prompt = get_config(requirements_key, "")

    # Get the wrap up cutoff from config
    wrap_up_cutoff = get_config('wrap_up_cutoff','')

    logging.basicConfig(filename=log_filename, level=logging.INFO)

    with open(f"{script_path}prompt.txt", 'r') as prompt:
        initial_prompt = prompt.read()

    os.chdir(script_path)
    script_path = "./"
    
    # This runs in a continuous loop until you kill it
    while True:
        try:
            
            git_path = script_path
            batch_file = f"{script_path}source.sh"
            script_file = f"{script_path}{program_filename}"
            requirements_file = f"{script_path}{requirements_filename}"
            
            prompt_file = f"{script_path}prompt.txt"
            with open(prompt_file, 'r') as prompt:
                initial_prompt = prompt.read()
            
            if not is_git_repo_initialized(git_path):
                log_message("Repository not initialized. Initializing...")
                git_init(git_path)
                log_message("Repository initialized.")
            else:
                log_message("Repository already initialized.")
            
            with open(script_file, 'r') as file:
                
                original_code = file.read()        
                # Run bash script and capture output
                # Run again to get latest error for the requirements file generation
                process = subprocess.Popen(["bash", batch_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                # Wait for 20 seconds
                time.sleep(10)
                stdout, stderr = process.communicate()
                run_error = stderr.decode()[:3000]
                # Terminate the process
                process.terminate()
                log_message(run_error)  
                    
                if len(original_code) > wrap_up_cutoff or run_error != "":
                    prompt = revision_prompt
                else:
                    prompt = default_prompt
                    
                if run_error != "":
                    message = f"<s><INST>Here is the original instruction:\n{initial_prompt}\nHere is the current code:\n```\n{original_code}\n```\nHere is the latest execution error when I try to run the code:\n{run_error}\n\n{prompt}\n\n</INST>\n"
                elif run_error == "":
                    message = f"<s><INST>Here is the original instruction:\n{initial_prompt}\nHere is the current code:\n```\n{original_code}\n```\n\n{prompt}\n\n</INST>\n"
                        
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

                # Run again to get latest error for the requirements file generation
                process = subprocess.Popen(["bash", batch_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                # Wait for 20 seconds
                time.sleep(10)
                stdout, stderr = process.communicate()
                run_error = stderr.decode()[:3000]
                # Terminate the process
                process.terminate()

                if run_error != "":
                    message = f"<s><INST>Here is my current code:\n```\n{revised_code}\n```Here is the latest execution error when I try to run the code:\n{run_error}\n\n{requirements_prompt}\n\n</INST>\n"
                else:
                    message = f"<s><INST>Here is my current code:\n```\n{revised_code}\n```\n\n{requirements_prompt}\n\n</INST>\n"
                data = {
                    'prompt': message,
                    'fileContents': ''
                }        
                req = Request(client_url, json.dumps(data).encode(), method="POST")
                req.add_header('Content-Type', 'application/json')
                try:
                    response = urlopen(req)
                    response_content = response.read()
                    new_requirements = response_content.decode()        
                    
                    if new_requirements != "":
                        os.remove(requirements_file)
                        
                        with open(requirements_file, 'w') as new_file:
                            new_file.write(new_requirements)
                            
                        git_commit(git_path, f"{requirements_filename} updated by The Rig")
                        log_message(f"Commit made for {requirements_filename}")
                    else:
                        log_message(f"No commit made for {requirements_filename} - response was empty")
                    
                except Exception as e:
                    log_message(f"Error: {e}")

        except Exception as e:
            log_message(f"Error: {e}")        
            time.sleep(360)

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
    subprocess.check_call(["git", "add", "--all"], cwd=path)
    subprocess.check_call(["git", "commit", "-m", message, path])