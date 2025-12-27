import streamlit as st
import google.generativeai as genai
import streamlit.components.v1 as components
# --- AYARLAR ---
# Guncelleme denemesi v1

# --- AYARLAR ---
# Buraya Google AI Studio'dan aldığın API anahtarını yapıştır
API_KEY = "AIzaSyA7-2GfqPIvxHJykolrM2aOAPXkfzm2g20"

# --- 1. İKON ve BAŞLIK AYARLARI (PCOS Nikosu) ---
st.set_page_config(
    page_title="PCOS Nikosu",
    page_icon="🌸",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ANDROID ANA EKRAN İKONU İÇİN HTML ENJEKSİYONU
# Bu kısım, "Ana Ekrana Ekle" dediğinde çıkacak ikonu belirlemeye çalışır.
# Kullandığım görsel, ücretsiz ve hoş bir çiçek ikonudur.
st.markdown(
    """
    <head>
        <link rel="apple-touch-icon" sizes="180x180" href="https://cdn-icons-png.flaticon.com/512/3461/3461858.png">
        <link rel="icon" type="image/png" sizes="32x32" href="https://cdn-icons-png.flaticon.com/512/3461/3461858.png">
    </head>
    """,
    unsafe_allow_html=True
)

# Ana Başlık
st.title("🌸 PCOS Nikosu")

# --- 2. SESLİ OKUMA MODU (KENAR ÇUBUĞU) ---
# Telefonda sol üstteki oka tıklayınca açılan menü
with st.sidebar:
    st.header("Ayarlar")
    tts_enabled = st.checkbox("🔊 Sesli Okuma Modu (Açmak için tıkla)", value=False, help="Bunu açarsan, ekranda çift tıkladığın herhangi bir yazı sesli okunur.")
    st.info("Not: Sesli okuma modu açıkken, okutmak istediğin yazının üzerine hızlıca iki kere tıkla/dokun.")

# SESLİ OKUMA JAVASCRIPT KODU
# Eğer kutucuk işaretliyse bu kod çalışır ve çift tıklamayı dinler.
if tts_enabled:
    js_code = """
    <script>
    // Çift tıklama (dblclick) olayını dinle
    document.body.addEventListener('dblclick', function(e) {
        // Tıklanan öğenin metnini al
        let target = e.target;
        // Bazen tıklanan yerin içi boş olabilir, en yakın metni bulmaya çalış
        let textToRead = target.innerText || target.textContent;

        // Eğer okunacak bir metin varsa
        if (textToRead && textToRead.length > 1) {
            // Eğer şu an başka bir şey okuyorsa sustur
            window.speechSynthesis.cancel();

            // Yeni okuma emri oluştur
            let utterance = new SpeechSynthesisUtterance(textToRead);
            utterance.lang = 'tr-TR'; // Türkçe oku
            utterance.rate = 0.9; // Hızı biraz yavaşlat (daha anlaşılır olsun)
            utterance.pitch = 1.0; // Ses tonu normal

            // Oku
            window.speechSynthesis.speak(utterance);
        }
    });
    </script>
    """
    # Bu JavaScript kodunu sayfaya gizlice gömüyoruz.
    components.html(js_code, height=0, width=0)


# --- 3. BAŞLANGIÇTA GÜNLÜK ÖĞÜN PLANI ---
# Senin düzenine uygun (2 öğün + glütensiz/şekersiz) standart plan.
with st.expander("📋 GÜNLÜK RUTİN & ÖRNEK MENÜM (Görmek için tıkla)", expanded=True):
    st.markdown("""
    **Sabah Ritüeli (Uyanınca):**
    * 1 büyük bardak su + 1 yemek kaşığı elma sirkesi.
    * Yüz masajı (ödem için).

    **Öğle Yemeği (12:00 - 13:00 gibi):**
    * **Ana Kural:** Tabağın yarısı sebze, çeyreği protein, çeyreği bakliyat/bulgur.
    * *Örnek:* Büyük bir kase ton balıklı/tavuklu salata (bol zeytinyağlı, limonlu) + 1 bardak ayran veya kefir.
    * *Veya:* Sebze yemeği + 1 kase yoğurt + 3-4 kaşık bulgur pilavı.

    **Ara Öğün (Sadece çok acıkırsan - 16:00 gibi):**
    * 1 avuç çiğ badem/ceviz VEYA 1 kase yoğurt (içine zerdeçal/karabiber atabilirsin).
    * *Meyve krizinde:* 1 küçük meyve + mutlaka yanında 2 ceviz.

    **Akşam Yemeği (En geç 19:30):**
    * **Ana Kural:** Karbonhidrat (bulgur, bakliyat) YOK. Sebze ve protein ağırlıklı.
    * *Örnek:* Izgara köfte/balık/hindi + yanında ızgara sebzeler veya bol salata.
    * *Veya:* Kıymalı/yumurtalı ıspanak yemeği + yoğurt.

    **Gece Rutini & Takviyeler:**
    * Günde 2 fincan Testere Dişli Aslan Pençesi (Sabah/Akşam aç).
    * Toplam 3 Litre su içildi mi? ✅
    * Yemekten sonra 10 dk hareket edildi mi? ✅
    """)


# --- YAPAY ZEKA AYARLARI ---
genai.configure(api_key=API_KEY)

# Modele yeni kimliğini (Nikosu) ve görevlerini öğretiyoruz.
system_instruction = """
Sen, PKOS (Polikistik Over Sendromu) olan, 74 kilo, 161 cm boyunda ve 25 yaşında bir kadının kişisel sağlık ve yaşam koçusun.
Adın 'PCOS Nikosu'. Kullanıcıya 'Balım', 'Tatlım' gibi samimi ve motive edici şekilde hitap etmelisin.
Kullanıcının şu anki düzeni:
- Glütensiz ve şekersiz beslenmeye çalışıyor (Düşük Glisemik İndeks).
- Günde 2 ana öğün yapıyor (Aralıklı oruç benzeri).
- Testere dişli aslan pençesi kürü uyguluyor (Günde 2 kez).
- Ödem ve şişkinlik sorunu yaşıyor (Sirke, zerdeçal kullanıyor).
Görevin: Onu motive etmek, kaçamak yaparsa yargılamadan toparlamak, sağlıklı tarifler vermek ve sorularını bir diyetisyen/en yakın arkadaş karışımı bir tonla yanıtlamak.
"""

model = genai.GenerativeModel('gemini-pro')

# --- SOHBET GEÇMİŞİ (HAFIZA) ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "model", "content": "Selam balım! PCOS Nikosu göreve hazır. 🌸 Bugün menüde plana sadık kaldık mı, nasıl hissediyorsun?"}
    ]

# Eski mesajları ekrana yazdır
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- KULLANICI GİRİŞİ ---
if prompt := st.chat_input("Buraya yazabilirsin..."):
    # Kullanıcı mesajını ekrana ekle
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Yapay zekadan cevap al
    try:
        # Geçmiş konuşmaları da modele gönderiyoruz ki bağlamı kopmasın
        chat = model.start_chat(history=[
            {"role": "user", "parts": [system_instruction]}, # İlk talimat
        ] + [
            {"role": m["role"], "parts": [m["content"]]} for m in st.session_state.messages if m["role"] != "system"
        ])

        with st.spinner('Nikosu düşünüyor... 🤔'):
            response = chat.send_message(prompt)
            bot_reply = response.text

        # Cevabı ekrana yazdır
        with st.chat_message("model"):
            st.markdown(bot_reply)
        st.session_state.messages.append({"role": "model", "content": bot_reply})

    except Exception as e:
        st.error(f"Bir hata oluştu, internetini kontrol et balım. Hata detayı: {e}")


