def chapter_to_markdown(chapter, include_metadata_comments=False):
    """
    Convert a ChapterPydantic model (with panels and generic content) to markdown.
    """
    lines = [f"# {chapter.chapter_title_text}"]
    if include_metadata_comments:
        if getattr(chapter, "source_filename", None):
            lines.append(f"<!-- source: {chapter.source_filename} -->")
        if getattr(chapter, "heading_line_number", None):
            lines.append(f"<!-- line: {chapter.heading_line_number} -->")
    # Walk document_elements in order
    for element in getattr(chapter, "document_elements", []):
        if element.__class__.__name__ == "PanelPydantic":
            lines.append(panel_to_markdown(element, include_metadata_comments))
        elif element.__class__.__name__ == "GenericContentPydantic":
            lines.append(
                generic_content_to_markdown(element, include_metadata_comments)
            )
        else:
            # If some other block type is present, handle gracefully
            lines.append(f"<!-- unknown element: {type(element).__name__} -->")
    return "\n\n".join(lines) + "\n"


def panel_to_markdown(panel, include_metadata_comments=False):
    lines = [f"## {panel.panel_title_text}"]
    if include_metadata_comments:
        if getattr(panel, "heading_line_number", None):
            lines.append(f"<!-- line: {panel.heading_line_number} -->")
        if hasattr(panel, "version"):
            lines.append(f"<!-- version: {getattr(panel, 'version', 1)} -->")
    for h3 in getattr(panel, "h3_sections", []):
        lines.append(h3_to_markdown(h3, include_metadata_comments))
    return "\n\n".join(lines)


def generic_content_to_markdown(generic, include_metadata_comments=False):
    """
    Export GenericContentPydantic node as a markdown H2 section or plain text.
    """
    lines = []
    # Use title_text as H2 if present
    if getattr(generic, "title_text", None):
        lines.append(f"## {generic.title_text}")
    if include_metadata_comments:
        if getattr(generic, "heading_line_number", None):
            lines.append(f"<!-- line: {generic.heading_line_number} -->")
        if hasattr(generic, "version"):
            lines.append(f"<!-- version: {getattr(generic, 'version', 1)} -->")
    if getattr(generic, "content_markdown", None):
        content = generic.content_markdown.strip()
        if content:
            lines.append(content)
    return "\n\n".join(lines)


def h3_to_markdown(h3, include_metadata_comments=False):
    lines = [f"### {h3.heading_text}"]
    if include_metadata_comments:
        if getattr(h3, "heading_line_number", None):
            lines.append(f"<!-- line: {h3.heading_line_number} -->")
        if hasattr(h3, "version"):
            lines.append(f"<!-- version: {getattr(h3, 'version', 1)} -->")
    if getattr(h3, "initial_content_markdown", None):
        content = h3.initial_content_markdown.strip()
        if content:
            lines.append(content)
    for h4 in getattr(h3, "h4_sections", []):
        lines.append(h4_to_markdown(h4, include_metadata_comments))
    return "\n\n".join(lines)


def h4_to_markdown(h4, include_metadata_comments=False):
    lines = [f"#### {h4.heading_text}"]
    if include_metadata_comments:
        if getattr(h4, "heading_line_number", None):
            lines.append(f"<!-- line: {h4.heading_line_number} -->")
        if hasattr(h4, "version"):
            lines.append(f"<!-- version: {getattr(h4, 'version', 1)} -->")
    if getattr(h4, "content_markdown", None):
        content = h4.content_markdown.strip()
        if content:
            lines.append(content)
    return "\n\n".join(lines)
