# agents/analyst.py
import cv2
import config
from ultralytics import YOLO

class AnalystAgent:
    def __init__(self):
        self.fire_model = YOLO(config.FIRE_MODEL_PATH)
        self.face_net = cv2.dnn.readNet(config.FACE_MODEL, config.FACE_PROTO)
        self.age_net = cv2.dnn.readNet(config.AGE_MODEL, config.AGE_PROTO)
        self.gender_net = cv2.dnn.readNet(config.GENDER_MODEL, config.GENDER_PROTO)

        self.MODEL_MEAN = (78.4263377603, 87.7689143744, 114.895847746)
        self.AGE_LIST = ['(0-2)', '(4-6)', '(8-12)', '(15-20)', '(25-32)', '(38-43)', '(48-53)', '(60-100)']
        self.GENDER_LIST = ['ذكر (Male)', 'أنثى (Female)']

    def analyze(self, frame):
        """فحص الإطار واستخراج المخاطر وبيانات الأشخاص."""
        hazard_detected = False
        hazard_label = ""
        hazard_boxes = []

        # 1. كشف الحريق والدخان مع فلترة الإنذار الكاذب
        results = self.fire_model.predict(frame, conf=0.50, imgsz=640, verbose=False)
        for res in results:
            for box in res.boxes:
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])
                name = self.fire_model.names.get(cls_id, str(cls_id)).lower()

                # استبعاد الدخان الخفيف لمنع الإنذار الكاذب
                if "smoke" in name and conf < 0.70:
                    continue

                hazard_detected = True
                hazard_label = "حريق (Fire)" if "fire" in name else "دخان / غاز (Smoke)"
                x1, y1, x2, y2 = [int(v) for v in box.xyxy[0]]
                hazard_boxes.append((x1, y1, x2, y2, hazard_label, conf))

        # 2. كشف الوجوه والنوع والعمر
        people = []
        h, w = frame.shape[:2]
        blob = cv2.dnn.blobFromImage(frame, 1.0, (300, 300), [104, 117, 123], swapRB=False, crop=False)
        self.face_net.setInput(blob)
        detections = self.face_net.forward()

        for i in range(detections.shape[2]):
            conf = detections[0, 0, i, 2]
            if conf > 0.60:
                x1 = max(0, int(detections[0, 0, i, 3] * w))
                y1 = max(0, int(detections[0, 0, i, 4] * h))
                x2 = min(w - 1, int(detections[0, 0, i, 5] * w))
                y2 = min(h - 1, int(detections[0, 0, i, 6] * h))

                face = frame[y1:y2, x1:x2]
                if face.shape[0] < 20 or face.shape[1] < 20:
                    continue

                # النوع والعمر
                bg = cv2.dnn.blobFromImage(face, 1.0, (227, 227), self.MODEL_MEAN, swapRB=False)
                self.gender_net.setInput(bg)
                gender = self.GENDER_LIST[self.gender_net.forward()[0].argmax()]

                ba = cv2.dnn.blobFromImage(face, 1.0, (227, 227), self.MODEL_MEAN, swapRB=False)
                self.age_net.setInput(ba)
                age = self.AGE_LIST[self.age_net.forward()[0].argmax()]

                people.append({"box": (x1, y1, x2, y2), "gender": gender, "age": age})

        return {
            "hazard_detected": hazard_detected,
            "hazard_label": hazard_label,
            "hazard_boxes": hazard_boxes,
            "people": people
        }