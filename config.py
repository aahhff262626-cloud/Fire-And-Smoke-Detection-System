# config.py
# إعدادات النظام الموحدة

LOCATION_TAG = "مصنع - قسم التشغيل الرئيسي (Factory - Main Section)"

# بيانات التواصل المعتمدة
TARGET_EMAIL = "aahhff262626@gmail.com"
SENDER_EMAIL = "aahhff262626@gmail.com"
SENDER_PASSWORD = "eudu rlps wyat zeok"

TARGET_PHONE = "+201060034154"
CALLMEBOT_API_KEY = "1388599"

# الكاميرا والتسجيل
CAMERA_INDEX = 0
RECORD_DURATION = 30
ALERT_COOLDOWN = 60
OUTPUT_DIR = "alert_records"
LOG_FILE = "fires.log"

# النماذج والأصوات
FIRE_MODEL_PATH = "fire.pt"
ALARM_SOUND_PATH = "alarm_new.mp3"

FACE_PROTO = "opencv_face_detector.pbtxt"
FACE_MODEL = "opencv_face_detector_uint8.pb"
AGE_PROTO = "age_deploy.prototxt"
AGE_MODEL = "age_net.caffemodel"
GENDER_PROTO = "gender_deploy.prototxt"
GENDER_MODEL = "gender_net.caffemodel"