import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="DGN Sipariş Performansı", layout="wide")
st.title("📦 Mağaza Sipariş Onaylama Performansı Dashboard")

# 📥 Excel dosyasını oku
dosya_yolu = "Temmuz.xlsx"
df = pd.read_excel(dosya_yolu)

# 🛠️ "4543-3" paketleyen mağaza ismini "Ereğli Mağaza" yapalım
df['Paketleyen Mağaza'] = df['Paketleyen Mağaza'].apply(lambda x: "Ereğli Mağaza" if x == "4245-3" else x)

# 📅 Tarihleri işleyelim
df['Oluşma Tarihi'] = pd.to_datetime(df['Oluşma Tarihi'])
df['Paketleme Tarihi'] = pd.to_datetime(df['Paketleme Tarihi'])

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

# 🎨 Renk belirleme (sadece 0-1 Gün oranı)
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

# 💅 CSS tanımları
st.markdown("""
<style>
@keyframes blink {
  0% { opacity: 1; }
  50% { opacity: 0; }
  100% { opacity: 1; }
}
.blinking-alert {
  animation: blink 1s infinite;
  font-size: 28px;
  position: absolute;
  right: 15px;
  top: 50%;
  transform: translateY(-50%);
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
bolgeler = oran_df['Bölge'].unique()

for bolge in bolgeler:
    st.subheader(f"📍 Bölge: {bolge} E-Ticaret Sipariş Onaylama Raporu")

    # 🎨 Açıklama her bölgenin altında
    st.markdown("""
   <div style="margin-bottom: 10px; font-size: 16px;">
        <div>
            <span class="emoji-label">🟢</span><b>İyi</b> &nbsp;&nbsp;&nbsp;
            <span class="emoji-label">🟠</span><b>Orta</b> &nbsp;&nbsp;&nbsp;
            <span class="emoji-label">🔴</span><b>Kötü</b>
        </div>
        <div style="margin-top: 4px;">
            <span class="emoji-label">🚨</span><b>İconun Bulunduğu Mağazalarda 2+ Gün Oranı Hedeflenen Oranın Üstündedir.</b>
        </div>
    </div>
    """, unsafe_allow_html=True)

    bolge_df = oran_df[oran_df['Bölge'] == bolge].copy()
    bolge_df['Renk'] = bolge_df['0-1 Gün Oranı (%)'].apply(kart_renk)
    bolge_df['Renk Sırası'] = bolge_df['Renk'].apply(renk_sirasi)
    bolge_df = bolge_df.sort_values(by='Renk Sırası').reset_index(drop=True)

    cols = st.columns(4)
    for i, row in bolge_df.iterrows():
        renk = row['Renk']
        alert_icon_html = ""
        if row['2+ Gün Oranı (%)'] >= 3:
            alert_icon_html = '<span style="font-size: 28px; position: absolute; right: 15px; top: 50%; transform: translateY(-50%);">🚨</span>'

        with cols[i % 4]:
            st.markdown(
                f"""
                <div class="kart" style="background-color: {renk};">
                    <h2>{row['Paketleyen Mağaza']}</h2>
                    <p>0-1 Gün: {row['0-1 Gün']} adet / %{row['0-1 Gün Oranı (%)']:.2f}</p>
                    <p>1-2 Gün: {row['1-2 Gün']} adet / %{row['1-2 Gün Oranı (%)']:.2f}</p>
                    <p>2+ Gün: {row['2+ Gün']} adet / %{row['2+ Gün Oranı (%)']:.2f}</p>
                    <p><b>Toplam: {row['Toplam']}</b></p>
                    {alert_icon_html}
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
