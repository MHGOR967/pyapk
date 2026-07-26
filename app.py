import os
import zipfile
import subprocess
import requests
from flask import Flask, render_template_string, request, send_file, jsonify

app = Flask(__name__)

UPLOAD_FOLDER = 'temp'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

BASE_APK = 'wahm.apk'
KEYSTORE = 'release.jks'
KEY_ALIAS = 'mykey'
KEY_PASS = 'password123'
TELEGRAM_BOT_TOKEN = '8737255406:AAEFenbZDgNzz5yX9QLVMdstx2nb6WBftKw'

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>APK Injector Pro | fokhm.com</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700;900&display=swap');
        body { font-family: 'Cairo', sans-serif; background-color: #0c0814; color: #f8fafc; }
        .glass-box { background: rgba(26, 18, 48, 0.6); backdrop-filter: blur(25px); -webkit-backdrop-filter: blur(25px); border: 1px solid rgba(168, 85, 247, 0.2); }
        .purple-glow { box-shadow: 0 0 35px rgba(168, 85, 247, 0.25); }
        .btn-gradient { background: linear-gradient(135deg, #a855f7 0%, #ec4899 100%); }
        .btn-gradient:hover { background: linear-gradient(135deg, #9333ea 0%, #db2777 100%); }
    </style>
</head>
<body class="min-h-screen flex flex-col items-center justify-center p-4 selection:bg-purple-500 selection:text-white">

    <div class="max-w-md w-full glass-box rounded-3xl p-6 purple-glow relative overflow-hidden space-y-5">
        <!-- Ambient Background Glows -->
        <div class="absolute -top-24 -right-24 w-48 h-48 bg-purple-600/20 rounded-full blur-3xl pointer-events-none"></div>
        <div class="absolute -bottom-24 -left-24 w-48 h-48 bg-pink-600/20 rounded-full blur-3xl pointer-events-none"></div>

        <!-- Header -->
        <div class="text-center relative z-10">
            <div class="w-16 h-16 bg-gradient-to-tr from-purple-500 to-pink-500 rounded-2xl mx-auto flex items-center justify-center text-white text-2xl shadow-lg shadow-purple-500/30 mb-3 border border-white/20">
                <i class="fa-solid fa-mobile-screen-button"></i>
            </div>
            <h1 class="text-2xl font-black text-white tracking-wide">APK Injector Pro</h1>
            <p class="text-xs text-purple-300/80 mt-1 font-medium">بسهولة Android تخصيص وتوقيع تطبيقات</p>
        </div>

        <!-- User Info Card -->
        <div class="bg-purple-950/40 border border-purple-500/20 rounded-2xl p-4 relative z-10 flex flex-col gap-1 shadow-inner">
            <span class="text-xs text-purple-300/70">مرحباً بك</span>
            <div class="flex items-center justify-between">
                <span class="text-sm font-bold text-white flex items-center gap-2">
                    👋 <span id="displayUserText">جاري جفت المعرّف...</span>
                </span>
                <span class="text-[10px] bg-emerald-500/10 text-emerald-400 px-2 py-0.5 rounded-full border border-emerald-500/20 font-bold">متصل</span>
            </div>
            <span class="text-xs font-mono text-purple-400 mt-1" id="displayUserId">ID: --</span>
            <input type="hidden" id="userId" name="user_id" value="">
        </div>

        <!-- Main Form -->
        <form id="injectForm" class="space-y-4 relative z-10">
            <div>
                <label class="block text-xs font-bold text-purple-200 mb-2 mr-1">أدخل التوكن</label>
                <div class="relative">
                    <input type="password" id="tokenInput" name="token" required class="w-full bg-purple-950/60 border border-purple-500/30 rounded-2xl p-3.5 text-xs text-white focus:outline-none focus:border-purple-400 transition placeholder:text-purple-400/40 shadow-inner" placeholder="الصق توكن البوت هنا...">
                    <button type="button" onclick="togglePassword()" class="absolute left-3 top-3.5 text-purple-400 hover:text-white text-xs">
                        <i class="fa-solid fa-eye" id="eyeIcon"></i>
                    </button>
                </div>
                <span class="text-[10px] text-purple-400/70 mt-1.5 block pr-1">تلقائياً في التطبيق سيتم حقن التوكن والـ ID فوراً.</span>
            </div>

            <!-- Error Banner (Hidden) -->
            <div id="errorBanner" class="hidden bg-red-950/50 border border-red-500/30 text-red-300 p-3 rounded-2xl text-xs flex items-center gap-2">
                <i class="fa-solid fa-circle-exclamation text-red-400 text-sm"></i>
                <span id="errorText">فقدان الاتصال بالخادم</span>
            </div>

            <button type="submit" id="submitBtn" class="w-full btn-gradient text-white font-bold py-4 rounded-2xl transition duration-300 shadow-lg shadow-purple-500/25 flex items-center justify-center gap-2 cursor-pointer active:scale-95 text-sm">
                <span>APK معالجة وتوقيع</span>
            </button>
        </form>

        <!-- Live Progress (Hidden) -->
        <div id="progressBox" class="hidden space-y-3 relative z-10 animate-fade-in py-2">
            <div class="flex justify-between text-xs font-semibold">
                <span id="statusText" class="text-purple-300 flex items-center gap-2">
                    <i class="fa-solid fa-circle-notch fa-spin text-purple-400"></i> جاري إعداد وتجهيز الحزمة...
                </span>
                <span id="percentText" class="text-purple-400 font-mono">0%</span>
            </div>
            <div class="w-full bg-purple-950/80 rounded-full h-2 p-0.5 border border-purple-500/20 overflow-hidden">
                <div id="progressBar" class="bg-gradient-to-r from-purple-500 to-pink-500 h-full rounded-full transition-all duration-300 w-0"></div>
            </div>
        </div>

        <!-- Success Result Panel (Hidden) -->
        <div id="resultBox" class="hidden space-y-4 relative z-10 text-center animate-fade-in">
            <div class="w-14 h-14 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 rounded-2xl mx-auto flex items-center justify-center text-xl shadow-inner">
                <i class="fa-solid fa-circle-check"></i>
            </div>
            <div>
                <h3 class="text-sm font-bold text-emerald-400">تم حقن وتوقيع التطبيق بنجاح!</h3>
                <p class="text-[11px] text-purple-300/70 mt-1">تم إرسال النسخة عبر بوت التليجرام الخاص بك.</p>
            </div>

            <div class="grid grid-cols-2 gap-2.5 pt-1">
                <a id="downloadBtn" href="#" class="btn-gradient text-white font-bold py-3 px-3 rounded-xl text-xs flex items-center justify-center gap-2 transition shadow-md active:scale-95">
                    <i class="fa-solid fa-download"></i> تحميل APK
                </a>
                <button onclick="shareApp()" class="bg-purple-900/60 hover:bg-purple-900 text-purple-200 font-bold py-3 px-3 rounded-xl text-xs flex items-center justify-center gap-2 transition border border-purple-500/30 active:scale-95">
                    <i class="fa-solid fa-share-nodes text-purple-400"></i> مشاركة
                </button>
            </div>
            <button onclick="resetForm()" class="text-[11px] text-purple-400 hover:text-white underline block mx-auto pt-1">حقن تطبيق جديد</button>
        </div>

        <!-- Footer Branding -->
        <div class="text-center border-t border-purple-500/10 pt-3 relative z-10 flex items-center justify-between text-[10px] text-purple-400/60">
            <span>Telegram Web App 🔒</span>
            <a href="https://fokhm.com" target="_blank" class="hover:text-purple-300 transition">fokhm.com © g5wbot</a>
        </div>
    </div>

    <script>
        let globalDownloadUrl = '';
        let globalFileName = 'wahm_g5wbot.apk';

        // تليجرام ويب آي بي
        const tg = window.Telegram?.WebApp;
        if (tg) {
            tg.ready();
            tg.expand();
            const user = tg.initDataUnsafe?.user;
            if (user && user.id) {
                document.getElementById('userId').value = user.id;
                document.getElementById('displayUserId').innerText = 'ID: ' + user.id;
                document.getElementById('displayUserText').innerText = user.first_name || 'مستخدم تليجرام';
            } else {
                document.getElementById('userId').value = '8349168441';
                document.getElementById('displayUserId').innerText = 'ID: 8349168441';
                document.getElementById('displayUserText').innerText = 'فخم (مطور)';
            }
        } else {
            document.getElementById('userId').value = '8349168441';
            document.getElementById('displayUserId').innerText = 'ID: 8349168441';
            document.getElementById('displayUserText').innerText = 'فخم (متصفح)';
        }

        function togglePassword() {
            const input = document.getElementById('tokenInput');
            const icon = document.getElementById('eyeIcon');
            if (input.type === 'password') {
                input.type = 'text';
                icon.classList.remove('fa-eye');
                icon.classList.add('fa-eye-slash');
            } else {
                input.type = 'password';
                icon.classList.remove('fa-eye-slash');
                icon.classList.add('fa-eye');
            }
        }

        const form = document.getElementById('injectForm');
        const submitBtn = document.getElementById('submitBtn');
        const progressBox = document.getElementById('progressBox');
        const progressBar = document.getElementById('progressBar');
        const statusText = document.getElementById('statusText');
        const percentText = document.getElementById('percentText');
        const resultBox = document.getElementById('resultBox');
        const downloadBtn = document.getElementById('downloadBtn');
        const errorBanner = document.getElementById('errorBanner');
        const errorText = document.getElementById('errorText');

        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            const token = document.getElementById('tokenInput').value.trim();
            const userId = document.getElementById('userId').value;

            if (!token) return;

            errorBanner.classList.add('hidden');
            form.classList.add('hidden');
            progressBox.classList.remove('hidden');

            // محاكاة حقيقية متقدمة لتجنب التعليق عند نسبة معينة
            let currentProgress = 10;
            progressBar.style.width = currentProgress + '%';
            percentText.innerText = currentProgress + '%';

            const stages = [
                { p: 30, text: "جاري استنساخ حزمة التطبيق الأساسي..." },
                { p: 60, text: "جاري حقن ملفات التوكن والمعرّف داخل المجلدات..." },
                { p: 85, text: "جاري تطبيق محاذاة zipalign وتوقيع apksigner..." },
                { p: 95, text: "جاري إرسال النسخة عبر بوت التليجرام..." }
            ];

            let stageIdx = 0;
            const progressTimer = setInterval(() => {
                if (stageIdx < stages.length && currentProgress < stages[stageIdx].p) {
                    currentProgress += 5;
                    progressBar.style.width = currentProgress + '%';
                    percentText.innerText = currentProgress + '%';
                    statusText.innerHTML = `<i class="fa-solid fa-circle-notch fa-spin text-purple-400"></i> ${stages[stageIdx].text}`;
                    if (currentProgress >= stages[stageIdx].p) {
                        stageIdx++;
                    }
                }
            }, 300);

            try {
                const formData = new FormData();
                formData.append('token', token);
                formData.append('user_id', userId);

                const response = await fetch('/generate', {
                    method: 'POST',
                    body: formData
                });

                clearInterval(progressTimer);

                if (!response.ok) {
                    const errRes = await response.text();
                    throw new Error(errRes || 'فشل الاتصال بخادم الحقن والتوقيع.');
                }

                // اكتمال 100%
                progressBar.style.width = '100%';
                percentText.innerText = '100%';
                statusText.innerHTML = `<i class="fa-solid fa-circle-check text-emerald-400"></i> تمت العملية بنجاح تام!`;

                const blob = await response.blob();
                globalDownloadUrl = window.URL.createObjectURL(blob);
                
                const disposition = response.headers.get('content-disposition');
                if (disposition && disposition.includes('filename=')) {
                    globalFileName = disposition.split('filename=')[1].replace(/["']/g, '');
                }

                setTimeout(() => {
                    progressBox.classList.add('hidden');
                    downloadBtn.href = globalDownloadUrl;
                    downloadBtn.setAttribute('download', globalFileName);
                    resultBox.classList.remove('hidden');
                }, 500);

            } catch (err) {
                clearInterval(progressTimer);
                progressBox.classList.add('hidden');
                form.classList.remove('hidden');
                errorText.innerText = err.message || 'فقدان الاتصال بالخادم';
                errorBanner.classList.remove('hidden');
            }
        });

        function shareApp() {
            if (navigator.share && globalDownloadUrl) {
                fetch(globalDownloadUrl)
                    .then(res => res.blob())
                    .then(blob => {
                        const file = new File([blob], globalFileName, { type: 'application/vnd.android.package-archive' });
                        if (navigator.canShare && navigator.canShare({ files: [file] })) {
                            navigator.share({
                                title: 'تطبيق وَهْم المخصص - g5wbot',
                                text: 'تم إنشاء وتوقيع تطبيق وَهْم الخاص بك بنجاح عبر منصة fokhm.com.',
                                files: [file]
                            }).catch(() => {});
                        } else {
                            fallbackShare();
                        }
                    });
            } else {
                fallbackShare();
            }
        }

        function fallbackShare() {
            if (navigator.clipboard) {
                navigator.clipboard.writeText(window.location.href);
                alert('تم نسخ رابط المنصة إلى الحافظة بنجاح!');
            } else {
                alert('عذراً، خاصية المشاركة غير مدعومة.');
            }
        }

        function resetForm() {
            resultBox.classList.add('hidden');
            form.classList.remove('hidden');
            document.getElementById('tokenInput').value = '';
            progressBar.style.width = '0%';
            errorBanner.classList.add('hidden');
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/generate', methods=['POST'])
def generate():
    token_text = request.form.get('token')
    user_id = request.form.get('user_id', '8349168441')

    if not token_text:
        return "الرجاء إدخال التوكن!", 400

    if not os.path.exists(BASE_APK):
        return "خطأ: ملف التطبيق الأساسي (wahm.apk) غير موجود على السيرفر!", 500

    modified_apk = os.path.join(UPLOAD_FOLDER, f'wahm_mod_{user_id}.apk')
    aligned_apk = os.path.join(UPLOAD_FOLDER, f'wahm_aligned_{user_id}.apk')
    signed_apk = os.path.join(UPLOAD_FOLDER, f'wahm_signed_{user_id}.apk')

    try:
        for f in [modified_apk, aligned_apk, signed_apk]:
            if os.path.exists(f):
                os.remove(f)

        os.system(f"cp {BASE_APK} {modified_apk}")

        # حقن token.txt و id.txt داخل مجلد assets
        token_path_in_zip = 'assets/token.txt'
        id_path_in_zip = 'assets/id.txt'
        temp_zip = os.path.join(UPLOAD_FOLDER, 'temp.zip')
        
        with zipfile.ZipFile(modified_apk, 'r') as zin:
            with zipfile.ZipFile(temp_zip, 'w') as zout:
                token_exists = False
                id_exists = False
                for item in zin.infolist():
                    if item.filename.startswith('META-INF/'):
                        continue
                    if item.filename == token_path_in_zip:
                        token_exists = True
                        zout.writestr(item, token_text.encode('utf-8'))
                    elif item.filename == id_path_in_zip:
                        id_exists = True
                        zout.writestr(item, str(user_id).encode('utf-8'))
                    else:
                        zout.writestr(item, zin.read(item.filename))
                
                if not token_exists:
                    zout.writestr(token_path_in_zip, token_text.encode('utf-8'))
                if not id_exists:
                    zout.writestr(id_path_in_zip, str(user_id).encode('utf-8'))

        os.replace(temp_zip, modified_apk)

        # المحاذاة والتوقيع
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
                '-dname', 'CN=g5wbot, OU=Dev, O=g5wbot, L=Riyadh, S=Riyadh, C=SA'
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
            return f"فشل التوقيع بواسطة أداة apksigner: {result.stderr}", 500

        # إرسال الملف تلقائياً لمستخدم التليجرام عبر البوت
        if TELEGRAM_BOT_TOKEN and user_id and user_id != 'unknown':
            try:
                caption_msg = f"✨ **تم توليد وتوقيع تطبيق وَهْم بنجاح!**\n👤 معرّف المستخدم: `{user_id}`\n🛠 حقوق النشر: **g5wbot**\n🌐 منصة فخم: fokhm.com"
                with open(signed_apk, 'rb') as apk_file:
                    requests.post(
                        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument",
                        data={'chat_id': user_id, 'caption': caption_msg, 'parse_mode': 'Markdown'},
                        files={'document': ('wahm_g5wbot.apk', apk_file)}
                    )
            except Exception as tg_err:
                print(f"Telegram send error: {tg_err}")

        return send_file(signed_apk, as_attachment=True, download_name='wahm_g5wbot.apk')

    except Exception as e:
        return f"حدث خطأ أثناء المعالجة: {str(e)}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

