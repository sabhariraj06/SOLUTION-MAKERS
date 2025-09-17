import os
import streamlit as st
import datetime
from streamlit.components.v1 import html
from backend.pdf_loader import extract_text_from_pdf, chunk_text
from backend.embeddings import build_faiss_index
from backend.retriever import retrieve_top_k
from backend.ollama_client import ask_ollama
from backend.translator import translate_text, LANGUAGE_OPTIONS
from backend.history_manager import load_history, add_to_history
from backend.quiz_generator import generate_quiz, create_quiz, evaluate_quiz_responses, load_quiz, generate_quiz_html, create_youtube_quiz
from backend.youtube_processor import youtube_processor

st.set_page_config(page_title="StudyMate - AI PDF Q&A", layout="wide")

# ----------------- Check for Quiz URL Parameter -----------------
query_params = st.query_params
if 'quiz_id' in query_params:
    quiz_id = query_params['quiz_id']
    quiz_data = load_quiz(quiz_id)
    if quiz_data:
        st.title("📝 StudyMate Quiz")
        html_content = generate_quiz_html(quiz_data)
        html(html_content, height=800, scrolling=True)
        
        if st.button("← Back to StudyMate"):
            st.query_params.clear()
            st.rerun()
    else:
        st.error("Quiz not found! The link may be invalid or expired.")
        if st.button("← Back to StudyMate"):
            st.query_params.clear()
            st.rerun()
    
    st.stop()

# ----------------- Main Application -----------------
st.title("📘 StudyMate: AI-Powered PDF Q&A System")

# ----------------- Setup Directories -----------------
UPLOAD_DIR = "data/uploads"
QUIZ_DIR = "data/quizzes"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(QUIZ_DIR, exist_ok=True)

if os.path.isfile(UPLOAD_DIR):
    os.remove(UPLOAD_DIR)

# ----------------- Initialize Session State -----------------
if 'show_translator' not in st.session_state:
    st.session_state.show_translator = False
if 'translated_text' not in st.session_state:
    st.session_state.translated_text = ""
if 'text_to_translate' not in st.session_state:
    st.session_state.text_to_translate = ""
if 'show_history' not in st.session_state:
    st.session_state.show_history = False
if 'show_quiz' not in st.session_state:
    st.session_state.show_quiz = False
if 'current_quiz' not in st.session_state:
    st.session_state.current_quiz = None
if 'quiz_results' not in st.session_state:
    st.session_state.quiz_results = None
if 'search_history' not in st.session_state:
    st.session_state.search_history = load_history()
if 'current_pdf' not in st.session_state:
    st.session_state.current_pdf = None
if 'pdf_text' not in st.session_state:
    st.session_state.pdf_text = ""
if 'proctor_report' not in st.session_state:
    st.session_state.proctor_report = None
if 'youtube_url' not in st.session_state:
    st.session_state.youtube_url = ""
if 'youtube_quiz' not in st.session_state:
    st.session_state.youtube_quiz = None
if 'youtube_error' not in st.session_state:
    st.session_state.youtube_error = None

# ----------------- Sidebar for Navigation -----------------
with st.sidebar:
    st.title("🔧 Navigation")
    
    if st.button("🏠 Main Page", use_container_width=True):
        st.session_state.show_translator = False
        st.session_state.show_history = False
        st.session_state.show_quiz = False
        st.rerun()
    
    if st.button("🌐 Translator", use_container_width=True):
        st.session_state.show_translator = True
        st.session_state.show_history = False
        st.session_state.show_quiz = False
        st.rerun()
    
    if st.button("📜 History", use_container_width=True):
        st.session_state.show_history = True
        st.session_state.show_translator = False
        st.session_state.show_quiz = False
        st.rerun()
    
    if st.button("📝 Quiz Generator", use_container_width=True):
        st.session_state.show_quiz = True
        st.session_state.show_translator = False
        st.session_state.show_history = False
        st.rerun()
    
    st.markdown("---")
    
    if st.session_state.current_pdf:
        st.info(f"**Current PDF:** {st.session_state.current_pdf}")

# ----------------- Quiz Generator Page -----------------
if st.session_state.show_quiz:
    st.header("📝 Quiz Generator")
    
    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("❌ Close Quiz", use_container_width=True):
            st.session_state.show_quiz = False
            st.rerun()
    
    # Create tabs for PDF and YouTube quiz generation
    tab1, tab2 = st.tabs(["📄 PDF Quiz", "🎥 YouTube Video Quiz"])
    
    with tab1:
        if not st.session_state.pdf_text:
            st.warning("Please upload a PDF first to generate quizzes.")
        else:
            st.info("Generate a quiz based on your uploaded PDF content")
            
            # Quiz configuration
            col1, col2 = st.columns(2)
            with col1:
                difficulty = st.selectbox(
                    "Difficulty Level",
                    ["easy", "medium", "hard"],
                    index=1,
                    key="pdf_difficulty"
                )
            with col2:
                num_questions = st.slider("Number of Questions", 3, 20, 5, key="pdf_num_questions")
            
            if st.button("🎯 Generate Quiz", type="primary", key="generate_pdf_quiz"):
                with st.spinner("Generating quiz questions..."):
                    quiz_data = generate_quiz(st.session_state.pdf_text, difficulty, num_questions)
                    if quiz_data and 'questions' in quiz_data:
                        form_info = create_quiz(quiz_data, f"Quiz - {st.session_state.current_pdf}")
                        st.session_state.current_quiz = form_info
                        st.success("✅ Quiz generated successfully!")
                    else:
                        st.error("❌ Failed to generate quiz. Please try again.")
            
            # Display quiz if available
            if st.session_state.current_quiz:
                st.markdown("---")
                st.subheader("📋 Your Generated Quiz")
                
                st.markdown(f"""
                **Quiz Title:** {st.session_state.current_quiz['title']}
                
                **Number of Questions:** {len(st.session_state.current_quiz['questions'])}
                
                **Difficulty Level:** {difficulty.capitalize()}
                """)
                
                if st.button("🎯 Open Quiz in New Tab", type="primary", key="open_quiz_btn"):
                    js = f"window.open('{st.session_state.current_quiz['share_url']}', '_blank')"
                    st.components.v1.html(f"<script>{js}</script>", height=0)
                    st.success("Quiz opened in new tab! ✅")
                
                st.markdown("### 📋 Shareable Link")
                st.code(st.session_state.current_quiz['share_url'], language="text")
                
                if st.button("📋 Copy Link to Clipboard", key="copy_link_btn"):
                    st.success("Link copied to clipboard! ✅")
                
                st.markdown("""
                ---
                ### 📝 How to use:
                1. Click **"Open Quiz in New Tab"** to take the quiz yourself
                2. **Copy the link** and share it with others
                3. Anyone with the link can take the quiz
                4. Results are automatically evaluated
                """)
                
                with st.expander("👁️ Preview Questions (Optional)"):
                    for i, question in enumerate(st.session_state.current_quiz["questions"]):
                        st.markdown(f"**Q{i+1}: {question['question']}**")
                        for option, text in question["options"].items():
                            st.markdown(f"- {option.upper()}. {text}")
                        st.markdown("---")
    
    with tab2:
        st.subheader("🎥 Generate Quiz from YouTube Video")
        
        st.info("""
        **Create quizzes from YouTube videos!**
        - Paste a YouTube URL
        - Video will be analyzed (max 15 minutes)
        - Quiz questions generated from video content
        """)
        
        youtube_url = st.text_input(
            "YouTube Video URL:",
            value=st.session_state.youtube_url,
            placeholder="https://www.youtube.com/watch?v=...",
            key="youtube_url_input"
        )
        
        if youtube_url:
            st.session_state.youtube_url = youtube_url
            
            # Get video info for preview
            video_info = youtube_processor.get_video_info(youtube_url)
            
            if video_info:
                col1, col2 = st.columns(2)
                with col1:
                    st.image(video_info['thumbnail'], width=200)
                with col2:
                    st.write(f"**Title:** {video_info['title']}")
                    minutes, seconds = divmod(video_info['duration'], 60)
                    st.write(f"**Duration:** {minutes}m {seconds}s")
                    st.write(f"**Views:** {video_info['view_count']:,}")
            
            # Quiz configuration
            col1, col2 = st.columns(2)
            with col1:
                yt_difficulty = st.selectbox(
                    "Difficulty Level",
                    ["easy", "medium", "hard"],
                    index=1,
                    key="yt_difficulty"
                )
            with col2:
                yt_num_questions = st.slider(
                    "Number of Questions", 
                    3, 20, 5,
                    key="yt_num_questions"
                )
            
            if st.button("🎬 Generate Quiz from Video", type="primary", key="generate_yt_quiz"):
                with st.spinner("Analyzing video and generating quiz..."):
                    quiz_data, error = create_youtube_quiz(
                        youtube_url, 
                        yt_difficulty, 
                        yt_num_questions
                    )
                    
                    if error:
                        st.session_state.youtube_error = error
                        st.session_state.youtube_quiz = None
                        st.error(f"❌ Error: {error}")
                    else:
                        st.session_state.youtube_quiz = quiz_data
                        st.session_state.youtube_error = None
                        st.success("✅ YouTube quiz generated successfully!")
        
        # Display YouTube quiz if available
        if st.session_state.youtube_error:
            st.error(f"❌ Error: {st.session_state.youtube_error}")
        
        if st.session_state.youtube_quiz:
            st.markdown("---")
            st.subheader("📋 Your YouTube Video Quiz")
            
            st.markdown(f"""
            **Quiz Title:** {st.session_state.youtube_quiz['title']}
            
            **Number of Questions:** {len(st.session_state.youtube_quiz['questions'])}
            
            **Difficulty Level:** {yt_difficulty.capitalize()}
            
            **Video Source:** [Watch Original Video]({st.session_state.youtube_url})
            """)
            
            if st.button("🎯 Open YouTube Quiz in New Tab", type="primary", key="open_yt_quiz_btn"):
                js = f"window.open('{st.session_state.youtube_quiz['share_url']}', '_blank')"
                st.components.v1.html(f"<script>{js}</script>", height=0)
                st.success("YouTube quiz opened in new tab! ✅")
            
            st.markdown("### 📋 Shareable Link")
            st.code(st.session_state.youtube_quiz['share_url'], language="text")
            
            if st.button("📋 Copy YouTube Quiz Link", key="copy_yt_link_btn"):
                st.success("YouTube quiz link copied to clipboard! ✅")
            
            st.markdown("""
            ---
            ### 📝 How to use:
            1. Click **"Open YouTube Quiz in New Tab"** to take the quiz
            2. **Copy the link** and share it with others
            3. Anyone with the link can take the video-based quiz
            4. Results are automatically evaluated
            """)
            
            # Preview of questions
            with st.expander("👁️ Preview YouTube Quiz Questions"):
                for i, question in enumerate(st.session_state.youtube_quiz["questions"]):
                    st.markdown(f"**Q{i+1}: {question['question']}**")
                    for option, text in question["options"].items():
                        st.markdown(f"- {option.upper()}. {text}")
                    st.markdown("---")

# ----------------- Main Page Layout -----------------
elif not st.session_state.show_history:
    if st.session_state.show_translator:
        main_col, translator_col = st.columns([2, 1])
    else:
        main_col = st.container()
        translator_col = None
    
    with main_col:
        if 'reuse_question' in st.session_state:
            query = st.text_input("💡 Ask a question about your PDF:", value=st.session_state.reuse_question)
            del st.session_state.reuse_question
        else:
            query = st.text_input("💡 Ask a question about your PDF:")

        uploaded_file = st.file_uploader("📂 Upload a PDF", type="pdf")

        if uploaded_file:
            file_path = os.path.join(UPLOAD_DIR, uploaded_file.name)

            with open(file_path, "wb") as f:
                f.write(uploaded_file.read())

            st.success(f"✅ PDF uploaded successfully: {uploaded_file.name}")
            st.session_state.current_pdf = uploaded_file.name

            try:
                text = extract_text_from_pdf(file_path)
                st.session_state.pdf_text = text
                chunks = chunk_text(text)
                index, _ = build_faiss_index(chunks)

                st.info("📄 PDF processed into chunks. You can now ask questions!")
                
                if st.button("🎯 Generate Quiz from this PDF", key="generate_quiz_btn"):
                    st.session_state.show_quiz = True
                    st.rerun()

                if query:
                    context = retrieve_top_k(query, index, chunks)
                    prompt = f"Answer the question based on the context:\n\n{context}\n\nQuestion: {query}"
                    answer = ask_ollama(prompt)

                    st.session_state.search_history = add_to_history(
                        question=query, 
                        answer=answer, 
                        pdf_name=uploaded_file.name
                    )

                    st.subheader("📝 Answer:")
                    st.write(answer)
                    
                    if st.button("🌐 Send to Translator", key="send_to_translator"):
                        st.session_state.text_to_translate = answer
                        st.session_state.show_translator = True
                        st.rerun()

                    st.subheader("📚 Sources from PDF:")
                    for i, c in enumerate(context, 1):
                        st.markdown(f"**{i}.** {c[:300]}...")

            except Exception as e:
                st.error(f"❌ Error while processing PDF: {e}")
        else:
            st.info("📁 Please upload a PDF file to get started.")

    if st.session_state.show_translator and translator_col:
        with translator_col:
            st.markdown("---")
            st.subheader("🌐 Translator")
            
            text_input = st.text_area(
                "Text to translate:", 
                value=st.session_state.text_to_translate,
                height=150,
                help="Paste text here to translate",
                key="translator_input"
            )
            
            target_lang = st.selectbox(
                "Translate to:",
                options=list(LANGUAGE_OPTIONS.keys()),
                format_func=lambda x: f"{LANGUAGE_OPTIONS[x]['flag']} {LANGUAGE_OPTIONS[x]['name']}",
                key="target_lang"
            )
            
            if st.button("Translate", type="primary", key="translate_btn"):
                if text_input.strip():
                    with st.spinner("Translating..."):
                        translated = translate_text(text_input, target_lang)
                        st.session_state.translated_text = translated
                else:
                    st.warning("Please enter some text to translate")
            
            if st.session_state.translated_text:
                st.markdown("**Translation Result:**")
                st.info(st.session_state.translated_text)
                
                if st.button("📋 Copy Translation", key="copy_btn"):
                    st.code(st.session_state.translated_text, language='text')
                    st.success("Translation copied to code block above. You can now copy it from there.")
            
            if st.button("❌ Close Translator", key="close_translator"):
                st.session_state.show_translator = False
                st.rerun()

# ----------------- History Page -----------------
else:
    st.header("📜 Search History")
    
    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("❌ Close History", use_container_width=True):
            st.session_state.show_history = False
            st.rerun()
    
    if not st.session_state.search_history:
        st.info("No search history yet. Ask some questions to build your history!")
    else:
        current_pdf_history = [
            item for item in st.session_state.search_history 
            if st.session_state.current_pdf and item['pdf_name'] == st.session_state.current_pdf
        ]
        all_history = st.session_state.search_history
        
        show_all = st.toggle("Show all PDFs history", value=True)
        display_history = all_history if show_all else current_pdf_history
        
        if not display_history:
            st.info("No history for this PDF yet.")
        else:
            for i, history_item in enumerate(reversed(display_history)):
                with st.expander(f"📄 {history_item['pdf_name']} - {history_item['timestamp']}"):
                    st.markdown(f"**Question:** {history_item['question']}")
                    st.markdown(f"**Answer:** {history_item['answer']}")
                    st.markdown(f"**PDF:** {history_item['pdf_name']}")
                    st.markdown(f"**Date:** {history_item['timestamp']}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"🔁 Use this question", key=f"reuse_{i}"):
                            st.session_state.reuse_question = history_item['question']
                            st.session_state.show_history = False
                            st.rerun()
                    with col2:
                        if st.button(f"🌐 Translate answer", key=f"translate_{i}"):
                            st.session_state.text_to_translate = history_item['answer']
                            st.session_state.show_translator = True
                            st.session_state.show_history = False
                            st.rerun()

# ----------------- Footer -----------------
st.markdown("---")
st.markdown("### 🚀 StudyMate - AI-Powered Learning Assistant")
st.markdown("""
**Features:**
- 📄 PDF-based Q&A
- 🎥 YouTube video quiz generation
- 🌐 Multi-language translation
- 📜 Search history
- 🔒 Proctored quizzes
- 📝 Auto-grading system
""")