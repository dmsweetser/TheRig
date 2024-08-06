import re
from lib.config_manager import *
from lib.custom_logger import *
import time

def extract_code_blocks(markdown_text, return_first_only):
    code_blocks = []
    lines = markdown_text.split('\n')
    in_code_block = False
    code_block = []

    for line in lines:
        if line.startswith('```') and in_code_block == False:
            in_code_block = True
        elif line.startswith('```') and in_code_block == True:
            if code_block:
                code_blocks.append('\n'.join(code_block))
            in_code_block = False
            code_block = []
        elif in_code_block:
            code_block.append(line)

    if return_first_only and len(code_blocks) > 0:
        return code_blocks[0]

    return '\n\n'.join(code_blocks)

def run(original_code, llama_model, prompt, logger):

    start_time = time.time() # Get the start time

    response = llama_model.create_completion(
        prompt,
        temperature=get_key_from_params('temperature'),
        top_p=get_key_from_params('top_p'),
        top_k=get_key_from_params('top_k'),
        repeat_penalty=get_key_from_params('repeat_penalty'),
        typical_p=get_key_from_params('typical_p'),
        max_tokens= get_key_from_params('max_tokens')
        )

    revised_code = response['choices'][0]['text']
    
    # Check if extracting from Markdown is enabled in config
    extract_from_markdown = get_config('extract_from_markdown',False)
    
    return_first_only = False
    if get_config('requirements_prompt',False) in prompt:
        return_first_only = True
    if get_config('nuget_prompt',False) in prompt:
        return_first_only = True

    if extract_from_markdown:
        revised_code = extract_code_blocks(revised_code, return_first_only)
    
    end_time = time.time() # Get the end time
    duration = end_time - start_time # Calculate the duration

    print(f"Total duration in seconds: {duration}")
    
    logger.log(f"Original code length (not tokens): {len(original_code)}")
    logger.log(f"New code length (not tokens): {len(revised_code)}")

    if len(revised_code) < .8 * len(original_code):
        logger.log(f"Generated code was too short")
        return original_code
    elif len(revised_code) > 1.7 * len(original_code) and len(original_code) > 10000:
        logger.log(f"Generated code was too long")
        return original_code
    else:
        return revised_code
