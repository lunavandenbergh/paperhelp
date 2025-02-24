def get_corrections(tool, text):
    matches = tool.check(text)
    corrections = []
    
    for match in matches:
        corrections.append({
            "error": match.context,
            "suggestion": match.replacements,
            "offset": match.offset,
            "length": match.errorLength,
            "type": match.ruleIssueType
        })
    
    return corrections

def highlight_text(text, corrections):
    highlighted_text = text
    for correction in sorted(corrections, key=lambda x: x["offset"], reverse=True):  
        start = correction["offset"]
        end = start + correction["length"]
        error_text = text[start:end]
        suggestion = ", ".join(correction["suggestion"])
        if correction["type"] == "misspelling":
            highlighted_text = (
                highlighted_text[:start] +
                f'<span style="background-color: pink;" title="{suggestion}">{error_text}</span>' +
                highlighted_text[end:]
            )
        elif correction["type"] == "grammar":
            highlighted_text = (
                highlighted_text[:start] +
                f'<span style="background-color: lightblue;" title="{suggestion}">{error_text}</span>' +
                highlighted_text[end:]
            )
        else:
            highlighted_text = (
                highlighted_text[:start] +
                f'<span style="background-color: yellow;" title="{suggestion}">{error_text}</span>' +
                highlighted_text[end:]
        )

    return highlighted_text