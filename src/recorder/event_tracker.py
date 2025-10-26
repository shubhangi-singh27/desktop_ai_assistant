import json
import time
import threading
from datetime import datetime
from pathlib import Path
from pynput import mouse, keyboard
import pygetwindow as gw
from PIL import Image, ImageGrab
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

class EventTracker:
    """Captures mouse, keyboard and window events"""
    def __init__(self, output_dir="data/events"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Event storage
        self.events = []
        self.max_events_before_save = 50

        # Control flag
        self.is_tracking = False

        # Event listeners
        self.mouse_listener = None
        self.keyboard_listener = None

        # Mouse position and threshold to track position
        self.last_mouse_x = None
        self.last_mouse_y = None
        self.movement_threshold = 5

        # Windows tracker
        self.current_window = None

        # Generate session_id
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        # OCR Configuration
        self.ocr_enabled = True
        self.ocr_crop_size = 100

    def _log_event(self, event_type, data):
        """Log an event with timestamp and windows info"""

        try:
            active_window = gw.getActiveWindow()
            window_title = active_window.title if active_window else "Unknown"
        except:
            window_title = "Unknown"

        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "window": window_title,
            **data
        }

        self.events.append(event)

        if len(self.events) >= self.max_events_before_save:
            self._save_events()

    def _on_mouse_click(self, x, y, button, pressed):
        """To handle mouse click event"""
        if not pressed:
            return

        clicked_element = None
        if self.ocr_enabled:
            clicked_element = self._extract_text_near_click(x, y)
        
        event_data = {
            "x": x,
            "y": y,
            "button": str(button)
        }

        if clicked_element:
            event_data["clicked_element"] = clicked_element

        self._log_event("mouse_click", event_data)

    def _on_mouse_move(self, x, y):
        """To handle mouse movement event"""

        if self.last_mouse_x is not None:
            dx = abs(x-self.last_mouse_x)
            dy = abs(y-self.last_mouse_y)

            if dx<self.movement_threshold and dy<self.movement_threshold:
                return

        self.last_mouse_x = x
        self.last_mouse_y = y

        self._log_event("mouse_move", {
            "x": x,
            "y": y,
        })

    def _on_mouse_scroll(self, x, y, dx, dy):
        """To handle mouse scroll event"""
        self._log_event("mouse_scroll", {
            "x": x,
            "y": y,
            "delta_x": dx,
            "delta_y": dy
        })
    
    def _extract_text_near_click(self, x, y):
        """Extract text from screenshot near click location using OCR"""
        if not self.is_tracking:
            return None

        try:
            # Capture small area around the click
            left = max(0, x-self.ocr_crop_size//2)
            top = max(0, y-self.ocr_crop_size//2)
            right = x + self.ocr_crop_size//2
            bottom = y + self.ocr_crop_size//2

            screenshot = ImageGrab.grab(bbox=(left, top, right, bottom))

            text = pytesseract.image_to_string(
                screenshot, 
                lang='eng',
                # config='--psm 8 -c tessedict_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890_'
            )
            text = text.strip().replace('\n', '')

            return text if text else None
        
        except Exception as e:
            print(f"OCR error: {e}")
            return None

    def _on_key_press(self, key):
        """Handle keyboard key press event"""
        try:
            key_str = key.char

        except AttributeError:
            key_str = str(key).replace("Key.", "")

        self._log_event("key_press", {
            "key": key_str
        })

    def _save_events(self):
        """Save events to a JSON file"""
        if not self.events:
            return

        filename = f"events_{self.session_id}.json"
        filepath = self.output_dir/filename

        existing_events = []
        if filepath.exists():
            try:
                with open(filepath, "r") as f:
                    existing_events = json.load(f)
            except:
                pass
        
        # Add all events to one list
        all_events = existing_events + self.events

        with open(filepath, "w") as f:
            json.dump(all_events, f, indent=2)

        print(f"Saved {len(self.events)} events.")

        self.events = []

    def start(self):
        """Start tracking events"""

        if self.is_tracking:
            print("Event tracker already running.")
            return

        self.is_tracking = True

        self.mouse_listener = mouse.Listener(
            on_click=self._on_mouse_click,
            on_move=self._on_mouse_move,
            on_scroll=self._on_mouse_scroll
        )
        self.mouse_listener.start()

        self.keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press
        )
        self.keyboard_listener.start()

        print("Event tracking started.")

    def stop(self):
        """Stop event tracking"""
        if not self.is_tracking:
            print("Event tracking not running!")
            return

        self.is_tracking = False

        # Stop listeners
        if self.mouse_listener:
            self.mouse_listener.stop()
        if self.keyboard_listener:
            self.keyboard_listener.stop()

        self._save_events()

        print("Event tracking stopped.")


if __name__ == "__main__":
    print("Event Tracker Test")
    print("Tracking will start in 2 seconds.")
    print("Move, scroll, click, press key on keyboard for 10 seconds.")
    time.sleep(2)

    tracker = EventTracker()
    tracker.start()
    print("Tracking for 20 seconds")

    time.sleep(20)

    tracker.stop()

    print("Test complete")
    print("Check the file called event_date_time.json")