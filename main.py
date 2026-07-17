import requests
import time
import json
import re
import os
import threading
from flask import Flask

# =========================
# 🌐 FLASK SERVER (Keep Alive)
# =========================
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is Running smoothly ✅"

def run_server():
    # পোর্ট ১০০০০ এ সার্ভার চালু হবে যা হোস্টিং সার্ভারের জন্য উপযোগী
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# =========================
# 🔐 API SETTINGS (Updated from Screenshot)
# =========================
API_URL = "http://147.135.212.197/crapi/had/viewstats" 
TOKEN = "QlFYRElXQkU0blFEWoNkVYOMlmiHaJmIQ1aIWmeAU2lghYdoRneLdXg=" 

# রেকর্ড কাউন্ট ৫০ করে দিলাম যাতে একসাথে অনেক OTP আসলে মিস না হয়
RECORDS_COUNT = 50 

# =========================
# 🤖 TELEGRAM SETTINGS
# =========================
BOT_TOKEN = "8655501706:AAEc6gs8cudby9TQaym_WrHwCaQIHuOTtx0"
CHAT_ID = -1003530245573

# =========================
# 📁 STORAGE (মেসেজ ডুপ্লিকেট রোধের জন্য)
# =========================
FILE = "sent.txt"
if os.path.exists(FILE):
    with open(FILE, "r") as f:
        sent_messages = set(f.read().splitlines())
else:
    sent_messages = set()

def save_message(uid):
    with open(FILE, "a") as f:
        f.write(uid + "\n")

# =========================
# 📱 MASK NUMBER
# =========================
def mask_number(num):
    if num and len(str(num)) >= 8:
        n = str(num)
        return n[:4] + "XXXX" + n[-4:]
    return num

# =========================
# 📤 SEND FUNCTION
# =========================
def send(msg_text, number, sender_id):
    try:
        # মেসেজ থেকে ৪-৯ ডিজিটের OTP খুঁজে বের করা
        otp = re.findall(r"\b\d{4,9}\b", msg_text)
        otp_text = otp[0] if otp else "N/A"
        masked = mask_number(number)  

        text = f"""
📩 <b>NEW OTP RECEIVED</b>

👤 Sender: <b>{sender_id}</b>
📱 Number: <b>{masked}</b>

🔐 OTP: <code>{otp_text}</code>

📝 Full Msg: 
<i>{msg_text}</i>
"""
        buttons = {  
            "inline_keyboard": [  
                [{"text": "📋 Copy OTP", "callback_data": f"copy_{otp_text}"}],  
                [  
                    {"text": "📢 CHANNEL", "url": "https://t.me/OX_OFFLINE_EARNING"},  
                    {"text": "🌐 NUMBER CHANNEL", "url": "https://t.me/OX_OFFLINE_CHANNEL"}  
                ]  
            ]  
        }  

        requests.post(  
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",  
            data={  
                "chat_id": CHAT_ID,  
                "text": text,  
                "parse_mode": "HTML",  
                "reply_markup": json.dumps(buttons)  
            },  
            timeout=10  
        )  
    except Exception as e:  
        print("Send Error:", e)

# =========================
# 🔄 BOT LOOP (Auto-Check)
# =========================
def bot_loop():
    global sent_messages
    print("Bot loop started...")
    while True:
        try:
            # API থেকে ডাটা রিকোয়েস্ট করা
            params = {
                "token": TOKEN,
                "records": RECORDS_COUNT
            }
            
            res = requests.get(API_URL, params=params, timeout=15)
            result = res.json()

            if result.get("status") == "success" and "data" in result:  
                # ডাটা উল্টো করে নেওয়া হচ্ছে (পুরানো থেকে নতুনের দিকে প্রসেস করবে)
                messages = result["data"][::-1] 

                for sms in messages:  
                    msg_content = sms.get("message") 
                    number = sms.get("num")
                    dt = sms.get("dt")
                    sender_id = sms.get("cli")

                    # প্রতিটি মেসেজের জন্য একটি ইউনিক আইডি
                    unique_id = f"{dt}_{number}" 

                    if unique_id not in sent_messages:  
                        send(msg_content, number, sender_id)  
                        sent_messages.add(unique_id)  
                        save_message(unique_id)
                        
                        # একসাথে অনেক ওটিপি আসলে যাতে টেলিগ্রাম ব্লক না করে, 
                        # তাই প্রতিটি মেসেজের পর ০.৫ সেকেন্ড বিরতি।
                        time.sleep(0.5) 

        except Exception as e:  
            print("Main Loop Error:", e)  

        # ৫ সেকেন্ড পর পর নতুন মেসেজ চেক করবে
        time.sleep(5) 

# =========================
# 🚀 RUN BOT & SERVER
# =========================
if __name__ == "__main__":
    # বোটের লুপটিকে আলাদা থ্রেডে চালানো হচ্ছে
    threading.Thread(target=bot_loop, daemon=True).start()
    # মেইন থ্রেডে ফ্লাস্ক সার্ভার চালানো হচ্ছে
    run_server()
