import os
import zipfile
import subprocess
import threading
import logging
from flask import Flask, render_template_string
import telebot

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = '8737255406:AAEFenbZDgNzz5yX9QLVMdstx2nb6WBftKw'
bot = telebot.TeleBot(BOT_TOKEN)

app = Flask(__name__)

UPLOAD_FOLDER = 'temp'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

BASE_APK = 'wahm.apk'
KEYSTORE = 'release.jks'
KEY_ALIAS = 'mykey'
KEY_PASS = 'password123'

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>خدمة بوت توقيع وحقن وَهْم - fokhm.com</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen flex items-center justify-center p-4">
    <div class="max-w-md w-full bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-2xl text-center">
        <h1 class="text-2xl font-bold text-amber-400 mb-2">منصة fokhm.com لتوقيع وَهْم</h1>
        <p class="text-sm text-slate-400">السيرفر والبوت يعملان مباشرة وبدون وسيط لضمان الاستجابة الفورية.</p>
        <div class="mt-4 inline-block bg-amber-500/10 text-amber-400 border border-amber-500/20 px-4 py-2 rounded-xl text-xs">
            Status: Direct Process Online 🚀
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

waiting_for_token = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    logging.info(f"تم استقبال أمر /start بنجاح من المستخدم: {message.from_user.id}")
    markup = telebot.types.InlineKeyboardMarkup()
    btn = telebot.types.InlineKeyboardButton("🚀 صناعة وتوقيع التطبيق", callback_data="make_app")
    markup.add(btn)
    
    bot.reply_to(
        message,
        "أهلاً بك يا فخم في بوت منصة **fokhm.com** لحقن التوكن والايدي وتوقيع تطبيق **وهم** بأحدث معايير أندرويد.\n\nاضغط على الزر أدناه للبدء:",
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

    msg = bot.reply_to(message, "⏳ جاري جلب الأيدي الخاص بك، حقن الملفات (Token & ID)، ومحاذاة وتوقيع التطبيق، انتظر قليلاً...")

    modified_apk = os.path.join(UPLOAD_FOLDER, f'wahm_modified_{user_id}.apk')
    aligned_apk = os.path.join(UPLOAD_FOLDER, f'wahm_aligned_{user_id}.apk')
    signed_apk = os.path.join(UPLOAD_FOLDER, f'wahm_signed_{user_id}.apk')

    try:
        for f in [modified_apk, aligned_apk, signed_apk]:
            if os.path.exists(f):
                os.remove(f)

        if not os.path.exists(BASE_APK):
            bot.edit_message_text("❌ خطأ: ملف التطبيق الأساسي (wahm.apk) غير مرفوع على السيرفر!", message.chat.id, msg.message_id)
            return

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
            bot.edit_message_text(f"❌ فشل التوقيع عبر apksigner: {result.stderr}", message.chat.id, msg.message_id)
            return

        with open(signed_apk, 'rb') as apk_file:
            bot.send_document(
                message.chat.id,
                apk_file,
                caption="✅ تم حقن التوكن والايدي وتوقيع نسختك بنجاح لتتوافق مع أحدث جوالات أندرويد!",
                visible_file_name="wahm_customized.apk"
            )
        bot.delete_message(message.chat.id, msg.message_id)

    except Exception as e:
        bot.edit_message_text(f"❌ حدث خطأ أثناء المعالجة: {str(e)}", message.chat.id, msg.message_id)

def run_bot():
    logging.info("بدء تشغيل البوت بنظام Polling المباشر...")
    bot.infinity_polling(skip_pending=True)

if __name__ == '__main__':
    # تشغيل البوت في مسار خلفي
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # تشغيل سيرفر الويب المباشر المخصص للبورت في Render
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

