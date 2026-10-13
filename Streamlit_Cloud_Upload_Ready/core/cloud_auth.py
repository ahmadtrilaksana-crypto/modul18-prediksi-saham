"""
cloud_auth.py — Client-Side Authentication & 7-Day Offline Grace-Period Engine
Connected to www.trilaksanamining.my.id (Google Apps Script Cloud Backend)
Telegram Bot Integration & Geolocation Telemetry
Modul 17: Intelijen Ekonometrika Makro-Tambang, Hilirisasi & Proyeksi PDB

Author: Dr. Ir. Ahmad Raymond Trilaksana, S.T., M.Ak., IPM, ASEAN Eng. (ahmad.trilaksana@gmail.com)
License: Proprietary / www.trilaksanamining.my.id & PT Aneka Tambang Tbk
"""

import os
import sys
import json
import time
import uuid
import hashlib
import platform
import urllib.request
import urllib.parse
from datetime import datetime, date
from typing import Dict, Any, Optional

CLOUD_API_URL = "https://script.google.com/macros/s/AKfycbxSSQexztexwacy7pI1febIt8mokXSE9DZa_ik70-XONV4DG2opFuUnIyvmQo9FKoKj1Q/exec"
APP_ID = 18
APP_NAME = "Modul 18: Quantitative Stock Price Prediction & Dynamic Screener Suite"
GRACE_PERIOD_DAYS = 7


def get_hardware_id() -> str:
    try:
        node_id = str(uuid.getnode())
        system_info = f"{platform.node()}|{platform.machine()}|{platform.processor()}|{node_id}"
        hwid_hash = hashlib.sha256(system_info.encode("utf-8")).hexdigest()[:16].upper()
        return f"HWID-{hwid_hash[:4]}-{hwid_hash[4:8]}-{hwid_hash[8:12]}-{hwid_hash[12:16]}"
    except Exception:
        return "HWID-DEFAULT-WIN-PC"


def get_license_store_path() -> str:
    appdata = os.environ.get("APPDATA")
    if appdata and os.path.exists(appdata):
        folder = os.path.join(appdata, "TrilaksanaMiningSuite")
    else:
        folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".license")

    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, f"license_app{APP_ID}.json")


def _save_local_license(data: Dict[str, Any]) -> None:
    path = get_license_store_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[AUTH ERROR] Failed to save local license: {e}")


def _load_local_license() -> Optional[Dict[str, Any]]:
    path = get_license_store_path()
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def clear_local_license() -> None:
    path = get_license_store_path()
    if os.path.exists(path):
        try:
            os.remove(path)
        except Exception:
            pass


def _http_get(url: str, timeout: int = 10) -> Optional[Dict[str, Any]]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "TrilaksanaMiningSuite/2.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content = resp.read().decode("utf-8")
            return json.loads(content)
    except Exception:
        return None


_LAST_NOTIFIED_TIME = 0


def get_network_info() -> Dict[str, str]:
    try:
        req = urllib.request.Request(
            "http://ip-api.com/json/?fields=status,message,country,regionName,city,isp,query",
            headers={"User-Agent": "Mozilla/5.0"},
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("status") == "success":
                city = data.get("city", "")
                region = data.get("regionName", "")
                loc = f"{city}, {region}" if (city and region) else (city or region or data.get("country", "Indonesia"))
                return {
                    "ip": data.get("query", "Unknown IP"),
                    "location": loc,
                    "isp": data.get("isp", "Internet Provider"),
                }
    except Exception:
        pass

    try:
        req2 = urllib.request.Request("https://api.ipify.org?format=json", headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req2, timeout=2) as resp2:
            data2 = json.loads(resp2.read().decode("utf-8"))
            return {
                "ip": data2.get("ip", "IP Terdeteksi"),
                "location": "Indonesia (Site Tambang)",
                "isp": "Koneksi Satelit / Seluler",
            }
    except Exception:
        pass

    return {
        "ip": "Mode Offline (No Internet)",
        "location": "Site Tambang (Remote Area)",
        "isp": "Koneksi Lokal Offline",
    }


def is_cloud_hosted() -> bool:
    """Mendeteksi apakah aplikasi berjalan di server cloud (Streamlit Community Cloud / Linux Server)."""
    if os.path.exists("/mount/src") or os.environ.get("STREAMLIT_SHARING_MODE") or os.environ.get("IS_STREAMLIT_CLOUD"):
        return True
    if sys.platform.startswith("linux") and not getattr(sys, "frozen", False):
        return True
    return False


def notify_online_visitor_async(
    visitor_name: str = "Pengunjung Web",
    visitor_email: str = "-",
    visitor_company: str = "Publik / Akademisi / Praktisi",
    event_title: str = "🌐 DETEKSI AKSES LIVE SHOW ONLINE — MODUL 18",
    extra_detail: str = "Membuka Dashboard Online Live Show (Streamlit Cloud)",
):
    """Mengirim notifikasi real-time ke Telegram Inovator setiap ada yang mengakses atau menggunakan Modul 17 Online."""
    import threading

    def _worker():
        try:
            net_info = get_network_info()
            ip = net_info.get("ip", "IP Cloud")
            loc = net_info.get("location", "Indonesia / Global")
            isp = net_info.get("isp", "Cloud Network")
            now_str = datetime.now().strftime("%d-%b-%Y %H:%M WIB")
            platform_mode = "🌐 Streamlit Cloud (Online Live Show)" if is_cloud_hosted() else "💻 Desktop / Local Server"

            tg_text = (
                f"{event_title}\n"
                "────────────────────────────\n"
                f"👤 *Pengguna:* {visitor_name} (`{visitor_email}`)\n"
                f"🏢 *Instansi:* {visitor_company}\n"
                f"📦 *Modul:* {APP_NAME}\n"
                f"🖥️ *Platform:* {platform_mode}\n"
                f"📌 *Aktivitas:* {extra_detail}\n"
                f"🌐 *IP & Lokasi:* `{ip}` ({loc} — {isp})\n"
                f"🕒 *Waktu:* {now_str}"
            )
            tg_url = "https://api.telegram.org/bot8560004508:AAEnTCSQwN8pM6B58dNCqsKXWvINKrX20OU/sendMessage"
            tg_data = json.dumps({
                "chat_id": "1604993430",
                "text": tg_text,
                "parse_mode": "Markdown",
            }).encode("utf-8")
            tg_req = urllib.request.Request(tg_url, data=tg_data, headers={"Content-Type": "application/json"})
            urllib.request.urlopen(tg_req, timeout=5)
        except Exception:
            pass

    threading.Thread(target=_worker, daemon=True).start()


def notify_usage_async(user_dict: Optional[Dict[str, Any]] = None, mode: str = "Online", force: bool = False):
    import threading

    global _LAST_NOTIFIED_TIME
    now = time.time()
    if not force and (now - _LAST_NOTIFIED_TIME < 1800):
        return

    _LAST_NOTIFIED_TIME = now
    if not user_dict:
        user_dict = _load_local_license() or {}

    def _worker():
        try:
            net_info = get_network_info()
            hwid = get_hardware_id()

            if "No Internet" in net_info.get("ip", ""):
                return

            email = user_dict.get("email", "")
            fullName = user_dict.get("fullName", "Engineer")
            company = user_dict.get("company", "PT Trilaksana Mineral Nusantara")
            ip = net_info.get("ip", "IP Tidak Terdeteksi")
            loc = net_info.get("location", "Indonesia")
            isp = net_info.get("isp", "Provider Internet")
            now_str = datetime.now().strftime("%d-%b-%Y %H:%M WIB")
            header_tag = (
                "🌐 *DETEKSI PEMAKAIAN LIVE SHOW ONLINE (MODUL 18)*"
                if is_cloud_hosted()
                else "🛰️ *DETEKSI PEMAKAIAN SOFTWARE SAHAM (.EXE)*"
            )

            try:
                tg_text = (
                    f"{header_tag}\n"
                    "────────────────────────────\n"
                    f"👤 *Engineer:* {fullName} (`{email}`)\n"
                    f"🏢 *Perusahaan:* {company}\n"
                    f"📦 *Software:* {APP_NAME}\n"
                    f"💻 *Perangkat:* `{hwid}`\n"
                    f"🌐 *Alamat IP:* `{ip}`\n"
                    f"📡 *Provider / ISP:* {isp}\n"
                    f"📍 *Lokasi:* {loc}\n"
                    f"🕒 *Waktu Akses:* {now_str}\n"
                    f"📌 *Status:* {mode}"
                )
                tg_url = "https://api.telegram.org/bot8560004508:AAEnTCSQwN8pM6B58dNCqsKXWvINKrX20OU/sendMessage"
                tg_data = json.dumps({
                    "chat_id": "1604993430",
                    "text": tg_text,
                    "parse_mode": "Markdown",
                }).encode("utf-8")
                tg_req = urllib.request.Request(tg_url, data=tg_data, headers={"Content-Type": "application/json"})
                urllib.request.urlopen(tg_req, timeout=5)
            except Exception:
                pass

            try:
                params = urllib.parse.urlencode({
                    "action": "log_app_usage",
                    "email": email,
                    "fullName": fullName,
                    "company": company,
                    "appId": APP_ID,
                    "appName": APP_NAME,
                    "hwid": hwid,
                    "ip": ip,
                    "location": loc,
                    "isp": isp,
                    "mode": mode,
                })
                _http_get(f"{CLOUD_API_URL}?{params}", timeout=6)
            except Exception:
                pass
        except Exception:
            pass

    t = threading.Thread(target=_worker, daemon=True)
    t.start()


def login_online(email: str, password: str) -> Dict[str, Any]:
    email = email.strip().lower()
    hwid = get_hardware_id()

    # Emergency Offline Master Passwords (Fail-Safe for Competitions / No Internet)
    offline_master_creds = {
        "ahmad.trilaksana@gmail.com": ["Munjul23#", "superadmin", "trilaksana2026"],
        "ahmad.trilaksana@antam.com": ["Munjul23#", "antam2026", "superadmin"],
        "mahesa@pongkeru.com": ["mahesa123", "pomu2026"],
        "mahesa": ["mahesa123", "pomu2026"],
        "raymond": ["superadmin", "Munjul23#"],
        "antam": ["antam2026"],
        "pomu": ["pomu2026"],
        "bigmind": ["bigmind2026"],
        "juri": ["bigmind2026"],
    }

    params = urllib.parse.urlencode({
        "action": "verify_license",
        "email": email,
        "password": password,
        "appId": APP_ID,
        "hwid": hwid,
    })

    endpoint = f"{CLOUD_API_URL}?{params}"
    data = _http_get(endpoint, timeout=12)

    # If online success:
    if data and data.get("status") == "success":
        user = data.get("user", {})
        now_ts = int(time.time())
        cache_payload = {
            "userId": user.get("userId"),
            "fullName": user.get("fullName"),
            "email": user.get("email"),
            "company": user.get("company"),
            "role": user.get("role"),
            "status": user.get("status"),
            "allowedApps": user.get("allowedApps"),
            "validUntil": user.get("validUntil"),
            "appId": APP_ID,
            "hwid": hwid,
            "lastVerifiedOnline": now_ts,
            "lastVerifiedDate": datetime.fromtimestamp(now_ts).strftime("%Y-%m-%d %H:%M:%S"),
            "gracePeriodDays": GRACE_PERIOD_DAYS,
            "offlineToken": data.get("offlineToken", ""),
        }
        _save_local_license(cache_payload)
        notify_usage_async(cache_payload, mode="Login Online (Cloud Google)", force=True)
        return {
            "success": True,
            "mode": "online",
            "message": f"Selamat datang, {user.get('fullName')}! Lisensi {APP_NAME} aktif.",
            "user": user,
            "gracePeriodDays": GRACE_PERIOD_DAYS,
        }

    # If Cloud Server rejected with specific message (e.g. wrong password or appId 17 not yet in sheet):
    if data and data.get("status") == "error":
        if email in offline_master_creds and password in offline_master_creds[email]:
            now_ts = int(time.time())
            cache_payload = {
                "userId": "USR-VIP-ADMIN",
                "fullName": (
                    "Dr. Ir. Ahmad Raymond Trilaksana, S.T., M.Ak., IPM, ASEAN Eng."
                    if "trilaksana" in email or "raymond" in email
                    else "Innovator Tim POMU"
                ),
                "email": email,
                "company": "PT Antam Tbk & PT Pongkeru Mineral Utama",
                "role": "Superadmin",
                "status": "active",
                "allowedApps": "ALL",
                "validUntil": "2030-12-31",
                "appId": APP_ID,
                "hwid": hwid,
                "lastVerifiedOnline": now_ts,
                "lastVerifiedDate": datetime.fromtimestamp(now_ts).strftime("%Y-%m-%d %H:%M:%S"),
                "gracePeriodDays": GRACE_PERIOD_DAYS,
                "offlineToken": "OFFLINE-MASTER-BYPASS",
            }
            _save_local_license(cache_payload)
            notify_usage_async(cache_payload, mode="Login Master Fail-Safe", force=True)
            return {
                "success": True,
                "mode": "offline_master",
                "message": f"Akses Master Terverifikasi! Lisensi {APP_NAME} aktif.",
                "user": cache_payload,
                "gracePeriodDays": GRACE_PERIOD_DAYS,
            }
        return {
            "success": False,
            "message": data.get("message", "Autentikasi gagal."),
        }

    # If connection failed (offline / no internet):
    if email in offline_master_creds and password in offline_master_creds[email]:
        now_ts = int(time.time())
        cache_payload = {
            "userId": "USR-OFFLINE-MASTER",
            "fullName": (
                "Dr. Ir. Ahmad Raymond Trilaksana, S.T., M.Ak., IPM, ASEAN Eng."
                if "trilaksana" in email or "raymond" in email
                else "Innovator Tim POMU"
            ),
            "email": email,
            "company": "PT Antam Tbk & PT Pongkeru Mineral Utama",
            "role": "Superadmin",
            "status": "active",
            "allowedApps": "ALL",
            "validUntil": "2030-12-31",
            "appId": APP_ID,
            "hwid": hwid,
            "lastVerifiedOnline": now_ts,
            "lastVerifiedDate": datetime.fromtimestamp(now_ts).strftime("%Y-%m-%d %H:%M:%S"),
            "gracePeriodDays": GRACE_PERIOD_DAYS,
            "offlineToken": "OFFLINE-MASTER-BYPASS",
        }
        _save_local_license(cache_payload)
        return {
            "success": True,
            "mode": "offline",
            "message": f"Mode Offline Master Terverifikasi! Lisensi {APP_NAME} aktif.",
            "user": cache_payload,
            "gracePeriodDays": GRACE_PERIOD_DAYS,
        }

    return {
        "success": False,
        "message": "Gagal terhubung ke Cloud Server www.trilaksanamining.my.id. Periksa koneksi internet Anda.",
    }


def check_license(silent_refresh: bool = True) -> Dict[str, Any]:
    cached = _load_local_license()
    current_hwid = get_hardware_id()
    now_ts = int(time.time())

    if not cached:
        return {
            "authenticated": False,
            "reason": "NO_LICENSE",
            "message": "Silakan login menggunakan akun terdaftar di www.trilaksanamining.my.id",
        }

    if cached.get("hwid") != current_hwid:
        return {
            "authenticated": False,
            "reason": "HWID_MISMATCH",
            "message": "Lisensi ini terikat pada perangkat komputer lain. Silakan login kembali pada perangkat ini.",
        }

    valid_until_str = cached.get("validUntil", "")
    if valid_until_str:
        try:
            exp_date = datetime.strptime(valid_until_str, "%Y-%m-%d").date()
            if exp_date < date.today():
                return {
                    "authenticated": False,
                    "reason": "EXPIRED",
                    "message": f"Masa aktif lisensi Anda telah berakhir pada {valid_until_str}. Silakan perpanjang di www.trilaksanamining.my.id",
                }
        except Exception:
            pass

    last_verified = cached.get("lastVerifiedOnline", 0)
    elapsed_seconds = now_ts - last_verified
    elapsed_days = elapsed_seconds / 86400.0
    remaining_days = max(0.0, round(GRACE_PERIOD_DAYS - elapsed_days, 1))

    online_success = False
    if silent_refresh:
        try:
            ping = _http_get(f"{CLOUD_API_URL}?action=ping", timeout=3)
            if ping and ping.get("status") == "success":
                cached["lastVerifiedOnline"] = now_ts
                cached["lastVerifiedDate"] = datetime.fromtimestamp(now_ts).strftime("%Y-%m-%d %H:%M:%S")
                _save_local_license(cached)
                online_success = True
                remaining_days = float(GRACE_PERIOD_DAYS)
        except Exception:
            online_success = False

    if online_success:
        notify_usage_async(cached, mode="Buka Aplikasi (Online)")
        return {
            "authenticated": True,
            "mode": "online",
            "remainingGraceDays": GRACE_PERIOD_DAYS,
            "user": cached,
            "message": "Lisensi Aktif (Online Terverifikasi - Cloud Google)",
        }
    elif elapsed_days <= GRACE_PERIOD_DAYS:
        notify_usage_async(cached, mode="Buka Aplikasi (Mode Lapangan 7 Hari)")
        return {
            "authenticated": True,
            "mode": "offline",
            "remainingGraceDays": remaining_days,
            "user": cached,
            "message": f"Lisensi Aktif (Mode Lapangan/Offline: Sisa {remaining_days} hari)",
        }
    else:
        return {
            "authenticated": False,
            "reason": "GRACE_EXPIRED",
            "message": f"Masa tenggang offline ({GRACE_PERIOD_DAYS} hari) telah habis. Silakan hubungkan laptop ke internet untuk verifikasi ulang.",
        }
