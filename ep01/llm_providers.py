"""EP01: the same generate() function, three ways.

Pick the provider with the LLM_PROVIDER environment variable (or .env):
    LLM_PROVIDER=ollama | openai | anthropic
"""
import os


def generate_ollama(prompt: str) -> str:
    import ollama

    r = ollama.chat(
        model=os.getenv("OLLAMA_MODEL", "llama3.2"),
        messages=[{"role": "user", "content": prompt}],
    )
    return r["message"]["content"]


def generate_openai(prompt: str) -> str:
    from openai import OpenAI

    client = OpenAI()  # reads OPENAI_API_KEY
    r = client.chat.completions.create(
        model=os.environ["OPENAI_MODEL"],
        messages=[{"role": "user", "content": prompt}],
    )
    return r.choices[0].message.content


def generate_anthropic(prompt: str) -> str:
    import anthropic

    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY
    r = client.messages.create(
        model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5-5"),
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return r.content[0].text


PROVIDERS = {
    "ollama": generate_ollama,
    "openai": generate_openai,
    "anthropic": generate_anthropic,
}


def generate(prompt: str) -> str:
    provider = os.getenv("LLM_PROVIDER", "ollama").lower()
    if provider not in PROVIDERS:
        raise ValueError(f"LLM_PROVIDER must be one of {list(PROVIDERS)}, got {provider!r}")
    return PROVIDERS[provider](prompt)


if __name__ == "__main__":
    print(generate("In one sentence: what is retrieval augmented generation?"))
