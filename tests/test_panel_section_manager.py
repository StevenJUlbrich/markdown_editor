import sys
import os
sys.path.insert(0, os.path.abspath('src'))

from src.panel_section_manager import PanelSectionManager
from document_model import PanelPydantic, H3Pydantic


def make_panel():
    h3 = H3Pydantic(heading_text="Scene Description", h3_number_in_panel=1)
    panel = PanelPydantic(panel_title_text="Panel 1", h3_sections=[h3])
    return panel


def test_update_injects_heading():
    panel = make_panel()
    result = PanelSectionManager.update_named_section(panel, "Scene Description", "New content")
    assert result is True
    expected = "### Scene Description\n\nNew content"
    assert panel.h3_sections[0].api_improved_markdown == expected
    assert panel.h3_sections[0].api_suggested_enhancement_needed is True


def test_update_missing_title():
    panel = make_panel()
    result = PanelSectionManager.update_named_section(panel, "Missing", "text")
    assert result is False


def test_remove_fences_and_duplicate_heading():
    panel = make_panel()
    md = """```markdown
### Scene Description
foo
```
"""
    PanelSectionManager.update_named_section(panel, "Scene Description", md)
    expected = "### Scene Description\n\nfoo"
    assert panel.h3_sections[0].api_improved_markdown == expected
