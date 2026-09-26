Fire_Project/
│
├── config.py                 # الإعدادات الموحدة (الإيميل، الواتساب، المسارات)
├── main.py                   # نقطة تشغيل النظام
├── dashboard.py              # لوحة تحكم ذكية حية (Streamlit Dashboard)
├── fires.log                 # سجل أمني دائم لكل الحرائق المكتشفة
│
└── agents/                   # مجلد الوكلاء الأذكياء
    ├── __init__.py
    ├── watcher.py            # [Agent 1: The Watcher] - مسؤول الكاميرا والربط
    ├── analyst.py            # [Agent 2: The Analyst] - مسؤول كشف الحريق والوجوه ومنع الإنذار الكاذب
    ├── responder.py          # [Agent 3: The Responder] - مسؤول الإنذار الصوتي والواتساب والإيميل
    ├── reporter.py           # [Agent 4: The Reporter] - مسجل الفيديوهات ومسؤول الـ Logging
    └── orchestrator.py       # [The Director] - مدير الرسم البياني وموجه المهام (StateGraph)