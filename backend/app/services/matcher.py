"""
Internship Relevance and Ranking Engine.
Computes deterministic, explainable match scores between Internship Offers and Subscriber Preferences.
Supports configurable feature weights, hard exclusions, and optional embedding interfaces.
"""

from typing import List, Dict, Any, Tuple, Optional
import re

ALGORITHM_VERSION = "1.0.0-deterministic"

# Feature Weights (Sum = 100)
WEIGHTS = {
    "role": 30.0,
    "skills": 25.0,
    "location": 20.0,
    "internship_type": 10.0,
    "language": 10.0,
    "keywords": 5.0,
}


def normalize_text(text: Optional[str]) -> str:
    """Safely normalizes text to lowercase stripped string."""
    if not text:
        return ""
    return re.sub(r"\s+", " ", str(text).lower().strip())


def normalize_list(items: Optional[List[Any]]) -> List[str]:
    """Safely normalizes a list of strings or JSON-serialized arrays."""
    if not items:
        return []
    res = []
    for item in items:
        if isinstance(item, str):
            res.append(normalize_text(item))
        elif isinstance(item, list):
            res.extend([normalize_text(i) for i in item if i])
    return [i for i in res if i]


def calculate_match_score(offer: Any, preference: Any) -> Dict[str, Any]:
    """
    Calculates a deterministic relevance score between 0.0 and 100.0.
    Returns score, breakdown, match features, hard exclusion flags, and algorithm version.
    """
    reasons = []
    breakdown = {k: 0.0 for k in WEIGHTS.keys()}
    
    # Extract normalized offer attributes
    offer_title = normalize_text(getattr(offer, "title", ""))
    offer_norm_title = normalize_text(getattr(offer, "normalized_title", ""))
    offer_company = normalize_text(getattr(offer, "company", ""))
    offer_desc = normalize_text(getattr(offer, "description", ""))
    offer_combined_text = f"{offer_title} {offer_norm_title} {offer_company} {offer_desc}"
    
    offer_skills = set(normalize_list(getattr(offer, "required_skills", [])))
    offer_languages = set(normalize_list(getattr(offer, "languages", [])))
    offer_country = normalize_text(getattr(offer, "country", ""))
    offer_location = normalize_text(getattr(offer, "location_raw", ""))
    offer_workplace = normalize_text(getattr(offer, "workplace_type", ""))  # remote, hybrid, onsite
    offer_type = normalize_text(getattr(offer, "internship_type", ""))      # pfe, standard, etc.

    # Extract normalized user preferences
    target_roles = normalize_list(getattr(preference, "target_roles", []))
    pref_skills = set(normalize_list(getattr(preference, "skills", [])))
    pref_countries = set(normalize_list(getattr(preference, "preferred_countries", [])))
    pref_workplaces = set(normalize_list(getattr(preference, "workplace_types", [])))
    pref_types = set(normalize_list(getattr(preference, "internship_types", [])))
    pref_languages = set(normalize_list(getattr(preference, "preferred_languages", [])))
    keywords = normalize_list(getattr(preference, "keywords", []))
    exclusion_keywords = normalize_list(getattr(preference, "exclusion_keywords", []))

    # --- 1. HARD EXCLUSION CHECKS ---
    for ex_kw in exclusion_keywords:
        if ex_kw and ex_kw in offer_combined_text:
            reasons.append(f"Excluded by negative keyword: '{ex_kw}'")
            return {
                "score": 0.0,
                "is_excluded": True,
                "exclusion_reason": f"Excluded by negative keyword: '{ex_kw}'",
                "breakdown": breakdown,
                "reasons": reasons,
                "algorithm_version": ALGORITHM_VERSION,
            }

    # Hard Exclusion for PFE-only preference
    if pref_types and "pfe" in pref_types and offer_type and offer_type != "pfe":
        # If user explicitly specified PFE and offer is explicitly non-PFE
        reasons.append(f"Excluded by internship type mismatch: Required PFE, got '{offer_type}'")
        return {
            "score": 0.0,
            "is_excluded": True,
            "exclusion_reason": f"Required PFE internship type, got '{offer_type}'",
            "breakdown": breakdown,
            "reasons": reasons,
            "algorithm_version": ALGORITHM_VERSION,
        }

    # --- 2. ROLE RELEVANCE (Weight: 30) ---
    role_score = 0.0
    if target_roles:
        matched_roles = [r for r in target_roles if r in offer_title or r in offer_norm_title]
        if matched_roles:
            role_score = WEIGHTS["role"]
            reasons.append(f"Role match: found {matched_roles}")
        else:
            reasons.append("No explicit target role match found in job title")
    else:
        role_score = WEIGHTS["role"] * 0.5  # Neutral default if no preference specified
        reasons.append("No specific role preference specified; neutral score given")
    breakdown["role"] = role_score

    # --- 3. SKILL OVERLAP (Weight: 25) ---
    skill_score = 0.0
    if pref_skills:
        if offer_skills:
            intersection = pref_skills.intersection(offer_skills)
            overlap_ratio = len(intersection) / len(pref_skills)
            skill_score = WEIGHTS["skills"] * overlap_ratio
            reasons.append(f"Skill overlap: {len(intersection)}/{len(pref_skills)} skills matched ({list(intersection)})")
        else:
            # Check for skills in job description as partial fallback
            matched_in_desc = [s for s in pref_skills if s in offer_desc]
            if matched_in_desc:
                overlap_ratio = (len(matched_in_desc) / len(pref_skills)) * 0.7  # Partial credit
                skill_score = WEIGHTS["skills"] * overlap_ratio
                reasons.append(f"Partial skill match in text: {matched_in_desc}")
            else:
                reasons.append("No skill overlap found")
    else:
        skill_score = WEIGHTS["skills"] * 0.5
        reasons.append("No skill preferences specified; neutral score given")
    breakdown["skills"] = skill_score

    # --- 4. LOCATION & WORKPLACE COMPATIBILITY (Weight: 20) ---
    loc_score = 0.0
    loc_reasons = []
    
    # Country / Location check
    country_matched = False
    if pref_countries:
        if offer_country and offer_country in pref_countries:
            country_matched = True
            loc_reasons.append(f"Country match: {offer_country}")
        elif any(c in offer_location for c in pref_countries):
            country_matched = True
            loc_reasons.append("Country matched in raw location text")
    else:
        country_matched = True  # Any country allowed

    # Remote / Workplace type check
    workplace_matched = False
    if pref_workplaces:
        if offer_workplace and offer_workplace in pref_workplaces:
            workplace_matched = True
            loc_reasons.append(f"Workplace match: {offer_workplace}")
        elif "remote" in pref_workplaces and "remote" in offer_combined_text:
            workplace_matched = True
            loc_reasons.append("Remote match found in text")
    else:
        workplace_matched = True  # Any workplace allowed

    if country_matched and workplace_matched:
        loc_score = WEIGHTS["location"]
    elif country_matched or workplace_matched:
        loc_score = WEIGHTS["location"] * 0.5
        loc_reasons.append("Partial location/workplace match")
    else:
        loc_reasons.append("Location/workplace mismatch")

    reasons.append("; ".join(loc_reasons) if loc_reasons else "Location checked")
    breakdown["location"] = loc_score

    # --- 5. INTERNSHIP TYPE COMPATIBILITY (Weight: 10) ---
    type_score = 0.0
    if pref_types:
        if offer_type and offer_type in pref_types:
            type_score = WEIGHTS["internship_type"]
            reasons.append(f"Internship type match: {offer_type}")
        elif not offer_type:
            type_score = WEIGHTS["internship_type"] * 0.5
            reasons.append("Offer internship type unstated; partial neutral score")
    else:
        type_score = WEIGHTS["internship_type"]
    breakdown["internship_type"] = type_score

    # --- 6. LANGUAGE COMPATIBILITY (Weight: 10) ---
    lang_score = 0.0
    if pref_languages:
        if offer_languages:
            lang_intersection = pref_languages.intersection(offer_languages)
            if lang_intersection:
                lang_score = WEIGHTS["language"]
                reasons.append(f"Language match: {list(lang_intersection)}")
            else:
                reasons.append("Language mismatch")
        else:
            lang_score = WEIGHTS["language"] * 0.5
            reasons.append("Offer languages unspecified; partial neutral score")
    else:
        lang_score = WEIGHTS["language"]
    breakdown["language"] = lang_score

    # --- 7. POSITIVE KEYWORDS (Weight: 5) ---
    kw_score = 0.0
    if keywords:
        matched_kws = [kw for kw in keywords if kw in offer_combined_text]
        if matched_kws:
            kw_score = WEIGHTS["keywords"] * (len(matched_kws) / len(keywords))
            reasons.append(f"Keywords matched: {matched_kws}")
    else:
        kw_score = WEIGHTS["keywords"]
    breakdown["keywords"] = kw_score

    total_score = round(sum(breakdown.values()), 2)

    return {
        "score": total_score,
        "is_excluded": False,
        "exclusion_reason": None,
        "breakdown": breakdown,
        "reasons": reasons,
        "algorithm_version": ALGORITHM_VERSION,
    }


class OptionalSemanticMatcher:
    """Optional embedding-based semantic matcher fallback interface."""

    def __init__(self, enabled: bool = False):
        self.enabled = enabled

    def get_semantic_similarity(self, text_a: str, text_b: str) -> float:
        """Fallback interface returning 0.0 when external paid LLM APIs are not present."""
        if not self.enabled:
            return 0.0
        # Extensible for local HuggingFace sentences-transformers or embeddings
        return 0.0