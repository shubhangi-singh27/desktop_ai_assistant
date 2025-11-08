import json
import time
import re
import threading
from datetime import datetime
from pathlib import Path
from pynput import mouse, keyboard
import pygetwindow as gw
import pytesseract
from PIL import Image,ImageGrab
import uiautomation as auto

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

        self.pressed_modifiers = set()

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

    def _get_element_at_point(self, x, y):
        try:
            with auto.UIAutomationInitializerInThread():
                element = auto.ControlFromPoint(x, y)

                if not element:
                    return None, None

                info = {
                    "name": element.Name,
                    "control_type": element.ControlTypeName,
                    "automation_id": element.AutomationId,
                    "class_name": element.ClassName
                }

                rect = getattr(element, "BoundingRectangle", None)
                if rect: 
                    info["rectangle"] = [rect.left, rect.top, rect.right, rect.bottom]
                
                friendly = None
                if info["name"]:
                    friendly = info["name"]
                    if info["control_type"] and info["control_type"] not in {'Button', 'MenuItem'}:
                        friendly = f"{info['control_type']}: {friendly}"
                elif info["control_type"]:
                    friendly = info["control_type"]
                    if info["class_name"]:
                        friendly = f"{friendly}({info['class_name']})"
                    
                return friendly, info
        
        except Exception as e:
            print(f"UIA lookup failed: {e}")
            return None, None

    def _on_mouse_click(self, x, y, button, pressed):
        if not pressed:
            return
            
        clicked_element = None

        label, element_info = self._get_element_at_point(x, y)

        event_data = {
            "x": x,
            "y": y,
            "button": str(button)
        }

        if element_info:
            event_data["element"] = element_info
        if label:
            event_data["clicked_element"] = label
        else:
            event_data["clicked_element"] = f"Position({x}, {y})"
        
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

        """self._log_event("mouse_move", {
            "x": x,
            "y": y,
        })"""
        return

    def _on_mouse_scroll(self, x, y, dx, dy):
        """To handle mouse scroll event"""
        self._log_event("mouse_scroll", {
            "x": x,
            "y": y,
            "delta_x": dx,
            "delta_y": dy
        })

    def _clean_ocr_text(self, text):
        if not text:
            return None
        text = text.strip().replace('\n', ' ').replace('\r', '')

        text = re.sub(r'[^\w\s\-_.]', '', text)

        if not text:
            return None

        alphanumeric_count = sum(c.isalnum() for c in text)
        total_chars = len(text)
        alphanumeric_ratio = alphanumeric_count / total_chars if total_chars > 0 else 0

        if alphanumeric_ratio < 0.5:
            return None

        return text if len(text) > 1 else None
    
    def _extract_text_near_click(self, x, y):
        """Extract text from screenshot near click location using OCR"""
        if not self.is_tracking:
            return None

        try:
            # Capture small area around the click
            left = max(0, x-100)
            top = max(0, y-50)
            right = x + 100
            bottom = y + 5

            screenshot = ImageGrab.grab(bbox=(left, top, right, bottom))

            from PIL import ImageEnhance, ImageFilter

            screenshot = screenshot.convert('L')

            enhancer = ImageEnhance.Contrast(screenshot)
            screenshot = enhancer.enhance(2.0)

            screenshot = screenshot.filter(ImageFilter.SHARPEN)

            screenshot = screenshot.resize(
                (screenshot.width * 2, screenshot.height * 2),
                Image.LANCZOS
            )

            ocr_configs = [
                '--psm 8',
                '--psm 7',
                '--psm 11',
                '--psm 13'
            ]
            best_text = None
            for config in ocr_configs:
                text = pytesseract.image_to_string(
                    screenshot, 
                    lang='eng',
                    config=config
                )
                cleaned_text = self._clean_ocr_text(text)

                if cleaned_text:
                    best_text = cleaned_text
                    break

            return best_text
        
        except Exception as e:
            print(f"OCR error: {e}")
            return None

    def _on_key_press(self, key):
        """Handle keyboard key press event"""
        try:
            key_str = key.char

            if key_str and ord(key_str) < 32:
                control_chars = {
                    1: 'Ctrl+A', 3: 'Ctrl+C', 6:'Ctrl+F', 22: 'Ctrl+V', 
                    24: 'Ctrl+X', 26: 'Ctrl+Z'
                }
                key_str = control_chars.get(ord(key_str))
        except AttributeError:
            key_str = str(key).replace("Key.", "")

        if key_str in ['ctrl_l', 'alt_l', 'shift_l', 'ctrl_r', 'alt_r', 'shift_r']:
            self.pressed_modifiers.add(key_str)
            return
        
        if self.pressed_modifiers:
            modifiers = []
            if any('ctrl' in m for m in self.pressed_modifiers):
                modifiers.append('Ctrl')

            if any('alt' in m for m in self.pressed_modifiers):
                modifiers.append('Alt')

            if any('shift' in m for m in self.pressed_modifiers):
                modifiers.append('Shift')

            """key_str = key.upper() if len(key) == 1 else key
            combo = "+".join(modifiers + [key_str])
            self._log_event("key_press", {
                "key": combo 
            })"""
            shortcut = f"{'+'.join(modifiers)} + {key_str}"

            common_shortcuts = {
                'Ctrl+A': 'Select All',
                'Ctrl+C': 'Copy',
                'Ctrl+V': 'Paste',
                'Ctrl+X': 'Cut',
                'Ctrl+Z': 'Undo',
                'Ctrl+Y': 'Redo',
                'Alt+Tab': 'Switch tab',
                'Ctrl+N': 'New',
                'Ctrl+O': 'Open'
            }
            shortcut_clean = shortcut.replace(' ', '')
            if shortcut_clean in common_shortcuts:
                action = common_shortcuts[shortcut]
                self._log_event("key_press",{
                    "key": f"{shortcut} {action}"
                })
            else:
                self._log_event("key_press", {
                    "key": shortcut
                })
            
            self.pressed_modifiers.clear()
            return

        if key_str:
            self._log_event("key_press", {
                "key": key_str.encode('ascii', errors='ignore').decode('ascii')
            })

    def _on_key_release(self, key):
        try:
            key_str = str(key).replace("Key.", "")
            if key_str in ['ctrl_l', 'alt_l', 'shift_l', 'ctrl_r', 'alt_r', 'shift_r']:
                self.pressed_modifiers.discard(key_str)
            
        except:
            pass

    def _save_events(self):
        """Save events to a JSON file"""
        if not self.events:
            return

        filename = f"events_{self.session_id}.json"
        filepath = self.output_dir/filename

        existing_events = []
        if filepath.exists():
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    existing_events = json.load(f)
            except:
                pass
        
        # Add all events to one list
        all_events = existing_events + self.events

        with open(filepath, "w", encoding="utf-8") as f:
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
            on_press=self._on_key_press,
            on_release=self._on_key_release        
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

    track_time = 60
    tracker = EventTracker()
    tracker.start()
    print(f"Tracking for {track_time} seconds")

    time.sleep(track_time)

    tracker.stop()

    print("Test complete")
    print("Check the file called event_date_time.json")