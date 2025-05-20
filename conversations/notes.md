        elif choice == "8":
            if not document_loaded:
                print("Load and enrich a document first.")
                continue
            prompts_path = input("Enter LLM prompts YAML path: ").strip()
            characters_path = input("Enter character base list JSON path: ").strip()
            controller.load_llm_prompts(prompts_path)
            controller.load_character_base(characters_path)
            enriched = controller.enrich_all_panels()
            out_path = input("Enter output JSON file path: ").strip()
            controller.save_enriched_panels(out_path, enriched)