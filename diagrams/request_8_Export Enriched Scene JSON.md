Below are **Mermaid-compatible** diagrams for the **“Export Enriched Scene JSON”** command in **`src/main.py`**.
They follow the same MVC style as the earlier sets and reference the modules present in your repo (e.g. `scene_enhancer.py`, `chapter_scene_json_exporter.py`) .

---

### 1 ️⃣ Flow-of-Control (Flowchart)

```mermaid
flowchart TD
    %% ─────────── CONTROLLER LAYER ───────────
    subgraph Controller
        A[main.py<br/>CLI entry-point]
        B["AppController<br/>-- export_scene_json(src_md, out_json) --"]
    end

    %% ─────────── VIEW / SERVICE LAYER ───────────
    subgraph View & Helpers
        C["MarkdownFileManager<br/>(read .md)"]
        D["MarkdownParser"]
        E["DocumentModelBuilder"]
        F["SceneEnhancer<br/>(add AI enrichment)"]
        G["ChapterSceneJSONExporter<br/>(serialise ➜ JSON)"]
        H["MarkdownFileManager<br/>(write .json)"]
    end

    %% ─────────── MODEL LAYER ───────────
    subgraph Model
        I[DocumentModel<br/>↳ Panel ↳ Section]
    end

    %% ─────────── PRIMARY FLOW ───────────
    A -->|parse args| B
    B --> C
    C --> D
    D --> E
    E --> I
    I --> F
    F --> I     
    I --> G
    G --> H
    H -->|JSON file saved| B
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
    participant Enhance as SceneEnhancer
    participant Export as ChapterSceneJSONExporter
    participant IOw as MarkdownFileManager (write)

    User->>Main: python main.py --export-json chapter.md scene.json
    Main->>Ctrl: instantiate & delegate

    %% Load & parse markdown
    Ctrl->>IO: read(chapter.md)
    IO-->>Ctrl: markdown_text
    Ctrl->>Parse: parse(markdown_text)
    Parse-->>Ctrl: token_stream
    Ctrl->>Build: build(token_stream)
    Build-->>Model: DocumentModel

    %% Enrich scene descriptions (AI / templates)
    Ctrl->>Enhance: enrich(Model)
    Enhance-->>Model: enriched_model

    %% Export JSON
    Ctrl->>Export: to_json(enriched_model)
    Export-->>Ctrl: json_blob
    Ctrl->>IOw: write(scene.json, json_blob)
    IOw-->>Ctrl: write_complete

    %% Finish
    Ctrl-->>Main: success / file path
    Main-->>User: “scene.json exported ✓” / exit 0
```

---

### Implementation & Extension Tips

| Aspect                | Guidance                                                                                                                             |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| **AI Calls**          | `SceneEnhancer` typically leverages **`openai_service.py`**. Add retry logic or rate-limit handling there if you expect high volume. |
| **JSON Schema**       | Keep a version field inside the JSON output. Future changes to panel or character structures won’t break downstream consumers.       |
| **Output Location**   | Accept an optional `--out-dir` flag. Branch from **`AppController`** to adjust the target path before the final write.               |
| **Dry-Run / Preview** | If users pass `--dry-run`, route `json_blob` to `stdout` instead of calling **`MarkdownFileManager.write`**.                         |
| **Batch Mode**        | For folder-wide exports, loop the “Load → Enhance → Export” steps inside `AppController`, similar to the role-suggestion flow.       |

Copy either diagram into any Mermaid editor (or your Kroki Docker instance) to generate SVG/PNG artifacts for documentation or slide decks.

Need diagrams for additional commands or error-handling branches? Just let me know!
