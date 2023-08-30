# Optimizing the clean_text function to correctly handle various kinds of escape sequences
import re

def clean_text_advanced(text: str) -> str:
    # Decode any escape sequences to their actual Unicode characters
    text = bytes(text, "utf-8").decode("unicode_escape")
    
    # Remove non-ASCII characters
    text = ''.join(char for char in text if ord(char) < 128)
    
    return text.strip()


# Update sanitize_string to use clean_text_advanced
def sanitize_string(field: str) -> str:
    cleaned_field = clean_text_advanced(field)
    return cleaned_field.strip()

# Update sanitize_dict to use the new sanitize_string
def sanitize_dict(data_dict: dict) -> dict:
    return {
        key: sanitize_string(value) if isinstance(value, str) else value
        for key, value in data_dict.items()
    }
