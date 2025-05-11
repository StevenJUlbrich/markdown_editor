# Python Markdown Parser and OpenAI

Created with 2.5 Pro (preview) May 8, 2025 at 08:53 PM  
Published May 11, 2025 at 09:34 AM

## Initial Request

I need help to write a python application that can read and parse this markdown file. I have many files that I need to read and parse. The goal is it take a section "Panel" and section following it to the next panel or end of the document. The sections would be sent to a OpenAI API to respond to some prompt. I would update the document.

## Analysis

Okay, I can help you outline a Python application to read and parse your Markdown files, extract the "Panel" sections as you've described, and prepare them for an OpenAI API.

Here's a breakdown of the approach and a Python code snippet to get you started.

### Approach

1. **Read the Markdown File**: The first step is to read the content of your Markdown file into your Python script.
2. **Identify "Panel" Sections**: You'll need a way to identify the start of each "Panel" section. Based on your chapter_01_draft.md file, these sections seem to start with ## Panel X:.
3. **Extract Content**: Once a "Panel" section is identified, you need to capture all the text that follows it until either the next "Panel" section begins or the end of the document is reached.
4. **Process Each Section**: For each extracted section, you will:
   - Send it to the OpenAI API (you'll need to integrate the openai Python library for this).
   - Receive the response from the API.
   - Update the document (this part will heavily depend on how you want to incorporate the OpenAI response back into your Markdown structure).

### Python Code Example

```python
import re

def parse_markdown_panels(file_path):
    """
    Reads a Markdown file and extracts sections starting with "## Panel X:"
    and the content following it until the next panel or end of the document.

    Args:
        file_path (str): The path to the Markdown file.

    Returns:
        list: A list of dictionaries, where each dictionary contains
              the panel title and its content.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return []
    except Exception as e:
        print(f"Error reading file: {e}")
        return []

    # Regex to find "## Panel X: Title" and capture the content
    # until the next "## Panel" or end of the document.
    # This regex uses a positive lookahead to find the next panel or end of file.
    panels = re.finditer(r"(##\s+Panel\s+\d+:[^\n]+)\n(.*?)(?=(?:##\s+Panel\s+\d+:)|$)", content, re.DOTALL | re.MULTILINE)

    extracted_sections = []
    for match in panels:
        panel_title = match.group(1).strip()
        panel_content = match.group(2).strip()
        extracted_sections.append({
            "title": panel_title,
            "content": panel_content
        })
    return extracted_sections

def process_with_openai(panel_content, your_prompt):
    """
    Placeholder function to simulate sending content to OpenAI API.
    Replace this with your actual OpenAI API call.
    """
    print(f"\n--- Sending to OpenAI (Simulated) ---")
    print(f"Prompt: {your_prompt}")
    print(f"Content Snippet: {panel_content[:200]}...") # Displaying a snippet

    # Example: Replace with actual API call
    # from openai import OpenAI
    # client = OpenAI(api_key="YOUR_OPENAI_API_KEY")
    # response = client.chat.completions.create(
    # model="gpt-3.5-turbo", # Or your desired model
    # messages=[
    # {"role": "system", "content": "You are a helpful assistant."},
    # {"role": "user", "content": f"{your_prompt}\n\n{panel_content}"}
    # ]
    # )
    # api_response = response.choices[0].message.content
    api_response = f"This is a simulated OpenAI response for the content related to: {panel_content[:50]}..."
    print(f"OpenAI Response (Simulated): {api_response}")
    return api_response

def update_document_logic(original_content, panel_title, openai_response):
    """
    Placeholder for your document update logic.
    This will be highly specific to how you want to integrate the OpenAI response.
    For example, you might want to insert it after the panel, or replace
    certain parts, or add it as a comment.
    """
    print(f"\n--- Updating Document (Simulated) ---")
    print(f"Logic to update document with OpenAI response for '{panel_title}' would go here.")
    # This is a very basic example of appending. You'll need more sophisticated logic.
    updated_content = original_content + f"\n\n\n{openai_response}\n"
    return updated_content

# --- Main Execution ---

if __name__ == "__main__":
    # Replace with the actual path to your file
    markdown_file_path = 'chapter_01_draft.md'
    # You can also iterate through a list of files if you have many.

    print(f"Parsing Markdown file: {markdown_file_path}")
    panel_sections = parse_markdown_panels(markdown_file_path)

    if not panel_sections:
        print("No panel sections found or error in parsing.")
    else:
        print(f"\nFound {len(panel_sections)} panel sections.")

        # Example: Read the original content again if you need to modify it in place
        # Or, build a new document string
        try:
            with open(markdown_file_path, 'r', encoding='utf-8') as f:
                original_document_content = f.read()
            new_document_content = original_document_content # Start with original
        except Exception as e:
            print(f"Error reading file for update: {e}")
            original_document_content = "" # Or handle error appropriately
            new_document_content = ""


        for section in panel_sections:
            print(f"\nProcessing Panel: {section['title']}")
            # Define your prompt for the OpenAI API
            your_custom_prompt = "Please summarize the key issues described in the following panel section and suggest three actionable recommendations:"

            openai_response = process_with_openai(section['content'], your_custom_prompt)

            # --- Document Update ---
            # This is where you would implement the logic to update your document.
            # For this example, we're just printing.
            # You might want to write to a new file or modify the existing one.
            # Be careful when modifying files in place.
            print(f"\nSimulating update for section: {section['title']}")
            # If you were to update the document content string:
            # new_document_content = update_document_logic(new_document_content, section['title'], openai_response)


        # Example: Save the updated content to a new file or overwrite
        # output_file_path = 'chapter_01_draft_updated.md'
        # try:
        #     with open(output_file_path, 'w', encoding='utf-8') as f:
        #         f.write(new_document_content)
        #     print(f"\nUpdated document saved to: {output_file_path}")
        # except Exception as e:
        #     print(f"Error writing updated file: {e}")

        print("\n--- Processing Complete ---")
```

### Explanation of the Code

- **parse_markdown_panels(file_path):**
  - Reads the specified Markdown file.
  - Uses re.finditer with a regular expression:
    - `(##\s+Panel\s+\d+:[^\n]+)\n`: This part captures the panel title line (e.g., "## Panel 1: Why Traditional Metrics Fail").
    - `(.*?)`: This captures the content of the panel (non-greedy).
    - `(?=(?:##\s+Panel\s+\d+:)|$)`: This is a positive lookahead. It ensures the content is captured up to the next "## Panel X:" heading or the end of the file ($), without including the next panel's heading in the current panel's content.
    - `re.DOTALL`: Allows . to match newline characters.
    - `re.MULTILINE`: Makes ^ and $ match the start/end of each line.
  - Returns a list of dictionaries, each containing a title and content.

- **process_with_openai(panel_content, your_prompt):**
  - This is a placeholder function. You will need to replace the commented-out section with your actual code to call the OpenAI API.
  - Remember to install the OpenAI library (pip install openai) and set up your API key.

- **update_document_logic(...):**
  - This is also a placeholder. Updating the document can be complex. You need to decide:
    - Do you want to insert the OpenAI response directly after each panel?
    - Do you want to replace the original panel content?
    - Do you want to create a new file with the changes or modify the existing one?
  - The example shows a very simple way to append the response as a comment. You'll likely need a more sophisticated method, perhaps involving finding the end of the specific panel in the original text and inserting the new content there.

- **Main Execution Block (if __name__ == "__main__":):**
  - Sets the markdown_file_path.
  - Calls parse_markdown_panels to get the sections.
  - Loops through each section.
  - Calls the (placeholder) process_with_openai.
  - Includes commented-out example logic for how you might manage the document content for updates and save it.

### Considerations for Your Application

- **OpenAI API Integration:**
  - You'll need an OpenAI API key.
  - Install the openai library: pip install openai.
  - Refer to the official OpenAI documentation for the most up-to-date methods for making API calls.
  - Consider API rate limits and costs.
  - Implement proper error handling for API requests.

- **Document Updating:**
  - This is the trickiest part. Modifying files programmatically requires care.
  - Strategy 1: Create a New File: Read the original, process, and write all content (original + modifications) to a new file. This is safer.
  - Strategy 2: In-Place Modification (More Complex): If you need to modify the original file, you'll need to carefully manage how you insert or replace text. This could involve reading the whole file, making changes in memory, and then writing the entire modified content back, or more advanced text manipulation.
  - Structure of Updates: Decide precisely how the OpenAI response should be formatted and where it should appear in relation to the original panel text.

- **Error Handling:**
  - Add robust error handling for file operations, API calls, and unexpected Markdown structures.
  - Configuration: For API keys or other settings, consider using environment variables or configuration files instead of hardcoding them.
  - Processing Many Files: You can easily extend the if __name__ == "__main__": block to loop through a list of file paths if you have multiple Markdown files to process.

This script should give you a solid foundation. Remember to fill in the OpenAI API call and the document update logic according to your specific requirements.

## Python Libraries for Markdown Processing

Yes, there are several Python libraries that can provide more robust and structured ways to read, parse, and even update Markdown files, going beyond what a simple regular expression approach can offer. Using these libraries can make your code cleaner, more resilient to variations in Markdown syntax, and easier to maintain, especially when you need to modify the document structure.

The key advantage of many of these libraries is that they parse the Markdown into an Abstract Syntax Tree (AST) or a similar structured representation. This allows you to programmatically navigate and manipulate the document's components (like headings, paragraphs, lists, code blocks) before regenerating the Markdown output.

Here are some Python libraries that can help:

### Mistletoe

- **Reading/Parsing**: Mistletoe is a fast, extensible, and CommonMark-compliant Markdown parser. It parses Markdown into an AST.
- **Updating**: Crucially, Mistletoe provides a Markdown renderer. This means you can parse a document, potentially modify the AST (though direct AST manipulation might require understanding its structure), and then render it back to a Markdown string. This is very useful for your goal of updating the document.
- **How it could help you**: You could parse the document, traverse the AST to find your "Panel" heading blocks, collect the subsequent blocks until the next "Panel" or end of document, and then potentially insert new blocks (representing the OpenAI response) into the AST before rendering back to Markdown.

```python
# Conceptual example with Mistletoe
from mistletoe import Document
from mistletoe.markdown_renderer import MarkdownRenderer

# doc = Document(open('chapter_01_draft.md').read())
# Traverse doc.children (AST nodes) to find panels
# Modify the AST (e.g., by inserting new nodes)
# ... (requires specific logic based on Mistletoe's AST structure)
# Render back to Markdown
# with MarkdownRenderer() as renderer:
#     updated_markdown = renderer.render(doc)
# print(updated_markdown)
```

### markdown-it-py

- **Reading/Parsing**: This is a Python port of the popular markdown-it JavaScript library. It's known for its speed, CommonMark compliance, and extensibility through plugins. It parses Markdown into a token stream, which is a list of recognized Markdown elements.
- **Updating**: While its primary output is often HTML, the token stream itself can be manipulated. If you can modify this list of tokens (e.g., insert new tokens representing the OpenAI response) and then find a way to render that token stream back to Markdown (either via a plugin or a custom function), this could work. The extensibility might allow you to create custom rules or renderers.

### markdown-toolkit

- **Reading/Parsing & Updating**: This library is specifically designed for creating and manipulating Markdown. Its documentation mentions "Injection of static text, file contents, or dynamically generated markdown into existing documents." This sounds very aligned with your needs. It provides an object-oriented interface for working with Markdown elements.
- **How it could help you**: You might be able to parse the document into its object model, locate the "Panel" elements, and then use the library's functions to inject your OpenAI responses in the desired locations.

### Python-Markdown

- **Reading/Parsing**: This is one of the oldest and most well-known Python Markdown libraries. It's highly extensible. It parses Markdown and typically converts it to HTML. It does build an internal ElementTree-like structure.
- **Updating**: While its main focus is HTML conversion, its extension API is powerful. It might be possible to write an extension to traverse the tree, identify your panels, and then reconstruct a Markdown document. However, rendering back to Markdown is not its primary out-of-the-box feature, so it might require more effort for the "updating" part compared to Mistletoe or markdown-toolkit.

### Marko

- **Reading/Parsing**: A CommonMark-compliant parser that also aims for high extensibility. It parses to an AST.
- **Updating**: Similar to other AST-based parsers, if you can modify the AST and if there's a straightforward way to serialize that AST back into Markdown text, Marko could be a good option. You'd need to check its API for Markdown rendering capabilities.

### How to Choose and General Approach for Updating

For your specific use case (finding Panels and inserting content):
- Mistletoe seems like a strong candidate due to its explicit Markdown renderer.
- markdown-toolkit also appears promising due to its focus on manipulation and injection.

General workflow for updating:
1. **Parse**: Read the Markdown file and parse it into the library's internal representation (AST, token stream, object model).
2. **Traverse/Identify**: Navigate this structure to find your "## Panel X:" headings.
3. **Extract**: Collect the content associated with each panel (the nodes/tokens that follow the heading until the next panel or the end).
4. **Send to API**: Send this extracted content to OpenAI.
5. **Modify Structure**: This is the crucial part for updating. You'll need to insert the OpenAI response back into the parsed structure. This might involve:
   - Creating new nodes/tokens representing the OpenAI response (e.g., as a new paragraph or blockquote).
   - Inserting these new nodes into the AST/token list at the correct position (e.g., after the original panel content).
6. **Render/Serialize**: Convert the modified structure back into a Markdown string.
7. **Write**: Save this new Markdown string to a file (either overwriting the original or creating a new one).

Using a library that properly understands Markdown structure will be more reliable than regex, especially if your Markdown files have complex or nested structures. The initial learning curve for a library's AST or object model will likely pay off in terms of robustness. I recommend starting with the documentation for Mistletoe or markdown-toolkit to see if their APIs for AST traversal and Markdown generation fit your needs.

## Working with Mistletoe

That's a great choice because it's CommonMark compliant and, importantly, offers a Markdown renderer, which will be essential for updating your file.

Your first worry is a good one: "How do I ensure the Markdown is formatted properly to work with Mistletoe?"

Here's the breakdown:

### Mistletoe and CommonMark Compliance

- Mistletoe is designed to parse Markdown that follows the CommonMark specification. CommonMark is an attempt to create a standard, unambiguous specification for Markdown.
- This means if your Markdown uses standard syntax for headings, paragraphs, lists, bold, italics, code blocks, links, etc., as defined by CommonMark, Mistletoe will understand it and parse it into a predictable Abstract Syntax Tree (AST).
- The good news is that your provided chapter_01_draft.md file appears to use very standard Markdown features. Elements like:

```markdown
# Chapter Title (H1 Heading)

## Panel 1: Why Traditional Metrics Fail (H2 Heading)

**Bold Text** (Strong emphasis)

- List item or 1. List item (Lists)
--- (Horizontal Rule)
```

Regular paragraphs of text. Are all standard Markdown and will be parsed correctly by Mistletoe.

### What "Properly Formatted" Means for Your Goal

- **Mistletoe's Perspective**: Mistletoe will correctly parse any valid CommonMark. If there are slight deviations that are still generally accepted Markdown, it will often make a reasonable interpretation.
- **Your Script's Perspective**: The most crucial aspect for your script to work correctly is the consistency of the "Panel" section identifiers. As long as your panels always start with a clear and consistent Markdown pattern (like ## Panel X: ...), your Python code will be able to find them within the AST Mistletoe produces.
- Minor Markdown formatting quirks elsewhere in the document are less likely to break Mistletoe's parsing of the overall document, but extreme inconsistencies could make the resulting AST harder for your script to navigate logically.

### Ensuring Your Markdown Works Well

- **Adhere to CommonMark**: Try to follow CommonMark guidelines when writing your Markdown. This is generally good practice anyway.
- **Consistency is Key**: As mentioned, ensure the structure you care about (the "Panel" headings) is used consistently across all your files.
- **Visual Inspection**: Your chapter_01_draft.md looks well-structured. Lines are distinct, headings are clear. This is usually a good sign.
- **Avoid Ambiguity**: Common areas where Markdown can become ambiguous (though CommonMark tries to resolve these) include nested lists with mixed indentation, or complex inline HTML. Your current example doesn't show these complexities in the panel structure itself.
- **Markdown Linters** (Optional but good practice): For a larger project with many files or collaborators, you might consider using a Markdown linter like markdownlint (available as a command-line tool or editor extension). Linters can check your Markdown against CommonMark rules (and other style preferences) and warn you about potential issues or inconsistencies. This is more about maintaining quality and consistency than a strict requirement for Mistletoe to function, but it helps ensure the Markdown is unambiguous.

### Mistletoe's Robustness

- Mistletoe is built to handle valid Markdown. It's unlikely to outright fail or crash unless the Markdown is severely broken in a way that makes it unparseable (e.g., unclosed constructs in a way that fundamentally breaks the document structure).
- The main "worry" isn't typically about Mistletoe failing but about how it interprets Markdown that might be ambiguous or not strictly CommonMark-compliant. However, for standard structures like headings and paragraphs, it's very reliable.

In summary for your chapter_01_draft.md: The way your "Panel" sections are defined (## Panel X: Some Title) is standard Markdown for a Level 2 Heading. Mistletoe will have no trouble parsing these as heading objects in its AST. Your primary task will be to write Python code that iterates through the AST, identifies these specific heading objects, and then captures the subsequent content.

## Review of Loading and Parsing Functionality

Let's generate some Python code using Mistletoe to load, parse, and then review the basic structure of your Markdown file. This will help you see how Mistletoe interprets your document and how we can start identifying those "Panel" sections.

First, you'll need to install Mistletoe. A commonly used and often updated fork is mistletoe-ebp. You can install it using pip:

```bash
pip install mistletoe-ebp
```

If you prefer the original, you can use `pip install mistletoe`. For this example, mistletoe-ebp is a good choice.

Here's the Python code:

```python
from mistletoe import Document
from mistletoe.ast_renderer import ASTRenderer # For a detailed AST view
from mistletoe.block_token import Heading, Paragraph, List, BlockCode, Quote, Table, ThematicBreak
from mistletoe.span_token import RawText, LineBreak, Emphasis, Strong, Link, Image, AutoLink

def review_markdown_parsing(file_path):
    """
    Loads a Markdown file, parses it with Mistletoe, and prints a review
    of the parsed structure, highlighting Panel sections.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as fin:
            markdown_content = fin.read()
        print(f"Successfully loaded '{file_path}'.\n")
    except FileNotFoundError:
        print(f"Error: File not found at '{file_path}'")
        return
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    print("--- Parsing with Mistletoe ---")
    doc = Document(markdown_content)
    print("Successfully parsed the document.\n")

    print("--- Document Structure Review (Top-Level Blocks) ---")
    for i, block in enumerate(doc.children):
        block_type = type(block).__name__
        print(f"\nBlock {i+1}: Type = {block_type}")

        if isinstance(block, Heading):
            # To get the text of a heading, we need to combine its children (span tokens)
            heading_text = ""
            for span_child in block.children:
                if hasattr(span_child, 'content'): # e.g., RawText
                    heading_text += span_child.content
                # Could add more checks for other span tokens like Emphasis, etc.
                # if you expect them within your panel titles
            print(f"  Level: {block.level}")
            print(f"  Text: '{heading_text.strip()}'")
            if heading_text.strip().startswith("Panel "):
                print(f"  >>> This is a 'Panel' heading!")
        elif isinstance(block, Paragraph):
            # Similar to heading, get text from children span tokens
            para_text = ""
            for span_child in block.children:
                if hasattr(span_child, 'content'):
                    para_text += span_child.content
            print(f"  Content Snippet: '{para_text.strip()[:100]}...'") # Print a snippet
        elif isinstance(block, List):
            print(f"  Start Number (if ordered): {block.start}")
            print(f"  List Items: {len(block.children)}")
            # You could iterate through block.children (which are ListItems) for more detail
        elif isinstance(block, BlockCode):
            print(f"  Language: '{block.language}'")
            print(f"  Content Snippet: '{block.children[0].content.strip()[:100]}...'")
        elif isinstance(block, ThematicBreak):
            print("  (Horizontal Rule ---)")
        elif isinstance(block, Quote):
            print("  (Blockquote)")
            # block.children would contain the paragraphs/blocks inside the quote
        else:
            print("  (Other block type, content not fully displayed here for brevity)")

    print("\n--- Detailed AST (First few top-level nodes) ---")
    # The ASTRenderer gives a very detailed, nested view.
    # This can be overwhelming for the whole document, so let's limit it.
    # You can render the whole 'doc' if you want a complete AST dump.
    renderer = ASTRenderer()
    for i, block in enumerate(doc.children):
        if i < 5: # Print AST for the first 5 blocks
            print(f"\nAST for Block {i+1}:")
            print(renderer.render(block))
        else:
            break
    if len(doc.children) > 5:
        print("\n(AST review limited to the first 5 top-level blocks for brevity)")

    print("\n--- Review Complete ---")

# --- Main Execution ---

if __name__ == "__main__":
    # Make sure 'chapter_01_draft.md' is in the same directory as the script,
    # or provide the full path to the file.
    markdown_file = 'chapter_01_draft.md'
    review_markdown_parsing(markdown_file)
```

### How to Use and Understand the Output

- **Save the Code**: Save the Python code above as a .py file (e.g., parse_reviewer.py) in the same directory as your chapter_01_draft.md file.
- **Run from Terminal**: Open your terminal or command prompt, navigate to that directory, and run the script:

```bash
python parse_reviewer.py
```

### Output Explanation

- **File Loading**: Confirms if the file was loaded.
- **Parsing Confirmation**: Confirms Mistletoe parsed it.
- **Document Structure Review**: This section iterates through the top-level blocks of your Markdown document (paragraphs, headings, lists, etc.).
  - For each block, it prints its type (e.g., Heading, Paragraph).
  - If it's a Heading, it extracts and prints the heading text and its level (e.g., H1, H2). It specifically flags headings that start with "Panel ".
  - For Paragraphs and BlockCode, it prints a snippet of their content.
- **Detailed AST**: This section uses ASTRenderer to print a more technical, tree-like representation of the first few blocks. This shows you the hierarchy of tokens (e.g., a Heading block containing RawText span tokens). This can be very helpful for understanding how to access specific pieces of content later.
- **"Panel" Heading Identification**: The script explicitly looks for headings that start with "Panel " and prints a message. This is the first step towards isolating those sections.

This script should give you a good initial insight into how Mistletoe "sees" your Markdown file. From here, the next step would be to refine the logic to not just identify the "Panel" headings but also to collect all the content that belongs to each panel section (i.e., all subsequent blocks until the next "Panel" heading or the end of the document).

## Extracting Panel Sections from a Document

Let's modify the approach to extract the full content for each "Panel" section from your Markdown document, "chapter_01_draft.md", using Mistletoe. Each section will start with the "Panel X" heading and include all subsequent content until the next "Panel X" heading or the end of the document.

We'll parse the document, identify the start of each panel, collect all associated blocks, and then render these collected blocks back into a Markdown string.

First, ensure you have mistletoe installed in your Anaconda environment (as discussed, preferably from conda-forge):

```bash
# In your activated conda environment (e.g., markdown_env)
conda install -c conda-forge mistletoe
```

Here's the Python code:

```python
from mistletoe import Document
from mistletoe.block_token import Heading
from mistletoe.markdown_renderer import MarkdownRenderer

def get_heading_text(heading_node):
    """
    Extracts the plain text from a Mistletoe Heading node.
    """
    text = ""
    if hasattr(heading_node, 'children'):
        for child in heading_node.children:
            if hasattr(child, 'content'): # Typically RawText
                text += child.content
    return text.strip()

def extract_panel_sections(file_path):
    """
    Loads a Markdown file, parses it with Mistletoe, extracts sections
    starting with "## Panel X:", and prints their Markdown content.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as fin:
            markdown_content = fin.read()
        print(f"Successfully loaded '{file_path}'.\n")
    except FileNotFoundError:
        print(f"Error: File not found at '{file_path}'")
        return
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    print("--- Parsing with Mistletoe ---")
    doc = Document(markdown_content)
    print("Successfully parsed the document.\n")

    panel_sections = []
    current_panel_blocks = []
    current_panel_title = None

    # Iterate through all top-level blocks in the document
    for i, block in enumerate(doc.children):
        is_panel_heading = False
        panel_heading_text = ""

        if isinstance(block, Heading) and block.level == 2:
            heading_text = get_heading_text(block)
            if heading_text.startswith("Panel "):
                is_panel_heading = True
                panel_heading_text = f"## {heading_text}" # Reconstruct the full heading markdown

        if is_panel_heading:
            # If we were collecting a previous panel, store it
            if current_panel_title and current_panel_blocks:
                panel_sections.append({
                    "title": current_panel_title,
                    "blocks": current_panel_blocks
                })
            
            # Start a new panel
            current_panel_title = panel_heading_text
            current_panel_blocks = [block] # Start with the heading itself
        elif current_panel_title:
            # If we are already inside a panel, add the current block to it
            current_panel_blocks.append(block)

    # Add the last collected panel after the loop finishes
    if current_panel_title and current_panel_blocks:
        panel_sections.append({
            "title": current_panel_title,
            "blocks": current_panel_blocks
        })

    if not panel_sections:
        print("No 'Panel X:' sections found in the document.")
        return

    print(f"\n--- Extracted Panel Sections ({len(panel_sections)} found) ---")
    
    # Initialize the renderer 
    renderer = MarkdownRenderer()

    for i, section in enumerate(panel_sections):
        print(f"\n--- Panel Extracted #{i+1} ---")
        print(f"Title: {section['title']}")
        
        # Create a temporary Document to render the list of blocks
        temp_doc = Document('')
        temp_doc.children = section['blocks'] # Assign the already parsed blocks
        
        # Now render the temporary document which contains only the panel's blocks
        panel_markdown_content = renderer.render(temp_doc)
        
        print("Content:")
        # The renderer might add an extra newline at the end, strip() can clean it up
        print(panel_markdown_content.strip())
        print("--- End of Panel ---")
        if i < len(panel_sections) - 1: # Add a separator for readability
            print("\n=====================================\n")

# --- Main Execution ---

if __name__ == "__main__":
    markdown_file = 'chapter_01_draft.md' # Ensure this file is accessible
    extract_panel_sections(markdown_file)
```

### Issues with Render Tokens

You may encounter issues with the render_tokens method that doesn't exist in some versions of Mistletoe. In this case, the corrected approach is to create a temporary Document and assign its children property directly.

When working with mistletoe in Anaconda with Python 3.12, remember to:

1. Create a dedicated conda environment: `conda create --name markdown_env python=3.12`
2. Activate it: `conda activate markdown_env`
3. Install Mistletoe using conda: `conda install -c conda-forge mistletoe`
4. Run your Python script from within this activated environment.

This approach provides a clean, isolated, and robust environment for your project using Anaconda's strengths in package and environment management.
