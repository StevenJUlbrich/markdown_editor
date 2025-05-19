Below is an **MVC-aligned** map of the *“Update Named Section in Panel”* command exposed by **`src/main.py`**.
As before, you get a **flowchart** and a **sequence diagram** you can paste straight into any Mermaid-enabled renderer (or your Kroki container).
Module names match the folders and files listed in `dir_report_may_19_2025.txt` .

---

### 1 ️⃣ Flow-of-Control (Flowchart)

```mermaid
flowchart TD
    %% ───────── CONTROLLER LAYER ─────────
    subgraph Controller
        A[main.py<br/>CLI entry-point]
        B["AppController<br/>-- update_section(panel_n, h3_title, new_md) --"]
    end

    %% ───────── VIEW / SERVICE LAYER ─────────
    subgraph View & Helpers
        C["MarkdownFileManager<br/>(read .md)"]
        D["MarkdownParser"]
        E["DocumentModelBuilder"]
        F["PanelSectionManager<br/>(locate panel n)"]
        G["NamedSectionUpdater<br/>(replace H3 content)"]
        H["DocumentValidator<br/>(optional re-validate)"]
        I["PanelMarkdownExporter<br/>(write updated .md)"]
    end

    %% ───────── MODEL LAYER ─────────
    subgraph Model
        J["DocumentModel<br/>↳ Panel ↳ Section objects"]
        K["SectionTitles<br/>(normalise H3 names)"]
    end

    %% ───────── PRIMARY FLOW ─────────
    A -->|parse CLI args| B
    B --> C
    C --> D
    D --> E
    E --> J
    J --> F
    F -->|Panel n| G
    G --> K
    K --> G
    G --> J
    J --> H
    H --> I
    I -->|save file| B
    B -->|stdout / CLI| A
```

---

### 2 ️⃣ Sequence-of-Interactions (Runtime View)

```mermaid
sequenceDiagram
    autonumber
    participant User
    participant Main as main.py
    participant Ctrl as AppController
    participant IO as MarkdownFileManager
    participant Parse as MarkdownParser
    participant Build as DocumentModelBuilder
    participant Model as DocumentModel
    participant Sect as PanelSectionManager
    participant Upd as NamedSectionUpdater
    participant Titles as SectionTitles
    participant Val as DocumentValidator
    participant Exp as PanelMarkdownExporter

    User->>Main: python main.py --panel 4 --section "Teaching Narrative" --update new.md chapter.md
    Main->>Ctrl: instantiate & delegate
    Ctrl->>IO: read(chapter.md)
    IO-->>Ctrl: markdown_text
    Ctrl->>Parse: parse(markdown_text)
    Parse-->>Ctrl: token_stream
    Ctrl->>Build: build(token_stream)
    Build-->>Model: DocumentModel
    Ctrl-->>Sect: locate_panel(model, 4)
    Sect-->>Ctrl: Panel(id=4,…)
    Ctrl->>Upd: replace_section(panel,"Teaching Narrative", new_md)
    Upd->>Titles: canonicalise("Teaching Narrative")
    Titles-->>Upd: canonical
    Upd-->>Ctrl: Panel updated
    Ctrl->>Val: validate(model)
    Val-->>Ctrl: OK
    Ctrl->>Exp: export(model)
    Exp-->>Main: write_success
    Main-->>User: “Section updated ✓” / exit 0
```

---

### Usage & Next Steps

* **Render** – Copy either diagram into your Mermaid viewer or run it through your Kroki Docker service to produce SVG/PNG assets for docs or slide decks.
* **Extensibility** –

  * If you add content-enrichment via OpenAI, branch from **`NamedSectionUpdater`** to **`openai_service`** before the write-back step.
  * For dry-run or diff-only modes, branch from **`PanelMarkdownExporter`** to **`diff_utils`** rather than writing to disk.
* **Documentation** – Insert these diagrams into an architecture guide (e.g., `docs/cli_flows.md`) so contributors instantly see how updates propagate through the MVC layers.

Let me know if you’d like comparable diagrams for other commands—*validate-doc*, *sync-images*, *export-json*, etc.—and I’ll whip them up in the same style.
