import re

def is_greeting(message: str) -> bool:
    # Normalize message: lower case and remove extra repeated characters (e.g., hiiii -> hi)
    normalized = re.sub(r'(.)\1{2,}', r'\1', message.lower().strip())
    # Also handle 'hii' specifically
    normalized = re.sub(r'hi+', 'hi', normalized)
    
    greetings = ["hi", "hello", "hey", "greetings", "good morning", "good afternoon",
                 "good evening", "how are you", "what's up", "sup"]
    
    # Check if any greeting word is present as a standalone word
    return any(re.search(rf"\b{re.escape(word)}\b", normalized) for word in greetings)
