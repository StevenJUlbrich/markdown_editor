# SRE Graphic Novel Scene Enhancement: Project Plan & Reference

## Project Overview

This document summarizes the plan for enhancing scene descriptions in an SRE educational graphic novel. The project aims to transform bland, teaching-focused scenes into rich, character-driven narratives that better engage production support professionals transitioning to SRE roles.

## Current State Assessment

### Issues Identified
- Scene descriptions lack visual richness and character details
- Most scenes have a singular teaching tone without variety
- Limited connection to the target audience (Production Support → SRE transition)
- Missing character dynamics and emotional elements
- Insufficient environmental and visual storytelling details

### Example Source Material
- 118 markdown chapter files
- Each file contains multiple educational panels
- Each panel includes Scene Description, Teaching Narrative, and Common Example sections

## Enhancement Workflow

The planned workflow is a semi-automated process that will:

1. **Analyze scene theme** (Chaos, Reflection, Teaching, Decision, Meta)
2. **Extract required roles** based on scene theme
3. **Match roles to existing characters** from character_base_list.json
4. **Rewrite scene** with enhanced details and character integration
5. **Evaluate against quality checklist**
6. **Generate speech bubbles** for characters
7. **Create image references** for the enhanced markdown

### Process Flow Diagram
```
Original Markdown → Scene Analysis → Role Extraction → Character Matching
                                                           ↓
Final Markdown ← Image Reference ← Speech Generation ← Scene Rewriting
                                                           ↓
                                                    Quality Validation
                                                     (Iterative Fix)
```

## Implementation Components

### 1. Scene Theme Analysis
- Uses LLM to classify scenes into predefined types
- Ensures variety across chapters via local validation
- **Enhancement needed:** Add chapter-level balance check

### 2. Role & Character Integration
- Extracts required roles based on scene theme
- Matches roles to existing characters in character_base_list.json
- Uses role-to-scene mapping to ensure appropriate representation
- **Enhancement needed:** Create scoring function for character-to-role matching

### 3. Scene Rewriting
- Transforms generic descriptions to character-driven narratives
- Incorporates teaching moments and emotional realism
- **Enhancement needed:** Add more environmental detail guidance

### 4. Content Validation
- Checks against quality criteria (teaching clarity, role effectiveness)
- Provides feedback for iterative improvement
- **Enhancement needed:** Add maximum iteration limit and confidence threshold

### 5. Speech Bubble Generation
- Creates character-appropriate dialogue
- Indicates communication medium (in-person, Slack, Zoom)
- Limits to 20 words per bubble

### 6. Output Generation
- Creates new markdown with enhanced scenes
- Generates image.json for the image generation pipeline
- Adds image references to markdown

## Quality Checklist

| Step | Description | Automated | Manual Check |
|------|-------------|-----------|--------------|
| Evaluate Scene Type | Is the scene type balanced in chapter? | Yes | Optional |
| Assign Roles/Cast | Are all characters clear and present? | Partial | Yes |
| Detail Environment | Lighting, UI, mood, placement | Yes | Yes |
| Concise Narration | 5 words or less essence | Yes | Yes |
| Character Presence | Physical or digital defined? | Yes | Yes |
| Validate Effectiveness | Are all elements pedagogically clear? | Partial | Yes |

## LLM Prompts Analysis

The current prompt collection (llm_prompts.yaml) includes:

- `scene_theme_analysis`: Identifies dominant theme
- `role_extraction`: Lists required character roles
- `scene_rewrite`: Transforms scene with character integration
- `scene_checklist_evaluation`: Validates against quality criteria
- `scene_rewrite_fix`: Addresses missing elements
- `character_enhancement`: Creates character details
- `speech_bubble_generation`: Generates appropriate dialogue
- `panel_image_alt_text`: Creates image alt text
- `neutral_scene_summary`: Provides neutral description

### Prompt Enhancement Recommendations

1. **Add scene_narration_essence prompt**:
   ```yaml
   scene_narration_essence: |
     Create a concise 5-words-or-less statement that captures the essence of this scene:
     ---
     {scene_text}
     ---
     Return only the concise statement.
   ```

2. **Enhance scene_rewrite prompt** to include more environmental guidance:
   ```yaml
   scene_rewrite: |
     Rewrite the following panel scene for a graphic novel, ensuring that at least these roles appear: {required_roles}.
     If available, use time of day or customer context to enhance mood.
     Make the SRE Lead guide or teach the junior SRE(s).
     Focus on emotional/psychological realism—not just action.
     Include specific environmental details:
     - Lighting and color tones
     - Key visible tech/UI elements
     - Character placement and postures
     Scene:
     ---
     {original_scene}
     ---
     Return only the rewritten scene as plain text.
   ```

3. **Add character_matching prompt**:
   ```yaml
   character_matching: |
     For each required role in this list: {required_roles}, find the best match from the available characters:
     ---
     {available_characters}
     ---
     Consider role compatibility, voice tone, and appearance.
     Return JSON with role-to-character mapping and confidence score (0-100):
     [
       {"role": "<role>", "character": "<name>", "confidence": <score>, "rationale": "<why>"},
       ...
     ]
   ```

## Integration Plan

The enhanced scene workflow will integrate with the existing MVC architecture:

1. **Input**: Selection of markdown file(s) or directory
2. **Processing**: Apply enhancement workflow to each panel
3. **Output**: 
   - New markdown files with enhanced scenes
   - Image.json files for image generation pipeline
   - Directory structure preserving organization

### File Structure
```
output/
  ├── enhanced_markdown/
  │   └── chapter_01.md
  ├── image_data/
  │   └── chapter_01_images.json
  └── images/
      └── ch1_p1_image.png
```

## Next Steps & Action Items

1. **Develop Character Matching Logic**
   - Create algorithm to match roles to existing characters
   - Define scoring criteria for match quality

2. **Implement Scene Type Balancing**
   - Develop validation for chapter-level scene type distribution
   - Create configuration for required scene type ratios

3. **Enhance Prompts**
   - Add narration essence prompt
   - Improve environmental detail guidance
   - Create character matching prompt

4. **Build Iteration Logic**
   - Implement quality validation loop
   - Set maximum iterations and confidence thresholds

5. **Integration Testing**
   - Test with sample chapters
   - Validate output quality and consistency

6. **Pipeline Integration**
   - Connect to image generation system
   - Ensure proper file structure for downstream processes

## References

- Character base list: character_base_list.json
- LLM prompts: llm_prompts.yaml
- Scene enhancement checklist
- Example before/after scene transformations

---

*This document serves as a living reference for the SRE Graphic Novel Scene Enhancement project. Update as requirements and implementation details evolve.*