Below is a **side-by-side reality check** that maps your desired 14-step flow to what the current
`batch_processing/comic_panel_batch_processor.py` actually does. I dug through the file so you don’t have to read 5 kB of mixed logic.

| #      | Your intended step                                                                | What the code does today                                                                     | Gap / Risk                                                                                 |
| ------ | --------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| **1**  | Load the Markdown                                                                 | ✅ `create_panel_sheets_from_markdown()` is the entry point used by `process_markdown_file()` | —                                                                                          |
| **2**  | Retrieve all scene material                                                       | ✅ Each `ComicPanelImageSheet` already carries `scene_description_original`                   | —                                                                                          |
| **3**  | LLM → classify theme                                                              | ✅ `scene_theme_analysis` prompt; result saved in local var `scene_theme`                     | Stored only in `scene_enhancement.llm_metadata`, **not** bubbled up to chapter-level stats |
| **4**  | Evaluate *all* scenes                                                             | ⚠️ Processor loops panels **sequentially** inside one Python process                         | No batching / concurrency → slow + rate-limit risk                                         |
| **5**  | Rewrite scene to new tone and inject required roles                               | ✅ `scene_rewrite` prompt uses `required_roles` placeholder                                   | Prompt is fragile: if role list empty the LLM free-styles                                  |
| **6**  | Verify required roles exist or invent                                             | ⚠️ `role_extraction` just returns roles; no check vs character DB                            | Missing PL validation logic                                                                |
| **7**  | Resolve character names from `character_base_list.json`                           | ✅ `character_details = find_matches(character_db, roles)`                                    | BUT if no match, silently invents a name → drift                                           |
| **8**  | Generate image prompt (tone + teaching narrative, no duplicate of common example) | ✅ `image_prompt_generation` template tries this                                              | Needs stricter “don’t copy example” guard in prompt                                        |
| **9**  | Ask for speech bubbles                                                            | ✅ `speech_bubble_generation` prompt                                                          | Hard-caps at 3 bubbles – configurable?                                                     |
| **10** | Save into `ComicPanelImageSheet` extension                                        | ✅ Instantiates `SceneEnhancement` and appends to `comic_panel.scene_enhancements`            | Enhancement object omits `image_prompt` (!)                                                |
| **11** | Repeat for each panel                                                             | ✅ `process_markdown_file()` iterates                                                         | —                                                                                          |
| **12** | Run checklist QA                                                                  | ✅ Calls `checklist_prompt`; stores result in `ChecklistResult`                               | No blocking: even “FAIL” panels keep moving                                                |
| **13** | Write image JSON per chapter                                                      | ✅ `export_chapter_to_json()` at end of file                                                  | Schema undocumented; field order varies per run                                            |
| **14** | Insert H4 markdown reference                                                      | ❌ Not implemented (TODO comment)                                                             | Requires parser round-trip update                                                          |

### What this means

* **Major wins** – theme tagging, role extraction, rewrite, speech bubbles, JSON export all exist.
* **Primary gaps** – validation logic (steps 6 & 12), deterministic character matching, missing markdown insertion, and overall **speed** (no async batching).

---

## Suggested refactor roadmap

| Phase            | Goal                  | High-impact tasks                                                                                                                                                                                                                                |
| ---------------- | --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **A (1-2 days)** | *Stability & tracing* | • Wrap every OpenAI call in a decorator that stores `<panel_id, prompt_name, response, request_id>` into a SQLite DB <br>• Bubble `scene_theme` up to chapter summary so later distribution check is trivial                                     |
| **B (2-3 days)** | *Validation layer*    | • Create `RoleValidator` (pure-Python): checks role exists in DB; if not, raise `UnknownRoleError` so we can generate or reject <br>• Harden checklist: if any `blocker == True`, mark panel “FAILED” and skip downstream steps unless `--force` |
| **C (1 day)**    | *Speed*               | • Convert `process_panel` to an `async def` coroutine <br>• Use `asyncio.gather` with a semaphore equal to your OpenAI RPM limit                                                                                                                 |
| **D (1 day)**    | *Markdown round-trip* | • Add `MarkdownDocument.insert_image_h4(panel_number, file_name)` and call it after JSON export                                                                                                                                                  |
| **E (ongoing)**  | *Prompt hardening*    | • Add a negative example to `image_prompt_generation` (“If the Common Example is X, do **not** restate X…”) <br>• Promote prompt templates to versioned YAML with unit tests                                                                     |

---

## Concrete next step I can take for you

1. **Refactor `process_panel` into smaller, testable functions** (`classify_theme`, `extract_roles`, `rewrite_scene`, …) *and* add an `async` orchestrator.
2. **Write a pytest suite** with fake OpenAI responses to exercise the validation layer.
3. **Implement the markdown H4 insertion** so your docs link straight to generated images.

Let me know which of these (or something else) you’d like first, and I’ll jump straight into code (or spec) updates.
