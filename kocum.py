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
    page_title="PCOS Nikosu Pro",
    page_icon="🥑",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- TASARIM ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Poppins', sans-serif; }
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
        border: none;
        width: 100%;
    }
    .stButton>button:hover { background-color: #064e3b; }
    #MainMenu, footer, header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- TARİF VE YEMEK HAVUZU (Hepsi Low GI & Glutensiz) ---
TARIFLER = {
    # Kahvaltılar
    "Kabak Detoksu (Yoğurtlu)": {"malz": ["2 Kabak", "Yoğurt", "Dereotu", "Ceviz"], "tarif": "Kabakları rendele sotele. Soğuyunca dereotlu cevizli yoğurtla karıştır."},
    "Glutensiz Omlet": {"malz": ["2 Yumurta", "Lor Peyniri", "Maydanoz", "Kapya Biber"], "tarif": "Sebzeleri ince doğra, yumurtayla çırp pişir."},
    "Avokado & Yumurta": {"malz": ["Yarım Avokado", "2 Haşlanmış Yumurta", "Limon", "Pul Biber"], "tarif": "Avokadoyu ez, baharatla tatlandır. Yanına yumurta."},
    "Menemen (Ekmeksiz)": {"malz": ["Domates", "Biber", "Yumurta", "Zeytinyağı"], "tarif": "Bol domatesli biberli yap, ekmek banma, kaşıkla ye."},
    "Yulaflı Pankek (Şekersiz)": {"malz": ["Yulaf Ezmesi", "1 Muz", "1 Yumurta", "Tarçın"], "tarif": "Hepsini blenderdan geçir. Az yağlı tavada arkalı önlü pişir."},
    "Peynirli Maydanozlu Omlet": {"malz": ["2 Yumurta", "Beyaz Peynir", "Maydanoz"], "tarif": "Klasik, tok tutan protein kaynağı."},

    # Öğle (Hafif & Sebze Ağırlıklı)
    "Yeşil Mercimek Salatası": {"malz": ["Haşlanmış Mercimek", "Köz Biber", "Dereotu", "Limon"], "tarif": "Yeşilliklerle karıştır, bol limon sık."},
    "Ton Balıklı Salata": {"malz": ["Ton Balığı", "Marul", "Roka", "Salatalık", "Limon"], "tarif": "Yağını süz, bol yeşillikle karıştır (Mısır koyma)."},
    "Kabak Spagetti": {"malz": ["2 Kabak", "Sarımsaklı Yoğurt", "Ceviz", "Pul Biber"], "tarif": "Kabakları soyacakla şerit yap, hafif haşla, yoğurtla."},
    "Zeytinyağlı Enginar": {"malz": ["Enginar", "Bezelye/Havuç (Az)", "Portakal Suyu", "Zeytinyağı"], "tarif": "Klasik zeytinyağlı usulü pişir."},
    "Kinoalı Kısır": {"malz": ["Haşlanmış Kinoa", "Salça", "Yeşillik", "Nar Ekşisi"], "tarif": "Bulgur yerine kinoa kullan. Şişkinlik yapmaz."},
    "Semizotu Salatası": {"malz": ["Semizotu", "Yoğurt", "Sarımsak", "Ketentohumu"], "tarif": "Çiğ semizotunu yoğurtla karıştır."},
    "Mantar Sote": {"malz": ["Mantar", "Biber", "Soğan", "Baharat"], "tarif": "Suyunu salıp çekene kadar sotele."},

    # Akşam (Protein & Sebze)
    "Izgara Tavuk & Yeşillik": {"malz": ["Tavuk Göğsü", "Kekik", "Roka", "Limon"], "tarif": "Tavuğu baharatla ızgara yap. Yanına bol salata."},
    "Fırın Somon": {"malz": ["Somon Dilim", "Kuşkonmaz/Brokoli", "Limon"], "tarif": "Yağlı kağıtta sebzelerle fırınla."},
    "Zeytinyağlı Brokoli": {"malz": ["Brokoli", "Sarımsak", "Zeytinyağı", "Limon"], "tarif": "Hafif haşla, zeytinyağı ve limon sosuyla ılık ye."},
    "Fırın Mücver (Unsuz)": {"malz": ["Kabak", "Yumurta", "Peynir", "Dereotu"], "tarif": "Rendele, karıştır, tepsiye dök fırınla."},
    "Şevketi Bostan": {"malz": ["Şevketi Bostan", "Kuzu eti (az)", "Terbiye için limon"], "tarif": "Ege usulü, ekşili pişir."},
    "Etli Bamya": {"malz": ["Bamya", "Kuşbaşı Et", "Limon", "Domates"], "tarif": "Salyalanmaması için bol limonla pişir."},
    "Kıymalı Yeşil Mercimek": {"malz": ["Yeşil Mercimek", "Kıyma", "Soğan"], "tarif": "Yahnisi gibi sulu yap, ekmeksiz iç."},
    "Izgara Köfte": {"malz": ["Kıyma", "Baharat", "Soğan (Ekmek yok)"], "tarif": "Ekmek içi koymadan yoğur, ızgara yap."}
}

# --- YEMEK LİSTELERİ (Random Seçim İçin) ---
STRICT_LUNCH = ["Yeşil Mercimek Salatası", "Ton Balıklı Salata", "Kabak Spagetti", "Zeytinyağlı Enginar", "Kinoalı Kısır", "Semizotu Salatası", "Mantar Sote"]
STRICT_DINNER = ["Izgara Tavuk & Yeşillik", "Fırın Somon", "Zeytinyağlı Brokoli", "Fırın Mücver (Unsuz)", "Şevketi Bostan", "Etli Bamya", "Kıymalı Yeşil Mercimek", "Izgara Köfte"]
STRICT_BREAKFAST_WEEKEND = ["Glutensiz Omlet", "Avokado & Yumurta", "Menemen (Ekmeksiz)", "Yulaflı Pankek (Şekersiz)", "Peynirli Maydanozlu Omlet"]
SABAH_SIVILARI = ["Sirkeli Ilık Su", "Yeşil Çay", "Sade Filtre Kahve", "Maydanoz Suyu", "Kiraz Sapı Çayı"]

# --- FONKSİYONLAR ---

def create_random_weekly_menu():
    """Tamamen kurallara uygun rastgele bir hafta oluşturur"""
    days = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
    menu = {}
    for day in days:
        if day in ["Cumartesi", "Pazar"]:
            sabah = random.choice(STRICT_BREAKFAST_WEEKEND)
            sabah_tip = "YEMEK"
        else:
            sabah = f"{random.choice(SABAH_SIVILARI)} (IF)"
            sabah_tip = "SIVI"
            
        menu[day] = {
            "Sabah": sabah,
            "Sabah_Tip": sabah_tip,
            "Ogle": random.choice(STRICT_LUNCH),
            "Aksam": random.choice(STRICT_DINNER)
        }
    return menu

# State Başlatma
if "current_week_num" not in st.session_state:
    st.session_state.current_week_num = 1

if "weekly_menu" not in st.session_state:
    # İlk açılışta rastgele bir liste yap
    st.session_state.weekly_menu = create_random_weekly_menu()

def generate_shopping_list(menu):
    shopping_set = set()
    for day, meals in menu.items():
        if meals['Ogle'] in TARIFLER:
            for item in TARIFLER[meals['Ogle']]['malz']: shopping_set.add(item)
        if meals['Aksam'] in TARIFLER:
            for item in TARIFLER[meals['Aksam']]['malz']: shopping_set.add(item)
        if meals['Sabah_Tip'] == "YEMEK" and meals['Sabah'] in TARIFLER:
             for item in TARIFLER[meals['Sabah']]['malz']: shopping_set.add(item)
    return sorted(list(shopping_set))

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2964/2964514.png", width=80)
    st.title(f"{st.session_state.current_week_num}. Hafta")
    st.progress(st.session_state.current_week_num / 4)
    
    # Hafta İlerleme Butonları
    c1, c2 = st.columns(2)
    with c1:
        if st.button("⬅️ Geri"):
            if st.session_state.current_week_num > 1:
                st.session_state.current_week_num -= 1
                st.session_state.weekly_menu = create_random_weekly_menu() # Yeni hafta için menü üret
                st.rerun()
    with c2:
        if st.button("İleri ➡️"):
            if st.session_state.current_week_num < 4:
                st.session_state.current_week_num += 1
                st.session_state.weekly_menu = create_random_weekly_menu() # Yeni hafta için menü üret
                st.rerun()

    # BUGÜNÜN ÖZETİ
    days = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
    day_idx = datetime.datetime.today().weekday()
    today_name = days[day_idx]
    today_menu = st.session_state.weekly_menu[today_name]
    
    st.markdown("---")
    st.markdown(f"**Bugün: {today_name}**")
    st.info(f"🍳 {today_menu['Sabah']}")
    st.success(f"🥗 {today_menu['Ogle']}")
    st.warning(f"🍽️ {today_menu['Aksam']}")

# --- ANA EKRAN ---
st.title("🥑 PCOS Nikosu Pro")
st.caption("Glutensiz, Düşük GI, Sıfır Şeker. Fabrika Ayarları Modu.")

# --- TABLAR ---
tab1, tab2, tab3, tab4 = st.tabs(["💬 Sohbet", "📅 Haftalık Plan", "🛒 Alışveriş", "🧘‍♀️ Spor"])

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
            Sen Nikosu'sun. Kullanıcı PCOS için çok sıkı bir diyette (Glutensiz, Düşük GI).
            Bugün: {today_name}. Menü: {today_menu}.
            Motivasyon ver, kaçamak yapmasına izin verme.
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
        st.session_state.messages = [{"role": "model", "content": "Fabrika ayarlarına döndük balım! Bu liste insülin direncini paramparça edecek. Hazır mısın? 💪"}]

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

# --- TAB 2: HAFTALIK PLAN (DEĞİŞTİRME BUTONLU) ---
with tab2:
    col_head, col_btn = st.columns([3, 1])
    with col_head:
        st.header(f"📅 {st.session_state.current_week_num}. Hafta Menüsü")
    with col_btn:
        # İŞTE ÖZGÜRLÜK BUTONU BURADA 👇
        if st.button("🔄 Menüyü Karıştır"):
            st.session_state.weekly_menu = create_random_weekly_menu()
            st.rerun()

    menu = st.session_state.weekly_menu
    days = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
    
    for d in days:
        is_weekend = d in ["Cumartesi", "Pazar"]
        
        with st.expander(f"{d}", expanded=True if d == today_name else False):
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
    st.header("🛒 İhtiyaç Listesi")
    st.write("Sadece bu haftaki menüde geçen malzemeler:")
    shop_list = generate_shopping_list(st.session_state.weekly_menu)
    
    c1, c2 = st.columns(2)
    for i, item in enumerate(shop_list):
        if i % 2 == 0: c1.checkbox(item, key=f"s_{i}")
        else: c2.checkbox(item, key=f"s_{i}")

# --- TAB 4: SPOR ---
with tab4:
    st.header("🧘‍♀️ Egzersiz")
    c1, c2 = st.columns(2)
    with c1: st.video("https://www.youtube.com/watch?v=enYITYwvPAQ")
    with c2: st.video("https://www.youtube.com/watch?v=inpok4MKVLM")
