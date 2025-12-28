import streamlit as st
import requests
from gtts import gTTS
import io
import re

# --- AYARLAR ---
if "GOOGLE_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    st.error("API Anahtarı bulunamadı! Secrets ayarlarını kontrol et.")
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

# --- 1. ADIM: METİN TEMİZLİĞİ ---
def clean_text_for_gtts(text):
    # Emojileri ve Markdown işaretlerini temizle
    # gTTS emojileri okumaya çalışırken saçmalamasın diye siliyoruz
    clean = re.sub(r'[*_#`]', '', text) 
    clean = re.sub(r'http\S+', '', clean)
    # Sadece harf, rakam ve Türkçe karakterleri tut
    clean = re.sub(r'[^a-zA-Z0-9çğıöşüÇĞİÖŞÜ .,!?\-\n]', '', clean)
    return clean.strip()

# --- 2. ADIM: SES OLUŞTURMA (gTTS - GARANTİLİ) ---
def play_audio_gtts(text):
    clean_text = clean_text_for_gtts(text)
    
    if not clean_text:
        return

    try:
        # Sesi hafızada oluştur (Dosya kaydetme derdi yok)
        tts = gTTS(text=clean_text, lang='tr')
        audio_bytes = io.BytesIO()
        tts.write_to_fp(audio_bytes)
        audio_bytes.seek(0)
        
        # Oynat
        st.audio(audio_bytes, format='audio/mp3')
        
    except Exception as e:
        st.warning(f"Ses hatası: {e}")

# --- 3. ADIM: OTOMATİK MODEL BULUCU ---
def get_working_model():
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"
    try:
        response = requests.get(url)
        data = response.json()
        if "models" in data:
            for model in data["models"]:
                if "generateContent" in model.get("supportedGenerationMethods", []):
                    return model["name"]
        return "models/gemini-pro"
    except:
        return "models/gemini-pro"

# --- 4. ADIM: SOHBET ---
def ask_google(history, new_msg):
    model_name = get_working_model()
    url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:generateContent?key={API_KEY}"
    headers = {'Content-Type': 'application/json'}
    
    contents = [{"role": "user", "parts": [{"text": SYSTEM_PROMPT}]}]
    for msg in history:
        role = "user" if msg["role"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": msg["content"]}]})
    contents.append({"role": "user", "parts": [{"text": new_msg}]})
    
    try:
        response = requests.post(url, headers=headers, json={"contents": contents})
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"Hata oldu balım ({response.status_code}): {response.text}"
    except Exception as e:
        return f"Bağlantı sorunu: {str(e)}"

# --- ARAYÜZ ---
if prompt := st.chat_input("Yaz balım..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.spinner('Nikosu düşünüyor...'):
        bot_reply = ask_google(st.session_state.messages[:-1], prompt)
    
    st.session_state.messages.append({"role": "model", "content": bot_reply})
    
    with st.chat_message("model"):
        st.markdown(bot_reply)
        
        # Hata yoksa sesi çal
        if "Hata" not in bot_reply:
            play_audio_gtts(bot_reply)
