Below is an **MVC-styled** depiction of the *“Save Document”* action exposed by **`src/main.py`**.
As with the prior commands, you get both a **flowchart** (control flow) and a **sequence diagram** (runtime interactions).
Module names mirror the current repository layout in `dir_report_may_19_2025.txt` .

---

### 1 ️⃣ Flow-of-Control (Flowchart)

```mermaid
flowchart TD
    %% ───────── CONTROLLER LAYER ─────────
    subgraph Controller
        A[main.py<br/>CLI entry-point]
        B["AppController<br/>-- save_document(path) --"]
    end

    %% ───────── VIEW / SERVICE LAYER ─────────
    subgraph View & Helpers
        C["DocumentValidator<br/>(optional re-validate)"]
        D["PanelMarkdownExporter<br/>(serialise ➜ markdown)"]
        E["MarkdownFileManager<br/>(write file)"]
        F["DiffUtils<br/>(show diff / backup)<br/>(optional)"]
    end

    %% ───────── MODEL LAYER ─────────
    subgraph Model
        G["DocumentModel<br/>(in-memory)"]
    end

    %% ───────── PRIMARY FLOW ─────────
    A -->|parse args| B
    B --> G           
    G --> C
    C -->|valid✔| D
    D --> E
    E -->|file saved| F
    F -->|"diff / backup (opt)"| B
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
    participant Model as DocumentModel
    participant Val as DocumentValidator
    participant Exp as PanelMarkdownExporter
    participant IO as MarkdownFileManager
    participant Diff as DiffUtils

    User->>Main: python main.py --save chapter.md
    Main->>Ctrl: instantiate & delegate
    Note over Ctrl: DocumentModel already\npopulated from prior ops
    Ctrl-->>Model: get_current_state()
    Ctrl->>Val: validate(model)
    Val-->>Ctrl: OK
    Ctrl->>Exp: serialize(model)
    Exp-->>Ctrl: markdown_text
    Ctrl->>IO: write(chapter.md, markdown_text)
    IO-->>Ctrl: write_complete
    Ctrl->>Diff: show_diff(chapter.md, markdown_text) opt
    Diff-->>Ctrl: diff_summary
    Ctrl-->>Main: success / diff summary
    Main-->>User: “Document saved ✓” / exit 0
```

---

### Usage & Extension Tips

| Aspect                     | Guidance                                                                                                                                                |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Rendering**              | Paste either diagram into any Mermaid-enabled editor (or your Kroki Docker container) to obtain SVG/PNG artifacts.                                      |
| **Validation Toggle**      | If you add a `--skip-validation` flag, simply branch from **`AppController`** directly to **`PanelMarkdownExporter`** when the flag is set.             |
| **Back-ups / Revisioning** | For automatic versioning, branch from **`MarkdownFileManager`** to a new **`RevisionStore`** service before the final write.                            |
| **Dry-Run**                | Route `markdown_text` to `stdout` (or a temp file) instead of **`MarkdownFileManager.write`** when users pass `--dry-run`, avoiding filesystem changes. |

These visuals round out the core CLI flows.
Let me know if you’d like similar diagrams for any additional commands, or if you need sequence details expanded to include OpenAI enrichment calls, diff previews, or error-handling branches.
