import openai
from django.conf import settings

def generate_completion(prompt, model="gpt-3.5-turbo", max_tokens=1000, temperature=0.7):
    """
    Generate text completion using OpenAI API
    
    Args:
        prompt (str): The prompt to generate completion for
        model (str): The model to use for completion
        max_tokens (int): Maximum number of tokens to generate
        temperature (float): Sampling temperature
        
    Returns:
        str: The generated completion text
    """
    try:
        # Set API key from settings
        openai.api_key = settings.OPENAI_API_KEY
        
        # Create chat completion
        response = openai.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        # Return the generated text
        return response.choices[0].message.content
    except Exception as e:
        # Log the error and return None or raise it depending on your preference
        print(f"Error generating completion: {e}")
        return None