# -*- coding: utf-8 -*-
"""
========================================================================================
THE TRILAKSANA MINING SUITE - MODUL 18: PREDIKSI SAHAM KUANTITATIF
DOKUMENTASI METODOLOGI, DASAR TEORI MATEMATIKA, & PANDUAN PENGGUNAAN
========================================================================================
Hak Cipta: Dr. Ir. Ahmad Raymond Trilaksana
Lisensi: Central Cloud Licensing v107
========================================================================================
"""

import streamlit as st


def render_theory_tab():
    """
    Menampilkan tab dokumentasi lengkap mengenai latar belakang, dasar teori,
    formulasi matematika, proses stokastik, arsitektur machine learning,
    dan protokol manajemen risiko institusional untuk Modul 18.
    """
    st.markdown("""
    <div style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); border: 1px solid #334155; border-radius: 12px; padding: 22px 26px; margin-bottom: 25px;">
        <div style="display:inline-block; padding:4px 14px; background:rgba(59,130,246,0.2); border:1px solid #3b82f6; border-radius: 20px; color:#60a5fa; font-size:11px; font-weight:800; letter-spacing:1px; margin-bottom:8px;">
            WHITEPAPER KUANTITATIF & METODOLOGI
        </div>
        <h2 style="color:#ffffff; margin:0 0 8px 0; font-size:24px; font-weight:800;">
            Fondasi Teori, Algoritma Matematika, & Panduan Operasional Modul 18
        </h2>
        <div style="color:#94a3b8; font-size:13.5px; line-height:1.6;">
            Dokumentasi komprehensif mengenai prinsip ilmiah di balik model peramalan pergerakan harga saham,
            rekayasa fitur statistika, arsitektur <i>Dual-Ensemble Learning</i>, penentuan target waktu dinamis
            melalui teori <i>First-Passage Time</i>, serta protokol manajemen risiko asimetris berstandar institusional.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ----------------------------------------------------------------------------------
    # BAB 1: LATAR BELAKANG & FILOSOFI INVESTASI
    # ----------------------------------------------------------------------------------
    with st.expander("📌 1. Latar Belakang & Filosofi Investasi Kuantitatif", expanded=True):
        st.markdown(r"""
        ### 1.1 Paradigma Kuantitatif vs Spekulasi Pasar
        Pasar modal Indonesia (khususnya saham-saham yang terafiliasi dengan siklus komoditas mineral, energi, 
        perbankan, dan manufaktur) kerap dicirikan oleh volatilitas tinggi akibat arus modal asing (*foreign flow*), 
        sentimen makroekonomi global, dan dinamika harga komoditas dunia.

        Pendekatan konvensional yang mengandalkan intuisi subjektif, sentimen forum publik, atau analisis teknikal 
        klasik secara manual sering kali terjebak dalam bias kognitif:
        1. **Loss Aversion Bias:** Keengganan memotong kerugian kecil (*cut loss*) sehingga berujung pada kerugian masif yang merusak portofolio.
        2. **FOMO (Fear of Missing Out):** Pembelian pada puncak euforia (*buying at the top*) akibat dorongan emosional.
        3. **Overconfidence & Random Reinforcement:** Menganggap keuntungan acak sebagai keahlian analisis tanpa keunggulan statistik (*statistical edge*) yang terukur.

        ### 1.2 Filosofi *Evidence-Based Quantitative Finance*
        Modul 18 dirancang dengan filosofi **keuangan kuantitatif berbasis bukti empiris**:
        - **Objektivitas Mutlak:** Setiap keputusan beli (*Buy*), tahan (*Hold*), maupun keluar (*Exit*) diturunkan dari persamaan matematika deterministik dan probabilitas statistik.
        - **Keunggulan Statistik (*Mathematical Edge*):** Sistem tidak menuntut akurasi sempurna 100%, melainkan mengeksploitasi probabilitas terkalibrasi ($\ge 55\%$) yang dikombinasikan dengan rasio *Risk-to-Reward* asimetris ($\ge 1:1.5$).
        - **Proteksi Kapital Sebagai Prioritas Tertinggi:** Keberlangsungan modal (*capital preservation*) dijamin melalui pembatasan risiko ketat (*hard stop loss*) dan jeda karantina (*lockout*) emiten bermasalah.
        """)

    # ----------------------------------------------------------------------------------
    # BAB 2: DASAR TEORI STATISTIK & REKAYASA FITUR (FEATURE ENGINEERING)
    # ----------------------------------------------------------------------------------
    with st.expander("📐 2. Dasar Teori Statistika & Rekayasa Fitur (Feature Engineering)", expanded=True):
        st.markdown("""
        Data mentah berupa harga pembukaan (*Open*), tertinggi (*High*), terendah (*Low*), penutupan (*Close*), 
        dan volume (*Volume*) ditransformasikan ke dalam ruang fitur berdimensi jamak yang merepresentasikan 
        momentum, volatilitas, kekuatan tren, dan akumulasi likuiditas.
        """)

        st.markdown("#### A. Return Logaritmik & Normalisasi Distribusi (*Z-Score*)")
        st.markdown("""
        Return harga dihitung menggunakan logaritma natural untuk memastikan sifat aditifitas temporal 
        dan stabilisasi varians:
        """)
        st.latex(r"r_t = \ln\left(\frac{P_t}{P_{t-1}}\right)")
        st.markdown("""
        Untuk membandingkan pergerakan antar saham dengan skala harga yang berbeda, nilai return distandarisasi 
        ke dalam nilai Z-Score:
        """)
        st.latex(r"Z_t = \frac{r_t - \mu_r}{\sigma_r}")
        st.caption(r"di mana $P_t$ adalah harga penutupan hari $t$, $\mu_r$ adalah nilai rata-rata return historis, dan $\sigma_r$ adalah standar deviasi return.")

        st.markdown("#### B. Relative Strength Index (RSI) Wilder 14 Periode")
        st.markdown("""
        Untuk mengukur kecepatan dan perubahan magnitudo pergerakan harga tanpa terjadinya penumpukan pecahan, 
        perhitungan dibagi ke dalam dua tahap deterministik:
        """)
        st.markdown("**Tahap 1: Rasio Kekuatan Relatif (*Relative Strength / RS*)**")
        st.latex(r"\text{RS} = \frac{\text{EMA}(\text{Gain}, 14)}{\text{EMA}(\text{Loss}, 14)}")
        st.markdown("**Tahap 2: Normalisasi Indeks Osilator (0 hingga 100)**")
        st.latex(r"\text{RSI} = 100 - \frac{100}{1 + \text{RS}}")
        st.caption(r"Gain dihitung jika $P_t > P_{t-1}$, sedangkan Loss dihitung jika $P_t < P_{t-1}$. EMA menggunakan faktor perataan eksponensial Wilder.")

        st.markdown("#### C. Volatilitas Pasar: Average True Range (ATR)")
        st.markdown("""
        Rentang sebenarnya (*True Range / TR*) mengukur ruang gerak volatilitas harian termasuk celah loncatan (*price gaps*):
        """)
        st.latex(r"\text{TR}_t = \max\Big( H_t - L_t, \; |H_t - C_{t-1}|, \; |L_t - C_{t-1}| \Big)")
        st.markdown("ATR periode $N = 14$ diperbarui secara rekursif:")
        st.latex(r"\text{ATR}_t = \frac{(N - 1)\text{ATR}_{t-1} + \text{TR}_t}{N}")
        st.caption(r"di mana $H_t$ adalah harga tertinggi, $L_t$ adalah harga terendah, dan $C_{t-1}$ adalah harga penutupan hari sebelumnya.")

        st.markdown("#### D. Moving Average Differencing & Faktor Perataan Eksponensial")
        st.markdown(r"Faktor bobot peluruhan eksponensial $\alpha$ untuk periode $N$ dirumuskan:")
        st.latex(r"\alpha = \frac{2}{N + 1}")
        st.markdown("Nilai Exponential Moving Average (EMA) pada hari $t$ adalah:")
        st.latex(r"\text{EMA}_t = \alpha P_t + (1 - \alpha)\text{EMA}_{t-1}")
        st.markdown("Selisih tren momentum persentase antara rata-rata jangka pendek (20 hari) dan menengah (50 hari):")
        st.latex(r"\Delta_{\text{EMA}} = \frac{\text{EMA}_{20} - \text{EMA}_{50}}{\text{EMA}_{50}} \times 100\%")

        st.markdown("#### E. Volume Price Trend (VPT) & Lonjakan Likuiditas")
        st.markdown("Perubahan harga relatif pada hari $t$ dihitung:")
        st.latex(r"\Delta P_{\text{rel}} = \frac{C_t - C_{t-1}}{C_{t-1}}")
        st.markdown("Akumulasi arus dana dihitung melalui integrasi volume harian:")
        st.latex(r"\text{VPT}_t = \text{VPT}_{t-1} + \Big(V_t \times \Delta P_{\text{rel}}\Big)")
        st.markdown("Rasio lonjakan volume di atas rata-rata 20 hari:")
        st.latex(r"V_{\text{ratio}} = \frac{V_t}{\text{SMA}(V, 20)}")

    # ----------------------------------------------------------------------------------
    # BAB 3: ARSITEKTUR MACHINE LEARNING (DUAL-ENSEMBLE MODEL)
    # ----------------------------------------------------------------------------------
    with st.expander("🤖 3. Arsitektur Machine Learning: Dual-Ensemble (RF + Gradient Boosting)", expanded=True):
        st.markdown("""
        ### 3.1 Mengapa Memadukan Random Forest & Gradient Boosting?
        Dalam ekonometrika finansial, data pasar memiliki rasio *signal-to-noise* yang rendah. Menggunakan satu algoritma 
        saja rentan terhadap bias spesifik atau *overfitting*. Modul 18 menerapkan arsitektur hibrida:
        - **Random Forest (RF):** Mengurangi varians data (*variance reduction*) melalui *Bootstrap Aggregating (Bagging)* dan pemilihan subset fitur acak pada ribuan pohon keputusan independen.
        - **Gradient Boosting (GB):** Mengurangi bias pemodelan (*bias reduction*) melalui optimasi sekuensial yang secara khusus menargetkan kesalahan prediksi (*pseudo-residuals*) pada iterasi sebelumnya.

        ### 3.2 Formulasi Pemisahan Node: Gini Impurity
        Pada setiap simpul pohon keputusan Random Forest, pemilihan fitur pemisah optimal ditentukan dengan meminimalkan kotoran Gini (*Gini Impurity*):
        """)
        st.latex(r"I_G(p) = 1 - \sum_{k=1}^{K} p_k^2")
        st.caption(r"di mana $p_k$ adalah proporsi sampel kelas $k$ (arah harga naik vs turun) pada simpul tertentu.")

        st.markdown("""
        ### 3.3 Fungsi Kerugian & Pembaruan Residual Gradient Boosting
        Gradient Boosting meminimalkan fungsi kerugian *Binary Cross-Entropy (Log-Loss)*:
        """)
        st.latex(r"\mathcal{L}(y, \hat{y}) = -\frac{1}{N} \sum_{i=1}^{N} \Big[ y_i \ln(\hat{y}_i) + (1 - y_i) \ln(1 - \hat{y}_i) \Big]")
        st.markdown("Pada setiap iterasi ke-$m$, arah penurunan gradien dihitung dari pseudo-residual:")
        st.latex(r"r_{im} = -\left[ \frac{\partial \mathcal{L}(y_i, f(x_i))}{\partial f(x_i)} \right]_{f(x) = f_{m-1}(x)}")

        st.markdown(r"""
        ### 3.4 Soft Voting Ensemble Probability
        Probabilitas final kenaikan harga $\hat{P}(Y=1|X)$ dihitung menggunakan mekanisme pemungutan suara berbobot 
        (*Soft Voting Ensemble*):
        """)
        st.latex(r"\hat{P}(Y=1|X) = w_{\text{RF}} P_{\text{RF}}(Y=1|X) + w_{\text{GB}} P_{\text{GB}}(Y=1|X)")
        st.markdown("dengan penetapan bobot berimbang terkalibrasi:")
        st.latex(r"w_{\text{RF}} = 0.50, \quad w_{\text{GB}} = 0.50")
        st.markdown("""
        Sinyal beli institusional (*Strong Buy*) hanya diterbitkan apabila probabilitas gabungan melampaui 
        ambang batas keyakinan minimum:
        """)
        st.latex(r"\hat{P}(Y=1|X) \ge 0.55 \quad (55\%)")

        st.markdown("""
        ### 3.5 Jendela Pelatihan Rolling 2 Tahun (Adaptasi Rezim Pasar)
        Model dilatih menggunakan jendela data bergulir (*rolling window*) **2 tahun (~500 hari bursa aktif)**. 
        Hal ini krusial untuk:
        - Membuang struktur data usang dari rezim ekonomi masa lampau yang tidak lagi relevan.
        - Beradaptasi secara lincah terhadap siklus komoditas mineral dan kebijakan suku bunga Bank Indonesia terkini.
        - Menghindari *memory distortion* yang kerap terjadi pada jendela data statis 10 tahun.
        """)

    # ----------------------------------------------------------------------------------
    # BAB 4: PENENTUAN TARGET WAKTU (DYNAMIC HOLDING HORIZON & FIRST-PASSAGE TIME)
    # ----------------------------------------------------------------------------------
    with st.expander("⏳ 4. Metodologi Target Waktu: Teori First-Passage Time (FPT)", expanded=True):
        st.markdown(r"""
        ### 4.1 Mengapa Target Waktu Berbeda untuk Setiap Saham?
        Banyak pelaku pasar keliru mengasumsikan bahwa semua saham memiliki jangka waktu ayunan (*swing horizon*) yang seragam. 
        Secara empiris, saham berkarakter likuiditas tinggi seperti **TINS** memiliki target holding **7 hari**, 
        sedangkan saham manufaktur defensif seperti **AUTO** memerlukan waktu **9 hari**.

        Perbedaan ini dijelaskan secara matematis melalui teori proses stokastik **First-Passage Time (FPT)**.

        ### 4.2 Dinamika Stokastik: Geometric Brownian Motion (GBM)
        Lintasan harga saham diasumsikan mengikuti persamaan diferensial stokastik dengan drift $\mu$ dan volatilitas $\sigma$:
        """)
        st.latex(r"dS_t = \mu S_t dt + \sigma S_t dW_t")
        st.caption(r"di mana $W_t$ adalah proses Wiener standar (Gerak Brown).")

        st.markdown(r"""
        ### 4.3 Formulasi Waktu Capai Pertama (*First-Passage Time*)
        Waktu acak $\tau$ di mana harga saham pertama kali menembus ambang keuntungan target $\Delta_{\text{target}}$ 
        didefinisikan sebagai *stopping time*:
        """)
        st.latex(r"\tau = \inf \Big\{ t > 0 : S_t \ge S_0 (1 + \Delta_{\text{target}}) \Big\}")
        st.markdown("""
        Waktu transit ini mengikuti distribusi *Inverse Gaussian (Wald Distribution)* dengan nilai ekspektasi:
        """)
        st.latex(r"\mathbb{E}[\tau] = \frac{\ln(1 + \Delta_{\text{target}})}{\mu - \frac{1}{2}\sigma^2}")
        st.markdown(r"""
        **Implikasi Matematis:**
        - Saham dengan volatilitas terarah ($\sigma$) yang tinggi akan menembus batas target $\Delta_{\text{target}}$ 
          dalam waktu transit yang lebih singkat ($\tau$ kecil $\rightarrow 5 - 7$ hari).
        - Saham dengan volatilitas rendah membutuhkan difusi kumulatif yang lebih lama ($\tau$ besar $\rightarrow 9 - 14$ hari).
        
        Model 18 menghitung nilai median historis $\tau$ dari seluruh siklus ayunan berhasil pada 2 tahun terakhir 
        untuk menetapkan **Target Waktu (Holding Days)** yang unik dan realistis bagi masing-masing emiten:
        """)
        st.latex(r"H_{\text{dynamic}} = \text{Median}\Big(\tau_1, \tau_2, \dots, \tau_k\Big)")

    # ----------------------------------------------------------------------------------
    # BAB 5: PROTOKOL MANAJEMEN RISIKO INSTITUSIONAL (RISK MANAGEMENT)
    # ----------------------------------------------------------------------------------
    with st.expander("🛡️ 5. Protokol Manajemen Risiko Institusional & Asymmetric Payoff", expanded=True):
        st.markdown(r"""
        ### 5.1 Nilai Harapan Matematis Positif (*Positive Expected Value*)
        Keberhasilan finansial portofolio jangka panjang ditentukan oleh nilai harapan matematis $\mathbb{E}[\mathcal{R}]$:
        """)
        st.latex(r"\mathbb{E}[\mathcal{R}] = \Big( P_{\text{win}} \times R_{\text{win}} \Big) - \Big( (1 - P_{\text{win}}) \times R_{\text{loss}} \Big)")
        st.markdown(r"""
        Agar $\mathbb{E}[\mathcal{R}] > 0$ secara konsisten dalam jangka panjang, Modul 18 menegakkan dua syarat batas asimetris:
        """)
        st.markdown("**Syarat Batas 1: Probabilitas Kemenangan Minimal**")
        st.latex(r"P_{\text{win}} \ge 0.55 \quad (55\%)")
        st.markdown("**Syarat Batas 2: Asimetri Risk-to-Reward Minimum 1 banding 1.5**")
        st.latex(r"\text{R:R} = \frac{R_{\text{win}}}{R_{\text{loss}}} \ge 1.50")

        st.markdown("""
        ### 5.2 Pembatasan Risiko Ketat: Hard Stop Loss 5.5%
        Batas risiko (*Stop Loss*) dihitung secara dinamis berbasis volatilitas ATR pasar, namun **dikunci oleh batas absolut institusional (*Hard Cap*) maksimal 5.5%**:
        """)
        st.latex(r"\text{Stop Loss} = \min\Big(\text{ATR-Based Volatility Stop}, \; 5.5\%\Big)")
        st.markdown("""
        Hal ini mencegah risiko kehancuran modal (*Risk of Ruin*) apabila terjadi peristiwa luar biasa (*Black Swan event*) 
        pada bursa.

        ### 5.3 Protokol Ticker Lockout & Jeda Karantina (*Injury Time*)
        Jika suatu saham mengalami penurunan harga yang menyentuh level Stop Loss, algoritma secara otomatis 
        mengaktifkan **Ticker Lockout Protocol**:
        - Saham tersebut **dikarantina selama 3 hingga 5 hari bursa**.
        - Radar dilarang menerbitkan sinyal beli baru pada emiten tersebut meskipun harganya tampak murah (*avoiding catching falling knives*).
        - Menghilangkan dorongan psikologis *revenge trading* dan memastikan struktur tren telah kembali stabil sebelum modal baru dialokasikan.
        """)

    # ----------------------------------------------------------------------------------
    # BAB 6: PANDUAN PENGGUNAAN & CARA MEMBACA TERMINAL
    # ----------------------------------------------------------------------------------
    with st.expander("📖 6. Panduan Praktis & Cara Membaca Output Terminal", expanded=True):
        st.markdown(r"""
        ### 6.1 Cara Membaca Kolom pada Tabel Radar Eksekutif
        Ketika membuka tab **🎯 Radar Keputusan Eksekutif**, pengguna disajikan kolom-kolom analitik berikut:

        | Kolom | Arti & Penjelasan | Pedoman Tindakan |
        | :--- | :--- | :--- |
        | **Ticker & Nama Emiten** | Kode bursa saham 4 huruf beserta nama lengkap perseroan. | Verifikasi profil likuiditas dan fundamental emiten. |
        | **Harga Terakhir (Rp)** | Harga penutupan pasar reguler terakhir yang berhasil dicatat. | Level patokan harga saat eksekusi beli di pasar. |
        | **Modal 1 Lot (Rp)** | Kebutuhan dana tunai untuk membeli 1 lot (100 lembar) saham. | Digunakan untuk perhitungan ukuran posisi (*position sizing*). |
        | **Probabilitas Naik (%)** | Keyakinan gabungan model Dual-Ensemble ($\ge 55\%$). | Semakin tinggi di atas 55%, semakin kuat sinyal beli. |
        | **Take Profit / TP (Rp)** | Level harga target pelepasan profit yang dihitung dari volatilitas. | Pasang order jual otomatis (*profit taking*) pada level ini. |
        | **Stop Loss / SL (Rp)** | Level proteksi pemotongan kerugian maksimal ($\le 5.5\%$). | Wajib dipasang di aplikasi sekuritas sebagai jaring pengaman. |
        | **Target Waktu (Hari)** | Estimasi durasi ayunan (*holding days*) berbasis First-Passage Time. | Evaluasi saham jika hingga batas hari ini target belum tercapai. |
        | **Risk / Reward** | Rasio antara potensi keuntungan terhadap risiko kerugian. | Wajib bernilai $\ge 1.50$ untuk menjamin asimetri laba. |
        | **Rekomendasi** | Status keputusan: **STRONG BUY** atau **WAIT & SEE**. | Eksekusi hanya jika statusnya bernilai **STRONG BUY**. |

        ### 6.2 Empat Aturan Emas Disiplin Eksekusi
        1. **Disiplin Sinyal:** Jangan pernah membeli saham yang berstatus *Wait & See*, betapapun menariknya berita di media.
        2. **Alokasi Modal Seimbang:** Jangan menempatkan lebih dari 10% – 15% dari total portofolio Anda pada satu saham saja.
        3. **Pasang Stop Loss Otomatis:** Begitu order beli Anda terpenuhi di bursa, langsung pasang order *Automatic Stop Loss (GTC - Good 'Til Cancelled)* pada level SL yang tertera.
        4. **Keluar Tepat Waktu:** Realisasikan laba begitu harga menyentuh target Take Profit (TP), atau tutup posisi saat batas hari target waktu telah habis dan momentum melemah.
        """)

    # ----------------------------------------------------------------------------------
    # BAB 7: KESIMPULAN EKSEKUTIF & DISCLAIMER HUKUM
    # ----------------------------------------------------------------------------------
    with st.expander("⚖️ 7. Kesimpulan Model & Batasan Tanggung Jawab (Disclaimer)", expanded=True):
        st.markdown("""
        ### 7.1 Kesimpulan Eksekutif
        Modul 18 *The Trilaksana Mining Suite* merepresentasikan sinergi antara **keuangan kuantitatif**, 
        **pemodelan stokastik**, dan **machine learning modern**. Dengan mengombinasikan keunggulan probabilitas 
        Random Forest dan Gradient Boosting, perlindungan *Hard Stop Loss 5.5%*, serta estimasi target waktu 
        *First-Passage Time*, sistem ini menyediakan instrumen pendukung keputusan (*Decision Support System*) 
        yang kokoh, terukur, dan bebas dari bias emosional manusia.

        ### 7.2 Pernyataan Kepatuhan & Disclaimer Finansial
        - **Bukan Jaminan Hasil di Masa Depan:** Kinerja historis dan akurasi backtesting tidak menjamin hasil perdagangan di masa mendatang. Kondisi pasar modal dapat mengalami anomali di luar cakupan distribusi data masa lalu.
        - **Instrumen Pendukung Keputusan:** Seluruh sinyal, probabilitas, dan target harga yang diterbitkan oleh sistem ini bersifat informasi analitik dan edukasi kuantitatif. Keputusan akhir untuk melakukan transaksi sepenuhnya berada pada diskresi dan tanggung jawab masing-masing investor.
        - **Manajemen Modal Pribadi:** Pengguna disarankan untuk selalu berkonsultasi dengan penasihat keuangan berizin dan menerapkan manajemen risiko portofolio secara bijaksana sesuai profil risiko masing-masing.
        """)

    st.markdown("""
    <div style="text-align: center; color: #64748b; font-size: 12px; margin-top: 30px; padding-top: 15px; border-top: 1px solid #334155;">
        The Trilaksana Mining Suite • Modul 18: Quantitative Stock Intelligence Terminal<br>
        Didesain & Dikembangkan oleh Dr. Ir. Ahmad Raymond Trilaksana &bull; Hak Cipta Dilindungi Undang-Undang
    </div>
    """, unsafe_allow_html=True)
