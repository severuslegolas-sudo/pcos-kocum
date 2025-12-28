import streamlit as st
import requests
from gtts import gTTS
import io
import re
import datetime

# --- AYARLAR ---
if "GOOGLE_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    st.error("⚠️ Google API Anahtarı bulunamadı!")
    st.stop()

# --- SAYFA AYARLARI ---
st.set_page_config(
    page_title="PCOS Nikosu Pro",
    page_icon="🥑",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- TASARIM (CLEAN HEALTHY AESTHETIC) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Poppins', sans-serif; }
    
    /* Arka Plan: Sağlıklı Yeşil/Beyaz */
    .stApp { background: linear-gradient(135deg, #f0fff4 0%, #e6fffa 100%); }
    
    .menu-card {
        background-color: white;
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        border-left: 5px solid #059669;
    }
    
    h1, h2, h3 { color: #047857; } 
    
    .stButton>button {
        background-color: #059669;
        color: white;
        border-radius: 25px;
        width: 100%;
        border: none;
    }
    .stButton>button:hover { background-color: #064e3b; }
    
    .week-badge {
        background-color: #d1fae5;
        color: #065f46;
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
        margin-bottom: 10px;
    }

    #MainMenu, footer, header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- 1 AYLIK SABİT LİSTE (LOW GI & GLUTENSİZ) ---
AYLIK_PLAN = {
    1: { # 1. HAFTA: Ödem Atma & Arınma
        "Title": "1. Hafta: Ödem Atma & Arınma 🌿",
        "Menu": {
            "Pazartesi": {"Sabah": "Sirkeli Su + Yeşil Çay", "Sabah_Tip": "SIVI", "Ogle": "Kabak Detoksu (Yoğurtlu)", "Aksam": "Izgara Tavuk + Bol Yeşillik"},
            "Salı":      {"Sabah": "Sade Kahve + 2 Ceviz", "Sabah_Tip": "SIVI", "Ogle": "Yeşil Mercimek Salatası", "Aksam": "Zeytinyağlı Brokoli"},
            "Çarşamba":  {"Sabah": "Kiraz Sapı Çayı", "Sabah_Tip": "SIVI", "Ogle": "Ton Balıklı Salata (Mısırsız)", "Aksam": "Fırın Sebze (Patatessiz)"},
            "Perşembe":  {"Sabah": "Limonlu Su", "Sabah_Tip": "SIVI", "Ogle": "Haşlanmış Yumurta + Avokado", "Aksam": "Ispanak Yemeği (Pirinçsiz)"},
            "Cuma":      {"Sabah": "Türk Kahvesi", "Sabah_Tip": "SIVI", "Ogle": "Kinoalı Mevsim Salatası", "Aksam": "Izgara Köfte + Roka"},
            "Cumartesi": {"Sabah": "Glutensiz Omlet + 5 Zeytin", "Sabah_Tip": "YEMEK", "Ogle": "Zeytinyağlı Enginar", "Aksam": "Fırın Balık (Levrek/Somon)"},
            "Pazar":     {"Sabah": "Menemen (Ekmeksiz) + Ceviz", "Sabah_Tip": "YEMEK", "Ogle": "Ayran Aşı Çorbası (Buğdaysız)", "Aksam": "Mantar Sote"}
        }
    },
    2: { # 2. HAFTA: Protein Artışı & Yağ Yakımı
        "Title": "2. Hafta: Protein & Yağ Yakımı 🔥",
        "Menu": {
            "Pazartesi": {"Sabah": "Sirkeli Su", "Sabah_Tip": "SIVI", "Ogle": "Izgara Tavuklu Salata", "Aksam": "Zeytinyağlı Taze Fasulye"},
            "Salı":      {"Sabah": "Yeşil Çay", "Sabah_Tip": "SIVI", "Ogle": "3 Yumurtalı Omlet (Sebzeli)", "Aksam": "Kıymalı Kabak Sote"},
            "Çarşamba":  {"Sabah": "Sade Kahve", "Sabah_Tip": "SIVI", "Ogle": "Nohutlu Roka Salatası", "Aksam": "Fırın Mücver (Unsuz)"},
            "Perşembe":  {"Sabah": "Limonlu Su", "Sabah_Tip": "SIVI", "Ogle": "Ton Balığı + Haşlanmış Brokoli", "Aksam": "Pazı Kavurma (Yumurtalı)"},
            "Cuma":      {"Sabah": "Türk Kahvesi", "Sabah_Tip": "SIVI", "Ogle": "Karabuğday Pilavı + Yoğurt", "Aksam": "Hindi Füme Söğüş Tabağı"},
            "Cumartesi": {"Sabah": "Sahanda Yumurta + Avokado", "Sabah_Tip": "YEMEK", "Ogle": "Semizotu Salatası", "Aksam": "Izgara Çipura + Salata"},
            "Pazar":     {"Sabah": "Peynirli Maydanozlu Omlet", "Sabah_Tip": "YEMEK", "Ogle": "Köz Patlıcan Salatası", "Aksam": "Etli Bamya"}
        }
    },
    3: { # 3. HAFTA: Düşük Karbonhidrat & Ketojenik Etki
        "Title": "3. Hafta: İnatçı Kiloları Kırma 🔨",
        "Menu": {
            "Pazartesi": {"Sabah": "Sirkeli Su", "Sabah_Tip": "SIVI", "Ogle": "Kabak Spagetti (Yoğurtlu)", "Aksam": "Fırın Tavuk Baget"},
            "Salı":      {"Sabah": "Yeşil Çay", "Sabah_Tip": "SIVI", "Ogle": "Lor Peynirli Salata", "Aksam": "Karnabahar Graten (Unsuz)"},
            "Çarşamba":  {"Sabah": "Sade Kahve", "Sabah_Tip": "SIVI", "Ogle": "Menemen + Salatalık", "Aksam": "Zeytinyağlı Pırasa (Havuca dikkat)"},
            "Perşembe":  {"Sabah": "Limonlu Su", "Sabah_Tip": "SIVI", "Ogle": "Haşlanmış Yumurta + Ceviz", "Aksam": "Izgara Köfte + Köz Biber"},
            "Cuma":      {"Sabah": "Türk Kahvesi", "Sabah_Tip": "SIVI", "Ogle": "Ton Balıklı Marul Dürüm", "Aksam": "Mantar Sote"},
            "Cumartesi": {"Sabah": "Avokado Ezmesi + Haşlanmış Yumurta", "Sabah_Tip": "YEMEK", "Ogle": "Yeşil Mercimek Yemeği", "Aksam": "Fırın Somon"},
            "Pazar":     {"Sabah": "Otlu Peynirli Omlet", "Sabah_Tip": "YEMEK", "Ogle": "Cacık + Ceviz", "Aksam": "Şevketi Bostan"}
        }
    },
    4: { # 4. HAFTA: Denge & Koruma
        "Title": "4. Hafta: Yeni Sen, Yeni Düzen ✨",
        "Menu": {
            "Pazartesi": {"Sabah": "Sirkeli Su", "Sabah_Tip": "SIVI", "Ogle": "Kinoalı Kısır (Bol yeşillik)", "Aksam": "Izgara Tavuk"},
            "Salı":      {"Sabah": "Yeşil Çay", "Sabah_Tip": "SIVI", "Ogle": "Zeytinyağlı Barbunya (Az)", "Aksam": "Ispanaklı Yumurta"},
            "Çarşamba":  {"Sabah": "Sade Kahve", "Sabah_Tip": "SIVI", "Ogle": "Mevsim Salatası + Peynir", "Aksam": "Hamsi Buğulama (Ekmeksiz)"},
            "Perşembe":  {"Sabah": "Limonlu Su", "Sabah_Tip": "SIVI", "Ogle": "Kabak Sıyırma", "Aksam": "Kıymalı Yeşil Mercimek"},
            "Cuma":      {"Sabah": "Türk Kahvesi", "Sabah_Tip": "SIVI", "Ogle": "Omlet Dürüm (Yeşillikli)", "Aksam": "Fırın Karnabahar"},
            "Cumartesi": {"Sabah": "Yulaflı Muzlu Pankek (Şekersiz)", "Sabah_Tip": "YEMEK", "Ogle": "Enginar Kalbi", "Aksam": "Izgara Et + Salata"},
            "Pazar":     {"Sabah": "Krallar Gibi Ege Kahvaltısı", "Sabah_Tip": "YEMEK", "Ogle": "Yoğurtlu Semizotu", "Aksam": "Zeytinyağlı Karışık Sebze"}
        }
    }
}

# --- TARİF DETAYLARI (GLUTENSİZ & LOW GI) ---
TARIFLER = {
    "Kabak Detoksu (Yoğurtlu)": {"malz": ["2 Kabak", "3 kaşık Yoğurt", "Dereotu", "Ceviz", "Sarımsak"], "tarif": "Kabakları rendele, yağsız tavada suyunu çekene kadar sotele. Soğuyunca sarımsaklı yoğurt, dereotu ve cevizle karıştır."},
    "Fırın Mücver (Unsuz)": {"malz": ["2 Kabak", "1 Havuç", "2 Yumurta", "Dereotu", "Beyaz Peynir", "1 kaşık Zeytinyağı"], "tarif": "Sebzeleri rendele suyunu sık. Yumurta, peynir ve otlarla karıştır. Yağlı kağıda kaşıkla dök. Fırında kızarana kadar pişir."},
    "Kabak Spagetti (Yoğurtlu)": {"malz": ["2 Kabak", "Sarımsaklı Yoğurt", "Pul Biber", "Ceviz"], "tarif": "Kabakları soyacakla spagetti gibi uzun uzun kes. Kaynar suda 2 dk haşla (çok erimesin). Üzerine yoğurt dök."},
    "Karabuğday Pilavı": {"malz": ["1 bardak Karabuğday", "1 Soğan", "1 Biber", "Domates", "Zeytinyağı"], "tarif": "Soğan ve biberi kavur. Yıkanmış karabuğdayı ekle. 2 bardak sıcak su koy. Suyunu çekene kadar pişir. (Bulgurdan çok daha sağlıklıdır)."},
    "Karnabahar Graten (Unsuz)": {"malz": ["Karnabahar", "Yumurta", "Yoğurt", "Kaşar Peyniri"], "tarif": "Karnabaharı haşla. Yumurta ve yoğurdu çırpıp üzerine dök. En üste kaşar serp fırına ver."},
    "Hamsi Buğulama (Ekmeksiz)": {"malz": ["Hamsi", "Soğan", "Limon", "Maydanoz"], "tarif": "Tepsiye soğan halkalarını diz. Üzerine hamsileri diz. En üste limon dilimleri. Fırına ver."},
    "Kinoalı Kısır": {"malz": ["Haşlanmış Kinoa", "Salça", "Bol Yeşillik", "Limon", "Nar Ekşisi"], "tarif": "Bulgur yerine haşlanmış kinoa kullan. Salçalı sos ve yeşilliklerle karıştır. Şişkinlik yapmaz."},
    "Avokado Ezmesi": {"malz": ["Yarım Avokado", "Limon", "Tuz", "Pul Biber", "Haşlanmış Yumurta"], "tarif": "Avokadoyu çatalla ez, baharatla tatlandır. Yanına yumurta ile tüket."},
    "Menemen (Ekmeksiz)": {"malz": ["Domates", "Biber", "Yumurta", "Zeytinyağı"], "tarif": "Bol domatesli biberli yap, ekmek banmak yerine çatalla ye."}
}

# --- STATE YÖNETİMİ ---
if "current_week" not in st.session_state:
    st.session_state.current_week = 1

def next_week():
    if st.session_state.current_week < 4:
        st.session_state.current_week += 1
    else:
        st.session_state.current_week = 1 # Başa dön

def prev_week():
    if st.session_state.current_week > 1:
        st.session_state.current_week -= 1

def get_current_menu_data():
    week_num = st.session_state.current_week
    return AYLIK_PLAN[week_num]

def get_todays_details(menu_data):
    days = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
    day_idx = datetime.datetime.today().weekday()
    today_name = days[day_idx]
    return today_name, menu_data["Menu"][today_name]

# --- FONKSİYONLAR (ALISVERIS & AI) ---
def generate_shopping_list(menu_data):
    shopping_set = set()
    menu = menu_data["Menu"]
    for day, meals in menu.items():
        # Sadece tarif veritabanında olanların malzemelerini çek
        if meals.get('Ogle') in TARIFLER:
            for item in TARIFLER[meals['Ogle']]['malz']: shopping_set.add(item)
        if meals.get('Aksam') in TARIFLER:
            for item in TARIFLER[meals['Aksam']]['malz']: shopping_set.add(item)
        if meals.get('Sabah_Tip') == "YEMEK" and meals.get('Sabah') in TARIFLER:
             for item in TARIFLER[meals['Sabah']]['malz']: shopping_set.add(item)
    return sorted(list(shopping_set))

# --- SIDEBAR (DURUM PANELİ) ---
curr_week_data = get_current_menu_data()
today_name, today_menu = get_todays_details(curr_week_data)

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2964/2964514.png", width=80)
    st.markdown(f"### {curr_week_data['Title']}")
    st.progress(st.session_state.current_week / 4)
    
    st.markdown(f"**Bugün: {today_name}**")
    st.info(f"🍳 {today_menu['Sabah']}")
    st.success(f"🥗 {today_menu['Ogle']}")
    st.warning(f"🍽️ {today_menu['Aksam']}")
    
    st.write("---")
    c1, c2 = st.columns(2)
    with c1: 
        if st.button("⬅️ Önceki"): prev_week(); st.rerun()
    with c2: 
        if st.button("Sonraki ➡️"): next_week(); st.rerun()

# --- ANA SAYFA ---
st.title("🥑 PCOS Nikosu: GL & Gluten Kontrolü")
st.caption("İnsülin direncini kıran, ödem atan 'Fabrika Ayarları' listesi.")

# --- TABLAR ---
tab1, tab2, tab3, tab4 = st.tabs(["💬 Koçunla Konuş", "📅 Haftalık Plan", "🛒 Alışveriş", "🧘‍♀️ Spor"])

# --- TAB 1: SOHBET (AI) ---
with tab1:
    # ... (Ses ve AI kodları standart, sadece promptu özelleştiriyoruz)
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
                if "generateContent" in m.get("supportedGenerationMethods", []): return m["name"]
            return "models/gemini-pro"
        except: return "models/gemini-pro"

    def ask_ai(hist, msg):
        try:
            mdl = get_model_name()
            url = f"https://generativelanguage.googleapis.com/v1beta/{mdl}:generateContent?key={API_KEY}"
            
            prompt = f"""
            Sen Nikosu'sun. Çok sıkı, disiplinli ama sevgi dolu bir yaşam koçusun.
            Kullanıcı "Fabrika Ayarlarına" döndü.
            Şu an {st.session_state.current_week}. Haftadayız: {curr_week_data['Title']}.
            Bugünün menüsü: {today_menu}.
            Konumuz: Düşük Glisemik İndeks, Glutensiz Beslenme, İnsülin Direnci.
            ASLA ekmek, şeker, pirinç önerme. Alternatif olarak kinoa, karabuğday öner.
            """
            
            con = [{"role": "user", "parts": [{"text": prompt}]}]
            for h in hist:
                r = "user" if h["role"] == "user" else "model"
                con.append({"role": r, "parts": [{"text": h["content"]}]})
            con.append({"role": "user", "parts": [{"text": msg}]})
            
            res = requests.post(url, headers={'Content-Type':'application/json'}, json={"contents": con})
            if res.status_code == 200: return res.json()['candidates'][0]['content']['parts'][0]['text']
            return "Bağlantıda sorun var balım."
        except: return "İnternetini kontrol et kuzum."

    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "model", "content": "Harika karar balım! Eski sıkı düzene döndük. Bu hafta ödemleri atıyoruz, kaçamak yok tamam mı? 💪"}]

    for m in st.session_state.messages:
        with st.chat_message(m["role"], avatar="🥑" if m["role"] == "model" else None):
            st.write(m["content"])

    if user_in := st.chat_input("Nikosu'ya yaz..."):
        st.session_state.messages.append({"role": "user", "content": user_in})
        with st.chat_message("user"): st.write(user_in)
        with st.spinner("..."):
            ai_reply = ask_ai(st.session_state.messages[:-1], user_in)
        st.session_state.messages.append({"role": "model", "content": ai_reply})
        with st.chat_message("model", avatar="🥑"):
            st.write(ai_reply)
            if "sorun" not in ai_reply: play_audio_gtts(ai_reply)

# --- TAB 2: HAFTALIK PLAN ---
with tab2:
    st.header(f"📅 {curr_week_data['Title']}")
    st.write("Bu listenin dışına çıkmak yok! Ekmek yok, şeker yok.")
    
    days = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
    menu = curr_week_data["Menu"]
    
    for d in days:
        is_weekend = d in ["Cumartesi", "Pazar"]
        color = "#d97706" if is_weekend else "#059669"
        
        with st.expander(f"{d} Menüsü", expanded=True if d == today_name else False):
            c1, c2, c3 = st.columns(3)
            # Sabah
            sabah = menu[d]['Sabah']
            c1.markdown(f"**🍳 Sabah:** {sabah}")
            if menu[d]['Sabah_Tip'] == "YEMEK" and sabah in TARIFLER:
                c1.caption(f"📝 {TARIFLER[sabah]['tarif']}")
            
            # Öğle
            ogle = menu[d]['Ogle']
            c2.markdown(f"**🥗 Öğle:** {ogle}")
            if ogle in TARIFLER:
                c2.caption(f"📝 {TARIFLER[ogle]['tarif']}")
            
            # Akşam
            aksam = menu[d]['Aksam']
            c3.markdown(f"**🍽️ Akşam:** {aksam}")
            if aksam in TARIFLER:
                c3.caption(f"📝 {TARIFLER[aksam]['tarif']}")

# --- TAB 3: ALIŞVERİŞ ---
with tab3:
    st.header(f"🛒 {st.session_state.current_week}. Hafta Alışveriş Listesi")
    st.write("Bu hafta ihtiyacın olan her şey burada. Glutensiz ve sağlıklı!")
    
    shop_list = generate_shopping_list(curr_week_data)
    
    if not shop_list:
        st.info("Bu haftaki özel tariflerin malzemeleri listeleniyor... (Tarif veritabanındaki yemeklere göre)")
    
    c1, c2 = st.columns(2)
    for i, item in enumerate(shop_list):
        if i % 2 == 0: c1.checkbox(item, key=f"s_{i}")
        else: c2.checkbox(item, key=f"s_{i}")

# --- TAB 4: SPOR ---
with tab4:
    st.header("🧘‍♀️ İnsülin Direnci İçin Egzersiz")
    st.write("Yemekten 1 saat sonra mutlaka yapıyoruz!")
    c1, c2 = st.columns(2)
    with c1:
        st.video("https://www.youtube.com/watch?v=enYITYwvPAQ") # Leslie
        st.caption("Evde Yürüyüş (Mutlaka her gün)")
    with c2:
        st.video("https://www.youtube.com/watch?v=inpok4MKVLM") # Yoga
        st.caption("PCOS Yogası")
