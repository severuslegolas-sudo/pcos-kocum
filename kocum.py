import streamlit as st
import requests
import asyncio
import edge_tts
import os
import re # Metin temizliği için gerekli

# --- AYARLAR ---
if "GOOGLE_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    # Eğer secrets çalışmazsa buraya manuel yazabilirsin ama secrets daha iyidir.
    st.error("API Anahtarı bulunamadı! Lütfen Secrets ayarlarını kontrol et.")
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
Sen 'PCOS Nikosu'sun. Karşındaki kişi senin en yakın kız arkadaşın.
Ona 'Balım', 'Kuzum', 'Çiçeğim' gibi samimi hitap et.
WhatsApp'tan yazışıyormuş gibi samimi konuş. "Size nasıl yardımcı olabilirim" ASLA deme.
Kullanıcı glütensiz besleniyor. Kaçamak yaparsa tatlı sert kız ama moral ver.
"""

# --- HAFIZA ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "model", "content": "Selam balım! Ben geldim, nasılsın bugün? 🌸"}]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- SES İÇİN METİN TEMİZLEYİCİ ---
def clean_text_for_speech(text):
    # Yıldızları (*), kareleri (#) ve markdown işaretlerini temizle
    clean = re.sub(r'[*_#`]', '', text)
    return clean

# --- YENİ NESİL SES FONKSİYONU ---
async def text_to_speech_edge(text):
    voice = "tr-TR-NesrinNeural" # En doğal Türkçe kadın sesi
    output_file = "output.mp3"
    
    # Metni temizle ki motor bozulmasın
    cleaned_text = clean_text_for_speech(text)
    
    # Eğer metin boşsa işlem yapma
    if not cleaned_text.strip():
        return
        
    communicate = edge_tts.Communicate(cleaned_text, voice)
    await communicate.save(output_file)

# --- MODEL SEÇİMİ VE SOHBET ---
@st.cache_resource
def get_best_model():
    # Model bulamazsa garanti olanı döndürür
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
        bot_reply = ask_google_auto(st.session_state.messages[:-1], prompt)
    
    st.session_state.messages.append({"role": "model", "content": bot_reply})
    
    with st.chat_message("model"):
        st.markdown(bot_reply)
        
        # --- SES OLUŞTURMA ---
        try:
            # Önceki ses dosyasını temizle (çakışma olmasın)
            if os.path.exists("output.mp3"):
                os.remove("output.mp3")
                
            # Yeni sesi oluştur
            asyncio.run(text_to_speech_edge(bot_reply))
            
            # Dosyayı oynat
            if os.path.exists("output.mp3"):
                audio_file = open("output.mp3", "rb")
                audio_bytes = audio_file.read()
                st.audio(audio_bytes, format="audio/mp3")
                audio_file.close()
            else:
                st.warning("Ses dosyası oluşturulamadı (Sunucu yoğun olabilir).")
                
        except Exception as e:
            # Kullanıcıya teknik hata gösterme, sadece logla
            print(f"Ses hatası: {e}")
            st.info("Ses şu an yüklenemedi ama metin yukarıda 👆")
