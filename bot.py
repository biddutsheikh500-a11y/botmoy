from flask import Flask
import io
import json
import os
import requests
import telebot
from telebot import types
import threading
import time

# --- কনফিগারেশন ---
BOT_TOKEN = "9030460416:AAHvrU2kD4QaO-_TaJdRie8KINMco3ZvuRI"  # @BotFather থেকে পাওয়া আপনার বটের টোকেন দিন
NETLIFY_TOKEN = (
    "nfp_PUj4ntBv2FyMiXxQbsHQF1jh6FGB8jfK1e01"  # Netlify Personal Access Token দিন
)
CHANNEL_USERNAME = (
    "@unknownapps1"  # যে চ্যানেলে জয়েন করা বাধ্যতামূলক তার ইউজারনেম
)
OWNER_ID = 7586962564

bot = telebot.TeleBot(BOT_TOKEN)
DATA_FILE = "bot_data.json"

# --- RENDER 24/7 KEEP ALIVE (FLASK SERVER) ---
app = Flask("")


@app.route("/")
def home():
  print("🤖 Bot is active and running 24/7!")
  return "🤖 AUTO NETLIFY FILE HOST BY TAMIM is Running 24/7!"


def run_web():
  app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))


def keep_alive():
  t = threading.Thread(target=run_web)
  t.start()


# --- ডাটা লোড ও সেভ ফাংশন ---
def load_data():
  if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
      return json.load(f)
  return {"users": [], "total_files": 0, "user_file_counts": {}, "file_logs": []}


def save_data(data):
  with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=4, ensure_ascii=False)


# --- চ্যানেল সাবস্ক্রিপশন চেক ---
def is_subscribed(user_id):
  if user_id == OWNER_ID:
    return True
  try:
    member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
    if member.status in ["member", "administrator", "creator"]:
      return True
  except Exception as e:
    print(f"সাবস্ক্রিপশন চেক ত্রুটি: {e}")
  return False


# --- /start কমান্ড ---
@bot.message_handler(commands=["start"])
def send_welcome(message):
  user_id = message.from_user.id
  data = load_data()

  # নতুন ইউজার ট্র্যাক করা
  if user_id not in data["users"]:
    data["users"].append(user_id)
    save_data(data)

  # চ্যানেল জয়েন চেক
  if not is_subscribed(user_id):
    markup = types.InlineKeyboardMarkup()
    join_btn = types.InlineKeyboardButton(
        "📢 চ্যানেলে জয়েন করুন", url="https://t.me/unknownapps1"
    )
    check_btn = types.InlineKeyboardButton(
        "🔄 জয়েন করেছি, চেক করুন", callback_data="check_sub"
    )
    markup.add(join_btn)
    markup.add(check_btn)

    bot.send_message(
        message.chat.id,
        "❌ **বট ব্যবহার করতে হলে অবশ্যই আমাদের চ্যানেলে জয়েন করতে হবে!**\n\nচ্যানেল"
        " লিংক: https://t.me/unknownapps1",
        reply_markup=markup,
        parse_mode="Markdown",
    )
    return

  show_main_menu(message.chat.id, user_id)


def show_main_menu(chat_id, user_id):
  markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
  stats_btn = types.KeyboardButton("📊 স্ট্যাটাস")
  owner_btn = types.KeyboardButton("👑 ওনার")

  if user_id == OWNER_ID:
    admin_panel_btn = types.KeyboardButton("⚙️ ওনার প্যানেল")
    markup.add(stats_btn, owner_btn, admin_panel_btn)
  else:
    markup.add(stats_btn, owner_btn)

  bot.send_message(
      chat_id,
      "🚀 **AUTO NETLIFY FILE HOST BY TAMIM**\n\nস্বাগতম! আপনার যেকোনো `.html`"
      " ফাইল এখানে পাঠান, আমি স্বয়ংক্রিয়ভাবে কাস্টম URL সহ Netlify-এ হোস্ট করে"
      " দেবো!",
      reply_markup=markup,
      parse_mode="Markdown",
  )


# --- সাবস্ক্রিপশন ভেরিফিকেশন কলব্যাক ---
@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def verify_subscription(call):
  user_id = call.from_user.id
  if is_subscribed(user_id):
    bot.answer_callback_query(call.id, "✅ ভেরিফিকেশন সফল হয়েছে!")
    try:
      bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
      pass
    show_main_menu(call.message.chat.id, user_id)
  else:
    bot.answer_callback_query(
        call.id,
        "❌ আপনি এখনও চ্যানেলে জয়েন করেননি! দয়া করে আগে জয়েন করুন।",
        show_alert=True,
    )


# --- ওনার বাটন হ্যান্ডলার ---
@bot.message_handler(func=lambda message: message.text == "👑 ওনার")
def owner_info(message):
  markup = types.InlineKeyboardMarkup()
  btn = types.InlineKeyboardButton(
      "💬 ওনারের সাথে যোগাযোগ করুন", url="https://t.me/tamim_bhai_dv"
  )
  markup.add(btn)
  bot.send_message(
      message.chat.id,
      "👑 **বট ওনার তথ্য**\n\nটেলিগ্রাম: https://t.me/tamim_bhai_dv",
      reply_markup=markup,
      parse_mode="Markdown",
  )


# --- স্ট্যাটাস বাটন হ্যান্ডলার ---
@bot.message_handler(func=lambda message: message.text == "📊 স্ট্যাটাস")
def bot_stats(message):
  data = load_data()
  total_users = len(data["users"])
  total_files = data["total_files"]
  user_id_str = str(message.from_user.id)
  user_hosted = data["user_file_counts"].get(user_id_str, 0)

  stats_text = (
      "📊 **AUTO NETLIFY FILE HOST STATS**\n\n👥 মোট মেম্বার: "
      f"`{total_users}`\n📂 মোট হোস্টেড ফাইল: `{total_files}`\n👤 আপনার হোস্ট করা"
      f" ফাইল: `{user_hosted}/10`"
  )
  bot.send_message(message.chat.id, stats_text, parse_mode="Markdown")


# --- ওনার প্যানেল (অ্যাডমিন কন্ট্রোল) ---
@bot.message_handler(func=lambda message: message.text == "⚙️ ওনার প্যানেল")
def owner_panel(message):
  if message.from_user.id != OWNER_ID:
    bot.reply_to(message, "❌ এই কমান্ডটি শুধুমাত্র ওনারের জন্য!")
    return

  markup = types.InlineKeyboardMarkup(row_width=1)
  logs_btn = types.InlineKeyboardButton(
      "📁 ফাইল হোস্টিং হিস্ট্রি (Logs)", callback_data="admin_logs"
  )
  users_btn = types.InlineKeyboardButton(
      "👥 মেম্বার লিস্ট ও পরিসংখ্যান", callback_data="admin_users"
  )
  markup.add(logs_btn, users_btn)

  bot.send_message(
      message.chat.id,
      "⚙️ **স্বাগতম ওনার প্যানেলে**\n\nনিچیর অপশনগুলো থেকে বট কন্ট্রোল"
      " করুন:",
      reply_markup=markup,
      parse_mode="Markdown",
  )


@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_"))
def admin_callbacks(call):
  if call.from_user.id != OWNER_ID:
    bot.answer_callback_query(call.id, "❌ আপনার অনুমতি নেই!", show_alert=True)
    return

  data = load_data()

  if call.data == "admin_users":
    total_users = len(data["users"])
    total_files = data["total_files"]
    text = (
        "👥 **মেম্বার ও ফাইল পরিসংখ্যান**\n\n• মোট বট ব্যবহারকারী:"
        f" `{total_users}`\n• মোট আপলোডকৃত ফাইল: `{total_files}`"
    )
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, text, parse_mode="Markdown")

  elif call.data == "admin_logs":
    logs = data.get("file_logs", [])
    if not logs:
      bot.answer_callback_query(
          call.id, "কোনো হোস্টিং হিস্ট্রি নেই!", show_alert=True
      )
      return

    log_text = "📁 **সাম্প্রতিক হোস্টিং হিস্ট্রি (শেষ ১০টি):**\n\n"
    for log in logs[-10:]:
      log_text += (
          f"👤 User ID: `{log['user_id']}`\n📂 File: `{log['file_name']}`\n🌐 URL:"
          f" {log['url']}\n⏱ Time: `{log['time']}`\n-------------------------\n"
      )
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, log_text, parse_mode="Markdown")


# --- ফাইল / ডকুমেন্ট হ্যান্ডলার (শুধুমাত্র HTML) ---
@bot.message_handler(content_types=["document"])
def handle_document(message):
  user_id = message.from_user.id

  if not is_subscribed(user_id):
    bot.reply_to(
        message,
        "❌ দয়া করে আগে https://t.me/unknownapps1 চ্যানেলে জয়েন করুন এবং /start"
        " দিন।",
    )
    return

  data = load_data()
  user_id_str = str(user_id)
  user_hosted_count = data["user_file_counts"].get(user_id_str, 0)

  # ১০ ফাইল লিমিট চেক (ওনার ছাড়া)
  if user_id != OWNER_ID and user_hosted_count >= 10:
    bot.reply_to(
        message,
        "❌ **লিমিট শেষ!**\n\nআপনি সর্বোচ্চ ১০টি ফাইল হোস্ট করার লিমিট পূর্ণ"
        " করেছেন।",
        parse_mode="Markdown",
    )
    return

  file_info = message.document
  file_name = file_info.file_name

  # .html এক্সটেনশন ভ্যালিডেশন
  if not file_name or not file_name.endswith(".html"):
    bot.reply_to(
        message,
        "❌ **ভুল ফরম্যাট!**\n\nবটে শুধুমাত্র `.html` ফাইল আপলোড করা যাবে।",
        parse_mode="Markdown",
    )
    return

  msg = bot.reply_to(
      message,
      "⏳ ফাইল ডাউনলোড হচ্ছে এবং Netlify-এ কাস্টম URL সহ হোস্ট করা হচ্ছে...",
      parse_mode="Markdown",
  )

  try:
    # টেলিগ্রাম থেকে ফাইল ডাউনলোড
    file_path = bot.get_file(file_info.file_id)
    downloaded_file = bot.download_file(file_path.file_path)

    # কাস্টম সাবডোমেন বা সাইটের নাম তৈরি (Custom URL)
    custom_site_name = (
        f"tamim-html-{user_id}-{int(time.time())}"  # ইউনিক কাস্টম নাম
    )

    headers = {
        "Authorization": f"Bearer {NETLIFY_TOKEN}",
        "Content-Type": "application/json",
    }

    # প্রথমে কাস্টম নাম দিয়ে সাইট তৈরি করা (Netlify API)
    site_creation_res = requests.post(
        "https://api.netlify.com/api/v1/sites",
        headers=headers,
        json={"name": custom_site_name},
    )

    if site_creation_res.status_code in [200, 201]:
      site_data = site_creation_res.json()
      site_id = site_data.get("id")
      site_url = site_data.get("ssl_url") or site_data.get("url")

      # এখন ফাইলটি জিপ করে সাইটে ডিপ্লয় করা
      zip_buffer = io.BytesIO()
      with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr("index.html", downloaded_file)
      zip_buffer.seek(0)

      deploy_headers = {
          "Authorization": f"Bearer {NETLIFY_TOKEN}",
          "Content-Type": "application/zip",
      }

      deploy_res = requests.post(
          f"https://api.netlify.com/api/v1/sites/{site_id}/deploys",
          headers=deploy_headers,
          data=zip_buffer.read(),
      )

      if deploy_res.status_code in [200, 201]:
        # ডাটা আপডেট ও সেভ
        data["total_files"] += 1
        data["user_file_counts"][user_id_str] = user_hosted_count + 1

        # লগ সংরক্ষণ
        current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        data["file_logs"].append({
            "user_id": user_id,
            "file_name": file_name,
            "url": site_url,
            "time": current_time,
        })
        save_data(data)

        success_text = (
            "✅ **ফাইল সফলভাবে হোস্ট করা হয়েছে!**\n\n🌐 **কাস্টম লাইভ URL:**"
            f" {site_url}\n📂 **ফাইলের নাম:** `{file_name}`\n👑 **ব্র্যান্ডিং:**"
            " `AUTO NETLIFY FILE HOST BY TAMIM`"
        )
        bot.edit_message_text(
            success_text,
            chat_id=message.chat.id,
            message_id=msg.message_id,
            parse_mode="Markdown",
        )
      else:
        bot.edit_message_text(
            f"❌ **ডিপ্লয় ব্যর্থ হয়েছে!**\n\nএরর কোড:"
            f" `{deploy_res.text[:200]}`",
            chat_id=message.chat.id,
            message_id=msg.message_id,
            parse_mode="Markdown",
        )
    else:
      bot.edit_message_text(
          "❌ **কাস্টম সাইট তৈরি ব্যর্থ হয়েছে!** (সম্ভবত এই নামটি আগেই কেউ নিয়ে"
          f" নিয়েছে)\nএরর: `{site_creation_res.text[:200]}`",
          chat_id=message.chat.id,
          message_id=msg.message_id,
          parse_mode="Markdown",
      )

  except Exception as e:
    bot.edit_message_text(
        f"❌ **একটি সমস্যা হয়েছে:** `{str(e)}`",
        chat_id=message.chat.id,
        message_id=msg.message_id,
        parse_mode="Markdown",
    )


if __name__ == "__main__":
  print("🤖 বট সফলভাবে চালু হয়েছে এবং কাজ করছে...")
  keep_alive()  # Render-এ সার্ভার চালু রাখার জন্য
  bot.infinity_polling()