# تثبيت المكتبات المطلوبة (في حال لم تكن مثبتة):
# pip install opencv-python==4.8.1.78 ultralytics pygame

import cv2  # استيراد مكتبة OpenCV الخاصة بمعالجة الصور والرؤية الحاسوبية
import threading  # استيراد مكتبة Multi-threading لتشغيل الصوت في الخلفية دون إيقاف الكاميرا
import time  # استيراد مكتبة التحكم بالوقت والأزمنة
from datetime import datetime  # تصحيح استيراد وحدة التاريخ والوقت لعرض وقت كشف الحريق
import pygame  # استيراد مكتبة Pygame الخاصة بتشغيل الصوتيات
from ultralytics import YOLO  # استيراد نموذج YOLO المخصص لكشف الكائنات والحرائق والدخان

# --- إعدادات النماذج والمتغيرات المرجعية ---
MODEL_FIRE = "fire.pt"  # تحديد مسار نموذج كشف الحريق والدخان
MODEL_MEAN_VALUES = (
    78.4263377603,
    87.7689143744,
    114.895847746,
)  # قيم متوسط الألوان المعتمدة لضبط دخل نموذج السن والنوع
GENDER_LIST = ["Male", "Female"]  # قائمة خيارات تحديد الجنس
AGE_LIST = [
    "(0-2)",
    "(4-6)",
    "(8-12)",
    "(15-20)",
    "(25-32)",
    "(38-43)",
    "(48-53)",
    "(60-100)",
]  # قائمة الفئات العمرية المتوقعة

# --- تحميل النماذج المدربة الخاصة بالوجوه والعمر والجنس ---
print("جاري تحميل النماذج...")  # طباعة رسالة تفيد ببدء عملية تحميل النماذج
face_net = cv2.dnn.readNet(
    "opencv_face_detector_uint8.pb", "opencv_face_detector.pbtxt"
)  # تحميل شبكة كشف الوجوه
age_net = cv2.dnn.readNet(
    "age_net.caffemodel", "age_deploy.prototxt"
)  # تحميل شبكة التنبؤ بالعمر
gender_net = cv2.dnn.readNet(
    "gender_net.caffemodel", "gender_deploy.prototxt"
)  # تحميل شبكة التنبؤ بالجنس

# --- تحميل نموذج كشف الحريق والدخان ---
fire_model = YOLO(MODEL_FIRE)  # تهيئة وتضمين نموذج YOLO لكشف الحريق والدخان
print("تم تحميل جميع النماذج بنجاح!")  # طباعة رسالة تأكيد النجاح

# --- إعدادات نظام الإنذار الصوتي ---
pygame.mixer.init()  # تهيئة محرك الصوتيات في Pygame
is_alarming = False  # متغير منطقي لمنع تكرار تشغيل صوت الإنذار بالتوازي


def play_alarm():
    """دالة مسؤولة عن تشغيل صوت الإنذار بصيغة MP3 عند كشف الحريق أو الدخان."""
    global is_alarming  # استدعاء المتغير العام الخاص بالحالة
    if is_alarming:  # إذا كان الإنذار يعمل بالفعل، اخرج من الدالة
        return
    is_alarming = True  # تعيين حالة الإنذار على أنه يعمل حالياً
    try:
        pygame.mixer.music.load(
            "alarm_new.mp3"
        )  # تحميل ملف الإنذار الصوتي الجديد
        pygame.mixer.music.play(
            loops=-1
        )  # تشغيل الإنذار بشكل تكراري لا ينتهي
    except Exception as e:
        print(f"\a خطأ في تشغيل الصوت: {e}")  # إصدار صوت النظام في حال الخلل
    time.sleep(5)  # استمرار تشغيل الإنذار لمدة 5 ثوانٍ على الأقل
    pygame.mixer.music.stop()  # إيقاف تشغيل الصوت
    is_alarming = False  # إرجاع المتغير لحالته الأصلية لاستقبال إنذارات جديدة


# --- دالة تحليل الوجوه واستخراج البيانات ---
def detect_faces_and_info(frame):
    """دالة كشف الوجوه وتحليل الفئة العمرية والجنس."""
    h, w = frame.shape[:2]  # الحصول على أبعاد الإطار (الارتفاع والعرض)
    blob = cv2.dnn.blobFromImage(
        frame, 1.0, (300, 300), [104, 117, 123], True, False
    )  # تحويل الإطار إلى Blob مناسب لشبكة كشف الوجوه
    face_net.setInput(blob)  # إدخال البيانات المجهزة إلى الشبكة
    detections = face_net.forward()  # إجبار الشبكة على المعالجة وإخراج النتائج
    faces_data = []  # قائمة لتخزين بيانات الوجوه المكتشفة

    for i in range(
        detections.shape[2]
    ):  # المرور عبر جميع النتائج المحتملة للوجوه
        confidence = detections[0, 0, i, 2]  # استخراج درجة ثقة النموذج بالوجه
        if confidence > 0.7:  # قبول النتيجة فقط إذا كان ميزان الثقة أعلى من 70%
            x1 = int(
                detections[0, 0, i, 3] * w
            )  # حساب الإحداثي الأيسر للصندوق
            y1 = int(
                detections[0, 0, i, 4] * h
            )  # حساب الإحداثي الأعلي للصندوق
            x2 = int(
                detections[0, 0, i, 5] * w
            )  # حساب الإحداثي الأيمن للصندوق
            y2 = int(
                detections[0, 0, i, 6] * h
            )  # حساب الإحداثي السفلي للصندوق

            face = frame[
                y1:y2, x1:x2
            ]  # اقتصاص منطقة الوجه فقط من الإطار الكلي
            if face.size == 0:  # تجنب الأخطاء في حالة اقتصاص منطقة فارغة
                continue

            # معالجة صورة الوجه وتجهيزها لنماذج العمر والجنس
            face_blob = cv2.dnn.blobFromImage(
                face, 1.0, (227, 227), MODEL_MEAN_VALUES, swapRB=False
            )

            # التنبؤ بالجنس
            gender_net.setInput(face_blob)  # إدخال الوجه لنموذج الجنس
            gender_preds = gender_net.forward()  # تنفيذ التنبؤ
            gender = GENDER_LIST[
                gender_preds[0].argmax()
            ]  # اختيار النتيجة ذات الاحتمالية الأعلى

            # التنبؤ بالعمر
            age_net.setInput(face_blob)  # إدخال الوجه لنموذج العمر
            age_preds = age_net.forward()  # تنفيذ التنبؤ
            age = AGE_LIST[
                age_preds[0].argmax()
            ]  # اختيار الفئة العمرية الأعلى احتمالاً

            # تحديد تصنيف الشخص (طفل أم بالغ)
            if age in ["(0-2)", "(4-6)", "(8-12)"]:
                arabic_type = "Child"
            else:
                arabic_type = "Man" if gender == "Male" else "Woman"

            # إضافة الإحداثيات والمعلومات إلى القائمة
            faces_data.append((x1, y1, x2, y2, arabic_type, age))

    return faces_data  # إرجاع قائمة الوجوه المكتشفة ببياناتها


# --- حلقة المعالجة الرئيسية (الكاميرا) ---
cap = cv2.VideoCapture(0)  # فتح كاميرا الجهاز الرئيسية (المؤشر 0)

while cap.isOpened():  # الاستمرار طالما الكاميرا متصلة وتعمل
    ret, frame = cap.read()  # قراءة إطار/صورة جديدة من الكاميرا
    if not ret:  # إيقاف الحلقة إذا تعذر جلب الصورة
        break

    # 1. كشف الحريق والدخان بأعلى دقة باستخدام YOLO
    results = fire_model.predict(
        frame, conf=0.35, imgsz=640, verbose=False
    )  # استخدام دقة صورة أعلى 640 وتعديل نسبة الثقة لرصد أدق
    for r in results:  # التكرار عبر نتائج الكشف
        for box in r.boxes:  # التكرار عبر الصناديق المحددة
            x1, y1, x2, y2 = map(
                int, box.xyxy[0]
            )  # استخراج إحداثيات صندوق الكشف
            conf = float(box.conf[0])  # استخراج نسبة التأكد
            cls_id = int(box.cls[0])  # استخراج رقم الفئة המكتشفة
            class_name = fire_model.names[
                cls_id
            ]  # استخراج اسم الكائن (Fire / Smoke)

            # تحديد لون المربع بناءً على نوع الكشف (أحمر للحريق - برتقالي للدخان)
            color = (
                (0, 0, 255)
                if "fire" in class_name.lower()
                else (0, 165, 255)
            )

            cv2.rectangle(
                frame, (x1, y1), (x2, y2), color, 2
            )  # رسم المربع الملون حول الكشف

            time_now = datetime.now().strftime(
                "%H:%M:%S"
            )  # استخراج الوقت الحالي
            label_text = f"{class_name.upper()} {conf*100:.0f}% [{time_now}]"  # نص يحتوي النوع ونسبة الدقة والوقت
            cv2.putText(
                frame,
                label_text,
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                color,
                2,
            )  # طباعة البيانات المحدثة فوق المربع

            # تشغيل الإنذار الصوتي في مسار منفصل (Thread)
            threading.Thread(target=play_alarm, daemon=True).start()

    # 2. كشف الوجوه وتحليل الأشخاص
    faces = detect_faces_and_info(frame)  # استدعاء دالة تحليل الوجوه
    for x1, y1, x2, y2, p_type, age in faces:  # المرور على كل شخص تم كشفه
        cv2.rectangle(
            frame, (x1, y1), (x2, y2), (0, 255, 0), 2
        )  # رسم مربع أخضر حول الوجه
        label = f"{p_type} {age}"  # تجهيز النص المكتوب
        cv2.putText(
            frame,
            label,
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2,
        )  # طباعة البيانات فوق المربع الأخضر

    # عرض الإطار النهائي المكتمل على الشاشة
    cv2.imshow("High Precision Fire & Smoke Detection", frame)

    # الاستجابة للضغط على زر 'q' الخروج من البرنامج
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# --- إنهاء واستعادة الموارد ---
cap.release()  # تحرير الكاميرا وإغلاق الاتصال بها
cv2.destroyAllWindows()  # إغلاق جميع نوافذ OpenCV المفتوحة