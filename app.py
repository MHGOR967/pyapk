import os
import json
import zipfile
import subprocess
import requests
import threading
from flask import Flask, render_template_string, request, send_file, jsonify

app = Flask(__name__)

UPLOAD_FOLDER = 'temp'
DATA_FILE = 'users_data.json'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

BASE_APK = 'wahm.apk'
KEYSTORE = 'release.jks'
KEY_ALIAS = 'mykey'
KEY_PASS = 'password123'
TELEGRAM_BOT_TOKEN = '8737255406:AAEFenbZDgNzz5yX9QLVMdstx2nb6WBftKw'

def load_users():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_users(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def get_user_info(user_id):
    users = load_users()
    str_id = str(user_id)
    if str_id not in users:
        users[str_id] = {
            'attempts': 2,
            'invites': 0,
            'unlimited': False,
            'invited_list': [],
            'referred_by': None
        }
        save_users(users)
    return users[str_id]

def update_user_attempts(user_id):
    users = load_users()
    str_id = str(user_id)
    if str_id in users:
        if not users[str_id]['unlimited']:
            if users[str_id]['attempts'] > 0:
                users[str_id]['attempts'] -= 1
                save_users(users)
                return True
            return False
        return True
    return False

def send_apk_to_telegram(chat_id, file_path):
    if not TELEGRAM_BOT_TOKEN or not chat_id or chat_id == 'unknown':
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
        caption_msg = f"✨ **تم توليد وتوقيع تطبيق وَهْم بنجاح!**\n👤 معرّف المستخدم: `{chat_id}`\n🛠 خدمة: **wahmapk** | **g5wbot**\n🌐 منصة فخم: fokhm.com"
        
        with open(file_path, 'rb') as apk_file:
            files = {'document': ('wahm_customized.apk', apk_file)}
            data = {
                'chat_id': chat_id,
                'caption': caption_msg,
                'parse_mode': 'Markdown'
            }
            requests.post(url, data=data, files=files, timeout=60)
    except Exception as e:
        print(f"Background Telegram send error: {e}")

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
        .glass-box { background: rgba(26, 18, 48, 0.75); backdrop-filter: blur(25px); -webkit-backdrop-filter: blur(25px); border: 1px solid rgba(168, 85, 247, 0.2); }
        .purple-glow { box-shadow: 0 0 35px rgba(168, 85, 247, 0.25); }
        .btn-gradient { background: linear-gradient(135deg, #a855f7 0%, #ec4899 100%); }
        .btn-gradient:hover { background: linear-gradient(135deg, #9333ea 0%, #db2777 100%); }
    </style>
</head>
<body class="min-h-screen flex flex-col items-center justify-center p-4 selection:bg-purple-500 selection:text-white">

    <div class="max-w-md w-full glass-box rounded-3xl p-6 purple-glow relative overflow-hidden space-y-4 my-auto">
        <div class="absolute -top-24 -right-24 w-48 h-48 bg-purple-600/20 rounded-full blur-3xl pointer-events-none"></div>
        <div class="absolute -bottom-24 -left-24 w-48 h-48 bg-pink-600/20 rounded-full blur-3xl pointer-events-none"></div>

        <!-- Header -->
        <div class="text-center relative z-10">
            <div class="w-14 h-14 bg-gradient-to-tr from-purple-500 to-pink-500 rounded-2xl mx-auto flex items-center justify-center text-white text-xl shadow-lg shadow-purple-500/30 mb-2 border border-white/20">
                <i class="fa-solid fa-wand-magic-sparkles"></i>
            </div>
            <h1 class="text-xl font-black text-white tracking-wide">APK Injector Pro</h1>
            <p class="text-[11px] text-purple-300/80">منصة فخم الماسية لتخصيص وتوقيع تطبيقات وَهْم</p>
        </div>

        <!-- User Stats Card -->
        <div class="bg-purple-950/50 border border-purple-500/30 rounded-2xl p-3.5 relative z-10 flex items-center justify-between shadow-inner">
            <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-xl bg-purple-500/20 flex items-center justify-center text-purple-300">
                    <i class="fa-solid fa-user-shield text-base"></i>
                </div>
                <div>
                    <span class="text-[10px] text-purple-300/70 block">حالة الحساب</span>
                    <span id="accountStatusText" class="text-xs font-bold text-amber-400">جارِ التحقق...</span>
                </div>
            </div>
            <div class="text-left">
                <span class="text-[10px] text-purple-300/70 block">المحاولات المتاحة</span>
                <span id="attemptsBadge" class="text-xs font-black bg-purple-500/20 text-purple-200 px-2.5 py-1 rounded-xl border border-purple-500/30">--</span>
            </div>
        </div>

        <!-- Navigation Tabs -->
        <div class="grid grid-cols-3 gap-1.5 bg-purple-950/40 p-1 rounded-2xl border border-purple-500/25 relative z-10 text-center">
            <button onclick="switchTab('generator')" id="tabGenBtn" class="py-2 text-[11px] font-bold rounded-xl transition bg-purple-600 text-white shadow">الأساسي</button>
            <button onclick="switchTab('advanced')" id="tabAdvBtn" class="py-2 text-[11px] font-bold rounded-xl transition text-purple-300 hover:text-white">التعديلات ⚙️</button>
            <button onclick="switchTab('invites')" id="tabInvBtn" class="py-2 text-[11px] font-bold rounded-xl transition text-purple-300 hover:text-white">الدعوات 🔥</button>
        </div>

        <!-- MAIN FORM -->
        <form id="injectForm" class="space-y-3 relative z-10">
            <!-- TAB 1: Generator Form -->
            <div id="tabGenerator" class="space-y-3">
                <div>
                    <label class="block text-xs font-bold text-purple-200 mb-1.5 mr-1"><i class="fa-solid fa-key text-amber-400 ml-1"></i> أدخل توكن البوت:</label>
                    <div class="relative">
                        <input type="password" id="tokenInput" name="token" required class="w-full bg-purple-950/60 border border-purple-500/30 rounded-2xl p-3 text-xs text-white focus:outline-none focus:border-purple-400 transition placeholder:text-purple-400/40 shadow-inner" placeholder="الصق التوكن هنا...">
                        <button type="button" onclick="togglePassword()" class="absolute left-3.5 top-3 text-purple-400 hover:text-white text-xs">
                            <i class="fa-solid fa-eye" id="eyeIcon"></i>
                        </button>
                    </div>
                </div>
            </div>

            <!-- TAB 2: Advanced Customizations (URL Injection) -->
            <div id="tabAdvanced" class="hidden space-y-3">
                <div>
                    <label class="block text-xs font-bold text-purple-200 mb-1.5 mr-1"><i class="fa-solid fa-link text-purple-400 ml-1"></i> رابط التطبيق (assets/url.txt):</label>
                    <input type="url" id="appUrl" name="app_url" class="w-full bg-purple-950/60 border border-purple-500/30 rounded-2xl p-3 text-xs text-white focus:outline-none focus:border-purple-400 transition placeholder:text-purple-400/40 shadow-inner" placeholder="https://example.com (اختياري)">
                    <span class="text-[10px] text-purple-400/70 mt-1 block pr-1">سيتم حقنه تلقائياً في مسار assets/url.txt داخل الحزمة.</span>
                </div>
            </div>

            <!-- TAB 3: Invites System -->
            <div id="tabInvites" class="hidden space-y-3 text-center">
                <div class="bg-purple-950/60 border border-purple-500/30 rounded-2xl p-4 space-y-2">
                    <div class="w-10 h-10 bg-amber-500/20 text-amber-400 rounded-xl mx-auto flex items-center justify-center text-lg">
                        <i class="fa-solid fa-bullhorn"></i>
                    </div>
                    <h3 class="text-xs font-bold text-white">رابط دعوة wahmapk الحصري!</h3>
                    <p class="text-[11px] text-purple-300/80 leading-relaxed">
                        شارك رابط الـ Web App أدناه. عند دعوة 5 أشخاص جدد، سيتحول حسابك تلقائياً إلى وضع (غير محدود - Unlimited) مدى الحياة!
                    </p>
                    <div class="pt-1">
                        <span class="text-[10px] text-purple-400">عدد الأعضاء المدعوين:</span>
                        <div class="text-lg font-black text-amber-400" id="invitesCount">0 / 5</div>
                    </div>
                    <div class="w-full bg-purple-950 rounded-full h-2 p-0.5 border border-purple-500/20 overflow-hidden">
                        <div id="invitesBar" class="bg-gradient-to-r from-amber-500 to-yellow-400 h-full rounded-full transition-all duration-300 w-0"></div>
                    </div>
                    <button type="button" onclick="copyInviteLink()" class="w-full bg-purple-600 hover:bg-purple-500 text-white font-bold py-2.5 rounded-xl text-xs transition shadow flex items-center justify-center gap-2 mt-2">
                        <i class="fa-solid fa-copy"></i> نسخ رابط الدعوة الخاص بك
                    </button>
                </div>
            </div>

            <div id="errorBanner" class="hidden bg-red-950/50 border border-red-500/30 text-red-300 p-3 rounded-xl text-xs flex items-center gap-2">
                <i class="fa-solid fa-circle-exclamation text-red-400"></i>
                <span id="errorText">حدث خطأ ما</span>
            </div>

            <button type="submit" id="submitBtn" class="w-full btn-gradient text-white font-bold py-3.5 rounded-2xl transition duration-300 shadow-lg shadow-purple-500/25 flex items-center justify-center gap-2 cursor-pointer active:scale-95 text-xs mt-3">
                <span>بدء المعالجة والتوقيع الفوري</span>
            </button>
        </form>

        <!-- Live Progress (Hidden) -->
        <div id="progressBox" class="hidden space-y-3 relative z-10 py-2">
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
        <div id="resultBox" class="hidden space-y-3 relative z-10 text-center">
            <div class="w-12 h-12 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 rounded-2xl mx-auto flex items-center justify-center text-lg shadow-inner">
                <i class="fa-solid fa-circle-check"></i>
            </div>
            <div>
                <h3 class="text-xs font-bold text-emerald-400">تم حقن وتوقيع التطبيق بنجاح!</h3>
                <p class="text-[10px] text-purple-300/70 mt-0.5">تم إرسال النسخة عبر بوت التليجرام الخاص بك.</p>
            </div>

            <div class="grid grid-cols-2 gap-2 pt-1">
                <a id="downloadBtn" href="#" class="btn-gradient text-white font-bold py-2.5 px-3 rounded-xl text-xs flex items-center justify-center gap-2 transition shadow active:scale-95">
                    <i class="fa-solid fa-download"></i> تحميل APK
                </a>
                <button onclick="shareApp()" class="bg-purple-900/60 hover:bg-purple-900 text-purple-200 font-bold py-2.5 px-3 rounded-xl text-xs flex items-center justify-center gap-2 transition border border-purple-500/30 active:scale-95">
                    <i class="fa-solid fa-share-nodes text-purple-400"></i> مشاركة
                </button>
            </div>
            <button onclick="resetForm()" class="text-[10px] text-purple-400 hover:text-white underline block mx-auto pt-1">حقن تطبيق جديد</button>
        </div>

        <div class="text-center border-t border-purple-500/10 pt-2 relative z-10 flex items-center justify-between text-[10px] text-purple-400/60">
            <span>g5wbot نظام آمن 🔒</span>
            <a href="https://fokhm.com" target="_blank" class="hover:text-purple-300 transition">fokhm.com</a>
        </div>
    </div>

    <input type="hidden" id="userId" value="">

    <script>
        let globalDownloadUrl = '';
        let globalFileName = 'wahm_g5wbot.apk';
        let currentUserId = '8349168441';
        let inviteLink = '';

        const urlParams = new URLSearchParams(window.location.search);
        let referrerId = urlParams.get('ref') || urlParams.get('startapp');
        if (referrerId && referrerId.startsWith('ref_')) {
            referrerId = referrerId.replace('ref_', '');
        }

        const tg = window.Telegram?.WebApp;
        if (tg) {
            tg.ready();
            tg.expand();
            const user = tg.initDataUnsafe?.user;
            if (user && user.id) {
                currentUserId = user.id;
            }
            if (tg.initDataUnsafe?.start_param && tg.initDataUnsafe.start_param.startsWith('ref_')) {
                referrerId = tg.initDataUnsafe.start_param.replace('ref_', '');
            }
        }
        document.getElementById('userId').value = currentUserId;
        inviteLink = `https://t.me/g5wbot/wahmapk?startapp=ref_${currentUserId}`;

        async function initUserData() {
            try {
                if (referrerId && referrerId !== String(currentUserId)) {
                    await fetch('/api/register_invite', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ referrer_id: referrerId, new_user_id: currentUserId })
                    });
                }
                const res = await fetch(`/api/user?user_id=${currentUserId}`);
                const data = await res.json();
                
                if (data.unlimited) {
                    document.getElementById('accountStatusText').innerText = 'حساب غير محدود (VIP)';
                    document.getElementById('attemptsBadge').innerText = '∞ لامحدود';
                } else {
                    document.getElementById('accountStatusText').innerText = 'حساب تجريبي';
                    document.getElementById('attemptsBadge').innerText = data.attempts + ' محاولات';
                }
                document.getElementById('invitesCount').innerText = `${data.invites} / 5`;
                let percent = (data.invites / 5) * 100;
                if (percent > 100) percent = 100;
                document.getElementById('invitesBar').style.width = percent + '%';
            } catch(e) {}
        }
        initUserData();

        function switchTab(tab) {
            const genTab = document.getElementById('tabGenerator');
            const advTab = document.getElementById('tabAdvanced');
            const invTab = document.getElementById('tabInvites');
            const genBtn = document.getElementById('tabGenBtn');
            const advBtn = document.getElementById('tabAdvBtn');
            const invBtn = document.getElementById('tabInvBtn');

            genTab.classList.add('hidden');
            advTab.classList.add('hidden');
            invTab.classList.add('hidden');
            genBtn.className = 'py-2 text-[11px] font-bold rounded-xl transition text-purple-300 hover:text-white';
            advBtn.className = 'py-2 text-[11px] font-bold rounded-xl transition text-purple-300 hover:text-white';
            invBtn.className = 'py-2 text-[11px] font-bold rounded-xl transition text-purple-300 hover:text-white';

            if (tab === 'generator') {
                genTab.classList.remove('hidden');
                genBtn.className = 'py-2 text-[11px] font-bold rounded-xl transition bg-purple-600 text-white shadow';
            } else if (tab === 'advanced') {
                advTab.classList.remove('hidden');
                advBtn.className = 'py-2 text-[11px] font-bold rounded-xl transition bg-purple-600 text-white shadow';
            } else {
                invTab.classList.remove('hidden');
                invBtn.className = 'py-2 text-[11px] font-bold rounded-xl transition bg-purple-600 text-white shadow';
            }
        }

        function copyInviteLink() {
            navigator.clipboard.writeText(inviteLink);
            alert('✨ تم نسخ رابط دعوة (wahmapk) المخصص بنجاح!');
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
            if (!token) return;

            errorBanner.classList.add('hidden');
            form.classList.add('hidden');
            progressBox.classList.remove('hidden');

            let currentProgress = 10;
            progressBar.style.width = currentProgress + '%';
            percentText.innerText = currentProgress + '%';

            const stages = [
                { p: 30, text: "جاري التحقق من الرصيد وفتح الحزمة..." },
                { p: 60, text: "جاري حقن التوكن، معرف المستخدم، والرابط المخصص..." },
                { p: 85, text: "جاري تطبيق المحاذاة zipalign والتوقيع..." },
                { p: 98, text: "جاري إرسال النسخة عبر البوت وتجهيز التحميل..." }
            ];

            let stageIdx = 0;
            const progressTimer = setInterval(() => {
                if (stageIdx < stages.length && currentProgress < stages[stageIdx].p) {
                    currentProgress += 4;
                    progressBar.style.width = currentProgress + '%';
                    percentText.innerText = currentProgress + '%';
                    statusText.innerHTML = `<i class="fa-solid fa-circle-notch fa-spin text-purple-400"></i> ${stages[stageIdx].text}`;
                    if (currentProgress >= stages[stageIdx].p) {
                        stageIdx++;
                    }
                }
            }, 200);

            try {
                const formData = new FormData(form);
                formData.append('user_id', currentUserId);

                const response = await fetch('/generate', {
                    method: 'POST',
                    body: formData
                });

                clearInterval(progressTimer);

                if (!response.ok) {
                    const errRes = await response.text();
                    throw new Error(errRes || 'حدث خطأ أثناء المعالجة.');
                }

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
                    initUserData();
                }, 400);

            } catch (err) {
                clearInterval(progressTimer);
                progressBox.classList.add('hidden');
                form.classList.remove('hidden');
                errorText.innerText = err.message || 'حدث خطأ ما';
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
                        }
                    });
            }
        }

        function resetForm() {
            resultBox.classList.add('hidden');
            form.classList.remove('hidden');
            document.getElementById('tokenInput').value = '';
            document.getElementById('appUrl').value = '';
            progressBar.style.width = '0%';
            errorBanner.classList.add('hidden');
            initUserData();
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/user')
def api_user():
    user_id = request.args.get('user_id', '8349168441')
    info = get_user_info(user_id)
    return jsonify(info)

@app.route('/api/register_invite', methods=['POST'])
def register_invite():
    data = request.get_json() or {}
    referrer_id = str(data.get('referrer_id'))
    new_user_id = str(data.get('new_user_id'))

    if not referrer_id or not new_user_id or referrer_id == new_user_id:
        return jsonify({'status': 'ignored'})

    users = load_users()
    if referrer_id not in users:
        get_user_info(referrer_id)
        users = load_users()

    if new_user_id not in users:
        users[new_user_id] = {'attempts': 2, 'invites': 0, 'unlimited': False, 'invited_list': [], 'referred_by': referrer_id}
    else:
        if not users[new_user_id].get('referred_by'):
            users[new_user_id]['referred_by'] = referrer_id

    if new_user_id not in users[referrer_id].get('invited_list', []):
        users[referrer_id].setdefault('invited_list', []).append(new_user_id)
        users[referrer_id]['invites'] = len(users[referrer_id]['invited_list'])
        if users[referrer_id]['invites'] >= 5:
            users[referrer_id]['unlimited'] = True
        save_users(users)
        return jsonify({'status': 'success', 'invites': users[referrer_id]['invites']})

    save_users(users)
    return jsonify({'status': 'already_counted'})

@app.route('/generate', methods=['POST'])
def generate():
    token_text = request.form.get('token')
    app_url = request.form.get('app_url', '').strip()
    user_id = request.form.get('user_id', '8349168441')

    if not token_text:
        return "الرجاء إدخال التوكن!", 400

    user_info = get_user_info(user_id)
    if not user_info['unlimited'] and user_info['attempts'] <= 0:
        return "عذراً! انتهت محاولاتك المجانية. ادعُ أصدقائك عبر رابط الـ Web App لفتح الصنع اللانهائي بلا حدود!", 403

    if not os.path.exists(BASE_APK):
        return "خطأ: ملف التطبيق الأساسي (wahm.apk) غير موجود على السيرفر!", 500

    modified_apk = os.path.join(UPLOAD_FOLDER, f'wahm_mod_{user_id}.apk')
    aligned_apk = os.path.join(UPLOAD_FOLDER, f'wahm_aligned_{user_id}.apk')
    signed_apk = os.path.join(UPLOAD_FOLDER, f'wahm_signed_{user_id}.apk')

    try:
        if not user_info['unlimited']:
            update_user_attempts(user_id)

        for f in [modified_apk, aligned_apk, signed_apk]:
            if os.path.exists(f):
                os.remove(f)

        # نسخ التطبيق الأصلي للعمل عليه
        os.system(f"cp {BASE_APK} {modified_apk}")

        # المسارات المباشرة داخل ملف الـ ZIP
        token_path_in_zip = 'assets/token.txt'
        id_path_in_zip = 'assets/id.txt'
        url_path_in_zip = 'assets/url.txt'
        temp_zip = os.path.join(UPLOAD_FOLDER, 'temp.zip')
        
        with zipfile.ZipFile(modified_apk, 'r') as zin:
            with zipfile.ZipFile(temp_zip, 'w') as zout:
                token_exists = False
                id_exists = False
                url_exists = False
                
                for item in zin.infolist():
                    # استبعاد التوقيعات القديمة لمنع التضارب
                    if item.filename.startswith('META-INF/'):
                        continue
                    if item.filename == token_path_in_zip:
                        token_exists = True
                        zout.writestr(item, token_text.encode('utf-8'))
                    elif item.filename == id_path_in_zip:
                        id_exists = True
                        zout.writestr(item, str(user_id).encode('utf-8'))
                    elif item.filename == url_path_in_zip:
                        if app_url:
                            url_exists = True
                            zout.writestr(item, app_url.encode('utf-8'))
                    else:
                        zout.writestr(item, zin.read(item.filename))
                
                if not token_exists:
                    zout.writestr(token_path_in_zip, token_text.encode('utf-8'))
                if not id_exists:
                    zout.writestr(id_path_in_zip, str(user_id).encode('utf-8'))
                if app_url and not url_exists:
                    zout.writestr(url_path_in_zip, app_url.encode('utf-8'))

        os.replace(temp_zip, modified_apk)

        # المحاذاة البرمجية zipalign
        subprocess.run(['zipalign', '-v', '-p', '4', modified_apk, aligned_apk], check=True)

        # توليد المفتاح تلقائياً إن لم يكن موجوداً
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

        # التوقيع باستخدام apksigner
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

        # إرسال الملف للبوت في الخلفية
        if TELEGRAM_BOT_TOKEN and user_id and user_id != 'unknown':
            threading.Thread(target=send_apk_to_telegram, args=(user_id, signed_apk)).start()

        return send_file(signed_apk, as_attachment=True, download_name='wahm_customized.apk')

    except Exception as e:
        return f"حدث خطأ أثناء المعالجة: {str(e)}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

