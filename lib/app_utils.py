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
    llama_params = get_params()

    try:
        return Llama(model_path, **llama_params)
    except Exception as e:
        logger.log("Failed to create Llama object:", str(e))
        return None