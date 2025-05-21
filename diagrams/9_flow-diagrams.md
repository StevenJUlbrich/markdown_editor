# Mermaid Diagrams for "Enhance Panel with Roles and Speech"

## Flow Diagram

```mermaid
flowchart TD
    subgraph Controller
        A[main.py<br/>Menu option 9]
        B["AppController<br/>enhance_panel_with_roles_and_speech()"]
    end

    subgraph View & Helpers
        C["Get panel from doc"]
        D["Extract panel markdown"]
        E["Create ComicPanelImageSheet"]
        F["Get role suggestions"]
        G["Create SceneEnhancer"]
        H["Generate speech bubbles"]
        I["Display results"]
    end

    subgraph Model
        J["Document Model<br/>(Panel)"]
        K[CharacterRoleSuggester]
        L[SceneEnhancer]
        M["OpenAI Service<br/>(generate_speech_for_characters)"]
    end

    A -->|Select option 9| A1["Get panel number"]
    A1 --> B
    B --> C
    C --> D
    D --> E
    E --> F
    F --> G
    G --> H
    H --> I
    I --> A

    C -.-> J
    D -.-> J
    F -.-> K
    G -.-> L
    H -.-> M
```

## Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant Main as main.py
    participant AC as AppController
    participant MD as MarkdownDocument
    participant CRM as ComicPanelMapping
    participant CRS as CharacterRoleSuggester
    participant SE as SceneEnhancer
    participant API as OpenAIService

    User->>Main: Select option 9
    Main->>User: Prompt for panel number
    User->>Main: Enter panel number
    Main->>AC: enhance_panel_with_roles_and_speech(panel_num)
    AC->>MD: get_panel_by_number(panel_num)
    MD-->>AC: panel
    AC->>MD: get_panel_markdown_by_number(panel_num)
    MD-->>AC: panel_markdown
    AC->>CRM: map_to_comic_panel_image_sheet(panel_markdown)
    CRM-->>AC: panel_sheet
    AC->>CRS: suggest_character_roles_in_file(doc.filepath)
    CRS->>MD: Extract sections & content
    MD-->>CRS: scene & teaching text
    CRS->>API: Request character roles
    API-->>CRS: character roles
    CRS-->>AC: roles_dict
    AC->>AC: Extract roles for panel
    AC->>SE: Create SceneEnhancer instance
    AC->>SE: generate_speech_bubbles_for_roles(panel_sheet, roles)
    SE->>API: generate_speech_for_characters()
    API-->>SE: speech_data
    SE->>SE: Create SpeechBubble objects
    SE-->>AC: updated_panel_sheet
    AC-->>Main: panel_sheet with speech
    Main->>User: Display speech bubbles
```

These diagrams illustrate the flow and interactions for the "Enhance Panel with Roles and Speech" feature (option 9). The process involves:

1. Getting the panel markdown from the document model
2. Creating a ComicPanelImageSheet from the markdown
3. Getting character role suggestions using the CharacterRoleSuggester
4. Instantiating a SceneEnhancer to generate speech bubbles
5. Using OpenAI to generate speech content for the characters
6. Returning the enhanced panel with speech bubbles to display to the user

The implementation properly follows object-oriented principles by creating and using class instances for each service.
