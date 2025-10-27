import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict

class ActivityAnalyzer:
    """Analyze user activity from screenshots, events and audio"""
    def __init__(self, 
                screenshot_dir = "data/screenshots",
                events_dir = "data/events",
                audio_dir = "data/audio"):
        self.screenshots_dir = Path(screenshot_dir)
        self.events_dir = Path(events_dir)
        self.audio_dir = Path(audio_dir)

        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        self.events_dir.mkdir(parents=True, exist_ok=True)
        self.audio_dir.mkdir(parents=True, exist_ok=True)

    def load_events(self, session_id=None):
        event_files = list(self.events_dir.glob("events_*.json"))

        if not event_files:
            return []

        if session_id:
            event_file = self.events_dir/f"events_{session_id}.json"
        else:
            event_file = sorted(event_files)[-1]

        try:
            with open(event_file, 'r') as f:
                return json.load(f)

        except Exception as e:
            print(f"Error loading events: {e}")
            return []

    def load_screenshots(self) -> List[Path]:
        screenshot_files = sorted(self.screenshots_dir.glob("screenshot_*.png"))
        return screenshot_files

    def load_audio_transcripts(self) -> List[Path]:
        transcript_files = sorted(self.audio_dir.glob("transcript_*.json"))
        transcripts = []

        for transcript_file in transcript_files:
            try:
                with open(transcript_file, 'r') as f:
                    transcript_data = json.load(f)
                    transcripts.append(transcript_data)
            except Exception as e:
                print(f"Error loading transcript {transcript_file}: {e}")
        
        return transcripts

    def generate_workflow_json(self, session_id=None) -> Dict:
        events = self.load_events(session_id)
        screenshots = self.load_screenshots()
        transcripts = self.load_audio_transcripts()

        workflow = {
            "session_id": session_id or datetime.now().strftime("%Y%m%d_%H%M%S"),
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_events": len(events),
                "total_screenshots": len(screenshots),
                "total_transcripts": len(transcripts)
            },
            "events": events,
            "screenshots": [str(s) for s in screenshots],
            "transcripts": transcripts,
            "workflow_steps": self._analyze_workflow_steps(events)
        }

        return workflow
    
    def _analyze_workflow_steps(self, events: List[Dict]) -> List[Dict]:
        steps = []

        for event in events:
            step = {
                "timestamp": event.get("timestamp"),
                "window": event.get("window"),
                "action_type": event.get("type")
            }

            if event.get("type") == "mouse_click":
                step["click_location"] = {"x": event.get("x"), "y": event.get("y")}
                if "clicked_element" in event:
                    step["clicked_element"] = event.get("clicked_element")

            elif event.get("type") == "key_press":
                step["key"] = event.get("key")

            steps.append(step)

        return steps

if __name__ == "__main__":
    print("Activity Analyser Test")

    analyzer = ActivityAnalyzer()

    workflow = analyzer.generate_workflow_json()

    print(f"Session ID: {workflow['session_id']}")
    print(f"Total Events: {workflow['summary']['total_events']}")
    print(f"Total Screenshots: {workflow['summary']['total_screenshots']}")
    print(f"Total Transcripts: {workflow['summary']['total_transcripts']}")
    print(f"Workflow Steps: {len(workflow['workflow_steps'])}")

    output_file = Path("data")/f"workflow_{workflow['session_id']}.json"
    with open(output_file, 'w') as f:
        json.dump(workflow, f, indent=2)

    print(f"Workflow saved to {output_file}")