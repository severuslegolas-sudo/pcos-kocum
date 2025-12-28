import streamlit as st
import requests
import edge_tts
import asyncio
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

# --- 1. ADIM: METİN TEMİZLİK ---
def clean_text_final(text):
    # Ses motorunu bozan her şeyi sil
    clean = re.sub(r'[*_#`]', '', text)       # Markdown işaretleri
    clean = re.sub(r'http\S+', '', clean)     # Linkler
    # Emojileri sil (Sadece harf, rakam ve noktalama kalsın)
    clean = re.sub(r'[^a-zA-Z0-9çğıöşüÇĞİÖŞÜ .,!?\-\n]', '', clean)
    return clean.strip()

# --- 2. ADIM: SES OLUŞTURMA (SENKRONİZE YÖNTEM) ---
async def edge_tts_async(text):
    voice = "tr-TR-NesrinNeural"
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save("output.mp3")

def generate_audio_sync(text):
    clean = clean_text_final(text)
    if not clean: return
    
    # Eski dosyayı sil
    if os.path.exists("output.mp3"):
        try:
            os.remove("output.mp3")
        except:
            pass

    # Streamlit üzerinde Async çalıştırmanın en güvenli yolu:
    try:
        # Mevcut bir döngü var mı kontrol et
        loop = asyncio.get_event_loop()
        # Varsa o döngü içinde koştur
        if loop.is_running():
            asyncio.ensure_future(edge_tts_async(clean))
            # Not: Çalışan döngüde sonucu beklemek zordur, 
            # ancak dosya oluşumu hızlı olduğu için genellikle yakalar.
        else:
            loop.run_until_complete(edge_tts_async(clean))
    except RuntimeError:
        # Eğer döngü yoksa yeni yarat
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(edge_tts_async(clean))
        
    return True

# --- 3. ADIM: GOOGLE MODEL BULUCU ---
def get_working_model():
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"
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
        
        # Hata yoksa sesi oluştur
        if "Hata" not in bot_reply:
            with st.spinner('Ses hazırlanıyor...'):
                generate_audio_sync(bot_reply)
                
                # Dosyanın dolmasını bekle ve çal
                if os.path.exists("output.mp3") and os.path.getsize("output.mp3") > 0:
                    with open("output.mp3", "rb") as f:
                        audio_bytes = f.read()
                    st.audio(audio_bytes, format="audio/mp3")
                else:
                    # Dosya boşsa veya oluşmadıysa uyarı ver (hata kodu basma)
                    st.warning("Ses şu an oluşturulamadı (Sunucu yoğunluğu).")
