# config.py
import os

LOCATION_TAG = "مصنع - قسم التشغيل الرئيسي (Factory - Main Section)"

# بيانات الإيميل المعتمدة
TARGET_EMAIL = "aahhff262626@gmail.com"
SENDER_EMAIL = "aahhff262626@gmail.com"
SENDER_PASSWORD = "eudu rlps wyat zeok"

# بيانات الواتساب
TARGET_PHONE = "+201060034154"
CALLMEBOT_API_KEY = "1388599"

# إعدادات التخزين السحابي Cloudinary (محدثة بالرقم الصحيح)
CLOUDINARY_CLOUD_NAME = "nievei2z"
CLOUDINARY_API_KEY = "389124879819132"
CLOUDINARY_API_SECRET = "bGODaPVOWswocPbn9fVtlLSz_F8"

# ضبط متغير البيئة التلقائي
os.environ["CLOUDINARY_URL"] = f"cloudinary://{CLOUDINARY_API_KEY}:{CLOUDINARY_API_SECRET}@{CLOUDINARY_CLOUD_NAME}"

# إعدادات الكاميرا والتسجيل
CAMERA_INDEX = 0
RECORD_DURATION = 30
ALERT_COOLDOWN = 60
OUTPUT_DIR = "alert_records"
LOG_FILE = "fires.log"

FIRE_MODEL_PATH = "fire.pt"
ALARM_SOUND_PATH = "alarm_new.mp3"

FACE_PROTO = "opencv_face_detector.pbtxt"
FACE_MODEL = "opencv_face_detector_uint8.pb"
AGE_PROTO = "age_deploy.prototxt"
AGE_MODEL = "age_net.caffemodel"
GENDER_PROTO = "gender_deploy.prototxt"
GENDER_MODEL = "gender_net.caffemodel"