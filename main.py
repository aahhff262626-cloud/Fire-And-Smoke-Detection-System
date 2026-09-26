# main.py
import cv2
from agents.orchestrator import Orchestrator

def main():
    print("🚀 جاري بدء نظام Multi-Agent المطور (Level 5)...")
    system = Orchestrator()

    try:
        while True:
            frame, analysis = system.process_step()
            if frame is None:
                continue

            # رسم نتائج التحليل على الشاشة
            for x1, y1, x2, y2, label, conf in analysis["hazard_boxes"]:
                color = (0, 0, 255) if "حريق" in label else (0, 140, 255)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame, f"{label} {conf*100:.1f}%", (x1, max(y1 - 10, 25)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

            for p in analysis["people"]:
                x1, y1, x2, y2 = p["box"]
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f"{p['gender']} {p['age']}", (x1, max(y1 - 10, 25)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            # حالة النظام وتسجيل الـ 30 ثانية
            status = "DANGER" if analysis["hazard_detected"] else "SAFE"
            col = (0, 0, 255) if analysis["hazard_detected"] else (0, 255, 0)
            cv2.putText(frame, f"System: {status}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, col, 2)

            if system.reporter.is_recording:
                cv2.putText(frame, "● RECORDING 30s CLIP...", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            cv2.imshow("FlameEye - Enterprise Multi-Agent System", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        system.close()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()