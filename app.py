from flask import Flask
import threading
import os

app = Flask('')

@app.route('/')
def home():
    print("🤖 Bot is active and running 24/7!")
    return "🤖 Auto Netlify File Host Bot by Tamim is Running!"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

def keep_alive():
    t = threading.Thread(target=run)
    t.start()
    