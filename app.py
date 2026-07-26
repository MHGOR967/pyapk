import os
import zipfile
import subprocess
import threading
import logging
from flask import Flask, request, send_file, render_template_string
import telebot

logging.basicConfig(level=logging.INFO)

# توكن البوت الخاص بك يا فخم
BOT_TOKEN = '8737255406:AAEFenbZDgNzz5yX9QLVMdstx2nb6WBftKw'
bot = telebot.TeleBot(BOT_TOKEN)

app = Flask(__name__)

UPLOAD_FOLDER = 'temp'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

BASE_APK = 'wahm.apk'
KEYSTORE = 'release.jks'
KEY_ALIAS = 'mykey'
KEY_PASS = 'password123'

# صفحة ويب رئيسية للتأكد من عمل السيرفر واستقبال طلبات Keep-Alive
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>منصة API توقيع وَهْم - fokhm.com</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen flex items-center justify-center p-4">
    <div class="max-w-md w-full bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-2xl text-center">
        <h1 class="text-2xl font-bold text-amber-400 mb-2">منصة API fokhm.com</h1>
        <p class="text-sm text-slate-400">نظام الـ API لتوقيع وحقن تطبيق وَهْم يعمل بكفاءة تامة ومتصل بالبوت.</p>
        <div class="mt-4 inline-block bg-amber-500/10 text-amber-400 border border-amber-500/20 px-4 py-2 rounded-xl text-xs">
            API Status: Online & Ready 🚀
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

# نقطة نهاية الـ API التي يستدعيها البوت أو أي واجهة خارجية
@app.route('/api/generate', methods=['POST'])
def api_generate():
    data = request.json or request.form
    token_text = data.get('token')
    user_id = data.get('user_id')

    if not token_text or not user_id:
        return {"error": "الرجاء إرسال التوكن والأيدي"}, 400

    if not os.path.exists(BASE_APK):
        return {"error": "ملف التطبيق الأساسي غير موجود على السيرفر"}, 500

    modified_apk = os.path.join(UPLOAD_FOLDER, f'wahm_modified_{user_id}.apk')
    aligned_apk = os.path.join(UPLOAD_FOLDER, f'wahm_aligned_{user_id}.apk')
    signed_apk = os.path.join(UPLOAD_FOLDER, f'wahm_signed_{user_id}.apk')

    try:
        for f in [modified_apk, aligned_apk, signed_apk]:
            if os.path.exists(f):
                os.remove(f)

        os.system(f"cp {BASE_APK} {modified_apk}")

        target_token = 'assets/token.txt'
        target_id = 'assets/id.txt'
        temp_zip = os.path.join(UPLOAD_FOLDER, f'temp_{user_id}.zip')

        with zipfile.ZipFile(modified_apk, 'r') as zin:
            with zipfile.ZipFile(temp_zip, 'w') as zout:
                token_exists = False
                id_exists = False
                
                for item in zin.infolist():
                    if item.filename.startswith('META-INF/'):
                        continue
                    if item.filename == target_token:
                        token_exists = True
                        zout.writestr(item, token_text.encode('utf-8'))
                    elif item.filename == target_id:
                        id_exists = True
                        zout.writestr(item, str(user_id).encode('utf-8'))
                    else:
                        zout.writestr(item, zin.read(item.filename))
                
                if not token_exists:
                    zout.writestr(target_token, token_text.encode('utf-8'))
                if not id_exists:
                    zout.writestr(target_id, str(user_id).encode('utf-8'))

        os.replace(temp_zip, modified_apk)

        # المحاذاة والتوقيع بأحدث المعايير
        subprocess.run(['zipalign', '-v', '-p', '4', modified_apk, aligned_apk], check=True)

        global KEYSTORE
        if not os.path.exists(KEYSTORE):
            subprocess.run([
                'keytool', '-genkey', '-v',
                '-keystore', KEYSTORE,
                '-alias', KEY_ALIAS,
                '-keyalg', 'RSA',
                '-keysize', '2048',
                '-validity', '10000',
                '-storepass', KEY_PASS,
                '-keypass', KEY_PASS,
                '-dname', 'CN=Fokhm, OU=Dev, O=Fokhm, L=Riyadh, S=Riyadh, C=SA'
            ], check=True)

        sign_cmd = [
            'apksigner', 'sign',
            '--ks', KEYSTORE,
            '--ks-pass', f'pass:{KEY_PASS}',
            '--min-sdk-version', '21',
            '--v2-signing-enabled', 'true',
            '--v3-signing-enabled', 'true',
            '--in', aligned_apk,
            '--out', signed_apk
        ]
        
        result = subprocess.run(sign_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            return {"error": f"فشل التوقيع: {result.stderr}"}, 500

        return send_file(signed_apk, as_attachment=True, download_name='wahm_customized.apk')

    except Exception as e:
        return {"error": str(e)}, 500

# --- قسم تليجرام بوت ---
waiting_for_token = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = telebot.types.InlineKeyboardMarkup()
    btn = telebot.types.InlineKeyboardButton("🚀 صناعة وتوقيع التطبيق", callback_data="make_app")
    markup.add(btn)
    
    bot.reply_to(
        message,
        "أهلاً بك يا فخم في بوت منصة **fokhm.com** لحقن التوكن والايدي وتوقيع تطبيق **وهم** عبر الـ API.\n\nاضغط على الزر أدناه للبدء:",
        parse_mode="Markdown",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "make_app")
def callback_query(call):
    waiting_for_token[call.from_user.id] = True
    bot.answer_callback_query(call.id)
    bot.send_message(
        call.message.chat.id,
        "أرسل الآن **التوكن** المطلوب حقنه في التطبيق:",
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda message: waiting_for_token.get(message.from_user.id, False))
def handle_token(message):
    user_id = message.from_user.id
    token_text = message.text.strip()
    waiting_for_token[user_id] = False

    msg = bot.reply_to(message, "⏳ جاري إرسال الطلب إلى سيرفر API fokhm.com لمعالجة التطبيق وتوقيعه، انتظر قليلاً...")

    try:
        # بناء الرابط المحلي للسيرفر أو رابط مشروعك على Render
        # بما أن البوت والسيرفر على نفس التطبيق، نقدر نستدعي الـ API محلياً أو عبر الدومين
        port = os.environ.get('PORT', 5000)
        api_url = f"http://127.0.0.1:{port}/api/generate"
        
        import requests
        response = requests.post(api_url, json={"token": token_text, "user_id": user_id}, timeout=180)

        if response.status_code == 200:
            output_path = os.path.join(UPLOAD_FOLDER, f'wahm_final_{user_id}.apk')
            with open(output_path, 'wb') as f:
                f.write(response.content)

            with open(output_path, 'rb') as apk_file:
                bot.send_document(
                    message.chat.id,
                    apk_file,
                    caption="✅ تم توليد وتوقيع التطبيق بنجاح عبر الـ API ليعمل على أحدث أجهزة أندرويد!",
                    visible_file_name="wahm_customized.apk"
                )
            bot.delete_message(message.chat.id, msg.message_id)
        else:
            err_msg = response.json().get('error', 'خطأ غير معروف')
            bot.edit_message_text(f"❌ حدث خطأ من السيرفر: {err_msg}", message.chat.id, msg.message_id)

    except Exception as e:
        bot.edit_message_text(f"❌ حدث خطأ أثناء الاتصال بالـ API: {str(e)}", message.chat.id, msg.message_id)

def run_bot():
    logging.info("بدء تشغيل استقبال البوت المتصل بالـ API...")
    bot.infinity_polling(skip_pending=True)

if __name__ == '__main__':
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

