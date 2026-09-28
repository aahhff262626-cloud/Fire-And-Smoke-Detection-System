# agents/reporter.py
# ==============================================================================
# وكيل التسجيل والتوثيق السحابي (The Reporter) - المسؤول عن:
#   1. تسجيل مقطع فيديو 30 ثانية عند رصد أي خطر
#   2. رفع الفيديو لأفضل سحابة متاحة بالترتيب:
#      أولاً: uguu.se (الأسرع والأكثر موثوقية من مصر)
#      ثانياً: catbox.moe (احتياطي)
#      ثالثاً: Cloudinary (احتياطي أخير)
#   3. توثيق الحادثة في ملف fires.log
# ==============================================================================

import cv2                      # مكتبة معالجة الفيديو وكتابة الإطارات
import time                     # مكتبة التوقيت وحساب المدة
import os                       # مكتبة التعامل مع الملفات
import json                     # مكتبة تحليل استجابات JSON
import requests                 # مكتبة إرسال طلبات HTTP للسحابات
import config                   # إعدادات النظام الموحدة
import cloudinary               # مكتبة Cloudinary السحابية (احتياطي)
import cloudinary.uploader

# -----------------------------------------------------------
# تهيئة سحابة Cloudinary (تُستخدم كخيار احتياطي أخير)
# -----------------------------------------------------------
try:
    cloudinary.config(
        cloud_name = str(config.CLOUDINARY_CLOUD_NAME).strip(),
        api_key    = str(config.CLOUDINARY_API_KEY).strip(),
        api_secret = str(config.CLOUDINARY_API_SECRET).strip(),
        secure     = True  # استخدام HTTPS دائماً
    )
except Exception:
    pass  # إذا فشل الاتصال بـ Cloudinary يستمر النظام

class ReporterAgent:
    """
    وكيل التسجيل والتوثيق:
    يسجل الفيديو لمدة 30 ثانية ويرفعه سحابياً ويوثق الحادثة
    """

    def __init__(self):
        # -----------------------------------------------------------
        # متغيرات حالة التسجيل
        # -----------------------------------------------------------
        self.is_recording       = False  # هل التسجيل جارٍ حالياً؟
        self.writer             = None   # كائن كتابة الفيديو (VideoWriter)
        self.current_video_path = ""     # مسار ملف الفيديو المُسجَّل حالياً
        self.start_time         = 0      # وقت بدء التسجيل (بالثواني)

    # ==============================================================================
    # بدء تسجيل فيديو جديد
    # ==============================================================================
    def start_recording(self):
        """
        بدء تسجيل مقطع فيديو جديد بدقة 640x360 بـ 15 إطار/ثانية
        يُسمَّى الملف باسم يحتوي على التاريخ والوقت لسهولة التعرف عليه
        """
        self.is_recording = True
        self.start_time   = time.time()  # حفظ وقت البدء

        # توليد اسم الملف من التاريخ والوقت (مثال: alert_20260928_213000.mp4)
        timestamp                = time.strftime("%Y%m%d_%H%M%S")
        self.current_video_path  = os.path.join(
            config.OUTPUT_DIR, f"alert_{timestamp}.mp4"
        )

        # إعداد كائب كتابة الفيديو بترميز mp4v
        fourcc      = cv2.VideoWriter_fourcc(*'mp4v')  # ترميز الفيديو
        self.writer = cv2.VideoWriter(
            self.current_video_path,
            fourcc,
            15.0,        # معدل الإطارات (Frames Per Second)
            (640, 360)   # دقة الفيديو المُسجَّل (توازن بين الحجم والجودة)
        )
        return self.current_video_path

    # ==============================================================================
    # كتابة إطار للفيديو الجاري تسجيله
    # ==============================================================================
    def write_frame(self, frame):
        """
        إضافة إطار جديد للفيديو المُسجَّل.
        يُعيد True إذا اكتملت مدة الـ 30 ثانية وتوقف التسجيل تلقائياً.
        يُعيد False إذا كان التسجيل ما زال جارياً.
        """
        if self.is_recording and self.writer:
            # تصغير الإطار لدقة التسجيل (640x360) قبل حفظه
            small_frame = cv2.resize(frame, (640, 360))
            self.writer.write(small_frame)

            # فحص إذا اكتملت مدة التسجيل المطلوبة
            elapsed = time.time() - self.start_time
            if elapsed >= config.RECORD_DURATION:
                self.stop_recording()
                return True  # التسجيل اكتمل

        return False  # التسجيل ما زال جارياً

    # ==============================================================================
    # إيقاف التسجيل وإغلاق الملف
    # ==============================================================================
    def stop_recording(self):
        """إيقاف التسجيل وحفظ ملف الفيديو على القرص"""
        self.is_recording = False
        if self.writer:
            self.writer.release()  # إغلاق ملف الفيديو وحفظه
            self.writer = None

    # ==============================================================================
    # رفع الفيديو للسحابة - يجرب ثلاث خدمات بالترتيب
    # ==============================================================================
    def upload_to_cloud(self, video_path):
        """
        رفع الفيديو لأول سحابة تعمل بنجاح من القائمة التالية:
        1. uguu.se    - الأفضل والأسرع من مصر (يعمل دائماً)
        2. catbox.moe - احتياطي (أحياناً يكون بطيئاً)
        3. Cloudinary - احتياطي أخير (يحتاج API صحيحة)
        يُعيد الرابط المباشر للفيديو، أو None إذا فشل الجميع
        """

        # ===============================================================
        # محاولة 1: رفع الفيديو على uguu.se (الأسرع والأكثر موثوقية)
        # يعمل دائماً من مصر، يعطي رابط HTTPS مباشر يُفتح فوراً
        # ===============================================================
        try:
            print("☁️ [Reporter] جاري الرفع على uguu.se (سحابة مجانية سريعة)...")
            with open(video_path, "rb") as f:
                response = requests.post(
                    "https://uguu.se/upload.php",
                    files={"files[]": f},
                    timeout=30  # انتظار 30 ثانية قبل الاستسلام
                )

            if response.status_code == 200:
                data = response.json()
                # استخراج الرابط من استجابة JSON
                files_list = data.get("files", [])
                if files_list and "url" in files_list[0]:
                    cloud_url = files_list[0]["url"]
                    print(f"✅ تم الرفع على uguu.se بنجاح!\n🔗 {cloud_url}")
                    return cloud_url

        except Exception as e:
            print(f"⚠️ uguu.se غير متاح: {e}")

        # ===============================================================
        # محاولة 2: رفع الفيديو على catbox.moe (رابط دائم مدى الحياة)
        # ===============================================================
        try:
            print("☁️ [Reporter] جاري المحاولة على catbox.moe...")
            with open(video_path, "rb") as f:
                response = requests.post(
                    "https://catbox.moe/user/api.php",
                    data={"reqtype": "fileupload"},
                    files={"fileToUpload": f},
                    timeout=30
                )
            if response.status_code == 200 and response.text.startswith("http"):
                cloud_url = response.text.strip()
                print(f"✅ تم الرفع على catbox.moe بنجاح!\n🔗 {cloud_url}")
                return cloud_url

        except Exception as e:
            print(f"⚠️ catbox.moe غير متاح: {e}")

        # ===============================================================
        # محاولة 3: رفع الفيديو على Cloudinary (تحتاج API صحيحة)
        # ===============================================================
        try:
            print("☁️ [Reporter] جاري المحاولة على Cloudinary...")
            result    = cloudinary.uploader.upload(
                video_path,
                resource_type="video"
            )
            cloud_url = result.get("secure_url", "")
            if cloud_url:
                print(f"✅ تم الرفع على Cloudinary بنجاح!\n🔗 {cloud_url}")
                return cloud_url

        except Exception as e:
            print(f"⚠️ Cloudinary غير متاح: {e}")

        # إذا فشلت جميع المحاولات
        print("❌ [Reporter] فشل الرفع السحابي على جميع الخدمات. الفيديو محفوظ محلياً.")
        return None

    # ==============================================================================
    # توثيق الحادثة في ملف السجل
    # ==============================================================================
    def log_incident(self, hazard_label, people_summary, cloud_url=""):
        """
        تسجيل تفاصيل الحادثة في ملف fires.log للمراجعة لاحقاً.
        يظهر في الداشبورد تحت قسم سجل التدقيق الأمني.
        """
        with open(config.LOG_FILE, "a", encoding="utf-8") as f:
            # بناء سطر السجل بكل التفاصيل
            log_entry = (
                f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] "
                f"خطر: {hazard_label} | "
                f"موقع: {config.LOCATION_TAG} | "
                f"أشخاص: {people_summary} | "
                f"رابط: {cloud_url or 'محلي فقط'}\n"
            )
            f.write(log_entry)

        print("📝 [Reporter] تم توثيق الحادثة في fires.log")