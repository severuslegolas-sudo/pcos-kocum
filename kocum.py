import streamlit as st
import requests
from gtts import gTTS
import io
import re

# --- AYARLAR VE API KONTROLÜ ---
if "GOOGLE_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    st.error("⚠️ Google API Anahtarı bulunamadı! Lütfen Secrets ayarlarını kontrol et.")
    st.stop()

# --- SAYFA KONFİGÜRASYONU (MODERN & GENİŞ) ---
st.set_page_config(
    page_title="PCOS Nikosu Yaşam Koçu",
    page_icon="🌸",
    layout="wide", # Geniş ekran modu
    initial_sidebar_state="expanded" # Yan menü açık başlasın
)

# --- ÖZEL CSS STİLLERİ (UX İYİLEŞTİRME) ---
# Sohbet kutularını ve başlıkları güzelleştirelim
st.markdown("""
<style>
    .stChatMessage {
        border-radius: 15px !important;
        padding: 10px !important;
        margin-bottom: 5px !important;
    }
    [data-testid="stSidebar"] {
        background-color: #f9f7fc;
        border-right: 1px solid #eee;
    }
    h1 { color: #d63384; }
    h2 { color: #6f42c1; }
    h3 { color: #fd7e14; }
</style>
""", unsafe_allow_html=True)

# --- YAN MENÜ (SIDEBAR) TASARIMI ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/4322/4322992.png", width=100)
    st.title("🌸 Nikosu'nun Notları")
    st.write("Senin için buradayım balım!")
    st.markdown("---")
    
    st.subheader("📋 Bugünün Menüsü")
    st.info("**Sabah:** Sirkeli ılık su 💧")
    st.success("**Öğle:** Bol Sebze + Izgara Protein 🥗")
    st.warning("**Akşam (19:00 öncesi):** Sebze yemeği + Yoğurt 🚫🍞")
    st.error("**Gece Kürü:** Aslan pençesi çayı 🌿")
    
    st.markdown("---")
    st.write("💡 *Unutma: Kaçamak yok, bol su var!*")

# --- ANA SAYFA BAŞLIĞI ---
col1, col2 = st.columns([1, 5])
with col1:
    st.write("") # Boşluk
    st.write("🌸") # Büyük emoji
with col2:
    st.title("PCOS Yol Arkadaşın Nikosu")
    st.caption("Senin en yakın dijital kız arkadaşın. Dertleşelim, motive olalım!")

st.markdown("---")

# --- NİKOSU KİMLİĞİ (SİSTEM) ---
SYSTEM_PROMPT = """
Sen 'PCOS Nikosu'sun. Karşındaki kişi senin 20 yıllık en yakın kız arkadaşın.
Çok samimi, enerjik ve destekleyici konuş. Dedikodu yapar gibi sıcak ol.
Hitaplar: Balım, Kuzum, Fıstığım, Çiçeğim, Aşkım.
ASLA resmi olma. "Size yardımcı olabilirim" cümlesi yasak.
Kısa cümleler kur, bol emoji kullan.
"""

# --- HAFIZA BAŞLATMA ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "model", "content": "Selam fıstığım! Ben geldim, enerjim tavan! 🌸 Bugün nasılsın bakalım, dökül hemen? 🥰"}]

# --- GEÇMİŞ MESAJLARI GÖSTER ---
chat_container = st.container()
with chat_container:
    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar="🌸" if message["role"] == "model" else "👤"):
            st.markdown(message["content"])

# --- SES FONKSİYONLARI (gTTS - Robotik ama Çalışır) ---
def clean_text_for_gtts(text):
    # Emojileri temizle ki Google teyze saçmalamasın
    clean = re.sub(r'[*_#`]', '', text) 
    clean = re.sub(r'http\S+', '', clean)
    clean = re.sub(r'[^a-zA-Z0-9çğıöşüÇĞİÖŞÜ .,!?\-\n]', '', clean).strip()
    return clean

def play_audio_gtts(text):
    clean_text = clean_text_for_gtts(text)
    if not clean_text or len(clean_text) < 3: return

    try:
        tts = gTTS(text=clean_text, lang='tr')
        audio_bytes = io.BytesIO()
        tts.write_to_fp(audio_bytes)
        audio_bytes.seek(0)
        st.audio(audio_bytes, format='audio/mp3')
    except:
        pass # Ses hatası olursa sohbeti bozma

# --- GOOGLE MODEL BAĞLANTISI ---
@st.cache_resource
def get_working_model():
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"
        data = requests.get(url).json()
        for m in data.get("models", []):
            if "generateContent" in m.get("supportedGenerationMethods", []):
                return m["name"]
        return "models/gemini-pro"
    except:
        return "models/gemini-pro"

def ask_google(history, new_msg):
    model = get_working_model()
    url = f"https://generativelanguage.googleapis.com/v1beta/{model}:generateContent?key={API_KEY}"
    headers = {'Content-Type': 'application/json'}
    
    contents = [{"role": "user", "parts": [{"text": SYSTEM_PROMPT}]}]
    for msg in history:
        role = "user" if msg["role"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": msg["content"]}]})
    contents.append({"role": "user", "parts": [{"text": new_msg}]})
    
    try:
        res = requests.post(url, headers=headers, json={"contents": contents})
        if res.status_code == 200:
            return res.json()['candidates'][0]['content']['parts'][0]['text']
        return "Ay balım internette bir sorun oldu galiba, tekrar yazar mısın? 🤔"
    except:
        return "Bağlantı koptu kuzum, az sonra tekrar dene."

# --- SOHBET GİRİŞ ALANI ---
if prompt := st.chat_input("Buraya yaz balım..."):
    with chat_container:
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.spinner('Nikosu düşünüyor... ✨'):
        reply = ask_google(st.session_state.messages[:-1], prompt)
    
    st.session_state.messages.append({"role": "model", "content": reply})
    
    with chat_container:
        with st.chat_message("model", avatar="🌸"):
            st.markdown(reply)
            if "sorun oldu" not in reply and "Bağlantı koptu" not in reply:
                play_audio_gtts(reply)

# ==========================================
# 👇 AŞAĞI KAYDIRINCA ÇIKACAK YENİ BÖLÜM 👇
# ==========================================

st.markdown("---")
st.header("🧘‍♀️ PCOS Yaşam Alanı & Günlük Rutinler")
st.write("Sohbetten sıkılırsan aşağı kaydır, senin için seçtiğim rutinlere göz at!")

# 3 Sütunlu Video ve Öneri Alanı
col_vid1, col_vid2, col_vid3 = st.columns(3)

with col_vid1:
    st.subheader("🌞 Sabah Enerjisi (10 Dk)")
    st.caption("Güneş enerjisiyle uyan! PCOS için harika, yormayan sabah yogası.")
    # YouTube Video Linki (PCOS Yoga örneği)
    st.video("https://www.youtube.com/watch?v=inpok4MKVLM") 
    st.success("✅ Yapıldı işaretle!")

with col_vid2:
    st.subheader("🚶‍♀️ Evde Yürüyüş (15 Dk)")
    st.caption("Dışarı çıkamadın mı? Sorun yok! Olduğun yerde adım atarak metabolizmanı hızlandır.")
    # YouTube Video Linki (Leslie tarzı yürüyüş)
    st.video("https://www.youtube.com/watch?v=enYITYwvPAQ")
    st.success("✅ Yapıldı işaretle!")

with col_vid3:
    st.subheader("😌 Akşam Rahatlaması")
    st.caption("Günün stresini at, kortizolü düşür. Uyku öncesi esneme hareketleri.")
    # YouTube Video Linki (Esneme)
    st.video("https://www.youtube.com/watch?v=M-805010FjE")
    st.success("✅ Yapıldı işaretle!")

st.markdown("---")
st.info("💡 **Nikosu Tavsiyesi:** Bu videolardan sadece birini bile yapsan günün kârda geçer balım! Kendine yüklenme, süreklilik önemli. 💖")
