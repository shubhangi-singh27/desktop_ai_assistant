import time
import json
from pathlib import Path
from collections import Counter
from src.recorder.screen_recorder import ScreenRecorder
from src.recorder.event_tracker import EventTracker
from src.recorder.audio_recorder import AudioRecorder
from src.analyzer.activity_analyzer import ActivityAnalyzer
from src.llm.ollama_client import OllamaClient
from src.utils.data_cleaner import clear_all_data

def main():
    print("="*60)
    print("Desktop AI Assistant - Recording Session")
    print("="*60)

    print("Do you want old recorded data to be deleted?")
    choice = input("Enter 'yes' to delete, or press Enter to keep them: ")
    if choice.lower() == 'yes':
        clear_all_data(confirm=False)
        print()

    RECORDING_DURATION = 180

    print("[1/5]Initalizing recorders...")
    screen_recorder = ScreenRecorder(interval=2)
    event_tracker = EventTracker()
    audio_recorder = AudioRecorder()

    print("[2/5] Starting all recorders...")
    screen_recorder.start()
    event_tracker.start()
    audio_recorder.start()

    print(f"Recording for {RECORDING_DURATION} seconds...")
    print("You can interact with your computer during this time.")
    print("Try clicking, typing, opening apps, etc")

    time.sleep(RECORDING_DURATION)

    print("[3/5] Stopping all recorders...")
    screen_recorder.stop()
    event_tracker.stop()
    audio_recorder.stop()

    print("[4/5] Analyzing workflow...")
    analyzer = ActivityAnalyzer()
    workflow = analyzer.generate_workflow_json()
    workflow_file = Path("data")/f"workflow_{workflow['session_id']}.json"
    with open(workflow_file, 'w') as f:
        json.dump(workflow, f, indent=2)

    print(f"Workflow saved to: {workflow_file}")

    print(f"Captured {workflow['summary']['total_events']} events")
    print(f"Captured {workflow['summary']['total_screenshots']} screenshots")
    print(f"Captured {workflow['summary']['total_transcripts']} audio transcripts")

    print("[Bonus] Generating hybrid pattern suggestions...")
    hybrid_suggestions = analyzer.detect_patterns_hybrid(workflow['events'])

    print("[5/5] Generating automation suggestions...")
    print("This may take 30-60 seconds...")

    llm_client = OllamaClient()
    suggestions = llm_client.generate_suggestions(workflow)

    # Save both suggestions to a file for comparison
    suggestions_file = Path("data") / f"automation_suggestions_{workflow['session_id']}.txt"
    with open(suggestions_file, 'w', encoding='utf-8') as f:
        f.write("="*60 + "\n")
        f.write("AUTOMATION SUGGESTIONS - COMPARISON\n")
        f.write("="*60 + "\n\n")
        
        f.write("LLM-BASED SUGGESTIONS:\n")
        f.write("-"*60 + "\n")
        f.write(suggestions)
        f.write("\n\n" + "="*60 + "\n\n")
        
        f.write("HYBRID PATTERN DETECTION:\n")
        f.write("-"*60 + "\n")
        if hybrid_suggestions:
            f.write("\n".join(hybrid_suggestions))
        else:
            f.write("No patterns detected.")
        
        f.write("\n\n" + "="*60 + "\n")

    print(f"\nAll suggestions saved to: {suggestions_file}")

    print("="*60)
    print("AUTOMATION SUGGESTIONS:")
    print("="*60)
    print(suggestions)
    print("="*60)
    print("HYBRID PATTERN SUGGESTIONS:")
    print("="*60)
    print("\n".join(hybrid_suggestions))
    print("="*60)

    print("Recording session complete!")
    print(f"Check 'data/' folder for captured data.")

if __name__ == "__main__":
    main()