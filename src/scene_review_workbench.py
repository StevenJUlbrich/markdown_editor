import json
from pathlib import Path

import streamlit as st

from document_model import MarkdownDocument, PanelPydantic
from openai_service import (
    generate_improved_visual_scene_description,
    generate_scene_analysis_from_ai,
    rewrite_scene_and_teaching_as_summary,
)

st.set_page_config(page_title="Scene Review Workbench", layout="wide")

st.title("🧠 Scene Review Workbench")
st.markdown(
    "Use this tool to load a markdown chapter, analyze scenes, and optionally rewrite panels using OpenAI."
)

md_file = st.file_uploader("Upload a markdown file (.md)", type=["md"])
char_file = st.file_uploader("Upload your character JSON", type=["json"])

if md_file and char_file:
    temp_md_path = Path("_uploaded_temp.md")
    temp_json_path = Path("_uploaded_characters.json")
    temp_md_path.write_text(md_file.read().decode("utf-8"), encoding="utf-8")
    temp_json_path.write_text(char_file.read().decode("utf-8"), encoding="utf-8")

    doc = MarkdownDocument(filepath=str(temp_md_path))
    character_data = json.loads(temp_json_path.read_text(encoding="utf-8"))

    st.success(
        f"Loaded {temp_md_path.name} with {len(doc.chapter_model.document_elements)} document elements."
    )

    panel_options = [
        panel
        for panel in doc.chapter_model.document_elements
        if isinstance(panel, PanelPydantic)
    ]

    panel_labels = [
        f"Panel {p.panel_number_in_doc}: {p.panel_title_text}" for p in panel_options
    ]
    selected_index = st.selectbox(
        "Select a panel to review:",
        list(range(len(panel_labels))),
        format_func=lambda i: panel_labels[i],
    )
    selected_panel = panel_options[selected_index]

    if selected_panel:
        section_map = doc.extract_named_sections_from_panel(
            selected_panel.panel_number_in_doc
        )
        scene_md = section_map.get("Scene Description", "")
        teaching_md = section_map.get("Teaching Narrative", "")
        example_md = section_map.get("Common Example of the Problem", "")

        st.subheader("📝 Scene Description")
        st.markdown(f"```markdown\n{scene_md}\n```")

        st.subheader("🎓 Teaching Narrative")
        st.markdown(f"```markdown\n{teaching_md}\n```")

        if st.button("🔍 Run Scene Analysis"):
            analysis = generate_scene_analysis_from_ai(scene_md, teaching_md)
            selected_panel.scene_analysis = analysis
            st.session_state["scene_analysis"] = analysis

        if "scene_analysis" in st.session_state:
            analysis = st.session_state["scene_analysis"]
            st.subheader("📊 Scene Analysis")
            st.write(analysis.model_dump())

            st.markdown("---")
            st.subheader("✍️ AI-Assisted Scene Rewriter")
            rewrite_intent = st.text_input(
                "Describe how you'd like to improve this scene (e.g., 'Make this a Chaos Scene with visual tension.')"
            )

            if st.button("🔁 Generate Improved Scene Description"):
                result = generate_improved_visual_scene_description(
                    scene_md=scene_md,
                    teaching_md=teaching_md,
                    common_example_md=example_md,
                    scene_analysis=analysis,
                    character_roles={},  # placeholder
                    chapter_index=1,  # placeholder
                    panel_index=selected_panel.panel_number_in_doc,
                )
                st.session_state["rewrite_result"] = result

        if "rewrite_result" in st.session_state:
            st.subheader("🖼️ Rewritten Scene Description")
            st.markdown(
                f"```markdown\n{st.session_state['rewrite_result']['improved_scene_description']}\n```"
            )
            st.subheader("🎭 Cast and Visual Tags")
            st.json(st.session_state["rewrite_result"], expanded=False)

            if st.button("📥 Replace Scene in Markdown"):
                updated_md = st.session_state["rewrite_result"][
                    "improved_scene_description"
                ]
                doc.update_named_section_in_panel(
                    panel_id=selected_panel.panel_number_in_doc,
                    section_h3_title="Scene Description",
                    new_markdown_content=updated_md,
                )
                st.success(
                    "Scene Description replaced in memory. You can now export the full markdown."
                )

        if st.button("💾 Save Updated Markdown"):
            output_md_path = Path("_edited_" + temp_md_path.name)
            doc.save_document(str(output_md_path))
            st.download_button(
                label="Download Updated Markdown File",
                data=output_md_path.read_text(encoding="utf-8"),
                file_name=output_md_path.name,
                mime="text/markdown",
            )

        if st.button("📦 Export panel JSON"):
            from comic_image_pipeline import process_panel_to_json

            panel_json = process_panel_to_json(
                doc=doc,
                panel=selected_panel,
                character_data=character_data,
                character_json_path=temp_json_path,
                characters_per_role=2,
                chapter_prefix=temp_md_path.stem,
                images_folder="images",
            )
            if panel_json:
                st.download_button(
                    label="Download JSON for this panel",
                    data=json.dumps(panel_json, indent=2),
                    file_name=f"panel_{selected_panel.panel_number_in_doc}_analysis.json",
                    mime="application/json",
                )
