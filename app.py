import os
from flask import Flask, render_template, jsonify
from flask_cors import CORS
from imap_tools import MailBox, AND

app = Flask(__name__)
CORS(app)

# Environment variables (GitHub'a şifre atmamak için sunucu ayarlarından çekeceğiz)
EMAIL_USER = os.environ.get("teomanakgn84@gmail.com")
EMAIL_PASS = os.environ.get("yrwuyyrwryngyokg")
IMAP_SERVER = "imap.gmail.com"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/count')
def get_rejection_count():
    if not EMAIL_USER or not EMAIL_PASS:
        return jsonify({"success": False, "error": "Credentials not set on server."})

# app.py içindeki ilgili kısmı bul ve şununla değiştir:

    try:
        # Connect to Gmail
        with MailBox(IMAP_SERVER).login(EMAIL_USER, EMAIL_PASS) as mailbox:
            
            # --- YENİ EKLENEN SATIR: Sadece Inbox değil, Tüm Postaları seç ---
            mailbox.folder.set('[Gmail]/All Mail') 
            # ------------------------------------------------------------------

            # SEARCH: All emails containing "unfortunately"
            msgs = mailbox.fetch(AND(text='unfortunately'))
            count = sum(1 for _ in msgs)
            
            return jsonify({"success": True, "count": count})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    # Local development
    app.run(debug=True)