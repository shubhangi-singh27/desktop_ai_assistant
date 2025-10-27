import requests
import json
from typing import Dict, List, Optional

class OllamaClient:
    """Client for Ollama interaction. Send workflow data and get automation suggestions"""
    def __init__(self, base_url="http://localhost:11434"):
        self.base_url = base_url
        self.model = "tinyllama"

    def _create_prompt(self, workflow_data: Dict) -> str:
        total_events = workflow_data.get('summary', {}).get('total_events', 0)
        steps = workflow_data.get('workflow_steps', [])

        total_steps = len(steps)
        sample_size = min(5, total_steps)

        if total_steps > sample_size:
            step_indices = [int(i*total_steps/sample_size) for i in range(sample_size)]
            sampled_steps = [steps[i] for i in step_indices]
        else:
            sampled_steps = steps

        # Build timeline with context
        timeline = ""
        previous_window = None
        for i, step in enumerate(steps, 1):
            current_window = step.get('window', 'Unknown')
            
            # Add window/app context
            if previous_window and current_window!=previous_window:
                timeline += f"--- SWITCHED TO: {current_window} ---"

            timeline += f"\n{i}. "
            
            # Add action
            action_type = step.get('action_type', 'unknown')
            
            if action_type == 'mouse_click':
                if step.get('clicked_element'):
                    timeline += f"Clicked '{step.get('clicked_element')}'"
                elif step.get('click_location'):
                    x = step.get('click_location', {}).get('x')
                    y = step.get('click_location', {}).get('y')
                    if x is not None and y is not None:
                        timeline += f"Clicked at coordinates: ({x}, {y})"
                    else:
                        timeline += "Clicked"
                else:
                    timeline += "Clicked"
            
            elif action_type == 'key_press':
                key = step.get('key', '')
                if '+' in key or '(' in key:
                    timeline += f"Keyboard shortcut: {key}"
                else:
                    timeline += f"Typed: {key}"
            
            timeline += f" in {step.get('window', '')}"
            previous_window = current_window
        
        prompt = f"""You are an **automation analysis assistant**.
            Analyze the user's desktop activity log below and suggest realistic automations.

            === ACTIVITY TIMELINE ===
            {timeline}

            === TASK ===
            1. Understand what overall task the user is trying to complete.
            2. Identify any repeated sequences or multi-step workflows.
            3. Suggest specific automations that could save time or reduce manual effort.
            - Focus on automations that are possible using common desktop tools (Excel, browser, etc.).
            - Avoid generic advice. Suggest concrete steps.

            === OUTPUT FORMAT ===
            USER GOAL:
            [Brief and specific goal statement]

            REPEATING PATTERNS:
            - [Pattern 1: concise description of repeated behavior]
            - [Pattern 2: another repeated sequence, if any]

            AUTOMATION IDEAS:
            - [Automation 1: what can be automated + how (macro/script/workflow)]
            - [Automation 2: another possible automation]
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
                    "stream": False
                },
                timeout = 300
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