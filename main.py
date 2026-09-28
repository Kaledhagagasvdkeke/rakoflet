import urllib3
urllib3.disable_warnings()
import requests
import threading
import time
import hashlib
import flet as ft

BOT_TOKEN = "8912753675:AAHDx7R0qRDLRz0XGssxSLxSveuuQzmHnMo"

# 🔴🔴 اكتب الـ ID الخاص بالمستخدم هنا 
USER_CHAT_ID = "1663809859"  

SECRET_CHANNEL = hashlib.md5(f"sama3ni_sync_{USER_CHAT_ID}".encode()).hexdigest()

def send_tg_message(text):
    try: 
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": USER_CHAT_ID, "text": text, "parse_mode": "Markdown"}, timeout=5)
    except: 
        pass

def engine_loop(page: ft.Page, status_text: ft.Text):
    user = None
    pwd = None
    
    # 1. انتظار استقبال البيانات من البوت
    while not user:
        try:
            r = requests.get(f"https://ntfy.sh/{SECRET_CHANNEL}/json?poll=1", timeout=10)
            lines = r.text.strip().split('\n')
            if lines and lines[-1]:
                import json
                last_msg = json.loads(lines[-1])
                if last_msg.get('event') == 'message' and '||' in last_msg.get('message', ''):
                    creds = last_msg['message'].split('||')
                    user, pwd = creds[0], creds[1]
                    
                    # تحديث الواجهة عند الاتصال
                    status_text.value = "✅ المحرك يعمل الآن بـ IP هاتفك!"
                    status_text.color = ft.colors.GREEN
                    status_text.update()
                    
                    send_tg_message("🚀 **تطبيق الموبايل متصل الآن!**\nاذهب للبوت واضغط (شراء رنج) أو اترك الأرقام تتجدد تلقائياً.")
                    break
        except: 
            pass
        time.sleep(3)

    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (Android; Mobile)"})
    session.post("https://www.sama3ni.com/api/auth/login", json={"username": user, "password": pwd}, verify=False)

    seen = set()
    while True:
        try:
            # 2. القنص السريع
            recs = session.get("https://www.sama3ni.com/api/receipts", params={"limit": 5}, verify=False, timeout=10).json()
            data = recs.get("receipts", recs.get("data", [])) if isinstance(recs, dict) else recs
            
            for r in data:
                r_id = r.get("id")
                num_id = r.get("numberId") or r.get("number_id")
                phone = r.get("number", "Unknown")
                
                if r_id not in seen and num_id:
                    seen.add(r_id)
                    send_tg_message(f"🌟 **رسالة جديدة!** (`{phone}`)\n⏳ جاري الإجبار والتفعيل...")
                    
                    for _ in range(4):
                        res = session.post(f"https://www.sama3ni.com/api/numbers/{num_id}/activate", verify=False, timeout=5)
                        if res.status_code in [200, 201, 409]:
                            send_tg_message(f"⚡️ **تم تفعيل الرقم بنجاح!** (`{phone}`)")
                            break
                        time.sleep(0.5)

            # 3. إعادة التفعيل للمنتهي
            nums = session.get("https://www.sama3ni.com/api/numbers", params={"limit": 20}, verify=False, timeout=10).json()
            ndata = nums.get("numbers", nums.get("data", [])) if isinstance(nums, dict) else nums
            for num in ndata:
                status = str(num.get("status", "")).lower()
                num_id = num.get("id")
                phone = num.get("number", "")
                if status in ['expired', 'canceled', 'timeout', '2', '3', '0'] and num_id:
                    res = session.post(f"https://www.sama3ni.com/api/numbers/{num_id}/activate", verify=False, timeout=5)
                    if res.status_code in [200, 201]:
                        send_tg_message(f"🔄 **تم إحياء الرقم بنجاح:** `{phone}`")
        except:
            pass
        time.sleep(4)


def main(page: ft.Page):
    page.title = "Sama3ni Mobile Engine"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.padding = 20

    status_text = ft.Text("⏳ جاري الاتصال بالبوت...", size=25, weight=ft.FontWeight.BOLD, color=ft.colors.YELLOW)
    info_text = ft.Text("اترك هذا التطبيق مفتوحاً في الخلفية", size=15, color=ft.colors.GREY)

    page.add(
        ft.Column(
            [
                status_text,
                info_text
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10
        )
    )

    # تشغيل المحرك في الخلفية فور فتح التطبيق وتمرير العناصر لتحديث الواجهة
    threading.Thread(target=engine_loop, args=(page, status_text), daemon=True).start()


if __name__ == '__main__':
    ft.app(target=main, view=ft.AppView.FLET_APP)
