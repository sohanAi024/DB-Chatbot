def is_greeting(message: str) -> bool:
    greetings = ["hi", "hello", "hey", "greetings", "good morning", "good afternoon",
                 "good evening", "how are you", "what's up", "sup"]
    return any(word in message.lower() for word in greetings)