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
    "n_threads_batch": 4,
    "top_k": 85,
    "use_mlock": False,
    "n_threads": 4,
    "max_file_size": 10485760,
    "verbose": True,
    "model_folder": "models/",
    "temperature": 1,
    "revisions_per_page": 10,
    "repeat_penalty": 1.01,
    "max_tokens": 16384,
    "default_prompt": "Generate ONLY a full revision of this code that resolves all execution errors, completely implements all existing features and implements 5 additional new features. If any execution error is due to a missing file, include code that creates the file if it is not present.",
    "n_gpu_layers": 0,
    "tensor_split": "",
    "model_filename_creative": "Mistral-7B-Instruct-v0.3-Q8_0.gguf",
    "model_filename_cleanup": "mixtral-8x7b-instruct-v0.1.Q5_K_M.gguf",
    "model_url": "about:blank",
    "port": "5032",
    "rope_freq_base": 0,
    "typical_p": 0.68,
    "use_mmap": False,
    "n_batch": 32,
    "numa": False,
    "host": "0.0.0.0",
    "session_type": "filesystem",
    "secret_key": "your_secret_key",
    "extract_from_markdown": True,
    "revision_prompt": "Generate ONLY a full revision of the code above that resolves all execution errors, completely removes all comments, and completely removes redundant code. If any execution error is due to a missing file, include code that creates the file if it is not present.",
    "main_gpu": 0,
    "top_p": 0.99,
    "n_ctx": 32768,
    "log_folder": "logs/",
    "wrap_up_cutoff": 35000,
    "requirements_prompt": "Generate ONLY a sample requirements.txt file in markdown that would work for this code.",
    "nuget_prompt": "Generate ONLY a sample packages.config file in markdown that would work for this code.",
    "model": ""
}

   return config