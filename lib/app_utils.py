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
        "n_threads": get_key_from_params('n_threads'),
        "n_threads_batch": get_key_from_params('n_threads_batch'),
        "use_mmap": get_key_from_params('use_mmap'),
        "use_mlock": get_key_from_params('use_mlock'),
        "n_gpu_layers": get_key_from_params('n_gpu_layers'),
        "main_gpu": get_key_from_params('main_gpu'),
        "tensor_split": get_key_from_params('tensor_split'),
        "top_p": get_key_from_params('top_p'),
        "n_ctx": get_key_from_params('n_ctx'),
        "rope_freq_base": get_key_from_params('rope_freq_base'),
        "numa": get_key_from_params('numa'),
        "verbose": get_key_from_params('verbose'),
        "top_k": get_key_from_params('top_k'),
        "use_mlock": get_key_from_params('use_mlock'),
        "temperature": get_key_from_params('temperature'),
        "repeat_penalty": get_key_from_params('repeat_penalty'),
        "max_tokens": get_key_from_params('max_tokens'),
        "typical_p": get_key_from_params('typical_p'),
        "n_batch": get_key_from_params('n_batch')
    }

    try:
        return Llama(model_path, **llama_params)
    except Exception as e:
        logger.log("Failed to create Llama object:", str(e))
        return None