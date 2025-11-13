import requests
import re
import time
import json
import random
from bs4 import BeautifulSoup
import os # <-- این ماژول را اضافه کنید

# ⚙️ اطلاعات ربات را از GitHub Secrets بخوان
# به جای هاردکد کردن، از متغیرهای محیطی استفاده می‌کنیم
BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

# بررسی کنید که آیا متغیرها تنظیم شده‌اند
if not BOT_TOKEN or not CHAT_ID:
    print("خطا: متغیرهای محیطی BOT_TOKEN و CHAT_ID تنظیم نشده‌اند.")
    exit() # از اسکریپت خارج شو

TOTAL_PROXIES_TO_SEND = 40

# ----------------- تابع دریافت حدیث با استفاده از API عمومی (روش جدید و پایدار) -----------------
def get_daily_hadith():
    """
    از API سایت dorar.net یک حدیث تصادفی دریافت کرده و اطلاعات آن را استخراج می‌کند.
    این روش بسیار پایدارتر از اسکرپ کردن وب‌سایت است.
    """
    api_url = "https://dorar.net/dorar_api.json?skey=random"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        print("در حال ارسال درخواست به API حدیث dorar.net...")
        response = requests.get(api_url, headers=headers, timeout=15)
        response.raise_for_status() # بررسی خطا

        # محتوای JSON را استخراج می‌کنیم
        data = response.json()
        
        # اطلاعات را از پاسخ JSON استخراج می‌کنیم
        html_content = data.get('ahadith', {}).get('result', '')
        
        if not html_content:
            print("خطا: محتوای حدیث در پاسخ API یافت نشد.")
            return None
        
        # از BeautifulSoup برای پاکسازی تگ‌های HTML استفاده می‌کنیم
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # استخراج بخش‌های مختلف حدیث
        hadith_text = soup.find('p', class_='hadith').get_text(strip=True, separator='\n')
        source_info = soup.find('p', class_='hadith-info').get_text(strip=True, separator=' | ')

        # چون این API ترجمه فارسی ندارد، ساختار خروجی را کمی تغییر می‌دهیم
        # برای عنوان و گوینده، یک متن عمومی قرار می‌دهیم
        hadith_data = {
            "title": "قال رسول الله ﷺ", # یک عنوان عمومی برای حدیث
            "speaker": "", # گوینده در متن اصلی است
            "hadith_arabic": hadith_text,
            "translation": "(در حال حاضر ترجمه فارسی برای این حدیث از طریق API در دسترس نیست)",
            "source": source_info
        }
        print("حدیث از API با موفقیت دریافت شد.")
        return hadith_data

    except requests.exceptions.RequestException as e:
        print(f"خطا در اتصال به API حدیث: {e}")
        return None
    except (json.JSONDecodeError, KeyError, AttributeError) as e:
        print(f"خطا در تجزیه پاسخ API حدیث: {e}")
        print("پاسخ دریافتی:", response.text if 'response' in locals() else "پاسخی دریافت نشد")
        return None
    except Exception as e:
        print(f"خطای پیش‌بینی نشده در دریافت حدیث: {e}")
        return None

# ----------------- بخش اصلی اسکریپت (بدون تغییر در منطق) -----------------

print("در حال دریافت لیست پروکسی‌ها...")
proxy_list_url = 'https://raw.githubusercontent.com/SoliSpirit/mtproto/refs/heads/master/all_proxies.txt'
try:
    r = requests.get(proxy_list_url).text
    proxy_links = re.findall(r'https://t\.me/proxy\?[^ \n]+', r)
    print(f"تعداد {len(proxy_links)} پروکسی پیدا شد.")
except requests.exceptions.RequestException as e:
    print(f"خطا در دریافت لیست پروکسی‌ها: {e}")
    proxy_links = []

if proxy_links:
    good_proxies = []
    bad_proxies = []
    for link in proxy_links:
        if re.search(r'A{10,}$', link):
            bad_proxies.append(link)
        else:
            good_proxies.append(link)

    def get_mixed_proxies(total_needed):
        num_good = int(total_needed * 0.8)
        num_bad = total_needed - num_good
        selected_good = random.sample(good_proxies, min(num_good, len(good_proxies)))
        selected_bad = random.sample(bad_proxies, min(num_bad, len(bad_proxies)))
        return selected_good + selected_bad

    all_proxies_combined = get_mixed_proxies(TOTAL_PROXIES_TO_SEND)
    random.shuffle(all_proxies_combined)
    
    if all_proxies_combined:
        print(f"در حال آماده‌سازی پیام برای {len(all_proxies_combined)} پروکسی...")
        keyboard = []
        row = []
        for link in all_proxies_combined:
            button = {"text": "🌐 اتصال", "url": link}
            row.append(button)
            if len(row) == 2:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)

        reply_markup = {"inline_keyboard": keyboard}

        message_text = (
            f"🚀 *لیست کامل پروکسی‌های فعال امروز*\n"
            f"📡 *تعداد: {len(all_proxies_combined)} پروکسی*\n\n"
            "📣️توجه :\n"
            "این ربات هیچ‌گونه نقشی در ساخت یا پیکربندی این پروکسی‌ها ندارد.\n"
            "تمام لینک‌ها از منابع عمومی جمع‌آوری شده و صرفاً جهت سهولت دسترسی کاربران بازنشر می‌شوند.\n\n"
            "محتوای اسپانسر یا تبلیغاتی که هنگام اتصال از طریق این پروکسی‌ها نمایش داده می‌شود "
            "کاملاً خارج از کنترل ما بوده و مسئولیت آن بر عهده ارائه‌دهندگان پروکسی است.\n\n"
            "#پروکسی\n"
            "🆔@ProxyKlik"
        )
        
        send_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': CHAT_ID,
            'text': message_text,
            'reply_markup': json.dumps(reply_markup),
            'parse_mode': 'Markdown'
        }

        try:
            res = requests.post(send_url, data=payload)
            print(f"پیام تجمیعی پروکسی‌ها ارسال شد: {res.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"خطا در ارسال پیام پروکسی‌ها: {e}")
        
        time.sleep(2)

    print("\nدر حال دریافت حدیث روز...")
    hadith = get_daily_hadith()

    if hadith:
        print("حدیث با موفقیت دریافت شد. در حال ارسال به تلگرام...")
        hadith_message = (
            f"🕌 *حدیث روز*\n\n"
            f"*{hadith['title']}*\n\n"
            f"*{hadith['speaker']}*\n"
            f"_{hadith['hadith_arabic']}_\n\n"
            f"📖 *ترجمه:*\n"
            f"{hadith['translation']}\n\n"
            f"📚 *منبع:*\n"
            f"{hadith['source']}\n\n"
            f"#حدیث\n"
            f"🆔@ProxyKlik"
        )
        
        send_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': CHAT_ID,
            'text': hadith_message,
            'parse_mode': 'Markdown'
        }

        try:
            res = requests.post(send_url, data=payload)
            print(f"پیام حدیث ارسال شد: {res.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"خطا در ارسال پیام حدیث: {e}")
            
    else:
        print("دریافت حدیث ناموفق بود. از ارسال آن صرف نظر شد.")
else:
    print("هیچ پروکسی برای ارسال یافت نشد. اسکریپت پایان یافت.")
