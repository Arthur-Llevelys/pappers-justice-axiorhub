def clamp_page(page: int, max_page: int) -> int:
    return min(max(1, page), max_page)


def clamp_per_page(requested: int, max_per_page: int) -> int:
    return min(max(1, requested), max_per_page)


def clean_params(data: dict) -> dict:
    cleaned = {}
    for key, value in data.items():
        if value is None or value == []:
            continue
        if key == "per_page":
            continue
        cleaned[key] = value
    return cleaned


def ensure_list_of_strings(value):
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value]
    return [str(value)]


def truncate_text(value: str | None, max_len: int) -> str | None:
    if value is None:
        return None
    if len(value) <= max_len:
        return value
    return value[:max_len] + "..."


def format_piece_reference(numbers: list[int]) -> str:
    nums = sorted(set(int(n) for n in numbers if n))
    if not nums:
        return ""
    if len(nums) == 1:
        return f"Pièce n°{nums[0]}"
    if len(nums) == 2:
        return f"Pièces n°{nums[0]} et {nums[1]}"
    return "Pièces n°" + ", ".join(map(str, nums[:-1])) + f" et {nums[-1]}"


def apply_inline_references(text: str, inline_references: list) -> str:
    if not text or not inline_references:
        return text
    result = text
    for ref in inline_references:
        target = getattr(ref, "target_text", None) if not isinstance(ref, dict) else ref.get("target_text")
        exhibit_numbers = getattr(ref, "exhibit_numbers", None) if not isinstance(ref, dict) else ref.get("exhibit_numbers", [])
        note = getattr(ref, "note", None) if not isinstance(ref, dict) else ref.get("note")
        if not target or target not in result:
            continue
        piece_ref = format_piece_reference(exhibit_numbers)
        suffix = f" ({piece_ref}"
        if note:
            suffix += f" ; {note}"
        suffix += ")"
        result = result.replace(target, target + suffix, 1)
    return result


def suggest_inline_references_for_text(text: str, exhibits: list[dict], max_suggestions: int = 8) -> list[dict]:
    if not text or not exhibits:
        return []
    lowered = text.lower()
    suggestions = []
    for exhibit in exhibits:
        num = exhibit.get("number")
        title = (exhibit.get("title") or "").strip()
        if not num or not title:
            continue
        candidates = []
        for sep in [":", "-", ","]:
            if sep in title:
                candidates.extend([p.strip() for p in title.split(sep) if p.strip()])
        candidates.append(title)
        picked = None
        for cand in candidates:
            cand_clean = cand.strip()
            if len(cand_clean) >= 8 and cand_clean.lower() in lowered:
                picked = cand_clean
                break
        if not picked:
            for token in title.split():
                token_clean = token.strip("()[];:,.")
                if len(token_clean) >= 8 and token_clean.lower() in lowered:
                    picked = token_clean
                    break
        if picked:
            suggestions.append({
                "target_text": picked,
                "exhibit_numbers": [num],
                "note": None,
            })
        if len(suggestions) >= max_suggestions:
            break
    return suggestions
