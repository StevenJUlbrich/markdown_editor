# Operation: Show Named Sections

## Command: `python main.py --panel 4 --show-sections chapter.md`

### 1 ️⃣ Flow-of-Control (Flowchart)

```mermaid
flowchart TD
    %% ───────── CONTROLLER LAYER ─────────
    subgraph Controller
        A[main.py<br/>CLI entry-point]
        B["AppController<br/>-- show_named_sections(panel_n) --"]
    end

    %% ───────── VIEW / SERVICE LAYER ─────────
    subgraph View & Helpers
        C["MarkdownFileManager<br/>(load .md)"]
        D["MarkdownParser"]
        E["DocumentModelBuilder"]
        F["PanelSectionManager<br/>(locate Panel n)"]
        G["NamedSectionExtractor<br/>(collect H3 titles)"]
        H["Formatter / Exporter<br/>(print list / JSON)"]
    end

    %% ───────── MODEL LAYER ─────────
    subgraph Model
        I["DocumentModel<br/>↳ Panel ↳ Section objects"]
        J["SectionTitles<br/>(normalise names)"]
    end

    %% ───────── PRIMARY FLOW ─────────
    A -->|parse args| B
    B --> C
    C --> D
    D --> E
    E --> I
    I --> F
    F -->|Panel n| G
    G --> J
    J --> G
    G --> H
    H -->|named-section list| B
    B -->|stdout / CLI| A
```

---

### 2 ️⃣ Sequence-of-Interactions (Sequence Diagram)

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
    participant SectMgr as PanelSectionManager
    participant NSE as NamedSectionExtractor
    participant Titles as SectionTitles
    participant Out as CLI Formatter

    User->>Main: python main.py --panel 4 --show-sections chapter.md
    Main->>Ctrl: instantiate & delegate
    Ctrl->>IO: read(chapter.md)
    IO-->>Ctrl: markdown_text
    Ctrl->>Parse: parse(markdown_text)
    Parse-->>Ctrl: token_stream
    Ctrl->>Build: build(token_stream)
    Build-->>Model: DocumentModel
    Ctrl-->>SectMgr: locate_panel(model, 4)
    SectMgr-->>Ctrl: Panel(id = 4,…)
    Ctrl->>NSE: extract_sections(panel)
    NSE->>Titles: normalise(H3 titles)
    Titles-->>NSE: canonical_names
    NSE-->>Ctrl: [“Scene Description”, “Teaching Narrative”, …]
    Ctrl->>Out: format(section_list)
    Out-->>Main: formatted output
    Main-->>User: printed list / exit 0
```

---

### How to Render & Extend

* **Render** – Paste either block into any Mermaid-enabled editor (or your Kroki instance) to obtain SVG/PNG assets.
* **Extend** – If you later add filters (e.g., “only empty sections”), branch from **`NamedSectionExtractor`** to the relevant filter service and from **`Formatter`** to a JSON/CSV exporter.
* **Document** – Drop these diagrams into `docs/architecture.md` (or similar) so new contributors can immediately visualise this control path.

Let me know if you’d like diagrams for any other sub-commands (e.g., **sync-images**, **validate-doc**) and I’ll generate matching MVC views.
