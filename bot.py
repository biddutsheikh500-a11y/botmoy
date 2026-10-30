from flask import Flask
import io
import json
import os
import requests
import telebot
from telebot import types
import threading
import time
import zipfile

# --- CONFIGURATION ---
BOT_TOKEN = "9030460416:AAHvrU2kD4QaO-_TaJdRie8KINMco3ZvuRI"
NETLIFY_TOKEN = "nfp_PUj4ntBv2FyMiXxQbsHQF1jh6FGB8jfK1e01"
CHANNEL_USERNAME = "@unknownapps1"
MASTER_OWNER_ID = 7586962564
BKASH_NUMBER = "01909993360"

bot = telebot.TeleBot(BOT_TOKEN)
DATA_FILE = "bot_data.json"

pending_payments = {}

# --- RENDER 24/7 KEEP ALIVE ---
app = Flask("")


@app.route("/")
def home():
  return "🤖 AUTO NETLIFY FILE HOST BY TAMIM is Running 24/7!"


def run_web():
  app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))


def keep_alive():
  t = threading.Thread(target=run_web)
  t.start()


# --- DATA LOAD & SAVE ---
def load_data():
  if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
      return json.load(f)
  return {
      "users": [],
      "admins": [MASTER_OWNER_ID],
      "premium_users": {},
      "total_files": 0,
      "user_file_counts": {},
      "file_logs": [],
  }


def save_data(data):
  with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=4, ensure_ascii=False)


# --- CHECK ADMIN / PREMIUM ---
def is_admin(user_id):
  data = load_data()
  return user_id == MASTER_OWNER_ID or user_id in data.get("admins", [])


def get_user_package(user_id):
  data = load_data()
  if is_admin(user_id):
    return "Unlimited (Admin)"
  return data.get("premium_users", {}).get(str(user_id), "Free (3 Files Limit)")


# --- CHANNEL SUBSCRIPTION CHECK ---
def is_subscribed(user_id):
  if is_admin(user_id):
    return True
  try:
    member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
    if member.status in ["member", "administrator", "creator"]:
      return True
  except Exception as e:
    print(f"Sub check error: {e}")
  return False


# --- /START COMMAND ---
@bot.message_handler(commands=["start"])
def send_welcome(message):
  user_id = message.from_user.id
  data = load_data()

  if user_id not in data["users"]:
    data["users"].append(user_id)
    save_data(data)

  if not is_subscribed(user_id):
    markup = types.InlineKeyboardMarkup()
    join_btn = types.InlineKeyboardButton(
        "📢 Join Channel", url="https://t.me/unknownapps1"
    )
    check_btn = types.InlineKeyboardButton(
        "🔄 Check Join", callback_data="check_sub"
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
  # Keyboard buttons in English as requested
  markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
  stats_btn = types.KeyboardButton("Status")
  host_btn = types.KeyboardButton("File Host")
  buy_btn = types.KeyboardButton("Buy Pkg")
  account_btn = types.KeyboardButton("Account")
  owner_btn = types.KeyboardButton("Owner")

  if is_admin(user_id):
    admin_panel_btn = types.KeyboardButton("Admin Panel")
    markup.add(stats_btn, host_btn, buy_btn, account_btn, owner_btn, admin_panel_btn)
  else:
    markup.add(stats_btn, host_btn, buy_btn, account_btn, owner_btn)

  bot.send_message(
      chat_id,
      "🚀 **AUTO NETLIFY FILE HOST BY TAMIM**\n\nস্বাগতম! আপনার ফাইল ম্যানেজ"
      " করার জন্য নিচের বাটনগুলো ব্যবহার করুন।",
      reply_markup=markup,
      parse_mode="Markdown",
  )


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


# --- FILE HOST BUTTON HANDLER ---
@bot.message_handler(func=lambda message: message.text == "File Host")
def file_host_prompt(message):
  bot.reply_to(
      message,
      "📂 **ফাইল হোেস্ট করার নিয়ম:**\n\nআপনার যেকোনো `.html` ফাইল এখানে ডকুমেন্ট"
      " হিসেবে পাঠান। ফাইলের নামের শেষে `.html` থাকতে হবে, তাহলেই আমি এটি"
      " সরাসরি ব্রাউজারে মেইন পেজ আকারে রান করার জন্য Netlify-এ `-by-tamim`"
      " ইউরল দিয়ে হোস্ট করে দেবো!",
      parse_mode="Markdown",
  )


# --- ACCOUNT BUTTON HANDLER ---
@bot.message_handler(func=lambda message: message.text == "Account")
def account_info(message):
  user = message.from_user
  user_id = user.id
  name = user.first_name if user.first_name else "Unknown"
  username = f"@{user.username}" if user.username else "None"

  data = load_data()
  user_hosted = data["user_file_counts"].get(str(user_id), 0)
  pkg_status = get_user_package(user_id)

  acc_text = (
      f"👤 **আপনার অ্যাকাউন্ট তথ্য**\n\n"
      f"• **নাম:** `{name}`\n"
      f"• **ইউজারনেম:** `{username}`\n"
      f"• **ইউজার আইডি:** `{user_id}`\n"
      f"• **প্যাকেজ স্ট্যাটাস:** `{pkg_status}`\n"
      f"• **মোট হোস্টেড ফাইল:** `{user_hosted}`"
  )
  bot.send_message(message.chat.id, acc_text, parse_mode="Markdown")


# --- BUY PKG BUTTON & INLINE PACKAGE LIST ---
@bot.message_handler(func=lambda message: message.text == "Buy Pkg")
def buy_packages(message):
  markup = types.InlineKeyboardMarkup(row_width=1)
  btn1 = types.InlineKeyboardButton(
      "💎 Unlimited File Hosting — 100 TK", callback_data="pkg_Unlimited"
  )
  btn2 = types.InlineKeyboardButton(
      "📦 1 Din (1 File) — 10 TK", callback_data="pkg_1Din_1File"
  )
  btn3 = types.InlineKeyboardButton(
      "📦 7 Din (5 Files) — 30 TK", callback_data="pkg_7Din_5Files"
  )
  btn4 = types.InlineKeyboardButton(
      "📦 30 Din (20 Files) — 60 TK", callback_data="pkg_30Din_20Files"
  )
  markup.add(btn1, btn2, btn3, btn4)

  bot.send_message(
      message.chat.id,
      "🛒 **ফাইল হোস্টিং প্যাকেজসমূহ**\n\nদয়া করে আপনার পছন্দের প্যাকেজটি"
      " সিলেক্ট করুন:",
      reply_markup=markup,
      parse_mode="Markdown",
  )


@bot.callback_query_handler(func=lambda call: call.data.startswith("pkg_"))
def select_package_callback(call):
  pkg_name = call.data.replace("pkg_", "").replace("_", " ")
  user_id = call.from_user.id
  pending_payments[user_id] = pkg_name
  bot.answer_callback_query(call.id)

  instructions = (
      f"💳 **সিলেক্টেড প্যাকেজ:** `{pkg_name}`\n\n"
      f"• **বিকাশ পার্সোনাল নম্বর:** `{BKASH_NUMBER}`\n\n"
      f"⚠️ **পেমেন্ট করার নিয়ম:**\n"
      f"১. উপরের নম্বরে টাকা সেন্ড করুন।\n"
      f"২. এরপর শুধু আপনার **বিকাশ নম্বর অথবা ট্রানজেকশন আইডি (TrxID)** এখানে"
      f" রিপ্লাই দিন।\n\n"
      f"অ্যাডমিন চেক করে আপনার প্যাকেজটি খুব শীঘ্রই একটিভ করে দেবেন!"
  )
  bot.send_message(call.message.chat.id, instructions, parse_mode="Markdown")


# --- HANDLE TEXT MESSAGE FOR PAYMENT SUBMISSION ---
@bot.message_handler(
    func=lambda message: message.from_user.id in pending_payments
    and not message.text.startswith("/")
)
def handle_payment_submission(message):
  user_id = message.from_user.id
  pkg_name = pending_payments.pop(user_id, "Unlimited")
  payment_info = message.text
  username = (
      f"@{message.from_user.username}"
      if message.from_user.username
      else message.from_user.first_name
  )

  data = load_data()
  admins_list = data.get("admins", [MASTER_OWNER_ID])

  markup = types.InlineKeyboardMarkup()
  confirm_btn = types.InlineKeyboardButton(
      "✅ কনফার্ম পেমেন্ট", callback_data=f"app_pay_{user_id}_{pkg_name}"
  )
  reject_btn = types.InlineKeyboardButton(
      "❌ রিজেক্ট", callback_data=f"rej_pay_{user_id}"
  )
  markup.add(confirm_btn, reject_btn)

  admin_msg = (
      f"🔔 **নতুন পেমেন্ট সাবমিশন!**\n\n"
      f"👤 ইউজার: {username} (`{user_id}`)\n"
      f"📦 প্যাকেজ: `{pkg_name}`\n"
      f"💳 ট্রানজেকশন তথ্য / নম্বর: `{payment_info}`\n\n"
      f"প্যাকেজ একটিভ করতে কনফার্ম বাটনে ক্লিক করুন।"
  )

  for adm in admins_list:
    try:
      bot.send_message(adm, admin_msg, reply_markup=markup, parse_mode="Markdown")
    except Exception as e:
      print(f"Error sending to admin {adm}: {e}")

  bot.reply_to(
      message,
      "✅ **পেমেন্ট তথ্য সফলভাবে সাবমিট হয়েছে!**\n\nঅ্যাডমিন চেক করে আপনার প্যাকেজটি"
      " শীঘ্রই একটিভ করে দেবেন।",
      parse_mode="Markdown",
  )


@bot.callback_query_handler(
    func=lambda call: call.data.startswith("app_pay_")
    or call.data.startswith("rej_pay_")
)
def handle_payment_approval(call):
  if not is_admin(call.from_user.id):
    bot.answer_callback_query(call.id, "❌ আপনার অনুমতি নেই!", show_alert=True)
    return

  data = load_data()
  parts = call.data.split("_")
  action = parts[0]
  target_user_id = int(parts[2])

  if action == "app":
    pkg_name = (
        "_".join(parts[3:]) if len(parts) > 3 else "Unlimited"
    )
    if "premium_users" not in data:
      data["premium_users"] = {}
    data["premium_users"][str(target_user_id)] = pkg_name
    save_data(data)

    bot.answer_callback_query(
        call.id, "✅ পেমেন্ট অ্যাপ্রুভ এবং প্যাকেজ একটিভ করা হয়েছে!"
    )
    bot.edit_message_text(
        call.message.text
        + "\n\n**স্ট্যাটাস:** `✅ অ্যাডমিন কর্তৃক কনফার্ম`",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        parse_mode="Markdown",
    )

    try:
      bot.send_message(
          target_user_id,
          f"🎉 **অভিনন্দন!**\n\nআপনার পেমেন্ট অ্যাডমিন সফলভাবে কনফার্ম করেছেন।"
          f" আপনার অ্যাকাউন্টে `{pkg_name}` প্যাকেজটি এখন একটিভ!",
          parse_mode="Markdown",
      )
    except Exception as e:
      print(f"Could not notify user {target_user_id}: {e}")

  elif action == "rej":
    bot.answer_callback_query(call.id, "❌ পেমেন্ট রিজেক্ট করা হয়েছে।")
    bot.edit_message_text(
        call.message.text + "\n\n**স্ট্যাটাস:** `❌ অ্যাডমিন কর্তৃক রিজেক্ট`",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        parse_mode="Markdown",
    )

    try:
      bot.send_message(
          target_user_id,
          "❌ **পেমেন্ট রিজেক্ট হয়েছে!**\n\nআপনার পেমেন্ট রিকোয়েস্টটি অ্যাডমিন"
          " রিজেক্ট করেছেন। সঠিক তথ্য দিয়ে আবার চেষ্টা করুন।",
          parse_mode="Markdown",
      )
    except Exception as e:
      print(f"Could not notify user {target_user_id}: {e}")


@bot.message_handler(func=lambda message: message.text == "Owner")
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


@bot.message_handler(func=lambda message: message.text == "Status")
def bot_stats(message):
  data = load_data()
  user_id = message.from_user.id
  total_users = len(data["users"])
  total_files = data["total_files"]
  user_id_str = str(user_id)
  user_hosted = data["user_file_counts"].get(user_id_str, 0)

  pkg_info = get_user_package(user_id)
  if "Free" in pkg_info:
    free_limit = max(0, 3 - user_hosted)
    limit_text = f"{free_limit} free slots left (Hosted: {user_hosted})"
  else:
    limit_text = f"{pkg_info} (Hosted: {user_hosted})"

  stats_text = (
      "📊 **AUTO NETLIFY FILE HOST STATS**\n\n👥 মোট মেম্বার:"
      f" `{total_users}`\n📂 মোট হোস্টেড ফাইল: `{total_files}`\n👤 আপনার"
      f" স্ট্যাটাস: `{limit_text}`"
  )
  bot.send_message(message.chat.id, stats_text, parse_mode="Markdown")


# --- ADMIN PANEL ---
@bot.message_handler(func=lambda message: message.text == "Admin Panel")
def admin_panel(message):
  if not is_admin(message.from_user.id):
    bot.reply_to(message, "❌ এই কমান্ডটি শুধু অ্যাডমিনদের জন্য!")
    return

  markup = types.InlineKeyboardMarkup(row_width=1)
  logs_btn = types.InlineKeyboardButton(
      "📁 ফাইল হোস্টিং লগস", callback_data="admin_logs"
  )
  users_btn = types.InlineKeyboardButton(
      "👥 মেম্বার পরিসংখ্যান", callback_data="admin_users"
  )
  add_admin_btn = types.InlineKeyboardButton(
      "➕ নতুন অ্যাডমিন যুক্ত করুন", callback_data="admin_add"
  )
  markup.add(logs_btn, users_btn, add_admin_btn)

  bot.send_message(
      message.chat.id,
      "⚙️ **অ্যাডমিন কন্ট্রোল প্যানেল**\n\nনিচের অপশনগুলো থেকে সিলেক্ট করুন:",
      reply_markup=markup,
      parse_mode="Markdown",
  )


@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_"))
def admin_callbacks(call):
  if not is_admin(call.from_user.id):
    bot.answer_callback_query(call.id, "❌ অনুমতি নেই!", show_alert=True)
    return

  data = load_data()

  if call.data == "admin_users":
    total_users = len(data["users"])
    total_files = data["total_files"]
    text = (
        "👥 **পরিসংখ্যান ওভারভিউ**\n\n• মোট ইউজার: `{total_users}`\n• মোট হোস্টেড"
        f" ফাইল: `{total_files}`\n• মোট অ্যাডমিন: `{len(data['admins'])}`\n•"
        f" প্রিমিয়াম ইউজার: `{len(data.get('premium_users', {}))}`"
    )
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, text, parse_mode="Markdown")

  elif call.data == "admin_logs":
    logs = data.get("file_logs", [])
    if not logs:
      bot.answer_callback_query(call.id, "কোনো লগ পাওয়া যায়নি!", show_alert=True)
      return

    log_text = "📁 **সাম্প্রতিক ফাইল লগস (শেষ ১০টি):**\n\n"
    for log in logs[-10:]:
      log_text += (
          f"👤 ইউজার: `{log['user_id']}`\n📂 ফাইল: `{log['file_name']}`\n🌐 ইউআরএল:"
          f" {log['url']}\n⏱ সময়: `{log['time']}`\n-------------------------\n"
      )
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, log_text, parse_mode="Markdown")

  elif call.data == "admin_add":
    bot.answer_callback_query(call.id)
    bot.send_message(
        call.message.chat.id,
        "➕ নতুন অ্যাডমিন যোগ করতে এই কমান্ডটি ব্যবহার করুন:\n\n`"
        "/addadmin <User_ID>`",
        parse_mode="Markdown",
    )


@bot.message_handler(commands=["addadmin"])
def add_admin_cmd(message):
  if message.from_user.id != MASTER_OWNER_ID:
    bot.reply_to(message, "❌ শুধুমাত্র মেইন ওনার নতুন অ্যাডমিন যোগ করতে পারেন!")
    return

  try:
    parts = message.text.split()
    if len(parts) < 2:
      bot.reply_to(
          message,
          "❌ সঠিক নিয়ম: `/addadmin <User_ID>`",
          parse_mode="Markdown",
      )
      return

    new_admin_id = int(parts[1])
    data = load_data()

    if new_admin_id not in data["admins"]:
      data["admins"].append(new_admin_id)
      save_data(data)
      bot.reply_to(
          message,
          f"✅ সফল! ইউজার আইডি `{new_admin_id}` এখন অ্যাডমিন হিসেবে যুক্ত হয়েছে।",
          parse_mode="Markdown",
      )
    else:
      bot.reply_to(
          message,
          f"⚠️ ইউজার আইডি `{new_admin_id}` ইতিমধ্যে অ্যাডমিন তালিকায় রয়েছে।",
          parse_mode="Markdown",
      )
  except Exception as e:
    bot.reply_to(message, f"❌ ত্রুটি: {str(e)}")


# --- DOCUMENT HANDLER & DEPLOYMENT ---
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

  pkg_info = get_user_package(user_id)
  is_free_user = "Free" in pkg_info

  if is_free_user and user_hosted_count >= 3:
    bot.reply_to(
        message,
        "❌ **ফ্রি লিমিট শেষ!**\n\nআপনার ফ্রি ৩টি ফাইল হোেস্ট করার লিমিট শেষ"
        " হয়েছে। আরো হোস্ট করতে `Buy Pkg` বাটন থেকে প্যাকেজ কিনুন।",
        parse_mode="Markdown",
    )
    return

  file_info = message.document
  file_name = file_info.file_name

  if not file_name or not (
      file_name.lower().endswith(".html") or file_name.lower().endswith(".htm")
  ):
    bot.reply_to(
        message,
        "❌ **ভুল ফরম্যাট!**\n\nফাইলের নাম যাই হোক না কেন, শেষে অবশ্যই `.html`"
        " থাকতে হবে।",
        parse_mode="Markdown",
    )
    return

  msg = bot.reply_to(
      message,
      "⏳ ফাইল ডাউনলোড হচ্ছে এবং Netlify-এ সঠিক পেজ ফরম্যাটে ডিপ্লয় করা হচ্ছে...",
      parse_mode="Markdown",
  )

  try:
    file_path = bot.get_file(file_info.file_id)
    downloaded_file = bot.download_file(file_path.file_path)

    base_name = os.path.splitext(file_name)[0].lower()
    clean_name = "".join([c if c.isalnum() else "-" for c in base_name]).strip(
        "-"
    )
    if not clean_name:
      clean_name = f"site-{user_id}"

    custom_site_name = f"{clean_name}-by-tamim"

    headers = {
        "Authorization": f"Bearer {NETLIFY_TOKEN}",
        "Content-Type": "application/json",
    }

    site_creation_res = requests.post(
        "https://api.netlify.com/api/v1/sites",
        headers=headers,
        json={"name": custom_site_name},
    )

    if site_creation_res.status_code in [200, 201]:
      site_data = site_creation_res.json()
      site_id = site_data.get("id")
      site_url = site_data.get("ssl_url") or site_data.get("url")

      # Proper packaging as index.html so it renders the web page instead of plain text code
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
        data["total_files"] += 1
        data["user_file_counts"][user_id_str] = user_hosted_count + 1

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
            f"❌ **ডিপ্লয় ব্যর্থ হয়েছে!**\nএরর: `{deploy_res.text[:200]}`",
            chat_id=message.chat.id,
            message_id=msg.message_id,
            parse_mode="Markdown",
        )
    else:
      bot.edit_message_text(
          "❌ **সাইট তৈরি ব্যর্থ হয়েছে! (এই নাম দিয়ে ইতিমধ্যে অন্য সাইট তৈরি"
          f" হয়েছে, অন্য নাম দিয়ে ট্রাই করুন)**\nএরর:"
          f" `{site_creation_res.text[:200]}`",
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
  print("🤖 Bot চালু হয়েছে...")
  keep_alive()
  bot.infinity_polling()