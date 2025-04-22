# workflows/utils.py
import logging
import io
from gtts import gTTS
from transformers import pipeline
from .models import Node

logger = logging.getLogger(__name__)
summarizer_pipeline = pipeline("summarization", model="facebook/bart-large-cnn")

def execute_node(node: Node, input_data, continue_on_error=False):
    """Execute a node with enhanced error handling and logging"""
    try:
        logger.info(f"Executing Node {node.id} ({node.type}) with input: {str(input_data)[:50]}...")

        # Extract text from input data
        text = None
        if isinstance(input_data, dict):
            text = (input_data.get('result') or 
                   input_data.get('input') or 
                   input_data.get('text'))
            # Handle variables
            variables = input_data.get('variables', {})
            if variables and node.type == 'text_input':
                config_text = node.config.get('text', '')
                for var_name, value in variables.items():
                    var_placeholder = f'${{{var_name}}}'
                    if var_placeholder in config_text:
                        return value
        else:
            text = str(input_data) if input_data is not None else None

        if node.type == "text_input":
            result = node.config.get('text', text or '')

        elif node.type == "huggingface_summarization":
            if not text:
                text = node.config.get('text') or (
                    input_data if isinstance(input_data, str) else None
                )
            if not text:
                raise ValueError("Summarization input must be a string")
            
            # Handle short inputs
            max_length = min(130, len(text.split()) + 10)
            summary = summarizer_pipeline(text, max_length=max_length, min_length=10)
            result = summary[0].get("summary_text", "")

        elif node.type == "openai_tts":
            if not text:
                text = node.config.get('text', '')
            
            if not isinstance(text, str) or not text.strip():
                raise ValueError("Invalid input for TTS: Expected a non-empty string")
            
            tts = gTTS(text=text, lang=node.config.get('voice', 'en'))
            audio_file = io.BytesIO()
            tts.write_to_fp(audio_file)
            audio_file.seek(0)
            result = "TTS audio generated successfully"

        else:
            raise ValueError(f"Unknown node type: {node.type}")

        logger.info(f"Node {node.id} executed successfully. Output: {str(result)[:50]}...")
        return result

    except Exception as e:
        logger.error(f"Error in Node {node.id}: {str(e)}", exc_info=True)
        if not continue_on_error:
            raise
        return f"ERROR: {str(e)}"
