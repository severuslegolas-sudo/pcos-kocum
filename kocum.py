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
    st.error("⚠️ Google API Anahtarı bulunamadı!")
    st.stop()

# --- SAYFA AYARLARI ---
st.set_page_config(
    page_title="PCOS Nikosu",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed" # Yan menüyü kapalı başlat, daha ferah olsun
)

# --- 🎨 PRO TASARIM & CSS (PINTEREST ESTETİĞİ) ---
st.markdown("""
<style>
    /* Google Font İçe Aktar */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap');

    /* GENEL SAYFA YAPISI */
    html, body, [class*="css"] {
        font-family: 'Poppins', sans-serif;
    }
    
    /* ARKA PLAN (Pastel Geçiş) */
    .stApp {
        background: linear-gradient(135deg, #fdfbf7 0%, #fce7f3 100%);
    }

    /* SOHBET BALONLARI (Buzlu Cam Efekti) */
    .stChatMessage {
        background-color: rgba(255, 255, 255, 0.6);
        backdrop-filter: blur(10px);
        border-radius: 20px !important;
        border: 1px solid rgba(255, 255, 255, 0.5);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        margin-bottom: 15px !important;
        padding: 20px !important;
    }

    /* MENÜ KARTLARI (Şık & Modern) */
    .menu-card {
        background-color: #ffffff;
        border-radius: 20px;
        padding: 25px;
        margin-bottom: 20px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s;
        border: 1px solid #f3f4f6;
    }
    .menu-card:hover {
        transform: translateY(-5px);
    }
    
    /* BAŞLIKLAR */
    h1, h2, h3 {
        color: #831843; /* Koyu Gül Kurusu */
        font-weight: 600;
    }
    
    /* BUTONLAR */
    .stButton>button {
        background-color: #be185d;
        color: white;
        border-radius: 50px;
        padding: 10px 25px;
        border: none;
        box-shadow: 0 4px 6px rgba(190, 24, 93, 0.3);
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #9d174d;
        box-shadow: 0 6px 8px rgba(190, 24, 93, 0.4);
    }
    
    /* GİZLİ ELEMENTLER (Temizlik) */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
</style>
""", unsafe_allow_html=True)

# --- YEMEK VERİLERİ (GÜNCELLENMİŞ) ---
SABAH_SIVILARI = [
    "Sade Filtre Kahve ☕", "Yeşil Çay + Limon 🍵", "Sirkeli Ilık Su 💧", "Maden Suyu + Limon 🍋"
]

KAHVALTI_WEEKEND = [
    "Menemen + 1 Dilim Ekmek", "Avokadolu Haşlanmış Yumurta", "Peynirli Omlet + Zeytin", "Yulaflı Muzlu Pankek"
]

OGLE = [
    "Izgara Tavuk + Yeşillik", "Ton Balıklı Salata", "Mantarlı Omlet (Hafta içi)", 
    "Yeşil Mercimek + Yoğurt", "Kabak Sote + Ceviz", "Kinoalı Bowl"
]

AKSAM = [
    "Fırın Somon + Kuşkonmaz", "Zeytinyağlı Enginar", "Etli Bamya (Pirinçsiz)", 
    "Fırın Mücver + Yoğurt", "Karnabahar Graten", "Brokoli Çorbası"
]

# --- FONKSİYONLAR ---
def create_weekly_menu():
    days = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
    menu = {}
    for day in days:
        if day in ["Cumartesi", "Pazar"]:
            sabah = f"Hafta Sonu Keyfi ✨: {random.choice(KAHVALTI_WEEKEND)}"
        else:
            sabah = f"IF (Sıvı Dönemi) 💧: {random.choice(SABAH_SIVILARI)}"
        menu[day] = {"Sabah": sabah, "Ogle": random.choice(OGLE), "Aksam": random.choice(AKSAM)}
    return menu

if "weekly_menu" not in st.session_state:
    st.session_state.weekly_menu = create_weekly_menu()

def get_todays_menu():
    day_idx = datetime.datetime.today().weekday()
    days = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
    today = days[day_idx]
    return today, st.session_state.weekly_menu[today]

curr_day, curr_menu = get_todays_menu()

# --- YAN MENÜ (SIDEBAR - MINIMALIST) ---
with st.sidebar:
    st.title(f"🌿 {curr_day}")
    st.markdown("### Günlük Planın")
    
    # Kart Görünümü (Sidebar içi)
    st.markdown(f"""
    <div style="background:white; padding:15px; border-radius:15px; box-shadow:0 2px 5px rgba(0,0,0,0.05);">
        <p style="font-size:14px; color:#888; margin-bottom:5px;">SABAH</p>
        <p style="font-weight:600; color:#333;">{curr_menu['Sabah']}</p>
        <hr style="margin:10px 0; border-top:1px solid #eee;">
        <p style="font-size:14px; color:#888; margin-bottom:5px;">ÖĞLE</p>
        <p style="font-weight:600; color:#333;">{curr_menu['Ogle']}</p>
        <hr style="margin:10px 0; border-top:1px solid #eee;">
        <p style="font-size:14px; color:#888; margin-bottom:5px;">AKŞAM</p>
        <p style="font-weight:600; color:#333;">{curr_menu['Aksam']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.info("🌙 **Gece Kürü:** Aslan Pençesi")

# --- ANA EKRAN BAŞLIK ---
col_logo, col_text = st.columns([1, 6])
with col_text:
    st.markdown("<h1 style='margin-bottom:0;'>PCOS Nikosu</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#666; font-size:18px;'>Dengeli beslenme ve yaşam rehberin.</p>", unsafe_allow_html=True)

# --- TAB MENÜSÜ ---
tab_chat, tab_menu, tab_yoga = st.tabs(["💬 Sohbet", "📅 Yemek Planı", "🧘‍♀️ Egzersiz"])

# --- TAB 1: SOHBET ---
with tab_chat:
    # Model & Ses Fonksiyonları
    def clean_text_for_gtts(text):
        clean = re.sub(r'[*_#`]', '', text) 
        clean = re.sub(r'http\S+', '', clean)
        clean = re.sub(r'[^a-zA-Z0-9çğıöşüÇĞİÖŞÜ .,!?\-\n]', '', clean).strip()
        return clean

    def play_audio_gtts(text):
        clean = clean_text_for_gtts(text)
        if not clean: return
        try:
            tts = gTTS(text=clean, lang='tr')
            aud = io.BytesIO()
            tts.write_to_fp(aud)
            aud.seek(0)
            st.audio(aud, format='audio/mp3')
        except: pass

    @st.cache_resource
    def get_model_name():
        try:
            u = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"
            d = requests.get(u).json()
            for m in d.get("models", []):
                if "generateContent" in m.get("supportedGenerationMethods", []):
                    return m["name"]
            return "models/gemini-pro"
        except: return "models/gemini-pro"

    def ask_ai(hist, msg):
        try:
            mdl = get_model_name()
            url = f"https://generativelanguage.googleapis.com/v1beta/{mdl}:generateContent?key={API_KEY}"
            
            prompt = f"""
            Sen Nikosu'sun. En yakın kız arkadaş gibi samimi, sıcak ve motive edici konuş.
            Kullanıcı hafta içi IF yapıyor, hafta sonu kahvaltı yapıyor.
            Bugün: {curr_day}. Menü: {curr_menu}.
            Sadece Türkçe konuş.
            """
            
            con = [{"role": "user", "parts": [{"text": prompt}]}]
            for h in hist:
                r = "user" if h["role"] == "user" else "model"
                con.append({"role": r, "parts": [{"text": h["content"]}]})
            con.append({"role": "user", "parts": [{"text": msg}]})
            
            res = requests.post(url, headers={'Content-Type':'application/json'}, json={"contents": con})
            if res.status_code == 200: return res.json()['candidates'][0]['content']['parts'][0]['text']
            return "Bağlantıda minik bir sorun var tatlım."
        except: return "İnternetini kontrol eder misin balım?"

    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "model", "content": "Selam balım! Bugün çok güzel bir gün, enerjin nasıl? 🌿"}]

    for m in st.session_state.messages:
        with st.chat_message(m["role"], avatar="🌿" if m["role"] == "model" else None):
            st.write(m["content"])

    if user_in := st.chat_input("Nikosu'ya bir şeyler söyle..."):
        st.session_state.messages.append({"role": "user", "content": user_in})
        with st.chat_message("user"): st.write(user_in)
        
        with st.spinner("Yazıyor..."):
            ai_reply = ask_ai(st.session_state.messages[:-1], user_in)
        
        st.session_state.messages.append({"role": "model", "content": ai_reply})
        with st.chat_message("model", avatar="🌿"):
            st.write(ai_reply)
            if "sorun" not in ai_reply: play_audio_gtts(ai_reply)

# --- TAB 2: YEMEK PLANI ---
with tab_menu:
    col_btn, _ = st.columns([1, 4])
    with col_btn:
        if st.button("🔄 Listeyi Yenile"):
            st.session_state.weekly_menu = create_weekly_menu()
            st.rerun()

    menu = st.session_state.weekly_menu
    days = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
    
    col1, col2 = st.columns(2)
    for i, d in enumerate(days):
        # Hafta sonu rengi farklı
        is_weekend = d in ["Cumartesi", "Pazar"]
        accent = "#d97706" if is_weekend else "#be185d" # Amber vs Pink
        title_text = f"{d} (Hafta Sonu Keyfi)" if is_weekend else d
        
        html_card = f"""
        <div class="menu-card" style="border-left: 5px solid {accent};">
            <h3 style="margin-top:0; color:{accent}; font-size:18px;">{title_text}</h3>
            <div style="margin-top:10px;">
                <p style="margin:5px 0; font-size:14px;"><strong style="color:#555;">Sabah:</strong><br>{menu[d]['Sabah']}</p>
                <p style="margin:5px 0; font-size:14px;"><strong style="color:#555;">Öğle:</strong><br>{menu[d]['Ogle']}</p>
                <p style="margin:5px 0; font-size:14px;"><strong style="color:#555;">Akşam:</strong><br>{menu[d]['Aksam']}</p>
            </div>
        </div>
        """
        if i % 2 == 0: col1.markdown(html_card, unsafe_allow_html=True)
        else: col2.markdown(html_card, unsafe_allow_html=True)

# --- TAB 3: EGZERSİZ ---
with tab_yoga:
    st.markdown("### 🧘‍♀️ Senin İçin Seçtiklerim")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('<div class="menu-card"><h4>🌞 Sabah Akışı</h4><p>Güneş enerjisiyle uyan.</p></div>', unsafe_allow_html=True)
        st.video("https://www.youtube.com/watch?v=inpok4MKVLM")
    with c2:
        st.markdown('<div class="menu-card"><h4>🔥 Yağ Yakımı</h4><p>Metabolizmanı hızlandır.</p></div>', unsafe_allow_html=True)
        st.video("https://www.youtube.com/watch?v=enYITYwvPAQ")
    with c3:
        st.markdown('<div class="menu-card"><h4>🌙 Uyku Öncesi</h4><p>Rahatla ve gevşe.</p></div>', unsafe_allow_html=True)
        st.video("https://www.youtube.com/watch?v=M-805010FjE")
