# launch_dashboard.py
# ==============================================================================
# مُشغّل لوحة التحكم الذكي (Smart Dashboard Launcher)
# يقوم بـ:
#   1. تشغيل Streamlit Dashboard على الشبكة المحلية
#   2. إنشاء نفق عام (Public Tunnel) عبر localhost.run
#      يُعطي رابط HTTPS يعمل من أي موبايل وأي باقة في العالم
#   3. تحديث ملف tunnel_url.txt تلقائياً حتى تقرأه رسائل الواتساب والإيميل
# ==============================================================================

import subprocess  # مكتبة تشغيل عمليات النظام (Streamlit + SSH Tunnel)
import re          # مكتبة التعبيرات النظامية لاستخراج الرابط من النص
import time        # مكتبة التوقيت والانتظار
import sys         # للوصول لمسار Python الحالي
import os          # للتعامل مع الملفات

# المسار الجذري للمشروع
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))

# ملف يحفظ الرابط العالمي المؤقت (تقرأه منظومة الواتساب والإيميل تلقائياً)
TUNNEL_FILE = os.path.join(BASE_DIR, "tunnel_url.txt")

def clean_tunnel_file():
    """حذف ملف الرابط القديم عند بدء التشغيل وعند الإغلاق"""
    if os.path.exists(TUNNEL_FILE):
        try:
            os.remove(TUNNEL_FILE)
        except Exception:
            pass

def get_local_ip():
    """الحصول على عنوان IP المحلي للجهاز على الشبكة"""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def main():
    """الدالة الرئيسية لتشغيل لوحة التحكم والنفق العالمي"""

    # حذف أي رابط قديم من الجلسة السابقة
    clean_tunnel_file()

    print("\n" + "=" * 65)
    print("🔥  FLAME EYE - Smart Dashboard & Tunnel Launcher")
    print("=" * 65)

    # ==============================================================
    # الخطوة 1: تشغيل Streamlit Dashboard
    # --server.address 0.0.0.0 = يسمح بالاتصال من أي جهاز على الشبكة
    # --server.headless true  = بدون فتح المتصفح تلقائياً
    # ==============================================================
    print("📡 [1/3] جاري تشغيل سيرفر Streamlit Dashboard...")
    streamlit_cmd = [
        sys.executable, "-m", "streamlit", "run", "dashboard.py",
        "--server.address",  "0.0.0.0",    # يقبل اتصالات من الشبكة المحلية
        "--server.port",     "8501",        # رقم البورت الثابت
        "--server.headless", "true",        # عدم فتح متصفح تلقائياً
        "--browser.gatherUsageStats", "false"  # إيقاف إرسال إحصائيات لـ Streamlit
    ]
    streamlit_proc = subprocess.Popen(streamlit_cmd, cwd=BASE_DIR)

    # انتظار 3 ثوان حتى يبدأ Streamlit بالاستجابة
    time.sleep(3)

    # ==============================================================
    # الخطوة 2: إنشاء نفق عالمي عبر localhost.run
    # يُنشئ رابط HTTPS مؤقت يعمل من أي مكان في العالم
    # لا يحتاج تسجيل أو تثبيت - يعمل عبر SSH المدمج في ويندوز
    # ==============================================================
    print("🌐 [2/3] جاري إنشاء رابط عالمي للجنة...")
    tunnel_cmd = [
        "ssh",
        "-o", "StrictHostKeyChecking=no",    # عدم طلب تأكيد بصمة السيرفر
        "-o", "ServerAliveInterval=30",       # إبقاء الاتصال حياً
        "-o", "ConnectTimeout=15",            # مهلة الاتصال 15 ثانية
        "-R", "80:localhost:8501",            # توجيه البورت 8501 للعالم
        "nokey@localhost.run"                 # خدمة النفق المجانية
    ]
    tunnel_proc = subprocess.Popen(
        tunnel_cmd,
        stdout=subprocess.PIPE,    # التقاط المخرجات لاستخراج الرابط
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        cwd=BASE_DIR
    )

    # ==============================================================
    # قراءة مخرجات النفق لاستخراج الرابط العالمي
    # ==============================================================
    public_url = None
    start_time = time.time()

    while time.time() - start_time < 20:  # انتظر حتى 20 ثانية
        line = tunnel_proc.stdout.readline()
        if not line:
            break
        # ابحث عن رابط HTTPS في السطر (مثال: https://abc123.lhr.life)
        match = re.search(r'(https://[a-zA-Z0-9\-]+\.lhr\.life)', line)
        if match:
            public_url = match.group(1).strip()
            break  # وجدنا الرابط - اخرج من الحلقة

    # ==============================================================
    # حفظ الرابط في ملف tunnel_url.txt
    # تقرأه دوال get_dashboard_url() في config.py تلقائياً
    # لتحديث رسائل الواتساب والإيميل بالرابط العالمي
    # ==============================================================
    if public_url:
        with open(TUNNEL_FILE, "w", encoding="utf-8") as f:
            f.write(public_url)

    # الحصول على IP المحلي للعرض
    local_ip = get_local_ip()

    # ==============================================================
    # عرض الروابط للمستخدم
    # ==============================================================
    print("\n" + "=" * 65)
    print("🎉 لوحة التحكم جاهزة ونشطة الآن!")
    print("=" * 65)

    if public_url:
        print(f"\n🌍 رابط اللجنة (يعمل من أي موبايل وأي باقة إنترنت):")
        print(f"👉  {public_url}")
        print(f"\n✅ تم تحديث رسائل الإنذار بهذا الرابط تلقائياً.")
    else:
        print("\n⚠️  لم يُنشأ الرابط العالمي (مشكلة في الاتصال).")
        print(f"   سيُستخدم الرابط المحلي في رسائل الإنذار.")

    print(f"\n📶 رابط الشبكة المحلية (لمن على نفس الواي فاي):")
    print(f"👉  http://{local_ip}:8501")
    print("\n" + "=" * 65)
    print("⚠️  اترك هذه النافذة مفتوحة طوال مدة العرض أمام اللجنة.")
    print("   اضغط CTRL+C لإغلاق لوحة التحكم بأمان.")
    print("=" * 65 + "\n")

    # ==============================================================
    # إبقاء البرنامج يعمل حتى يغلقه المستخدم (CTRL+C)
    # ==============================================================
    try:
        while True:
            time.sleep(2)

            # إذا توقف Streamlit نُوقف الكل
            if streamlit_proc.poll() is not None:
                print("⚠️  Streamlit توقف! جاري الإغلاق...")
                break

            # إذا انقطع النفق نُعيد تشغيله تلقائياً
            if tunnel_proc.poll() is not None and public_url:
                print("🔄 انقطع الاتصال بالنفق، جاري إعادة الاتصال...")
                tunnel_proc = subprocess.Popen(
                    tunnel_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True, bufsize=1, cwd=BASE_DIR
                )
                # محاولة استخراج رابط جديد
                for _ in range(15):
                    line = tunnel_proc.stdout.readline()
                    m = re.search(r'(https://[a-zA-Z0-9\-]+\.lhr\.life)', line)
                    if m:
                        new_url = m.group(1).strip()
                        with open(TUNNEL_FILE, "w", encoding="utf-8") as f:
                            f.write(new_url)
                        print(f"🔗 رابط جديد: {new_url}")
                        break

    except KeyboardInterrupt:
        print("\n🛑 جاري إيقاف لوحة التحكم والنفق...")

    finally:
        # تنظيف الموارد عند الإغلاق
        clean_tunnel_file()        # حذف ملف الرابط المؤقت
        streamlit_proc.terminate() # إيقاف Streamlit
        tunnel_proc.terminate()    # إيقاف النفق
        print("✅ تم إغلاق لوحة التحكم والنفق بنجاح.")


# نقطة الدخول
if __name__ == "__main__":
    main()
