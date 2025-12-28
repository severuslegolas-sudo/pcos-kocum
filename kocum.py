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

# --- 1. ADIM: GELİŞMİŞ METİN TEMİZLİĞİ (EMOJİ SAVAR) ---
def clean_text_for_speech(text):
    # 1. Yıldız, kare, alt tire gibi markdown işaretlerini sil
    text = re.sub(r'[*_#`]', '', text)
    
    # 2. Linkleri sil (http ile başlayan her şey)
    text = re.sub(r'http\S+', '', text)
    
    # 3. Sadece Harfleri, Rakamları ve Noktalama İşaretlerini Tut
    # (Bu işlem emojileri yok eder, çünkü emojiler harf değildir)
    # Türkçeye özgü karakterleri koruyoruz (çğıöşüÇĞİÖŞÜ)
    cleaned = re.sub(r'[^a-zA-Z0-9çğıöşüÇĞİÖŞÜ .,!?\-\n]', '', text)
    
    return cleaned.strip()

# --- 2. ADIM: SES OLUŞTURMA ---
async def edge_tts_generate(text):
    voice = "tr-TR-NesrinNeural"
    output_file = "output.mp3"
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)

def play_audio(text):
    # Temizlenmiş metni al
    clean = clean_text_for_speech(text)
    
    # Eğer temizlendikten sonra geriye hiçbir şey kalmadıysa (sadece emoji atmışsa) ses çalma
    if not clean or len(clean) < 2:
        return
        
    try:
        # Asenkron döngü yönetimi
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
        # Hata olursa kullanıcıya yansıtma, loga yaz
        print(f"Ses hatası: {e}")

# --- 3. ADIM: SOHBET VE MODEL ---
@st.cache_resource
def get_best_model():
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"
    try:
        response = requests.get(url)
        data = response.json()
        if "models" in data:
            for model in data["models"]:
                if "generateContent" in model["supportedGenerationMethods"]:
                    return model["name"]
        return "models/gemini-1.5-flash"
    except:
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
        if "Hata" not in bot_reply:
            play_audio(bot_reply)
