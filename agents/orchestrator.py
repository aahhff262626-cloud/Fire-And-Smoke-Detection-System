# agents/orchestrator.py
# ==============================================================================
# وكيل التنسيق والإدارة (The Orchestrator) - المسؤول عن:
#   1. تشغيل دورة المراقبة الكاملة (Watcher → Analyst → Reporter → Responder)
#   2. إدارة حالات النظام (آمن / خطر / تسجيل)
#   3. ضمان إرسال التنبيهات في خيط منفصل لعدم تجميد الكاميرا
# ==============================================================================

import time       # مكتبة التوقيت وحساب الفترات
import threading  # مكتبة الخيوط المتوازية (Threads) لإرسال الإنذارات في الخلفية
import config     # إعدادات النظام الموحدة

# استيراد جميع الوكلاء (Agents) التخصصيين
from agents.watcher   import WatcherAgent    # وكيل الكاميرا
from agents.analyst   import AnalystAgent    # وكيل التحليل الذكي
from agents.responder import ResponderAgent  # وكيل الاستجابة والإنذار
from agents.reporter  import ReporterAgent   # وكيل التسجيل والتوثيق

class Orchestrator:
    """
    مدير المنظومة الكاملة:
    يُنسّق بين الوكلاء الأربعة لضمان عمل النظام بكفاءة عالية
    """

    def __init__(self):
        # -----------------------------------------------------------
        # إنشاء الوكلاء الأربعة (كل وكيل متخصص في مهمة محددة)
        # -----------------------------------------------------------
        self.watcher   = WatcherAgent(config.CAMERA_INDEX)  # وكيل الكاميرا
        self.analyst   = AnalystAgent()                      # وكيل التحليل الذكي
        self.responder = ResponderAgent()                    # وكيل الإنذار والتنبيه
        self.reporter  = ReporterAgent()                     # وكيل التسجيل السحابي

        # -----------------------------------------------------------
        # متغيرات تتبع حالة النظام
        # -----------------------------------------------------------
        self.last_alert_time      = 0   # وقت آخر إنذار أُطلق (لمنع التكرار المتسارع)
        self.active_hazard_label  = ""  # نوع الخطر الجاري تسجيله
        self.active_people_summary = "" # ملخص الأشخاص المتواجدين عند الإنذار

    # ==============================================================================
    # الدورة الرئيسية: تُستدعى لكل إطار من الكاميرا
    # ==============================================================================
    def process_step(self):
        """
        تنفيذ خطوة كاملة من دورة المراقبة:
        1. الحصول على إطار من الكاميرا (Watcher)
        2. تحليله بالذكاء الاصطناعي (Analyst)
        3. إدارة التسجيل والإنذارات حسب النتائج
        يُعيد الإطار المُعالَج ونتائج التحليل
        """

        # الخطوة 1: الحصول على إطار من الكاميرا
        ret, frame = self.watcher.get_frame()
        if not ret:
            return None, None  # الكاميرا غير متاحة - سيُعاد المحاولة تلقائياً

        # الخطوة 2: تحليل الإطار (كشف الحريق + الأشخاص)
        analysis = self.analyst.analyze(frame)

        # بناء ملخص الأشخاص المرئيين (للرسائل وسجل الحوادث)
        people_list = [
            f"{p['gender']} {p['age']}".strip()
            for p in analysis["people"]
        ]
        people_summary = ", ".join(people_list) if people_list else "لا يوجد أشخاص"

        current_time = time.time()

        # ---------------------------------------------------------------
        # الخطوة 3: إدارة الإنذار والتسجيل عند رصد الخطر
        # ---------------------------------------------------------------
        if analysis["hazard_detected"]:
            # تشغيل صفارة الإنذار الصوتية فوراً
            self.responder.play_siren()

            # بدء التسجيل فقط إذا:
            # - لا يوجد تسجيل جارٍ حالياً
            # - مرّ وقت كافٍ منذ آخر إنذار (ALERT_COOLDOWN ثانية)
            if (not self.reporter.is_recording
                    and (current_time - self.last_alert_time > config.ALERT_COOLDOWN)):

                self.last_alert_time      = current_time               # تحديث وقت الإنذار
                self.active_hazard_label  = analysis["hazard_label"]   # حفظ نوع الخطر
                self.active_people_summary = people_summary             # حفظ الأشخاص

                self.reporter.start_recording()  # بدء التسجيل (30 ثانية)
                print(f"🎥 بدء التسجيل: {self.active_hazard_label}")

        # ---------------------------------------------------------------
        # إضافة إطار للفيديو الجاري تسجيله (إذا كان التسجيل نشطاً)
        # ---------------------------------------------------------------
        if self.reporter.is_recording:

            # إذا ظهر أشخاص بعد بدء التسجيل نُحدّث الملخص
            if (people_summary != "لا يوجد أشخاص"
                    and self.active_people_summary == "لا يوجد أشخاص"):
                self.active_people_summary = people_summary

            # كتابة الإطار في الفيديو - يُعيد True عند اكتمال 30 ثانية
            recording_finished = self.reporter.write_frame(frame)

            if recording_finished:
                # التسجيل اكتمل - الآن نُنفذ الخطوات التالية
                video_file   = self.reporter.current_video_path
                saved_hazard = self.active_hazard_label or "حريق (Fire)"
                saved_people = self.active_people_summary or people_summary

                print(f"✅ اكتمل التسجيل: {video_file}")
                print("☁️ جاري رفع الفيديو للسحابة...")

                # الخطوة 4: رفع الفيديو للسحابة (في نفس الخيط لأنه ضروري قبل الإرسال)
                cloud_url = self.reporter.upload_to_cloud(video_file)

                # الخطوة 5: توثيق الحادثة في ملف fires.log
                self.reporter.log_incident(saved_hazard, saved_people, cloud_url)

                # الخطوة 6: إرسال التنبيهات في خيط منفصل
                # daemon=False يضمن إكمال الإرسال حتى لو أغلق المستخدم النافذة
                alert_thread = threading.Thread(
                    target=self._dispatch_alerts,
                    args=(video_file, saved_hazard, saved_people, cloud_url),
                    daemon=False   # مهم: عدم إيقافه عند إغلاق نافذة الكاميرا
                )
                alert_thread.start()

        return frame, analysis

    # ==============================================================================
    # إرسال جميع التنبيهات (واتساب + إيميل) في خيط منفصل
    # ==============================================================================
    def _dispatch_alerts(self, video_file, hazard_label, people_summary, cloud_url=""):
        """
        يُرسَل في خيط (Thread) منفصل لعدم تجميد واجهة الكاميرا أثناء الإرسال.
        يُرسل الواتساب والإيميل بالترتيب.
        """
        print("📤 جاري إرسال التنبيهات (واتساب + إيميل)...")
        self.responder.send_whatsapp(hazard_label, people_summary, cloud_url)
        self.responder.send_email(video_file, hazard_label, people_summary, cloud_url)
        print("✅ تم إرسال جميع التنبيهات بنجاح!")

    # ==============================================================================
    # إغلاق النظام وتحرير الموارد
    # ==============================================================================
    def close(self):
        """إغلاق الكاميرا وتحرير جميع الموارد عند انتهاء التشغيل"""
        self.watcher.release()
        print("🛑 تم إغلاق نظام Flame Eye.")