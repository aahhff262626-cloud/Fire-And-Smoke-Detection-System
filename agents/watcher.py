# agents/watcher.py
import cv2

class WatcherAgent:
    def __init__(self, camera_index=0):
        self.camera_index = camera_index
        self.cap = None
        self.connect()

    def connect(self):
        """الربط بالكاميرا وإعادة المحاولة في حال الانقطاع."""
        if self.cap is not None:
            self.cap.release()
        self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        if self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            return True
        return False

    def get_frame(self):
        """جلب الإطار التالي مع ميزة Auto-Reconnect."""
        if not self.cap or not self.cap.isOpened():
            if not self.connect():
                return False, None
        
        ret, frame = self.cap.read()
        if not ret:
            self.connect()
            ret, frame = self.cap.read()
        return ret, frame

    def release(self):
        if self.cap:
            self.cap.release()