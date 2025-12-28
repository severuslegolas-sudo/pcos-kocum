import streamlit as st
import requests
import asyncio
import edge_tts
import os
import re

# --- AYARLAR ---
if "GOOGLE_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    # Kasa yoksa manuel giriş (tavsiye edilmez ama test için gerekebilir)
    # API_KEY = "BURAYA_ANAHTAR_GELEBILIR"
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

# --- METİN TEMİZLEME ---
def clean_text(text):
    return re.sub(r'[*_#`]', '', text)

# --- SES OLUŞTURMA (DÖNGÜ DÜZELTMELİ) ---
async def edge_tts_generate(text):
    voice = "tr-TR-NesrinNeural"
    output_file = "output.mp3"
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)

def play_audio(text):
    clean = clean_text(text)
    if not clean.strip():
        return
        
    try:
        # Mevcut bir döngü varsa onu kullan, yoksa yeni oluştur
        # Streamlit bulut ortamında bu kısım kritiktir
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        if loop.is_running():
            # Eğer döngü zaten çalışıyorsa (Streamlit bazen yapar) görevi ekle
            future = asyncio.ensure_future(edge_tts_generate(clean))
            # Streamlit'te çalışan döngüyü beklemek zor olduğu için
            # burada alternatif bir yöntem deniyoruz:
            loop.run_until_complete(edge_tts_generate(clean))
        else:
            loop.run_until_complete(edge_tts_generate(clean))
            
        # Sesi Çal
        if os.path.exists("output.mp3"):
            with open("output.mp3", "rb") as f:
                audio_bytes = f.read()
            st.audio(audio_bytes, format="audio/mp3")
            
    except Exception as e:
        # HATAYI GİZLEME, GÖSTER
        st.error(f"⚠️ Ses Hatası: {str(e)}")

# --- GOOGLE MODEL ---
@st.cache_resource
def get_model_url():
    # Model bulma işini basitleştirdik, direkt Pro kullanıyoruz hata riskini azaltmak için
    return f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={API_KEY}"

def ask_google(history, new_msg):
    url = get_model_url()
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
            return f"Hata: {response.text}"
    except Exception as e:
        return f"Bağlantı sorunu: {str(e)}"

# --- ARAYÜZ ---
if prompt := st.chat_input("Yaz balım..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.spinner('Yazıyor...'):
        bot_reply = ask_google(st.session_state.messages[:-1], prompt)
    
    st.session_state.messages.append({"role": "model", "content": bot_reply})
    
    with st.chat_message("model"):
        st.markdown(bot_reply)
        # Ses fonksiyonunu çağır
        play_audio(bot_reply)
