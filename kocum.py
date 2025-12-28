import streamlit as st
import requests
import re

# --- AYARLAR ---
if "GOOGLE_API_KEY" in st.secrets:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    st.error("Google Anahtarı Yok!")
    st.stop()

if "ELEVEN_API_KEY" in st.secrets:
    ELEVEN_API_KEY = st.secrets["ELEVEN_API_KEY"]
else:
    st.error("ElevenLabs Anahtarı Yok! Secrets ayarına ekle.")
    st.stop()

# --- SAYFA ---
st.set_page_config(page_title="PCOS Nikosu", page_icon="🌸", layout="centered", initial_sidebar_state="collapsed")
st.title("🌸 PCOS Nikosu")

# --- MENÜ ---
with st.expander("📋 GÜNLÜK MENÜM", expanded=False):
    st.markdown("""
    * **Sabah:** Sirkeli su 💧
    * **Öğle:** Sebze + Protein 🥗
    * **Gece:** Aslan pençesi 🌿
    """)

# --- KİMLİK ---
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

# --- SES (ELEVENLABS - DİREKT BAĞLANTI) ---
def play_elevenlabs_audio(text):
    # Temizlik
    clean = re.sub(r'[*_#`]', '', text)
    clean = re.sub(r'http\S+', '', clean)
    clean = re.sub(r'[^a-zA-Z0-9çğıöşüÇĞİÖŞÜ .,!?\-\n]', '', clean).strip()
    
    if not clean: return

    # Rachel Sesinin ID'si (Sabittir)
    VOICE_ID = "21m00Tcm4TlvDq8ikWAM" 
    
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVEN_API_KEY
    }
    
    data = {
        "text": clean,
        "model_id": "eleven_multilingual_v2", # Türkçe için en iyi model
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }

    try:
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code == 200:
            st.audio(response.content, format='audio/mp3')
        else:
            # Hata varsa (Kredi bitti vs.) ekrana yazdırıp uyaralım
            st.warning(f"Ses oluşturulamadı (Kod: {response.status_code})")
            
    except Exception as e:
        st.warning(f"Bağlantı hatası: {e}")

# --- GOOGLE MODEL ---
def get_model():
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GOOGLE_API_KEY}"
        data = requests.get(url).json()
        for m in data.get("models", []):
            if "generateContent" in m.get("supportedGenerationMethods", []):
                return m["name"]
        return "models/gemini-pro"
    except:
        return "models/gemini-pro"

def ask_google(history, new_msg):
    model = get_model()
    url = f"https://generativelanguage.googleapis.com/v1beta/{model}:generateContent?key={GOOGLE_API_KEY}"
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
            play_elevenlabs_audio(reply)
