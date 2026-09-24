# ==============================================================================
# نظام الإنذار الذكي المتكامل - الإصدار السريع وخفيف الحجم
# ==============================================================================

import os
import cv2
import time
import requests
import urllib.parse
import smtplib
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

import pygame
from ultralytics import YOLO

# ==============================================================================
# 1) البيانات والإعدادات
# ==============================================================================

LOCATION_TAG = "مصنع - قسم التشغيل الرئيسي (Factory - Main Section)"

# بيانات التواصل الخاصة بك
TARGET_EMAIL = "aahhff262626@gmail.com"
TARGET_PHONE = "+201060034154"
CALLMEBOT_API_KEY = "1388599"

# إعدادات إرسال الإيميل المعتمدة
SENDER_EMAIL = "aahhff262626@gmail.com"
SENDER_PASSWORD = "eudu rlps wyat zeok"

# إعدادات الكاميرا والتسجيل (دقة خفيفة وسريعة الرفع 640x360)
CAMERA_INDEX = 0
RECORD_DURATION = 30                           # 30 ثانية
REC_WIDTH = 640                                # دقة خفيفة لتقليل الحجم إلى 2-3 ميجا
REC_HEIGHT = 360
REC_FPS = 15.0

ALERT_COOLDOWN = 60
OUTPUT_DIR = "alert_records"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ملفات النماذج والأصوات
FIRE_MODEL_PATH = "fire.pt"
ALARM_SOUND_PATH = "alarm_new.mp3"

FACE_PROTO = "opencv_face_detector.pbtxt"
FACE_MODEL = "opencv_face_detector_uint8.pb"
AGE_PROTO = "age_deploy.prototxt"
AGE_MODEL = "age_net.caffemodel"
GENDER_PROTO = "gender_deploy.prototxt"
GENDER_MODEL = "gender_net.caffemodel"

# ==============================================================================
# 2) تهيئة مشغل الصوت والنماذج
# ==============================================================================

pygame.mixer.init()

if not os.path.exists(FIRE_MODEL_PATH):
    raise FileNotFoundError(f"ملف نموذج الحريق غير موجود: {FIRE_MODEL_PATH}")
fire_model = YOLO(FIRE_MODEL_PATH)

MODEL_MEAN_VALUES = (78.4263377603, 87.7689143744, 114.895847746)
AGE_LIST = ['(0-2)', '(4-6)', '(8-12)', '(15-20)', '(25-32)', '(38-43)', '(48-53)', '(60-100)']
GENDER_LIST = ['ذكر (Male)', 'أنثى (Female)']

face_net = cv2.dnn.readNet(FACE_MODEL, FACE_PROTO)
age_net = cv2.dnn.readNet(AGE_MODEL, AGE_PROTO)
gender_net = cv2.dnn.readNet(GENDER_MODEL, GENDER_PROTO)

# ==============================================================================
# 3) كشف الأشخاص وتحديد النوع والعمر
# ==============================================================================

def detect_faces_and_info(frame, conf_threshold=0.6):
    h, w = frame.shape[:2]
    blob = cv2.dnn.blobFromImage(frame, 1.0, (300, 300), [104, 117, 123], swapRB=False, crop=False)
    face_net.setInput(blob)
    detections = face_net.forward()

    faces_info = []
    for i in range(detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        if confidence > conf_threshold:
            x1 = int(detections[0, 0, i, 3] * w)
            y1 = int(detections[0, 0, i, 4] * h)
            x2 = int(detections[0, 0, i, 5] * w)
            y2 = int(detections[0, 0, i, 6] * h)

            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w - 1, x2), min(h - 1, y2)

            face = frame[y1:y2, x1:x2]
            if face.shape[0] < 20 or face.shape[1] < 20:
                continue

            blob_gender = cv2.dnn.blobFromImage(face, 1.0, (227, 227), MODEL_MEAN_VALUES, swapRB=False)
            gender_net.setInput(blob_gender)
            gender = GENDER_LIST[gender_net.forward()[0].argmax()]

            blob_age = cv2.dnn.blobFromImage(face, 1.0, (227, 227), MODEL_MEAN_VALUES, swapRB=False)
            age_net.setInput(blob_age)
            age = AGE_LIST[age_net.forward()[0].argmax()]

            faces_info.append((x1, y1, x2, y2, gender, age))

    return faces_info

# ==============================================================================
# 4) دوال الإرسال الفوري (WhatsApp أولاً ثم Email)
# ==============================================================================

def send_whatsapp_alert(hazard_type, people_summary):
    """إرسال تنبيه الواتساب السريع أولاً."""
    email_inbox_link = "https://mail.google.com/mail/u/0/#inbox"
    message_text = (
        f"إنذار طوارئ: تم رصد {hazard_type}\n"
        f"الموقع: {LOCATION_TAG}\n"
        f"الأشخاص: {people_summary}\n\n"
        f"تم إرسال الفيديو (30 ثانية) إلى بريدك:\n"
        f"{email_inbox_link}"
    )

    print(f"📱 [1/2] جاري إرسال إشعار الواتساب إلى {TARGET_PHONE}...")
    try:
        phone_clean = TARGET_PHONE.replace("+", "").strip()
        msg_encoded = urllib.parse.quote(message_text)
        url = f"https://api.callmebot.com/whatsapp.php?phone={phone_clean}&text={msg_encoded}&apikey={CALLMEBOT_API_KEY}"
        res = requests.get(url, timeout=10)
        print(f"📡 رد سيرفر الواتساب: {res.text.strip()}")
        if res.status_code == 200:
            print("✅ تم تسليم رسالة الواتساب بنجاح!")
    except Exception as e:
        print(f"⚠️ خطأ الواتساب: {e}")


def send_email_alert(video_filename, hazard_type, people_summary):
    """إرسال الإيميل مع مرفق الفيديو الخفيف."""
    print(f"📧 [2/2] جاري إرسال الإيميل ومرفق الفيديو إلى {TARGET_EMAIL}...")
    try:
        file_size_mb = os.path.getsize(video_filename) / (1024 * 1024)
        print(f"📦 حجم الفيديو: {file_size_mb:.2f} ميجابايت (حجم ممتاز وخفيف).")

        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = TARGET_EMAIL
        msg['Subject'] = f"🚨 إنذار طارئ: رصد {hazard_type} في {LOCATION_TAG}"

        body = f"""
تحذير عاجل من نظام المراقبة الذكي:
--------------------------------------------------
- نوع الخطر: {hazard_type}
- الموقع: {LOCATION_TAG}
- التوقيت: {time.strftime('%Y-%m-%d %H:%M:%S')}
- الأشخاص في المكان: {people_summary}
--------------------------------------------------
(فيديو الحدث مدته 30 ثانية مرفق مع هذه الرسالة)
        """
        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        # إرفاق الفيديو
        if os.path.exists(video_filename):
            with open(video_filename, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename={os.path.basename(video_filename)}")
            msg.attach(part)

        # الاتصال بـ Gmail
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=25) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
            print("✅ تم إرسال الإيميل ومرفق الفيديو بنجاح!")

    except Exception as e:
        print(f"⚠️ خطأ الإيميل: {e}")


def dispatch_alerts_background(video_path, hazard_type, people_summary):
    """إرسال التنبيهات في الخلفية مع تقديم الواتساب أولاً."""
    # 1. إرسال الواتساب أولاً ليصلك فوراً
    send_whatsapp_alert(hazard_type, people_summary)
    
    # 2. إرسال الإيميل مع ملف الفيديو
    send_email_alert(video_path, hazard_type, people_summary)

# ==============================================================================
# 5) تشغيل الكاميرا وحلقة المراقبة
# ==============================================================================

cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
if not cap.isOpened():
    raise RuntimeError("تعذر فتح الكاميرا.")

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

is_recording = False
record_start_time = 0
video_writer = None
current_video_path = ""
current_hazard_label = ""
current_people_summary = ""
last_global_alert_time = 0

print("=" * 60)
print(f"🟢 نظام المراقبة يعمل الآن في: {LOCATION_TAG}")
print(f"📩 الإيميل: {TARGET_EMAIL}")
print(f"📱 الواتساب: {TARGET_PHONE}")
print("=" * 60)

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        hazard_detected = False
        hazard_label = ""

        # فحص الحريق والدخان
        results = fire_model.predict(frame, conf=0.50, imgsz=640, verbose=False)
        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = [int(v) for v in box.xyxy[0]]
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])
                name = fire_model.names.get(cls_id, str(cls_id)).lower()

                if "smoke" in name and conf < 0.70:
                    continue

                hazard_detected = True
                hazard_label = "حريق (Fire)" if "fire" in name else "دخان / غاز (Smoke)"

                color = (0, 0, 255) if "fire" in name else (0, 140, 255)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame, f"{hazard_label} {conf*100:.1f}%", (x1, max(y1 - 10, 25)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        # فحص الأشخاص
        detected_people = []
        try:
            faces = detect_faces_and_info(frame)
            for x1, y1, x2, y2, gender, age in faces:
                detected_people.append(f"{gender} {age}")
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f"{gender} {age}", (x1, max(y1 - 10, 25)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        except Exception:
            pass

        people_summary = ", ".join(detected_people) if detected_people else "لا يوجد أشخاص"

        # عند رصد الخطر
        current_time = time.time()
        if hazard_detected:
            if os.path.exists(ALARM_SOUND_PATH) and not pygame.mixer.music.get_busy():
                pygame.mixer.music.load(ALARM_SOUND_PATH)
                pygame.mixer.music.play()

            # بدء تسجيل 30 ثانية بحجم خفيف
            if not is_recording and (current_time - last_global_alert_time > ALERT_COOLDOWN):
                last_global_alert_time = current_time
                is_recording = True
                record_start_time = current_time

                timestamp = time.strftime("%Y%m%d_%H%M%S")
                current_video_path = os.path.join(OUTPUT_DIR, f"alert_{timestamp}.mp4")
                current_hazard_label = hazard_label
                current_people_summary = people_summary

                # مسجل فيديو خفيف الحجم (640x360 و 15fps)
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                video_writer = cv2.VideoWriter(current_video_path, fourcc, REC_FPS, (REC_WIDTH, REC_HEIGHT))
                print(f"\n🔴 [تسجيل إنذار] بدأ تسجيل فيديو خفيف وسريع مدته 30 ثانية...")

        # كتابة إطارات الفيديو أثناء التسجيل
        if is_recording and video_writer is not None:
            # تصغير حجم الإطار قبل حفظه لتقليل الحجم الإجمالي
            small_frame = cv2.resize(frame, (REC_WIDTH, REC_HEIGHT))
            video_writer.write(small_frame)

            elapsed = int(time.time() - record_start_time)
            remaining = max(0, RECORD_DURATION - elapsed)
            cv2.putText(frame, f"REC [●] Alert 30s ({remaining}s left)", (20, 120),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            # انتهاء الـ 30 ثانية
            if elapsed >= RECORD_DURATION:
                is_recording = False
                video_writer.release()
                video_writer = None
                print(f"💾 تم اكتمال حفظ الفيديو: {current_video_path}")

                # إرسال التنبيهات
                t = threading.Thread(
                    target=dispatch_alerts_background,
                    args=(current_video_path, current_hazard_label, current_people_summary)
                )
                t.start()

        # عرض الحالة
        status_text = f"DANGER: {hazard_label}" if hazard_detected else "System: Safe"
        status_color = (0, 0, 255) if hazard_detected else (0, 255, 0)
        cv2.putText(frame, status_text, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, status_color, 2)
        cv2.putText(frame, f"Location: {LOCATION_TAG}", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

        cv2.imshow("Fire & Hazard Detection System", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    if video_writer is not None:
        video_writer.release()
    cap.release()
    cv2.destroyAllWindows()
    try:
        pygame.mixer.quit()
    except Exception:
        pass