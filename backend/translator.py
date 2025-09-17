from backend.ollama_client import ask_ollama

# Language mapping for better prompts
LANGUAGE_NAMES = {
    "es": "Spanish",
    "fr": "French", 
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "ru": "Russian",
    "ja": "Japanese",
    "zh": "Chinese",
    "hi": "Hindi",
    "ar": "Arabic"
}

def translate_text(text, target_language):
    """
    Uses Ollama to translate text between languages
    """
    try:
        target_name = LANGUAGE_NAMES.get(target_language, target_language)
        
        prompt = f"""
        You are a professional translator. Translate the following English text to {target_name}.
        Provide only the translation, no additional text or explanations.
        
        Text to translate: "{text}"
        
        Translation:
        """
        
        translation = ask_ollama(prompt)
        
        # Clean up the response (remove any extra text Ollama might add)
        translation = translation.strip()
        
        # Remove any prefix like "Translation:" or similar
        if ':' in translation:
            parts = translation.split(':', 1)
            if len(parts) > 1:
                translation = parts[1].strip()
        
        return translation
        
    except Exception as e:
        return f"Translation failed: {str(e)}"

# Language options with codes and flags
LANGUAGE_OPTIONS = {
    "es": {"name": "Spanish", "flag": "🇪🇸"},
    "fr": {"name": "French", "flag": "🇫🇷"},
    "de": {"name": "German", "flag": "🇩🇪"},
    "it": {"name": "Italian", "flag": "🇮🇹"},
    "pt": {"name": "Portuguese", "flag": "🇵🇹"},
    "ru": {"name": "Russian", "flag": "🇷🇺"},
    "ja": {"name": "Japanese", "flag": "🇯🇵"},
    "zh": {"name": "Chinese", "flag": "🇨🇳"},
    "hi": {"name": "Hindi", "flag": "🇮🇳"},
    "ar": {"name": "Arabic", "flag": "🇸🇦"},
}