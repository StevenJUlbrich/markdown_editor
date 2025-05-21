# Scene Theme Analysis: Detailed Implementation Guide

## Overview

This document outlines a comprehensive implementation plan for the Scene Theme Analysis component within the SRE graphic novel enhancement project. The implementation follows an MVC architecture pattern and focuses on analyzing scene types in markdown files, outputting structured results for review and further processing.

## 1. MVC Architecture

### Model
- `SceneModel`: Represents parsed markdown scenes with metadata
- `ThemeAnalysisModel`: Stores theme analysis results and metadata
- `ChapterModel`: Represents a collection of scenes with chapter-level insights

### View
- `AnalysisOutputView`: Generates structured output files (JSON/YAML/TEXT)
- `ConsoleProgressView`: Displays analysis progress in the console

### Controller
- `FileReaderController`: Handles file/folder reading operations
- `SceneExtractionController`: Extracts scenes from markdown
- `ThemeAnalysisController`: Orchestrates the analysis process
- `OutputController`: Manages results output

## 2. Input/Output Specifications

### Input
- Individual markdown file OR
- Directory of markdown files
- Optional configuration file for analysis parameters

### Output
- Primary: Structured file (JSON/YAML) with detailed scene analysis
- Secondary: Console output showing progress and summary statistics
- Optional: HTML report for visual review of analysis results

## 3. Detailed Component Specifications

### 3.1. Models

#### SceneModel
```python
class SceneModel:
    """Represents a single scene extracted from markdown."""
    
    def __init__(self, scene_id, panel_number, scene_text, teaching_narrative, common_example):
        self.scene_id = scene_id  # Unique identifier (e.g., "chapter_01_panel_03")
        self.panel_number = panel_number
        self.scene_text = scene_text
        self.teaching_narrative = teaching_narrative
        self.common_example = common_example
        self.source_file = None  # Path to source file
        self.line_range = None  # Line range in source file
```

#### ThemeAnalysisModel
```python
class ThemeAnalysisModel:
    """Stores theme analysis result for a scene."""
    
    def __init__(self, scene_id, theme, confidence, rationale):
        self.scene_id = scene_id
        self.theme = theme  # "Teaching", "Chaos", "Reflection", "Decision", "Meta"
        self.confidence = confidence  # 0-100 score
        self.rationale = rationale
        self.timestamp = datetime.now()
        self.llm_model_used = None  # LLM model identifier
```

#### ChapterModel
```python
class ChapterModel:
    """Represents a chapter with scene collection and metrics."""
    
    def __init__(self, chapter_id, title=None):
        self.chapter_id = chapter_id
        self.title = title
        self.scenes = []  # List of SceneModel objects
        self.analysis_results = {}  # scene_id -> ThemeAnalysisModel
        self.theme_distribution = {}  # theme -> count
        self.target_distribution = {
            "Teaching": 0.4,
            "Chaos": 0.25,
            "Reflection": 0.15,
            "Decision": 0.15,
            "Meta": 0.05
        }
    
    def add_scene(self, scene):
        self.scenes.append(scene)
    
    def add_analysis_result(self, result):
        self.analysis_results[result.scene_id] = result
        self._update_distribution()
    
    def _update_distribution(self):
        # Count occurrence of each theme
        self.theme_distribution = Counter([
            result.theme for result in self.analysis_results.values()
        ])
        # Convert to percentages
        total = len(self.analysis_results)
        if total > 0:
            self.theme_distribution = {
                theme: count/total for theme, count in self.theme_distribution.items()
            }
    
    def get_theme_gaps(self):
        """Calculate gaps between current and target distribution."""
        return {
            theme: self.target_distribution.get(theme, 0) - 
                  self.theme_distribution.get(theme, 0)
            for theme in set(self.target_distribution) | set(self.theme_distribution)
        }
```

### 3.2. Controllers

#### FileReaderController
```python
class FileReaderController:
    """Handles file/folder reading operations."""
    
    def read_file(self, filepath):
        """Read a single markdown file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        return content, filepath
    
    def read_folder(self, folderpath, pattern="*.md"):
        """Read all markdown files in a folder."""
        file_paths = glob.glob(os.path.join(folderpath, pattern))
        return [(self.read_file(fp), fp) for fp in file_paths]
    
    def get_input_handler(self, path):
        """Return appropriate handler for given path."""
        if os.path.isfile(path):
            return lambda: [self.read_file(path)]
        elif os.path.isdir(path):
            return lambda: self.read_folder(path)
        else:
            raise ValueError(f"Invalid path: {path}")
```

#### SceneExtractionController
```python
class SceneExtractionController:
    """Extracts scenes from markdown content."""
    
    def extract_scenes(self, content, source_file=None):
        """Extract all scenes from markdown content."""
        scenes = []
        # Use regex or markdown parser to identify scene blocks
        # Example pattern: matching H3 "Scene Description" sections
        scene_pattern = r'#{3}\s+Scene Description\s*\n(.*?)(?=#{3}|\Z)'
        teaching_pattern = r'#{3}\s+Teaching Narrative\s*\n(.*?)(?=#{3}|\Z)'
        example_pattern = r'#{3}\s+Common Example of the Problem\s*\n(.*?)(?=#{3}|\Z)'
        panel_pattern = r'#{2}\s+\*\*Panel (\d+).*?\*\*'
        
        # Find all panels
        panels = re.finditer(panel_pattern, content, re.DOTALL)
        
        for panel_match in panels:
            panel_number = int(panel_match.group(1))
            panel_start = panel_match.start()
            
            # Find next panel or end of content
            next_panel = re.search(panel_pattern, content[panel_start+1:], re.DOTALL)
            panel_end = next_panel.start() + panel_start + 1 if next_panel else len(content)
            panel_content = content[panel_start:panel_end]
            
            # Extract sections
            scene_match = re.search(scene_pattern, panel_content, re.DOTALL)
            teaching_match = re.search(teaching_pattern, panel_content, re.DOTALL)
            example_match = re.search(example_pattern, panel_content, re.DOTALL)
            
            if scene_match:
                scene_text = scene_match.group(1).strip()
                teaching_narrative = teaching_match.group(1).strip() if teaching_match else ""
                common_example = example_match.group(1).strip() if example_match else ""
                
                scene_id = f"{os.path.basename(source_file).split('.')[0]}_panel_{panel_number}"
                
                scene = SceneModel(
                    scene_id=scene_id,
                    panel_number=panel_number,
                    scene_text=scene_text,
                    teaching_narrative=teaching_narrative,
                    common_example=common_example
                )
                scene.source_file = source_file
                scene.line_range = (panel_start, panel_end)  # Approximate
                
                scenes.append(scene)
        
        return scenes
```

#### ThemeAnalysisController
```python
class ThemeAnalysisController:
    """Orchestrates the theme analysis process using LLM."""
    
    def __init__(self, llm_service):
        self.llm_service = llm_service
        self.scene_extraction = SceneExtractionController()
        self.prompt_template = """
        You are an SRE Senior professional with 20 years of experience in comic script editing.
        Given this panel scene:
        ---
        {scene_text}
        
        Teaching Narrative:
        {teaching_narrative}
        
        Common Example:
        {common_example}
        ---
        
        Identify the dominant theme for this scene (choose from: Chaos, Reflection, Teaching, Decision, Meta, or another suitable category).
        Return only this JSON object:
        {{
          "scene_theme": "<type>",
          "confidence": <0-100>,
          "rationale": "<short explanation>"
        }}
        """
    
    def analyze_scene(self, scene):
        """Analyze a single scene and return theme analysis."""
        prompt = self.prompt_template.format(
            scene_text=scene.scene_text,
            teaching_narrative=scene.teaching_narrative,
            common_example=scene.common_example
        )
        
        response = self.llm_service.get_completion(prompt)
        
        try:
            result = json.loads(response)
            analysis = ThemeAnalysisModel(
                scene_id=scene.scene_id,
                theme=result["scene_theme"],
                confidence=result.get("confidence", 90),  # Default if not provided
                rationale=result["rationale"]
            )
            analysis.llm_model_used = self.llm_service.model_name
            return analysis
        except (json.JSONDecodeError, KeyError):
            # Fallback for parsing errors
            return ThemeAnalysisModel(
                scene_id=scene.scene_id,
                theme="Unknown",
                confidence=0,
                rationale="Failed to parse LLM response"
            )
    
    def analyze_chapter(self, content, source_file=None):
        """Analyze all scenes in a chapter."""
        scenes = self.scene_extraction.extract_scenes(content, source_file)
        
        chapter_id = os.path.basename(source_file).split('.')[0] if source_file else "unknown_chapter"
        chapter = ChapterModel(chapter_id=chapter_id)
        
        for scene in scenes:
            chapter.add_scene(scene)
            analysis = self.analyze_scene(scene)
            chapter.add_analysis_result(analysis)
        
        return chapter
    
    def analyze_multiple_chapters(self, file_contents):
        """Analyze multiple chapters from list of file contents."""
        chapters = []
        for content, source_file in file_contents:
            chapter = self.analyze_chapter(content, source_file)
            chapters.append(chapter)
        return chapters
```

#### OutputController
```python
class OutputController:
    """Manages the output of analysis results."""
    
    def save_as_json(self, chapters, output_path):
        """Save analysis results as JSON."""
        output = {
            "analysis_timestamp": datetime.now().isoformat(),
            "chapters": []
        }
        
        for chapter in chapters:
            chapter_data = {
                "chapter_id": chapter.chapter_id,
                "title": chapter.title,
                "scene_count": len(chapter.scenes),
                "theme_distribution": chapter.theme_distribution,
                "target_distribution": chapter.target_distribution,
                "theme_gaps": chapter.get_theme_gaps(),
                "scenes": []
            }
            
            for scene in chapter.scenes:
                analysis = chapter.analysis_results.get(scene.scene_id)
                if analysis:
                    scene_data = {
                        "scene_id": scene.scene_id,
                        "panel_number": scene.panel_number,
                        "theme": analysis.theme,
                        "confidence": analysis.confidence,
                        "rationale": analysis.rationale,
                        # Include abbreviated scene text for reference
                        "scene_text_preview": scene.scene_text[:200] + "..." if len(scene.scene_text) > 200 else scene.scene_text
                    }
                    chapter_data["scenes"].append(scene_data)
            
            output["chapters"].append(chapter_data)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2)
    
    def save_as_yaml(self, chapters, output_path):
        """Save analysis results as YAML."""
        # Implementation similar to save_as_json but using yaml.dump
        pass
    
    def save_report(self, chapters, format_type, output_path):
        """Save report in specified format."""
        if format_type.lower() == "json":
            self.save_as_json(chapters, output_path)
        elif format_type.lower() == "yaml":
            self.save_as_yaml(chapters, output_path)
        else:
            raise ValueError(f"Unsupported format: {format_type}")
```

### 3.3. Views

#### ConsoleProgressView
```python
class ConsoleProgressView:
    """Displays analysis progress in the console."""
    
    def show_start(self, file_count):
        """Show start of analysis."""
        print(f"Starting analysis of {file_count} files...")
    
    def update_progress(self, current, total):
        """Update progress bar."""
        bar_length = 50
        progress = current / total
        bar = '█' * int(bar_length * progress) + '░' * (bar_length - int(bar_length * progress))
        print(f"\r[{bar}] {int(progress * 100)}% ({current}/{total})", end='')
    
    def show_chapter_summary(self, chapter):
        """Show summary for a chapter."""
        print(f"\nChapter: {chapter.chapter_id}")
        print(f"Scenes analyzed: {len(chapter.scenes)}")
        print("Theme distribution:")
        for theme, percentage in chapter.theme_distribution.items():
            print(f"  - {theme}: {percentage:.1%}")
        
        gaps = chapter.get_theme_gaps()
        if any(abs(gap) > 0.05 for gap in gaps.values()):
            print("Theme balance issues:")
            for theme, gap in gaps.items():
                if gap > 0.05:
                    print(f"  - Needs more {theme} scenes (+{gap:.1%})")
                elif gap < -0.05:
                    print(f"  - Too many {theme} scenes ({gap:.1%})")
    
    def show_completion(self, output_path):
        """Show completion message."""
        print(f"\nAnalysis complete. Results saved to {output_path}")
```

## 4. Main Application Flow

### 4.1. Main Controller
```python
class SceneThemeAnalysisApp:
    """Main application controller for scene theme analysis."""
    
    def __init__(self, llm_service):
        self.file_reader = FileReaderController()
        self.theme_analyzer = ThemeAnalysisController(llm_service)
        self.output_controller = OutputController()
        self.console_view = ConsoleProgressView()
    
    def run(self, input_path, output_path, output_format="json"):
        """Run the scene theme analysis application."""
        # Step 1: Determine if input is file or folder
        input_handler = self.file_reader.get_input_handler(input_path)
        
        # Step 2: Read input files
        file_contents = input_handler()
        self.console_view.show_start(len(file_contents))
        
        # Step 3: Process chapters
        chapters = []
        for i, (content, source_file) in enumerate(file_contents):
            self.console_view.update_progress(i+1, len(file_contents))
            chapter = self.theme_analyzer.analyze_chapter(content, source_file)
            chapters.append(chapter)
            self.console_view.show_chapter_summary(chapter)
        
        # Step 4: Generate output
        self.output_controller.save_report(chapters, output_format, output_path)
        self.console_view.show_completion(output_path)
        
        return chapters  # Return for potential further processing
```

### 4.2. LLM Service
```python
class OpenAIService:
    """Service for interacting with OpenAI API."""
    
    def __init__(self, api_key, model="gpt-4-turbo"):
        self.api_key = api_key
        self.model_name = model
        # Initialize OpenAI client
        import openai
        openai.api_key = api_key
        self.client = openai.OpenAI()
    
    def get_completion(self, prompt, max_tokens=1000):
        """Get completion from OpenAI API."""
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            return None
```

### 4.3. Entry Point

```python
def main():
    """Entry point for command-line execution."""
    parser = argparse.ArgumentParser(description="Analyze scene themes in markdown files")
    parser.add_argument("input", help="Input file or directory path")
    parser.add_argument("output", help="Output file path for analysis results")
    parser.add_argument("--format", choices=["json", "yaml"], default="json", 
                        help="Output format (default: json)")
    parser.add_argument("--api-key", help="OpenAI API key")
    args = parser.parse_args()
    
    # Get API key from args or environment
    api_key = args.api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OpenAI API key must be provided")
        return 1
    
    # Initialize services and app
    llm_service = OpenAIService(api_key)
    app = SceneThemeAnalysisApp(llm_service)
    
    # Run analysis
    app.run(args.input, args.output, args.format)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

## 5. Output File Format

### 5.1. JSON Output Structure

```json
{
  "analysis_timestamp": "2023-05-21T10:15:30.123456",
  "chapters": [
    {
      "chapter_id": "chapter_01",
      "title": "The Site Is Down",
      "scene_count": 7,
      "theme_distribution": {
        "Teaching": 0.71,
        "Chaos": 0.14,
        "Reflection": 0.14,
        "Decision": 0.0,
        "Meta": 0.0
      },
      "target_distribution": {
        "Teaching": 0.4,
        "Chaos": 0.25,
        "Reflection": 0.15,
        "Decision": 0.15,
        "Meta": 0.05
      },
      "theme_gaps": {
        "Teaching": -0.31,
        "Chaos": 0.11,
        "Reflection": 0.01,
        "Decision": 0.15,
        "Meta": 0.05
      },
      "scenes": [
        {
          "scene_id": "chapter_01_panel_1",
          "panel_number": 1,
          "theme": "Chaos",
          "confidence": 85,
          "rationale": "Scene depicts urgent situation with alerts and customer impact",
          "scene_text_preview": "A dimly lit operations center at 2 AM. A banking support engineer sits hunched over a desk, illuminated by the eerie glow of multiple monitoring dashboards..."
        },
        {
          "scene_id": "chapter_01_panel_2",
          "panel_number": 2,
          "theme": "Teaching",
          "confidence": 92,
          "rationale": "Senior SRE explains concept to junior staff",
          "scene_text_preview": "Slack explodes with VP-level pings. *\"$4 million in stuck transfers?!\"*\nWanjiru Maina, the eager junior dev, slams her mouse from graph to graph..."
        }
        // More scenes...
      ]
    }
    // More chapters...
  ]
}
```

## 6. Implementation Considerations

### 6.1. Error Handling

- **LLM Service Failures**: Implement retry logic and fallbacks
- **Parsing Errors**: Handle malformed markdown gracefully
- **API Limitations**: Add rate limiting and throttling for OpenAI API

### 6.2. Performance Optimization

- **Batch Processing**: Process multiple scenes in parallel where possible
- **Caching**: Cache LLM responses for similar prompts
- **Incremental Processing**: Allow resuming analysis from checkpoint

### 6.3. Extensibility

- **Plugin Architecture**: Allow for custom analyzers or output formats
- **Configuration File**: Support external configuration for analysis parameters
- **Feedback Loop**: Enable manual corrections to be fed back into the system

## 7. Test Plan

### 7.1. Unit Tests

- Test markdown parsing logic
- Test scene extraction from various markdown formats
- Test theme distribution calculation
- Test gap analysis logic

### 7.2. Integration Tests

- Test end-to-end with sample markdown files
- Test different output formats
- Test with mock LLM service responses

### 7.3. Manual Testing

- Validate scene theme classification accuracy
- Review distribution recommendations on real chapters
- Verify output format compatibility with downstream processes

## 8. Sample Implementation

A simplified working example (without full error handling):

```python
import os
import json
import argparse
import re
from collections import Counter
from datetime import datetime

def extract_scenes(content, source_file=None):
    """Extract scenes from markdown content."""
    scenes = []
    # Simple regex pattern to identify panel sections and scene descriptions
    panel_pattern = r'## \*\*Panel (\d+).*?\*\*'
    scene_pattern = r'### Scene Description\s*\n(.*?)(?=###|$)'
    
    panels = re.finditer(panel_pattern, content, re.DOTALL)
    
    for panel_match in panels:
        panel_num = int(panel_match.group(1))
        panel_start = panel_match.start()
        
        # Find next panel or end of content
        next_panel = re.search(panel_pattern, content[panel_start+1:], re.DOTALL)
        panel_end = next_panel.start() + panel_start + 1 if next_panel else len(content)
        panel_content = content[panel_start:panel_end]
        
        # Extract scene description
        scene_match = re.search(scene_pattern, panel_content, re.DOTALL)
        if scene_match:
            scene_text = scene_match.group(1).strip()
            scene_id = f"{os.path.basename(source_file).split('.')[0]}_panel_{panel_num}"
            
            scene = {
                "scene_id": scene_id,
                "panel_num": panel_num,
                "scene_text": scene_text
            }
            scenes.append(scene)
    
    return scenes

def analyze_scene_theme(scene_text):
    """Mock LLM analysis of scene theme."""
    # In a real implementation, this would call the OpenAI API
    # For testing, we'll use a simplistic keyword-based approach
    keywords = {
        "Chaos": ["alert", "emergency", "urgent", "alarm", "failure"],
        "Teaching": ["explain", "lesson", "learn", "understand", "concept"],
        "Reflection": ["consider", "reflect", "review", "ponder", "retrospective"],
        "Decision": ["decide", "choice", "option", "select", "determine"],
        "Meta": ["process", "approach", "methodology", "practice", "discipline"]
    }
    
    # Count keyword occurrences
    counts = {theme: 0 for theme in keywords}
    for theme, words in keywords.items():
        for word in words:
            counts[theme] += scene_text.lower().count(word)
    
    # Find theme with most matches
    if all(count == 0 for count in counts.values()):
        theme = "Teaching"  # Default if no keywords match
        confidence = 60
    else:
        theme = max(counts, key=counts.get)
        total = sum(counts.values())
        confidence = int(counts[theme] / total * 100) if total > 0 else 60
    
    return {
        "scene_theme": theme,
        "confidence": confidence,
        "rationale": f"Identified through keyword analysis"
    }

def analyze_file(filepath):
    """Analyze a single markdown file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract scenes
    scenes = extract_scenes(content, filepath)
    
    # Analyze each scene
    results = []
    for scene in scenes:
        analysis = analyze_scene_theme(scene["scene_text"])
        results.append({
            "scene_id": scene["scene_id"],
            "panel_num": scene["panel_num"],
            "theme": analysis["scene_theme"],
            "confidence": analysis["confidence"],
            "rationale": analysis["rationale"],
            "scene_text_preview": scene["scene_text"][:100] + "..." if len(scene["scene_text"]) > 100 else scene["scene_text"]
        })
    
    # Calculate theme distribution
    themes = [r["theme"] for r in results]
    theme_counts = Counter(themes)
    total = len(themes)
    distribution = {theme: count/total for theme, count in theme_counts.items()}
    
    return {
        "file": os.path.basename(filepath),
        "scene_count": len(scenes),
        "theme_distribution": distribution,
        "scenes": results
    }

def main():
    parser = argparse.ArgumentParser(description="Analyze scene themes in markdown files")
    parser.add_argument("input", help="Input file or directory path")
    parser.add_argument("output", help="Output JSON file path")
    args = parser.parse_args()
    
    # Determine if input is file or directory
    if os.path.isfile(args.input):
        results = [analyze_file(args.input)]
    elif os.path.isdir(args.input):
        results = []
        for filename in os.listdir(args.input):
            if filename.endswith(".md"):
                filepath = os.path.join(args.input, filename)
                results.append(analyze_file(filepath))
    else:
        print(f"Error: {args.input} is not a valid file or directory")
        return 1
    
    # Save results
    output = {
        "analysis_timestamp": datetime.now().isoformat(),
        "file_count": len(results),
        "results": results
    }
    
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)
    
    print(f"Analysis complete. Results saved to {args.output}")
    return 0

if __name__ == "__main__":
    main()
```

## 9. Next Steps

1. **Initial Implementation**: Develop the core scene extraction and theme analysis components
2. **Testing with Sample Data**: Verify the analysis accuracy with a subset of chapters
3. **Refinement of Theme Definitions**: Adjust theme classification criteria based on initial results
4. **Integration with MVC Framework**: Connect to your existing application architecture
5. **Pilot Testing**: Process a few chapters end-to-end and review results
6. **Optimization**: Refine for performance, accuracy, and ease of use

This implementation provides a foundation for the Scene Theme Analysis component that can be integrated into your MVC framework and expanded as needed.