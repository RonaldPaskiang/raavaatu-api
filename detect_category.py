# detect_category.py

def detect_category_and_tags(prompt):
    prompt_lower = prompt.lower()
    
    if any(kw in prompt_lower for kw in ["resonance", "skyfall", "animology", "animic field"]):
        return "Science & Spirit Dynamics", ["resonance", "skyfall", "animology"]
    
    elif any(kw in prompt_lower for kw in ["write a scene", "emotional", "avatar state", "confrontation"]):
        return "Drama & Emotional Beats", ["scene", "emotion", "character"]

    elif any(kw in prompt_lower for kw in ["format", "notion", "table", "schema", "block"]):
        return "Notion Formatting", ["notion", "format", "structure"]

    elif any(kw in prompt_lower for kw in ["timeline", "canon", "year", "date", "event"]):
        return "Timeline & Canon Checker", ["timeline", "canon", "event"]

    elif any(kw in prompt_lower for kw in ["describe", "narrate", "poetic", "cinematic", "style"]):
        return "Scene Writing & Style", ["poetry", "cinema", "description"]

    else:
        return "Uncategorized", ["misc"]

import re

# Keywords grouped by category
CATEGORY_KEYWORDS = {
    "Science & Spirit Dynamics": [
        "resonance", "skyfall", "animology", "animusology", "bending", "spirit energy", "quantum", "field theory"
    ],
    "Drama & Emotional Beats": [
        "avatar state", "confront", "emotion", "love", "hurt", "teacher", "villain", "sparring"
    ],
    "Notion Formatting": [
        "notion", "table", "schema", "block", "paragraph", "quote", "structure", "format"
    ],
    "Timeline & Canon Checker": [
        "timeline", "contradiction", "year", "canon", "conflict", "event", "map", "origin"
    ],
    "Scene Writing & Style": [
        "write", "describe", "scene", "flashback", "narrate", "elemental", "poetic", "studio ghibli"
    ],
}

# Optional synonyms to catch more natural phrasing
TAG_SYNONYMS = {
    "resonance": ["harmonic", "frequency", "wave"],
    "animology": ["spirit science", "energy field", "spiritual physics"],
    "skyfall": ["anomaly", "disaster", "surge"],
    "avatar state": ["rage mode", "divine form"],
    "timeline": ["date", "era", "year", "period"],
    "notion": ["database", "table", "page", "entry"]
}


def smart_detect_category_and_tags(text):
    text_lower = text.lower()
    matched_tags = set()
    category_scores = {cat: 0 for cat in CATEGORY_KEYWORDS}

    # Tag matching with synonym expansion
    for tag, synonyms in TAG_SYNONYMS.items():
        if tag in text_lower or any(s in text_lower for s in synonyms):
            matched_tags.add(tag)

    # Add direct tag hits
    for cat, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                category_scores[cat] += 1
                matched_tags.add(keyword)

    # Pick the best scoring category
    best_category = max(category_scores, key=category_scores.get)
    return best_category, list(matched_tags)

