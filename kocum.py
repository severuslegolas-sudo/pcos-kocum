import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import io
import re
import random
import datetime

# --- AYARLAR ---
if "GOOGLE_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
    # Google Kütüphanesini Kuruyoruz
    genai.configure(api_key=API_KEY)
else:
    st.error("⚠️ Google API Anahtarı bulunamadı!")
    st.stop()

# --- SAYFA AYARLARI ---
st.set_page_config(
    page_title="PCOS Nikosu: Türk Usulü",
    page_icon="🍲",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- TASARIM (SICAK & BİZDEN) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Poppins', sans-serif; }
    
    .stApp { background: linear-gradient(135deg, #fffbf0 0%, #fff0f0 100%); }
    
    .menu-card {
        background-color: white;
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        border-left: 5px solid #c0392b;
    }
    
    h1, h2, h3 { color: #c0392b; } 
    
    .stButton>button {
        background-color: #c0392b;
        color: white;
        border-radius: 25px;
        border: none;
        width: 100%;
    }
    .stButton>button:hover { background-color: #a93226; }
    .streamlit-expanderHeader { color: #922b21; font-weight: 600; }
    #MainMenu, footer, header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- TÜRK USULÜ TARİF HAVUZU ---
TARIFLER = {
    # Kahvaltılar
    "Klasik Türk Kahvaltısı": {"malz": ["2 Haşlanmış Yumurta", "Beyaz Peynir", "Zeytin", "Yeşillik"], "tarif": "Ekmek yok! Çatalla peynir zeytin keyfi."},
    "Menemen": {"malz": ["Domates", "Sivri Biber", "2 Yumurta", "Yağ"], "tarif": "Ekmek banmak yok, kaşıklıyoruz."},
    "Sucuklu Yumurta": {"malz": ["Kangal Sucuk (Az)", "2 Yumurta", "Tereyağı"], "tarif": "Sucukları kurutmadan pişir, yumurtayı kır."},
    "Peynirli Omlet": {"malz": ["2 Yumurta", "Ezine Peyniri", "Maydanoz"], "tarif": "Peyniri bol, ekmeği hiç yok."},
    "Çılbır (Ekmeksiz)": {"malz": ["2 Yumurta", "Sarımsaklı Yoğurt", "Pul Biberli Yağ"], "tarif": "Yumurtaları haşla, üzerine yoğurt dök."},
    "Sahanda Ispanaklı Yumurta": {"malz": ["Ispanak", "Soğan", "2 Yumurta"], "tarif": "Soğan ve ıspanağı kavur, yumurtayı kır."},

    # Yemekler
    "Etli Kuru Fasulye": {"malz": ["Kuru Fasulye", "Kuşbaşı Et", "Soğan", "Salça"], "tarif": "Yanına pilav yasak! Yanına turşu ve ayran serbest."},
    "Etli Nohut Yemeği": {"malz": ["Nohut", "Et", "Soğan", "Salça"], "tarif": "Suyuna ekmek banmak yok. Kaşıkla ye."},
    "Yeşil Mercimek": {"malz": ["Yeşil Mercimek", "Soğan", "Salça"], "tarif": "İçine erişte koyma! Sade mercimek yemeği."},
    "Kıymalı Ispanak": {"malz": ["Ispanak", "Kıyma", "Soğan", "Yoğurt"], "tarif": "Pirinç yerine az bulgur atabilirsin. Yoğurtla ye."},
    "Zeytinyağlı Pırasa": {"malz": ["Pırasa", "Havuç", "Limon", "Zeytinyağı"], "tarif": "Bol limonlu. Pirinci çok az koy."},
    "Karnıyarık (Kızartmasız)": {"malz": ["Patlıcan", "Kıyma", "Soğan", "Biber"], "tarif": "Patlıcanları fırında közle, öyle doldur."},
    "Türlü Yemeği": {"malz": ["Patlıcan", "Fasulye", "Kabak", "Et"], "tarif": "Patates koyma! Kısık ateşte pişir."},
    "Zeytinyağlı Taze Fasulye": {"malz": ["Taze Fasulye", "Domates", "Soğan"], "tarif": "Şeker koyma, domatesin tadı yeter."},
    "Kapuska (Kıymalı)": {"malz": ["Lahana", "Kıyma", "Salça", "Acı Biber"], "tarif": "Bol acılı, kıymalı lahana."},
    "İzmir Köfte (Patatessiz)": {"malz": ["Kıyma", "Biber", "Domates Sos", "Kabak"], "tarif": "Patates yerine iri doğranmış kabak koy."},
    "Hamsi Buğulama": {"malz": ["Hamsi", "Soğan", "Limon", "Maydanoz"], "tarif": "Tepsiye diz, fırına ver. Kızartma yok."},
    "Tavuk Sote": {"malz": ["Tavuk", "Biber", "Domates", "Kekik"], "tarif": "Sebzelerle sotele."},
    "Mercimek Çorbası": {"malz": ["Kırmızı Mercimek", "Soğan", "Havuç"], "tarif": "Un kavurma, patates koyma. Bol limon."},
}

YAN_URUNLER = ["Bol Cacık", "Çoban Salata", "Ev Turşusu", "Söğüş Salatalık", "Ayran", "Gavurdağı Salata"]
SABAH_SIVILARI = ["Türk Kahvesi ☕", "Demleme Çay 🍵", "Limonlu Su 💧", "Maden Suyu 🍋"]
KAHVALTI_SECENEKLERI = ["Klasik Türk Kahvaltısı", "Menemen", "Sucuklu Yumurta", "Peynirli Omlet", "Çılbır", "Sahanda Ispanaklı Yumurta"]
YEMEK_SECENEKLERI = ["Etli Kuru Fasulye", "Etli Nohut Yemeği", "Yeşil Mercimek", "Kıymalı Ispanak", "Zeytinyağlı Pırasa", "Karnıyarık (Kızartmasız)", "Türlü Yemeği", "Zeytinyağlı Taze Fasulye", "Kapuska (Kıymalı)", "İzmir Köfte (Patatessiz)", "Hamsi Buğulama", "Tavuk Sote"]

# --- FONKSİYONLAR ---
def create_turkish_menu():
    days = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
    menu = {}
    random.shuffle(YEMEK_SECENEKLERI)
    
    for i, day in enumerate(days):
        if day in ["Cumartesi", "Pazar"]:
            sabah = random.choice(KAHVALTI_SECENEKLERI)
            sabah_tip = "YEMEK"
        else:
            sabah = f"{random.choice(SABAH_SIVILARI)} (IF)"
            sabah_tip = "SIVI"
            
        ogle = YEMEK_SECENEKLERI[i % len(YEMEK_SECENEKLERI)]
        aksam = YEMEK_SECENEKLERI[(i + 4) % len(YEMEK_SECENEKLERI)]
        
        menu[day] = {
            "Sabah": sabah, "Sabah_Tip": sabah_tip,
            "Ogle": f"{ogle} + {random.choice(YAN_URUNLER)}",
            "Ogle_Ana": ogle,
            "Aksam": f"{aksam} + {random.choice(YAN_URUNLER)}",
            "Aksam_Ana": aksam
        }
    return menu

if "weekly_menu" not in st.session_state: st.session_state.weekly_menu = create_turkish_menu()

def generate_shopping_list(menu):
    shopping_set = set()
    for day, meals in menu.items():
        if meals['Ogle_Ana'] in TARIFLER:
            for item in TARIFLER[meals['Ogle_Ana']]['malz']: shopping_set.add(item)
        if meals['Aksam_Ana'] in TARIFLER:
            for item in TARIFLER[meals['Aksam_Ana']]['malz']: shopping_set.add(item)
        if meals['Sabah_Tip'] == "YEMEK" and meals['Sabah'] in TARIFLER:
             for item in TARIFLER[meals['Sabah']]['malz']: shopping_set.add(item)
    return sorted(list(shopping_set))

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2964/2964514.png", width=80)
    st.title("🇹🇷 Türk Usulü")
    if st.button("🔄 Yeni Liste"): 
        st.session_state.weekly_menu = create_turkish_menu()
        st.rerun()

    day_idx = datetime.datetime.today().weekday()
    days = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
    today_name = days[day_idx]
    today_menu = st.session_state.weekly_menu[today_name]
    
    st.markdown(f"**Bugün: {today_name}**")
    st.info(f"🍳 {today_menu['Sabah']}")
    st.success(f"🍲 {today_menu['Ogle']}")
    st.warning(f"🍽️ {today_menu['Aksam']}")

# --- ANA EKRAN ---
st.title("🥘 PCOS Nikosu: Tencere Yemekleri")
st.caption("Bağlantı sorunu çözüldü! Nikosu hizmetinizde.")

tab1, tab2, tab3, tab4 = st.tabs(["💬 Sohbet", "📅 Haftalık Menü", "🛒 Pazar Listesi", "🧘‍♀️ Spor"])

# --- TAB 1: SOHBET (YENİLENMİŞ & GÜÇLENDİRİLMİŞ AI) ---
with tab1:
    def play_audio_gtts(text):
        clean = re.sub(r'[*_#`]', '', text)
        clean = re.sub(r'http\S+', '', clean)
        clean = re.sub(r'[^a-zA-Z0-9çğıöşüÇĞİÖŞÜ .,!?\-\n]', '', clean).strip()
        if not clean: return
        try:
            tts = gTTS(text=clean, lang='tr')
            aud = io.BytesIO()
            tts.write_to_fp(aud)
            aud.seek(0)
            st.audio(aud, format='audio/mp3')
        except: pass

    # --- YENİ NESİL AI FONKSİYONU (Resmi Kütüphane) ---
    def ask_ai(history, message):
        try:
            # En hızlı ve stabil model: gemini-1.5-flash
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # Sohbet geçmişini Google formatına çevir
            chat_history = []
            # Sistem promptunu başa ekleyelim
            system_prompt = f"""
            Sen Nikosu'sun. Türk usulü beslenen bir yaşam koçusun.
            Kullanıcı "tencere yemekleri" yiyor ama ekmek ve pilav yasak.
            Bugün: {today_name}. Menü: {today_menu}.
            Çok samimi, abla/kardeş gibi konuş.
            """
            chat_history.append({"role": "user", "parts": [system_prompt]})
            chat_history.append({"role": "model", "parts": ["Tamam balım, anlaşıldı! Türk usulü ama sağlıklı devam ediyoruz."]})
            
            for msg in history:
                if msg["role"] == "user":
                    chat_history.append({"role": "user", "parts": [msg["content"]]})
                else:
                    chat_history.append({"role": "model", "parts": [msg["content"]]})
            
            chat = model.start_chat(history=chat_history)
            response = chat.send_message(message)
            return response.text
        except Exception as e:
            return f"Şu an Google biraz yoğun balım, ama ben buradayım! Hata: {str(e)}"

    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "model", "content": "Bağlantımı güçlendirdim geldim balım! 💪 Bugün ne pişiriyoruz?"}]

    for m in st.session_state.messages:
        with st.chat_message(m["role"], avatar="🥘" if m["role"] == "model" else None):
            st.write(m["content"])

    if user_in := st.chat_input("Nikosu'ya yaz..."):
        st.session_state.messages.append({"role": "user", "content": user_in})
        with st.chat_message("user"): st.write(user_in)
        
        with st.spinner("Nikosu cevaplıyor..."):
            ai_reply = ask_ai(st.session_state.messages[:-1], user_in)
        
        st.session_state.messages.append({"role": "model", "content": ai_reply})
        with st.chat_message("model", avatar="🥘"):
            st.write(ai_reply)
            if "Hata" not in ai_reply: play_audio_gtts(ai_reply)

# --- TAB 2: MENÜ ---
with tab2:
    st.header("📅 Türk Usulü Haftalık Plan")
    for d in days:
        with st.expander(f"{d}", expanded=True if d == today_name else False):
            c1, c2, c3 = st.columns(3)
            # Sabah
            sabah = st.session_state.weekly_menu[d]['Sabah']
            c1.markdown(f"**🍳 Sabah:** {sabah}")
            # Öğle
            ogle = st.session_state.weekly_menu[d]['Ogle_Ana']
            c2.markdown(f"**🍲 Öğle:** {st.session_state.weekly_menu[d]['Ogle']}")
            if ogle in TARIFLER: c2.caption(f"📝 {TARIFLER[ogle]['tarif']}")
            # Akşam
            aksam = st.session_state.weekly_menu[d]['Aksam_Ana']
            c3.markdown(f"**🍽️ Akşam:** {st.session_state.weekly_menu[d]['Aksam']}")
            if aksam in TARIFLER: c3.caption(f"📝 {TARIFLER[aksam]['tarif']}")

# --- TAB 3: ALIŞVERİŞ ---
with tab3:
    st.header("🛒 Pazar Listesi")
    shop_list = generate_shopping_list(st.session_state.weekly_menu)
    c1, c2 = st.columns(2)
    for i, item in enumerate(shop_list):
        if i % 2 == 0: c1.checkbox(item, key=f"s_{i}")
        else: c2.checkbox(item, key=f"s_{i}")

# --- TAB 4: SPOR ---
with tab4:
    st.header("🧘‍♀️ Evde Hareket")
    st.video("https://www.youtube.com/watch?v=enYITYwvPAQ")
