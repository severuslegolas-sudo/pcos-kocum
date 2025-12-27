import streamlit as st
import requests
import asyncio
import edge_tts
import os

# --- AYARLAR ---
# Şifreyi Streamlit Secrets kasasından çekiyoruz
# Eğer kasa yapmadıysan buraya: API_KEY = "kendi_sifren" yaz.
if "GOOGLE_API_KEY" in st.secrets:
    API_KEY = st.secrets["AIzaSyDV_RU_d5a-e9wRpECsJOflYBeFaB8mxJs"]
else:
    st.error("API Anahtarı bulunamadı! Lütfen Secrets ayarlarını yap.")
    st.stop()

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
Sen 'PCOS Nikosu'sun. Karşındaki kişi senin en yakın kız arkadaşın, ona 'Balım', 'Kuzum', 'Çiçeğim' gibi samimi hitap et.
ASLA robot gibi konuşma. WhatsApp'tan yazışıyormuş gibi "ya", "hani", "aynen" gibi kelimeler kullan.
Kullanıcı glütensiz besleniyor. Kaçamak yaparsa tatlı sert kız ama moral ver.
Kısa, net ve emojili cevaplar ver.
"""

# --- HAFIZA ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "model", "content": "Selam balım! Ben geldim, nasılsın bugün? 🌸"}]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- YENİ NESİL SES FONKSİYONU (DOĞAL SES) ---
async def text_to_speech_edge(text):
    # 'tr-TR-NesrinNeural' sesi çok doğaldır.
    voice = "tr-TR-NesrinNeural"
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save("output.mp3")

# --- MODEL SEÇİMİ VE SOHBET ---
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
        return "models/gemini-pro"
    except:
        return "models/gemini-pro"

def ask_google_auto(history, new_msg):
    model_name = get_best_model()
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
            return f"Hata oldu balım: {response.text}"
    except Exception as e:
        return f"Bağlantı sorunu: {str(e)}"

# --- ARAYÜZ ---
if prompt := st.chat_input("Yaz balım..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.spinner('Nikosu düşünüyor...'):
        bot_reply = ask_google_auto(st.session_state.messages[:-1], prompt) # Son mesaj hariç geçmişi gönder
    
    st.session_state.messages.append({"role": "model", "content": bot_reply})
    
    with st.chat_message("model"):
        st.markdown(bot_reply)
        
        # --- SES OLUŞTURMA KISMI ---
        try:
            # Ses dosyasını oluştur
            asyncio.run(text_to_speech_edge(bot_reply))
            
            # Dosyayı okuyup oynatıcıya ver
            if os.path.exists("output.mp3"):
                audio_file = open("output.mp3", "rb")
                audio_bytes = audio_file.read()
                st.audio(audio_bytes, format="audio/mp3")
                audio_file.close()
        except Exception as e:
            st.warning(f"Ses oluşturulamadı: {e}")
