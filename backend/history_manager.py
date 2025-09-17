import json
import os
import datetime

HISTORY_FILE = "data/search_history.json"

def load_history():
    """Load search history from file"""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    return []

def save_history(history):
    """Save search history to file"""
    try:
        os.makedirs("data", exist_ok=True)
        with open(HISTORY_FILE, 'w') as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        print(f"Error saving history: {e}")

def add_to_history(question, answer, pdf_name=""):
    """Add a new item to search history and return updated history"""
    history = load_history()
    
    # Create new history item
    history_item = {
        "question": question,
        "answer": answer,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "pdf_name": pdf_name
    }
    
    # Add to history (avoid exact duplicates)
    if not any(
        item['question'] == question and 
        item['answer'] == answer and 
        item['pdf_name'] == pdf_name 
        for item in history
    ):
        history.append(history_item)
        
        # Keep only last 100 items to prevent file from growing too large
        history = history[-100:]
        
        # Save to file
        save_history(history)
    
    return history

def clear_history():
    """Clear all search history"""
    if os.path.exists(HISTORY_FILE):
        os.remove(HISTORY_FILE)
    return []

def get_history_by_pdf(pdf_name):
    """Get history filtered by PDF name"""
    history = load_history()
    return [item for item in history if item['pdf_name'] == pdf_name]