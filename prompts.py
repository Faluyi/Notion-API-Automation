NAMING_CONVENTION_PROMPT = """
    Analyze if this project name follows GTD outcome-focused naming convention: "{name}"

    Rules:
    1. Name should use present perfect ("has been") or present tense ("is"/"are") constructions
    2. Name should describe a completed state
    3. Name should be clear and specific

    If invalid, suggest a better name following these rules.

    Return exactly two lines:
    Line 1: "valid" or "invalid"
    Line 2: If invalid, suggest better name. If valid, return original name
"""
