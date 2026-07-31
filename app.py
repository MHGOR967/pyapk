
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
TELEGRAM_BOT_TOKEN = '5712676916:AAGxIlZqufjcHYUGBb9waoCbrTNEzlEvkx8'

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
        caption_msg = f"✅ *تم توليد وتوقيع التطبيق بنجاح*\n👤 معرّف المستخدم: `{chat_id}`\n🛠 الخدمة: *wahmapk* | *g5wbot*"
        with open(file_path, 'rb') as apk_file:
            requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument",
                data={'chat_id': chat_id, 'caption': caption_msg, 'parse_mode': 'Markdown'},
                files={'document': ('wahm_g5wbot.apk', apk_file)},
                timeout=60
            )
    except Exception as e:
        print(f"Background Telegram send error: {e}")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>APK Injector Pro | g5wbot</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700;900&display=swap');

        :root {
            --bg-primary: #060b18;
            --bg-card: rgba(8, 15, 35, 0.85);
            --accent-blue: #0ea5e9;
            --accent-cyan: #06b6d4;
            --accent-indigo: #6366f1;
            --border-color: rgba(14, 165, 233, 0.18);
            --text-primary: #e2e8f0;
            --text-muted: rgba(148, 163, 184, 0.7);
        }

        * { box-sizing: border-box; }

        body {
            font-family: 'Cairo', sans-serif;
            background-color: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            overflow-x: hidden;
        }

        /* ===== ANIMATED GRID BACKGROUND ===== */
        body::before {
            content: '';
            position: fixed;
            inset: 0;
            background-image:
                linear-gradient(rgba(14, 165, 233, 0.04) 1px, transparent 1px),
                linear-gradient(90deg, rgba(14, 165, 233, 0.04) 1px, transparent 1px);
            background-size: 40px 40px;
            pointer-events: none;
            z-index: 0;
        }

        body::after {
            content: '';
            position: fixed;
            top: -30%;
            left: 50%;
            transform: translateX(-50%);
            width: 900px;
            height: 600px;
            background: radial-gradient(ellipse at center, rgba(6, 182, 212, 0.07) 0%, rgba(99, 102, 241, 0.05) 40%, transparent 70%);
            pointer-events: none;
            z-index: 0;
        }

        /* ===== GLASS CARD ===== */
        .glass-card {
            background: var(--bg-card);
            backdrop-filter: blur(30px);
            -webkit-backdrop-filter: blur(30px);
            border: 1px solid var(--border-color);
            box-shadow:
                0 0 0 1px rgba(14, 165, 233, 0.06),
                0 25px 60px rgba(0, 0, 0, 0.6),
                inset 0 1px 0 rgba(255,255,255,0.04);
        }

        .card-glow {
            box-shadow:
                0 0 40px rgba(14, 165, 233, 0.12),
                0 0 80px rgba(99, 102, 241, 0.06),
                0 25px 60px rgba(0, 0, 0, 0.7);
        }

        /* ===== LOGO / ICON ===== */
        .logo-ring {
            background: linear-gradient(135deg, #0ea5e9, #6366f1);
            padding: 2px;
            border-radius: 18px;
        }
        .logo-inner {
            background: #060b18;
            border-radius: 16px;
            width: 100%;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        /* ===== USER PROFILE CARD ===== */
        .profile-card {
            background: linear-gradient(135deg, rgba(14, 165, 233, 0.08) 0%, rgba(99, 102, 241, 0.06) 100%);
            border: 1px solid rgba(14, 165, 233, 0.2);
            border-radius: 18px;
            position: relative;
            overflow: hidden;
        }
        .profile-card::before {
            content: '';
            position: absolute;
            top: 0; right: 0;
            width: 120px; height: 120px;
            background: radial-gradient(circle, rgba(14, 165, 233, 0.1), transparent 70%);
            pointer-events: none;
        }

        .avatar-ring {
            background: linear-gradient(135deg, #0ea5e9, #6366f1, #06b6d4);
            padding: 2.5px;
            border-radius: 50%;
            flex-shrink: 0;
        }
        .avatar-inner {
            background: #060b18;
            border-radius: 50%;
            overflow: hidden;
            width: 100%;
            height: 100%;
        }
        .avatar-inner img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            display: block;
        }

        /* ===== STATUS BADGE ===== */
        .badge-vip {
            background: linear-gradient(135deg, rgba(245, 158, 11, 0.15), rgba(234, 179, 8, 0.1));
            border: 1px solid rgba(245, 158, 11, 0.35);
            color: #fbbf24;
        }
        .badge-trial {
            background: linear-gradient(135deg, rgba(14, 165, 233, 0.12), rgba(6, 182, 212, 0.08));
            border: 1px solid rgba(14, 165, 233, 0.3);
            color: #38bdf8;
        }
        .badge-dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            animation: pulse-dot 2s ease-in-out infinite;
        }
        .badge-dot-vip { background: #fbbf24; box-shadow: 0 0 6px #fbbf24; }
        .badge-dot-trial { background: #38bdf8; box-shadow: 0 0 6px #38bdf8; }

        @keyframes pulse-dot {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.5; transform: scale(0.7); }
        }

        /* ===== STAT BOXES ===== */
        .stat-box {
            background: rgba(14, 165, 233, 0.06);
            border: 1px solid rgba(14, 165, 233, 0.15);
            border-radius: 14px;
            padding: 10px 14px;
            text-align: center;
        }

        /* ===== TABS ===== */
        .tab-container {
            background: rgba(8, 15, 35, 0.6);
            border: 1px solid rgba(14, 165, 233, 0.12);
            border-radius: 16px;
            padding: 4px;
        }
        .tab-btn {
            border-radius: 12px;
            padding: 8px 0;
            font-size: 11px;
            font-weight: 700;
            transition: all 0.25s ease;
            cursor: pointer;
            border: none;
            outline: none;
            width: 100%;
        }
        .tab-btn.active {
            background: linear-gradient(135deg, #0ea5e9, #6366f1);
            color: #fff;
            box-shadow: 0 4px 15px rgba(14, 165, 233, 0.3);
        }
        .tab-btn.inactive {
            background: transparent;
            color: rgba(148, 163, 184, 0.7);
        }
        .tab-btn.inactive:hover { color: #e2e8f0; }

        /* ===== INPUT ===== */
        .input-field {
            width: 100%;
            background: rgba(6, 11, 24, 0.8);
            border: 1px solid rgba(14, 165, 233, 0.2);
            border-radius: 14px;
            padding: 12px 44px 12px 14px;
            font-size: 12px;
            color: #e2e8f0;
            font-family: 'Cairo', sans-serif;
            transition: border-color 0.2s, box-shadow 0.2s;
            outline: none;
        }
        .input-field:focus {
            border-color: rgba(14, 165, 233, 0.5);
            box-shadow: 0 0 0 3px rgba(14, 165, 233, 0.08);
        }
        .input-field::placeholder { color: rgba(148, 163, 184, 0.35); }

        /* ===== BUTTON ===== */
        .btn-primary {
            background: linear-gradient(135deg, #0ea5e9 0%, #6366f1 100%);
            color: #fff;
            font-weight: 700;
            font-size: 12px;
            border-radius: 14px;
            padding: 13px;
            width: 100%;
            border: none;
            cursor: pointer;
            transition: all 0.25s ease;
            box-shadow: 0 6px 20px rgba(14, 165, 233, 0.25);
            font-family: 'Cairo', sans-serif;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }
        .btn-primary:hover {
            background: linear-gradient(135deg, #0284c7 0%, #4f46e5 100%);
            box-shadow: 0 8px 25px rgba(14, 165, 233, 0.35);
            transform: translateY(-1px);
        }
        .btn-primary:active { transform: scale(0.97); }

        .btn-secondary {
            background: rgba(14, 165, 233, 0.08);
            border: 1px solid rgba(14, 165, 233, 0.2);
            color: #7dd3fc;
            font-weight: 700;
            font-size: 11px;
            border-radius: 12px;
            padding: 10px;
            cursor: pointer;
            transition: all 0.2s;
            font-family: 'Cairo', sans-serif;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
        }
        .btn-secondary:hover {
            background: rgba(14, 165, 233, 0.14);
            border-color: rgba(14, 165, 233, 0.35);
        }
        .btn-secondary:active { transform: scale(0.97); }

        /* ===== PROGRESS BAR ===== */
        .progress-track {
            background: rgba(14, 165, 233, 0.08);
            border: 1px solid rgba(14, 165, 233, 0.12);
            border-radius: 99px;
            height: 8px;
            overflow: hidden;
            padding: 1px;
        }
        .progress-fill {
            background: linear-gradient(90deg, #0ea5e9, #6366f1, #06b6d4);
            border-radius: 99px;
            height: 100%;
            transition: width 0.3s ease;
            box-shadow: 0 0 10px rgba(14, 165, 233, 0.5);
        }

        /* ===== ERROR BANNER ===== */
        .error-banner {
            background: rgba(239, 68, 68, 0.08);
            border: 1px solid rgba(239, 68, 68, 0.25);
            border-radius: 12px;
            padding: 10px 14px;
            color: #fca5a5;
            font-size: 11px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        /* ===== SUCCESS BOX ===== */
        .success-icon {
            width: 52px; height: 52px;
            background: rgba(16, 185, 129, 0.1);
            border: 1px solid rgba(16, 185, 129, 0.3);
            border-radius: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #34d399;
            font-size: 20px;
            margin: 0 auto;
            box-shadow: 0 0 20px rgba(16, 185, 129, 0.15);
        }

        /* ===== INVITE PROGRESS ===== */
        .invite-progress-track {
            background: rgba(245, 158, 11, 0.08);
            border: 1px solid rgba(245, 158, 11, 0.15);
            border-radius: 99px;
            height: 8px;
            overflow: hidden;
            padding: 1px;
        }
        .invite-progress-fill {
            background: linear-gradient(90deg, #f59e0b, #eab308);
            border-radius: 99px;
            height: 100%;
            transition: width 0.4s ease;
            box-shadow: 0 0 8px rgba(245, 158, 11, 0.4);
        }

        /* ===== FOOTER ===== */
        .footer-bar {
            border-top: 1px solid rgba(14, 165, 233, 0.08);
            padding-top: 12px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-size: 10px;
            color: rgba(148, 163, 184, 0.45);
        }
        .footer-dot {
            width: 5px; height: 5px;
            background: #22c55e;
            border-radius: 50%;
            box-shadow: 0 0 5px #22c55e;
            animation: pulse-dot 2s ease-in-out infinite;
            display: inline-block;
            margin-left: 4px;
        }

        /* ===== SCAN LINE EFFECT ===== */
        @keyframes scanline {
            0% { transform: translateY(-100%); }
            100% { transform: translateY(100vh); }
        }
        .scanline {
            position: fixed;
            top: 0; left: 0; right: 0;
            height: 2px;
            background: linear-gradient(90deg, transparent, rgba(14, 165, 233, 0.15), transparent);
            animation: scanline 8s linear infinite;
            pointer-events: none;
            z-index: 1;
        }

        /* ===== CORNER DECORATIONS ===== */
        .corner-tl, .corner-br {
            position: absolute;
            width: 20px; height: 20px;
            pointer-events: none;
        }
        .corner-tl {
            top: 12px; right: 12px;
            border-top: 1.5px solid rgba(14, 165, 233, 0.4);
            border-right: 1.5px solid rgba(14, 165, 233, 0.4);
            border-radius: 0 4px 0 0;
        }
        .corner-br {
            bottom: 12px; left: 12px;
            border-bottom: 1.5px solid rgba(14, 165, 233, 0.4);
            border-left: 1.5px solid rgba(14, 165, 233, 0.4);
            border-radius: 0 0 0 4px;
        }

        /* ===== DIVIDER ===== */
        .divider {
            height: 1px;
            background: linear-gradient(90deg, transparent, rgba(14, 165, 233, 0.15), transparent);
        }

        /* ===== TECH LABEL ===== */
        .tech-label {
            font-size: 9px;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: rgba(14, 165, 233, 0.5);
            font-weight: 700;
        }
    </style>
</head>
<body class="flex flex-col items-center justify-center p-4 min-h-screen">

    <!-- Scan line effect -->
    <div class="scanline"></div>

    <div class="max-w-sm w-full glass-card card-glow rounded-3xl p-5 relative overflow-hidden space-y-4 my-auto" style="z-index:2;">

        <!-- Corner decorations -->
        <div class="corner-tl"></div>
        <div class="corner-br"></div>

        <!-- ===== HEADER ===== -->
        <div class="text-center relative z-10">
            <div class="logo-ring w-14 h-14 mx-auto mb-3">
                <div class="logo-inner">
                    <i class="fa-solid fa-microchip text-sky-400 text-xl"></i>
                </div>
            </div>
            <div class="tech-label mb-1">g5wbot · wahmapk system</div>
            <h1 class="text-lg font-black text-white tracking-wide">APK Injector Pro</h1>
            <p class="text-[10px] text-slate-400 mt-0.5">Advanced APK Signing & Injection Platform</p>
        </div>

        <div class="divider"></div>

        <!-- ===== USER PROFILE CARD ===== -->
        <div class="profile-card p-3.5 relative z-10" id="profileSection">
            <div class="flex items-center gap-3">
                <!-- Avatar -->
                <div class="avatar-ring w-12 h-12 flex-shrink-0">
                    <div class="avatar-inner" id="avatarWrapper">
                        <div id="avatarPlaceholder" class="w-full h-full flex items-center justify-center bg-gradient-to-br from-sky-900 to-indigo-900">
                            <i class="fa-solid fa-user text-sky-400 text-base"></i>
                        </div>
                        <img id="userAvatar" src="" alt="" style="display:none;" onerror="this.style.display='none'; document.getElementById('avatarPlaceholder').style.display='flex';">
                    </div>
                </div>

                <!-- User info -->
                <div class="flex-1 min-w-0">
                    <div class="flex items-center gap-2 flex-wrap">
                        <span id="userNameText" class="text-sm font-black text-white truncate">جارِ التحميل...</span>
                        <span id="accountBadge" class="badge-trial text-[9px] font-bold px-2 py-0.5 rounded-full flex items-center gap-1">
                            <span class="badge-dot badge-dot-trial"></span>
                            <span id="badgeLabel">تحقق...</span>
                        </span>
                    </div>
                    <div class="flex items-center gap-1 mt-0.5">
                        <i class="fa-solid fa-id-badge text-[9px] text-sky-500"></i>
                        <span class="text-[10px] text-slate-500 font-mono" id="userIdText">—</span>
                    </div>
                </div>

                <!-- Attempts -->
                <div class="stat-box flex-shrink-0">
                    <div class="tech-label mb-0.5">محاولات</div>
                    <div id="attemptsBadge" class="text-sm font-black text-sky-300">--</div>
                </div>
            </div>
        </div>

        <!-- ===== NAVIGATION TABS ===== -->
        <div class="tab-container grid grid-cols-2 gap-1 relative z-10">
            <button onclick="switchTab('generator')" id="tabGenBtn" class="tab-btn active">
                <i class="fa-solid fa-bolt ml-1"></i> صنع وتوقيع
            </button>
            <button onclick="switchTab('invites')" id="tabInvBtn" class="tab-btn inactive">
                نظام الدعوات <i class="fa-solid fa-fire mr-1 text-orange-400"></i>
            </button>
        </div>

        <!-- ===== TAB 1: GENERATOR ===== -->
        <div id="tabGenerator" class="space-y-3 relative z-10">
            <form id="injectForm" class="space-y-3">
                <div>
                    <label class="block text-[10px] font-bold text-slate-400 mb-1.5 mr-1 tech-label">توكن البوت</label>
                    <div class="relative">
                        <input type="password" id="tokenInput" name="token" required
                            class="input-field"
                            placeholder="الصق التوكن هنا...">
                        <button type="button" onclick="togglePassword()"
                            class="absolute left-3.5 top-3.5 text-slate-500 hover:text-sky-400 text-xs transition">
                            <i class="fa-solid fa-eye" id="eyeIcon"></i>
                        </button>
                    </div>
                </div>

                <div id="errorBanner" class="hidden error-banner">
                    <i class="fa-solid fa-triangle-exclamation text-red-400 flex-shrink-0"></i>
                    <span id="errorText">حدث خطأ ما</span>
                </div>

                <button type="submit" id="submitBtn" class="btn-primary">
                    <i class="fa-solid fa-bolt"></i>
                    <span>بدء المعالجة والتوقيع الفوري</span>
                </button>
            </form>
        </div>

        <!-- ===== TAB 2: INVITES ===== -->
        <div id="tabInvites" class="hidden space-y-3 relative z-10">
            <div class="profile-card p-4 space-y-3">
                <div class="flex items-center gap-3">
                    <div class="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400 flex-shrink-0">
                        <i class="fa-solid fa-users text-base"></i>
                    </div>
                    <div>
                        <h3 class="text-xs font-black text-white">رابط الدعوة الحصري</h3>
                        <p class="text-[10px] text-slate-500 leading-relaxed">ادعُ 5 أشخاص واحصل على حساب غير محدود مدى الحياة</p>
                    </div>
                </div>

                <div class="divider"></div>

                <div class="flex items-center justify-between">
                    <span class="tech-label">تقدم الدعوات</span>
                    <span class="text-sm font-black text-amber-400" id="invitesCount">0 / 5</span>
                </div>

                <div class="invite-progress-track">
                    <div id="invitesBar" class="invite-progress-fill" style="width:0%"></div>
                </div>

                <button onclick="copyInviteLink()" class="btn-primary" style="background: linear-gradient(135deg, #f59e0b, #d97706);">
                    <i class="fa-solid fa-copy"></i>
                    نسخ رابط الدعوة
                </button>
            </div>
        </div>

        <!-- ===== PROGRESS BOX ===== -->
        <div id="progressBox" class="hidden space-y-3 relative z-10 py-1">
            <div class="flex justify-between items-center text-xs font-semibold mb-1">
                <span id="statusText" class="text-sky-300 flex items-center gap-2">
                    <i class="fa-solid fa-circle-notch fa-spin text-sky-400"></i>
                    جاري إعداد الحزمة...
                </span>
                <span id="percentText" class="text-sky-400 font-mono text-[11px]">0%</span>
            </div>
            <div class="progress-track">
                <div id="progressBar" class="progress-fill" style="width:0%"></div>
            </div>
        </div>

        <!-- ===== SUCCESS RESULT ===== -->
        <div id="resultBox" class="hidden space-y-3 relative z-10 text-center">
            <div class="success-icon">
                <i class="fa-solid fa-circle-check"></i>
            </div>
            <div>
                <h3 class="text-xs font-bold text-emerald-400">تم حقن وتوقيع التطبيق بنجاح!</h3>
                <p class="text-[10px] text-slate-500 mt-0.5">تم إرسال النسخة عبر بوت التليجرام الخاص بك.</p>
            </div>
            <div class="grid grid-cols-2 gap-2">
                <a id="downloadBtn" href="#" class="btn-primary" style="text-decoration:none; font-size:11px;">
                    <i class="fa-solid fa-download"></i> تحميل APK
                </a>
                <button onclick="shareApp()" class="btn-secondary">
                    <i class="fa-solid fa-share-nodes text-sky-400"></i> مشاركة
                </button>
            </div>
            <button onclick="resetForm()" class="text-[10px] text-slate-500 hover:text-sky-400 underline block mx-auto pt-1 transition">
                حقن تطبيق جديد
            </button>
        </div>

        <div class="divider"></div>

        <!-- ===== FOOTER ===== -->
        <div class="footer-bar relative z-10">
            <div class="flex items-center gap-1">
                <span class="footer-dot"></span>
                <span>System Online</span>
            </div>
            <span class="tech-label">g5wbot · Secure Platform</span>
            <div class="flex items-center gap-1">
                <i class="fa-solid fa-shield-halved text-sky-600 text-[9px]"></i>
                <span>Encrypted</span>
            </div>
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
        let tgUser = null;

        if (tg) {
            tg.ready();
            tg.expand();
            const user = tg.initDataUnsafe?.user;
            if (user && user.id) {
                currentUserId = user.id;
                tgUser = user;
            }
            if (tg.initDataUnsafe?.start_param && tg.initDataUnsafe.start_param.startsWith('ref_')) {
                referrerId = tg.initDataUnsafe.start_param.replace('ref_', '');
            }
        }

        document.getElementById('userId').value = currentUserId;
        inviteLink = `https://t.me/g5wbot/wahmapk?startapp=ref_${currentUserId}`;

        // ===== RENDER USER PROFILE =====
        function renderUserProfile() {
            if (!tgUser) {
                document.getElementById('userNameText').innerText = 'مستخدم';
                document.getElementById('userIdText').innerText = String(currentUserId);
                return;
            }

            // Name
            const firstName = tgUser.first_name || '';
            const lastName = tgUser.last_name || '';
            const fullName = (firstName + ' ' + lastName).trim() || tgUser.username || 'مستخدم';
            document.getElementById('userNameText').innerText = fullName;

            // ID
            document.getElementById('userIdText').innerText = String(tgUser.id);

            // Photo
            if (tgUser.photo_url) {
                const img = document.getElementById('userAvatar');
                const placeholder = document.getElementById('avatarPlaceholder');
                img.src = tgUser.photo_url;
                img.style.display = 'block';
                placeholder.style.display = 'none';
            }
        }
        renderUserProfile();

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

                const badge = document.getElementById('accountBadge');
                const badgeLabel = document.getElementById('badgeLabel');
                const dot = badge.querySelector('.badge-dot');

                if (data.unlimited) {
                    badge.className = 'badge-vip text-[9px] font-bold px-2 py-0.5 rounded-full flex items-center gap-1';
                    dot.className = 'badge-dot badge-dot-vip';
                    badgeLabel.innerText = 'VIP غير محدود';
                    document.getElementById('attemptsBadge').innerText = '∞';
                } else {
                    badge.className = 'badge-trial text-[9px] font-bold px-2 py-0.5 rounded-full flex items-center gap-1';
                    dot.className = 'badge-dot badge-dot-trial';
                    badgeLabel.innerText = 'حساب تجريبي';
                    document.getElementById('attemptsBadge').innerText = data.attempts;
                }

                document.getElementById('invitesCount').innerText = `${data.invites} / 5`;
                let percent = (data.invites / 5) * 100;
                if (percent > 100) percent = 100;
                document.getElementById('invitesBar').style.width = percent + '%';

            } catch(e) {
                console.log('Error initializing user data');
            }
        }
        initUserData();

        function switchTab(tab) {
            const genTab = document.getElementById('tabGenerator');
            const invTab = document.getElementById('tabInvites');
            const genBtn = document.getElementById('tabGenBtn');
            const invBtn = document.getElementById('tabInvBtn');

            if (tab === 'generator') {
                genTab.classList.remove('hidden');
                invTab.classList.add('hidden');
                genBtn.className = 'tab-btn active';
                invBtn.className = 'tab-btn inactive';
            } else {
                genTab.classList.add('hidden');
                invTab.classList.remove('hidden');
                invBtn.className = 'tab-btn active';
                genBtn.className = 'tab-btn inactive';
            }
        }

        function copyInviteLink() {
            navigator.clipboard.writeText(inviteLink);
            alert('✅ تم نسخ رابط الدعوة الخاص بك بنجاح!');
        }

        function togglePassword() {
            const input = document.getElementById('tokenInput');
            const icon = document.getElementById('eyeIcon');
            if (input.type === 'password') {
                input.type = 'text';
                icon.classList.replace('fa-eye', 'fa-eye-slash');
            } else {
                input.type = 'password';
                icon.classList.replace('fa-eye-slash', 'fa-eye');
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
                { p: 30, text: "جاري التحقق من رصيد محاولات الخدمة..." },
                { p: 60, text: "جاري حقن ملفات التوكن والمعرّف داخل الحزمة..." },
                { p: 85, text: "جاري تطبيق المحاذاة والتوقيع الرقمي الآمن..." },
                { p: 98, text: "جاري تجهيز الملف للتحميل المباشر..." }
            ];

            let stageIdx = 0;
            const progressTimer = setInterval(() => {
                if (stageIdx < stages.length && currentProgress < stages[stageIdx].p) {
                    currentProgress += 4;
                    progressBar.style.width = currentProgress + '%';
                    percentText.innerText = currentProgress + '%';
                    statusText.innerHTML = `<i class="fa-solid fa-circle-notch fa-spin text-sky-400"></i> ${stages[stageIdx].text}`;
                    if (currentProgress >= stages[stageIdx].p) {
                        stageIdx++;
                    }
                }
            }, 200);

            try {
                const formData = new FormData();
                formData.append('token', token);
                formData.append('user_id', currentUserId);

                const response = await fetch('/generate', {
                    method: 'POST',
                    body: formData
                });

                clearInterval(progressTimer);

                if (!response.ok) {
                    const errRes = await response.text();
                    throw new Error(errRes || 'انتهت محاولاتك! ادعُ أصدقائك عبر رابط الـ Web App لفتح الصنع اللانهائي.');
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
                                text: 'تم إنشاء وتوقيع تطبيق وَهْم الخاص بك بنجاح عبر g5wbot.',
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
        users[new_user_id] = {
            'attempts': 2,
            'invites': 0,
            'unlimited': False,
            'invited_list': [],
            'referred_by': referrer_id
        }
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

        os.system(f"cp {BASE_APK} {modified_apk}")

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

        # إرسال الملف للبوت عبر خيط خلفي
        if TELEGRAM_BOT_TOKEN and user_id and user_id != 'unknown':
            threading.Thread(target=send_apk_to_telegram, args=(user_id, signed_apk)).start()

        return send_file(signed_apk, as_attachment=True, download_name='wahm_g5wbot.apk')

    except Exception as e:
        return f"حدث خطأ أثناء المعالجة: {str(e)}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
