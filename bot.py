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
      "premium_users": [],
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


def is_premium(user_id):
  data = load_data()
  return is_admin(user_id) or user_id in data.get("premium_users", [])


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
        "📢 Channel Join Korun", url="https://t.me/unknownapps1"
    )
    check_btn = types.InlineKeyboardButton(
        "🔄 Check Join", callback_data="check_sub"
    )
    markup.add(join_btn)
    markup.add(check_btn)

    bot.send_message(
        message.chat.id,
        "❌ **Bot use korte hole oboshshoi amader channel-e join korte"
        " hobe!**\n\nChannel: https://t.me/unknownapps1",
        reply_markup=markup,
        parse_mode="Markdown",
    )
    return

  show_main_menu(message.chat.id, user_id)


def show_main_menu(chat_id, user_id):
  markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
  stats_btn = types.KeyboardButton("📊 Status")
  buy_btn = types.KeyboardButton("🛒 BUY PKG")
  owner_btn = types.KeyboardButton("👑 Owner")

  if is_admin(user_id):
    admin_panel_btn = types.KeyboardButton("⚙️ Admin Panel")
    markup.add(stats_btn, buy_btn, owner_btn, admin_panel_btn)
  else:
    markup.add(stats_btn, buy_btn, owner_btn)

  bot.send_message(
      chat_id,
      "🚀 **AUTO NETLIFY FILE HOST BY TAMIM**\n\nApnar যেকোনো নামের `.html`"
      " ফাইল এখানে send করুন, যার শেষে `.html` আছে, সেটি আমি automatic"
      " Netlify-e host করে live URL দিয়ে দেবো!",
      reply_markup=markup,
      parse_mode="Markdown",
  )


@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def verify_subscription(call):
  user_id = call.from_user.id
  if is_subscribed(user_id):
    bot.answer_callback_query(call.id, "✅ Verified successfully!")
    try:
      bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
      pass
    show_main_menu(call.message.chat.id, user_id)
  else:
    bot.answer_callback_query(
        call.id, "❌ Apni ekhono channel join করেননি!", show_alert=True
    )


# --- BUY PKG BUTTON & BKASH INFO ---
@bot.message_handler(func=lambda message: message.text == "🛒 BUY PKG")
def buy_packages(message):
  pkg_text = (
      f"🛒 **FILE HOSTING PACKAGES & PRICING**\n\n"
      f"1️⃣ **Unlimited File Hosting** — `100 TK`\n"
      f"2️⃣ **1 Din (1 File)** — `10 TK`\n"
      f"3️⃣ **7 Din (5 Files)** — `30 TK`\n"
      f"4️⃣ **30 Din (20 Files)** — `60 TK`\n\n"
      f"💳 **bKash Send Money Number:**\n`{BKASH_NUMBER}` (Personal)\n\n"
      f"⚠️ **Kibabe Kinben?**\n"
      f"Uporer bKash number-e taka pathiye tarpor niche dewa niyome command"
      f" din:\n`/pay <Package_Name> <TrxID>`\n\n"
      f"*(Udahoron: `/pay Unlimited ABC123XYZ`)*\n\n"
      f"Taka pathanor por admin approve korle apnar package active hoye"
      f" jabe!"
  )
  bot.send_message(message.chat.id, pkg_text, parse_mode="Markdown")


# --- /PAY COMMAND FOR USERS ---
@bot.message_handler(commands=["pay"])
def payment_request(message):
  user_id = message.from_user.id
  args = message.text.split(maxsplit=2)

  if len(args) < 3:
    bot.reply_to(
        message,
        "❌ **Sothik niyome payment request din:**\n`/pay <Package_Name>"
        " <TrxID>`\n\nUdahoron: `/pay Unlimited TrxID12345`",
        parse_mode="Markdown",
    )
    return

  pkg_name = args[1]
  trx_id = args[2]
  username = (
      f"@{message.from_user.username}"
      if message.from_user.username
      else message.from_user.first_name
  )

  data = load_data()
  admins_list = data.get("admins", [MASTER_OWNER_ID])

  markup = types.InlineKeyboardMarkup()
  confirm_btn = types.InlineKeyboardButton(
      "✅ Confirm Payment", callback_data=f"app_pay_{user_id}"
  )
  reject_btn = types.InlineKeyboardButton(
      "❌ Reject", callback_data=f"rej_pay_{user_id}"
  )
  markup.add(confirm_btn, reject_btn)

  admin_msg = (
      f"🔔 **NEW PAYMENT REQUEST!**\n\n"
      f"👤 User: {username} (`{user_id}`)\n"
      f"📦 Package: `{pkg_name}`\n"
      f"💳 TrxID: `{trx_id}`\n\n"
      f"Confirm korle user automatic unlimited access peye jabe."
  )

  for adm in admins_list:
    try:
      bot.send_message(adm, admin_msg, reply_markup=markup, parse_mode="Markdown")
    except Exception as e:
      print(f"Error sending to admin {adm}: {e}")

  bot.reply_to(
      message,
      "✅ **Payment request sent successfully!**\n\nAdmin check kore khub"
      " shigghiri apnar package confirm kore dibe.",
      parse_mode="Markdown",
  )


# --- ADMIN CALLBACK FOR PAYMENT APPROVAL / REJECTION ---
@bot.callback_query_handler(
    func=lambda call: call.data.startswith("app_pay_")
    or call.data.startswith("rej_pay_")
)
def handle_payment_approval(call):
  if not is_admin(call.from_user.id):
    bot.answer_callback_query(call.id, "❌ Apnar permission nei!", show_alert=True)
    return

  data = load_data()
  parts = call.data.split("_")
  action = parts[0]
  target_user_id = int(parts[2])

  if action == "app":
    if target_user_id not in data.get("premium_users", []):
      data["premium_users"].append(target_user_id)
      save_data(data)

    bot.answer_callback_query(
        call.id, "✅ Payment Approved & Package Activated!"
    )
    bot.edit_message_text(
        call.message.text
        + "\n\n**STATUS:** `✅ APPROVED BY ADMIN`",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        parse_mode="Markdown",
    )

    try:
      bot.send_message(
          target_user_id,
          "🎉 **Congratulations!**\n\nApnar bKash payment admin successful"
          " confirm korechen. Ekhon apnar account-e **Unlimited File Hosting**"
          " active kore dewa hoyeche!",
          parse_mode="Markdown",
      )
    except Exception as e:
      print(f"Could not notify user {target_user_id}: {e}")

  elif action == "rej":
    bot.answer_callback_query(call.id, "❌ Payment Rejected.")
    bot.edit_message_text(
        call.message.text + "\n\n**STATUS:** `❌ REJECTED BY ADMIN`",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        parse_mode="Markdown",
    )

    try:
      bot.send_message(
          target_user_id,
          "❌ **Payment Rejected!**\n\nApnar bKash payment request-ti admin"
          " reject korechen. Sothik TrxID diye abar chesta korun ba owner-er"
          " sathe jogajog korun.",
          parse_mode="Markdown",
      )
    except Exception as e:
      print(f"Could not notify user {target_user_id}: {e}")


@bot.message_handler(func=lambda message: message.text == "👑 Owner")
def owner_info(message):
  markup = types.InlineKeyboardMarkup()
  btn = types.InlineKeyboardButton(
      "💬 Owner Contact", url="https://t.me/tamim_bhai_dv"
  )
  markup.add(btn)
  bot.send_message(
      message.chat.id,
      "👑 **Bot Owner Info**\n\nTelegram: https://t.me/tamim_bhai_dv",
      reply_markup=markup,
      parse_mode="Markdown",
  )


@bot.message_handler(func=lambda message: message.text == "📊 Status")
def bot_stats(message):
  data = load_data()
  user_id = message.from_user.id
  total_users = len(data["users"])
  total_files = data["total_files"]
  user_id_str = str(user_id)
  user_hosted = data["user_file_counts"].get(user_id_str, 0)

  if is_premium(user_id):
    limit_text = "Unlimited (Premium / Admin)"
  else:
    free_limit = max(0, 3 - user_hosted)
    limit_text = f"{free_limit} free slots left (Hosted: {user_hosted})"

  stats_text = (
      "📊 **AUTO NETLIFY FILE HOST STATS**\n\n👥 Total Members:"
      f" `{total_users}`\n📂 Total Hosted Files: `{total_files}`\n👤 Your"
      f" Status: `{limit_text}`"
  )
  bot.send_message(message.chat.id, stats_text, parse_mode="Markdown")


# --- ADMIN PANEL ---
@bot.message_handler(func=lambda message: message.text == "⚙️ Admin Panel")
def admin_panel(message):
  if not is_admin(message.from_user.id):
    bot.reply_to(message, "❌ Ei command-ti shudhumatro Admin-der jonno!")
    return

  markup = types.InlineKeyboardMarkup(row_width=1)
  logs_btn = types.InlineKeyboardButton(
      "📁 File Hosting Logs", callback_data="admin_logs"
  )
  users_btn = types.InlineKeyboardButton(
      "👥 Member Stats", callback_data="admin_users"
  )
  add_admin_btn = types.InlineKeyboardButton(
      "➕ Add New Admin", callback_data="admin_add"
  )
  markup.add(logs_btn, users_btn, add_admin_btn)

  bot.send_message(
      message.chat.id,
      "⚙️ **Admin Control Panel**\n\nSelect an option below:",
      reply_markup=markup,
      parse_mode="Markdown",
  )


@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_"))
def admin_callbacks(call):
  if not is_admin(call.from_user.id):
    bot.answer_callback_query(call.id, "❌ Permission denied!", show_alert=True)
    return

  data = load_data()

  if call.data == "admin_users":
    total_users = len(data["users"])
    total_files = data["total_files"]
    text = (
        "👥 **Stats Overview**\n\n• Total Users: `{total_users}`\n• Total Files"
        f" Hosted: `{total_files}`\n• Total Admins: `{len(data['admins'])}`\n•"
        f" Premium Users: `{len(data.get('premium_users', []))}`"
    )
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, text, parse_mode="Markdown")

  elif call.data == "admin_logs":
    logs = data.get("file_logs", [])
    if not logs:
      bot.answer_callback_query(call.id, "No logs found!", show_alert=True)
      return

    log_text = "📁 **Recent File Logs (Last 10):**\n\n"
    for log in logs[-10:]:
      log_text += (
          f"👤 User: `{log['user_id']}`\n📂 File: `{log['file_name']}`\n🌐 URL:"
          f" {log['url']}\n⏱ Time: `{log['time']}`\n-------------------------\n"
      )
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, log_text, parse_mode="Markdown")

  elif call.data == "admin_add":
    bot.answer_callback_query(call.id)
    bot.send_message(
        call.message.chat.id,
        "➕ Nicher command-ti use kore kono user ke admin banan:\n\n`"
        "/addadmin <User_ID>`",
        parse_mode="Markdown",
    )


@bot.message_handler(commands=["addadmin"])
def add_admin_cmd(message):
  if message.from_user.id != MASTER_OWNER_ID:
    bot.reply_to(
        message, "❌ Shudhumatro Main Owner-i notun admin add korte parbe!"
    )
    return

  try:
    parts = message.text.split()
    if len(parts) < 2:
      bot.reply_to(
          message,
          "❌ Sothik niyome din: `/addadmin <User_ID>`",
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
          f"✅ Successful! User ID `{new_admin_id}` ke ekhon admin kora hoyeche.",
          parse_mode="Markdown",
      )
    else:
      bot.reply_to(
          message,
          f"⚠️ User ID `{new_admin_id}` already admin-er talikay ache.",
          parse_mode="Markdown",
      )
  except Exception as e:
    bot.reply_to(message, f"❌ Error: {str(e)}")


# --- DOCUMENT HANDLER & DEPLOYMENT ---
@bot.message_handler(content_types=["document"])
def handle_document(message):
  user_id = message.from_user.id

  if not is_subscribed(user_id):
    bot.reply_to(
        message,
        "❌ Age https://t.me/unknownapps1 channel-e join korun ebong /start"
        " din.",
    )
    return

  data = load_data()
  user_id_str = str(user_id)
  user_hosted_count = data["user_file_counts"].get(user_id_str, 0)

  if not is_premium(user_id) and user_hosted_count >= 3:
    bot.reply_to(
        message,
        "❌ **Free Limit Shes!**\n\nApnar free 3 ti file host korar limit"
        " sesh hoyeche. Aro host korte `🛒 BUY PKG` button theke bKash-e taka"
        " pathiye package kinun.",
        parse_mode="Markdown",
    )
    return

  file_info = message.document
  file_name = file_info.file_name

  # Flexible check: accepts any name as long as it ends with .html or .htm
  if not file_name or not (
      file_name.lower().endswith(".html") or file_name.lower().endswith(".htm")
  ):
    bot.reply_to(
        message,
        "❌ **Bhul Format!**\n\nফাইলের নামের শেষে অবশ্যই `.html` থাকতে হবে।",
        parse_mode="Markdown",
    )
    return

  msg = bot.reply_to(
      message,
      "⏳ File download hochche ebong Netlify-e custom URL soho host kora"
      " hocche...",
      parse_mode="Markdown",
  )

  try:
    file_path = bot.get_file(file_info.file_id)
    downloaded_file = bot.download_file(file_path.file_path)

    custom_site_name = f"tamim-html-{user_id}-{int(time.time())}"

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
            "✅ **File safolvabe host kora hoyeche!**\n\n🌐 **Custom Live URL:**"
            f" {site_url}\n📂 **File Name:** `{file_name}`\n👑 **Branding:**"
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
            f"❌ **Deploy byrtho!**\nError: `{deploy_res.text[:200]}`",
            chat_id=message.chat.id,
            message_id=msg.message_id,
            parse_mode="Markdown",
        )
    else:
      bot.edit_message_text(
          "❌ **Custom site toiri byrtho!**\nError:"
          f" `{site_creation_res.text[:200]}`",
          chat_id=message.chat.id,
          message_id=msg.message_id,
          parse_mode="Markdown",
      )

  except Exception as e:
    bot.edit_message_text(
        f"❌ **Somoshsha hoyeche:** `{str(e)}`",
        chat_id=message.chat.id,
        message_id=msg.message_id,
        parse_mode="Markdown",
    )


if __name__ == "__main__":
  print("🤖 Bot chalu hoyeche...")
  keep_alive()
  bot.infinity_polling()