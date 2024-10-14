import os
from anthropic import Anthropic

# Ensure you have set the ANTHROPIC_API_KEY environment variable
api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
    raise ValueError("ANTHROPIC_API_KEY environment variable is not set")

client = Anthropic(api_key=api_key)

def translate_text(from_lang: str, to_lang: str, context: str, text: str) -> str:
    localization_guide = {
        'es': 'Use Spanish from Spain. Format dates as DD/MM/YYYY.',
        'fr': 'Use French from France. Format dates as DD/MM/YYYY.',
        'de': 'Use German from Germany. Format dates as DD.MM.YYYY.',
        'ru': 'Use Russian from Russia. Format dates as DD.MM.YYYY.',
        'zh-CN': 'Use Simplified Chinese from mainland China. Format dates as YYYY年MM月DD日.',
        'hi': 'Use Hindi as spoken in India. Format dates as DD/MM/YYYY.',
        'ar': 'Use Modern Standard Arabic. Format dates as DD/MM/YYYY. Use Arabic numerals (0-9), not Eastern Arabic numerals.'
    }
    
    prompt = f"""Translate the following text from {from_lang} to {to_lang}. 
    
    Localization guide: {localization_guide.get(to_lang, '')}
    
    Context: {context}
    
    Please ensure that the translation:
    1. Maintains the original meaning and tone
    2. Uses appropriate technical terminology for the target language
    3. Adapts any cultural references or idioms appropriately
    4. Follows the date format specified in the localization guide
    5. Uses appropriate formality level for technical documentation
    6. For Arabic, ensure the text is right-to-left compatible
    7. For Hindi, use Devanagari script
    
    Text to translate: {text}
    
    Translation:"""
    
    try:
        message = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ]
        )
        return message.content
    except Exception as e:
        print(f"Error in translation: {str(e)}")
        return ""

# Example usage
if __name__ == "__main__":
    result = translate_text("English", "hi", "Technical documentation about software deployment", "The update will be released on 4/1/2024.")
    print(result)
    result = translate_text("English", "ar", "Technical documentation about software deployment", "The update will be released on 4/1/2024.")
    print(result)
