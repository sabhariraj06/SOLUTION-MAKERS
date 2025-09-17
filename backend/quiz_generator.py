import json
import os
import uuid
import datetime
from backend.ollama_client import ask_ollama
# Add this import at the top
from backend.youtube_processor import generate_quiz_from_youtube

# Add this function to the existing quiz_generator.py
def create_youtube_quiz(youtube_url, difficulty="medium", num_questions=5):
    """
    Create quiz from YouTube video
    """
    quiz_data, error = generate_quiz_from_youtube(youtube_url, difficulty, num_questions)
    
    if error:
        return None, error
    
    form_id = str(uuid.uuid4())[:12]
    
    base_url = "http://localhost:8501"
    share_url = f"{base_url}?quiz_id={form_id}"
    
    form_info = {
        "form_id": form_id,
        "title": quiz_data["quiz_title"],
        "questions": quiz_data["questions"],
        "quiz_url": f"/quiz/{form_id}",
        "share_url": share_url,
        "created_at": datetime.datetime.now().isoformat(),
        "is_shareable": True,
        "video_info": quiz_data.get("video_info", {})
    }
    
    os.makedirs("data/quizzes", exist_ok=True)
    with open(f"data/quizzes/quiz_{form_id}.json", "w") as f:
        json.dump(form_info, f, indent=2)
    
    return form_info, None

def generate_quiz(text, difficulty="medium", num_questions=5):
    """
    Generate quiz questions based on the PDF text content
    """
    try:
        # Limit number of questions to maximum 20
        num_questions = min(num_questions, 20)
        
        prompt = f"""
        IMPORTANT: Generate {num_questions} {difficulty}-level multiple choice questions based EXCLUSIVELY on the following text content.
        
        Text content to base questions on:
        {text[:4000]}
        
        Format your response as JSON with this exact structure:
        {{
            "quiz_title": "Quiz Based on Document Content",
            "questions": [
                {{
                    "question": "Specific question based on the text",
                    "options": {{
                        "a": "Option A that relates to text",
                        "b": "Option B that relates to text", 
                        "c": "Option C that relates to text",
                        "d": "Option D that relates to text"
                    }},
                    "correct_answer": "a",
                    "explanation": "Brief explanation referencing the specific text content"
                }}
            ]
        }}
        """
        
        response = ask_ollama(prompt)
        
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
            
            if 'questions' not in quiz_data or not isinstance(quiz_data['questions'], list):
                raise ValueError("Invalid quiz format")
                
            return quiz_data
            
        except (json.JSONDecodeError, ValueError) as e:
            print(f"JSON parsing failed: {e}")
            return create_quiz_from_text(text, num_questions, difficulty)
            
    except Exception as e:
        print(f"Error generating quiz: {e}")
        return create_fallback_quiz(num_questions)

def create_quiz_from_text(text, num_questions=5, difficulty="medium"):
    """Create quiz questions by analyzing the text content directly"""
    try:
        # Limit number of questions to maximum 20
        num_questions = min(num_questions, 20)
        
        prompt = f"Analyze this text and create {num_questions} {difficulty}-level multiple choice questions: {text[:3000]}"
        response = ask_ollama(prompt)
        
        try:
            if '```json' in response:
                json_str = response.split('```json')[1].split('```')[0].strip()
            else:
                json_str = response.strip()
            
            quiz_data = json.loads(json_str)
            return quiz_data
        except:
            return create_fallback_quiz(num_questions)
            
    except Exception as e:
        print(f"Error creating quiz from text: {e}")
        return create_fallback_quiz(num_questions)

def create_fallback_quiz(num_questions):
    """Create a simple fallback quiz if AI generation fails"""
    # Limit number of questions to maximum 20
    num_questions = min(num_questions, 20)
    
    questions = []
    for i in range(min(num_questions, 5)):
        questions.append({
            "question": f"Sample question {i+1} about document content?",
            "options": {
                "a": "Option A related to content",
                "b": "Option B related to content", 
                "c": "Option C related to content",
                "d": "Option D related to content"
            },
            "correct_answer": "a",
            "explanation": "This answer is correct based on the document content analysis."
        })
    
    return {
        "quiz_title": "Document Content Quiz",
        "questions": questions
    }

def create_quiz(quiz_data, form_title="Generated Quiz"):
    """Create a quiz with unique URL that opens in new tab"""
    form_id = str(uuid.uuid4())[:12]
    
    base_url = "http://localhost:8501"
    share_url = f"{base_url}?quiz_id={form_id}"
    
    form_info = {
        "form_id": form_id,
        "title": form_title,
        "questions": quiz_data["questions"],
        "quiz_url": f"/quiz/{form_id}",
        "share_url": share_url,
        "created_at": datetime.datetime.now().isoformat(),
        "is_shareable": True
    }
    
    os.makedirs("data/quizzes", exist_ok=True)
    with open(f"data/quizzes/quiz_{form_id}.json", "w") as f:
        json.dump(form_info, f, indent=2)
    
    return form_info

def generate_quiz_html(quiz_data):
    """
    Generate HTML content for the quiz page with auto-submit on malpractices
    """
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{quiz_data['title']} - Proctored Test</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }}
            
            .main-container {{
                display: flex;
                gap: 20px;
                max-width: 1400px;
                margin: 0 auto;
            }}
            
            .quiz-section {{
                flex: 3;
                background: white;
                padding: 30px;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            }}
            
            .proctor-section {{
                flex: 1;
                background: white;
                padding: 20px;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                min-width: 300px;
            }}
            
            .quiz-header {{
                text-align: center;
                margin-bottom: 30px;
                color: #333;
            }}
            
            .question {{
                margin-bottom: 25px;
                padding: 20px;
                border: 2px solid #e8e8e8;
                border-radius: 12px;
                background-color: #fafafa;
            }}
            
            .options label {{
                display: block;
                padding: 12px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                cursor: pointer;
                transition: all 0.3s ease;
                background: white;
                margin: 8px 0;
            }}
            
            .options label:hover {{
                border-color: #667eea;
                background-color: #f8f9ff;
            }}
            
            .submit-btn {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 15px 30px;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                font-size: 16px;
                font-weight: 600;
                margin: 20px auto;
                display: block;
            }}
            
            .video-container {{
                width: 100%;
                background: #000;
                border-radius: 10px;
                overflow: hidden;
                margin-bottom: 15px;
            }}
            
            #videoFeed {{
                width: 100%;
                height: 200px;
                object-fit: cover;
            }}
            
            .proctor-status {{
                text-align: center;
                padding: 10px;
                background: #4CAF50;
                color: white;
                border-radius: 8px;
                margin-bottom: 15px;
            }}
            
            .proctor-alerts {{
                background: #fff3cd;
                border: 1px solid #ffeaa7;
                border-radius: 8px;
                padding: 15px;
                margin-top: 15px;
            }}
            
            .alert-item {{
                padding: 8px;
                margin: 5px 0;
                background: #fff;
                border-radius: 5px;
                border-left: 4px solid #ff6b6b;
            }}
            
            .results {{
                display: none;
                margin-top: 30px;
                padding: 25px;
                background: white;
                border-radius: 15px;
                border: 2px solid #4CAF50;
            }}
            
            .malpractice-warning {{
                background: #ffebee;
                border: 2px solid #f44336;
                border-radius: 10px;
                padding: 20px;
                text-align: center;
                margin: 20px 0;
            }}
            
            @media (max-width: 1024px) {{
                .main-container {{
                    flex-direction: column;
                }}
                .proctor-section {{
                    order: -1;
                    margin-bottom: 20px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="main-container">
            <!-- Quiz Section -->
            <div class="quiz-section">
                <div class="quiz-header">
                    <h1>📝 {quiz_data['title']}</h1>
                    <p>Total Questions: {len(quiz_data['questions'])} | 🔒 Proctored Test</p>
                    <p style="color: #ff6b6b; font-weight: bold;">⚠️ 3 malpractices will auto-submit your test!</p>
                </div>
                
                <div id="malpracticeWarning" class="malpractice-warning" style="display: none;">
                    <h2>🚨 MALPRACTICE DETECTED</h2>
                    <p>Your test has been automatically submitted due to multiple malpractices.</p>
                </div>
                
                <form id="quizForm">
    """
    
    for i, question in enumerate(quiz_data["questions"]):
        html_content += f"""
                    <div class="question">
                        <h3>Q{i+1}: {question['question']}</h3>
                        <div class="options">
        """
        
        for option, text in question["options"].items():
            html_content += f"""
                            <label>
                                <input type="radio" name="q{i}" value="{option}" required>
                                {option.upper()}. {text}
                            </label>
            """
        
        html_content += """
                        </div>
                    </div>
        """
    
    correct_answers_js = []
    for i, question in enumerate(quiz_data["questions"]):
        correct_answers_js.append(f'{{q: "q{i}", correct: "{question["correct_answer"]}", explanation: `{question.get("explanation", "No explanation provided.")}`}}')
    
    html_content += f"""
                    <button type="button" class="submit-btn" onclick="submitQuiz()">
                        📤 Submit Answers
                    </button>
                </form>
                
                <div id="results" class="results">
                    <h2>📊 Quiz Results</h2>
                    <div id="scoreDisplay"></div>
                    <div id="detailedResults"></div>
                    
                    <button onclick="goBack()" style="margin-top: 20px; padding: 10px 20px; background: #666; color: white; border: none; border-radius: 5px; cursor: pointer;">
                        ← Return to StudyMate
                    </button>
                </div>
            </div>
            
            <!-- Proctor Section -->
            <div class="proctor-section">
                <h3>🎥 Live Proctor</h3>
                
                <div class="proctor-status">
                    🔒 Proctor Active | Malpractices: <span id="malpracticeCount">0/3</span>
                </div>
                
                <div class="video-container">
                    <video id="videoFeed" autoplay muted></video>
                </div>
                
                <div style="text-align: center; margin: 10px 0;">
                    <button onclick="toggleCamera()" style="padding: 8px 15px; background: #667eea; color: white; border: none; border-radius: 5px; cursor: pointer;">
                        📷 Toggle Camera
                    </button>
                </div>
                
                <div class="proctor-alerts">
                    <h4>⚠️ Proctor Alerts</h4>
                    <div id="alertsContainer">
                        <div class="alert-item">Starting proctor monitoring...</div>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            const correctAnswers = [{','.join(correct_answers_js)}];
            let stream = null;
            let malpracticeCount = 0;
            const MAX_MALPRACTICES = 3;
            let startTime = new Date();
            let tabActive = true;
            let testAutoSubmitted = false;
            
            // Initialize camera
            async function initCamera() {{
                try {{
                    stream = await navigator.mediaDevices.getUserMedia({{ 
                        video: {{ 
                            width: {{ ideal: 640 }},
                            height: {{ ideal: 480 }},
                            facingMode: "user" 
                        }},
                        audio: false 
                    }});
                    
                    const video = document.getElementById('videoFeed');
                    video.srcObject = stream;
                    document.getElementById('cameraStatus').textContent = 'Active';
                    
                    addAlert('Camera initialized successfully', 'success');
                    
                }} catch (error) {{
                    console.error('Camera error:', error);
                    document.getElementById('cameraStatus').textContent = 'Failed';
                    addAlert('Camera access denied or unavailable', 'error');
                }}
            }}
            
            function toggleCamera() {{
                const video = document.getElementById('videoFeed');
                if (video.srcObject) {{
                    video.srcObject.getTracks().forEach(track => track.stop());
                    video.srcObject = null;
                    document.getElementById('cameraStatus').textContent = 'Off';
                    addAlert('Camera turned off', 'warning');
                }} else {{
                    initCamera();
                }}
            }}
            
            // Proctor monitoring with browser event detection
            function startProctorMonitoring() {{
                // Detect tab visibility changes
                document.addEventListener('visibilitychange', handleVisibilityChange);
                
                // Detect copy attempts
                document.addEventListener('copy', handleCopyAttempt);
                
                // Detect right-click (context menu)
                document.addEventListener('contextmenu', handleRightClick);
                
                // Detect keyboard events for unusual patterns
                document.addEventListener('keydown', handleKeyPress);
                
                // Periodic checks
                setInterval(checkInactivity, 30000); // Check every 30 seconds
                
                addAlert('Proctor monitoring started', 'success');
            }}
            
            function handleVisibilityChange() {{
                if (document.hidden) {{
                    tabActive = false;
                    addMalpractice('Tab switched or minimized');
                }} else {{
                    tabActive = true;
                }}
            }}
            
            function handleCopyAttempt(e) {{
                addMalpractice('Copy attempt detected');
                e.preventDefault(); // Prevent copying
            }}
            
            function handleRightClick(e) {{
                addMalpractice('Right-click attempt detected');
                e.preventDefault(); // Prevent context menu
            }}
            
            function handleKeyPress(e) {{
                // Detect unusual key patterns (simplified)
                if (e.ctrlKey || e.metaKey) {{
                    if (e.key === 'c' || e.key === 'v') {{
                        addMalpractice('Keyboard shortcut attempt detected');
                    }}
                }}
            }}
            
            function checkInactivity() {{
                // Check if user is inactive (simplified)
                const now = new Date();
                const inactiveTime = (now - startTime) / 1000;
                
                if (inactiveTime > 60) {{ // 60 seconds of inactivity
                    addMalpractice('Inactivity detected');
                    startTime = now; // Reset timer
                }}
            }}
            
            function addMalpractice(message) {{
                malpracticeCount++;
                document.getElementById('malpracticeCount').textContent = malpracticeCount + '/3';
                
                addAlert(message + ' (Malpractice ' + malpracticeCount + '/3)', 'error');
                
                // Auto-submit if max malpractices reached
                if (malpracticeCount >= MAX_MALPRACTICES && !testAutoSubmitted) {{
                    testAutoSubmitted = true;
                    addAlert('MAXIMUM MALPRACTICES REACHED! Test auto-submitting...', 'error');
                    
                    // Show malpractice warning
                    document.getElementById('malpracticeWarning').style.display = 'block';
                    
                    // Auto-submit after short delay
                    setTimeout(() => {{
                        submitQuiz();
                    }}, 3000);
                }}
            }}
            
            function addAlert(message, type = 'info') {{
                const alertsContainer = document.getElementById('alertsContainer');
                const alert = document.createElement('div');
                alert.className = 'alert-item';
                alert.style.borderLeftColor = type === 'error' ? '#ff6b6b' : 
                                            type === 'warning' ? '#ffd93d' : 
                                            type === 'success' ? '#6bcb77' : '#4d96ff';
                
                const timestamp = new Date().toLocaleTimeString();
                alert.innerHTML = `<strong>[${{timestamp}}]</strong> ${{message}}`;
                
                alertsContainer.insertBefore(alert, alertsContainer.firstChild);
                
                // Keep only last 10 alerts
                if (alertsContainer.children.length > 10) {{
                    alertsContainer.removeChild(alertsContainer.lastChild);
                }}
            }}
            
            function submitQuiz() {{
                if (testAutoSubmitted) {{
                    document.getElementById('malpracticeWarning').style.display = 'block';
                }}
                
                const form = document.getElementById('quizForm');
                const results = document.getElementById('results');
                const scoreDisplay = document.getElementById('scoreDisplay');
                const detailedResults = document.getElementById('detailedResults');
                
                let score = 0;
                let total = {len(quiz_data["questions"])};
                
                // Check answers
                let resultsHTML = '';
                for (let i = 0; i < total; i++) {{
                    const userAnswer = document.querySelector(`input[name="q${{i}}"]:checked`);
                    const correctAnswer = correctAnswers.find(ca => ca.q === `q${{i}}`);
                    
                    if (userAnswer && userAnswer.value === correctAnswer.correct) {{
                        score++;
                        resultsHTML += `
                            <div style="margin: 15px 0; padding: 15px; border-left: 4px solid #4CAF50; background-color: #f8fff8;">
                                <strong>Q${{i+1}}:</strong> 
                                <span style="color: #4CAF50;">✓ Your answer: ${{userAnswer.value.toUpperCase()}} (Correct)</span><br>
                                <span style="color: #4CAF50; font-weight: bold;">Correct answer: ${{correctAnswer.correct.toUpperCase()}}</span><br>
                                <div style="color: #666; font-style: italic; margin-top: 8px;">${{correctAnswer.explanation}}</div>
                            </div>
                        `;
                    }} else {{
                        const userAns = userAnswer ? userAnswer.value : 'Not answered';
                        resultsHTML += `
                            <div style="margin: 15px 0; padding: 15px; border-left: 4px solid #f44336; background-color: #fff8f8;">
                                <strong>Q${{i+1}}:</strong> 
                                <span style="color: #f44336;">✗ Your answer: ${{userAns.toUpperCase()}} (Incorrect)</span><br>
                                <span style="color: #4CAF50; font-weight: bold;">Correct answer: ${{correctAnswer.correct.toUpperCase()}}</span><br>
                                <div style="color: #666; font-style: italic; margin-top: 8px;">${{correctAnswer.explanation}}</div>
                            </div>
                        `;
                    }}
                }}
                
                const percentage = Math.round((score / total) * 100);
                
                if (testAutoSubmitted) {{
                    scoreDisplay.innerHTML = `
                        <h3 style="color: #f44336;">🚨 TEST AUTO-SUBMITTED DUE TO MALPRACTICES</h3>
                        <h3>Score: ${{score}}/${{total}} (${{percentage}}%)</h3>
                        <p>${{getScoreMessage(percentage)}}</p>
                    `;
                }} else {{
                    scoreDisplay.innerHTML = `
                        <h3>Score: ${{score}}/${{total}} (${{percentage}}%)</h3>
                        <p>${{getScoreMessage(percentage)}}</p>
                    `;
                }}
                
                detailedResults.innerHTML = resultsHTML;
                results.style.display = 'block';
                form.style.display = 'none';
                
                // Stop camera after submission
                if (stream) {{
                    stream.getTracks().forEach(track => track.stop());
                }}
                
                if (!testAutoSubmitted) {{
                    addAlert('Test submitted successfully. Camera turned off.', 'success');
                }}
            }}
            
            function getScoreMessage(percentage) {{
                if (percentage >= 90) return '🎉 Excellent! Perfect score!';
                if (percentage >= 70) return '👍 Good job! Well done!';
                if (percentage >= 50) return '😊 Not bad! Keep practicing!';
                return '📚 Keep learning! You can do better!';
            }}
            
            function goBack() {{
                window.location.href = 'http://localhost:8501';
            }}
            
            // Initialize when page loads
            window.addEventListener('load', function() {{
                // Request camera access
                initCamera();
                // Start other proctor monitoring
                startProctorMonitoring();
            }});
        </script>
    </body>
    </html>
    """
    
    return html_content

def evaluate_quiz_responses(form_id, user_answers):
    """Evaluate quiz responses and provide results"""
    try:
        quiz_file = f"data/quizzes/quiz_{form_id}.json"
        if not os.path.exists(quiz_file):
            return None
            
        with open(quiz_file, "r") as f:
            quiz_data = json.load(f)
        
        results = {
            "total_questions": len(quiz_data["questions"]),
            "correct_answers": 0,
            "incorrect_answers": 0,
            "score_percentage": 0,
            "question_results": []
        }
        
        for i, question in enumerate(quiz_data["questions"]):
            user_answer = user_answers.get(f"q{i}", "").lower()
            correct_answer = question["correct_answer"].lower()
            
            is_correct = user_answer == correct_answer
            
            if is_correct:
                results["correct_answers"] += 1
            else:
                results["incorrect_answers"] += 1
            
            results["question_results"].append({
                "question": question["question"],
                "user_answer": user_answer,
                "correct_answer": correct_answer,
                "is_correct": is_correct,
                "explanation": question.get("explanation", "No explanation provided.")
            })
        
        if results["total_questions"] > 0:
            results["score_percentage"] = (results["correct_answers"] / results["total_questions"]) * 100
        
        return results
        
    except Exception as e:
        print(f"Error evaluating quiz: {e}")
        return None

def load_quiz(quiz_id):
    """Load a quiz by ID"""
    try:
        quiz_file = f"data/quizzes/quiz_{quiz_id}.json"
        if os.path.exists(quiz_file):
            with open(quiz_file, "r") as f:
                return json.load(f)
        return None
    except Exception as e:
        print(f"Error loading quiz: {e}")
        return None