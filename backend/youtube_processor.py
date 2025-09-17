import yt_dlp
import whisper
import tempfile
import os
import re
import json
import time
from backend.ollama_client import ask_ollama

class YouTubeProcessor:
    def __init__(self):
        self.model = None
    
    def load_whisper_model(self):
        """Load the Whisper model for speech recognition"""
        try:
            self.model = whisper.load_model("base")
            return True
        except Exception as e:
            print(f"Error loading Whisper model: {e}")
            return False
    
    def is_valid_youtube_url(self, url):
        """Check if the URL is a valid YouTube URL"""
        youtube_regex = (
            r'(https?://)?(www\.)?'
            r'(youtube|youtu|youtube-nocookie)\.(com|be)/'
            r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
        )
        return re.match(youtube_regex, url) is not None
    
    def download_audio(self, youtube_url):
        """Download audio from YouTube video with better error handling"""
        try:
            # Create temporary directory for audio
            temp_dir = tempfile.mkdtemp()
            temp_audio_path = os.path.join(temp_dir, 'audio.mp3')
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'outtmpl': temp_audio_path.replace('.mp3', ''),
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Try to get info first to validate URL
                info = ydl.extract_info(youtube_url, download=False)
                
                # Check if video is available
                if not info:
                    raise Exception("Video not available")
                
                # Check duration limit (15 minutes)
                if info.get('duration', 0) > 900:
                    raise Exception("Video too long (max 15 minutes)")
                
                # Download the audio
                ydl.download([youtube_url])
                
                # Check if file was created
                if not os.path.exists(temp_audio_path):
                    # Try to find the actual file name
                    for file in os.listdir(temp_dir):
                        if file.endswith('.mp3'):
                            temp_audio_path = os.path.join(temp_dir, file)
                            break
                
                if os.path.exists(temp_audio_path):
                    return temp_audio_path
                else:
                    raise Exception("Audio file not created")
                
        except Exception as e:
            print(f"Error downloading audio: {e}")
            # Clean up temporary directory
            try:
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
            except:
                pass
            return None
    
    def transcribe_audio(self, audio_path):
        """Transcribe audio to text using Whisper"""
        try:
            if not self.model:
                if not self.load_whisper_model():
                    return None
            
            result = self.model.transcribe(audio_path)
            return result['text']
            
        except Exception as e:
            print(f"Error transcribing audio: {e}")
            return None
    
    def get_video_info(self, youtube_url):
        """Get video information with better error handling"""
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=False)
                
                if not info:
                    return None
                
                return {
                    'title': info.get('title', 'Unknown Title'),
                    'duration': info.get('duration', 0),
                    'upload_date': info.get('upload_date', ''),
                    'view_count': info.get('view_count', 0),
                    'thumbnail': info.get('thumbnail', ''),
                    'description': info.get('description', '')[:200] + '...' if info.get('description') else 'No description'
                }
                
        except Exception as e:
            print(f"Error getting video info: {e}")
            return None
    
    def get_video_transcript_alternative(self, youtube_url):
        """Alternative method to get video content without downloading"""
        try:
            # Try to get video description and metadata
            video_info = self.get_video_info(youtube_url)
            if not video_info:
                return None, "Could not get video information"
            
            # Use video title and description as fallback
            content = f"""
            Video Title: {video_info['title']}
            Description: {video_info['description']}
            Duration: {video_info['duration']} seconds
            """
            
            return content, None
            
        except Exception as e:
            return None, f"Alternative method failed: {str(e)}"
    
    def process_youtube_video(self, youtube_url):
        """
        Process YouTube video and return transcript with multiple fallbacks
        """
        try:
            # Validate YouTube URL
            if not self.is_valid_youtube_url(youtube_url):
                return None, "Invalid YouTube URL"
            
            # Get video info first
            video_info = self.get_video_info(youtube_url)
            if not video_info:
                return None, "Could not get video information"
            
            # Check if video is too long (more than 15 minutes)
            if video_info['duration'] > 900:  # 15 minutes in seconds
                return None, "Video too long. Please use videos under 15 minutes."
            
            # Try to download and transcribe audio
            audio_path = self.download_audio(youtube_url)
            if not audio_path:
                # If audio download fails, try alternative method
                print("Audio download failed. Using video metadata as fallback...")
                transcript, error = self.get_video_transcript_alternative(youtube_url)
                if error:
                    return None, error
                return transcript, video_info
            
            # Transcribe audio
            transcript = self.transcribe_audio(audio_path)
            
            # Clean up temporary files
            try:
                import shutil
                shutil.rmtree(os.path.dirname(audio_path), ignore_errors=True)
            except:
                pass
            
            if not transcript:
                # If transcription fails, try alternative method
                print("Transcription failed. Using video metadata as fallback...")
                transcript, error = self.get_video_transcript_alternative(youtube_url)
                if error:
                    return None, error
                return transcript, video_info
            
            return transcript, video_info
            
        except Exception as e:
            print(f"Error processing YouTube video: {e}")
            return None, f"Processing error: {str(e)}"

# Singleton instance
youtube_processor = YouTubeProcessor()

def generate_quiz_from_youtube(youtube_url, difficulty="medium", num_questions=5):
    """
    Generate quiz from YouTube video content with multiple fallbacks
    """
    try:
        # Process YouTube video
        transcript, video_info = youtube_processor.process_youtube_video(youtube_url)
        
        if not transcript:
            return None, video_info  # video_info contains error message
        
        # Generate quiz using Ollama
        prompt = f"""
        Based on the following YouTube video content, generate {num_questions} {difficulty}-level multiple choice questions.
        
        Video Title: {video_info['title']}
        Video Duration: {video_info['duration']} seconds
        Video Description: {video_info.get('description', 'No description available')}
        
        Video Content:
        {transcript[:3000]}  # Limit content length
        
        Create engaging multiple choice questions that test understanding of the video content.
        Make sure questions are specifically related to the video and not generic.
        
        Format your response as JSON with this structure:
        {{
            "quiz_title": "Quiz based on: {video_info['title'][:50]}",
            "video_info": {{
                "title": "{video_info['title']}",
                "duration": {video_info['duration']},
                "url": "{youtube_url}",
                "thumbnail": "{video_info.get('thumbnail', '')}"
            }},
            "questions": [
                {{
                    "question": "Specific question about video content",
                    "options": {{
                        "a": "Option A related to video",
                        "b": "Option B related to video", 
                        "c": "Option C related to video",
                        "d": "Option D related to video"
                    }},
                    "correct_answer": "a",
                    "explanation": "Explanation based on video content"
                }}
            ]
        }}
        """
        
        response = ask_ollama(prompt)
        
        # Try to extract JSON from the response
        try:
            if '```json' in response:
                json_str = response.split('```json')[1].split('```')[0].strip()
            elif '```' in response:
                json_str = response.split('```')[1].split('```')[0].strip()
            else:
                json_str = response.strip()
                json_start = json_str.find('{')
                if json_start != -1:
                    json_str = json_str[json_start:]
                json_end = json_str.rfind('}')
                if json_end != -1:
                    json_str = json_str[:json_end+1]
            
            quiz_data = json.loads(json_str)
            return quiz_data, None
            
        except (json.JSONDecodeError, ValueError) as e:
            print(f"JSON parsing failed: {e}")
            print(f"Raw response: {response}")
            return None, "Failed to generate quiz from video content"
            
    except Exception as e:
        print(f"Error generating quiz from YouTube: {e}")
        return None, f"Error: {str(e)}"