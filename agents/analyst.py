# agents/analyst.py
# ==============================================================================
# وكيل التحليل الذكي (The Analyst) - المسؤول عن:
#   1. كشف الحريق والدخان والغازات القابلة للاشتعال بنموذج YOLOv8
#   2. كشف الوجوه وتصنيف المتواجدين (رجل / امرأة / طفل) بالإنجليزية
#   3. تثبيت قراءة السن والجنس بتقنية التمهيد عبر إطارات متعددة
# ==============================================================================

import cv2                     # مكتبة معالجة الصور والفيديو
import os                      # مكتبة التعامل مع الملفات
import config                  # إعدادات النظام الموحدة
from ultralytics import YOLO   # مكتبة نموذج الذكاء الاصطناعي YOLOv8
from collections import deque  # قائمة متحركة لتثبيت قراءة السن والجنس

class AnalystAgent:
    """
    وكيل التحليل الذكي - يحلل كل إطار من الكاميرا ويعيد:
    - قائمة مربعات الخطر (حريق / دخان / غاز) مع درجة الثقة
    - قائمة الأشخاص المكتشفين مع التصنيف الديموغرافي
    """

    def __init__(self):
        # -----------------------------------------------------------
        # تحميل نموذج YOLOv8 للكشف عن الحريق والدخان والغازات
        # -----------------------------------------------------------
        self.fire_model = YOLO(config.FIRE_MODEL_PATH)

        # -----------------------------------------------------------
        # كاشف الوجوه بالـ Haar Cascade (مدمج مع OpenCV - لا يحتاج ملفات خارجية)
        # يُستخدم كبديل سريع وموثوق للشبكة العصبية
        # -----------------------------------------------------------
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )

        # -----------------------------------------------------------
        # تحميل نماذج العمر والجنس (Caffe Deep Learning Models)
        # تُحمَّل فقط إذا كانت الملفات موجودة (تجنب الأخطاء)
        # -----------------------------------------------------------
        self.age_net    = None  # نموذج التعرف على العمر
        self.gender_net = None  # نموذج التعرف على الجنس
        try:
            if os.path.exists(config.AGE_MODEL) and os.path.exists(config.AGE_PROTO):
                self.age_net = cv2.dnn.readNet(config.AGE_MODEL, config.AGE_PROTO)
            if os.path.exists(config.GENDER_MODEL) and os.path.exists(config.GENDER_PROTO):
                self.gender_net = cv2.dnn.readNet(config.GENDER_MODEL, config.GENDER_PROTO)
        except Exception:
            pass  # إذا فشل التحميل يستمر النظام بدون النماذج

        # -----------------------------------------------------------
        # ثوابت نماذج الكشف الديموغرافي
        # -----------------------------------------------------------
        # متوسطات ألوان RGB لإزالة التحيز من صور الوجه (ImageNet Mean)
        self.MODEL_MEAN = (78.4263377603, 87.7689143744, 114.895847746)

        # قائمة فئات العمر التي يتنبأ بها النموذج
        self.AGE_LIST = [
            '(0-2)', '(4-6)', '(8-12)',       # أطفال صغار
            '(15-20)', '(25-32)', '(38-43)',   # شباب وكبار
            '(48-53)', '(60-100)'              # مسنون
        ]

        # الجنس بالإنجليزية (ما يُرسَل في الإنذارات والشاشة)
        self.GENDER_EN = ['Male', 'Female']

        # -----------------------------------------------------------
        # نظام تثبيت القراءة (Smoothing) - يمنع تأرجح السن والجنس
        # يحتفظ بآخر N قراءات لكل وجه ويأخذ الأكثر تكراراً
        # -----------------------------------------------------------
        # قاموس: مفتاح = موقع الوجه التقريبي، قيمة = قائمة آخر القراءات
        self.face_history = {}     # تاريخ قراءات كل وجه
        self.history_size = config.AGE_SMOOTH_FRAMES  # عدد الإطارات المستخدمة

        # -----------------------------------------------------------
        # عداد تأكيد الخطر (يمنع الإنذار الكاذب من إطار واحد)
        # -----------------------------------------------------------
        self.hazard_frame_count = 0   # عدد الإطارات المتتالية التي رُصد فيها خطر
        self.confirm_needed = config.HAZARD_CONFIRM_FRAMES  # العدد المطلوب للتأكيد

    # ==============================================================================
    # الدالة الرئيسية: تحليل الإطار الواحد
    # ==============================================================================
    def analyze(self, frame):
        """
        تحليل إطار الكاميرا واكتشاف المخاطر والأشخاص.
        المدخلات: إطار BGR من OpenCV
        المخرجات: قاموس يحتوي على نتائج الكشف الكاملة
        """

        hazard_detected = False   # هل تم اكتشاف خطر في هذا الإطار؟
        hazard_label    = ""      # وصف نوع الخطر المكتشف
        hazard_boxes    = []      # قائمة مربعات الخطر (x1,y1,x2,y2,label,conf)

        # ==============================================================
        # الخطوة 1: كشف الحريق والدخان والغازات بنموذج YOLOv8
        # نستخدم حد ثقة منخفض (0.30) ثم نُطبق الحدود المختلفة يدوياً
        # حسب نوع الخطر لتحقيق أفضل توازن بين الحساسية والدقة
        # ==============================================================
        results = self.fire_model.predict(
            frame,
            conf=0.30,       # حد ثقة منخفض عند الإرسال للنموذج
            imgsz=640,       # حجم الصورة المُدخلة للنموذج
            verbose=False    # إيقاف طباعة نتائج النموذج في الكونسول
        )

        raw_hazard = False  # خطر خام قبل تطبيق عداد التأكيد

        for res in results:
            for box in res.boxes:
                conf    = float(box.conf[0])               # درجة ثقة الكشف
                cls_id  = int(box.cls[0])                  # رقم الفئة
                name    = self.fire_model.names.get(cls_id, str(cls_id)).lower()

                # تحديد نوع الخطر وتطبيق حد الثقة المناسب لكل نوع
                is_fire  = ("fire" in name or "flame" in name)
                is_smoke = ("smoke" in name or "gas" in name)

                # الحريق: يكفي conf >= 0.38 (نريد اكتشافه بسرعة)
                # الدخان/الغاز: يشترط conf >= 0.60 (لتجنب الإنذارات الكاذبة)
                if is_fire and conf >= config.FIRE_CONF_THRESHOLD:
                    raw_hazard  = True
                    label       = "حريق (Fire Hazard)"
                    disp_label  = label
                elif is_smoke and conf >= config.SMOKE_CONF_THRESHOLD:
                    raw_hazard  = True
                    label       = "دخان / غازات قابلة للاشتعال (Smoke & Gas Hazard)"
                    disp_label  = label
                elif not is_fire and not is_smoke and conf >= config.FIRE_CONF_THRESHOLD:
                    # فئات أخرى يكتشفها النموذج
                    raw_hazard  = True
                    label       = f"خطر ({name.upper()})"
                    disp_label  = label
                else:
                    continue  # تجاهل الكشوفات ذات الثقة المنخفضة

                # استخراج إحداثيات المربع المحيط بالخطر
                x1, y1, x2, y2 = [int(v) for v in box.xyxy[0]]
                hazard_boxes.append((x1, y1, x2, y2, disp_label, conf))
                if not hazard_label:
                    hazard_label = label  # أول خطر مكتشف يُعتمد كالتسمية الرئيسية

        # ==============================================================
        # تأكيد الخطر عبر عدة إطارات متتالية (يمنع الإنذار الكاذب)
        # يجب أن يُكتشف الخطر في HAZARD_CONFIRM_FRAMES إطارات متتالية
        # ==============================================================
        if raw_hazard:
            self.hazard_frame_count += 1    # زيادة العداد عند كشف خطر
        else:
            self.hazard_frame_count = 0     # إعادة العداد عند انتفاء الخطر

        # الخطر مؤكد فقط إذا تجاوز العداد الحد المطلوب
        hazard_detected = self.hazard_frame_count >= self.confirm_needed

        # إذا لم يكن الخطر مؤكداً بعد، نُخفي المربعات مؤقتاً
        if not hazard_detected:
            hazard_boxes = []
            hazard_label = ""

        # ==============================================================
        # الخطوة 2: كشف الوجوه وتصنيف المتواجدين
        # ==============================================================
        people = []
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # تحويل للرمادي لكاشف الوجوه

        # كشف الوجوه بالـ Haar Cascade
        # minNeighbors=7: يمنع الكشف الكاذب على الياقات والخلفيات المتشابهة
        # minSize=(80,80): يشترط أن يكون الوجه ذا حجم معقول في الإطار
        detected_faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=7,
            minSize=(80, 80)
        )

        for (x, y, w, h) in detected_faces:
            # اقتصاص منطقة الوجه من الإطار الأصلي
            face_crop  = frame[y:y+h, x:x+w]
            gender_raw = "Male"    # قيمة افتراضية للجنس
            age        = ""        # قيمة افتراضية للعمر

            # تحليل الوجه بالنماذج إذا كانت محمّلة وإذا كان الاقتصاص كافياً
            try:
                if (self.gender_net is not None
                        and face_crop.shape[0] > 20
                        and face_crop.shape[1] > 20):
                    # إعداد البيانات المُدخلة للشبكة العصبية (Blob)
                    blob = cv2.dnn.blobFromImage(
                        face_crop, 1.0, (227, 227), self.MODEL_MEAN, swapRB=False
                    )
                    # التنبؤ بالجنس
                    self.gender_net.setInput(blob)
                    gender_idx = self.gender_net.forward()[0].argmax()
                    gender_raw = self.GENDER_EN[gender_idx]  # 'Male' أو 'Female'

                if (self.age_net is not None
                        and face_crop.shape[0] > 20
                        and face_crop.shape[1] > 20):
                    blob = cv2.dnn.blobFromImage(
                        face_crop, 1.0, (227, 227), self.MODEL_MEAN, swapRB=False
                    )
                    # التنبؤ بالعمر
                    self.age_net.setInput(blob)
                    age_idx = self.age_net.forward()[0].argmax()
                    age = self.AGE_LIST[age_idx]

            except Exception:
                pass  # في حال أي خطأ نكمل بالقيم الافتراضية

            # ==============================================================
            # تثبيت قراءة السن والجنس (Temporal Smoothing)
            # نستخدم موقع الوجه كمفتاح ونحتفظ بآخر N قراءات
            # ونأخذ الأكثر تكراراً (Majority Vote) كقراءة نهائية مستقرة
            # ==============================================================
            face_key = self._get_face_key(x, y, w, h)  # مفتاح الموقع التقريبي

            if face_key not in self.face_history:
                self.face_history[face_key] = deque(maxlen=self.history_size)

            self.face_history[face_key].append((gender_raw, age))

            # اختيار الجنس والعمر الأكثر تكراراً في النافذة الزمنية
            genders = [r[0] for r in self.face_history[face_key]]
            ages    = [r[1] for r in self.face_history[face_key] if r[1]]

            stable_gender = max(set(genders), key=genders.count)
            stable_age    = max(set(ages), key=ages.count) if ages else age

            # ==============================================================
            # تصنيف نهائي: طفل أو امرأة أو رجل باللغة الإنجليزية
            # ==============================================================
            if stable_age in ['(0-2)', '(4-6)', '(8-12)']:
                # عمر أقل من 15 سنة = طفل
                person_type_en = "Child"
                person_type_ar = "طفل (Child)"
            elif stable_gender == "Female":
                # أنثى بالغة = امرأة
                person_type_en = "Woman"
                person_type_ar = "امرأة (Woman)"
            else:
                # ذكر بالغ = رجل
                person_type_en = "Man"
                person_type_ar = "رجل (Man)"

            # إضافة الشخص لقائمة النتائج
            people.append({
                "box":            (x, y, x+w, y+h),  # إحداثيات المربع المحيط بالوجه
                "gender":         person_type_ar,     # التصنيف بالعربية (للرسائل)
                "gender_display": person_type_en,     # التصنيف بالإنجليزية (للشاشة)
                "age":            stable_age           # الفئة العمرية المُثبَّتة
            })

        # تنظيف تاريخ الوجوه القديمة غير المرئية في الإطار الحالي
        self._cleanup_old_faces(detected_faces)

        # إرجاع نتائج التحليل الكاملة
        return {
            "hazard_detected": hazard_detected,  # هل يوجد خطر مؤكد؟
            "hazard_label":    hazard_label,     # نوع الخطر (نار / دخان / غاز)
            "hazard_boxes":    hazard_boxes,     # إحداثيات مربعات الخطر
            "people":          people            # قائمة الأشخاص المكتشفين
        }

    # ==============================================================================
    # دوال مساعدة داخلية
    # ==============================================================================

    def _get_face_key(self, x, y, w, h):
        """
        توليد مفتاح تقريبي لموقع الوجه (بدقة 60 بكسل)
        يُستخدم لمطابقة نفس الوجه عبر الإطارات المتتالية
        """
        step = 60  # حجم خلية الشبكة بالبكسل - يوازن بين الدقة والاستقرار
        return (x // step, y // step)

    def _cleanup_old_faces(self, current_faces):
        """
        حذف الوجوه القديمة من الذاكرة إذا غابت لفترة
        يمنع تراكم البيانات في الذاكرة عند اختفاء الأشخاص
        """
        if len(current_faces) == 0 and self.face_history:
            # إذا لا يوجد وجوه في الإطار، نمسح نصف التاريخ القديم
            keys_to_remove = list(self.face_history.keys())
            for k in keys_to_remove[:len(keys_to_remove)//2 + 1]:
                del self.face_history[k]