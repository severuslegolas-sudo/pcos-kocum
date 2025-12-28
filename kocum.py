import streamlit as st
import requests
from gtts import gTTS
import io
import re

# --- AYARLAR ---
if "GOOGLE_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    st.error("Google Anahtarı Yok! Lütfen Secrets ayarlarını kontrol et.")
    st.stop()

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="PCOS Nikosu", page_icon="🌸", layout="centered", initial_sidebar_state="collapsed")
st.title("🌸 PCOS Nikosu")

# --- MENÜ ---
with st.expander("📋 GÜNLÜK MENÜM", expanded=False):
    st.markdown("""
    * **Sabah:** Sirkeli su 💧
    * **Öğle:** Sebze + Protein 🥗
    * **Gece:** Aslan pençesi 🌿
    """)

# --- NİKOSU KİMLİĞİ ---
SYSTEM_PROMPT = """
Sen 'PCOS Nikosu'sun. En yakın kız arkadaş gibi samimi konuş.
Hitaplar: Balım, Kuzum, Çiçeğim.
ASLA 'Size nasıl yardımcı olabilirim' deme.
Kısa, net ve emojili cevaplar ver.
"""

# --- HAFIZA ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "model", "content": "Selam balım! Ben geldim. 🌸"}]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- SES (GARANTİLİ gTTS) ---
def play_audio_gtts(text):
    # Emojileri temizle ki Google okurken saçmalamasın
    clean = re.sub(r'[*_#`]', '', text) 
    clean = re.sub(r'http\S+', '', clean)
    clean = re.sub(r'[^a-zA-Z0-9çğıöşüÇĞİÖŞÜ .,!?\-\n]', '', clean).strip()
    
    if not clean: return

    try:
        # Sesi hafızada oluştur
        tts = gTTS(text=clean, lang='tr')
        audio_bytes = io.BytesIO()
        tts.write_to_fp(audio_bytes)
        audio_bytes.seek(0)
        
        # Oynat
        st.audio(audio_bytes, format='audio/mp3')
    except Exception as e:
        st.warning(f"Ses hatası: {e}")

# --- MODEL BULUCU ---
def get_working_model():
    # Otomatik olarak çalışan modeli bulur
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"
        data = requests.get(url).json()
        for m in data.get("models", []):
            if "generateContent" in m.get("supportedGenerationMethods", []):
                return m["name"]
        return "models/gemini-pro"
    except:
        return "models/gemini-pro"

# --- SOHBET ---
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
        return "Hata oldu balım."
    except:
        return "Bağlantı hatası."

# --- ARAYÜZ ---
if prompt := st.chat_input("Yaz balım..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.spinner('Nikosu düşünüyor...'):
        reply = ask_google(st.session_state.messages[:-1], prompt)
    
    st.session_state.messages.append({"role": "model", "content": reply})
    
    with st.chat_message("model"):
        st.markdown(reply)
        if "Hata" not in reply:
            play_audio_gtts(reply)
