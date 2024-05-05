import ollama

def stream_chat(model, prompt, messages=[], temperature=0, max_tokens=60):
    return ollama.chat(model=model,
                       prompt=prompt,
                       messages=messages,
                       temperature=temperature,
                       max_tokens=max_tokens)

