# main.py
# ==============================================================================
# نقطة دخول نظام Flame Eye الذكي
# يُشغّل دورة المراقبة الكاملة ويعرض نافذة الكاميرا المباشرة
# ==============================================================================

import cv2                              # مكتبة OpenCV لعرض نافذة الكاميرا
from agents.orchestrator import Orchestrator  # وكيل التنسيق الرئيسي

def main():
    """
    الدالة الرئيسية لتشغيل نظام Flame Eye:
    - تُنشئ كائن المنسق (Orchestrator) الذي يُشغّل جميع الوكلاء
    - تُشغّل حلقة المراقبة المستمرة
    - تعرض نافذة الكاميرا مع الكشوفات المرسومة عليها
    - اضغط 'q' لإغلاق النظام بأمان
    """
    print("=" * 60)
    print("🚀 جاري تشغيل نظام Flame Eye الذكي (Multi-Agent Level 5)...")
    print("=" * 60)

    # إنشاء المنسق الذي يُهيئ ويُدير جميع الوكلاء
    system = Orchestrator()

    try:
        # الحلقة الرئيسية - تعمل حتى يضغط المستخدم 'q'
        while True:
            # تنفيذ خطوة كاملة من دورة المراقبة (كاميرا → تحليل → إنذار)
            frame, analysis = system.process_step()

            # إذا لم يكن هناك إطار (الكاميرا غير متاحة) ننتظر ونكمل
            if frame is None:
                continue

            # ==============================================================
            # رسم مربعات الخطر على الإطار
            # اللون الأحمر للحريق، البرتقالي للدخان والغازات
            # ==============================================================
            for x1, y1, x2, y2, label, conf in analysis["hazard_boxes"]:
                # تحديد نوع الخطر من التسمية
                is_fire = ("Fire" in label or "حريق" in label)

                # لون المربع: أحمر للنار، برتقالي للدخان
                color = (0, 0, 255) if is_fire else (0, 140, 255)

                # النص بالإنجليزية على الشاشة (OpenCV لا يدعم العربية)
                display_text = "FIRE" if is_fire else "SMOKE / GAS"

                # رسم المربع المحيط بالخطر
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

                # كتابة نوع الخطر ونسبة الثقة فوق المربع
                cv2.putText(
                    frame,
                    f"{display_text} {conf * 100:.1f}%",
                    (x1, max(y1 - 10, 25)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2
                )

            # ==============================================================
            # رسم مربعات الأشخاص المكتشفين
            # اللون الأخضر مع التصنيف (Man / Woman / Child) والفئة العمرية
            # ==============================================================
            for person in analysis["people"]:
                x1, y1, x2, y2 = person["box"]

                # التصنيف بالإنجليزية (لمنع ظهور ???? على OpenCV)
                display_name = person.get("gender_display", "Person")
                age_label    = person.get("age", "")

                # رسم المربع الأخضر حول الوجه
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

                # كتابة التصنيف والعمر فوق الوجه
                label_text = f"{display_name} {age_label}".strip()
                cv2.putText(
                    frame,
                    label_text,
                    (x1, max(y1 - 10, 25)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2
                )

            # ==============================================================
            # عرض حالة النظام في الزاوية العلوية اليسرى
            # DANGER (أحمر) عند رصد خطر مؤكد - SAFE (أخضر) في الحالة الطبيعية
            # ==============================================================
            if analysis["hazard_detected"]:
                status_text  = "!! DANGER DETECTED !!"
                status_color = (0, 0, 255)   # أحمر
            else:
                status_text  = "System: SAFE"
                status_color = (0, 255, 0)   # أخضر

            cv2.putText(
                frame, status_text,
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, status_color, 2
            )

            # ==============================================================
            # مؤشر التسجيل النشط
            # ==============================================================
            if system.reporter.is_recording:
                cv2.putText(
                    frame, "● REC 30s",
                    (20, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 2
                )

            # ==============================================================
            # عرض الإطار في نافذة OpenCV
            # ==============================================================
            cv2.imshow("FlameEye - Autonomous Fire & Safety System", frame)

            # الخروج من الحلقة عند الضغط على زر 'q'
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("\n🛑 المستخدم طلب إيقاف النظام...")
                break

    finally:
        # إغلاق النظام بأمان عند الخروج (سواء بـ 'q' أو بأي خطأ)
        system.close()
        cv2.destroyAllWindows()
        print("✅ تم إغلاق نظام Flame Eye بنجاح.")


# نقطة الدخول الرئيسية للبرنامج
if __name__ == "__main__":
    main()