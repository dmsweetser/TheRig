import os
import re
import datetime
import docker
import json
import logging
import subprocess
from queue import Queue
import threading
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import requests
import time

# Load config
class Config:
    LOGGING_ENABLED = True
    LLM_API = "local"
    LLM_API_KEY = "your_llm_api_key"
    DOCKER_HOST = "localhost"
    DOCKER_IMAGE_PYTHON = "python:latest"
    DOCKER_IMAGE_DOTNET = "mcr.microsoft.com/dotnet/core/sdk:latest"
    DOCKER_IMAGE_JAVA = "openjdk:latest"
    DOCKER_IMAGE_GOSU = "gosu/gosu:latest"
    ENABLED = True
    MODEL_FOLDER = "models"
    MODEL_URL = "model_url"
    MODEL_NAME = "Mistral-Nemo-Instruct-2407-Q8_0.gguf"
    MAX_CONTEXT = 131072
    REVISIONS_PER_PAGE = 10
    SESSION_TYPE = "filesystem"
    MAX_FILE_SIZE = 1024 * 1024 * 1024
    LOG_FOLDER = "logs"
    DEFAULT_PROMPT = "Generate ONLY a production-ready revision of this code surrounded by triple-backticks, without additional commentary, that resolves all execution errors, completely implements all existing features and adds 2 additional new features. The code you generate should be entirely self-contained, not relying on any external assets such as images or font files. Include code that verifies on start that every function in the code executes without error."
    REVISION_PROMPT = "Generate ONLY a production-ready revision of the code above surrounded by triple-backticks, without additional commentary, that resolves all execution errors, completely removes all comments, completely implements all features, and completely removes redundant code. The code you generate should be entirely self-contained, not relying on any external assets such as images or font files. Include code that verifies on start that every function in the code executes without error."
    REQUIREMENTS_PROMPT = "Generate ONLY a sample requirements.txt surrounded by triple-backticks that would work for this code without version numbers or additional comments."
    ERROR_PROMPT = "Here is the latest execution error when I try to run the code:"
    WRAP_UP_CUTOFF = 70000

config = Config()

# Set up logging
if config.LOGGING_ENABLED:
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
else:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def extract_code_blocks(markdown_text, return_first_only):
    code_blocks = []
    lines = markdown_text.split('\\n')
    in_code_block = False
    code_block = []

    for line in lines:
        if line.startswith('```') and in_code_block == False:
            in_code_block = True
        elif line.startswith('```') and in_code_block == True:
            if code_block:
                code_blocks.append('\\n'.join(code_block))
            in_code_block = False
            code_block = []
        elif in_code_block:
            code_block.append(line)

    if return_first_only and len(code_blocks) > 0:
        return code_blocks[0]

    return '\\n\\n'.join(code_blocks)

def run_llm(original_code, llama_model, prompt, language):
    start_time = time.time() # Get the start time

    try:
        if config.LLM_API == 'local':
            # Instantiate LLM for each iteration
            llama_params = {
                "n_threads": 0,
                "n_threads_batch": 0,
                "use_mmap": False,
                "use_mlock": False,
                "n_gpu_layers": 0,
                "main_gpu": 0,
                "tensor_split": "",
                "top_p": 0.95,
                "n_ctx": config.MAX_CONTEXT,
                "rope_freq_base": 0,
                "numa": False,
                "verbose": True,
                "top_k": 40,
                "temperature": 0.8,
                "repeat_penalty": 1.01,
                "max_tokens": 65536,
                "typical_p": 0.68,
                "n_batch": 2048,
                "min_p": 0,
                "frequency_penalty": 0,
                "presence_penalty": 0.5
            }
            # Assuming you have a Llama class
            llama = Llama(f"{config.MODEL_FOLDER}/{config.MODEL_NAME}", **llama_params)

            # Generate complete revision of code, addressing build errors, surrounded by triple backticks
            response = llama.create_completion( f"{prompt}")
            revised_code = response['choices'][0]['text']
        else:
            # Use OpenAI-compatible API
            response = requests.post(
                f"{config.LLM_API}/completions",
                headers={"Authorization": f"Bearer {config.LLM_API_KEY}"},
                json={
                    "prompt": f"{prompt}",
                    "max_tokens": 65536,
                    "temperature": 0.8,
                    "top_p": 0.95,
                    "n": 1,
                    "stream": False,
                    "logprobs": None,
                    "echo": False,
                    "stop": None,
                    "timeout": None
                }
            )
            revised_code = response.json()['choices'][0]['text']
    except Exception as e:
        # Handle LLM call failure, return input code without throwing errors
        logging.error(f"LLM call failed: {e}")
        return original_code

    # Get the current ticks as a string
    now = datetime.datetime.now()
    current_ticks = now.strftime("%Y%m%d_%H%M%S")

    file_name = "raw_response_"

    with open(f"{config.LOG_FOLDER}{file_name}{current_ticks}.json", "w") as outfile:
        json.dump(revised_code, outfile, indent=4)

    # Check if extracting from Markdown is enabled in config
    extract_from_markdown = get_config('extract_from_markdown',False)

    return_first_only = False
    if config.REQUIREMENTS_PROMPT in prompt:
        return_first_only = True
    if config.NUGET_PROMPT in prompt:
        return_first_only = True

    if extract_from_markdown:
        revised_code = extract_code_blocks(revised_code, return_first_only)

    end_time = time.time() # Get the end time
    duration = end_time - start_time # Calculate the duration

    logging.info(f"Total duration in seconds: {duration}")

    logging.info(f"Original code length (not tokens): {len(original_code)}")
    logging.info(f"New code length (not tokens): {len(revised_code)}")

    if len(revised_code) < 0.8 * len(original_code) and len(original_code) > 10000:
        logging.info(f"Generated code was too short")
        return original_code
    elif len(revised_code) == 0:
        logging.info(f"Generated code was blank")
        return original_code
    elif len(revised_code) > 1.7 * len(original_code) and len(original_code) > 10000:
        logging.info(f"Generated code was too long")
        return original_code
    else:
        return revised_code

# Docker execution function
def execute_code(code, language):
    client = docker.DockerClient(base_url=f"{config.DOCKER_HOST}:2375")
    if language == "py":
        # Create requirements.txt
        requirements = []
        for line in code.splitlines():
            if "import" in line:
                module = line.split("import")[1].strip()
                requirements.append(module)
        with open("requirements.txt", "w") as f:
            for requirement in requirements:
                f.write(f"{requirement}\\n")

        # Run Docker container
        container = client.containers.run(
            config.DOCKER_IMAGE_PYTHON,
            command=f"bash -c 'pip install -r requirements.txt && python main.py'",
            detach=True,
            remove=True,
            stdout=True,
            stderr=True,
            volumes={
                "/app": {
                    "bind": "/app",
                    "mode": "rw"
                }
            }
        )
        build_output = container.logs(stdout=True, stderr=True).decode("utf-8")
        return build_output
    elif language == "cs":
        container = client.containers.run(
            config.DOCKER_IMAGE_DOTNET,
            command=f"bash -c 'dotnet run'",
            detach=True,
            remove=True,
            stdout=True,
            stderr=True
        )
        build_output = container.logs(stdout=True, stderr=True).decode("utf-8")
        return build_output
    elif language == "java":
        container = client.containers.run(
            config.DOCKER_IMAGE_JAVA,
            command=f"bash -c 'javac Main.java && java Main'",
            detach=True,
            remove=True,
            stdout=True,
            stderr=True,
            volumes={
                "/app": {
                    "bind": "/app",
                    "mode": "rw"
                }
            }
        )
        build_output = container.logs(stdout=True, stderr=True).decode("utf-8")
        return build_output
    elif language == "gosu":
        container = client.containers.run(
            config.DOCKER_IMAGE_GOSU,
            command=f"bash -c 'gosu Main.gosu'",
            detach=True,
            remove=True,
            stdout=True,
            stderr=True,
            volumes={
                "/app": {
                    "bind": "/app",
                    "mode": "rw"
                }
            }
        )
        build_output = container.logs(stdout=True, stderr=True).decode("utf-8")
        return build_output

# Function to sanitize app name
def sanitize_app_name(app_name):
    return re.sub(r'[^a-zA-Z0-9_\-]', '', app_name)

# Function to process app request
def process_app_request(app_name, prompt, language, input_code, logger):
    # Run LLM
    output_code = run_llm(input_code, None, prompt, language)

    # Execute code in Docker
    build_output = execute_code(output_code, language)

    # Store iteration in app_results folder
    app_results_folder = f"app_results/{sanitize_app_name(app_name)}/{datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}"
    if not os.path.exists(app_results_folder):
        os.makedirs(app_results_folder)

    with open(f"{app_results_folder}/output_code.txt", "w") as f:
        f.write(output_code)

    with open(f"{app_results_folder}/build_output.txt", "w") as f:
        f.write(build_output)

    if build_output.strip() == "":
        with open(f"{app_results_folder}/release_candidate.txt", "w") as f:
            f.write("Release candidate")

    return build_output

# Function to read app requests from app_requests folder
def read_app_requests():
    app_requests = []
    for filename in os.listdir("app_requests"):
        if filename.endswith(".txt"):
            with open(f"app_requests/{filename}", "r") as f:
                prompt = f.read()
                app_name = filename.split(".")[0]
                language = "py" if "python" in prompt.lower() else "cs" if "c#" in prompt.lower() else "java" if "java" in prompt.lower() else "gosu" if "gosu" in prompt.lower() else "py"
                input_code = ""
                app_requests.append((app_name, prompt, language, input_code))
    return app_requests

# Main function
def main():
    if not os.path.exists(config.LOG_FOLDER):
        os.makedirs(config.LOG_FOLDER)

    logging.basicConfig(filename=f"{config.LOG_FOLDER}/app.log", level=logging.INFO)

    app_requests = read_app_requests()
    while True:
        for app_name, prompt, language, input_code in app_requests:
            build_output = process_app_request(app_name, prompt, language, input_code, logging)
            logging.info(f"Processed {app_name} with build output: {build_output}")

            # Get default prompt from config or use a default value
            default_prompt = config.DEFAULT_PROMPT
            revision_prompt = config.REVISION_PROMPT 
            requirements_prompt = config.REQUIREMENTS_PROMPT

            # Get the wrap up cutoff from config
            wrap_up_cutoff = config.WRAP_UP_CUTOFF

            if len(input_code) > wrap_up_cutoff or build_output != "":
                prompt = revision_prompt
            else:
                prompt = default_prompt

            if input_code != "":
                message = f"<INST>Here is the original instruction:\\n{prompt}\\nHere is the current code:\\n
```\\n{input_code}\\n```\\n</INST> </s>\\n"
            else:
                message = f"<INST>{prompt}\\n</INST> </s>\\n"

            # Get response from LLM
            output_code = run_llm(input_code, None, message, language)

            # Execute code in Docker
            build_output = execute_code(output_code, language)

            # Store iteration in app_results folder
            app_results_folder = f"app_results/{sanitize_app_name(app_name)}/{datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}"
            if not os.path.exists(app_results_folder):
                os.makedirs(app_results_folder)

            with open(f"{app_results_folder}/output_code.txt", "w") as f:
                f.write(output_code)

            with open(f"{app_results_folder}/build_output.txt", "w") as f:
                f.write(build_output)

            if build_output.strip() == "":
                with open(f"{app_results_folder}/release_candidate.txt", "w") as f:
                    f.write("Release candidate")

            # Run again to get latest error for the requirements file generation
            build_output = execute_code(output_code, language)

            if build_output != "":
                message = f"<INST>Here is my current code:\\n```\\n{output_code}\\n```Here is the latest execution error when I try to run the code:\\n{build_output}\\n\\n{requirements_prompt}\\n\\n</INST> </s>\\n"
            else:
                message = f"<INST>Here is my current code:\\n```\\n{output_code}\\n```\\n\\n{requirements_prompt}\\n\\n</INST> </s>\\n"

            # Get response from LLM
            new_requirements = run_llm("", None, message, language)

            if new_requirements != "":
                with open(f"{app_results_folder}/requirements.txt", "w") as f:
                    f.write(new_requirements)

if __name__ == "__main__":
    main()
