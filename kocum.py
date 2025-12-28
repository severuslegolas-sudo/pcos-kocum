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

# --- 1. ADIM: OTOMATİK MODEL BULUCU (ÇÖZÜM BURADA) ---
def get_working_model():
    # Google'a "Elinizdeki modelleri ver" diyoruz
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"
    try:
        response = requests.get(url)
        data = response.json()
        
        # Listeyi tarayıp 'generateContent' yapabilen ilk modeli alıyoruz
        if "models" in data:
            for model in data["models"]:
                # Sadece sohbet edebilen modelleri seç
                if "generateContent" in model.get("supportedGenerationMethods", []):
                    return model["name"] # Örn: models/gemini-pro döner
        
        # Eğer liste boş gelirse en eski ve sağlam modeli dene
        return "models/gemini-pro"
    except:
        return "models/gemini-pro"

# --- 2. ADIM: SES OLUŞTURMA (GARANTİ YÖNTEM) ---
def clean_for_shell(text):
    # Emojileri ve garip işaretleri sil
    clean = re.sub(r'[^a-zA-Z0-9çğıöşüÇĞİÖŞÜ .,!?\-\n]', ' ', text)
    clean = clean.replace('"', '').replace("'", "")
    return clean.strip()

def generate_audio_simple(text):
    clean_text = clean_for_shell(text)
    if not clean_text: return
        
    if os.path.exists("output.mp3"):
        os.remove("output.mp3")
    
    # edge-tts komutunu direkt çalıştır
    command = f'edge-tts --text "{clean_text}" --write-media output.mp3 --voice tr-TR-NesrinNeural'
    os.system(command)

# --- 3. ADIM: SOHBET ---
def ask_google(history, new_msg):
    # Otomatik bulunan modeli al
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
            generate_audio_simple(bot_reply)
            
            if os.path.exists("output.mp3"):
                with open("output.mp3", "rb") as f:
                    audio_bytes = f.read()
                st.audio(audio_bytes, format="audio/mp3")
