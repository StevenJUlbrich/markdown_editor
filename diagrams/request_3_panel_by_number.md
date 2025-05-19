Below are **Mermaid-ready** diagrams for the **“Select Panel by Number”** command path that originates in **`src/main.py`**.
They follow the same MVC-centric style you requested earlier and use your current directory layout as the source of truth .

---

### 1 ️⃣  Flow-of-Control (Flowchart)

```mermaid
flowchart TD
    %% ────────── CONTROLLER LAYER ──────────
    subgraph Controller
        A[main.py<br/>CLI entry-point]
        B["AppController<br/>-- select_panel(n) --"]
    end

    %% ────────── VIEW / SERVICE LAYER ──────────
    subgraph View & Helpers
        C["MarkdownFileManager<br/>(load .md)"]
        D["MarkdownParser"]
        E["DocumentModelBuilder"]
        F["PanelSectionManager<br/>(locate Panel n)"]
        G["Formatter / Exporter<br/>(print / JSON)"]
    end

    %% ────────── MODEL LAYER ──────────
    subgraph Model
        H[DocumentModel<br/>↳ Panel objects]
    end

    %% ────────── PRIMARY FLOW ──────────
    A -->|parse args| B
    B --> C
    C --> D
    D --> E
    E --> H
    H --> F
    F --> G
    G -->|panel details| B
    B -->|stdout / CLI| A
```

---

### 2 ️⃣  Sequence-of-Interactions (Sequence Diagram)

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
    participant Out as CLI Formatter

    User->>Main: python main.py --panel 4 chapter.md
    Main->>Ctrl: instantiate & delegate
    Ctrl->>IO: read(chapter.md)
    IO-->>Ctrl: markdown_text
    Ctrl->>Parse: parse(markdown_text)
    Parse-->>Ctrl: token_stream
    Ctrl->>Build: build(token_stream)
    Build-->>Model: DocumentModel
    Ctrl-->>Sect: locate_panel(model, 4)
    Sect-->>Ctrl: Panel(id = 4, title, content…)
    Ctrl->>Out: format(panel)
    Out-->>Main: formatted output
    Main-->>User: panel details / exit 0
```

---

### Using These Diagrams

1. **Render** – Paste either block into any Mermaid-enabled viewer (or your Kroki container) to get SVG/PNG artifacts.
2. **Extend** – If selecting a panel triggers additional actions (e.g., opening an editor, exporting JSON), simply branch from **`PanelSectionManager`** to those services.
3. **Document** – Embedding the flowchart and sequence diagram in your repo (e.g., `docs/architecture.md`) helps new contributors quickly understand this specific control path.

Let me know if you need diagrams for any other sub-commands (such as **sync-images**, **generate-scene-json**, or **validate-doc**) and I’ll prepare matching MVC views.
