import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="DGN Sipariş Performansı", layout="wide")
st.title("📦 Mağaza Sipariş Onaylama Performansı Dashboard")

dosya_yolu = "Temmuz.xlsx"
df = pd.read_excel(dosya_yolu)

# 🛠️ "4245-3" paketleyen mağaza ismini "Ereğli Mağaza" yapalım
df['Paketleyen Mağaza'] = df['Paketleyen Mağaza'].apply(lambda x: "Ereğli Mağaza" if x == "4245-3" else x)

# 📅 Tarihleri işleyelim
df['Oluşma Tarihi'] = pd.to_datetime(df['Oluşma Tarihi'])
df['Paketleme Tarihi'] = pd.to_datetime(df['Paketleme Tarihi'])

# Üstte filtre: Yıllık / Aylık ve Ay seçimi
donem_tipi = st.sidebar.selectbox("Dönem Tipi Seçin", ["Yıllık", "Aylık"])

secili_aylar = []
if donem_tipi == "Aylık":
    aylar = ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran',
            'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık']
    ay_secimi = st.sidebar.multiselect("Ay Seçiniz", aylar, default=aylar)
    # Ay isimlerini ay numarasına çevir
    ay_dict = {ad: i+1 for i, ad in enumerate(aylar)}
    secili_aylar = [ay_dict[ay] for ay in ay_secimi]
else:
    secili_aylar = list(range(1,13))  # Tüm aylar

# Filtreleme: Seçilen ayların ortak verisi
df = df[df['Oluşma Tarihi'].dt.month.isin(secili_aylar)]

# ⏱ Süre hesaplama
df['Paketleme Süresi (Saat)'] = (df['Paketleme Tarihi'] - df['Oluşma Tarihi']).dt.total_seconds() / 3600
df['Paketleme Süresi (Gün)'] = df['Paketleme Süresi (Saat)'] / 24

def zaman_dilimi(gun):
    if gun <= 1:
        return '0-1 Gün'
    elif 1 < gun <= 2:
        return '1-2 Gün'
    else:
        return '2+ Gün'

df['Paketleme Süre Grubu'] = df['Paketleme Süresi (Gün)'].apply(zaman_dilimi)

# 📊 Oranları hesapla
oran_df = df.groupby(['Bölge', 'Paketleyen Mağaza', 'Paketleme Süre Grubu']).size().unstack(fill_value=0)
oran_df['Toplam'] = oran_df.sum(axis=1)

for col in ['0-1 Gün', '1-2 Gün', '2+ Gün']:
    if col not in oran_df.columns:
        oran_df[col] = 0
    oran_df[f'{col} Oranı (%)'] = (oran_df[col] / oran_df['Toplam']) * 100

oran_df = oran_df.reset_index()

# 💅 CSS tanımları
st.markdown("""
<style>
.blinking-alert {
  animation: blink 1s infinite;
  font-size: 28px;
}
.kart {
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 15px;
  color: white;
  position: relative;
}
.kart h2 {
    font-size: 20px;
    font-weight: bold;
    margin-bottom: 8px;
}
.kart p {
    font-size: 18px;
    font-weight: bold;
    margin: 4px 0;
}
.emoji-label {
  font-size: 20px;
  margin-right: 10px;
  vertical-align: middle;
}
</style>
""", unsafe_allow_html=True)

# 📘 Genel açıklama (üstte)
st.markdown("""
<div style="margin-bottom: 20px; font-size: 18px;">
    <span class="emoji-label">🟢</span><b>İyi</b> &nbsp;&nbsp;&nbsp;
    <span class="emoji-label">🟠</span><b>Orta</b> &nbsp;&nbsp;&nbsp;
    <span class="emoji-label">🔴</span><b>Kötü</b> &nbsp;&nbsp;&nbsp;
    <span class="emoji-label">🚨</span><b>Çok Riskli (2+ Gün oranı %3+)</b>
</div>
""", unsafe_allow_html=True)

# 🔄 Her bölge için kutular

# Adetleri göster/gizle seçeneği
adet_goster = st.sidebar.checkbox("Adetleri Göster", value=True)

def kart_renk(orani):
    if orani >= 97:
        return '#4CAF50'  # Yeşil
    elif 95 <= orani < 97:
        return '#FF9800'  # Turuncu
    else:
        return '#F44336'  # Kırmızı

def renk_sirasi(renk):
    if renk == '#4CAF50':
        return 0
    elif renk == '#FF9800':
        return 1
    elif renk == '#F44336':
        return 2
    return 3

bolgeler = oran_df['Bölge'].unique()

for bolge in bolgeler:
    st.subheader(f"📍 Bölge: {bolge}")

    st.markdown("""
    <div style="margin-bottom: 10px; font-size: 16px;">
        <div>
            <span class="emoji-label">🟢</span><b>İyi</b> &nbsp;&nbsp;&nbsp;
            <span class="emoji-label">🟠</span><b>Orta</b> &nbsp;&nbsp;&nbsp;
            <span class="emoji-label">🔴</span><b>Kötü</b>
        </div>
        <div style="margin-top: 4px;">
            <span class="emoji-label">🚨</span><b>İkonun Bulunduğu Mağazalarda 2+ Gün Oranı Hedeflenen Oranın Üstündedir.</b>
        </div>
    </div>
    """, unsafe_allow_html=True)

    bolge_df = oran_df[oran_df['Bölge'] == bolge].copy()
    bolge_df['Renk'] = bolge_df['0-1 Gün Oranı (%)'].apply(kart_renk)
    bolge_df['Renk Sırası'] = bolge_df['Renk'].apply(renk_sirasi)
    bolge_df = bolge_df.sort_values(by=['Renk Sırası', '0-1 Gün Oranı (%)'], ascending=[True, False]).reset_index(drop=True)


    cols = st.columns(4)
    for i, row in bolge_df.iterrows():
        renk = row['Renk']
        alert_icon_html = "🚨" if row['2+ Gün Oranı (%)'] >= 3 else ""

        adet_0_1 = f"{row['0-1 Gün']} adet / " if adet_goster else ""
        adet_1_2 = f"{row['1-2 Gün']} adet / " if adet_goster else ""
        adet_2_plus = f"{row['2+ Gün']} adet / " if adet_goster else ""

        with cols[i % 4]:
            st.markdown(
                f"""
                <div class="kart" style="background-color: {renk};">
                    <h2>{row['Paketleyen Mağaza']} {alert_icon_html}</h2>
                    <p>0-1 Gün: {adet_0_1}%{row['0-1 Gün Oranı (%)']:.2f}</p>
                    <p>1-2 Gün: {adet_1_2}%{row['1-2 Gün Oranı (%)']:.2f}</p>
                    <p>2+ Gün: {adet_2_plus}%{row['2+ Gün Oranı (%)']:.2f}</p>
                </div>
                """, unsafe_allow_html=True
            )

# 📊 Mağaza bazlı sipariş oranı grafiği
st.subheader("🏪 Depo Bazlı Sipariş Dağılımı (%) — Sıralı")
siparis_oran = df['Paketleyen Mağaza'].value_counts(normalize=True).sort_values(ascending=False) * 100

fig, ax = plt.subplots()
siparis_oran.plot(kind='barh', ax=ax, color='skyblue')
ax.set_xlabel("Sipariş Oranı (%)")
ax.set_ylabel("Depo")
ax.invert_yaxis()
for i, v in enumerate(siparis_oran):
    ax.text(v + 0.5, i, f"{v:.1f}%", va='center')
st.pyplot(fig)

# 🧾 Detaylı veri gösterimi
with st.expander("📋 İşlenmiş Veri Tablosu"):
    st.dataframe(df)
