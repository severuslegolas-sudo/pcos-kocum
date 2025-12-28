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
    initial_sidebar_state="collapsed"
)

# --- TASARIM (EGE & PINTEREST) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Poppins', sans-serif; }
    
    .stApp { background: linear-gradient(135deg, #f0fdf4 0%, #eff6ff 100%); }
    
    /* Expander (Tarif Kutuları) Tasarımı */
    .streamlit-expanderHeader {
        background-color: white;
        border-radius: 10px;
        border: 1px solid #e5e7eb;
        color: #065f46;
        font-weight: 600;
    }
    
    .stCheckbox { background-color: white; padding: 10px; border-radius: 10px; margin-bottom: 5px; }
    
    h1, h2, h3 { color: #047857; }
    #MainMenu, footer, header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- YEMEK VE TARİF VERİTABANI (DEV LİSTE) ---
# Format: "Yemek Adı": {"malz": [list], "tarif": "string"}

TARIFLER = {
    # --- SABAH (Hafta Sonu) ---
    "Ege Otlu Omlet": {
        "malz": ["2 Yumurta", "Ispanak/Isırgan Otu", "1 tatlı kaşığı Zeytinyağı", "Beyaz Peynir"],
        "tarif": "Otları yıkayıp zeytinyağında hafifçe çevir. Yumurtaları çırpıp üzerine dök. Peyniri ekle, kapağını kapatıp pişir."
    },
    "Lor Peynirli Roka Salatası": {
        "malz": ["Lor Peyniri", "Roka", "Çeri Domates", "Ceviz", "Zeytinyağı", "1 Haşlanmış Yumurta"],
        "tarif": "Tüm yeşillikleri doğra. Üzerine lor, ceviz ve zeytinyağını ekle. Yumurtayı dilimleyip servis et."
    },
    "Bergama Tulumu & Ceviz": {
        "malz": ["Bergama Tulum Peyniri", "2 tam Ceviz", "Salatalık", "Bol Yeşillik", "1 Dilim Ekmek"],
        "tarif": "Klasik Ege kahvaltısı tabağı hazırla. Cevizleri peynirle beraber tüket."
    },
    "Menemen (Ekmeksiz)": {
        "malz": ["2 Domates", "2 Biber", "2 Yumurta", "Zeytinyağı"],
        "tarif": "Biberleri ve domatesleri zeytinyağında öldür. Yumurtaları kır ama çok karıştırma."
    },

    # --- ÖĞLE (Hafif Ege) ---
    "Zeytinyağlı Kabak Sıyırma": {
        "malz": ["2 Kabak", "1 Soğan", "Yarım Limon", "Dereotu", "Pirinç (1 kaşık)"],
        "tarif": "Kabakları soyacakla şerit şerit doğra. Soğanı kavur, kabakları ve pirinci ekle. Kısık ateşte kendi suyuyla pişir. Limon ve dereotu ekle."
    },
    "Deniz Börülcesi & Tavuk": {
        "malz": ["Deniz Börülcesi", "Sarımsak", "Zeytinyağı", "Limon", "Izgara Tavuk Göğsü"],
        "tarif": "Börülceleri haşla ve kılçıklarını ayıkla. Sarımsaklı limonlu sos dök. Yanına tavuğu ızgara yap."
    },
    "Girit Kabağı Dolması": {
        "malz": ["2 Girit Kabağı (Top)", "Lor Peyniri", "Dereotu", "Zeytinyağı"],
        "tarif": "Kabakların içini oy, hafif haşla. Lor, dereotu ve zeytinyağını karıştırıp içine doldur. Fırında 15 dk pişir."
    },
    "Semizotu Salatası": {
        "malz": ["Semizotu", "Süzme Yoğurt", "Sarımsak", "Ceviz", "Zeytinyağı"],
        "tarif": "Semizotunu yıka, doğramadan yapraklarını ayır. Sarımsaklı yoğurtla karıştır, üzerine ceviz serp."
    },
    "Enginar Kalbi": {
        "malz": ["3 Enginar Çanağı", "Bezelye/Havuç garnitür", "Zeytinyağı", "Portakal Suyu"],
        "tarif": "Enginarları tencereye diz. Üzerine garnitürü koy. Zeytinyağı ve portakal suyunu gezdirip yumuşayana kadar pişir."
    },

    # --- AKŞAM (Protein & Zayıflama) ---
    "Fırın Levrek": {
        "malz": ["1 Levrek", "Defne Yaprağı", "Limon", "Roka"],
        "tarif": "Balığın içine defne yaprağı ve limon koy. Yağlı kağıtta fırına ver (200 derece 25 dk). Yanına bol roka."
    },
    "Şevketi Bostan": {
        "malz": ["Şevketi Bostan Otu", "1 Soğan", "Kuzu eti veya Tavuk", "Limon", "Yumurta sarısı (Terbiye)"],
        "tarif": "Etleri soğanla kavur. Otları ekle, su koy pişir. İnmeye yakın limon ve yumurta sarısı ile terbiye yap."
    },
    "Pazı Kavurma": {
        "malz": ["1 Demet Pazı", "1 Soğan", "Pul Biber", "2 Yumurta"],
        "tarif": "Soğanı kavur, doğranmış pazıları ekle suyunu çeksin. Ortasını açıp yumurtaları kır."
    },
    "Zeytinyağlı Bamya": {
        "malz": ["Bamya", "Domates", "Limon Tuzu/Suyu", "Zeytinyağı"],
        "tarif": "Bamyaları ayıkla. Domates sosunda, bol limonla (sünmemesi için) kısık ateşte pişir."
    },
    "Fırın Mücver": {
        "malz": ["2 Kabak", "1 Yumurta", "Dereotu", "Tam Buğday Unu (1 kaşık)", "Beyaz Peynir"],
        "tarif": "Kabağı rendele suyunu sık. Malzemeleri karıştır. Yağlı kağıda kaşıkla dök. Fırında kızarana kadar pişir."
    }
}

# Veritabanında olmayanlar için yedek içerik
GENERIC_RECIPE = {"malz": ["Mevsim sebzeleri", "Protein kaynağı", "Zeytinyağı"], "tarif": "Sağlıklı pişirme yöntemleriyle hazırla balım."}

# Listeler (Veritabanındaki anahtarları kullanmalı)
SABAH_SIVILARI = ["Filtre Kahve ☕", "Adaçayı 🌿", "Sirkeli Su 💧", "Maydanoz Suyu 🍋"]
KAHVALTI_SECENEKLERI = ["Ege Otlu Omlet", "Lor Peynirli Roka Salatası", "Bergama Tulumu & Ceviz", "Menemen (Ekmeksiz)"]
OGLE_SECENEKLERI = ["Zeytinyağlı Kabak Sıyırma", "Deniz Börülcesi & Tavuk", "Girit Kabağı Dolması", "Semizotu Salatası", "Enginar Kalbi"]
AKSAM_SECENEKLERI = ["Fırın Levrek", "Şevketi Bostan", "Pazı Kavurma", "Zeytinyağlı Bamya", "Fırın Mücver"]

# --- FONKSİYONLAR ---
def create_weekly_menu():
    days = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
    menu = {}
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
        # Öğle yemeği malzemeleri
        if meals['Ogle'] in TARIFLER:
            for item in TARIFLER[meals['Ogle']]['malz']:
                shopping_set.add(item)
        # Akşam yemeği malzemeleri
        if meals['Aksam'] in TARIFLER:
            for item in TARIFLER[meals['Aksam']]['malz']:
                shopping_set.add(item)
        # Kahvaltı (Hafta sonuysa)
        if meals['Sabah_Tip'] == "YEMEK" and meals['Sabah'] in TARIFLER:
             for item in TARIFLER[meals['Sabah']]['malz']:
                shopping_set.add(item)
    return sorted(list(shopping_set))

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
    st.title(f"🌿 {curr_day}")
    st.markdown("### Bugün Ne Yiyoruz?")
    
    st.info(f"🍳 **Sabah:** {curr_menu['Sabah']}")
    st.success(f"🥗 **Öğle:** {curr_menu['Ogle']}")
    st.warning(f"🍽️ **Akşam:** {curr_menu['Aksam']}")
    
    st.markdown("---")
    st.write("💧 *Hedef: 2.5 Litre Su*")

# --- ANA EKRAN ---
col_logo, col_text = st.columns([1, 6])
with col_text:
    st.markdown("<h1 style='margin-bottom:0; color:#065f46;'>PCOS Nikosu</h1>", unsafe_allow_html=True)
    st.caption("Ege Mutfağı, Sağlıklı Tarifler & Akıllı Alışveriş")

# --- TABLAR ---
tab_chat, tab_menu, tab_shop, tab_yoga = st.tabs(["💬 Sohbet", "📖 Tarifli Menü", "🛒 Alışveriş Listesi", "🧘‍♀️ Spor"])

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
            Sen Nikosu'sun. En yakın kız arkadaş gibi samimi konuş.
            Konumuz: Kilo verme, Ege Mutfağı, PCOS.
            Bugün: {curr_day}. Menü: {curr_menu}.
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
        st.session_state.messages = [{"role": "model", "content": "Selam balım! Tariflerini ve alışveriş listeni hazırladım. Bakalım mı? 🍋"}]

    for m in st.session_state.messages:
        with st.chat_message(m["role"], avatar="🌿" if m["role"] == "model" else None):
            st.write(m["content"])

    if user_in := st.chat_input("Nikosu'ya yaz..."):
        st.session_state.messages.append({"role": "user", "content": user_in})
        with st.chat_message("user"): st.write(user_in)
        with st.spinner("..."):
            ai_reply = ask_ai(st.session_state.messages[:-1], user_in)
        st.session_state.messages.append({"role": "model", "content": ai_reply})
        with st.chat_message("model", avatar="🌿"):
            st.write(ai_reply)
            if "sorun" not in ai_reply: play_audio_gtts(ai_reply)

# --- TAB 2: TARİFLİ MENÜ ---
with tab_menu:
    col_btn, _ = st.columns([1, 4])
    with col_btn:
        if st.button("🔄 Menüyü Yenile"):
            st.session_state.weekly_menu = create_weekly_menu()
            st.rerun()

    menu = st.session_state.weekly_menu
    days = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
    
    for d in days:
        is_weekend = d in ["Cumartesi", "Pazar"]
        color = "#d97706" if is_weekend else "#059669"
        
        st.markdown(f"<h3 style='color:{color}; border-bottom:1px solid #ddd; padding-bottom:5px;'>{d}</h3>", unsafe_allow_html=True)
        
        # Sabah
        sabah_yemek = menu[d]['Sabah']
        if menu[d]['Sabah_Tip'] == "YEMEK" and sabah_yemek in TARIFLER:
            with st.expander(f"🍳 Sabah: {sabah_yemek}"):
                st.write(f"**Malzemeler:** {', '.join(TARIFLER[sabah_yemek]['malz'])}")
                st.info(f"**Yapılışı:** {TARIFLER[sabah_yemek]['tarif']}")
        else:
            st.write(f"☕ **Sabah:** {sabah_yemek}")

        # Öğle
        ogle_yemek = menu[d]['Ogle']
        with st.expander(f"🥗 Öğle: {ogle_yemek}"):
            if ogle_yemek in TARIFLER:
                st.write(f"**Malzemeler:** {', '.join(TARIFLER[ogle_yemek]['malz'])}")
                st.info(f"**Yapılışı:** {TARIFLER[ogle_yemek]['tarif']}")
            else:
                st.write("Tarif yükleniyor...")

        # Akşam
        aksam_yemek = menu[d]['Aksam']
        with st.expander(f"🍽️ Akşam: {aksam_yemek}"):
            if aksam_yemek in TARIFLER:
                st.write(f"**Malzemeler:** {', '.join(TARIFLER[aksam_yemek]['malz'])}")
                st.info(f"**Yapılışı:** {TARIFLER[aksam_yemek]['tarif']}")
            else:
                st.write("Tarif yükleniyor...")
        st.markdown("<br>", unsafe_allow_html=True)

# --- TAB 3: ALIŞVERİŞ LİSTESİ ---
with tab_shop:
    st.header("🛒 Haftalık Alışveriş Listen")
    st.write("Bu haftaki menüne göre otomatik oluşturuldu. Aldıklarını işaretle!")
    
    shopping_list = generate_shopping_list(st.session_state.weekly_menu)
    
    # 3 Kolonlu Liste
    sc1, sc2, sc3 = st.columns(3)
    for i, item in enumerate(shopping_list):
        if i % 3 == 0: sc1.checkbox(item, key=f"shop_{i}")
        elif i % 3 == 1: sc2.checkbox(item, key=f"shop_{i}")
        else: sc3.checkbox(item, key=f"shop_{i}")
        
    st.markdown("---")
    st.caption("💡 *İpucu: Markete gitmeden önce mutfağındakileri kontrol etmeyi unutma balım!*")

# --- TAB 4: SPOR ---
with tab_yoga:
    st.markdown("### 🧘‍♀️ Ege Havasında Spor")
    c1, c2 = st.columns(2)
    with c1:
        st.video("https://www.youtube.com/watch?v=inpok4MKVLM")
    with c2:
        st.video("https://www.youtube.com/watch?v=enYITYwvPAQ")
