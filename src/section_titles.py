from enum import Enum


class SectionTitles(Enum):
    SCENE_DESCRIPTION = "Scene Description"
    TEACHING_NARRATIVE = "Teaching Narrative"
    COMMON_EXAMPLE = "Common Example of the Problem"
    SRE_BEST_PRACTICE = "SRE Best Practice: Evidence-Based Investigation"
    BANKING_IMPACT = "Banking Impact"
    IMPLEMENTATION_GUIDANCE = "Implementation Guidance"
    # Add more as needed


# Alias used across the codebase for convenience
SECTION_TITLES = SectionTitles
