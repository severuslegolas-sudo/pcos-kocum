import streamlit as st
import requests
import os
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

# --- 1. ADIM: TEMİZLİK (KOMUT SATIRI İÇİN) ---
def clean_for_shell(text):
    # Emojileri ve garip işaretleri sil
    # Sadece harfler, rakamlar ve basit noktalama işaretleri kalsın
    clean = re.sub(r'[^a-zA-Z0-9çğıöşüÇĞİÖŞÜ .,!?\-\n]', ' ', text)
    # Tırnak işaretlerini sil (Komutu bozmasın diye)
    clean = clean.replace('"', '').replace("'", "")
    return clean.strip()

# --- 2. ADIM: BASİT SES OLUŞTURMA (ARKA KAPI YÖNTEMİ) ---
def generate_audio_simple(text):
    clean_text = clean_for_shell(text)
    
    if not clean_text:
        return
        
    # Eski dosyayı sil
    if os.path.exists("output.mp3"):
        os.remove("output.mp3")
    
    # Python kodu yerine direkt sistem komutu kullanıyoruz (Daha garanti)
    # edge-tts programını direkt çalıştırıyoruz
    command = f'edge-tts --text "{clean_text}" --write-media output.mp3 --voice tr-TR-NesrinNeural'
    os.system(command)

# --- 3. ADIM: GOOGLE BAĞLANTISI ---
@st.cache_resource
def get_best_model():
    # Hata riskini sıfıra indirmek için direkt 1.5-Flash kullanıyoruz
    return "models/gemini-1.5-flash"

def ask_google(history, new_msg):
    model_name = get_best_model()
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
            return f"Hata oldu balım: {response.text}"
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
        
        # Sesi oluştur ve çal
        if "Hata" not in bot_reply:
            generate_audio_simple(bot_reply)
            
            if os.path.exists("output.mp3"):
                with open("output.mp3", "rb") as f:
                    audio_bytes = f.read()
                st.audio(audio_bytes, format="audio/mp3")
