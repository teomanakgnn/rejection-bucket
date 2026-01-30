import os
from flask import Flask, render_template, jsonify
from flask_cors import CORS
from imap_tools import MailBox, AND
import datetime
import time
from threading import Thread
import queue

app = Flask(__name__)
CORS(app)

EMAIL_USER = os.environ.get("EMAIL_USER")
EMAIL_PASS = os.environ.get("EMAIL_PASS")
IMAP_SERVER = "imap.gmail.com"

# Simple in-memory cache
cache = {"count": None, "timestamp": 0, "in_progress": False}
CACHE_DURATION = 120  # 2 minutes

def fetch_rejection_count_worker(result_queue):
    """Worker function to fetch count with timeout protection"""
    try:
       # Pass timeout to the MailBox constructor
        with MailBox(IMAP_SERVER, timeout=20).login(EMAIL_USER, EMAIL_PASS) as mailbox:
            try:
                available_folders = [f.name for f in mailbox.folder.list()]
                print(f"Available folders: {available_folders}")
                
                # Try to find the correct folder
                possible_folders = [
                    '[Gmail]/Tüm Postalar',
                    '[Gmail]/All Mail',
                    '[Gmail]/Tüm E-postalar',
                    'INBOX'
                ]
                
                target_folder = None
                for folder in possible_folders:
                    if folder in available_folders:
                        target_folder = folder
                        break
                
                if not target_folder:
                    for folder in available_folders:
                        if any(keyword in folder for keyword in ['All', 'Tüm', 'Tum', 'Postalar']):
                            target_folder = folder
                            break
                
                if not target_folder:
                    target_folder = 'INBOX'
                
                print(f"Using folder: {target_folder}")
                mailbox.folder.set(target_folder)
                
            except Exception as folder_error:
                print(f"Folder error: {folder_error}, using INBOX")
                mailbox.folder.set('INBOX')
            
            # Fetch emails with "unfortunately" - limit to 500 for performance
            msgs = mailbox.fetch(
                AND(text='unfortunately', date_gte=datetime.date.today() - datetime.timedelta(days=365)), 
                limit=500, 
                mark_seen=False
            )
            # Convert generator to list to get count
            count = len(list(msgs))
            
            result_queue.put({"success": True, "count": count})
            
    except Exception as e:
        print(f"Error in worker: {str(e)}")
        result_queue.put({"success": False, "error": str(e)})

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/count')
def get_rejection_count():
    global cache
    
    if not EMAIL_USER or not EMAIL_PASS:
        return jsonify({
            "success": False, 
            "error": "Credentials not set on server."
        })
    
    # Check cache
    current_time = time.time()
    if cache["count"] is not None and (current_time - cache["timestamp"]) < CACHE_DURATION:
        print("Returning cached result")
        return jsonify(cache["count"])
    
    # If already fetching, return cached or wait briefly
    if cache["in_progress"]:
        if cache["count"] is not None:
            return jsonify(cache["count"])
        return jsonify({"success": False, "error": "Already fetching, try again in a moment"})
    
    # Start fetch with timeout
    cache["in_progress"] = True
    result_queue = queue.Queue()
    
    worker_thread = Thread(target=fetch_rejection_count_worker, args=(result_queue,))
    worker_thread.daemon = True
    worker_thread.start()
    
    # Wait up to 25 seconds for result
    try:
        result = result_queue.get(timeout=25)
        cache["count"] = result
        cache["timestamp"] = current_time
        cache["in_progress"] = False
        return jsonify(result)
    except queue.Empty:
        cache["in_progress"] = False
        print("Request timed out")
        # Return old cache if available
        if cache["count"] is not None:
            return jsonify(cache["count"])
        return jsonify({"success": False, "error": "Request timed out - please try again"})

@app.route('/api/folders')
def list_folders():
    """Debug endpoint to see available folders"""
    if not EMAIL_USER or not EMAIL_PASS:
        return jsonify({"success": False, "error": "Credentials not set"})
    
    try:
        with MailBox(IMAP_SERVER, timeout=15).login(EMAIL_USER, EMAIL_PASS) as mailbox:
            folders = [f.name for f in mailbox.folder.list()]
            return jsonify({"success": True, "folders": folders})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    app.run(debug=True)