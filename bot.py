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
  host_btn = types.KeyboardButton("📂 File Host")
  buy_btn = types.KeyboardButton("🛒 Buy Pkg")
  account_btn = types.KeyboardButton("👤 Account")
  owner_btn = types.KeyboardButton("👑 Owner")

  if is_admin(user_id):
    admin_panel_btn = types.KeyboardButton("⚙️ Admin Panel")
    markup.add(stats_btn, host_btn, buy_btn, account_btn, owner_btn, admin_panel_btn)
  else:
    markup.add(stats_btn, host_btn, buy_btn, account_btn, owner_btn)

  bot.send_message(
      chat_id,
      "🚀 **AUTO NETLIFY FILE HOST BY TAMIM**\n\nSwagotom! Nicher button"
      " gulo use kore apnar kaj shuru korun.",
      reply_markup=markup,
      parse_mode="Markdown",
  )


@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def verify_subscription(call):
  user_id = call.from_user.id
  if is_subscribed(user_id):
    bot.answer_callback_query(call.id, "✅ Verification safol hoyeche!")
    try:
      bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
      pass
    show_main_menu(call.message.chat.id, user_id)
  else:
    bot.answer_callback_query(
        call.id, "❌ Apni ekhono channel join করেননি!", show_alert=True
    )


# --- FILE HOST BUTTON HANDLER ---
@bot.message_handler(func=lambda message: message.text == "📂 File Host")
def file_host_prompt(message):
  bot.reply_to(
      message,
      "📂 **File Host Korar Jonno:**\n\nApnar jekono .html file ekhane document"
      " hishebe send korun. File namer sheshe oboshshoi `.html` thakte hobe,"
      " taholei ami automatic URL-er sheshe `-by-tamim` add kore Netlify-e host"
      " kore live URL diye dibo!",
      parse_mode="Markdown",
  )


# --- ACCOUNT BUTTON HANDLER ---
@bot.message_handler(func=lambda message: message.text == "👤 Account")
def account_info(message):
  user = message.from_user
  user_id = user.id
  name = user.first_name if user.first_name else "Unknown"
  username = f"@{user.username}" if user.username else "Nai"

  data = load_data()
  user_hosted = data["user_file_counts"].get(str(user_id), 0)
  pkg_status = get_user_package(user_id)

  acc_text = (
      f"👤 **APNAR ACCOUNT INFO**\n\n"
      f"• **Nam:** `{name}`\n"
      f"• **Username:** `{username}`\n"
      f"• **User ID:** `{user_id}`\n"
      f"• **Package Status:** `{pkg_status}`\n"
      f"• **Total Hosted File:** `{user_hosted}`"
  )
  bot.send_message(message.chat.id, acc_text, parse_mode="Markdown")


# --- BUY PKG BUTTON & INLINE PACKAGE LIST ---
@bot.message_handler(func=lambda message: message.text == "🛒 Buy Pkg")
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
      "🛒 **FILE HOSTING PACKAGES LIST**\n\nNicher package gulo theke apnar"
      " pochhondo moto package select korun:",
      reply_markup=markup,
      parse_mode="Markdown",
  )


@bot.callback_query_handler(func=lambda call: call.data.startswith("pkg_"))
def select_package_callback(call):
  pkg_name = call.data.replace("pkg_", "").replace("_", " ")
  bot.answer_callback_query(call.id)

  instructions = (
      f"💳 **APNI SELECT KORECHEN:** `{pkg_name}`\n\n"
      f"• **bKash Personal Number:** `{BKASH_NUMBER}`\n\n"
      f"⚠️ **Kibabe Taka Pathaben O Confirm Korben?**\n"
      f"1. Uporer number-e bKash Send Money korun.\n"
      f"2. Tarpor nicher niyome command din:\n"
      f"`/pay <Package_Name> <TrxID> <SenderNumber>`\n\n"
      f"*(Udahoron: `/pay Unlimited ABC123XYZ 01812345678`)*\n\n"
      f"Admin check kore apnar package active kore dibe!"
  )
  bot.send_message(call.message.chat.id, instructions, parse_mode="Markdown")


# --- /PAY COMMAND FOR USERS ---
@bot.message_handler(commands=["pay"])
def payment_request(message):
  user_id = message.from_user.id
  args = message.text.split(maxsplit=3)

  if len(args) < 4:
    bot.reply_to(
        message,
        "❌ **Sothik niyome payment request din:**\n`/pay <Package_Name>"
        " <TrxID> <SenderNumber>`\n\nUdahoron: `/pay Unlimited TrxID12345"
        " 01812345678`",
        parse_mode="Markdown",
    )
    return

  pkg_name = args[1]
  trx_id = args[2]
  sender_num = args[3]
  username = (
      f"@{message.from_user.username}"
      if message.from_user.username
      else message.from_user.first_name
  )

  data = load_data()
  admins_list = data.get("admins", [MASTER_OWNER_ID])

  markup = types.InlineKeyboardMarkup()
  confirm_btn = types.InlineKeyboardButton(
      "✅ Confirm Payment", callback_data=f"app_pay_{user_id}_{pkg_name}"
  )
  reject_btn = types.InlineKeyboardButton(
      "❌ Reject", callback_data=f"rej_pay_{user_id}"
  )
  markup.add(confirm_btn, reject_btn)

  admin_msg = (
      f"🔔 **NEW PAYMENT REQUEST!**\n\n"
      f"👤 User: {username} (`{user_id}`)\n"
      f"📦 Package: `{pkg_name}`\n"
      f"💳 TrxID: `{trx_id}`\n"
      f"📱 Sender Number: `{sender_num}`\n\n"
      f"Confirm korle user-er package automatic active hoye jabe."
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
    pkg_name = (
        "_".join(parts[3:]) if len(parts) > 3 else "Unlimited"
    )
    if "premium_users" not in data:
      data["premium_users"] = {}
    data["premium_users"][str(target_user_id)] = pkg_name
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
          f"🎉 **Congratulations!**\n\nApnar bKash payment admin successful"
          f" confirm korechen. Ekhon apnar account-e `{pkg_name}` package"
          f" active kore dewa hoyeche!",
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
          " reject korechen. Sothik TrxID ebong number diye abar chesta korun"
          " ba owner-er sathe jogajog korun.",
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

  pkg_info = get_user_package(user_id)
  if "Free" in pkg_info:
    free_limit = max(0, 3 - user_hosted)
    limit_text = f"{free_limit} free slots left (Hosted: {user_hosted})"
  else:
    limit_text = f"{pkg_info} (Hosted: {user_hosted})"

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
        f" Premium Users: `{len(data.get('premium_users', {}))}`"
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

  pkg_info = get_user_package(user_id)
  is_free_user = "Free" in pkg_info

  if is_free_user and user_hosted_count >= 3:
    bot.reply_to(
        message,
        "❌ **Free Limit Shes!**\n\nApnar free 3 ti file host korar limit"
        " sesh hoyeche. Aro host korte `🛒 Buy Pkg` button theke package"
        " kinun.",
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
        "❌ **Bhul Format!**\n\nFile-er nam jekono kichu hok na keno, tar"
        " sheshe oboshshoi `.html` thakte hobe.",
        parse_mode="Markdown",
    )
    return

  msg = bot.reply_to(
      message,
      "⏳ File download hochche ebong custom name soho Netlify-e host kora"
      " hocche...",
      parse_mode="Markdown",
  )

  try:
    file_path = bot.get_file(file_info.file_id)
    downloaded_file = bot.download_file(file_path.file_path)

    # Clean file name and format custom URL: [name]-by-tamim
    base_name = os.path.splitext(file_name)[0].lower()
    # Remove unwanted characters for netlify subdomain compatibility
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
          "❌ **Custom site toiri byrtho! (Ei namti already onnoke niyeche,"
          " onno nam diye try korun)**\nError:"
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