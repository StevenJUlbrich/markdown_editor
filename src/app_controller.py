# app_controller.py
from document_model import MarkdownDocument


class AppController:
    def __init__(self):
        self.doc = None

    def load_document(self, filepath):
        self.doc = MarkdownDocument()
        return self.doc.load_and_process(filepath)

    def get_document_structure_view(self):
        if not self.doc or not self.doc.structured_data:
            return "No document loaded or structure is empty."

        output = []
        for panel in self.doc.structured_data:
            output.append(f"Panel: {panel['panel_title_text']}")
            for sub in panel["sub_content"]:
                output.append(
                    f"  Sub: {sub['sub_heading_text']} ({len(sub['blocks'])} blocks)"
                )
        return "\n".join(output)

    def get_content_for_api(self, panel_title_fragment, subsection_title_fragment):
        """Example: Get content of one subsection for an API call."""
        if not self.doc:
            return None
        panel = self.doc.get_panel_by_title(panel_title_fragment)
        if not panel:
            return "Panel not found."
        subsection = self.doc.get_subsection_by_title(panel, subsection_title_fragment)
        if not subsection:
            return "Subsection not found."

        return self.doc.get_subsection_markdown(subsection)

    def process_multiple_sections_for_api(self, sections_to_process, common_prompt):
        """
        sections_to_process: list of tuples [(panel_frag, sub_frag), ...]
        Simulates sending multiple sections to API.
        """
        if not self.doc:
            print("No document loaded.")
            return

        print("\n--- Simulating API Calls for Multiple Sections ---")
        all_api_data = []
        for panel_frag, sub_frag in sections_to_process:
            content = self.get_content_for_api(panel_frag, sub_frag)
            if content and "not found" not in content.lower():
                print(
                    f"\n[API Call Simulation for Panel '{panel_frag}', Sub-section '{sub_frag}']"
                )
                print(f"Prompt: {common_prompt}")
                print(f"Content to send (first 100 chars): {content[:100]}...")
                # In a real app, you'd make the API call here
                # mock_response = f"Mock API response for {sub_frag}"
                all_api_data.append(
                    {
                        "panel": panel_frag,
                        "subsection": sub_frag,
                        "original_content": content,
                        # "api_response": mock_response
                    }
                )
            else:
                print(
                    f"Could not retrieve content for Panel '{panel_frag}', Sub-section '{sub_frag}'."
                )
        return all_api_data

    def modify_content_example(self, panel_frag, sub_frag, new_content_md):
        """Example of modifying content."""
        if not self.doc:
            print("No document loaded.")
            return False
        print(f"\nAttempting to modify: Panel '{panel_frag}', Sub-section '{sub_frag}'")
        return self.doc.update_subsection_content(panel_frag, sub_frag, new_content_md)

    def add_content_example(self, panel_frag, sub_frag, new_content_md, position="end"):
        """Example of adding content."""
        if not self.doc:
            print("No document loaded.")
            return False
        print(
            f"\nAttempting to add content to: Panel '{panel_frag}', Sub-section '{sub_frag}'"
        )
        return self.doc.add_content_to_subsection(
            panel_frag, sub_frag, new_content_md, position
        )

    def save_document(self, output_filepath):
        if not self.doc:
            print("No document loaded to save.")
            return False
        return self.doc.save_document(output_filepath)
