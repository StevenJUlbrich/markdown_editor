# **Step-by-Step LLM-Driven Panel Processing Pipeline**

## **High-Level Steps**

1. **Load Markdown Source**

   * (Single file/panel, all panels, or all files in directory)
2. **Extract/Select Panel(s)**

   * Choose one, all, or batch as per tier.
3. **For Each Panel:**

   1. **Parse Panel Content** (scene, teaching narrative, common example, etc.)
   2. **Ask LLM: What is the Scene Theme?**
   3. **Ask LLM: What Roles are Required?**
   4. **Ask LLM: Rewrite Scene with Required Roles**
   5. **Ask LLM: Evaluate Scene Against Checklist**
   6. **If Fails: Loop Back and Rewrite Until Satisfied**
   7. **Enhance Characters (name, visual\_tags, etc. from JSON or LLM)**
   8. **Ask LLM: Generate Speech Bubbles for Scene**
   9. **Assemble JSON Output for Enhanced Panel**
4. **Save Enhanced JSON (single, batch, or per file as needed)**

---

## **Mermaid Flow Diagram**

```mermaid
flowchart TD
    subgraph Markdown Processing
        A1["Load Markdown File(s)"] --> A2["Extract Panels (PanelPydantic)"]
        A2 --> A3["Select/Parse Panel Sections"]
        A3 -->|Copy Core Fields| B1(ComicPanelImageSheet)
    end

    subgraph Scene Enhancement Workflow
        B1 --> B2["LLM: Analyze/Rewrite Scene"]
        B2 --> B3["LLM: Checklist Evaluation"]
        B3 -->|If fails, iterate| B2
        B3 --> B4["LLM: Enhance Characters & Roles"]
        B4 --> B5["LLM: Generate Speech Bubbles"]
        B5 -->|Store| B1
    end

    subgraph Versioned Enrichment & QA
        B1 --> C1["scene_enhancements (List)"]
        B1 --> C2["checklist_results (List)"]
        B1 --> C3["speech_bubbles (List)"]
    end

    B1 --> D1["Export Enhanced JSON"]
    D1 --> D2["Image Prompt Output"]
    D1 --> D3["QA/Review Reports"]
    D1 --> D4[(Optionally back to Markdown Exporter)]

```

---

## **Mermaid Sequence Diagram**

```mermaid
sequenceDiagram
    participant User/Orchestrator as CLI/Batch Process
    participant Loader as Markdown Loader
    participant Extractor as Panel Extractor
    participant PanelModel as ComicPanelImageSheet
    participant LLM as OpenAI API
    participant CharDB as Character JSON
    participant JSONer as Exporter

    User/Orchestrator->>Loader: Load markdown(s)
    Loader->>Extractor: Extract panels, parse sections
    Extractor->>PanelModel: Create/refresh ComicPanelImageSheet with core fields
    loop For each panel
        PanelModel->>LLM: Analyze/Rewrite Scene (LLM)
        LLM-->>PanelModel: Returns scene enhancement
        PanelModel->>LLM: Checklist evaluation
        LLM-->>PanelModel: Returns pass/fail & checklist
        alt Checklist fails
            PanelModel->>LLM: Rewrite with fixes (repeat as needed)
        end
        PanelModel->>CharDB: Pull character details (or via LLM)
        CharDB-->>PanelModel: Return character data
        PanelModel->>LLM: Generate speech bubbles for scene
        LLM-->>PanelModel: Return speech bubbles JSON
        PanelModel->>PanelModel: Store enhancement, speech, checklist
    end
    PanelModel->>JSONer: Export Enhanced JSON, Image Prompt, etc.
    JSONer-->>User/Orchestrator: Output file(s)

```

## **Class/Data Structure Diagram (UML-style for Pydantic Upgrade Reference)**

```mermaid
classDiagram
    class ComicPanelImageSheet {
        +str panel_id
        +str scene_description_original
        +str teaching_narrative_original
        +str common_example_original
        +list~SceneEnhancement~ scene_enhancements
        +list~SpeechBubble~ speech_bubbles
        +list~ChecklistResult~ checklist_results
        +dict processing_metadata
        +dict image_prompt_json
    }

    class SceneEnhancement {
        +str version_id
        +str scene_text
        +dict llm_metadata
        +ChecklistResult checklist
        +dict image_prompt_json
    }

    class SpeechBubble {
        +str character_name
        +str role
        +str speech
        +str interface
    }

    class ChecklistResult {
        +bool teaching_narrative_satisfied
        +bool common_example_aligned
        +bool roles_used_effectively
        +str missing_elements
        +str reviewer_notes
        +str timestamp
    }

    ComicPanelImageSheet "1" o-- "*" SceneEnhancement
    ComicPanelImageSheet "1" o-- "*" SpeechBubble
    ComicPanelImageSheet "1" o-- "*" ChecklistResult
    SceneEnhancement "1" o-- "1" ChecklistResult
```

---

## **Three-Tier Processing Support**

* **Tier 1:** Select a single panel to process (ideal for interactive or debugging).
* **Tier 2:** Process all panels in one markdown file (batch, for whole chapters).
* **Tier 3:** Process all markdown files in a directory (mass batch, for full curriculum builds).

**The diagrams above remain accurate—your orchestration just wraps more panels or files per tier.**

---

## **How This Will Help You**

* **Visual Traceability:** See every step and LLM call—perfect for debugging and QA.
* **Flexible Orchestration:** Each box in the diagram can be mapped to a function/method, pipeline stage, or even GUI step.
* **Easy Expansion:** Add more LLM steps, pre/post-processing, or QA logic as you iterate.
* **No Local Bias:** LLM does all high-order creative work; code only orchestrates and glues.

---

## **If/When You Want a GUI**

* The flow and sequence here could be the backend for a Tkinter or PyQt GUI.
* GUI would just add “panel/file/directory” selectors and progress/status visualization on top of this pipeline.
* You’ll get exactly the same output, just with more interactivity for manual review or edit-in-the-loop.

---

## **Anything Else?**

Would you like:

* Example code scaffolding (with stubs for each LLM call)?
* A YAML/JSON config format for these steps/prompts?
* A worked demo with a real markdown file?

**Just tell me your preferred next step—this design will scale with you!**
