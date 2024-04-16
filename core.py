from flask import Flask, render_template, request, send_file, abort, jsonify, redirect, url_for
import gc
from multiprocessing import Array
from urllib.error import HTTPError
from urllib.parse import quote_plus, unquote_plus
from werkzeug.utils import secure_filename

from lib.config_manager import *
from lib.app_utils import *
from lib.custom_logger import *
from lib import revise_code

app = Flask(__name__)

if not os.path.exists(get_config("log_folder","")):
    os.makedirs(get_config("log_folder",""))

logger = CustomLogger(get_config("log_folder",""))

# Load existing config or set defaults
config = load_config()

# Set defaults if not present in the config
app.secret_key = get_config('secret_key', '')
app.config['MODEL_FOLDER'] = get_config('model_folder', '')
app.config['MODEL_URL'] = get_config('model_url', "")
app.config['MODEL_FILENAME'] = get_config('model', "")
app.config['MAX_CONTEXT'] = get_config('n_ctx', "")
app.config['REVISIONS_PER_PAGE'] = get_config('revisions_per_page', "")
app.config['SESSION_TYPE'] = get_config('session_type', '')
app.config['MAX_FILE_SIZE'] = get_config('max_file_size', "")

@app.route('/process_request', methods=['POST'])
def process_request():

    data = request.get_json() if request.is_json else request.form

    # Get the current ticks as a string
    now = datetime.datetime.now()
    current_ticks = now.strftime("%Y%m%d_%H%M%S")

    # Save the dictionary as a JSON file with the current ticks as the name
    with open(f"{get_config("log_folder")}data_{current_ticks}.json", "w") as outfile:
        json.dump(data, outfile, indent=4)

    prompt = data.get('prompt', '')
    file_contents = data.get('fileContents', '')

    llm = load_model(app.config['MODEL_URL'], app.config['MODEL_FOLDER'], app.config['MODEL_FILENAME'], app.config['MAX_CONTEXT'], logger)
    revision = revise_code.run(file_contents, llm, prompt, logger)

    # Save the dictionary as a JSON file with the current ticks as the name
    with open(f"{get_config("log_folder")}response_{current_ticks}.json", "w") as outfile:
        json.dump(revision, outfile, indent=4)

    del llm
    gc.collect()
    time.sleep(10)
    return revision

if __name__ == '__main__':
    
    port_number = get_config("port","")
    process_name, process_pid = find_process_by_port(port_number)

    if process_name and process_pid:
        logger.log(f"App cannot start: Port {port_number} is being used by process '{process_name}' (PID: {process_pid})")
    else:
        app.run(host=get_config("host",""),port=get_config("port",""))

    