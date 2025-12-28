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
@st.cache_resource
def get_best_model():
    # Google'a "Elinizdeki modelleri ver" diyoruz
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"
    try:
        response = requests.get(url)
        data = response.json()
        
        # Listeyi tarayıp 'generateContent' yapabilen ilk modeli alıyoruz
        if "models" in data:
            for model in data["models"]:
                if "generateContent" in model["supportedGenerationMethods"]:
                    return model["name"] # Örn: models/gemini-1.5-flash döner
        
        # Liste boşsa varsayılanı döndür
        return "models/gemini-1.5-flash"
    except:
        # Bağlantı hatası olursa varsayılanı döndür
        return "models/gemini-1.5-flash"

# --- 2. ADIM: SES OLUŞTURMA ---
def clean_text(text):
    # Okunması zor işaretleri temizle
    return re.sub(r'[*_#`]', '', text)

async def edge_tts_generate(text):
    voice = "tr-TR-NesrinNeural"
    output_file = "output.mp3"
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)

def play_audio(text):
    clean = clean_text(text)
    # Eğer metin bir hata mesajıysa (içinde 'error' geçiyorsa) okuma
    if not clean.strip() or "error" in clean.lower() or "hata" in clean.lower():
        return
        
    try:
        # Asenkron döngü yönetimi (Loop Fix)
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        if loop.is_running():
            asyncio.ensure_future(edge_tts_generate(clean))
        else:
            loop.run_until_complete(edge_tts_generate(clean))
            
        if os.path.exists("output.mp3"):
            with open("output.mp3", "rb") as f:
                audio_bytes = f.read()
            st.audio(audio_bytes, format="audio/mp3")
            
    except Exception as e:
        st.warning(f"Ses çalınamadı: {e}")

# --- 3. ADIM: SOHBET ---
def ask_google(history, new_msg):
    # Otomatik bulunan modeli al
    model_name = get_best_model()
    
    # URL'yi oluştur
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
            # Hata kodunu direkt döndür
            return f"Hata oluştu: {response.text}"
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
        # Sadece mesaj başarılıysa ses çal
        if "Hata" not in bot_reply:
            play_audio(bot_reply)
