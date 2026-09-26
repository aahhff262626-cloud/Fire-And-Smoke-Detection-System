# agents/reporter.py
import cv2
import time
import os
import requests
import config
import cloudinary
import cloudinary.uploader

# تهيئة Cloudinary
if hasattr(config, 'CLOUDINARY_CLOUD_NAME') and config.CLOUDINARY_CLOUD_NAME != "ضع_اسم_السحابة_هنا":
    cloudinary.config(
        cloud_name=config.CLOUDINARY_CLOUD_NAME,
        api_key=config.CLOUDINARY_API_KEY,
        api_secret=config.CLOUDINARY_API_SECRET,
        secure=True
    )

class ReporterAgent:
    def __init__(self):
        self.is_recording = False
        self.writer = None
        self.current_video_path = ""
        self.start_time = 0

    def start_recording(self):
        self.is_recording = True
        self.start_time = time.time()
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        self.current_video_path = os.path.join(config.OUTPUT_DIR, f"alert_{timestamp}.mp4")
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.writer = cv2.VideoWriter(self.current_video_path, fourcc, 15.0, (640, 360))
        return self.current_video_path

    def write_frame(self, frame):
        if self.is_recording and self.writer:
            small = cv2.resize(frame, (640, 360))
            self.writer.write(small)
            if time.time() - self.start_time >= config.RECORD_DURATION:
                self.stop_recording()
                return True
        return False

    def stop_recording(self):
        self.is_recording = False
        if self.writer:
            self.writer.release()
            self.writer = None

    def upload_to_cloud(self, video_path):
        """رفع الفيديو إلى Cloudinary واستخراج رابط المشاهدة السحابي المباشر."""
        print(f"☁️ [Reporter] جاري رفع الفيديو سحابياً إلى Cloudinary...")
        try:
            if hasattr(config, 'CLOUDINARY_CLOUD_NAME') and config.CLOUDINARY_CLOUD_NAME != "ضع_اسم_السحابة_هنا":
                response = cloudinary.uploader.upload_large(
                    video_path,
                    resource_type="video",
                    folder="flame_eye_alerts"
                )
                cloud_url = response.get("secure_url", "")
                if cloud_url:
                    print(f"✅ تم الرفع بنجاح! الرابط السحابي:\n{cloud_url}")
                    return cloud_url
        except Exception as e:
            print(f"⚠️ ملاحظة Cloudinary: {e}")

        # خطة بديلة سحابية تلقائية
        try:
            with open(video_path, "rb") as f:
                res = requests.post("https://tmpfiles.org/api/v1/upload", files={"file": f}, timeout=15)
                if res.status_code == 200:
                    raw = res.json().get("data", {}).get("url", "")
                    if raw:
                        return raw.replace("https://tmpfiles.org/", "https://tmpfiles.org/dl/")
        except Exception:
            pass

        return None

    def log_incident(self, hazard_label, people_summary, cloud_url=""):
        with open(config.LOG_FILE, "a", encoding="utf-8") as f:
            log_entry = (
                f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] "
                f"خطر: {hazard_label} | "
                f"موقع: {config.LOCATION_TAG} | "
                f"أشخاص: {people_summary} | "
                f"رابط سحابي: {cloud_url or 'محلي'}\n"
            )
            f.write(log_entry)
        print(f"📝 [Reporter] تم توثيق الحدث والرابط في سجل fires.log")