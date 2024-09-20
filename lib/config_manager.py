import json
import os
import shutil
from lib.custom_logger import *

def is_numeric(value):
   return isinstance(value, (int, float)) and (isinstance(value, float) or str(value).replace('.', '', 1).isdigit())

def get_config(key, is_creative):
   config = get_full_config()
   if is_creative:
      config["model"] = config["model_filename_creative"]
   else:
      config["model"] = config["model_filename_cleanup"]
   config_value = config.get(key, "")
   return config_value

def get_full_config():

   config = {
    "core_url_cleanup": "http://mini_mob:5032/process_request_cleanup",
    "core_url_creative": "http://mini_mob:5032/process_request_creative",
    "max_file_size": 10485760,
    "model_folder": "models/",
    "revisions_per_page": 10,
    "default_prompt": "Generate ONLY a full revision of this code that resolves all execution errors, completely implements all existing features and adds 2 additional new features. The code you generate should be entirely self-contained, not relying on any external assets such as images or font files. Include code that verifies on start that every function in the code executes without error.",
    "model_filename_creative": "Mistral-Nemo-Instruct-2407-Q8_0.gguf",
    "model_filename_cleanup": "Mistral-Nemo-Instruct-2407-Q8_0.gguf",
    "model_url": "about:blank",
    "port": "5032",    
    "host": "0.0.0.0",
    "session_type": "filesystem",
    "secret_key": "your_secret_key",
    "extract_from_markdown": True,
    "revision_prompt": "Generate ONLY a full revision of the code above that resolves all execution errors, completely removes all comments, completely implements all features, and completely removes redundant code. The code you generate should be entirely self-contained, not relying on any external assets such as images or font files. Include code that verifies on start that every function in the code executes without error.",
    "log_folder": "logs/",
    "wrap_up_cutoff": 70000,
    "requirements_prompt": "Generate ONLY a sample requirements.txt file in markdown that would work for this code.",
    "nuget_prompt": "Generate ONLY a sample packages.config file in markdown that would work for this code.",
}

   return config

def get_params():

   params = {
        "n_threads": 0,
        "n_threads_batch": 0,
        "use_mmap": False,
        "use_mlock": False,
        "n_gpu_layers": 0,
        "main_gpu": 0,
        "tensor_split": "",
        "top_p": 1,
        "n_ctx": 131072,
        "rope_freq_base": 0,
        "numa": False,
        "verbose": True,
        "top_k": 1,
        "use_mlock": False,
        "temperature": 1,
        "repeat_penalty": 1,
        "max_tokens": 65536,
        "typical_p": 1,
        "n_batch": 2048,
        "min_p": 0,
        "frequency_penalty": 0,
        "presence_penalty": 0
    }
   
   return params

def get_key_from_params(key):
   params = get_params()
   return params[key]