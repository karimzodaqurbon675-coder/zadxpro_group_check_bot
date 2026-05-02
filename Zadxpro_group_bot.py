import telebot
import time
import threading
import json
from telebot import types

API_TOKEN = '7973873315:AAFvL7jA1p5laL38dvaDTV2Q2fCY6zzEB1k'
YUSUF_CHANNELS = ['@zadxproooo', '@zadxprootziv']
ADMIN_ID = 7424107874

bot = telebot.TeleBot(API_TOKEN)

group_db = {}
user_warnings = {}
user_last_message = {}
all_groups = set()
invite_stats = {}

# --- ЁРИДИҲАНДАҲО ---

def is_subscribed(user_id, channels):
    for ch in channels:
        try:
            status = bot.get_chat_member(ch, user_id).status
            if status not in ['member', 'administrator', 'creator']:
                return False
        except Exception as e:
            print(f"Хато дар is_subscribed: {e}")
            return True
    return True

def delete_later(chat_id, message_id, delay=30):
    def del_msg():
        time.sleep(delay)
        try:
            bot.delete_message(chat_id, message_id)
        except:
            pass
    threading.Thread(target=del_msg, daemon=True).start()

def get_db(gid):
    if gid not in group_db:
        group_db[gid] = {
            'channels': [],
            'spam': True,
            'rules': None,
            'min_len': None,
            'max_len': None,
            'punish': {},
            'forward_group': None
        }
    return group_db[gid]

def parse_time(val):
    if val == '0': return 0
    if val.endswith('m'): return int(val[:-1]) * 60
    if val.endswith('h'): return int(val[:-1]) * 3600
    if val.endswith('d'): return int(val[:-1]) * 86400
    return int(val)

def get_forward_group():
    try:
        with open('forward_group.json', 'r') as f:
            return json.load(f).get('group_id')
    except:
        return None

# ============================================================
# ЛИЧКА — /start
# ============================================================

@bot.message_handler(commands=['start'], func=lambda m: m.chat.type == 'private')
def start_private(message):
    bot_info = bot.get_me()
    add_url = f"https://t.me/{bot_info.username}?startgroup=true&admin=delete_messages+restrict_members"

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("➕ Ба гурӯҳат ботро илова кун", url=add_url))
    markup.add(types.InlineKeyboardButton("🚨 Командҳо", callback_data="show_commands"))
    markup.add(types.InlineKeyboardButton("📢 Админи бот", url="https://t.me/zadxpr0"))

    bot.send_message(
        message.chat.id,
        f"👋 *Салом, {message.from_user.first_name}!*\n\n"
        f"🤖 Боти идоракунии гурӯҳ\n\n"
        f"👇 Аз тугмаҳо истифода баред:",
        parse_mode="Markdown",
        reply_markup=markup
    )

# ============================================================
# САЛОМ — БО КНОПКАИ КОИДАҲО
# ============================================================

@bot.message_handler(content_types=['new_chat_members'])
def welcome(message):
    gid = message.chat.id
    all_groups.add(gid)
    db = get_db(gid)

    for user in message.new_chat_members:
        if user.is_bot:
            continue

        if message.from_user and not message.from_user.is_bot:
            inviter_id = message.from_user.id
            if inviter_id != user.id:
                if gid not in invite_stats:
                    invite_stats[gid] = {}
                invite_stats[gid][inviter_id] = invite_stats[gid].get(inviter_id, 0) + 1

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(
            "📋 Коидаҳои гурӯҳ",
            callback_data=f"rules#{gid}"
        ))

        msg = bot.send_message(
            gid,
            f"👋 *Салом, {user.first_name}!*\n"
            f"Хуш омадед ба гурӯҳи мо! 🎉\n\n"
            f"📋 Коидаҳоро хонед 👇",
            parse_mode="Markdown",
            reply_markup=markup
        )
        delete_later(gid, msg.message_id, 60)

    try:
        bot.delete_message(gid, message.message_id)
    except:
        pass

# ============================================================
# АЛВИДО
# ============================================================

@bot.message_handler(content_types=['left_chat_member'])
def goodbye(message):
    gid = message.chat.id
    user = message.left_chat_member
    if user.is_bot:
        return
    msg = bot.send_message(
        gid,
        f"👋 *Алвидо, {user.first_name}!*\nБарат муваффақият! 😢",
        parse_mode="Markdown"
    )
    delete_later(gid, msg.message_id, 30)
    try:
        bot.delete_message(gid, message.message_id)
    except:
        pass

# ============================================================
# /checkadd — ТОП 10
# ============================================================

@bot.message_handler(commands=['checkadd'])
def check_add(message):
    if message.chat.type == 'private': return
    if bot.get_chat_member(message.chat.id, message.from_user.id).status not in ['administrator', 'creator']: return

    gid = message.chat.id
    stats = invite_stats.get(gid, {})

    if not stats:
        msg = bot.send_message(gid, "📊 Ҳанӯз ҳеҷ кас одам наовардааст.")
        delete_later(gid, msg.message_id)
        try: bot.delete_message(gid, message.message_id)
        except: pass
        return

    sorted_stats = sorted(stats.items(), key=lambda x: x[1], reverse=True)[:10]
    medals = ["🥇","🥈","🥉","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]
    text = "🏆 *Топ-10 нафаре ки бештар одам овардааст:*\n\n"

    for i, (uid, count) in enumerate(sorted_stats):
        try:
            member = bot.get_chat_member(gid, uid)
            name = member.user.first_name
            username = f"@{member.user.username}" if member.user.username else name
        except:
            username = f"ID:{uid}"
        text += f"{medals[i]} {username} — *{count} одам*\n"

    msg = bot.send_message(gid, text, parse_mode="Markdown")
    delete_later(gid, msg.message_id, 60)
    try: bot.delete_message(gid, message.message_id)
    except: pass

# ============================================================
# ЛИЧКА → ГУРӮҲ (Forward)
# ============================================================

@bot.message_handler(commands=['setgroup'], func=lambda m: m.chat.type == 'private')
def set_group(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ Фақат барои соҳиби бот!")
        return
    args = message.text.split()
    if len(args) < 2:
        bot.send_message(message.chat.id,
            "⚠️ Намуна: `/setgroup -1001234567890`\n\n"
            "ID-и гурӯҳатро бо `/getid` гир",
            parse_mode="Markdown"
        )
        return
    try:
        group_id = int(args[1])
        with open('forward_group.json', 'w') as f:
            json.dump({'group_id': group_id}, f)
        bot.send_message(message.chat.id, f"✅ Гурӯҳ сабт шуд! ID: `{group_id}`", parse_mode="Markdown")
    except:
        bot.send_message(message.chat.id, "❌ ID нодуруст аст!")

@bot.message_handler(commands=['getid'])
def get_id(message):
    gid = message.chat.id
    msg = bot.send_message(gid, f"🆔 ID: `{gid}`", parse_mode="Markdown")
    if message.chat.type != 'private':
        delete_later(gid, msg.message_id, 30)
        try: bot.delete_message(gid, message.message_id)
        except: pass

@bot.message_handler(
    func=lambda m: m.chat.type == 'private' and m.from_user.id == ADMIN_ID,
    content_types=['text', 'photo', 'video', 'document', 'audio', 'voice', 'sticker']
)
def private_to_group(message):
    if message.text and message.text.startswith('/'):
        return
    target_group = get_forward_group()
    if not target_group:
        bot.send_message(message.chat.id,
            "⚠️ Аввал гурӯҳро танзим кун:\n`/setgroup -1001234567890`",
            parse_mode="Markdown"
        )
        return
    try:
        bot.forward_message(target_group, message.chat.id, message.message_id)
        bot.send_message(message.chat.id, "✅ Паём ба гурӯҳ фиристода шуд!")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Хато: {e}")

# ============================================================
# КОМАНДАҲОИ АДМИН
# ============================================================

@bot.message_handler(commands=['setrules'])
def set_rules(message):
    if message.chat.type == 'private': return
    if bot.get_chat_member(message.chat.id, message.from_user.id).status not in ['administrator', 'creator']: return
    gid = message.chat.id
    parts = message.text.split(None, 1)
    if len(parts) < 2:
        msg = bot.reply_to(message, "⚠️ Намуна: `/setrules матни коидаҳо`", parse_mode="Markdown")
        delete_later(gid, msg.message_id)
        return
    get_db(gid)['rules'] = parts[1]
    msg = bot.send_message(gid, "✅ Коидаҳо сабт шуд!")
    delete_later(gid, msg.message_id)
    try: bot.delete_message(gid, message.message_id)
    except: pass

@bot.message_handler(commands=['setlimit'])
def set_limit(message):
    if message.chat.type == 'private': return
    if bot.get_chat_member(message.chat.id, message.from_user.id).status not in ['administrator', 'creator']: return
    gid = message.chat.id
    args = message.text.split()
    if len(args) < 3:
        msg = bot.reply_to(message, "⚠️ Намуна: `/setlimit 1 100`", parse_mode="Markdown")
        delete_later(gid, msg.message_id)
        return
    try:
        mn, mx = int(args[1]), int(args[2])
        db = get_db(gid)
        db['min_len'] = mn
        db['max_len'] = mx
        msg = bot.send_message(gid, f"✅ Дарозии паём: аз {mn} то {mx} харф.")
        delete_later(gid, msg.message_id)
    except:
        pass
    try: bot.delete_message(gid, message.message_id)
    except: pass

@bot.message_handler(commands=['setpunish'])
def set_punish(message):
    if message.chat.type == 'private': return
    if bot.get_chat_member(message.chat.id, message.from_user.id).status not in ['administrator', 'creator']: return
    gid = message.chat.id
    args = message.text.split()
    if len(args) < 2:
        msg = bot.send_message(gid,
            "⚠️ Намуна: `/setpunish 1=10m 2=2h 3=1d`\n"
            "🔹 m=дақиқа h=соат d=рӯз 0=абадӣ бан",
            parse_mode="Markdown"
        )
        delete_later(gid, msg.message_id)
        return
    db = get_db(gid)
    result = []
    for arg in args[1:]:
        if '=' in arg:
            level, val = arg.split('=')
            try:
                db['punish'][int(level)] = parse_time(val)
                result.append(f"Огоҳӣ {level} → {'абадӣ' if val=='0' else val}")
            except: pass
    msg = bot.send_message(gid, "✅ Ҷазоҳо:\n" + "\n".join(result))
    delete_later(gid, msg.message_id)
    try: bot.delete_message(gid, message.message_id)
    except: pass

@bot.message_handler(commands=['unban'])
def unban_user(message):
    if message.chat.type == 'private': return
    if bot.get_chat_member(message.chat.id, message.from_user.id).status not in ['administrator', 'creator']: return
    gid = message.chat.id
    if not message.reply_to_message:
        msg = bot.send_message(gid, "⚠️ Ба паём reply карда `/unban` навис!", parse_mode="Markdown")
        delete_later(gid, msg.message_id)
        try: bot.delete_message(gid, message.message_id)
        except: pass
        return
    uid = message.reply_to_message.from_user.id
    name = message.reply_to_message.from_user.first_name
    try: bot.unban_chat_member(gid, uid, only_if_banned=True)
    except: pass
    try:
        bot.restrict_chat_member(gid, uid,
            can_send_messages=True, can_send_media_messages=True,
            can_send_other_messages=True, can_add_web_page_previews=True)
    except: pass
    if uid in user_warnings:
        del user_warnings[uid]
    msg = bot.send_message(gid, f"✅ {name} аз блок озод шуд!")
    delete_later(gid, msg.message_id)
    try: bot.delete_message(gid, message.message_id)
    except: pass

@bot.message_handler(commands=['addchannel'])
def add_ch(message):
    if message.chat.type == 'private': return
    if bot.get_chat_member(message.chat.id, message.from_user.id).status not in ['administrator', 'creator']: return
    args = message.text.split()
    if len(args) < 2 or not args[1].startswith('@'):
        msg = bot.reply_to(message, "⚠️ Намуна: `/addchannel @канал`", parse_mode="Markdown")
        delete_later(message.chat.id, msg.message_id)
        return
    gid = message.chat.id
    db = get_db(gid)
    if args[1] not in db['channels']:
        db['channels'].append(args[1])
    msg = bot.send_message(gid, f"✅ Канали {args[1]} илова шуд!")
    delete_later(gid, msg.message_id)
    try: bot.delete_message(gid, message.message_id)
    except: pass

@bot.message_handler(commands=['delchannel'])
def del_ch(message):
    if message.chat.type == 'private': return
    if bot.get_chat_member(message.chat.id, message.from_user.id).status not in ['administrator', 'creator']: return
    args = message.text.split()
    if len(args) < 2: return
    gid = message.chat.id
    db = get_db(gid)
    if args[1] in db['channels']:
        db['channels'].remove(args[1])
    msg = bot.send_message(gid, f"✅ Канали {args[1]} хориҷ шуд.")
    delete_later(gid, msg.message_id)
    try: bot.delete_message(gid, message.message_id)
    except: pass

@bot.message_handler(commands=['onspam'])
def on_spam(message):
    if message.chat.type == 'private': return
    if bot.get_chat_member(message.chat.id, message.from_user.id).status not in ['administrator', 'creator']: return
    gid = message.chat.id
    get_db(gid)['spam'] = True
    msg = bot.send_message(gid, "🛡 Анти-спам ФАЪОЛ шуд!")
    delete_later(gid, msg.message_id)
    try: bot.delete_message(gid, message.message_id)
    except: pass

@bot.message_handler(commands=['offspam'])
def off_spam(message):
    if message.chat.type == 'private': return
    if bot.get_chat_member(message.chat.id, message.from_user.id).status not in ['administrator', 'creator']: return
    gid = message.chat.id
    get_db(gid)['spam'] = False
    msg = bot.send_message(gid, "🔓 Анти-спам ХОМӮШ шуд!")
    delete_later(gid, msg.message_id)
    try: bot.delete_message(gid, message.message_id)
    except: pass

@bot.message_handler(commands=['broadcast'], func=lambda m: m.chat.type == 'private')
def broadcast_all(message):
    if message.from_user.id != ADMIN_ID: return
    parts = message.text.split(None, 1)
    if len(parts) < 2:
        bot.send_message(message.chat.id, "⚠️ Намуна: `/broadcast матн`", parse_mode="Markdown")
        return
    success = fail = 0
    for gid in all_groups:
        try:
            bot.send_message(gid, f"📢 *Эълон:*\n\n{parts[1]}", parse_mode="Markdown")
            success += 1
            time.sleep(0.1)
        except:
            fail += 1
    bot.send_message(message.chat.id, f"✅ Муваффақ: {success}\n❌ Хато: {fail}")

@bot.message_handler(commands=['announce'])
def announce_group(message):
    if message.chat.type == 'private': return
    if bot.get_chat_member(message.chat.id, message.from_user.id).status not in ['administrator', 'creator']: return
    gid = message.chat.id
    parts = message.text.split(None, 1)
    if len(parts) < 2:
        msg = bot.send_message(gid, "⚠️ Намуна: `/announce матн`", parse_mode="Markdown")
        delete_later(gid, msg.message_id)
        try: bot.delete_message(gid, message.message_id)
        except: pass
        return
    try: bot.delete_message(gid, message.message_id)
    except: pass
    msg = bot.send_message(gid, f"📢 *Эълон:*\n\n{parts[1]}", parse_mode="Markdown")
    delete_later(gid, msg.message_id, 3600)

# ============================================================
# НАЗОРАТИ ПАЁМҲО
# ============================================================

@bot.message_handler(
    func=lambda m: m.chat.type in ['group', 'supergroup'],
    content_types=['text', 'photo', 'video']
)
def group_control(message):
    gid = message.chat.id
    all_groups.add(gid)

    if bot.get_chat_member(gid, message.from_user.id).status in ['administrator', 'creator']:
        return

    uid = message.from_user.id
    db = get_db(gid)
    name = message.from_user.first_name

    # ФЛУД
    now = time.time()
    if gid not in user_last_message:
        user_last_message[gid] = {}
    last = user_last_message[gid].get(uid, 0)
    if now - last < 5:
        try: bot.delete_message(gid, message.message_id)
        except: pass
        msg = bot.send_message(gid, f"⏳ {name}, 5 сония интизор шавед!")
        delete_later(gid, msg.message_id, 5)
        return
    user_last_message[gid][uid] = now

    # ДАРОЗИИ ПАЁМ
    if message.text and (db['min_len'] is not None or db['max_len'] is not None):
        ln = len(message.text)
        mn = db['min_len'] or 0
        mx = db['max_len'] or 999999
        if ln < mn or ln > mx:
            try: bot.delete_message(gid, message.message_id)
            except: pass
            msg = bot.send_message(gid, f"⚠️ {name}, паём бояд аз {mn} то {mx} харф бошад!")
            delete_later(gid, msg.message_id)
            return

    # САНҶИШИ ОБУНА
    if db['channels']:
        if not is_subscribed(uid, db['channels']):
            try: bot.delete_message(gid, message.message_id)
            except: pass
            markup = types.InlineKeyboardMarkup()
            for ch in db['channels']:
                markup.add(types.InlineKeyboardButton(f"Обуна ба {ch}", url=f"https://t.me/{ch[1:]}"))
            markup.add(types.InlineKeyboardButton("✅ Санҷиш", callback_data="check_ramazon"))
            msg = bot.send_message(gid, f"⚠️ {name}, аввал обуна шавед!", reply_markup=markup)
            delete_later(gid, msg.message_id)
            return

    # АНТИ-СПАМ
    if db.get('spam', False):
        text = message.text.lower() if message.text else ""
        if any(x in text for x in ["http", "t.me/", "@"]):
            try: bot.delete_message(gid, message.message_id)
            except: pass
            user_warnings[uid] = user_warnings.get(uid, 0) + 1
            w = user_warnings[uid]
            punish = db.get('punish') or {1: 0, 2: 600, 3: 86400}
            duration = punish.get(w, 86400)
            if duration == 0:
                bot.ban_chat_member(gid, uid)
                msg = bot.send_message(gid, f"🚫 {name} абадӣ бан шуд!")
            else:
                bot.restrict_chat_member(gid, uid, until_date=int(time.time()) + duration)
                d = duration//86400; h = (duration%86400)//3600; m = (duration%3600)//60
                t = f"{d} рӯз" if d >= 1 else f"{h} соат" if h >= 1 else f"{m} дақиқа"
                msg = bot.send_message(gid, f"🔇 {name} {t} блок шуд! (Огоҳӣ {w})")
            delete_later(gid, msg.message_id)

# ============================================================
# CALLBACKS
# ============================================================

@bot.callback_query_handler(func=lambda call: True)
def calls(call):
    bot_info = bot.get_me()

    if call.data == "check_yusuf":
        if is_subscribed(call.from_user.id, YUSUF_CHANNELS):
            markup = types.InlineKeyboardMarkup()
            add_url = f"https://t.me/{bot_info.username}?startgroup=true&admin=delete_messages+restrict_members"
            markup.add(types.InlineKeyboardButton("➕ Ба гурӯҳат ботро илова кун", url=add_url))
            markup.add(types.InlineKeyboardButton("🚨 Командҳо", callback_data="show_commands"))
            markup.add(types.InlineKeyboardButton("📢 Канали мо", url="https://t.me/zadxproooo"))
            bot.edit_message_text(
                "✅ Обуна тасдиқ шуд!\n\n👇 Аз тугмаҳо истифода баред:",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup
            )
        else:
            bot.answer_callback_query(call.id, "Обуна нашудаед! ❌", show_alert=True)

    elif call.data == "show_commands":
        text = (
            "🚨 *Командаҳои бот:*\n\n"
            "➕ `/addchannel @ном` — Иловаи канал\n"
            "➖ `/delchannel @ном` — Хориҷ кардан\n"
            "🛡 `/onspam` — Анти-спам ON\n"
            "🔓 `/offspam` — Анти-спам OFF\n"
            "📋 `/setrules матн` — Коидаҳо\n"
            "📏 `/setlimit 1 100` — Дарозии паём\n"
            "⚖️ `/setpunish 1=10m 2=1h 3=1d` — Ҷазо\n"
            "🔓 `/unban` — Аз блок гирифтан (reply)\n"
            "📢 `/announce матн` — Эълон ба гурӯҳ\n"
            "🏆 `/checkadd` — Топ-10 фаъол\n"
            "🆔 `/getid` — ID-и гурӯҳ\n\n"
            "👑 *Личка (соҳиби бот):*\n"
            "📡 `/broadcast матн` — Ба ҳамаи гурӯҳҳо\n"
            "🔗 `/setgroup ID` — Гурӯҳи forward\n"
            "✉️ Ҳар паём дар личка → ба гурӯҳ"
        )
        msg = bot.send_message(call.message.chat.id, text, parse_mode="Markdown")
        delete_later(call.message.chat.id, msg.message_id, 60)
        bot.answer_callback_query(call.id)

    elif call.data == "check_ramazon":
        gid = call.message.chat.id
        db = get_db(gid)
        if is_subscribed(call.from_user.id, db['channels']):
            bot.answer_callback_query(call.id, "Обуна тасдиқ шуд ✅", show_alert=True)
            try: bot.delete_message(gid, call.message.message_id)
            except: pass
        else:
            bot.answer_callback_query(call.id, "Обуна нашудаед! ❌", show_alert=True)

    elif call.data.startswith("rules#"):
        gid = int(call.data.split("#")[1])
        db = get_db(gid)
        rules = db.get('rules') or (
            "📋 Коидаҳои гурӯҳ:\n\n"
            "1️⃣ Реклама МАНЪ аст\n"
            "2️⃣ Ҳурмат кунед\n"
            "3️⃣ Спам накунед\n\n"
            "⚠️ Риоя накунӣ — блок мешавӣ!"
        )
        bot.answer_callback_query(call.id, rules, show_alert=True)

print("Бот фаъол шуд... ✅")
bot.polling(none_stop=True)