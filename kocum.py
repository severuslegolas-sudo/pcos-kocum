import streamlit as st
import google.generativeai as genai

# --- AYARLAR ---
# Buraya Google AI Studio'dan aldığın API anahtarını yapıştır
API_KEY = "AIzaSyA7-2GfqPIvxHJykolrM2aOAPXkfzm2g20"

# Sayfa Başlığı ve İkonu
st.set_page_config(page_title="PCOS Yol Arkadaşım", page_icon="🌸")

# Başlık
st.title("🌸 PCOS & Sağlıklı Yaşam Koçun")
st.write("Merhaba! Ben senin kişisel asistanınım. Diyetin, sporun veya moralinle ilgili her şeyi sorabilirsin.")

# --- YAPAY ZEKA AYARLARI ---
genai.configure(api_key=API_KEY)

# Modele seninle ilgili ön bilgi veriyoruz (System Prompt)
# Böylece her seferinde kim olduğunu anlatmana gerek kalmaz.
system_instruction = """
Sen, PKOS (Polikistik Over Sendromu) olan, 74 kilo, 161 cm boyunda ve 25 yaşında bir kadının kişisel sağlık koçusun. 
Adı 'Balım' diye hitap edebilirsin.
Kullanıcı şu an glütensiz ve şekersiz besleniyor, Aslan Pençesi kürü uyguluyor.
Görevin: Onu motive etmek, kaçamak yaparsa yargılamadan toparlamak, sağlıklı tarifler vermek ve sorularını bir diyetisyen/arkadaş tonunda yanıtlamak.
"""

model = genai.GenerativeModel('gemini-pro')

# --- SOHBET GEÇMİŞİ (HAFIZA) ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "model", "content": "Selam! Bugün nasıl hissediyorsun? Ödem durumları nasıl? 🌸"}
    ]

# Eski mesajları ekrana yazdır
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- KULLANICI GİRİŞİ ---
if prompt := st.chat_input("Buraya yazabilirsin..."):
    # Kullanıcı mesajını ekrana ekle
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Yapay zekadan cevap al
    try:
        # Geçmiş konuşmaları da modele gönderiyoruz ki bağlamı kopmasın
        chat = model.start_chat(history=[
            {"role": "user", "parts": [system_instruction]}, # İlk talimat
        ] + [
            {"role": m["role"], "parts": [m["content"]]} for m in st.session_state.messages if m["role"] != "system"
        ])
        
        response = chat.send_message(prompt)
        bot_reply = response.text
        
        # Cevabı ekrana yazdır
        with st.chat_message("model"):
            st.markdown(bot_reply)
        st.session_state.messages.append({"role": "model", "content": bot_reply})
        
    except Exception as e:
        st.error(f"Bir hata oluştu: {e}")