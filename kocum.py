import streamlit as st
import requests
from elevenlabs.client import ElevenLabs
import re

# --- AYARLAR VE GÜVENLİK ---
# 1. Google Anahtarı Kontrolü
if "GOOGLE_API_KEY" in st.secrets:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    st.error("Google API Anahtarı bulunamadı! Secrets ayarlarını kontrol et.")
    st.stop()

# 2. ElevenLabs Anahtarı Kontrolü
if "ELEVEN_API_KEY" in st.secrets:
    ELEVEN_API_KEY = st.secrets["ELEVEN_API_KEY"]
else:
    st.error("ElevenLabs API Anahtarı bulunamadı! Lütfen Adım 2'yi tekrar yap.")
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

# --- 1. ADIM: SES İÇİN TEMİZLİK ---
def clean_text_final(text):
    # Yıldızları, linkleri ve emojileri temizle
    # ElevenLabs temiz metni daha güzel okur
    clean = re.sub(r'[*_#`]', '', text)
    clean = re.sub(r'http\S+', '', clean)
    clean = re.sub(r'[^a-zA-Z0-9çğıöşüÇĞİÖŞÜ .,!?\-\n]', '', clean)
    return clean.strip()

# --- 2. ADIM: ELEVENLABS SES OLUŞTURMA ---
def play_elevenlabs_audio(text):
    clean = clean_text_final(text)
    if not clean: return

    try:
        # ElevenLabs'e bağlan
        client = ElevenLabs(api_key=ELEVEN_API_KEY)
        
        # Sesi oluştur
        # Model: 'eleven_multilingual_v2' -> Bu model Türkçeyi mükemmel konuşur.
        # Voice: 'Rachel' -> Tatlı bir kadın sesi.
        audio_generator = client.generate(
            text=clean,
            voice="Rachel", 
            model="eleven_multilingual_v2"
        )
        
        # Gelen sesi birleştir ve çal
        audio_bytes = b"".join(audio_generator)
        st.audio(audio_bytes, format='audio/mp3')
        
    except Exception as e:
        # Eğer kredi biterse veya hata olursa
        st.warning(f"Ses oluşturulamadı (Kredi bitmiş olabilir): {e}")

# --- 3. ADIM: GOOGLE MODEL BULUCU ---
def get_working_model():
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GOOGLE_API_KEY}"
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
    url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:generateContent?key={GOOGLE_API_KEY}"
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
        
        if "Hata" not in bot_reply:
            play_elevenlabs_audio(bot_reply)
