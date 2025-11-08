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

    def _build_click_summary(self, event, label, element_info):
        window = event.get("window", "Unknown window")
        if label:
            return f"Clicked '{label}' in {window}"
        if element_info.get("control_type"):
            return f"Clicked {element_info['control_type']} in {window}"
        return f"Mouse click in {window}"

    def _build_key_summary(self, event):
        key = event.get("key", "Unknown key")
        window = event.get("window", "Unknown window")
        if '+' in key:
            return f"Used shortcut: {key} in {window}"
        if len(key) == 1:
            return f"Typed: {key} in {window}"
        return f"Pressed '{key}' in {window}"


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
        pending_keys = []
        pending_window = None
        pending_element = None
        pending_start = None

        def flush_pending_keys():
            nonlocal pending_keys, pending_window, pending_element, pending_start
            if not pending_keys:
                return
            key_text = " ".join(pending_keys)
            step = {
                'timestamp': pending_start,
                'window': pending_window or "Unknown window",
                'action_type': 'key_press',
                'keys': pending_keys[:],
                'summary': f"Typed: {key_text} in {pending_window or 'Unknown window'}"
            }
            if pending_element:
                step['element'] = pending_element

            steps.append(step)
            pending_keys = []
            pending_window = None
            pending_element = None
            pending_start = None

        for event in events:
            action_type = event.get("type")
            window = event.get("window")

            if action_type != "key_press":
                flush_pending_keys()

            if action_type == "mouse_click":
                element_info = event.get("element") or {}
                label = event.get("clicked_element") or element_info.get("name")
                steps.append({
                    'timestamp': event.get("timestamp"),
                    'window': window,
                    'action_type': 'mouse_click',
                    'click': {
                        "location": {"x": event.get("x"), "y": event.get("y")},
                        "label": label,
                        "element": element_info
                    },
                    'summary': self._build_click_summary(event, label, element_info)
                })
                pending_element = element_info or None

            elif action_type == "key_press":
                key = event.get("key")
                if not key:
                    continue
                if not pending_keys:
                    pending_window = window
                    pending_start = event.get("timestamp")
                    pending_element = event.get("element") or None
                elif window != pending_window:
                    flush_pending_keys()
                    pending_window = window
                    pending_start = event.get("timestamp")
                    pending_element = event.get("element") or None

                pending_keys.append(key)
            else:
                steps.append({
                    'timestamp': event.get("timestamp"),
                    'window': window,
                    'action_type': action_type,
                    'summary': f"{action_type or 'event'} recorded"
                })
            
        flush_pending_keys()

        return steps

    def detect_patterns_hybrid(self, events: List[Dict]) -> List[str]:
        suggestions = []

        actions = []
        windows = []

        for event in events:
            action_type = event.get('type', '')
            window = event.get('window', 'unknown')

            if action_type == "mouse_click":
                element = event.get('clicked_element', '')
                if element:
                    actions.append(f"{window}: {element}")
                else:
                    actions.append(f"{windows}: click")
            if action_type == 'key_press':
                key = event.get('key', '')
                actions.append(f"{window}: {key}")

            windows.append(window)

        from collections import Counter
        action_counts = Counter(actions)

        for action, count in action_counts.items():
            if count >= 3:
                windows, detail = action.split(':', 1)
                suggestions.append(
                    f"Detected repetitive action: {windows} - {detail} ({count} times)"
                    f"This can be automated."
                )
            
        unique_windows = [w for w in windows if w and w != 'unknown']
        if len(set(unique_windows)) >= 2:
            suggestions.append(
                f"Detected workflow spanning multiple apps: {', '.join(set(unique_windows))}."
                f"Data flow between these applications can be automated."
            )
        
        return suggestions

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