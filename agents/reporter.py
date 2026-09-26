# agents/reporter.py
import cv2
import time
import os
import config

class ReporterAgent:
    def __init__(self):
        self.is_recording = False
        self.writer = None
        self.current_video_path = ""
        self.start_time = 0

    def start_recording(self):
        """بدء جلسة تسجيل جديدة مدتها 30 ثانية."""
        self.is_recording = True
        self.start_time = time.time()
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        self.current_video_path = os.path.join(config.OUTPUT_DIR, f"alert_{timestamp}.mp4")
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.writer = cv2.VideoWriter(self.current_video_path, fourcc, 15.0, (640, 360))
        return self.current_video_path

    def write_frame(self, frame):
        """إضافة الإطار إلى الفيديو مع تقليل الحجم."""
        if self.is_recording and self.writer:
            small = cv2.resize(frame, (640, 360))
            self.writer.write(small)
            if time.time() - self.start_time >= config.RECORD_DURATION:
                self.stop_recording()
                return True
        return False

    def stop_recording(self):
        """إنهاء التسجيل وتفريغ الذاكرة."""
        self.is_recording = False
        if self.writer:
            self.writer.release()
            self.writer = None

    def log_incident(self, hazard_label, people_summary):
        """تسجيل الحدث في السجل الأمني الدائم fires.log."""
        with open(config.LOG_FILE, "a", encoding="utf-8") as f:
            log_entry = (
                f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] "
                f"خطر: {hazard_label} | "
                f"موقع: {config.LOCATION_TAG} | "
                f"أشخاص: {people_summary} | "
                f"ملف الفيديو: {self.current_video_path}\n"
            )
            f.write(log_entry)
        print(f"📝 [Reporter] تم توثيق الحدث في سجل الأمان: {config.LOG_FILE}")