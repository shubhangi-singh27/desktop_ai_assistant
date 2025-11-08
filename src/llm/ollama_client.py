import requests
import json
from typing import Dict, List, Optional

class OllamaClient:
    """Client for Ollama interaction. Send workflow data and get automation suggestions"""
    def __init__(self, base_url="http://localhost:11434"):
        self.base_url = base_url
        self.model = "tinyllama"
        # self.model = "qwen2:1.5b-instruct"

    def _create_prompt(self, workflow_data: Dict) -> str:
        total_events = workflow_data.get('summary', {}).get('total_events', 0)
        steps = workflow_data.get('workflow_steps', [])

        total_steps = len(steps)

        # Build timeline with context
        timeline_lines = []
        previous_window = None
        for i, step in enumerate(steps, 1):
            current_window = step.get('window', 'Unknown window')
            action = step.get('action_type')

            if previous_window and current_window != previous_window:
                timeline_lines.append(f"--- SWITCHED TO: {current_window} ---")

            summary = step.get('summary') or f"{action or 'event'} recorded"
            timeline_lines.append(f"{i}. {summary}")
            
            if step.get('action_type') == 'mouse_click':
                click = step.get("click", {})
                element = click.get("element", {})
                label = click.get("label")
                extras = []

                if label:
                    extras.append(f"Element: '{label}'")
                if element.get("control_type"):
                    extras.append(f"Control Type: {element.get('control_type')}")
                if element.get("automation_id"):
                    extras.append(f"Automation ID: {element.get('automation_id')}")
                if element.get("class_name"):
                    extras.append(f"Class Name: {element.get('class_name')}")

                location = click.get("location")
                if location:
                    extras.append(f"Coordinates: ({location.get('x')}, {location.get('y')})")

                if extras:
                    timeline_lines.append(f" - {', '.join(extras)}")

            elif action in {'key_press', 'key_sequence'}:
                keys = step.get("key")
                if keys:
                    timeline_lines.append(f" - Key sequence: {keys} in {current_window}")
                key = step.get("key")
                if not keys and key:
                    timeline_lines.append(f" - Key: {key} in {current_window}")
                element = step.get("element") or {}
                if element.get("name"):
                    timeline_lines.append(f" - Target Element: {element['name']} in {current_window}")
            
            previous_window = current_window

        timeline = "\n".join(timeline_lines)
        
        prompt = f"""SYSTEM ROLE:
            You are an automation analyst for desktop workflows. Study the provided activity timeline, infer the user’s objectives, and recommend actionable automations. Be specific, reference exact steps, and avoid generic statements.

            GUIDELINES:
            - Respect the chronological order; note window switches that define phases.
            - Note what action is taking place in which window.
            - Keep track if some particular actions are being repeated in a sequence.
            - Understand the user's intent and the context of the actions.
            - Identify the user's goals and the steps they are taking to achieve them.
            - Suggest and explain why an automation would help (time savings, error prevention, consistency).
            - If required information is missing, call it out briefly instead of guessing.

            OUTPUT SECTIONS:
            USER GOAL:
            [1 concise sentence referencing the relevant steps]

            KEY PATTERNS:
            - [Repeated or multi-step sequence with step references and frequency]

            AUTOMATION IDEAS:
            - [Automation 1: description, tools/approach, steps it replaces, expected benefit]
            - [Automation 2: ...]
            (Only include well-grounded ideas; omit this section if no credible automation is found.)

            === ACTIVITY TIMELINE ===
            {timeline}
            """
    
        return prompt
    
    def generate_suggestions(self, workflow_data: Dict) -> str:
        prompt = self._create_prompt(workflow_data)

        from pathlib import Path
        timeline_file = Path("data")/f"timeline_{workflow_data.get('session_id', 'unknown')}.txt"
        with open(timeline_file, 'w', encoding='utf-8') as f:
            f.write(prompt)

        print(f"Timeline save to: {timeline_file}")

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3
                    }
                },
                timeout = 600
            )
            response.raise_for_status()

            result = response.json()
            return result.get("response", "No suggestions generated")

        except requests.exceptions.RequestException as e:
            return f"Error connecting to Ollama: {e}"

if __name__ == "__main__":
    print("Ollama Client Test")

    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))

    from analyzer.activity_analyzer import ActivityAnalyzer

    print("Loading workflow data...")
    analyzer = ActivityAnalyzer()

    workflow = analyzer.generate_workflow_json()
    if workflow['summary']['total_events'] == 0:
        print("No events found! Run the recorder first to collect data")
        exit(1)

    print(f"Workflow loaded with {workflow['summary']['total_events']} events")

    client = OllamaClient()

    print("Generating automation sugeestions...")
    print("This may take 30-60 seconds...")

    suggestions = client.generate_suggestions(workflow)

    print("="*60)
    print("AUTOMATION SUGGESTIONS:")
    print("="*60)
    print(suggestions)
    print("="*60)