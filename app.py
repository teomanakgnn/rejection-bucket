import os
from flask import Flask, render_template, jsonify
from flask_cors import CORS
from imap_tools import MailBox, AND

app = Flask(__name__)
CORS(app)

# Environment variables - DEĞİŞTİRİLDİ
EMAIL_USER = os.environ.get("EMAIL_USER")
EMAIL_PASS = os.environ.get("EMAIL_PASS")
IMAP_SERVER = "imap.gmail.com"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/count')
def get_rejection_count():
    # Debug için log ekle
    print(f"EMAIL_USER: {EMAIL_USER}")
    print(f"EMAIL_PASS: {'*' * len(EMAIL_PASS) if EMAIL_PASS else 'None'}")
    
    if not EMAIL_USER or not EMAIL_PASS:
        return jsonify({
            "success": False, 
            "error": "Credentials not set on server. Please check environment variables."
        })

    try:
        # Gmail'e bağlan
        with MailBox(IMAP_SERVER).login(EMAIL_USER, EMAIL_PASS) as mailbox:
            # Tüm mailleri tara
            mailbox.folder.set('[Gmail]/All Mail')
            
            # "unfortunately" içeren mailleri say
            msgs = mailbox.fetch(AND(text='unfortunately'))
            count = sum(1 for _ in msgs)
            
            return jsonify({"success": True, "count": count})
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    app.run(debug=True)