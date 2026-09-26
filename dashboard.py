# dashboard.py
# ==============================================================================
# 🔥 FLAME EYE - Next-Gen Autonomous Fire & Safety Operations Center
# ==============================================================================

import streamlit as st
import os
import time
from datetime import datetime
import config

# إعداد الصفحة وتفعيل العرض الكامل
st.set_page_config(
    page_title="Flame Eye | Operations Center",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------------------------------------------
# تنسيق الواجهة بتصميم عصري غامق وفخم (Custom CSS & Glassmorphism)
# -------------------------------------------------------------
st.markdown("""
<style>
    /* خلفية الصفحة الداكنة والحديثة */
    .stApp {
        background: linear-gradient(135deg, #0b0f19 0%, #111827 50%, #0d131f 100%);
        color: #f3f4f6;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* رأس الصفحة والشعار */
    .brand-title {
        font-size: 2.8rem;
        font-weight: 800;
        background: linear-gradient(90deg, #ff4500, #ff8c00, #ff3366);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: 2px;
        margin-bottom: 0px;
    }
    .brand-subtitle {
        color: #9ca3af;
        font-size: 1.05rem;
        margin-bottom: 25px;
    }

    /* بطاقات المؤشرات (Metric Cards) */
    .metric-card {
        background: rgba(31, 41, 55, 0.7);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 69, 0, 0.25);
        border-radius: 14px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-4px);
        border-color: #ff4500;
    }
    .metric-value {
        font-size: 2.2rem;
        font-weight: 700;
        color: #ffffff;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #9ca3af;
        margin-top: 5px;
        text-transform: uppercase;
    }

    /* بطاقات الوكلاء الأذكياء */
    .agent-badge {
        background: rgba(17, 24, 39, 0.85);
        border: 1px solid rgba(16, 185, 129, 0.3);
        border-radius: 10px;
        padding: 12px 16px;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .pulse-dot {
        height: 10px;
        width: 10px;
        background-color: #10b981;
        border-radius: 50%;
        display: inline-block;
        box-shadow: 0 0 12px #10b981;
    }

    /* سجل الحوادث */
    .log-danger {
        background: rgba(239, 68, 68, 0.12);
        border-right: 4px solid #ef4444;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 8px;
        font-size: 0.95rem;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# القائمة الجانبية (Sidebar)
# -------------------------------------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/color/96/fire-element.png", width=70)
    st.markdown("### 🎛️ لوحة تحكم النظام")
    st.caption("FLAME EYE MULTI-AGENT V5.0")
    
    st.markdown("---")
    st.markdown(f"**📍 الموقع المراقب:**\n`{config.LOCATION_TAG}`")
    st.markdown(f"**📩 إيميل الطوارئ:**\n`{config.TARGET_EMAIL}`")
    st.markdown(f"**📱 هاتف الواتساب:**\n`{config.TARGET_PHONE}`")
    
    st.markdown("---")
    st.markdown("### 🔄 تحديث البيانات")
    if st.button("تحديث فوري للوحة (Refresh)", use_container_width=True):
        st.rerun()

    st.markdown("---")
    st.caption("🛡️ Flame Eye Autonomous AI Guard 2026")

# -------------------------------------------------------------
# رأس الصفحة (Header)
# -------------------------------------------------------------
col_head1, col_head2 = st.columns([3, 1])
with col_head1:
    st.markdown('<div class="brand-title">🔥 FLAME EYE</div>', unsafe_allow_html=True)
    st.markdown('<div class="brand-subtitle">مركز عمليات الحماية ومكافحة الحرائق الذاتي (Autonomous Multi-Agent Defense)</div>', unsafe_allow_html=True)

with col_head2:
    st.markdown("""
        <div style="background: rgba(16, 185, 129, 0.15); border: 1px solid #10b981; border-radius: 12px; padding: 12px; text-align: center; margin-top: 15px;">
            <span class="pulse-dot"></span>
            <span style="color: #10b981; font-weight: bold; margin-right: 8px;">النظام نشط 24/7</span>
            <div style="color: #9ca3af; font-size: 0.75rem; margin-top: 4px;">Fault-Tolerant Graph</div>
        </div>
    """, unsafe_allow_html=True)

# -------------------------------------------------------------
# قراءة الإحصائيات الحقيقية من السجلات
# -------------------------------------------------------------
total_incidents = 0
total_videos = 0
recent_logs = []

if os.path.exists(config.LOG_FILE):
    with open(config.LOG_FILE, "r", encoding="utf-8") as f:
        recent_logs = [line.strip() for line in f.readlines() if line.strip()]
        total_incidents = len(recent_logs)

if os.path.exists(config.OUTPUT_DIR):
    videos_list = [v for v in os.listdir(config.OUTPUT_DIR) if v.endswith(".mp4")]
    total_videos = len(videos_list)
else:
    videos_list = []

# -------------------------------------------------------------
# بطاقات الإحصائيات الحية (Top KPI Metric Cards)
# -------------------------------------------------------------
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color: #10b981;">ONLINE</div>
            <div class="metric-label">حالة الكاميرا والمراقبة</div>
        </div>
    """, unsafe_allow_html=True)

with kpi2:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color: #ff4500;">{total_incidents}</div>
            <div class="metric-label">إجمالي بلاغات الحريق المسجلة</div>
        </div>
    """, unsafe_allow_html=True)

with kpi3:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color: #3b82f6;">{total_videos}</div>
            <div class="metric-label">مقاطع فيديو الطوارئ (30s)</div>
        </div>
    """, unsafe_allow_html=True)

with kpi4:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color: #a855f7;">4 AGENTS</div>
            <div class="metric-label">وكلاء الذكاء الاصطناعي</div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# -------------------------------------------------------------
# جسم الصفحة الرئيسي: الوكلاء + سجل الحوادث
# -------------------------------------------------------------
col_main1, col_main2 = st.columns([1, 1.8])

with col_main1:
    st.markdown("### 🤖 وكلاء المنظومة (Multi-Agent Status)")
    st.caption("يعمل كل وكيل بشكل منفصل لضمان استمرارية التشغيل دون توقف.")

    st.markdown("""
        <div class="agent-badge">
            <div>
                <b style="color: #ffffff;">👁️ Agent 1: The Watcher</b><br>
                <span style="color: #9ca3af; font-size: 0.8rem;">بث الفيديو الحي و Auto-Reconnect</span>
            </div>
            <span style="color: #10b981; font-weight: bold; font-size: 0.85rem;">ACTIVE ●</span>
        </div>
        
        <div class="agent-badge">
            <div>
                <b style="color: #ffffff;">🧠 Agent 2: The Analyst</b><br>
                <span style="color: #9ca3af; font-size: 0.8rem;">YOLOv8 + كشف العمر والنوع ومنع الخطأ</span>
            </div>
            <span style="color: #10b981; font-weight: bold; font-size: 0.85rem;">ACTIVE ●</span>
        </div>

        <div class="agent-badge">
            <div>
                <b style="color: #ffffff;">🚨 Agent 3: The Responder</b><br>
                <span style="color: #9ca3af; font-size: 0.8rem;">صفارة الإنذار + واتساب + إيميل Gmail</span>
            </div>
            <span style="color: #10b981; font-weight: bold; font-size: 0.85rem;">ARMED ●</span>
        </div>

        <div class="agent-badge">
            <div>
                <b style="color: #ffffff;">📝 Agent 4: The Reporter</b><br>
                <span style="color: #9ca3af; font-size: 0.8rem;">تسجيل 30 ثانية وتوثيق fires.log</span>
            </div>
            <span style="color: #10b981; font-weight: bold; font-size: 0.85rem;">ACTIVE ●</span>
        </div>
    """, unsafe_allow_html=True)

with col_main2:
    st.markdown("### 📋 سجل التدقيق الأمني المباشر (Security Audit Log)")
    
    if recent_logs:
        # عرض آخر 6 أحداث مسجلة بتصميم أنيق
        for entry in reversed(recent_logs[-6:]):
            st.markdown(f"""
                <div class="log-danger">
                    <span style="color: #ff4500; font-weight: bold;">🚨 بلاغ أمني:</span> {entry}
                </div>
            """, unsafe_allow_html=True)
            
        # زر تنزيل السجل بالكامل
        log_text = "\n".join(recent_logs)
        st.download_button(
            label="📥 تحميل السجل الأمني بالكامل (Log File)",
            data=log_text,
            file_name=f"flame_eye_audit_{datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain"
        )
    else:
        st.success("🟢 المنطقة آمنة تماماً. لم تسجل أي بلاغات حريق أو دخان.")

st.markdown("---")

# -------------------------------------------------------------
# قسم استعراض وتشغيل الفيديوهات المسجلة
# -------------------------------------------------------------
st.markdown("### 📹 استعراض وتحليل فيديوهات الطوارئ المسجلة (Recorded Incidents)")
st.caption("كل فيديو مدته 30 ثانية يوثق لحظة رصد الخطر والأشخاص الموجودين في الموقع.")

if videos_list:
    sorted_vids = sorted(videos_list, reverse=True)
    c_vid1, c_vid2 = st.columns([1, 2])
    
    with c_vid1:
        chosen_video = st.selectbox("📂 حدد مقطع الفيديو:", sorted_vids)
        video_full_path = os.path.join(config.OUTPUT_DIR, chosen_video)
        
        # معلومات الفيديو
        v_size_mb = os.path.getsize(video_full_path) / (1024 * 1024)
        st.markdown(f"**حجم الملف:** `{v_size_mb:.2f} MB`")
        st.markdown(f"**المسار المحلي:** `{video_full_path}`")
        
        # زر تحميل الفيديو
        with open(video_full_path, "rb") as vf:
            st.download_button(
                label="⬇️ تحميل هذا الفيديو على الجهاز",
                data=vf.read(),
                file_name=chosen_video,
                mime="video/mp4",
                use_container_width=True
            )

    with c_vid2:
        st.video(video_full_path)
else:
    st.info("لم يتم تسجيل أي مقاطع فيديو حتى الآن. ستظهر هنا تلقائياً بمجرد رصد أي خطر.")