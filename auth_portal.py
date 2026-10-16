import streamlit as st
import time
from core.cloud_auth import (
    APP_ID,
    APP_NAME,
    check_license,
    login_online,
    get_hardware_id,
    clear_local_license,
    is_cloud_hosted,
    notify_online_visitor_async,
)


def check_authentication(module_title=None):
    """
    Unified Cloud Authentication & Licensing Gate
    Powered by www.trilaksanamining.my.id & Telegram Bot Integration
    - Versi Live Online (Streamlit Cloud): Akses langsung tanpa login + Telemetri Telegram otomatis.
    - Versi Desktop (.EXE): Wajib Login Online dengan Akun Resmi & HWID Licensing (7-Day Offline Grace).
    """
    if module_title is None:
        module_title = APP_NAME

    # 1. Untuk Versi Live Online (Streamlit Cloud): Langsung Masuk + Kirim Telemetri ke Telegram
    if is_cloud_hosted():
        if not st.session_state.get("tg_initial_visit_notified"):
            st.session_state["tg_initial_visit_notified"] = True
            notify_online_visitor_async(
                visitor_name="Pengunjung Live Online",
                visitor_email="Akses Terbuka Cloud",
                visitor_company="Publik / Klien / Investor",
                event_title="👀 *PENGUNJUNG MEMBUKA LIVE SHOW ONLINE — MODUL 18*",
                extra_detail="Membuka Dashboard Live Show Modul 18 (Streamlit Cloud)",
            )
        return True

    # 2. Jika sudah login di sesi desktop ini
    if st.session_state.get("authenticated") and st.session_state.get("lic_user"):
        return True

    # 3. Untuk versi Desktop (.EXE), periksa cache lisensi lokal 7 hari
    lic_status = check_license(silent_refresh=True)
    if lic_status.get("authenticated"):
        st.session_state["authenticated"] = True
        st.session_state["logged_in"] = True
        st.session_state["lic_user"] = lic_status.get("user", {})
        st.session_state["lic_mode"] = lic_status.get("mode", "online")
        st.session_state["username"] = lic_status.get("user", {}).get("fullName", "Investor / Engineer")
        return True

    # 4. Tampilkan Gerbang Login Wajib untuk Versi Desktop (.EXE)
    hwid = get_hardware_id()
    st.markdown(
        f"""
    <div style="background: linear-gradient(135deg, #090d16 0%, #111827 50%, #1e293b 100%); padding: 32px 24px; border-radius: 16px; border: 1px solid #334155; text-align: center; margin-bottom: 24px; box-shadow: 0 12px 35px rgba(0,0,0,0.6);">
        <div style="display: inline-block; padding: 5px 15px; background: rgba(34, 197, 94, 0.15); border: 1px solid #22c55e; border-radius: 30px; color: #22c55e; font-size: 11px; font-weight: 700; letter-spacing: 2px; margin-bottom: 12px; text-transform: uppercase;">
            CENTRAL CLOUD LICENSING &bull; MODUL 18 TRILAKSANA SUITE
        </div>
        <h1 style="color: #ffffff; font-size: 28px; font-weight: 800; margin: 0 0 6px 0; letter-spacing: -0.5px;">THE TRILAKSANA FRAMEWORK — MODUL 18</h1>
        <div style="color: #94a3b8; font-size: 14px; margin-bottom: 16px; font-weight: 500;">
            Quantitative Stock Price Prediction &amp; Dynamic Screener Suite &bull; Dr. Ir. Ahmad Raymond Trilaksana
        </div>
        <div style="background: rgba(255, 255, 255, 0.04); border-left: 3px solid #22c55e; border-radius: 6px; padding: 12px 18px; font-size: 13px; color: #cbd5e1; max-width: 680px; margin: 0 auto; text-align: left; line-height: 1.5;">
            🔒 <b>Autentikasi Lisensi Desktop (.EXE):</b> Aplikasi mandiri ini terhubung langsung ke Server Lisensi <a href="https://www.trilaksanamining.my.id" target="_blank" style="color: #38bdf8;">www.trilaksanamining.my.id</a> &amp; Bot Telegram. Silakan login menggunakan akun resmi Anda untuk mengaktifkan perangkat.
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    col_l, col_center, col_r = st.columns([1, 2, 1])
    with col_center:
        st.markdown(
            f"""
        <div style="background: rgba(30, 41, 59, 0.9); border: 1px solid rgba(34, 197, 94, 0.4); border-radius: 12px; padding: 16px; text-align: center; margin-bottom: 16px;">
            <div style="font-size: 14px; font-weight: 700; color: #ffffff; margin-bottom: 4px;">
                Masuk Menggunakan Akun Resmi Portal www.trilaksanamining.my.id
            </div>
            <div style="font-size: 12px; color: #94a3b8; margin-bottom: 10px;">
                Perangkat Terkunci Hardware ID: <code>{hwid}</code>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        with st.form("desktop_login_form"):
            email_input = st.text_input("Alamat Email Akun Portal:", placeholder="contoh: user@trilaksanamining.my.id")
            pass_input = st.text_input("Password:", type="password", placeholder="Masukkan password Anda")
            submitted = st.form_submit_button("🔐 VERIFIKASI LISENSI ONLINE (.EXE)", type="primary", use_container_width=True)

            if submitted:
                if not email_input.strip() or not pass_input:
                    st.error("Email dan password wajib diisi!")
                else:
                    with st.spinner("Memverifikasi lisensi ke Server www.trilaksanamining.my.id..."):
                        res = login_online(email_input.strip(), pass_input)
                        if res.get("success"):
                            st.session_state["authenticated"] = True
                            st.session_state["logged_in"] = True
                            st.session_state["lic_user"] = res.get("user", {})
                            st.session_state["lic_mode"] = "online"
                            st.session_state["username"] = res.get("user", {}).get("fullName", email_input)
                            notify_online_visitor_async(
                                visitor_name=res.get("user", {}).get("fullName", email_input),
                                visitor_email=email_input.strip(),
                                visitor_company=res.get("user", {}).get("company", "-"),
                                event_title="🔐 *LOGIN SUKSES DESKTOP .EXE — MODUL 18*",
                                extra_detail=f"Login Desktop Windows HWID: {hwid}",
                            )
                            st.success(f"✅ {res.get('message', 'Lisensi Desktop Berhasil Diverifikasi!')}")
                            time.sleep(0.6)
                            st.rerun()
                        else:
                            notify_online_visitor_async(
                                visitor_name=email_input.strip(),
                                visitor_email=email_input.strip(),
                                visitor_company="Percobaan Login Gagal",
                                event_title="⚠️ *LOGIN GAGAL DESKTOP .EXE — MODUL 18*",
                                extra_detail=f"Percobaan login gagal untuk HWID: {hwid}",
                            )
                            st.error(f"❌ {res.get('message', 'Autentikasi gagal.')}")

    st.stop()


def render_auth_sidebar():
    """
    Renders authenticated user badge in sidebar.
    """
    if is_cloud_hosted():
        st.sidebar.markdown(
            """
        <div style="background: rgba(34, 197, 94, 0.1); border: 1px solid rgba(34, 197, 94, 0.3); border-radius: 8px; padding: 10px; margin-bottom: 12px; font-size: 11.5px;">
            <div style="color: #22c55e; font-weight: 700;">🌐 LIVE ONLINE CLOUD MODE</div>
            <div style="color: #94a3b8; font-size: 10.5px; margin-top: 2px;">Trilaksana Suite &bull; Terkoneksi Telegram Telemetry</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
        return

    u_info = st.session_state.get("lic_user", {})
    full_name = u_info.get("fullName", st.session_state.get("username", "Investor"))
    email = u_info.get("email", "-")
    company = u_info.get("company", "PT Trilaksana Mineral Nusantara")
    hwid = u_info.get("hwid", get_hardware_id())
    mode = st.session_state.get("lic_mode", "online")

    st.sidebar.markdown(
        f"""
    <div style="background: rgba(30, 41, 59, 0.85); border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 10px; padding: 12px; margin-bottom: 14px;">
        <div style="font-size: 11px; text-transform: uppercase; color: #38bdf8; font-weight: 700; letter-spacing: 1px;">
            🔐 LISENSI DESKTOP AKTIF
        </div>
        <div style="font-size: 13px; font-weight: 700; color: #ffffff; margin-top: 3px;">
            {full_name}
        </div>
        <div style="font-size: 11px; color: #94a3b8;">
            {company}
        </div>
        <div style="font-size: 10px; font-family: monospace; color: #64748b; margin-top: 4px;">
            {hwid}
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    if st.sidebar.button("🚪 Keluar Akun (Logout)", use_container_width=True):
        clear_local_license()
        st.session_state["authenticated"] = False
        st.session_state["logged_in"] = False
        st.session_state.pop("lic_user", None)
        st.rerun()
