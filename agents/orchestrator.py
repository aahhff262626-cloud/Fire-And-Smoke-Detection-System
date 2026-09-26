# agents/orchestrator.py
import time
import threading
from agents.watcher import WatcherAgent
from agents.analyst import AnalystAgent
from agents.responder import ResponderAgent
from agents.reporter import ReporterAgent
import config

class Orchestrator:
    def __init__(self):
        # تهيئة الوكلاء الأربعة
        self.watcher = WatcherAgent(config.CAMERA_INDEX)
        self.analyst = AnalystAgent()
        self.responder = ResponderAgent()
        self.reporter = ReporterAgent()
        self.last_alert_time = 0

    def process_step(self):
        """تنفيذ خطوة عمل واحدة في الـ Graph."""
        # 1. Watcher يقرأ الكاميرا
        ret, frame = self.watcher.get_frame()
        if not ret:
            return None, None

        # 2. Analyst يحلل الإطار
        analysis = self.analyst.analyze(frame)

        people_summary = ", ".join([f"{p['gender']} {p['age']}" for p in analysis["people"]])
        if not people_summary:
            people_summary = "لا يوجد أشخاص"

        # 3. توجيه الأحداث عند رصد خطر
        current_time = time.time()
        if analysis["hazard_detected"]:
            self.responder.play_siren()

            if not self.reporter.is_recording and (current_time - self.last_alert_time > config.ALERT_COOLDOWN):
                self.last_alert_time = current_time
                self.reporter.start_recording()

        # 4. تسجيل الإطارات ومتابعة مؤقت الـ 30 ثانية
        if self.reporter.is_recording:
            finished = self.reporter.write_frame(frame)
            if finished:
                video_file = self.reporter.current_video_path
                hazard_label = analysis["hazard_label"]

                # توثيق الحدث في ملف fires.log
                self.reporter.log_incident(hazard_label, people_summary)

                # تشغيل الإرسال في خلفية مستقلة (Non-blocking Thread)
                threading.Thread(
                    target=self._dispatch_alerts,
                    args=(video_file, hazard_label, people_summary),
                    daemon=True
                ).start()

        return frame, analysis

    def _dispatch_alerts(self, video_file, hazard_label, people_summary):
        """توزيع مهام الإرسال على Responder."""
        self.responder.send_whatsapp(hazard_label, people_summary)
        self.responder.send_email(video_file, hazard_label, people_summary)

    def close(self):
        self.watcher.release()