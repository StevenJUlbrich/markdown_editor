# Request 1: Load Markdown File and Process

## Overview

This document describes the flow of control and sequence of interactions for loading a Markdown file, parsing it, validating its content, and exporting the processed data back to Markdown format. The system follows a Model-View-Controller (MVC) architecture, with components grouped into **Controller**, **Model**, and **View & Services**.

### 1 ️Flow-of-Control (Flowchart)

```mermaid
flowchart TD
    subgraph Controller
        A[main.py<br/>CLI entry-point]
        B[AppController]
    end

    subgraph Model
        G[DocumentModelBuilder]
        H[DocumentModel]
        I[SectionTitles / other POJOs]
    end

    subgraph View & Services
        J["MarkdownFileManager<br/>(I/O)"]
        K["MarkdownParser"]
        L["DocumentValidator"]
        M["Batch / Pipeline Services<br/>(comic_image_pipeline, …)"]
        N["PanelMarkdownExporter<br/>(writes MD back)"]
    end

    %% primary path
    A -->|parse args & config| B
    B --> J
    J -->|raw markdown| K
    K -->|token stream| G
    G -->|objects| H
    H --> L
    L -->|✔ valid| M
    M --> N
    N -->|updated .md file| B
    B -->|status| A
```

---

### 2 ️Sequence-of-Interactions (Sequence Diagram)

```mermaid
sequenceDiagram
    autonumber
    participant User
    participant Main as main.py
    participant Ctl as AppController
    participant IO as MarkdownFileManager
    participant Parser as MarkdownParser
    participant Builder as DocumentModelBuilder
    participant Val as DocumentValidator
    participant Pipe as Batch / Pipeline
    participant Exp as PanelMarkdownExporter

    User->>Main: invoke CLI with MD path
    Main->>Ctl: instantiate & pass CLI args
    Ctl->>IO: read(markdown_path)
    IO-->>Ctl: markdown_text
    Ctl->>Parser: parse(markdown_text)
    Parser-->>Ctl: tokens
    Ctl->>Builder: build(tokens)
    Builder-->>Ctl: DocumentModel
    Ctl->>Val: validate(DocumentModel)
    Val-->>Ctl: OK
    Ctl->>Pipe: process(DocumentModel)
    Pipe-->>Ctl: enriched_model
    Ctl->>Exp: export(enriched_model)
    Exp-->>Ctl: updated_markdown
    Ctl-->>Main: success message / exit code
    Main-->>User: “Processing complete”
```

---

### How to Use

* Paste either diagram into any Mermaid-enabled editor (or your existing **Kroki** Docker instance) to render PNG/SVG assets automatically.
* The MVC grouping can be expanded in future iterations—for example, you might split the **View** cluster into *Renderers* vs. *Report Generators* once those flows become distinct.
* When additional entry points appear in `main.py` (e.g. a **batch** flag that skips validation), you can replicate the same pattern and add diverging branches or alternate lifelines.

Let me know if you’d like a second set of diagrams for any other paths that `main.py` can launch (e.g. *“Generate scene JSON”* or *“Sync image metadata”*) and I’ll extend the models accordingly.
