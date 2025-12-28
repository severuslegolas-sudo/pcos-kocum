import streamlit as st
import requests
from gtts import gTTS
import io
import re
import random
import datetime

# --- AYARLAR ---
if "GOOGLE_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    st.error("⚠️ Google API Anahtarı bulunamadı! Secrets ayarlarını kontrol et.")
    st.stop()

# --- SAYFA AYARLARI ---
st.set_page_config(
    page_title="PCOS Nikosu",
    page_icon="🌸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS SÜSLEMELERİ ---
st.markdown("""
<style>
    .stChatMessage { border-radius: 15px !important; padding: 10px !important; }
    [data-testid="stSidebar"] { background-color: #fdf2f8; border-right: 1px solid #fce7f3; }
    h1, h2, h3 { color: #db2777; }
    .menu-card { background-color: #fff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); margin-bottom: 10px; border-left: 5px solid #db2777; }
</style>
""", unsafe_allow_html=True)

# --- YEMEK VERİ TABANI (ARALIKLI ORUÇ UYUMLU) ---

# Sabah artık yemek yok, sadece sıvı önerileri var
SABAH_SIVILARI = [
    "☕ Sade Filtre Kahve (Sütsüz/Şekersiz)",
    "🍵 Yeşil Çay + Yarım Limon",
    "💧 Büyük Bardak Sirkeli Ilık Su",
    "🧉 Sade Maden Suyu + Limon Dilimi",
    "🌿 Kiraz Sapı Çayı (Ödem atıcı)"
]

# Öğle (İlk Öğün - Doyurucu)
OGLE = [
    "Izgara Tavuk Göğsü + Bol Yeşillik + 10 Badem",
    "Ton Balıklı Büyük Salata + Zeytinyağı Soslu",
    "3 Yumurtalı Mantarlı Omlet + Yarım Avokado (İlk öğün)",
    "Zeytinyağlı Yeşil Mercimek + Yoğurt",
    "Kıymalı Kabak Sote + Ceviz",
    "Haşlanmış Yumurta + Beyaz Peynir + Domates/Salatalık Söğüş",
    "Kinoalı Tavuklu Bowl (Bol lifli)"
]

# Akşam (Hafif ve Erken)
AKSAM = [
    "Fırın Somon + Haşlanmış Kuşkonmaz",
    "Zeytinyağlı Enginar + Dereotu",
    "Etli Bamya Yemeği (Pirinçsiz)",
    "Fırın Mücver (Unsuz) + Sarımsaklı Yoğurt",
    "Kıymalı Karnabahar Graten",
    "Brokoli Çorbası + Izgara Tavuk Parçaları",
    "Zeytinyağlı Taze Fasulye"
]

# --- HAFTALIK MENÜ OLUŞTURUCU ---
def create_weekly_menu():
    days = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
    menu = {}
    for day in days:
        menu[day] = {
            "Sabah": f"🚫 YEMEK YOK (IF) - {random.choice(SABAH_SIVILARI)}",
            "Ogle": random.choice(OGLE),
            "Aksam": random.choice(AKSAM)
        }
    return menu

# Menüyü Hafızaya Kaydet
if "weekly_menu" not in st.session_state:
    st.session_state.weekly_menu = create_weekly_menu()

# --- BUGÜNÜN MENÜSÜNÜ BUL ---
def get_todays_menu():
    day_index = datetime.datetime.today().weekday()
    days_tr = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
    today_name = days_tr[day_index]
    todays_food = st.session_state.weekly_menu[today_name]
    return today_name, todays_food

current_day, menu_today = get_todays_menu()

# --- YAN MENÜ (SIDEBAR) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/4322/4322992.png", width=80)
    st.title(f"📅 {current_day}")
    st.caption("Aralıklı Oruç Planın:")
    
    st.info(f"⏳ **Sabah (Açlık):**\n{menu_today['Sabah']}")
    st.success(f"🥗 **Öğle (İlk Öğün):**\n{menu_today['Ogle']}")
    st.warning(f"🍽️ **Akşam (Son Öğün):**\n{menu_today['Aksam']}")
    st.error("🍵 **Gece Kürü:** Aslan Pençesi Çayı")
    
    st.markdown("---")
    st.write("💧 *Açlık pencerende bol su içmeyi unutma balım!*")

# --- ANA EKRAN ---
st.title("🌸 PCOS Nikosu")
st.write("Senin kişisel yaşam koçun ve diyet arkadaşın!")

# SEKMELER
tab1, tab2 = st.tabs(["💬 Sohbet Et", "📅 Haftalık Menü Listesi"])

# --- SEKME 1: SOHBET ---
with tab1:
    # NİKOSU KİMLİĞİ (Güncellendi: IF Yaptığını Biliyor)
    SYSTEM_PROMPT = f"""
    Sen 'PCOS Nikosu'sun. En yakın kız arkadaş gibi samimi konuş.
    Kullanıcı 'Aralıklı Oruç' (IF) yapıyor, sabahları kahvaltı ETMİYOR.
    
    Bugünkü planı:
    Sabah: {menu_today['Sabah']} (Sadece sıvı)
    Öğle: {menu_today['Ogle']}
    Akşam: {menu_today['Aksam']}
    
    Eğer 'Kahvaltı ne yiyeyim?' derse 'Kız unuttun mu oruçtayız, sadece kahve/su içiyoruz' diye uyar.
    Hitaplar: Balım, Kuzum, Fıstığım.
    ASLA resmi konuşma.
    """

    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "model", "content": "Selam balım! Aralıklı orucun nasıl gidiyor? Açlık durumun nasıl, dayanabiliyor musun? 🌸"}]

    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar="🌸" if message["role"] == "model" else "👤"):
            st.markdown(message["content"])

    # Ses Fonksiyonları (gTTS)
    def clean_text_for_gtts(text):
        clean = re.sub(r'[*_#`]', '', text) 
        clean = re.sub(r'http\S+', '', clean)
        clean = re.sub(r'[^a-zA-Z0-9çğıöşüÇĞİÖŞÜ .,!?\-\n]', '', clean).strip()
        return clean

    def play_audio_gtts(text):
        clean_text = clean_text_for_gtts(text)
        if not clean_text: return
        try:
            tts = gTTS(text=clean_text, lang='tr')
            audio_bytes = io.BytesIO()
            tts.write_to_fp(audio_bytes)
            audio_bytes.seek(0)
            st.audio(audio_bytes, format='audio/mp3')
        except:
            pass

    # Google Model
    def ask_google(history, new_msg):
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"
            model = "models/gemini-pro"
            gen_url = f"https://generativelanguage.googleapis.com/v1beta/{model}:generateContent?key={API_KEY}"
            headers = {'Content-Type': 'application/json'}
            contents = [{"role": "user", "parts": [{"text": SYSTEM_PROMPT}]}]
            for msg in history:
                role = "user" if msg["role"] == "user" else "model"
                contents.append({"role": role, "parts": [{"text": msg["content"]}]})
            contents.append({"role": "user", "parts": [{"text": new_msg}]})
            res = requests.post(gen_url, headers=headers, json={"contents": contents})
            if res.status_code == 200:
                return res.json()['candidates'][0]['content']['parts'][0]['text']
            return "Şu an bağlantıda minik bir pürüz var balım."
        except:
            return "İnternetinde sorun olabilir mi kuzum?"

    if prompt := st.chat_input("Nikosu'ya yaz..."):
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.spinner('Nikosu düşünüyor...'):
            reply = ask_google(st.session_state.messages[:-1], prompt)
        st.session_state.messages.append({"role": "model", "content": reply})
        with st.chat_message("model", avatar="🌸"):
            st.markdown(reply)
            play_audio_gtts(reply)

# --- SEKME 2: HAFTALIK MENÜ ---
with tab2:
    col_h1, col_h2 = st.columns([3, 1])
    with col_h1:
        st.header("🗓️ Bu Haftaki IF Planın")
        st.write("Aralıklı Oruç (16/8) düzenine göre hazırlandı! Sabahlar boş.")
    with col_h2:
        if st.button("🔄 Listeyi Yenile"):
            st.session_state.weekly_menu = create_weekly_menu()
            st.rerun()

    my_menu = st.session_state.weekly_menu
    days_order = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
    
    c1, c2 = st.columns(2)
    for i, day in enumerate(days_order):
        card_html = f"""
        <div class="menu-card">
            <h3 style="margin:0; color:#be185d;">{day}</h3>
            <p style="color:#6b7280;"><b>⏳ Sabah:</b> {my_menu[day]['Sabah']}</p>
            <p><b>🥗 İlk Öğün (Öğle):</b> {my_menu[day]['Ogle']}</p>
            <p><b>🍽️ Son Öğün (Akşam):</b> {my_menu[day]['Aksam']}</p>
        </div>
        """
        if i % 2 == 0: c1.markdown(card_html, unsafe_allow_html=True)
        else: c2.markdown(card_html, unsafe_allow_html=True)

# --- ALT KISIM (VİDEOLAR) ---
st.markdown("---")
st.subheader("🧘‍♀️ Günlük Egzersiz Önerileri")
v1, v2, v3 = st.columns(3)
with v1:
    st.video("https://www.youtube.com/watch?v=inpok4MKVLM")
    st.caption("🌞 Sabah Yogası (Aç Karnına Çok İyi Gelir)")
with v2:
    st.video("https://www.youtube.com/watch?v=enYITYwvPAQ")
    st.caption("🚶‍♀️ Evde Yürüyüş")
with v3:
    st.video("https://www.youtube.com/watch?v=M-805010FjE")
    st.caption("🌙 Akşam Esnemesi")
