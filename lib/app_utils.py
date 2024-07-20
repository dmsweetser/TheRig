import os
import sqlite3
import requests
import tempfile
from flask import abort
import psutil
import difflib
from markupsafe import escape

from llama_cpp import Llama

from lib.config_manager import *
from lib.custom_logger import *

import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = CustomLogger(get_config("log_folder",False))

def find_process_by_port(port):
    port = int(port)
    for conn in psutil.net_connections():
        if conn.laddr.port == port and conn.status == 'LISTEN':
            process = psutil.Process(conn.pid)
            return process.name(), process.pid
    return None, None

def load_model(model_url, model_folder, model_filename, max_context, logger, is_creative):

    model_path = model_folder + model_filename

    if not os.path.isfile(model_path):
        try:
            response = requests.get(model_url)
            with open(model_path, 'wb') as model_file:
                model_file.write(response.content)
        except Exception as e:
            logger.log("Failed to download or save the model:", str(e))
            return None

    # Define default llama.cpp parameters
    llama_params = {
        "n_threads": "0",
        "n_threads_batch": "0",
        "use_mmap": False,
        "use_mlock": False,
        "n_gpu_layers": "0",
        "main_gpu": "0",
        "tensor_split": "",
        "main_gpu": "0",
        "top_p": "0.99",
        "n_ctx": "32768",
        "rope_freq_base": "0",
        "numa": False,
        "verbose": True,
        "top_k": "85",
        "use_mlock": False,
        "temperature": "1",
        "repeat_penalty": "1.01",
        "max_tokens": "16384",
        "typical_p": "0.68",
        "n_batch": "2048",
        "model": "model_path"
    }

    try:
        return Llama(**llama_params)
    except Exception as e:
        logger.log("Failed to create Llama object:", str(e))
        return None