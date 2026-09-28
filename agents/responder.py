# agents/responder.py
# ==============================================================================
# وكيل التنبيه والاستجابة (The Responder) - المسؤول عن:
#   1. تشغيل صفارة الإنذار الصوتية فور رصد الخطر
#   2. إرسال رسالة واتساب فورية بالرابط السحابي ورابط لوحة التحكم
#   3. إرسال إيميل احترافي مع إرفاق الفيديو كاملاً
# ==============================================================================

import time                              # مكتبة التوقيت
import requests                          # مكتبة إرسال طلبات HTTP
import urllib.parse                      # مكتبة ترميز النصوص للروابط
import smtplib                           # مكتبة إرسال الإيميل عبر SMTP
import pygame                            # مكتبة تشغيل الصوت
import os                                # مكتبة التعامل مع الملفات
from email.mime.text        import MIMEText       # نص الإيميل
from email.mime.multipart   import MIMEMultipart  # هيكل الإيميل المركّب
from email.mime.base        import MIMEBase       # قاعدة المرفقات
from email                  import encoders       # ترميز المرفقات بـ Base64
import config                            # إعدادات النظام الموحدة

class ResponderAgent:
    """
    وكيل الاستجابة الطارئة:
    يُطلق التنبيهات الصوتية ويُرسل إشعارات الواتساب والإيميل
    مع رابط الفيديو السحابي ورابط لوحة التحكم المباشرة
    """

    def __init__(self):
        # تهيئة نظام الصوت (pygame mixer) لتشغيل صفارة الإنذار
        pygame.mixer.init()

    # ==============================================================================
    # تشغيل صفارة الإنذار الصوتية
    # ==============================================================================
    def play_siren(self):
        """
        تشغيل صوت صفارة الإنذار إذا كانت ملف الصوت موجوداً
        ولم تكن الصفارة تعزف بالفعل (لمنع التشغيل المتداخل)
        """
        if (os.path.exists(config.ALARM_SOUND_PATH)
                and not pygame.mixer.music.get_busy()):
            pygame.mixer.music.load(config.ALARM_SOUND_PATH)
            pygame.mixer.music.play()

    # ==============================================================================
    # إرسال رسالة واتساب عبر CallMeBot
    # ==============================================================================
    def send_whatsapp(self, hazard_label, people_summary, cloud_url=""):
        """
        إرسال رسالة واتساب فورية تحتوي على:
        - نوع الخطر المرصود
        - موقع الكاميرا
        - الأشخاص المتواجدين
        - رابط مشاهدة الفيديو السحابي مباشرة
        - رابط لوحة تحكم النظام (يعمل على نفس الواي فاي)
        """
        # الرابط السحابي للفيديو (أو رابط الإيميل كبديل إذا فشل الرفع)
        video_link = cloud_url if cloud_url else "https://mail.google.com/mail/u/0/#inbox"

        # رابط لوحة التحكم - يُقرأ ديناميكياً لضمان أحدث رابط
        dashboard_link = config.get_dashboard_url()

        # بناء نص الرسالة الكاملة
        message = (
            f"🚨 إنذار طوارئ: تم رصد {hazard_label}\n"
            f"📍 الموقع: {config.LOCATION_TAG}\n"
            f"👥 الأشخاص: {people_summary}\n\n"
            f"▶️ رابط مشاهدة فيديو الحدث (30 ثانية):\n"
            f"{video_link}\n\n"
            f"🖥️ لوحة التحكم (افتح على نفس الواي فاي):\n"
            f"{dashboard_link}"
        )

        try:
            # إزالة علامة + من رقم الهاتف (CallMeBot يحتاج الرقم بدونها)
            phone = config.TARGET_PHONE.replace("+", "").strip()

            # ترميز الرسالة لتكون آمنة في رابط URL
            msg_encoded = urllib.parse.quote(message)

            # بناء رابط API الخاص بـ CallMeBot
            api_url = (
                f"https://api.callmebot.com/whatsapp.php"
                f"?phone={phone}"
                f"&text={msg_encoded}"
                f"&apikey={config.CALLMEBOT_API_KEY}"
            )

            # إرسال الطلب لـ CallMeBot
            response = requests.get(api_url, timeout=12)
            print(f"📡 رد CallMeBot: {response.text.strip()[:100]}")
            print("✅ تم تسليم رسالة الواتساب بنجاح!")

        except Exception as e:
            print(f"⚠️ خطأ أثناء إرسال الواتساب: {e}")

    # ==============================================================================
    # إرسال إيميل طوارئ مع مرفق الفيديو
    # ==============================================================================
    def send_email(self, video_path, hazard_label, people_summary, cloud_url=""):
        """
        إرسال إيميل طوارئ احترافي يحتوي على:
        - تفاصيل الحادثة كاملة
        - رابط الفيديو السحابي
        - رابط لوحة التحكم
        - الفيديو كمرفق مباشر في الإيميل (30 ثانية)
        """
        print(f"📧 [Responder] جاري إعداد وإرسال الإيميل إلى {config.TARGET_EMAIL}...")

        try:
            # إنشاء هيكل الإيميل المركّب (نص + مرفقات)
            msg = MIMEMultipart()
            msg['From']    = config.SENDER_EMAIL
            msg['To']      = config.TARGET_EMAIL
            msg['Subject'] = f"🚨 إنذار طارئ: {hazard_label} | {config.LOCATION_TAG}"

            # قراءة رابط لوحة التحكم ديناميكياً
            dashboard_link = config.get_dashboard_url()

            # -----------------------------------------------------------
            # بناء نص الإيميل الكامل
            # -----------------------------------------------------------
            body = f"""
تحذير أمني عاجل من نظام Flame Eye (المراقبة الذاتية متعددة الوكلاء):
==================================================

📋 تفاصيل الحادثة:
- نوع الخطر: {hazard_label}
- الموقع:    {config.LOCATION_TAG}
- التوقيت:   {time.strftime('%Y-%m-%d %H:%M:%S')}
- الأشخاص:   {people_summary}

==================================================

▶️ رابط مشاهدة فيديو الحدث مباشرة (30 ثانية):
{cloud_url if cloud_url else 'الفيديو مرفق في نهاية هذه الرسالة'}

🖥️ لوحة تحكم النظام (تقارير + مشاهدة + تحميل):
{dashboard_link}
(افتح الرابط من أي جهاز على نفس شبكة الواي فاي)

==================================================
تم إرفاق مقطع الفيديو (30 ثانية) مع هذه الرسالة للمراجعة الفورية.
            """

            # إرفاق نص الإيميل (UTF-8 لدعم العربية)
            msg.attach(MIMEText(body, 'plain', 'utf-8'))

            # -----------------------------------------------------------
            # إرفاق ملف الفيديو كمرفق في الإيميل
            # -----------------------------------------------------------
            if os.path.exists(video_path):
                with open(video_path, "rb") as video_file:
                    attachment = MIMEBase("application", "octet-stream")
                    attachment.set_payload(video_file.read())

                encoders.encode_base64(attachment)  # ترميز الفيديو بـ Base64

                # اسم الملف المرفق (يظهر للمستلم)
                video_filename = os.path.basename(video_path)
                attachment.add_header(
                    "Content-Disposition",
                    f'attachment; filename="{video_filename}"'
                )
                msg.attach(attachment)
                print(f"📎 تم إرفاق الفيديو: {video_filename}")

            # -----------------------------------------------------------
            # الاتصال بسيرفر Gmail وإرسال الإيميل
            # -----------------------------------------------------------
            with smtplib.SMTP("smtp.gmail.com", 587, timeout=60) as server:
                server.starttls()  # تفعيل التشفير TLS
                server.login(config.SENDER_EMAIL, config.SENDER_PASSWORD)
                server.send_message(msg)
                print("✅ تم إرسال الإيميل مع مرفق الفيديو بنجاح!")

        except Exception as e:
            print(f"⚠️ تعذر إرسال الإيميل: {e}")