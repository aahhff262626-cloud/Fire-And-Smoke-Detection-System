# agents/responder.py
import time
import requests
import urllib.parse
import smtplib
import pygame
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import config

class ResponderAgent:
    def __init__(self):
        pygame.mixer.init()

    def play_siren(self):
        """تشغيل سرينة الإنذار."""
        if os.path.exists(config.ALARM_SOUND_PATH) and not pygame.mixer.music.get_busy():
            pygame.mixer.music.load(config.ALARM_SOUND_PATH)
            pygame.mixer.music.play()

    def send_whatsapp(self, hazard_label, people_summary):
        """إرسال تنبيه الواتساب السريع."""
        message = (
            f"إنذار طوارئ: تم رصد {hazard_label}\n"
            f"الموقع: {config.LOCATION_TAG}\n"
            f"الأشخاص: {people_summary}\n\n"
            f"تم إرسال الفيديو إلى بريدك:\nhttps://mail.google.com/mail/u/0/#inbox"
        )
        try:
            phone = config.TARGET_PHONE.replace("+", "").strip()
            msg_enc = urllib.parse.quote(message)
            url = f"https://api.callmebot.com/whatsapp.php?phone={phone}&text={msg_enc}&apikey={config.CALLMEBOT_API_KEY}"
            requests.get(url, timeout=10)
            print("✅ [Responder] تم إرسال رسالة الواتساب بنجاح.")
        except Exception as e:
            print(f"⚠️ [Responder] تعذر إرسال الواتساب: {e}")

    def send_email(self, video_path, hazard_label, people_summary):
        """إرسال الإيميل مع تقرير بالحدث ومرفق الفيديو."""
        try:
            msg = MIMEMultipart()
            msg['From'] = config.SENDER_EMAIL
            msg['To'] = config.TARGET_EMAIL
            msg['Subject'] = f"🚨 إنذار طارئ: رصد {hazard_label} في {config.LOCATION_TAG}"

            body = f"""
تقرير أمني عاجل من نظام المراقبة:
------------------------------------------
- نوع الخطر: {hazard_label}
- الموقع: {config.LOCATION_TAG}
- التوقيت: {time.strftime('%Y-%m-%d %H:%M:%S')}
- الأشخاص: {people_summary}
------------------------------------------
الفيديو مدته 30 ثانية مرفق مع هذه الرسالة.
            """
            msg.attach(MIMEText(body, 'plain', 'utf-8'))

            if os.path.exists(video_path):
                with open(video_path, "rb") as f:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header("Content-Disposition", f'attachment; filename="{os.path.basename(video_path)}"')
                msg.attach(part)

            with smtplib.SMTP("smtp.gmail.com", 587, timeout=25) as server:
                server.starttls()
                server.login(config.SENDER_EMAIL, config.SENDER_PASSWORD)
                server.send_message(msg)
                print("✅ [Responder] تم إرسال الإيميل ومرفق الفيديو بنجاح.")
        except Exception as e:
            print(f"⚠️ [Responder] تعذر إرسال الإيميل: {e}")