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
    
    /* Arka Plan: Sıcak Krem/Bej Tonları */
    .stApp { background: linear-gradient(135deg, #fffbf0 0%, #fff0f0 100%); }
    
    .menu-card {
        background-color: white;
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        border-left: 5px solid #c0392b; /* Türk Kırmızısı */
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
    
    /* Tarif Kutusu Başlıkları */
    .streamlit-expanderHeader { color: #922b21; font-weight: 600; }

    #MainMenu, footer, header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- TÜRK USULÜ TARİF HAVUZU (GLUTENSİZ & DÜŞÜK GI) ---
TARIFLER = {
    # --- KAHVALTILAR (Bizim Usul) ---
    "Klasik Türk Kahvaltısı": {"malz": ["2 Haşlanmış Yumurta", "Beyaz Peynir", "7-8 Zeytin", "Salatalık/Domates", "Yeşillik"], "tarif": "Ekmek yok! Çatalla peynir zeytin keyfi."},
    "Menemen": {"malz": ["Domates", "Sivri Biber", "2 Yumurta", "Tereyağı/Zeytinyağı"], "tarif": "Soğanlı/Soğansız keyfine göre. Ekmek banmak yok, kaşıklıyoruz."},
    "Sucuklu Yumurta": {"malz": ["Kangal Sucuk (Az)", "2 Yumurta", "Tereyağı"], "tarif": "Sucukları kurutmadan pişir, yumurtayı kır. Yanına bol maydanoz."},
    "Peynirli Omlet": {"malz": ["2 Yumurta", "Ezine Peyniri", "Maydanoz", "Tereyağı"], "tarif": "Peyniri bol, ekmeği hiç yok. Tam bir protein deposu."},
    "Çılbır (Ekmeksiz)": {"malz": ["2 Yumurta", "Sarımsaklı Yoğurt", "Pul Biberli Yağ"], "tarif": "Yumurtaları suda poşe et (veya kayısı haşla), üzerine sarımsaklı yoğurt ve kızgın yağ dök."},
    "Sahanda Ispanaklı Yumurta": {"malz": ["Ispanak", "Soğan", "2 Yumurta", "Salça"], "tarif": "Soğan ve ıspanağı kavur, yuvalar açıp yumurtayı kır."},

    # --- TENCERE YEMEKLERİ (Öğle/Akşam) ---
    "Etli Kuru Fasulye": {"malz": ["Kuru Fasulye", "Kuşbaşı Et", "Soğan", "Salça", "Tereyağı"], "tarif": "Klasik usul, düdüklüde pişir. DİKKAT: Yanına pilav yasak! Yanına turşu ve ayran serbest."},
    "Etli Nohut Yemeği": {"malz": ["Nohut", "Kuşbaşı Et/Kemikli Et", "Soğan", "Salça"], "tarif": "Bol etli, salçalı. Suyuna ekmek banmak yok. Kaşıkla ye."},
    "Yeşil Mercimek (Kara Şimşek)": {"malz": ["Yeşil Mercimek", "Soğan", "Salça", "Erişte YOK"], "tarif": "İçine erişte koyma! Sade mercimek yemeği. Yanına yoğurt çok yakışır."},
    "Kıymalı Ispanak": {"malz": ["Ispanak", "Kıyma", "Soğan", "Salça", "Yoğurt"], "tarif": "Pirinç yerine çok az bulgur atabilirsin veya hiç atma. Üzerine sarımsaklı yoğurt."},
    "Zeytinyağlı Pırasa": {"malz": ["Pırasa", "Havuç", "Limon", "Zeytinyağı", "Az Pirinç"], "tarif": "Bol limonlu, havuçlu. Pirinci sadece 'tane tane' görünecek kadar az koy."},
    "Karnıyarık (Kızartmasız)": {"malz": ["Patlıcan", "Kıyma", "Soğan", "Biber", "Domates"], "tarif": "Patlıcanları yağda kızartma! Fırında közle veya üzerine yağ sürüp fırınla. Sonra içini doldur."},
    "Türlü Yemeği": {"malz": ["Patlıcan", "Fasulye", "Kabak", "Biber", "Kuşbaşı Et/Tavuk"], "tarif": "Mevsimde ne varsa tencereye at, kısık ateşte pişir. Patates koyma!"},
    "Zeytinyağlı Taze Fasulye": {"malz": ["Taze Fasulye", "Domates", "Soğan", "Zeytinyağı"], "tarif": "Ayşe kadın fasulye. Şeker koyma, domatesin tadı yeter."},
    "Kapuska (Kıymalı)": {"malz": ["Lahana", "Kıyma", "Salça", "Pul Biber"], "tarif": "Bol acılı, kıymalı lahana yemeği. Metabolizmayı fişekler."},
    "İzmir Köfte (Patatessiz)": {"malz": ["Kıyma", "Biber", "Domates Sos", "Kabak/Havuç"], "tarif": "Patates yerine iri doğranmış kabak veya havuç koy. Köfteleri fırınla."},
    "Hamsi Buğulama": {"malz": ["Hamsi", "Soğan", "Limon", "Maydanoz"], "tarif": "Tepsiye diz, fırına ver. Kızartma yağı yok, koku yok."},
    "Tavuk Sote": {"malz": ["Tavuk Göğsü/But", "Yeşil Biber", "Domates", "Kekik"], "tarif": "Sac tavada veya tencerede sebzelerle sotele."},
    "Mercimek Çorbası": {"malz": ["Kırmızı Mercimek", "Soğan", "Havuç"], "tarif": "Un kavurmadan yap! Patates koyma. Blenderdan geçir, bol limon sık."},
    "Yayla Çorbası (Buğdaysız)": {"malz": ["Yoğurt", "Yumurta", "Nane", "Haşlanmış Karabuğday/Kinoa"], "tarif": "Pirinç yerine karabuğday kullan veya sadece yoğurtlu yap."},
}

# --- YAN ÜRÜNLER (Salata/Meze) ---
YAN_URUNLER = ["Bol Cacık", "Çoban Salata", "Ev Turşusu", "Söğüş Salatalık", "Ayran", "Gavurdağı Salata (Nar ekşili)"]

# --- LİSTELER ---
SABAH_SIVILARI = ["Türk Kahvesi ☕", "Demleme Çay 🍵", "Limonlu Su 💧", "Maden Suyu 🍋"]
KAHVALTI_SECENEKLERI = ["Klasik Türk Kahvaltısı", "Menemen", "Sucuklu Yumurta", "Peynirli Omlet", "Çılbır (Ekmeksiz)", "Sahanda Ispanaklı Yumurta"]
YEMEK_SECENEKLERI = ["Etli Kuru Fasulye", "Etli Nohut Yemeği", "Yeşil Mercimek (Kara Şimşek)", "Kıymalı Ispanak", "Zeytinyağlı Pırasa", "Karnıyarık (Kızartmasız)", "Türlü Yemeği", "Zeytinyağlı Taze Fasulye", "Kapuska (Kıymalı)", "İzmir Köfte (Patatessiz)", "Hamsi Buğulama", "Tavuk Sote"]

# --- FONKSİYONLAR ---
def create_turkish_menu():
    days = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
    menu = {}
    
    # Yemek havuzunu karıştır
    random.shuffle(YEMEK_SECENEKLERI)
    
    for i, day in enumerate(days):
        # Hafta sonu kahvaltı var
        if day in ["Cumartesi", "Pazar"]:
            sabah = random.choice(KAHVALTI_SECENEKLERI)
            sabah_tip = "YEMEK"
        else:
            sabah = f"{random.choice(SABAH_SIVILARI)} (IF)"
            sabah_tip = "SIVI"
            
        # Öğle ve Akşam farklı olsun
        ogle = YEMEK_SECENEKLERI[i % len(YEMEK_SECENEKLERI)]
        aksam = YEMEK_SECENEKLERI[(i + 4) % len(YEMEK_SECENEKLERI)] # Farklı bir yemek seç
        
        yan_urun_ogle = random.choice(YAN_URUNLER)
        yan_urun_aksam = random.choice(YAN_URUNLER)

        menu[day] = {
            "Sabah": sabah, "Sabah_Tip": sabah_tip,
            "Ogle": f"{ogle} + {yan_urun_ogle}",
            "Ogle_Ana": ogle, # Tarif çekmek için saf isim
            "Aksam": f"{aksam} + {yan_urun_aksam}",
            "Aksam_Ana": aksam # Tarif çekmek için saf isim
        }
    return menu

if "current_week_num" not in st.session_state: st.session_state.current_week_num = 1
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
    
    # Butonlar
    c1, c2 = st.columns(2)
    with c1:
        if st.button("⬅️ Önceki"): 
            st.session_state.weekly_menu = create_turkish_menu()
            st.rerun()
    with c2:
        if st.button("Sonraki ➡️"): 
            st.session_state.weekly_menu = create_turkish_menu()
            st.rerun()

    # Bugün
    day_idx = datetime.datetime.today().weekday()
    days = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
    today_name = days[day_idx]
    today_menu = st.session_state.weekly_menu[today_name]
    
    st.markdown("---")
    st.markdown(f"**Bugün: {today_name}**")
    st.info(f"🍳 {today_menu['Sabah']}")
    st.success(f"🍲 {today_menu['Ogle']}")
    st.warning(f"🍽️ {today_menu['Aksam']}")

# --- ANA EKRAN ---
st.title("🥘 PCOS Nikosu: Tencere Yemekleri")
st.caption("Ekmeksiz, Pirinçsiz, Hakiki Anne Yemekleri.")

# --- TABLAR ---
tab1, tab2, tab3, tab4 = st.tabs(["💬 Sohbet", "📅 Haftalık Menü", "🛒 Pazar Listesi", "🧘‍♀️ Spor"])

# --- TAB 1: SOHBET ---
with tab1:
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
            Sen Nikosu'sun. Türk usulü beslenen bir yaşam koçusun.
            Kullanıcı "tencere yemekleri" yiyor ama ekmek ve pilav yasak.
            Bugün: {today_name}. Menü: {today_menu}.
            Motivasyon ver. "Ekmek yoksa kaşık var!" de.
            """
            con = [{"role": "user", "parts": [{"text": prompt}]}]
            for h in hist:
                r = "user" if h["role"] == "user" else "model"
                con.append({"role": r, "parts": [{"text": h["content"]}]})
            con.append({"role": "user", "parts": [{"text": msg}]})
            res = requests.post(url, headers={'Content-Type':'application/json'}, json={"contents": con})
            if res.status_code == 200: return res.json()['candidates'][0]['content']['parts'][0]['text']
            return "Bağlantı koptu balım."
        except: return "İnternetini kontrol et kuzum."

    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "model", "content": "Oh mis gibi kokular geliyor! Kuru fasulye, ıspanak... Ama ekmek banmak yok, anlaştık mı? 😉"}]

    for m in st.session_state.messages:
        with st.chat_message(m["role"], avatar="🥘" if m["role"] == "model" else None):
            st.write(m["content"])

    if user_in := st.chat_input("Nikosu'ya yaz..."):
        st.session_state.messages.append({"role": "user", "content": user_in})
        with st.chat_message("user"): st.write(user_in)
        with st.spinner("..."):
            ai_reply = ask_ai(st.session_state.messages[:-1], user_in)
        st.session_state.messages.append({"role": "model", "content": ai_reply})
        with st.chat_message("model", avatar="🥘"):
            st.write(ai_reply)
            if "sorun" not in ai_reply: play_audio_gtts(ai_reply)

# --- TAB 2: MENÜ ---
with tab2:
    col_head, col_btn = st.columns([3, 1])
    with col_head: st.header("📅 Türk Usulü Haftalık Plan")
    with col_btn:
        if st.button("🔄 Menüyü Karıştır"):
            st.session_state.weekly_menu = create_turkish_menu()
            st.rerun()

    menu = st.session_state.weekly_menu
    for d in days:
        with st.expander(f"{d}", expanded=True if d == today_name else False):
            c1, c2, c3 = st.columns(3)
            
            # Sabah
            sabah = menu[d]['Sabah']
            c1.markdown(f"**🍳 Sabah:** {sabah}")
            if menu[d]['Sabah_Tip'] == "YEMEK" and sabah in TARIFLER:
                c1.caption(f"📝 {TARIFLER[sabah]['tarif']}")
            
            # Öğle
            ogle = menu[d]['Ogle_Ana']
            c2.markdown(f"**🍲 Öğle:** {menu[d]['Ogle']}")
            if ogle in TARIFLER:
                c2.caption(f"📝 {TARIFLER[ogle]['tarif']}")
            
            # Akşam
            aksam = menu[d]['Aksam_Ana']
            c3.markdown(f"**🍽️ Akşam:** {menu[d]['Aksam']}")
            if aksam in TARIFLER:
                c3.caption(f"📝 {TARIFLER[aksam]['tarif']}")

# --- TAB 3: ALIŞVERİŞ ---
with tab3:
    st.header("🛒 Pazar Listesi")
    st.write("Evin bereketi eksik olmasın. Bu hafta lazım olanlar:")
    shop_list = generate_shopping_list(st.session_state.weekly_menu)
    
    c1, c2 = st.columns(2)
    for i, item in enumerate(shop_list):
        if i % 2 == 0: c1.checkbox(item, key=f"s_{i}")
        else: c2.checkbox(item, key=f"s_{i}")

# --- TAB 4: SPOR ---
with tab4:
    st.header("🧘‍♀️ Evde Hareket")
    st.video("https://www.youtube.com/watch?v=enYITYwvPAQ")
