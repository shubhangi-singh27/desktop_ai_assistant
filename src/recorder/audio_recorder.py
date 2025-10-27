import sounddevice as sd
import numpy as np
import wave
import threading
from datetime import datetime
from pathlib import Path
from faster_whisper import WhisperModel

class AudioRecorder:
    """Record audio from mic and transcribe with Whisper"""

    def __init__(self, output_dir="data/audio", sample_rate=16000):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.sample_rate = sample_rate
        self.chunk_duration = 10
        self.chunk_size = int(self.sample_rate*self.chunk_duration)

        # Control flags
        self.is_recording = False
        self.recording_thread = None
        self.frames = []

        print("Loading Whisper model...")
        self.whisper_model = WhisperModel("tiny", device="cpu", compute_type="int8")
        print("Whisper model loaded!")

    def _audio_callback(self, indata, frames, time, status):
        """Function called for each audio chunk"""

        if status:
            print(f"Audio status: {status}")

        self.frames.append(indata.copy())

    def _save_audio_chunk(self, audio_data, filename):
        try:
            audio_data = (audio_data*32767).astype(np.int16)

            print(f"DEBUG: Saving to {filename}")
            print(f"DEBIG: Audio data shape: {audio_data.shape}")

            with wave.open(str(filename), "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(self.sample_rate)
                wf.writeframes(audio_data.tobytes())
            
            print("DEBUG: File saved successfully")
            return filename
        except Exception as e:
            print(f"Error saving audio: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _transcribe_audio(self, audio_file):
        try:
            segments, info = self.whisper_model.transcribe(
                str(audio_file),
                language="en",
                beam_size=5
            )

            text = " ".join([segment.text for segment in segments])
            return text.strip()

        except Exception as e:
            print(f"Error transcribing: {e}")
            return None

    def _recording_loop(self):
        print("Audio recording started...")

        chunk_count = 0
        while self.is_recording:
            while len(self.frames) < self.chunk_size/512:
                if not self.is_recording:
                    return
                threading.Event().wait(0.1)

            chunk_frames = self.frames
            self.frames = []

            audio_data = np.concatenate(chunk_frames, axis=0)
            audio_data = audio_data.flatten()

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            audio_file = self.output_dir/f"audio_{timestamp}.wav"
            self._save_audio_chunk(audio_data, audio_file)

            print(f"Saved audio chunk {chunk_count + 1}: {audio_file}")

            threading.Thread(
                target = self._process_transcription,
                args = (audio_file,),
                daemon = True
            ).start()

            chunk_count += 1
        
        print("Audio recording stopped!")

    def _process_transcription(self, audio_file):
        print(f"Transcribing {audio_file.name}...")

        transcript = self._transcribe_audio(audio_file)

        if transcript:
            print(f"Transcript: {transcript}")

            import json
            transcript_file = self.output_dir/f"transcript_{audio_file.stem}.json"
            transcript_data = {
                "audio_file": str(audio_file),
                "transcript": transcript,
                "timestamp": datetime.now().isoformat()
            }
            with open(transcript_file, 'w', encoding='utf-8') as f:
                json.dump(transcript_data, f, indent=2)
            
            print(f"Saved transcript to {transcript_file}")
        else:
            print("No speech detected")

    def start(self):
        if self.is_recording:
            print("recording is already running.")
            return
        
        self.is_recording = True
        self.frames = []

        self.stream = sd.InputStream(
            samplerate = self.sample_rate,
            channels = 1,
            callback = self._audio_callback
        )
        self.stream.start()

        self.recording_thread = threading.Thread(target=self._recording_loop, daemon=True)
        self.recording_thread.start()

        print("Audio recording started!")

    def stop(self):
        if not self.is_recording:
            print("Recording is not running!")

        self.is_recording = False

        if self.stream:
            self.stream.stop()
            self.stream.close()

        if self.recording_thread:
            self.recording_thread.join(timeout=5)

        print("Audio recording stopped!")

if __name__ == "__main__":
    print("Audio recorder started")
    print("Make sure your microphone is working")

    recorder = AudioRecorder()

    recorder.start()

    print("Recording for 15 seconds...")
    print("Speak into your microphone")
    import time
    time.sleep(15)

    recorder.stop()

    print("Test complete")
    print("Check 'data/audio' folder for audio files.")