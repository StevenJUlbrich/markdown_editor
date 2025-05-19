# Suggest Character Roles Only (all panels in a folder)

## Overview

Below are **Mermaid-ready** diagrams for the **“Suggest Character Roles Only (all panels in a folder)”** command exposed by **`src/main.py`**.
They follow the same MVC format you requested for earlier flows and use the modules shown in your repository listing .

---

### 1 ️⃣ Flow-of-Control (Flowchart)

```mermaid
flowchart TD
    %% ─────── CONTROLLER LAYER ───────
    subgraph Controller
        A[main.py<br/>CLI entry-point]
        B["AppController<br/>-- suggest_roles(folder) --"]
    end

    %% ─────── VIEW / SERVICE LAYER ───────
    subgraph View & Helpers
        C["MarkdownFileManager<br/>(scan & load *.md)"]
        D["MarkdownParser"]
        E["DocumentModelBuilder"]
        F["PanelSectionManager<br/>(enumerate H2 'Panel #')"]
        G["CharacterRoleSuggester<br/>(services/…)"]
        H["Formatter / Exporter<br/>(stdout / JSON)"]
    end

    %% ─────── MODEL LAYER ───────
    subgraph Model
        I[DocumentModel<br/>↳ Panel objects]
        J["CharacterProfiles<br/>(optional cache)"]
    end

    %% ─────── PRIMARY FLOW ───────
    A -->|parse args| B
    B --> C
    C --> D
    D --> E
    E --> I
    I --> F
    F --> G
    G --> J
    J --> G
    G --> H
    H -->|suggested roles list| B
    B -->|stdout / exit-code| A
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
    participant RoleSvc as CharacterRoleSuggester
    participant Prof as CharacterProfiles
    participant Out as CLI Formatter

    User->>Main: python main.py --suggest-roles ./chapters/
    Main->>Ctrl: instantiate & delegate

    Ctrl->>IO: list_files("./chapters/*.md")
    loop each markdown file
        Ctrl->>IO: read(file)
        IO-->>Ctrl: markdown_text
        Ctrl->>Parse: parse(markdown_text)
        Parse-->>Ctrl: token_stream
        Ctrl->>Build: build(token_stream)
        Build-->>Model: DocumentModel
        Ctrl-->>Sect: panels = enumerate_panels(model)
        Sect-->>Ctrl: [Panel1, Panel2, …]
        Ctrl->>RoleSvc: suggest_roles(panels)
        RoleSvc->>Prof: fetch_existing_profiles(opt)
        Prof-->>RoleSvc: profiles
        RoleSvc-->>Ctrl: {panel_id: [roles…]}
    end

    Ctrl->>Out: format_role_report(aggregated_roles)
    Out-->>Main: formatted summary
    Main-->>User: printed / JSON output ✓
```

---

### Implementation Notes & Extensions

| Aspect              | Guidance                                                                                                                                                                   |
| ------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Bulk Processing** | The loop in the sequence diagram emphasises batch scanning of every `.md` file in the folder.                                                                              |
| **Caching**         | If role suggestions depend on prior character profiles, **`CharacterProfiles`** can be injected before the call to **`CharacterRoleSuggester`** for context-aware results. |
| **Output Modes**    | Add a `--json` or `--csv` flag to route data from **`Formatter / Exporter`** to a file instead of stdout.                                                                  |
| **Parallelism**     | Large folders can be processed concurrently by branching from **`AppController`** into a worker pool before parsing each file.                                             |

Copy either block into a Mermaid-enabled viewer (or your Kroki instance) to generate SVG/PNG diagrams for documentation or slide decks.
Need similar diagrams for additional commands? Just let me know!
