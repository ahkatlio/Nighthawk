"""
Text-to-Speech service using Edge-TTS
Provides audio output for AI responses in Nighthawk TUI
"""

import os
import re
import time
import tempfile
import threading
import asyncio
import subprocess
from typing import Optional
from pathlib import Path

# Try importing edge-tts
try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False


class TTSService:
    """Text-to-Speech service using Edge-TTS (Microsoft Edge voices)"""
    
    def __init__(self, voice_model: str = 'en-US-AriaNeural'):
        self.enabled = False  # Default: OFF
        self.speech_rate = 0  # Default: normal speed (-50 to +50)
        
        # Voice models for edge-tts
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
        
        # Thread safety
        self._lock = threading.Lock()
        self.is_speaking = False
        self.current_process = None
        self.should_stop = False  # Flag to stop all chunks
        self.chunk_queue = []  # Queue of audio chunks to play
        self.current_thread = None  # Track the speaking thread
        
        # Temp directory for audio files
        self.temp_dir = tempfile.gettempdir()
        
        if not EDGE_TTS_AVAILABLE:
            print("[Warning] Edge-TTS not installed. Text-to-speech disabled.")
    
    def set_voice_model(self, voice_name: str):
        """Change the voice model"""
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
        """Enable or disable TTS"""
        self.enabled = enabled
    
    def set_speech_rate(self, rate: int):
        """Set speech rate (-50 to +50, 0 is normal)"""
        self.speech_rate = max(-50, min(50, rate))
        print(f"[TTS] Speech rate set to: {self.speech_rate:+d}%")
    
    def is_enabled(self) -> bool:
        """Check if TTS is enabled"""
        return self.enabled and EDGE_TTS_AVAILABLE
    
    def is_available(self) -> bool:
        """Check if TTS is available (installed and initialized)"""
        return EDGE_TTS_AVAILABLE
    
    def stop_speech(self):
        """Stop current speech playback and all queued chunks"""
        with self._lock:
            self.should_stop = True  # Signal to stop processing chunks
            
            if self.current_process:
                try:
                    print("[TTS] Stopping audio playback...")
                    self.current_process.terminate()
                    try:
                        self.current_process.wait(timeout=1)
                    except:
                        # If terminate didn't work, force kill
                        self.current_process.kill()
                        self.current_process.wait(timeout=1)
                    print("[TTS] Audio stopped successfully")
                except Exception as e:
                    print(f"[TTS Error] Failed to stop audio: {e}")
                finally:
                    self.current_process = None
            
            # Clear chunk queue
            for chunk_file in self.chunk_queue:
                try:
                    if os.path.exists(chunk_file):
                        os.remove(chunk_file)
                except:
                    pass
            self.chunk_queue = []
            self.is_speaking = False
    
    def _clean_text_for_speech(self, text: str) -> str:
        """Clean markdown and special characters from text"""
        # Remove markdown formatting
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)  # Bold
        text = re.sub(r'\*(.+?)\*', r'\1', text)  # Italic
        text = re.sub(r'`(.+?)`', r'\1', text)  # Code
        text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)  # Links
        text = re.sub(r'#+\s+', '', text)  # Headers
        text = re.sub(r'[-•]\s+', '', text)  # Bullet points
        
        # Remove code blocks
        text = re.sub(r'```[\s\S]*?```', '', text)
        
        # Remove URLs
        text = re.sub(r'https?://\S+', '', text)
        
        # Remove emojis and special Unicode characters
        text = re.sub(r'[^\x00-\x7F]+', '', text)
        
        # Clean up whitespace
        text = ' '.join(text.split())
        
        return text.strip()
    
    def speak_text(self, text: str, blocking: bool = False):
        """
        Convert text to speech and play it
        
        Args:
            text: Text to speak (markdown will be cleaned)
            blocking: If True, wait for speech to complete
        """
        if not self.is_enabled():
            return
        
        # Clean text
        clean_text = self._clean_text_for_speech(text)
        
        if not clean_text:
            return
        
        # Debug: Log text length
        print(f"[TTS Debug] Original text length: {len(text)} chars")
        print(f"[TTS Debug] Cleaned text length: {len(clean_text)} chars")
        
        # Split text into chunks (sentences or by length)
        chunks = self._split_into_chunks(clean_text)
        print(f"[TTS Debug] Split into {len(chunks)} chunks")
        
        if blocking:
            self._speak_chunks_blocking(chunks)
        else:
            # Stop any existing speech first
            if self.is_speaking:
                self.stop_speech()
                time.sleep(0.1)  # Brief pause to ensure cleanup
            
            # Run in background thread
            thread = threading.Thread(target=self._speak_chunks_blocking, args=(chunks,), daemon=True)
            self.current_thread = thread
            thread.start()
    
    def _split_into_chunks(self, text: str) -> list:
        """Split text into manageable chunks for streaming playback"""
        # Adjust chunk size based on speech rate
        # Base chunk size increased to avoid gaps
        base_chunk_size = 200  
        
        if self.speech_rate > 0:
            # For faster speech, increase chunk size even more
            chunk_size = base_chunk_size + (self.speech_rate * 10)
        else:
            # For slower or normal speech, use base size
            chunk_size = base_chunk_size
        
        print(f"[TTS Debug] Using chunk size: {chunk_size} chars (speech rate: {self.speech_rate:+d}%)")
        
        # Split by sentences (period, question mark, exclamation)
        import re
        sentences = re.split(r'([.!?]+\s+)', text)
        
        chunks = []
        current_chunk = ""
        
        for i in range(0, len(sentences), 2):
            sentence = sentences[i]
            punctuation = sentences[i + 1] if i + 1 < len(sentences) else ""
            
            # Combine sentence with its punctuation
            full_sentence = sentence + punctuation
            
            # If adding this sentence exceeds chunk_size, save chunk and start new one
            if len(current_chunk) + len(full_sentence) > chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = full_sentence
            else:
                current_chunk += full_sentence
        
        # Add remaining text
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _speak_chunks_blocking(self, chunks: list):
        """Generate and play audio chunks with parallel generation"""
        with self._lock:
            if self.is_speaking:
                return
            self.is_speaking = True
            self.should_stop = False
            self.chunk_queue = []
        
        try:
            import concurrent.futures
            
            # Producer: Generate all chunks in parallel
            def generate_chunk(i, chunk_text):
                # Check multiple times for responsiveness
                if self.should_stop:
                    return None
                    
                print(f"[TTS Generator] Processing chunk {i+1}/{len(chunks)}")
                audio_file = os.path.join(self.temp_dir, f"nighthawk_tts_chunk_{i}_{os.getpid()}.mp3")
                
                if self.should_stop:  # Check before generation
                    return None
                
                try:
                    asyncio.run(self._generate_speech(chunk_text, audio_file))
                    
                    if self.should_stop:  # Check immediately after generation
                        try:
                            os.remove(audio_file)
                        except:
                            pass
                        return None
                    print(f"[TTS Generator] Chunk {i+1} ready")
                    return (i, audio_file)
                except Exception as e:
                    if not self.should_stop:  # Only log if not intentionally stopped
                        print(f"[TTS Error] Failed to generate chunk {i+1}: {e}")
                    return None
            
            # Start generating all chunks in parallel
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                # Submit all generation tasks
                futures = []
                for i, chunk_text in enumerate(chunks):
                    if self.should_stop:
                        break
                    future = executor.submit(generate_chunk, i, chunk_text)
                    futures.append(future)
                
                # Consumer: Play chunks as they become ready (in order)
                played_count = 0
                for i in range(len(futures)):
                    if self.should_stop:
                        print(f"[TTS Player] Stopped at chunk {i+1}/{len(chunks)}")
                        break
                    
                    # Wait for chunk i to be ready
                    try:
                        result = futures[i].result(timeout=30)  # Add timeout
                    except concurrent.futures.TimeoutError:
                        print(f"[TTS Error] Chunk {i+1} generation timeout")
                        break
                    
                    if result is None or self.should_stop:
                        break
                    
                    chunk_index, audio_file = result
                    
                    # Play this chunk
                    print(f"[TTS Player] Playing chunk {chunk_index+1}/{len(chunks)}")
                    self._play_audio_file(audio_file)
                    
                    if not self.should_stop:
                        played_count += 1
                    
                    # Clean up this chunk
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
            # Clean up any remaining generated files
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
        """Play a single audio file and wait for completion"""
        if self.should_stop:
            return
            
        try:
            with self._lock:
                if self.should_stop:  # Double-check after acquiring lock
                    return
                self.current_process = subprocess.Popen(
                    ['mpv', '--really-quiet', audio_file],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            
            # Wait outside the lock so stop_speech can terminate it
            while self.current_process.poll() is None:
                if self.should_stop:
                    try:
                        self.current_process.terminate()
                        self.current_process.wait(timeout=0.5)
                    except:
                        pass
                    break
                time.sleep(0.01)  # Check every 10ms for faster response
                
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
                    time.sleep(0.01)  # Check every 10ms for faster response
                    
            except FileNotFoundError:
                print("[TTS Error] No audio player found. Install mpv or ffplay.")
    
    async def _generate_speech(self, text: str, output_file: str):
        """Generate speech using edge-tts asynchronously with user-defined speed"""
        # Convert speech_rate (-50 to +50) to edge-tts format
        rate_str = f"{self.speech_rate:+d}%"
        communicate = edge_tts.Communicate(text, self.current_voice, rate=rate_str)
        await communicate.save(output_file)
    
    def cleanup(self):
        """Clean up resources"""
        self.stop_speech()


# Global TTS service instance
_tts_service: Optional[TTSService] = None

def get_tts_service() -> TTSService:
    """Get or create global TTS service instance"""
    global _tts_service
    if _tts_service is None:
        _tts_service = TTSService()
    return _tts_service
