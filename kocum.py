import streamlit as st
import requests
import json
from gtts import gTTS
import io

# --- AYARLAR ---
# LÜTFEN KENDİ API ANAHTARINI BURAYA YAPIŞTIR
API_KEY = "AIzaSyA7-2GfqPIvxHJykolrM2aOAPXkfzm2g20" 

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="PCOS Nikosu", page_icon="🌸", layout="centered", initial_sidebar_state="collapsed")

# İkon Ayarları
st.markdown("""
    <head>
        <link rel="apple-touch-icon" sizes="180x180" href="https://cdn-icons-png.flaticon.com/512/3461/3461858.png">
        <link rel="icon" type="image/png" sizes="32x32" href="https://cdn-icons-png.flaticon.com/512/3461/3461858.png">
    </head>
""", unsafe_allow_html=True)

st.title("🌸 PCOS Nikosu")

# --- MENÜ ---
with st.expander("📋 GÜNLÜK MENÜM", expanded=False):
    st.markdown("""
    * **Sabah:** Sirkeli su 💧
    * **Öğle:** Sebze + Protein 🥗
    * **Akşam:** Sebze + Yoğurt (Ekmek yok) 🚫🍞
    * **Gece:** Aslan pençesi 🌿
    """)

# --- NİKOSU KİMLİĞİ ---
SYSTEM_PROMPT = """
Sen 'PCOS Nikosu' adında bir sağlık koçusun. Kullanıcıya 'Balım' diye hitap et.
Kullanıcı glütensiz besleniyor ve aslan pençesi kürü yapıyor.
Görevin: Motive etmek, kısa ve emojili cevaplar vermek.
"""

# --- HAFIZA ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "model", "content": "Selam balım! Nikosu yanında. Bugün nasılsın? 🌸"}]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- YENİ FONKSİYON: DİREKT BAĞLANTI ---
def ask_google_direct(history, new_msg):
    # DİKKAT: Buradaki boşluklar çok önemli!
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={API_KEY}"
    headers = {'Content-Type': 'application/json'}
    
    # Geçmiş konuşmaları hazırla
    contents = []
    contents.append({"role": "user", "parts": [{"text": SYSTEM_PROMPT + "\n\nKonuşma Başlıyor:"}]})
    
    for msg in history:
        role = "user" if msg["role"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": msg["content"]}]})
    
    contents.append({"role": "user", "parts": [{"text": new_msg}]})
    
    payload = {"contents": contents}
    
    # İsteği gönder
    try:
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"Hata oluştu balım :( Kod: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Bağlantı hatası: {e}"

# --- SOHBET ---
if prompt := st.chat_input("Yaz balım..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.spinner('Nikosu düşünüyor...'):
        bot_reply = ask_google_direct(st.session_state.messages, prompt)
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.messages.append({"role": "model", "content": bot_reply})
    
    with st.chat_message("model"):
        st.markdown(bot_reply)
        try:
            tts = gTTS(text=bot_reply, lang='tr')
            audio_bytes = io.BytesIO()
            tts.write_to_fp(audio_bytes)
            audio_bytes.seek(0)
            st.audio(audio_bytes, format='audio/mp3')
        except:
            pass
