def chapter_to_markdown(chapter, include_metadata_comments=False):
    """
    Convert a ChapterPydantic model to markdown.
    """
    lines = [f"# {chapter.chapter_title_text}"]
    if include_metadata_comments and getattr(chapter, "source_filename", None):
        lines.append(f"<!-- source: {chapter.source_filename} -->")
    for panel in getattr(chapter, "document_elements", []):
        lines.append(panel_to_markdown(panel, include_metadata_comments))
    return "\n\n".join(lines) + "\n"


def panel_to_markdown(panel, include_metadata_comments=False):
    lines = [f"## {panel.panel_title_text}"]
    if include_metadata_comments and getattr(panel, "heading_line_number", None):
        lines.append(f"<!-- line: {panel.heading_line_number} -->")
    for h3 in getattr(panel, "h3_sections", []):
        lines.append(h3_to_markdown(h3, include_metadata_comments))
    return "\n\n".join(lines)


def h3_to_markdown(h3, include_metadata_comments=False):
    lines = [f"### {h3.heading_text}"]
    if include_metadata_comments and getattr(h3, "heading_line_number", None):
        lines.append(f"<!-- line: {h3.heading_line_number} -->")
    if getattr(h3, "initial_content_markdown", None):
        content = h3.initial_content_markdown.strip()
        if content:
            lines.append(content)
    for h4 in getattr(h3, "h4_sections", []):
        lines.append(h4_to_markdown(h4, include_metadata_comments))
    return "\n\n".join(lines)


def h4_to_markdown(h4, include_metadata_comments=False):
    lines = [f"#### {h4.heading_text}"]
    if include_metadata_comments and getattr(h4, "heading_line_number", None):
        lines.append(f"<!-- line: {h4.heading_line_number} -->")
    if getattr(h4, "content_markdown", None):
        content = h4.content_markdown.strip()
        if content:
            lines.append(content)
    return "\n\n".join(lines)
