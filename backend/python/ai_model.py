from byllm import byLLM

def classify_waste(text):
    prompt = f"Classify this waste: {text}. Return one word: organic, plastic, metal, paper, or glass."
    return byLLM.generate(prompt)

def optimize_route(locations):
    if not locations:
        return []
    # Mock route optimization for MVP (simple sort)
    return sorted(locations)
