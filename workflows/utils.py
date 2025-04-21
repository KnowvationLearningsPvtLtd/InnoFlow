# workflows/utils.py
import logging
import io
from gtts import gTTS
from transformers import pipeline
from .models import Node
from ai_integration.models import AIModelConfig
from ai_integration.providers_registry import ProviderRegistry

logger = logging.getLogger(__name__)
summarizer_pipeline = pipeline("summarization", model="facebook/bart-large-cnn")

def execute_node(node, input_data, continue_on_error=True):
    """
    Execute a node with enhanced error handling and logging
    """
    NODE_TYPE_HANDLERS = {
        'text_input': handle_text_input,
        'ai_completion': handle_ai_completion,
        'openai_tts': handle_tts,
        'huggingface_summarization': handle_summarization
    }

    try:
        if node.type not in NODE_TYPE_HANDLERS:
            raise ValueError(f"Unknown node type: {node.type}")
        handler = NODE_TYPE_HANDLERS[node.type]
        return handler(node, input_data)
    except Exception as e:
        logger.error(f"Error in Node {node.id}: {str(e)}", exc_info=True)
        if not continue_on_error:
            raise
        return None

def handle_text_input(node, input_data):
    """Handle text input node type"""
    return node.config.get('text', '')

def handle_tts(node, input_data):
    """Handle TTS node type"""
    if isinstance(input_data, dict):
        input_data = input_data.get("result", "")  # Extract text safely

    if not isinstance(input_data, str) or not input_data.strip():
        raise ValueError("Invalid input for TTS: Expected a non-empty string.")
    # Simulate TTS with error simulation
    if "simulate_failure" in node.config:
        raise ConnectionError("Simulated API connection failure")

    tts = gTTS(text=input_data, lang='en')
    audio_file = io.BytesIO()

    tts.write_to_fp(audio_file)
    audio_file.seek(0)
    return "TTS audio generated successfully"

def handle_summarization(node, input_data):
    """Handle summarization node type"""
    summary = summarizer_pipeline(input_data)
    return summary[0].get("summary_text", "No summary found")

def handle_ai_completion(node, input_data):
    """Handle AI completion node type"""
    config = node.config
    model_config_id = config.get('model_config_id')
    
    if not model_config_id:
        raise ValueError("Missing model_config_id in node configuration")
        
    model_config = AIModelConfig.objects.get(id=model_config_id)
    provider = ProviderRegistry.get_provider(model_config)
    return provider.generate_completion(str(input_data))
