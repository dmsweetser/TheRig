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

logger = CustomLogger(get_config("log_folder",""))

def find_process_by_port(port):
    port = int(port)
    for conn in psutil.net_connections():
        if conn.laddr.port == port and conn.status == 'LISTEN':
            process = psutil.Process(conn.pid)
            return process.name(), process.pid
    return None, None

def load_model(model_url, model_folder, model_filename, max_context, logger):

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
    default_llama_params = {
        "n_threads": 0,
        "n_threads_batch": 0,
        "n_batch": 512,
        "use_mmap": False,
        "use_mlock": False,
        "n_gpu_layers": 36,
        "main_gpu": 0,
        "tensor_split": "",
        "n_ctx": max_context,
        "rope_freq_base": 0,
        "numa": False,
        "max_tokens": max_context,
        "verbose": True
    }

    # Update llama_params with values from config or use defaults
    llama_params = {key: get_config(key, default_value) for key, default_value in default_llama_params.items()}

    try:
        return Llama(model_path, **llama_params)
    except Exception as e:
        logger.log("Failed to create Llama object:", str(e))
        return None