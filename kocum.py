import streamlit as st
import requests
import json
from gtts import gTTS
import io

# --- AYARLAR ---
# YENİ ALDIĞIN API ANAHTARINI BURAYA YAPIŞTIR (Tırnakları silme!)
API_KEY = "AIzaSyDV_RU_d5a-e9wRpECsJOflYBeFaB8mxJs" 

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="PCOS Nikosu", page_icon="🌸", layout="centered", initial_sidebar_state="collapsed")

st.title("🌸 PCOS Nikosu (Dedektif Modu 🕵️‍♀️)")

# --- NİKOSU KİMLİĞİ ---
SYSTEM_PROMPT = "Sen PCOS Nikosu'sun. Kullanıcıya Balım de. Kısa cevap ver."

# --- HAFIZA ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "model", "content": "Selam! Hatayı bulmak için geldim. Bir şeyler yaz. 🕵️‍♀️"}]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- HATA GÖSTEREN FONKSİYON ---
def ask_google_debug(history, new_msg):
    # Sadece en garantili modeli deneyelim ve hatayı görelim
    model_name = "gemini-pro"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={API_KEY}"
    headers = {'Content-Type': 'application/json'}
    
    contents = []
    contents.append({"role": "user", "parts": [{"text": SYSTEM_PROMPT}]})
    contents.append({"role": "user", "parts": [{"text": new_msg}]})
    
    payload = {"contents": contents}

    try:
        response = requests.post(url, headers=headers, json=payload)
        
        # EĞER BAŞARILIYSA
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        
        # EĞER HATA VARSA (İşte burası bize hatayı söyleyecek)
        else:
            return f"🚨 HATA YAKALANDI! \n\nKOD: {response.status_code} \n\nMESAJ: {response.text}"
            
    except Exception as e:
        return f"🚨 BAĞLANTI HATASI: {str(e)}"

# --- SOHBET ---
if prompt := st.chat_input("Test mesajı yaz..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.spinner('Hata taranıyor...'):
        bot_reply = ask_google_debug(st.session_state.messages, prompt)
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.messages.append({"role": "model", "content": bot_reply})
    
    with st.chat_message("model"):
        st.markdown(bot_reply)
        # Hata mesajını okumasın, sadece başarılıysa okusun
        if "HATA" not in bot_reply:
            try:
                tts = gTTS(text=bot_reply, lang='tr')
                audio_bytes = io.BytesIO()
                tts.write_to_fp(audio_bytes)
                audio_bytes.seek(0)
                st.audio(audio_bytes, format='audio/mp3')
            except:
                pass
