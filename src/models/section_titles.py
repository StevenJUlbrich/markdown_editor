from enum import Enum


class SectionTitles(Enum):
    SCENE_DESCRIPTION = "Scene Description"
    TEACHING_NARRATIVE = "Teaching Narrative"
    COMMON_EXAMPLE = "Common Example of the Problem"
    SRE_BEST_PRACTICE = "SRE Best Practice: Evidence-Based Investigation"
    BANKING_IMPACT = "Banking Impact"
    IMPLEMENTATION_GUIDANCE = "Implementation Guidance"
    # Add more as needed


def normalize_section_name(name: str) -> str:
    """
    Maps any variant of a section name (case-insensitive, whitespace-trimmed)
    to the official SECTION_TITLES value.
    Raises ValueError if the name is not a recognized section.

    Example:
        normalize_section_name("scene description")  # -> "Scene Description"
        normalize_section_name("  Teaching Narrative  ")  # -> "Teaching Narrative"
    """
    name_clean = name.strip().lower()
    for section in SECTION_TITLES:
        if name_clean == section.value.lower():
            return section.value
    raise ValueError(
        f"Unknown section title: {name!r}. Allowed: {[s.value for s in SECTION_TITLES]}"
    )


# Alias used across the codebase for convenience
SECTION_TITLES = SectionTitles
