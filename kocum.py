import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import io

# --- AYARLAR ---
API_KEY = "SENIN_API_ANAHTARIN"  # Buraya kendi API anahtarını yapıştırmayı unutma!

# --- SAYFA AYARLARI ---
st.set_page_config(
    page_title="PCOS Nikosu",
    page_icon="🌸",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Android İkonu İçin HTML
st.markdown(
    """
    <head>
        <link rel="apple-touch-icon" sizes="180x180" href="https://cdn-icons-png.flaticon.com/512/3461/3461858.png">
        <link rel="icon" type="image/png" sizes="32x32" href="https://cdn-icons-png.flaticon.com/512/3461/3461858.png">
    </head>
    """,
    unsafe_allow_html=True
)

st.title("🌸 PCOS Nikosu")

# --- MENÜ (GÜNLÜK PLAN) ---
with st.expander("📋 GÜNLÜK RUTİN & MENÜM (Tıkla)", expanded=False):
    st.markdown("""
    **Sabah:** Sirkeli su + Yüz masajı 💧
    **Öğle:** Yarım tabak sebze + Ton balığı/Tavuk + Ayran 🥗
    **Ara:** Acıkırsan 2 ceviz + bitki çayı ☕
    **Akşam:** Sebze yemeği/Izgara + Yoğurt (Ekmek yok!) 🚫🍞
    **Gece:** Aslan pençesi kürü 🌿
    """)

# --- YAPAY ZEKA AYARLARI ---
genai.configure(api_key=API_KEY)

system_instruction = """
Sen, PKOS (Polikistik Over Sendromu) olan, 74 kilo, 161 cm boyunda ve 25 yaşında bir kadının kişisel sağlık ve yaşam koçusun.
Adın 'PCOS Nikosu'. Kullanıcıya 'Balım', 'Tatlım' gibi samimi hitap et.
Kullanıcı glütensiz/şekersiz besleniyor, Aslan Pençesi kürü yapıyor.
Görevin: Motive etmek, tarif vermek ve onu yargılamadan dinlemek.
Cevapların kısa, net ve emojili olsun.
"""

model = genai.GenerativeModel('gemini-pro')

# --- HAFIZA ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "model", "content": "Selam balım! Nikosu yanında. Bugün nasılsın, kaçamak var mı? 🌸"}
    ]

# Eski mesajları ekrana yaz
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- SOHBET VE SES ---
if prompt := st.chat_input("Buraya yaz balım..."):
    # Kullanıcı mesajını ekle
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Yapay zeka cevabı
    try:
        chat = model.start_chat(history=[
            {"role": "user", "parts": [system_instruction]},
        ] + [
            {"role": m["role"], "parts": [m["content"]]} for m in st.session_state.messages if m["role"] != "system"
        ])
        
        with st.spinner('Nikosu yazıyor... ✍️'):
            response = chat.send_message(prompt)
            bot_reply = response.text

        # Cevabı ekrana bas
        with st.chat_message("model"):
            st.markdown(bot_reply)
            
            # --- SESLİ OKUMA (Google Ses Teknolojisi) ---
            # Cevabı sese çeviriyoruz
            try:
                tts = gTTS(text=bot_reply, lang='tr')
                audio_bytes = io.BytesIO()
                tts.write_to_fp(audio_bytes)
                audio_bytes.seek(0)
                
                # Oynatıcıyı göster
                st.audio(audio_bytes, format='audio/mp3')
            except:
                st.warning("Ses oluşturulamadı ama metin yukarıda 👆")

        st.session_state.messages.append({"role": "model", "content": bot_reply})

    except Exception as e:
        st.error(f"Bir hata oldu: {e}")
