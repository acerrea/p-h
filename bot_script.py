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

# ----------------- تابع دریافت و تجزیه حدیث (با هدر User-Agent) -----------------
def get_daily_hadith():
    """
    از سایت hadithlib.com یک حدیث تصادفی دریافت کرده و اطلاعات آن را استخراج می‌کند.
    در صورت موفقیت یک دیکشنری و در غیر این صورت None برمی‌گرداند.
    """
    hadith_url = "https://www.hadithlib.com/hadithlibjs/random/a6150e/Tahoma/10/bold/ffcfcd/1f95a6/Tahoma/11/normal/c9f8ff/864d2b/Traditional%20Arabic/18/bold/ffc39f/20483E/Tahoma/12/normal/6bfdd9/CD8F6A/Tahoma/10/normal/fbe8dc/BFAD7B/double/3/fefce7/58/1/1/1/1/1/1/1/1/"
    
    # هدر را تعریف می‌کنیم تا خودمان را یک مرورگر واقعی جا بزنیم
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        print("در حال ارسال درخواست به سایت حدیث با هدر User-Agent...")
        # هدر را به درخواست اضافه می‌کنیم
        response = requests.get(hadith_url, headers=headers, timeout=15)
        response.raise_for_status() # اگر کد وضعیت خطا بود، استثنا ایجاد می‌کند
        
        raw_js = response.text
        print("پاسخ از سایت حدیث دریافت شد. در حال استخراج محتوا...")

        match = re.search(r"document\.write\('(.*)'\)", raw_js, re.DOTALL)
        if not match:
            print("خطا: الگوی Regex در محتوای JavaScript پیدا نشد.")
            print("محتوای دریافت شده (برای بررسی):", raw_js[:300])
            return None
            
        html_content = match.group(1)
        soup = BeautifulSoup(html_content, 'html.parser')
        spans = soup.find_all('span')
        print(f"تعداد {len(spans)} تگ <span> پیدا شد.")

        if len(spans) < 5:
            print("خطا: تعداد تگ‌های <span> کمتر از حد انتظار است. ساختار سایت ممکن است تغییر کرده باشد.")
            return None

        hadith_data = {
            "title": spans[0].get_text(strip=True),
            "speaker": spans[1].get_text(strip=True),
            "hadith_arabic": spans[2].get_text(strip=True),
            "translation": spans[3].get_text(strip=True),
            "source": spans[4].get_text(strip=True)
        }
        return hadith_data

    except requests.exceptions.RequestException as e:
        print(f"خطا در اتصال به سایت حدیث: {e}")
        return None
    except IndexError:
        print("خطا: ساختار HTML سایت حدیث تغییر کرده است (IndexError).")
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
