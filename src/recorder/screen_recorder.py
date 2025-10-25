import os
from pickletools import read_unicodestring8
import time
import threading
from datetime import datetime
from pathlib import Path
import mss
from PIL import Image

class ScreenRecorder:
    """Capture periodic screenshots"""

    def __init__(self, output_dir="data/screenshots", interval=3):
        self.output_dir = Path(output_dir)
        self.interval = interval

        # Create output dir if it doesn't already exist
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.is_recording = False
        self.is_paused = False

        # Background recording thread
        self.recording_thread = None


    def _capture_screenshot(self):
        """Capture a screenshot and save it with the timestamp"""

        try:
            # MSS instance
            sct = mss.mss()

            monitor = sct.monitors[1]

            screenshot = sct.grab(monitor)

            img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)

            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"screenshot_{timestamp}.png"
            filepath = self.output_dir/filename
            img.save(filepath)

            print(f"Screenshot saved: {filepath}")
            return str(filepath)

        except Exception as e:
            print(f"Error capturing screenshot: {e}")
            return None
        finally:
            if "sct" in locals():
                sct.close()

    def _recording_loop(self):
        """
        Captures screenshots at specified interval and saves them to the output directory
        Continues in the background until the recording is stopped
        """

        while self.is_recording:
            # Check if paused
            if self.is_paused:
                time.sleep(0.5)
                continue

            self._capture_screenshot()
            time.sleep(self.interval)

        print("Recording stopped")

    def start(self):
        """Start recording screenshots"""
        if self.is_recording:
            print("Already recording...")
            return

        self.is_recording = True
        self.is_paused = False

        self.recording_thread = threading.Thread(target=self._recording_loop)
        self.recording_thread.start()

        print("Recording now!")

    def stop(self):
        """Stop recording screenshots"""

        if not self.is_recording:
            print("Recording is not running.")
            return

        self.is_recording = False

        if self.recording_thread:
            self.recording_thread.join(timeout=5)

        print("Recording stopped")

    def pause(self):
        """Pause recording"""
        if not self.is_recording:
            print("Recording is not running.")
            return
        
        self.is_paused = True
        
        print("Recording paused")

    def resume(self):
        """Resume recording"""
        if not self.is_recording:
            print("Recording is not running.")
            return

        self.is_paused = False

        print("Recording resumed!")

    def get_status(self):
        """Get current recording status"""
        if not self.is_recording:
            return "stopped"
        elif self.is_paused:
            return "paused"
        else:
            return "recording"

    def set_interval(self, interval):
        """Incase you want to change the screenshot interval"""
        self.interval = interval
        print(f"Capture interval set to {interval} seconds")

    def cleanup(self):
        """Clean up resources"""
        self.stop()

if __name__ == "__main__":
    print("Starting screen recorder...")

    recorder = ScreenRecorder(interval=2)

    recorder.start()

    print("Recording for 20 seconds...")
    time.sleep(20)

    recorder.stop()

    recorder.cleanup()

    print("\nTest complete! Check the 'data/screenshots directory.")