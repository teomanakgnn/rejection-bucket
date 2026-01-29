import os
from flask import Flask, render_template, jsonify
from flask_cors import CORS
from imap_tools import MailBox, AND

app = Flask(__name__)
CORS(app)

EMAIL_USER = os.environ.get("EMAIL_USER")
EMAIL_PASS = os.environ.get("EMAIL_PASS")
IMAP_SERVER = "imap.gmail.com"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/count')
def get_rejection_count():
    if not EMAIL_USER or not EMAIL_PASS:
        return jsonify({
            "success": False, 
            "error": "Credentials not set on server."
        })

    try:
        with MailBox(IMAP_SERVER).login(EMAIL_USER, EMAIL_PASS) as mailbox:
            
            # Önce hangi klasörlerin var olduğunu kontrol et
            try:
                # Muhtemel klasör isimleri (dil ayarına göre değişir)
                possible_folders = [
                    '[Gmail]/All Mail',      # İngilizce
                    '[Gmail]/Tüm E-postalar', # Türkçe
                    '[Gmail]/Tum E-postalar',
                    'INBOX'                   # Fallback
                ]
                
                # Mevcut klasörleri listele
                available_folders = [f.name for f in mailbox.folder.list()]
                print(f"Available folders: {available_folders}")
                
                # Uygun klasörü bul
                target_folder = None
                for folder in possible_folders:
                    if folder in available_folders:
                        target_folder = folder
                        break
                
                # Eğer hiçbiri yoksa, tüm klasörleri ara
                if not target_folder:
                    # Gmail'deki tüm klasörlerde 'All' veya 'Tüm' içeren klasörü bul
                    for folder in available_folders:
                        if 'All' in folder or 'Tüm' in folder or 'Tum' in folder:
                            target_folder = folder
                            break
                
                # Hala bulunamadıysa INBOX kullan
                if not target_folder:
                    target_folder = 'INBOX'
                
                print(f"Using folder: {target_folder}")
                mailbox.folder.set(target_folder)
                
            except Exception as folder_error:
                print(f"Folder error: {folder_error}, using INBOX")
                # Klasör ayarlanamadıysa INBOX kullan
                mailbox.folder.set('INBOX')
            
            # "unfortunately" içeren mailleri say
            msgs = mailbox.fetch(AND(text='unfortunately'))
            count = sum(1 for _ in msgs)
            
            return jsonify({"success": True, "count": count})
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# Klasörleri görmek için debug endpoint ekle
@app.route('/api/folders')
def list_folders():
    if not EMAIL_USER or not EMAIL_PASS:
        return jsonify({"success": False, "error": "Credentials not set"})
    
    try:
        with MailBox(IMAP_SERVER).login(EMAIL_USER, EMAIL_PASS) as mailbox:
            folders = [f.name for f in mailbox.folder.list()]
            return jsonify({"success": True, "folders": folders})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    app.run(debug=True)