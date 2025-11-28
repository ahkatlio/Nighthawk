import os
import re
import time
import tempfile
import threading
import asyncio
import subprocess
from typing import Optional
from pathlib import Path

try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False


class TTSService:
    
    def __init__(self, voice_model: str = 'en-US-AriaNeural'):
        self.enabled = False  # Default: OFF
        self.speech_rate = 0
        
        self.voice_models = {
            'en-US-AriaNeural': 'English (US) - Aria',
            'en-US-GuyNeural': 'English (US) - Guy',
            'en-GB-SoniaNeural': 'English (UK) - Sonia',
            'en-GB-RyanNeural': 'English (UK) - Ryan',
            'en-AU-NatashaNeural': 'English (AU) - Natasha',
            'en-AU-WilliamNeural': 'English (AU) - William',
            'en-CA-ClaraNeural': 'English (CA) - Clara',
            'en-CA-LiamNeural': 'English (CA) - Liam'
        }
        
        # Set default voice
        self.current_voice = voice_model if voice_model in self.voice_models else 'en-US-AriaNeural'
        
        self._lock = threading.Lock()
        self.is_speaking = False
        self.current_process = None
        self.should_stop = False
        self.chunk_queue = []
        self.current_thread = None
        
        self.temp_dir = tempfile.gettempdir()
        
        if not EDGE_TTS_AVAILABLE:
            print("[Warning] Edge-TTS not installed. Text-to-speech disabled.")
    
    def set_voice_model(self, voice_name: str):
        if not EDGE_TTS_AVAILABLE:
            return False
        
        try:
            if voice_name in self.voice_models:
                self.current_voice = voice_name
                print(f"[TTS] Voice changed to: {self.voice_models[voice_name]}")
                return True
            else:
                print(f"[TTS Error] Voice model '{voice_name}' not found")
                return False
        except Exception as e:
            print(f"[TTS Error] Failed to change voice: {e}")
            return False
    
    def set_enabled(self, enabled: bool):
        self.enabled = enabled
    
    def set_speech_rate(self, rate: int):
        self.speech_rate = max(-50, min(50, rate))
        print(f"[TTS] Speech rate set to: {self.speech_rate:+d}%")
    
    def is_enabled(self) -> bool:
        return self.enabled and EDGE_TTS_AVAILABLE
    
    def is_available(self) -> bool:
        return EDGE_TTS_AVAILABLE
    
    def stop_speech(self):
        with self._lock:
            self.should_stop = True
            
            if self.current_process:
                try:
                    print("[TTS] Stopping audio playback...")
                    self.current_process.terminate()
                    try:
                        self.current_process.wait(timeout=1)
                    except:
                        self.current_process.kill()
                        self.current_process.wait(timeout=1)
                    print("[TTS] Audio stopped successfully")
                except Exception as e:
                    print(f"[TTS Error] Failed to stop audio: {e}")
                finally:
                    self.current_process = None
            
            for chunk_file in self.chunk_queue:
                try:
                    if os.path.exists(chunk_file):
                        os.remove(chunk_file)
                except:
                    pass
            self.chunk_queue = []
            self.is_speaking = False
    
    def _clean_text_for_speech(self, text: str) -> str:
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        text = re.sub(r'\*(.+?)\*', r'\1', text)
        text = re.sub(r'`(.+?)`', r'\1', text)
        text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)
        text = re.sub(r'#+\s+', '', text)
        text = re.sub(r'[-•]\s+', '', text)
        
        text = re.sub(r'```[\s\S]*?```', '', text)
        
        text = re.sub(r'https?://\S+', '', text)
        
        text = re.sub(r'[^\x00-\x7F]+', '', text)
        
        text = ' '.join(text.split())
        
        return text.strip()
    
    def speak_text(self, text: str, blocking: bool = False):
        if not self.is_enabled():
            return
        
        clean_text = self._clean_text_for_speech(text)
        
        if not clean_text:
            return
        
        print(f"[TTS Debug] Original text length: {len(text)} chars")
        print(f"[TTS Debug] Cleaned text length: {len(clean_text)} chars")
        
        chunks = self._split_into_chunks(clean_text)
        print(f"[TTS Debug] Split into {len(chunks)} chunks")
        
        if blocking:
            self._speak_chunks_blocking(chunks)
        else:
            if self.is_speaking:
                self.stop_speech()
                time.sleep(0.1)
            
            thread = threading.Thread(target=self._speak_chunks_blocking, args=(chunks,), daemon=True)
            self.current_thread = thread
            thread.start()
    
    def _split_into_chunks(self, text: str) -> list:
        base_chunk_size = 200
        
        if self.speech_rate > 0:
            chunk_size = base_chunk_size + (self.speech_rate * 10)
        else:
            chunk_size = base_chunk_size
        
        print(f"[TTS Debug] Using chunk size: {chunk_size} chars (speech rate: {self.speech_rate:+d}%)")
        
        import re
        sentences = re.split(r'([.!?]+\s+)', text)
        
        chunks = []
        current_chunk = ""
        
        for i in range(0, len(sentences), 2):
            sentence = sentences[i]
            punctuation = sentences[i + 1] if i + 1 < len(sentences) else ""
            
            full_sentence = sentence + punctuation
            
            if len(current_chunk) + len(full_sentence) > chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = full_sentence
            else:
                current_chunk += full_sentence
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _speak_chunks_blocking(self, chunks: list):
        with self._lock:
            if self.is_speaking:
                return
            self.is_speaking = True
            self.should_stop = False
            self.chunk_queue = []
        
        try:
            import concurrent.futures
            
            def generate_chunk(i, chunk_text):
                if self.should_stop:
                    return None
                    
                print(f"[TTS Generator] Processing chunk {i+1}/{len(chunks)}")
                audio_file = os.path.join(self.temp_dir, f"nighthawk_tts_chunk_{i}_{os.getpid()}.mp3")
                
                if self.should_stop:
                    return None
                
                try:
                    asyncio.run(self._generate_speech(chunk_text, audio_file))
                    
                    if self.should_stop:
                        try:
                            os.remove(audio_file)
                        except:
                            pass
                        return None
                    print(f"[TTS Generator] Chunk {i+1} ready")
                    return (i, audio_file)
                except Exception as e:
                    if not self.should_stop:
                        print(f"[TTS Error] Failed to generate chunk {i+1}: {e}")
                    return None
            
            # Start generating all chunks in parallel
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                futures = []
                for i, chunk_text in enumerate(chunks):
                    if self.should_stop:
                        break
                    future = executor.submit(generate_chunk, i, chunk_text)
                    futures.append(future)
                
                played_count = 0
                for i in range(len(futures)):
                    if self.should_stop:
                        print(f"[TTS Player] Stopped at chunk {i+1}/{len(chunks)}")
                        break
                    
                    try:
                        result = futures[i].result(timeout=30)
                    except concurrent.futures.TimeoutError:
                        print(f"[TTS Error] Chunk {i+1} generation timeout")
                        break
                    
                    if result is None or self.should_stop:
                        break
                    
                    chunk_index, audio_file = result
                    
                    print(f"[TTS Player] Playing chunk {chunk_index+1}/{len(chunks)}")
                    self._play_audio_file(audio_file)
                    
                    if not self.should_stop:
                        played_count += 1
                    
                    try:
                        os.remove(audio_file)
                    except:
                        pass
                    
                    if self.should_stop:
                        break
            
            print(f"[TTS] Completed {played_count}/{len(chunks)} chunks")
            
        except Exception as e:
            print(f"[TTS Error] Chunk processing failed: {e}")
        
        finally:
            for i in range(len(chunks)):
                audio_file = os.path.join(self.temp_dir, f"nighthawk_tts_chunk_{i}_{os.getpid()}.mp3")
                try:
                    if os.path.exists(audio_file):
                        os.remove(audio_file)
                except:
                    pass
            
            with self._lock:
                self.is_speaking = False
                self.should_stop = False
                self.current_process = None
                self.current_thread = None
    
    def _play_audio_file(self, audio_file: str):
        if self.should_stop:
            return
            
        try:
            with self._lock:
                if self.should_stop:
                    return
                self.current_process = subprocess.Popen(
                    ['mpv', '--really-quiet', audio_file],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            
            while self.current_process.poll() is None:
                if self.should_stop:
                    try:
                        self.current_process.terminate()
                        self.current_process.wait(timeout=0.5)
                    except:
                        pass
                    break
                time.sleep(0.01)
                
        except FileNotFoundError:
            try:
                with self._lock:
                    if self.should_stop:
                        return
                    self.current_process = subprocess.Popen(
                        ['ffplay', '-nodisp', '-autoexit', '-hide_banner', '-loglevel', 'error', audio_file],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                
                while self.current_process.poll() is None:
                    if self.should_stop:
                        try:
                            self.current_process.terminate()
                            self.current_process.wait(timeout=0.5)
                        except:
                            pass
                        break
                    time.sleep(0.01)
                    
            except FileNotFoundError:
                print("[TTS Error] No audio player found. Install mpv or ffplay.")
    
    async def _generate_speech(self, text: str, output_file: str):
        rate_str = f"{self.speech_rate:+d}%"
        communicate = edge_tts.Communicate(text, self.current_voice, rate=rate_str)
        await communicate.save(output_file)
    
    def cleanup(self):
        self.stop_speech()


# Global TTS service instance
_tts_service: Optional[TTSService] = None

def get_tts_service() -> TTSService:
    global _tts_service
    if _tts_service is None:
        _tts_service = TTSService()
    return _tts_service
