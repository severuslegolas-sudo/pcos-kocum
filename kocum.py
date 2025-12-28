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
    page_title="PCOS Niko",
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
    .big-font { font-size:18px !important; color: #4b5563; }
    .menu-card { background-color: #fff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); margin-bottom: 10px; border-left: 5px solid #db2777; }
</style>
""", unsafe_allow_html=True)

# --- YEMEK VERİ TABANI (PCOS DOSTU) ---
KAHVALTI = [
    "2 Haşlanmış Yumurta + Bol Yeşillik + 5 Zeytin",
    "Mantarlı Omlet + Yarım Avokado",
    "Menemen (Az yağlı) + 1 Dilim Karabuğday Ekmeği",
    "Yulaflı Chia Puding (Şekersiz, meyveli)",
    "Peynirli Maydanozlu Omlet + Salatalık",
    "Haşlanmış Yumurta + Ceviz + Beyaz Peynir",
    "Sebzeli Omlet (Biber, Domates, Ispanak)"
]

OGLE = [
    "Izgara Tavuk Göğsü + Mevsim Salatası",
    "Ton Balıklı Salata (Mısırsız) + Limon Soslu",
    "Zeytinyağlı Yeşil Mercimek Yemeği + Yoğurt",
    "Köfte (Ekmeksiz) + Fırın Sebze",
    "Kinoalı Tavuklu Bowl",
    "Kabak Spagetti + Yoğurtlu Cevizli Sos",
    "Nohutlu Ispanak Salatası"
]

AKSAM = [
    "Fırın Somon + Kuşkonmaz",
    "Zeytinyağlı Enginar + Dereotu",
    "Etli Bamya Yemeği (Az Pirinçli)",
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
            "Sabah": random.choice(KAHVALTI),
            "Ogle": random.choice(OGLE),
            "Aksam": random.choice(AKSAM)
        }
    return menu

# Menüyü Hafızaya Kaydet (Sayfa yenilenince kaybolmasın)
if "weekly_menu" not in st.session_state:
    st.session_state.weekly_menu = create_weekly_menu()

# --- BUGÜNÜN MENÜSÜNÜ BUL ---
def get_todays_menu():
    # Bugünün gününü bul (0=Pazartesi, 6=Pazar)
    day_index = datetime.datetime.today().weekday()
    days_tr = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
    today_name = days_tr[day_index]
    
    # Hafızadaki listeden bugünü çek
    todays_food = st.session_state.weekly_menu[today_name]
    return today_name, todays_food

current_day, menu_today = get_todays_menu()

# --- YAN MENÜ (SIDEBAR) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/4322/4322992.png", width=80)
    st.title(f"📅 {current_day}")
    st.caption("Bugünkü PCOS Planın:")
    
    st.info(f"🍳 **Sabah:**\n{menu_today['Sabah']}")
    st.success(f"🥗 **Öğle:**\n{menu_today['Ogle']}")
    st.warning(f"🍽️ **Akşam:**\n{menu_today['Aksam']}")
    st.error("🍵 **Gece:** Aslan Pençesi Kürü")
    
    st.markdown("---")
    st.write("💧 *Günde 2.5 Litre su içmeyi unutma balım!*")

# --- ANA EKRAN ---
st.title("🌸 PCOS Niko")
st.write("Senin kişisel yaşam koçun ve diyet arkadaşın!")

# SEKMELER (TABLAR)
tab1, tab2 = st.tabs(["💬 Sohbet Et", "📅 Haftalık Menü Listesi"])

# --- SEKME 1: SOHBET ---
with tab1:
    # NİKOSU KİMLİĞİ
    SYSTEM_PROMPT = f"""
    Sen 'PCOS Niko'sun. En yakın kız arkadaş gibi samimi konuş.
    Kullanıcının bugünkü menüsü şöyle:
    Sabah: {menu_today['Sabah']}
    Öğle: {menu_today['Ogle']}
    Akşam: {menu_today['Aksam']}
    Eğer yemek sorarsa bu menüden bahset.
    Hitaplar: Balım, Kuzum, Fıstığım.
    ASLA resmi konuşma.
    """

    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "model", "content": "Selam balım! Menüne baktım harika görünüyor. Bugün nasılsın? 🌸"}]

    # Mesajları Göster
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
            # Otomatik model seçimi (Basit)
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

    # Sohbet Girişi
    if prompt := st.chat_input("Niko'ya yaz..."):
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.spinner('Niko düşünüyor...'):
            reply = ask_google(st.session_state.messages[:-1], prompt)
        
        st.session_state.messages.append({"role": "model", "content": reply})
        
        with st.chat_message("model", avatar="🌸"):
            st.markdown(reply)
            play_audio_gtts(reply)

# --- SEKME 2: HAFTALIK MENÜ ---
with tab2:
    col_h1, col_h2 = st.columns([3, 1])
    with col_h1:
        st.header("🗓️ Bu Haftaki Planın")
        st.write("Senin için glütensiz, şekersiz ve PCOS dostu hazırladım!")
    with col_h2:
        # Menü Yenileme Butonu
        if st.button("🔄 Listeyi Yenile"):
            st.session_state.weekly_menu = create_weekly_menu()
            st.rerun()

    # Haftalık Listeyi Ekrana Bas
    my_menu = st.session_state.weekly_menu
    days_order = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
    
    # 2 Sütun halinde gösterelim
    c1, c2 = st.columns(2)
    
    for i, day in enumerate(days_order):
        # Kart Tasarımı HTML
        card_html = f"""
        <div class="menu-card">
            <h3 style="margin:0; color:#be185d;">{day}</h3>
            <p><b>🍳 Sabah:</b> {my_menu[day]['Sabah']}</p>
            <p><b>🥗 Öğle:</b> {my_menu[day]['Ogle']}</p>
            <p><b>🍽️ Akşam:</b> {my_menu[day]['Aksam']}</p>
        </div>
        """
        
        if i % 2 == 0:
            c1.markdown(card_html, unsafe_allow_html=True)
        else:
            c2.markdown(card_html, unsafe_allow_html=True)

# --- ALT KISIM (VİDEOLAR) ---
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
