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
        self.watcher = WatcherAgent(config.CAMERA_INDEX)
        self.analyst = AnalystAgent()
        self.responder = ResponderAgent()
        self.reporter = ReporterAgent()
        
        self.last_alert_time = 0
        self.active_hazard_label = ""
        self.active_people_summary = ""

    def process_step(self):
        ret, frame = self.watcher.get_frame()
        if not ret:
            return None, None

        analysis = self.analyst.analyze(frame)

        people_list = [f"{p['gender']} {p['age']}" for p in analysis["people"]]
        people_summary = ", ".join(people_list) if people_list else "لا يوجد أشخاص"

        current_time = time.time()
        
        # حفظ نوع الخطر والأشخاص فور بداية الرصد
        if analysis["hazard_detected"]:
            self.responder.play_siren()

            if not self.reporter.is_recording and (current_time - self.last_alert_time > config.ALERT_COOLDOWN):
                self.last_alert_time = current_time
                self.active_hazard_label = analysis["hazard_label"]
                self.active_people_summary = people_summary
                self.reporter.start_recording()

        # كتابة إطارات الفيديو (30 ثانية)
        if self.reporter.is_recording:
            finished = self.reporter.write_frame(frame)
            if finished:
                video_file = self.reporter.current_video_path
                saved_hazard = self.active_hazard_label if self.active_hazard_label else "حريق (Fire)"
                saved_people = self.active_people_summary if self.active_people_summary else people_summary

                # 1. الرفع السحابي
                cloud_url = self.reporter.upload_to_cloud(video_file)

                # 2. توثيق الحدث
                self.reporter.log_incident(saved_hazard, saved_people, cloud_url)

                # 3. إرسال التنبيهات (daemon=False لضمان اكتمال الإرسال حتى لو أغلقت الكاميرا)
                t = threading.Thread(
                    target=self._dispatch_alerts,
                    args=(video_file, saved_hazard, saved_people, cloud_url),
                    daemon=False
                )
                t.start()

        return frame, analysis

    def _dispatch_alerts(self, video_file, hazard_label, people_summary, cloud_url=""):
        self.responder.send_whatsapp(hazard_label, people_summary, cloud_url)
        self.responder.send_email(video_file, hazard_label, people_summary, cloud_url)

    def close(self):
        self.watcher.release()