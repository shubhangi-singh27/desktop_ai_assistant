import customtkinter as ctk
import threading
from pathlib import Path
import time
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from recorder.screen_recorder import ScreenRecorder
from recorder.event_tracker import EventTracker
from recorder.audio_recorder import AudioRecorder
from analyzer.activity_analyzer import ActivityAnalyzer
from llm.ollama_client import OllamaClient

class MainWindow:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Desktop AI Assistant")
        self.root.geometry("800x600")

        self.is_recording = False

        self.screen_recorder = None
        self.event_tracker = None
        self.audio_recorder = None

        self._create_widgets()

    def _create_widgets(self):
        title = ctk.CTkLabel(
            self.root,
            text="Desktop AI Assistant",
            font=("Arial", 24, "bold")
        )

        title.pack(pady=20)

        self.status_label = ctk.CTkLabel(
            self.root,
            text="Ready to record",
            font=("Arial", 14)
        )
        self.status_label.pack(pady=10)

        button_frame = ctk.CTkFrame(self.root)
        button_frame.pack(pady=20)

        self.start_button = ctk.CTkButton(
            button_frame,
            text="Start Recording",
            command=self.start_recording,
            width=150,
            height=40
        )

        self.start_button.pack(side="left", padx=10)

        self.stop_button = ctk.CTkButton(
            button_frame,
            text="Stop Recording",
            command=self.stop_recording,
            state="disabled",
            width=150,
            height=40
        )
        self.stop_button.pack(side="left", padx=10)

        # Suggestions
        suggestions_label = ctk.CTkLabel(
            self.root,
            text="Automation Suggestions:",
            font=("Arial", 16, "bold")
        )

        suggestions_label.pack(pady=(20,5))

        self.suggestions_text = ctk.CTkTextbox(
            self.root,
            width=750,
            height=300
        )
        self.suggestions_text.pack(pady=10)

        duration_frame = ctk.CTkFrame(self.root)
        duration_frame.pack(pady=15)

        duration_label = ctk.CTkLabel(
            duration_frame, 
            text="Recording Duration (seconds):",
            font=("Arial", 16, "bold")
        )
        duration_label.pack(side="left", padx=15)

        self.duration_entry = ctk.CTkEntry(
            duration_frame, 
            width=200,
            height=40,
            font=("Arial", 16)
        )
        self.duration_entry.insert(0, "60")
        self.duration_entry.pack(side="left", padx=15)


    def start_recording(self):
        try:
            duration = int(self.duration_entry.get())
        except ValueError:
            duration = 60

        self.is_recording = True
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.status_label.configure(text="Recording in progress...")

        recording_thread = threading.Thread(
            target=self._record_session, 
            args=(duration,),
            daemon=True
        )
        recording_thread.start()

    def stop_recording(self):
        self.is_recording = False
        self.status_label.configure(text="Recording stopped, Generating suggestions...")

    def _record_session(self, duration):
        try:
            self.screen_recorder = ScreenRecorder(interval=2)
            self.event_tracker = EventTracker()
            self.audio_recorder = AudioRecorder()

            self.screen_recorder.start()
            self.event_tracker.start()
            self.audio_recorder.start()

            time.sleep(duration)

            self.screen_recorder.stop()
            self.event_tracker.stop()
            self.audio_recorder.stop()

            self._generate_suggestions()
        
        except Exception as e:
            self.status_label.configure(text=f"Error: {str(e)}")

    def _generate_suggestions(self):
        try:
            self.status_label.configure(text="Building and Analyzing workflow...")

            analyzer = ActivityAnalyzer()
            workflow = analyzer.generate_workflow_json()

            llm_client = OllamaClient()
            suggestions = llm_client.generate_suggestions(workflow)

            hybrid_suggestion = analyzer.detect_patterns_hybrid(analyzer.load_events())

            result_text = f"Pattern Detection:\n" + "\n".join(hybrid_suggestion)
            result_text += f"LLM Suggestions:\n{suggestions}\n\n"

            self.suggestions_text.delete("1.0", "end")
            self.suggestions_text.insert("end", result_text)

            self.status_label.configure(text="Analysis complete!")
            self.start_button.configure(state="normal")
            self.stop_button.configure(state="disabled")

        except Exception as e:
            self.status_label.configure(text=f"Analysis error: {str(e)}")
            self.start_button.configure(state="normal")
            self.stop_button.configure(state="disabled")
    

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = MainWindow()
    app.run()