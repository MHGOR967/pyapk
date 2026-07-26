import os
import zipfile
import subprocess
from flask import Flask, render_template_string, request, send_file

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
    <title>منصة توقيع وحقن تطبيق وَهْم - fokhm.com</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen flex items-center justify-center p-4">
    <div class="max-w-md w-full bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-2xl">
        <div class="text-center mb-6">
            <h1 class="text-2xl font-bold text-amber-400">توقيع وحقن تطبيق وَهْم</h1>
            <p class="text-sm text-slate-400 mt-1">أدخل التوكن ليتم حقنه وتوقيع الـ APK بأحدث الصيغ</p>
        </div>

        <form method="POST" action="/generate" class="space-y-4" onsubmit="showLoading()">
            <div>
                <label class="block text-sm font-medium text-slate-300 mb-2">أدخل التوكن المطلوب:</label>
                <textarea name="token" rows="4" required class="w-full bg-slate-950 border border-slate-700 rounded-xl p-3 text-white focus:outline-none focus:border-amber-500 transition" placeholder="الصق التوكن هنا..."></textarea>
            </div>

            <button type="submit" id="submitBtn" class="w-full bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold py-3 rounded-xl transition duration-200 shadow-lg shadow-amber-500/20">
                إنشاء وتوقيع التطبيق
            </button>
        </form>

        <div id="loading" class="hidden text-center mt-4">
            <div class="inline-block animate-spin rounded-full h-8 w-8 border-4 border-amber-500 border-t-transparent"></div>
            <p class="text-xs text-amber-400 mt-2">جارٍ حقن التوكن وتوقيع التطبيق، انتظر قليلاً...</p>
        </div>
    </div>

    <script>
        function showLoading() {
            document.getElementById('submitBtn').disabled = true;
            document.getElementById('submitBtn').classList.add('opacity-50');
            document.getElementById('loading').classList.remove('hidden');
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
    if not token_text:
        return "الرجاء إدخال التوكن!", 400

    if not os.path.exists(BASE_APK):
        return "خطأ: ملف التطبيق الأساسي (wahm.apk) غير موجود على السيرفر!", 500

    modified_apk = os.path.join(UPLOAD_FOLDER, 'wahm_modified.apk')
    aligned_apk = os.path.join(UPLOAD_FOLDER, 'wahm_aligned.apk')
    signed_apk = os.path.join(UPLOAD_FOLDER, 'wahm_signed.apk')

    try:
        # تنظيف الملفات المؤقتة القديمة
        for f in [modified_apk, aligned_apk, signed_apk]:
            if os.path.exists(f):
                os.remove(f)

        # 1. نسخ التطبيق الأصلي للعمل عليه
        os.system(f"cp {BASE_APK} {modified_apk}")

        # 2. تعديل أو حقن ملف token.txt داخل الـ APK مباشرة بدون فك ضغط كامل
        target_in_zip = 'assets/token.txt'
        
        temp_zip = os.path.join(UPLOAD_FOLDER, 'temp.zip')
        with zipfile.ZipFile(modified_apk, 'r') as zin:
            with zipfile.ZipFile(temp_zip, 'w') as zout:
                file_exists = False
                for item in zin.infolist():
                    # إزالة التوقيع القديم لمنع التعارض
                    if item.filename.startswith('META-INF/'):
                        continue
                    if item.filename == target_in_zip:
                        file_exists = True
                        zout.writestr(item, token_text.encode('utf-8'))
                    else:
                        zout.writestr(item, zin.read(item.filename))
                
                if not file_exists:
                    zout.writestr(target_in_zip, token_text.encode('utf-8'))

        os.replace(temp_zip, modified_apk)

        # 3. محاذاة الملف باستخدام zipalign
        subprocess.run(['zipalign', '-v', '-p', '4', modified_apk, aligned_apk], check=True)

        # 4. توليد مفتاح التوقيع تلقائياً إن لم يكن موجوداً
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

        # 5. التوقيع باستخدام apksigner مع تحديد معاملات --in و --out بوضوح تام
        sign_cmd = [
            'apksigner', 'sign',
            '--ks', KEYSTORE,
            '--ks-pass', f'pass:{KEY_PASS}',
            '--v2-signing-enabled', 'true',
            '--v3-signing-enabled', 'true',
            '--in', aligned_apk,
            '--out', signed_apk
        ]
        
        result = subprocess.run(sign_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            return f"فشل التوقيع بواسطة أداة apksigner: {result.stderr}", 500

        # 6. إرسال الملف النهائي للتحميل المباشر
        return send_file(signed_apk, as_attachment=True, download_name='wahm_customized.apk')

    except Exception as e:
        return f"حدث خطأ أثناء المعالجة: {str(e)}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
