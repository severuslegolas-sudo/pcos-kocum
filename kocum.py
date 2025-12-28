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
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- TASARIM (SICAK EV TEMASI) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Poppins', sans-serif; }
    
    /* Arka Plan: Sıcak, samimi şeftali/krem tonları */
    .stApp { background: linear-gradient(135deg, #fff1eb 0%, #ace0f9 100%); }
    
    .stChatMessage {
        background-color: rgba(255, 255, 255, 0.8);
        border-radius: 15px !important;
        border: 1px solid #e0e0e0;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    
    .menu-card {
        background-color: white;
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #f0f0f0;
    }
    
    h1, h2, h3 { color: #d35400; } /* Kiremit Rengi */
    
    .stButton>button {
        background-color: #e67e22;
        color: white;
        border-radius: 20px;
        border: none;
    }
    .stButton>button:hover { background-color: #d35400; }
    
    .streamlit-expanderHeader { font-weight: 600; color: #d35400; }
    
    #MainMenu, footer, header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- EKONOMİK & EV TİPİ TARİF HAVUZU ---
TARIFLER = {
    # --- SABAH (Hafta Sonu - Ekonomik) ---
    "Patatesli Yumurta": {
        "malz": ["2 Orta Boy Patates", "2 Yumurta", "Az Sıvı Yağ", "Pul Biber", "Maydanoz"],
        "tarif": "Patatesleri küp küp doğra, az yağda kapağı kapalı yumuşat (kızartma değil). Üzerine yumurtaları kır."
    },
    "Menemen": {
        "malz": ["2 Domates", "3 Yeşil Biber", "2 Yumurta", "Az Sıvı Yağ"],
        "tarif": "Biberleri öldür, domatesi ekle suyunu çeksin. Yumurtaları kır, çok karıştırma."
    },
    "Peynirli Maydanozlu Omlet": {
        "malz": ["2 Yumurta", "Bir parça Beyaz Peynir/Lor", "Yarım demet Maydanoz"],
        "tarif": "Yumurtaları çırp, içine ezilmiş peynir ve kıyılmış maydanozu ekle. Tavada pişir."
    },
    "Simit Tadında Yumurta": {
        "malz": ["1 Yumurta", "Susam", "Kaşar Peyniri (varsa)", "Tereyağı"],
        "tarif": "Tavaya susamları dök biraz kavur. Yumurtayı üzerine kır. Varsa kaşar ekle."
    },
    "Haşlanmış Yumurta & Söğüş": {
        "malz": ["2 Yumurta", "Salatalık", "Domates", "Biber", "Zeytin"],
        "tarif": "Klasik, en sağlıklı kahvaltı. Yumurtaları kayısı kıvamında haşla."
    },

    # --- ÖĞLE (Bakliyat & Sebze - Ekonomik) ---
    "Yeşil Mercimek Yemeği": {
        "malz": ["1 su bardağı Yeşil Mercimek", "1 Soğan", "1 Havuç", "Salça", "Erişte (az)"],
        "tarif": "Soğanı salçayla kavur. Mercimeği ve küp havucu ekle. Suyunu koy pişir. İnmeye yakın az erişte at."
    },
    "Nohut Yemeği": {
        "malz": ["Haşlanmış Nohut", "1 Soğan", "Salça", "Kimyon"],
        "tarif": "Soğanı kavur, salçayı ekle. Nohutları ve sıcak suyu koy. Kimyon ekle (gaz yapmasın diye). Özleşene kadar pişir."
    },
    "Kısır (Bol Yeşillikli)": {
        "malz": ["İnce Bulgur", "Salça", "Maydanoz", "Marul", "Limon", "Nar Ekşisi"],
        "tarif": "Bulguru sıcak suyla şişir. Salçayı yağda kavurup dök (çiğ kalmasın). Bol yeşillik ve limonla harmanla."
    },
    "Yumurtalı Ispanak": {
        "malz": ["Ispanak", "1 Soğan", "2 Yumurta", "Salça"],
        "tarif": "Soğanı kavur, ıspanakları ekle sönene kadar pişir. Göz göz açıp yumurtaları kır."
    },
    "Mücver (Fırında)": {
        "malz": ["2 Kabak", "1 Havuç", "2 Yumurta", "Un", "Dereotu", "Peynir"],
        "tarif": "Sebzeleri rendele suyunu sık. Diğer malzemelerle karıştır. Yağlı kağıda dök, fırına ver (Yağ çekmez, ekonomiktir)."
    },
    "Bulgur Pilavı & Yoğurt": {
        "malz": ["Pilavlık Bulgur", "Salça/Domates", "Biber", "Yoğurt"],
        "tarif": "Soğan ve biberi kavur. Bulguru ekle, suyunu ver. Yanına ev yoğurdu ile servis et."
    },
    "Fırın Makarna (Sebzeli)": {
        "malz": ["Yarım paket Makarna", "Peynir", "Süt", "Yumurta", "Varsa Ispanak/Pırasa"],
        "tarif": "Makarnayı haşla. Süt, yumurta, peynir ve elindeki sebzeyi karıştırıp fırına ver."
    },

    # --- AKŞAM (Hafif & Ev Usulü) ---
    "Fırın Tavuk & Patates": {
        "malz": ["Tavuk Baget/Göğüs", "2 Patates", "Salça", "Kekik"],
        "tarif": "Salçalı su ve baharatla sos hazırla. Tavuk ve patatesleri sosa bulayıp fırın poşetine veya tepsiye at."
    },
    "Zeytinyağlı Pırasa": {
        "malz": ["Pırasa", "2 Havuç", "Pirinç (az)", "Limon", "Zeytinyağı"],
        "tarif": "Havuçları ve pırasaları doğra. Yağda çevir. Az pirinç ve limonlu su ekleyip pişir."
    },
    "Kuru Fasulye (Etsiz)": {
        "malz": ["Kuru Fasulye", "1 Soğan", "Salça", "Pul Biber"],
        "tarif": "Klasik usul. Soğanı salçayı kavur, akşamdan ıslattığın fasulyeyi ekle. Kısık ateşte helmelenene kadar pişir."
    },
    "Tavuk Sote": {
        "malz": ["Tavuk Göğsü", "Biber", "Domates", "Soğan", "Baharat"],
        "tarif": "Tavukları kuşbaşı doğra, suyunu çekene kadar kavur. Sebzeleri ekle sotele."
    },
    "Karnabahar Kızartma (Fırında)": {
        "malz": ["Karnabahar", "Yoğurt", "Sarımsak", "Az Zeytinyağı", "Baharat"],
        "tarif": "Karnabaharları çiçeklerine ayır. Yağ ve baharatla harmanla fırına at. Çıkınca sarımsaklı yoğurt dök."
    },
    "Mercimek Çorbası & Salata": {
        "malz": ["Kırmızı Mercimek", "Patates", "Havuç", "Soğan"],
        "tarif": "Hepsini tencereye at haşla, blenderdan geçir. Yanına bol salata ile doyurucu bir öğün."
    },
    "Türlü Yemeği": {
        "malz": ["Patlıcan", "Kabak", "Patates", "Biber", "Domates", "Sarımsak"],
        "tarif": "Evde kalan sebzeleri küp küp doğra. Salçalı suyla tencerede veya güveçte pişir."
    }
}

# --- LİSTELER (Çeşitlilik İçin Genişletildi) ---
SABAH_SIVILARI = ["Sade Kahve ☕", "Limonlu Çay 🍵", "Sirkeli Su 💧", "Ihlamur 🌿", "Tarçınlı Süt 🥛"]
KAHVALTI_SECENEKLERI = ["Patatesli Yumurta", "Menemen", "Peynirli Maydanozlu Omlet", "Simit Tadında Yumurta", "Haşlanmış Yumurta & Söğüş"]
OGLE_SECENEKLERI = ["Yeşil Mercimek Yemeği", "Nohut Yemeği", "Kısır (Bol Yeşillikli)", "Yumurtalı Ispanak", "Mücver (Fırında)", "Bulgur Pilavı & Yoğurt", "Fırın Makarna (Sebzeli)"]
AKSAM_SECENEKLERI = ["Fırın Tavuk & Patates", "Zeytinyağlı Pırasa", "Kuru Fasulye (Etsiz)", "Tavuk Sote", "Karnabahar Kızartma (Fırında)", "Mercimek Çorbası & Salata", "Türlü Yemeği"]

# --- FONKSİYONLAR ---
def create_weekly_menu():
    days = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
    menu = {}
    
    # Random havuzunu karıştır (Başa sarmaması için)
    # Her gün için farklı seçim yapmaya zorla
    for day in days:
        if day in ["Cumartesi", "Pazar"]:
            sabah = random.choice(KAHVALTI_SECENEKLERI)
            sabah_tip = "YEMEK"
        else:
            sabah = random.choice(SABAH_SIVILARI)
            sabah_tip = "SIVI"
            
        menu[day] = {
            "Sabah": sabah, "Sabah_Tip": sabah_tip,
            "Ogle": random.choice(OGLE_SECENEKLERI),
            "Aksam": random.choice(AKSAM_SECENEKLERI)
        }
    return menu

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

# --- HAFIZA KONTROLÜ (BAŞA SARMAYI ENGELLEME) ---
if "weekly_menu" not in st.session_state:
    st.session_state.weekly_menu = create_weekly_menu()

def get_todays_menu():
    day_idx = datetime.datetime.today().weekday()
    days = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
    today = days[day_idx]
    return today, st.session_state.weekly_menu[today]

curr_day, curr_menu = get_todays_menu()

# --- YAN MENÜ ---
with st.sidebar:
    st.title(f"🏠 {curr_day}")
    st.markdown("### Ev Usulü Menü")
    st.info(f"🍳 **Sabah:** {curr_menu['Sabah']}")
    st.success(f"🍲 **Öğle:** {curr_menu['Ogle']}")
    st.warning(f"🍽️ **Akşam:** {curr_menu['Aksam']}")
    st.markdown("---")
    st.write("💧 *Su içmeyi unutma balım!*")

# --- ANA EKRAN ---
col_logo, col_text = st.columns([1, 6])
with col_text:
    st.markdown("<h1 style='color:#e67e22;'>PCOS Nikosu</h1>", unsafe_allow_html=True)
    st.caption("Ekonomik, Pratik ve Bizden Tarifler")

# --- TABLAR ---
tab_chat, tab_menu, tab_shop, tab_yoga = st.tabs(["💬 Sohbet", "🍲 Haftalık Menü", "🛒 Pazar Listesi", "🧘‍♀️ Spor"])

# --- TAB 1: SOHBET ---
with tab_chat:
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
            Sen Nikosu'sun. Kullanıcı ekonomik ve pratik ev yemekleri istiyor.
            Samimi bir ev arkadaşı gibi konuş.
            Bugün: {curr_day}. Menü: {curr_menu}.
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
        st.session_state.messages = [{"role": "model", "content": "Selam balım! Dolaptakilerle harikalar yaratmaya hazır mısın? 🏠"}]

    for m in st.session_state.messages:
        with st.chat_message(m["role"], avatar="👩‍🍳" if m["role"] == "model" else None):
            st.write(m["content"])

    if user_in := st.chat_input("Nikosu'ya yaz..."):
        st.session_state.messages.append({"role": "user", "content": user_in})
        with st.chat_message("user"): st.write(user_in)
        with st.spinner("..."):
            ai_reply = ask_ai(st.session_state.messages[:-1], user_in)
        st.session_state.messages.append({"role": "model", "content": ai_reply})
        with st.chat_message("model", avatar="👩‍🍳"):
            st.write(ai_reply)
            if "sorun" not in ai_reply: play_audio_gtts(ai_reply)

# --- TAB 2: MENÜ ---
with tab_menu:
    col_btn, _ = st.columns([1, 4])
    with col_btn:
        if st.button("🔄 Yeni Liste Yap"):
            st.session_state.weekly_menu = create_weekly_menu()
            st.rerun()

    menu = st.session_state.weekly_menu
    days = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
    
    for d in days:
        is_weekend = d in ["Cumartesi", "Pazar"]
        color = "#d35400" if is_weekend else "#27ae60"
        
        st.markdown(f"<h3 style='color:{color}; border-bottom:1px solid #eee;'>{d}</h3>", unsafe_allow_html=True)
        
        # Sabah
        sabah = menu[d]['Sabah']
        if menu[d]['Sabah_Tip'] == "YEMEK" and sabah in TARIFLER:
            with st.expander(f"🍳 Sabah: {sabah}"):
                st.write(f"**Malzemeler:** {', '.join(TARIFLER[sabah]['malz'])}")
                st.info(f"**Yapılışı:** {TARIFLER[sabah]['tarif']}")
        else:
            st.write(f"☕ **Sabah:** {sabah}")

        # Öğle & Akşam (Expander içinde)
        for ogun, icon in [("Ogle", "🍲"), ("Aksam", "🍽️")]:
            yemek = menu[d][ogun]
            with st.expander(f"{icon} {ogun}: {yemek}"):
                if yemek in TARIFLER:
                    st.write(f"**Malzemeler:** {', '.join(TARIFLER[yemek]['malz'])}")
                    st.info(f"**Yapılışı:** {TARIFLER[yemek]['tarif']}")
        st.markdown("<br>", unsafe_allow_html=True)

# --- TAB 3: PAZAR LİSTESİ ---
with tab_shop:
    st.header("🛒 Pazar & Market Listesi")
    st.caption("Evde olanları işaretle, eksikleri al balım.")
    shopping_list = generate_shopping_list(st.session_state.weekly_menu)
    
    c1, c2, c3 = st.columns(3)
    for i, item in enumerate(shopping_list):
        if i % 3 == 0: c1.checkbox(item, key=f"s_{i}")
        elif i % 3 == 1: c2.checkbox(item, key=f"s_{i}")
        else: c3.checkbox(item, key=f"s_{i}")

# --- TAB 4: SPOR ---
with tab_yoga:
    st.markdown("### 🏠 Evde Spor Keyfi")
    st.video("https://www.youtube.com/watch?v=enYITYwvPAQ")
