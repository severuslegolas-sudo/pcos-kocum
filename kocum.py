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

# --- YEMEK VERİ TABANI ---
SABAH_SIVILARI = [
    "☕ Sade Filtre Kahve (Sütsüz/Şekersiz)",
    "🍵 Yeşil Çay + Yarım Limon",
    "💧 Büyük Bardak Sirkeli Ilık Su",
    "🧉 Sade Maden Suyu + Limon Dilimi",
    "🌿 Kiraz Sapı Çayı (Ödem atıcı)"
]

KAHVALTI_WEEKEND = [
    "🍳 Menemen + 1 Dilim Karabuğday Ekmeği",
    "🥑 2 Haşlanmış Yumurta + Yarım Avokado + Yeşillik",
    "🧀 Peynirli Maydanozlu Omlet + 5 Zeytin",
    "🥞 Yulaflı Muzlu Pankek (Şekersiz)",
    "🍅 Sahanda Yumurta + Domates/Salatalık Söğüş"
]

OGLE = [
    "Izgara Tavuk Göğsü + Bol Yeşillik",
    "Ton Balıklı Büyük Salata + Limon Soslu",
    "3 Yumurtalı Mantarlı Omlet (Hafta içi ilk öğün)",
    "Zeytinyağlı Yeşil Mercimek + Yoğurt",
    "Kıymalı Kabak Sote + Ceviz",
    "Haşlanmış Yumurta + Beyaz Peynir + Salata",
    "Kinoalı Tavuklu Bowl"
]

AKSAM = [
    "Fırın Somon + Haşlanmış Kuşkonmaz",
    "Zeytinyağlı Enginar + Dereotu",
    "Etli Bamya Yemeği (Pirinçsiz)",
    "Fırın Mücver (Unsuz) + Sarımsaklı Yoğurt",
    "Kıymalı Karnabahar Graten",
    "Brokoli Çorbası + Izgara Tavuk",
    "Zeytinyağlı Taze Fasulye"
]

# --- HAFTALIK MENÜ OLUŞTURUCU ---
def create_weekly_menu():
    days = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
    menu = {}
    for day in days:
        if day in ["Cumartesi", "Pazar"]:
            sabah_secimi = f"🎉 HAFTA SONU KEYFİ: {random.choice(KAHVALTI_WEEKEND)}"
        else:
            sabah_secimi = f"🚫 IF (Açlık): {random.choice(SABAH_SIVILARI)}"

        menu[day] = {
            "Sabah": sabah_secimi,
            "Ogle": random.choice(OGLE),
            "Aksam": random.choice(AKSAM)
        }
    return menu

if "weekly_menu" not in st.session_state:
    st.session_state.weekly_menu = create_weekly_menu()

def get_todays_menu():
    day_index = datetime.datetime.today().weekday()
    days_tr = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
    today_name = days_tr[day_index]
    todays_food = st.session_state.weekly_menu[today_name]
    return today_name, todays_food

current_day, menu_today = get_todays_menu()

# --- YAN MENÜ ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/4322/4322992.png", width=80)
    st.title(f"📅 {current_day}")
    st.caption("Bugünkü Planın:")
    if "HAFTA SONU" in menu_today['Sabah']:
        st.success(f"🍳 **Sabah:**\n{menu_today['Sabah']}")
    else:
        st.info(f"⏳ **Sabah:**\n{menu_today['Sabah']}")
    st.success(f"🥗 **Öğle:**\n{menu_today['Ogle']}")
    st.warning(f"🍽️ **Akşam:**\n{menu_today['Aksam']}")
    st.error("🍵 **Gece:** Aslan Pençesi Kürü")
    st.markdown("---")
    st.write("💧 *Bol su içmeyi unutma balım!*")

# --- ANA EKRAN ---
st.title("🌸 PCOS Nikosu")
st.write("Hafta içi disiplin, hafta sonu ödül! Dengeli yaşam koçun.")

tab1, tab2 = st.tabs(["💬 Sohbet Et", "📅 Haftalık Menü Listesi"])

# --- SOHBET ---
with tab1:
    SYSTEM_PROMPT = f"""
    Sen 'PCOS Nikosu'sun. En yakın kız arkadaş gibi samimi konuş.
    Kullanıcı hafta içi IF yapıyor (kahvaltı yok), ama HAFTA SONLARI kahvaltı yapıyor.
    Bugün günlerden: {current_day}
    Menü: {menu_today}
    ASLA resmi konuşma. Samimi ol.
    """

    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "model", "content": "Selam balım! Menünü ayarladım, her şey yolunda mı? 🌸"}]

    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar="🌸" if message["role"] == "model" else "👤"):
            st.markdown(message["content"])

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

    # --- OTOMATİK MODEL BULUCU (ÇÖZÜM BURADA) ---
    @st.cache_resource
    def get_working_model():
        # Google'a sor: Hangi modellerin çalışıyor?
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"
            response = requests.get(url)
            data = response.json()
            # Listeyi tara, sohbet edebilen ilk modeli kap gel
            if "models" in data:
                for model in data["models"]:
                    if "generateContent" in model.get("supportedGenerationMethods", []):
                        return model["name"]
            return "models/gemini-pro" # Bulamazsa eskisi
        except:
            return "models/gemini-pro"

    def ask_google(history, new_msg):
        try:
            # Otomatik bulunan çalışan modeli al
            model_name = get_working_model()
            
            url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:generateContent?key={API_KEY}"
            headers = {'Content-Type': 'application/json'}
            
            contents = [{"role": "user", "parts": [{"text": SYSTEM_PROMPT}]}]
            for msg in history:
                role = "user" if msg["role"] == "user" else "model"
                contents.append({"role": role, "parts": [{"text": msg["content"]}]})
            contents.append({"role": "user", "parts": [{"text": new_msg}]})
            
            res = requests.post(url, headers=headers, json={"contents": contents})
            
            if res.status_code == 200:
                return res.json()['candidates'][0]['content']['parts'][0]['text']
            else:
                return f"Google amca yine nazlandı balım, hata kodu: {res.status_code}"
        except Exception as e:
            return f"Bağlantı sorunu kuzum: {str(e)}"

    if prompt := st.chat_input("Nikosu'ya yaz..."):
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.spinner('Nikosu düşünüyor...'):
            reply = ask_google(st.session_state.messages[:-1], prompt)
        st.session_state.messages.append({"role": "model", "content": reply})
        with st.chat_message("model", avatar="🌸"):
            st.markdown(reply)
            if "hata" not in reply.lower():
                play_audio_gtts(reply)

# --- MENÜ LİSTESİ ---
with tab2:
    col_h1, col_h2 = st.columns([3, 1])
    with col_h1:
        st.header("🗓️ Bu Haftaki Planın")
    with col_h2:
        if st.button("🔄 Listeyi Yenile"):
            st.session_state.weekly_menu = create_weekly_menu()
            st.rerun()

    my_menu = st.session_state.weekly_menu
    days_order = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
    c1, c2 = st.columns(2)
    for i, day in enumerate(days_order):
        bg = "#fefce8" if day in ["Cumartesi", "Pazar"] else "#fff"
        border = "#ca8a04" if day in ["Cumartesi", "Pazar"] else "#db2777"
        html = f"""
        <div style="background-color:{bg}; padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid {border}; box-shadow: 0 2px 5px rgba(0,0,0,0.05);">
            <h3 style="margin:0; color:{border};">{day}</h3>
            <p style="color:#555;"><b>🍳 Sabah:</b> {my_menu[day]['Sabah']}</p>
            <p><b>🥗 Öğle:</b> {my_menu[day]['Ogle']}</p>
            <p><b>🍽️ Akşam:</b> {my_menu[day]['Aksam']}</p>
        </div>
        """
        if i % 2 == 0: c1.markdown(html, unsafe_allow_html=True)
        else: c2.markdown(html, unsafe_allow_html=True)

st.markdown("---")
st.subheader("🧘‍♀️ Günlük Egzersiz Önerileri")
v1, v2, v3 = st.columns(3)
with v1:
    st.video("https://www.youtube.com/watch?v=inpok4MKVLM")
    st.caption("🌞 Sabah Yogası")
with v2:
    st.video("https://www.youtube.com/watch?v=enYITYwvPAQ")
    st.caption("🚶‍♀️ Evde Yürüyüş")
with v3:
    st.video("https://www.youtube.com/watch?v=M-805010FjE")
    st.caption("🌙 Akşam Esnemesi")
