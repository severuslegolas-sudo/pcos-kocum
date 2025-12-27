

import streamlit as st
import requests
import json
from gtts import gTTS
import io

# --- AYARLAR ---
# BURAYA YENİ ALDIĞIN API ANAHTARINI YAPIŞTIR
API_KEY = "AIzaSyDV_RU_d5a-e9wRpECsJOflYBeFaB8mxJs" 

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="PCOS Nikosu", page_icon="🌸", layout="centered", initial_sidebar_state="collapsed")

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
    st.session_state.messages = [{"role": "model", "content": "Selam balım! Ben hazırım. Nasılsın? 🌸"}]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 1. ADIM: ÇALIŞAN MODELİ BULMA FONKSİYONU ---
@st.cache_resource # Bunu önbelleğe alıyoruz ki her seferinde aramasın
def get_best_model():
    # Google'a "Hangi modellerin var?" diye soruyoruz
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"
    try:
        response = requests.get(url)
        data = response.json()
        
        # Listeyi tarıyoruz
        if "models" in data:
            for model in data["models"]:
                # 'generateContent' özelliğini destekleyen bir model arıyoruz
                if "generateContent" in model["supportedGenerationMethods"]:
                    # Bulduğumuz ilk çalışan modelin adını döndür (Örn: models/gemini-1.5-flash)
                    return model["name"]
        return None
    except:
        return None

# --- 2. ADIM: SOHBET FONKSİYONU ---
def ask_google_auto(history, new_msg):
    # Önce çalışan modeli bulalım
    model_name = get_best_model()
    
    if not model_name:
        return "🚨 HATA: Geçerli bir model bulunamadı veya API Anahtarı hatalı."

    # Bulunan modeli kullanarak mesaj gönderelim
    # model_name zaten 'models/gemini-...' şeklinde geliyor
    url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:generateContent?key={API_KEY}"
    headers = {'Content-Type': 'application/json'}
    
    contents = []
    contents.append({"role": "user", "parts": [{"text": SYSTEM_PROMPT + "\n\nKonuşma Başlıyor:"}]})
    
    for msg in history:
        role = "user" if msg["role"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": msg["content"]}]})
    
    contents.append({"role": "user", "parts": [{"text": new_msg}]})
    
    payload = {"contents": contents}
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"Hata oldu balım (Kod {response.status_code}): {response.text}"
    except Exception as e:
        return f"Bağlantı sorunu: {str(e)}"

# --- SOHBET ARAYÜZÜ ---
if prompt := st.chat_input("Yaz balım..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.spinner('Nikosu düşünüyor...'):
        bot_reply = ask_google_auto(st.session_state.messages, prompt)
    
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
