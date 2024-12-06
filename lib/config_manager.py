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
    "core_url_cleanup": "http://192.168.56.1:5032/process_request_cleanup",
    "core_url_creative": "http://192.168.56.1:5032/process_request_creative",
    "max_file_size": 10485760,
    "model_folder": "models/",
    "revisions_per_page": 10,
    "default_prompt": "Generate ONLY a production-ready revision of this code surrounded by triple-backticks, without additional commentary, that resolves all execution errors, completely implements all existing features and adds 2 additional new features. The code you generate should be entirely self-contained, not relying on any external assets such as images or font files. Include code that verifies on start that every function in the code executes without error.",
    "model_filename_creative": "Mistral-Nemo-Instruct-2407-Q8_0.gguf",
    "model_filename_cleanup": "Mistral-Nemo-Instruct-2407-Q8_0.gguf",
    "model_url": "about:blank",
    "port": "5032",    
    "host": "0.0.0.0",
    "session_type": "filesystem",
    "secret_key": "your_secret_key",
    "extract_from_markdown": True,
    "revision_prompt": "Generate ONLY a production-ready revision of the code above surrounded by triple-backticks, without additional commentary, that resolves all execution errors, completely removes all comments, completely implements all features, and completely removes redundant code. The code you generate should be entirely self-contained, not relying on any external assets such as images or font files. Include code that verifies on start that every function in the code executes without error.",
    "log_folder": "logs/",
    "wrap_up_cutoff": 70000,
    "requirements_prompt": "Generate ONLY a sample requirements.txt surrounded by triple-backticks that would work for this code without version numbers or additional comments.",
    "nuget_prompt": "Generate ONLY a sample packages.config surrounded by triple-backticks that would work for this code without version numbers or additional comments.",
    "error_prompt": "Here is the latest execution error when I try to run the code:"
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
      "top_p": 0.95,
      "n_ctx": 131072,
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

   
   return params

def get_key_from_params(key):
   params = get_params()
   return params[key]