import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta, timezone
import asyncio
import json
import os
import re

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.guilds = True
intents.voice_states = True
intents.messages = True
intents.guild_messages = True

bot = commands.Bot(command_prefix='!', intents=intents)

WARN_FILE = "warns.json"
SPAM_FILE = "spam.json"
TICKET_FILE = "tickets.json"
TIKET_FILE = "tikets.json"
PUNISHMENT_APPEAL_FILE = "punishment_appeals.json"
GLOBAL_COUNTER_FILE = "global_counter.json"

MAX_WARNS = 3
WARN_MUTE_DURATION = 12 * 3600
AUTO_UNWARN_DAYS = 3
SPAM_MUTE_1 = 30 * 60
SPAM_MUTE_2 = 12 * 3600
SPAM_MUTE_3 = 5 * 24 * 3600
SPAM_LIMIT = 3
SPAM_TIME_WINDOW = 10

COLOR_MAIN = discord.Color.blue()
COLOR_LIGHT = discord.Color.teal()
COLOR_INFO = discord.Color.blue()
COLOR_ACCENT = discord.Color.purple()
COLOR_VIOLET = discord.Color.purple()
COLOR_YELLOW = discord.Color.gold()
COLOR_AZURE = discord.Color.from_rgb(0, 150, 255)

ANTI_RAID_GREEN = "green"
ANTI_RAID_YELLOW = "yellow"
ANTI_RAID_RED = "red"
RAID_JOIN_THRESHOLD = 5
RAID_JOIN_TIMEFRAME = 60
RAID_RED_THRESHOLD = 10
RED_DURATION = 20 * 60
RED_EXTEND_DURATION = 10 * 60
RED_IDLE_RELEASE = 300
YELLOW_IDLE_RELEASE = 300
SLOWMODE_DELAY = 20
LOCKDOWN_PERMS = [
    "send_messages", "add_reactions", "create_public_threads",
    "create_private_threads", "send_messages_in_threads",
    "connect", "speak"
]

LOG_ALL_CHANNEL_ID = 1543703750919725086
LOG_CHAT_CHANNEL_ID = 1543703774491713556
LOG_INVITE_CHANNEL_ID = 1543703801595433051
ALERT_ROLE_ID = 1540355086289600522
TARGET_GUILD_ID = 1097467632329969764
TICKET_CHANNEL_ID = 1542976947339132989
TIKET_CHANNEL_ID = 1542977042331476050
TIKET_PING_ROLE_ID = 1507395640445898782
MODERATOR_ROLE_ID = 1508078492552663141
TICKET_MODERATOR_ROLE_ID = 1543330529036996708
ADMIN_ROLE_ID = 1507395265215074434
CREATOR_ROLE_ID = 1491372311310368818

MODERATION_CHANNEL_ID = 1543393528762073108
APPEAL_CHANNEL_ID = 1543257702099320902
TICKET_PING_ROLE_1 = TICKET_MODERATOR_ROLE_ID
TICKET_PING_ROLE_2 = ADMIN_ROLE_ID
TIKET_PING_ROLE = TIKET_PING_ROLE_ID
MODERATION_PING_ROLE = MODERATOR_ROLE_ID

GROUP_TICKET_MOD = [TICKET_MODERATOR_ROLE_ID]
GROUP_ADMIN = [ADMIN_ROLE_ID]
GROUP_MOD = [MODERATOR_ROLE_ID]

EMOJI_SUPPORT = discord.PartialEmoji(name="Support", id=1555909739068526722)
EMOJI_QUESTION = discord.PartialEmoji(name="question", id=1555909725894217848)
EMOJI_APPEAL = discord.PartialEmoji(name="appeal1", id=1555877838442332281)
EMOJI_STAFF = discord.PartialEmoji(name="staff_1", id=1555909732525670420)
EMOJI_FORM = discord.PartialEmoji(name="form", id=1555877859527102474)
EMOJI_FORMULARIO = discord.PartialEmoji(name="Formulario", id=1555919581082558485)
EMOJI_JUDGE = discord.PartialEmoji(name="Judge", id=1555909708580130897)
EMOJI_TRASH = discord.PartialEmoji(name="bot_rubbishbin", id=1555909691207590038)
EMOJI_WRITING = discord.PartialEmoji(name="Writing", id=1555919585776115783)
EMOJI_ETIKET = discord.PartialEmoji(name="etiket", id=1555909701202616320)
EMOJI_APPEAL_BTN = discord.PartialEmoji(name="Appeal", id=1555877839885303839)
EMOJI_PAIRLY_APPEAL = discord.PartialEmoji(name="pairly_bt_appeal", id=1555909724623343656)
EMOJI_SHIELD = "<:bot_shield:1555909694369964072>"
LOG_EMOJI = "<:z_9_platform_pc:1558567241933656064>"

ERR_ACTION = "Error (code: 0231)"
ERR_UNAVAILABLE = "Error (code: 0232)"

raid_status = {}
join_tracker = {}
_invite_cache = {}
_persistent_registered = False


def has_role(member, role_id):
    if not isinstance(member, discord.Member):
        return False
    return any(role.id == role_id for role in member.roles)


def is_mod(member):
    if not isinstance(member, discord.Member):
        return False
    if member.id == member.guild.owner_id:
        return True
    if member.guild_permissions.administrator:
        return True
    return has_role(member, MODERATOR_ROLE_ID)


def is_admin(member):
    if not isinstance(member, discord.Member):
        return False
    if member.id == member.guild.owner_id:
        return True
    if member.guild_permissions.administrator:
        return True
    return has_role(member, ADMIN_ROLE_ID) or is_mod(member)


def is_ticket_mod(member):
    if not isinstance(member, discord.Member):
        return False
    if member.id == member.guild.owner_id:
        return True
    if member.guild_permissions.administrator:
        return True
    return has_role(member, TICKET_MODERATOR_ROLE_ID) or is_admin(member)


def is_admin_or_owner(interaction):
    return interaction.user.id == interaction.guild.owner_id or interaction.user.guild_permissions.administrator


def is_target_guild(guild):
    return guild.id == TARGET_GUILD_ID


def get_staff_label(member):
    if not isinstance(member, discord.Member):
        return "Модератор"
    if has_role(member, CREATOR_ROLE_ID):
        return "Создатель"
    if has_role(member, MODERATOR_ROLE_ID):
        return "Администратор"
    if has_role(member, TICKET_MODERATOR_ROLE_ID) or has_role(member, ADMIN_ROLE_ID):
        return "Модератор"
    return "Модератор"


def pluralize_time(amount, unit):
    n = abs(int(amount)) % 100
    n1 = n % 10
    if 11 <= n <= 19:
        idx = 2
    elif n1 == 1:
        idx = 0
    elif 2 <= n1 <= 4:
        idx = 1
    else:
        idx = 2

    forms = {
        'second': ('секунда', 'секунды', 'секунд'),
        'minute': ('минута', 'минуты', 'минут'),
        'hour': ('час', 'часа', 'часов'),
        'day': ('день', 'дня', 'дней'),
    }
    f = forms.get(unit, ('', '', ''))
    return f"{amount} {f[idx]}"


def get_next_global_number():
    data = {'counter': 0}
    if os.path.exists(GLOBAL_COUNTER_FILE):
        try:
            with open(GLOBAL_COUNTER_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if not isinstance(data, dict):
                    data = {'counter': 0}
        except:
            data = {'counter': 0}
    if 'counter' not in data:
        data['counter'] = 0
    data['counter'] += 1
    try:
        with open(GLOBAL_COUNTER_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
    except:
        pass
    return data['counter']


def format_global_number(num):
    return f"`№ {num:05d}`"


def load_warns():
    if os.path.exists(WARN_FILE):
        try:
            with open(WARN_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_warns(warns):
    try:
        with open(WARN_FILE, 'w', encoding='utf-8') as f:
            json.dump(warns, f, indent=4, ensure_ascii=False)
    except:
        pass


def get_user_warns(guild_id, user_id):
    warns = load_warns()
    guild_key, user_key = str(guild_id), str(user_id)
    if guild_key not in warns:
        warns[guild_key] = {}
    if user_key not in warns[guild_key]:
        warns[guild_key][user_key] = []
    return warns[guild_key][user_key]


def save_user_warns(guild_id, user_id, user_warns):
    warns = load_warns()
    guild_key, user_key = str(guild_id), str(user_id)
    if guild_key not in warns:
        warns[guild_key] = {}
    warns[guild_key][user_key] = user_warns
    save_warns(warns)


def clear_user_warns(guild_id, user_id):
    warns = load_warns()
    guild_key, user_key = str(guild_id), str(user_id)
    if guild_key in warns and user_key in warns[guild_key]:
        warns[guild_key][user_key] = []
        save_warns(warns)


def load_spam_data():
    if os.path.exists(SPAM_FILE):
        try:
            with open(SPAM_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_spam_data(spam_data):
    try:
        with open(SPAM_FILE, 'w', encoding='utf-8') as f:
            json.dump(spam_data, f, indent=4, ensure_ascii=False)
    except:
        pass


def get_user_spam(guild_id, user_id):
    spam_data = load_spam_data()
    guild_key, user_key = str(guild_id), str(user_id)
    if guild_key not in spam_data:
        spam_data[guild_key] = {}
    if user_key not in spam_data[guild_key]:
        spam_data[guild_key][user_key] = {'messages': [], 'spam_count': 0, 'last_spam_time': 0}
    return spam_data[guild_key][user_key]


def save_user_spam(guild_id, user_id, user_spam):
    spam_data = load_spam_data()
    guild_key, user_key = str(guild_id), str(user_id)
    if guild_key not in spam_data:
        spam_data[guild_key] = {}
    spam_data[guild_key][user_key] = user_spam
    save_spam_data(spam_data)


def load_tickets():
    if os.path.exists(TICKET_FILE):
        try:
            with open(TICKET_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if not isinstance(data, dict):
                    data = {}
                if 'tickets' not in data or not isinstance(data['tickets'], list):
                    data['tickets'] = []
                return data
        except:
            return {'tickets': []}
    return {'tickets': []}


def save_tickets(tickets_data):
    if not isinstance(tickets_data, dict):
        tickets_data = {'tickets': []}
    if 'tickets' not in tickets_data or not isinstance(tickets_data['tickets'], list):
        tickets_data['tickets'] = []
    try:
        with open(TICKET_FILE, 'w', encoding='utf-8') as f:
            json.dump(tickets_data, f, indent=4, ensure_ascii=False)
    except:
        pass


def load_tikets():
    if os.path.exists(TIKET_FILE):
        try:
            with open(TIKET_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if not isinstance(data, dict):
                    data = {}
                if 'tikets' not in data or not isinstance(data['tikets'], list):
                    data['tikets'] = []
                return data
        except:
            return {'tikets': []}
    return {'tikets': []}


def save_tikets(tikets_data):
    if not isinstance(tikets_data, dict):
        tikets_data = {'tikets': []}
    if 'tikets' not in tikets_data or not isinstance(tikets_data['tikets'], list):
        tikets_data['tikets'] = []
    try:
        with open(TIKET_FILE, 'w', encoding='utf-8') as f:
            json.dump(tikets_data, f, indent=4, ensure_ascii=False)
    except:
        pass


def load_punishment_appeals():
    if os.path.exists(PUNISHMENT_APPEAL_FILE):
        try:
            with open(PUNISHMENT_APPEAL_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if not isinstance(data, dict):
                    data = {}
                if 'appeals' not in data or not isinstance(data['appeals'], list):
                    data['appeals'] = []
                return data
        except:
            return {'appeals': []}
    return {'appeals': []}


def save_punishment_appeals(data):
    if not isinstance(data, dict):
        data = {'appeals': []}
    if 'appeals' not in data or not isinstance(data['appeals'], list):
        data['appeals'] = []
    try:
        with open(PUNISHMENT_APPEAL_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except:
        pass


def normalize_text(text):
    text = text.lower()
    text = re.sub(r'\s+', '', text)
    text = re.sub(r'[^a-zа-яё0-9]', '', text)
    return text


def get_raid_status(guild_id):
    if guild_id not in raid_status:
        raid_status[guild_id] = {
            'status': ANTI_RAID_GREEN,
            'alert_role_id': None,
            'last_join': None,
            'red_until': None,
            'manual_lockdown': False,
            'saved_overwrites': {},
            'slowmode_channels': []
        }
    return raid_status[guild_id]


def get_join_tracker(guild_id):
    if guild_id not in join_tracker:
        join_tracker[guild_id] = []
    return join_tracker[guild_id]


def prune_tracker(guild_id):
    current_time = datetime.now(timezone.utc).timestamp()
    tracker = [t for t in get_join_tracker(guild_id) if current_time - t <= RAID_JOIN_TIMEFRAME]
    join_tracker[guild_id] = tracker
    return tracker


def base_embed(title, color):
    return discord.Embed(title=title, color=color)


def user_embed(title, color, member):
    embed = base_embed(title, color)
    embed.set_thumbnail(url=member.display_avatar.url)
    return embed


def split_embed(embed, name, text):
    chunks = [text[i:i + 1024] for i in range(0, len(text), 1024)] or [text]
    for i, chunk in enumerate(chunks, 1):
        embed.add_field(name=name if i == 1 else f"{name} ({i})", value=chunk, inline=False)


def build_log_layout(title, fields=None, footer=None):
    container = discord.ui.Container()
    container.add_item(discord.ui.TextDisplay(f"{LOG_EMOJI} **{title}**"))
    container.add_item(discord.ui.Separator())
    if fields:
        for label, value in fields:
            container.add_item(discord.ui.TextDisplay(f"{label}: {value}"))
    if footer:
        container.add_item(discord.ui.Separator())
        container.add_item(discord.ui.TextDisplay(footer))
    layout = discord.ui.LayoutView(timeout=None)
    layout.add_item(container)
    return layout


def staff_footer(member):
    if not isinstance(member, discord.Member):
        return f"Модератор: {member}"
    label = get_staff_label(member)
    return f"{label}: {member} | {member.id}"


async def send_log_layout(layout, channel_id, guild=None):
    if guild and not is_target_guild(guild):
        return
    channel = bot.get_channel(channel_id)
    if channel:
        try:
            await channel.send(view=layout)
        except:
            pass


async def send_dm(user, embed, view=None):
    try:
        if view:
            await user.send(embed=embed, view=view)
        else:
            await user.send(embed=embed)
    except:
        pass


async def send_log(embed, channel_id, guild=None):
    if guild and not is_target_guild(guild):
        return
    channel = bot.get_channel(channel_id)
    if channel:
        try:
            await channel.send(embed=embed)
        except:
            pass


async def get_audit_log_actor(guild, action, target=None):
    if not is_target_guild(guild):
        return None
    try:
        async for entry in guild.audit_logs(limit=5, action=action):
            if target and entry.target.id == target.id:
                return entry.user
            if not target:
                return entry.user
    except:
        pass
    return None


async def get_username(user_id):
    try:
        u = await bot.fetch_user(user_id)
        return u.name
    except:
        return "Unknown"


async def build_verdict_dm_layout(ticket_data):
    is_complaint = ticket_data.get('type') in ('complaint', 'moderation')
    ticket_number = ticket_data.get('id', '')
    verdict = ticket_data.get('verdict', '') or ''
    moderator_id = ticket_data.get('moderator_id')

    mod_name = await get_username(moderator_id) if moderator_id else "Unknown"
    moderator_label = "Модератор" if is_complaint else "Агент поддержки"

    container = discord.ui.Container()

    if is_complaint:
        title = f"Решение по вашей жалобе {ticket_number}:"
    else:
        title = f"Решение по вашему тикету {ticket_number}:"

    container.add_item(discord.ui.TextDisplay(f"<:etiket:1555909701202616320> {title}"))
    container.add_item(discord.ui.Separator())
    container.add_item(discord.ui.TextDisplay(verdict))
    container.add_item(discord.ui.Separator())
    container.add_item(discord.ui.TextDisplay(f"{moderator_label}: {mod_name} | {moderator_id}"))
    container.add_item(discord.ui.Separator())

    if is_complaint:
        appeal = ticket_data.get('appeal')
        appeal_verdict = ticket_data.get('appeal_verdict')
        appeal_changed = ticket_data.get('appeal_verdict_changed')

        if appeal_verdict:
            appeal_mod_id = ticket_data.get('appeal_moderator_id')
            appeal_mod_name = await get_username(appeal_mod_id) if appeal_mod_id else "Unknown"

            if appeal_changed:
                title_appeal = "Вердикт по вашей апелляции (изменено)"
            else:
                title_appeal = "Вердикт по вашей апелляции"

            container.add_item(discord.ui.TextDisplay(f"<:etiket:1555909701202616320> {title_appeal}"))
            container.add_item(discord.ui.Separator())
            container.add_item(discord.ui.TextDisplay(appeal_verdict))
            container.add_item(discord.ui.Separator())
            container.add_item(discord.ui.TextDisplay(f"Администратор: {appeal_mod_name} | {appeal_mod_id}"))
            container.add_item(discord.ui.Separator())
        elif appeal:
            container.add_item(discord.ui.TextDisplay("Апелляция подана на рассмотрение администрации."))
            container.add_item(discord.ui.Separator())
        else:
            container.add_item(discord.ui.ActionRow(AppealButton(ticket_number)))

    layout = discord.ui.LayoutView(timeout=None)
    layout.add_item(container)
    return layout


async def send_or_edit_verdict_dm(user_id, ticket_data, existing_message_id=None):
    try:
        user = await bot.fetch_user(user_id)
        layout = await build_verdict_dm_layout(ticket_data)

        if existing_message_id:
            dm_channel = user.dm_channel
            if dm_channel is None:
                dm_channel = await user.create_dm()
            try:
                msg = await dm_channel.fetch_message(existing_message_id)
                await msg.edit(view=layout)
                return existing_message_id
            except:
                msg = await user.send(view=layout)
                return msg.id
        else:
            msg = await user.send(view=layout)
            return msg.id
    except:
        return None


async def delete_dm_message(user_id, message_id):
    try:
        user = await bot.fetch_user(user_id)
        dm_channel = user.dm_channel
        if dm_channel is None:
            dm_channel = await user.create_dm()
        msg = await dm_channel.fetch_message(message_id)
        await msg.delete()
    except:
        pass


async def send_delete_dm(user_id, type_word, ticket_number, reason):
    if type_word == "жалоба":
        title = f"<:bot_rubbishbin:1555909691207590038> Ваш жалоба {ticket_number} удалёна"
    else:
        title = f"<:bot_rubbishbin:1555909691207590038> Ваш тикет {ticket_number} удалён"

    try:
        user = await bot.fetch_user(user_id)
        container = discord.ui.Container()
        container.add_item(discord.ui.TextDisplay(title))
        container.add_item(discord.ui.Separator())
        container.add_item(discord.ui.TextDisplay(reason))
        container.add_item(discord.ui.Separator())
        layout = discord.ui.LayoutView(timeout=None)
        layout.add_item(container)
        await user.send(view=layout)
    except:
        pass


async def check_auto_unwarn():
    await bot.wait_until_ready()
    while not bot.is_closed():
        try:
            warns = load_warns()
            current_time = datetime.now(timezone.utc).timestamp()
            changed = False
            for guild_id in list(warns.keys()):
                for user_id in list(warns[guild_id].keys()):
                    user_warns = warns[guild_id][user_id]
                    if isinstance(user_warns, list):
                        updated_warns = []
                        for warn in user_warns:
                            if isinstance(warn, dict) and 'timestamp' in warn:
                                if current_time - warn['timestamp'] >= AUTO_UNWARN_DAYS * 24 * 3600:
                                    continue
                                updated_warns.append(warn)
                        if len(updated_warns) != len(user_warns):
                            warns[guild_id][user_id] = updated_warns if updated_warns else None
                            changed = True
            if changed:
                save_warns({k: {uk: uv for uk, uv in v.items() if uv} for k, v in warns.items()})
        except:
            pass
        await asyncio.sleep(3600)


async def check_raid_status():
    await bot.wait_until_ready()
    while not bot.is_closed():
        try:
            for guild in bot.guilds:
                if not is_target_guild(guild):
                    continue
                status = get_raid_status(guild.id)
                current_time = datetime.now(timezone.utc).timestamp()
                tracker = prune_tracker(guild.id)
                joins = len(tracker)

                if status['status'] == ANTI_RAID_RED:
                    if joins >= RAID_JOIN_THRESHOLD:
                        status['red_until'] = max(status['red_until'] or 0, current_time + RED_EXTEND_DURATION)
                        status['last_join'] = current_time
                    elif current_time >= (status['red_until'] or 0):
                        status['manual_lockdown'] = False
                        await set_raid_status(guild, ANTI_RAID_GREEN, status)
                elif status['status'] == ANTI_RAID_YELLOW:
                    if joins >= RAID_RED_THRESHOLD:
                        await set_raid_status(guild, ANTI_RAID_RED, status)
                    elif joins < RAID_JOIN_THRESHOLD and status['last_join'] and current_time - status['last_join'] > YELLOW_IDLE_RELEASE:
                        await set_raid_status(guild, ANTI_RAID_GREEN, status)
                elif status['status'] == ANTI_RAID_GREEN and joins >= RAID_JOIN_THRESHOLD:
                    await set_raid_status(guild, ANTI_RAID_YELLOW, status)
        except:
            pass
        await asyncio.sleep(10)


async def set_raid_status(guild, new_status, status, moderator=None):
    if not is_target_guild(guild):
        return
    status['status'] = new_status
    if moderator:
        footer = staff_footer(moderator)
    else:
        footer = "Автоматически"
    if new_status == ANTI_RAID_YELLOW:
        await setup_raid_yellow(guild, status)
        layout = build_log_layout(
            "Антирейд: Повышенная готовность",
            fields=[
                ("Сервер", guild.name),
                ("Статус", "Активирован Жёлтый режим"),
                ("Действие", "Выдана роль Raid Alert всем пользователям"),
            ],
            footer=footer
        )
        await send_log_layout(layout, LOG_ALL_CHANNEL_ID, guild)
    elif new_status == ANTI_RAID_RED:
        status['red_until'] = datetime.now(timezone.utc).timestamp() + RED_DURATION
        await setup_raid_red(guild, status)
        layout = build_log_layout(
            "Антирейд: Полная блокировка",
            fields=[
                ("Сервер", guild.name),
                ("Статус", "Активирован Красный режим"),
                ("Действия", "Каналы заблокированы, приглашения удалены, slowmode включён"),
            ],
            footer=footer
        )
        await send_log_layout(layout, LOG_ALL_CHANNEL_ID, guild)
    elif new_status == ANTI_RAID_GREEN:
        status['manual_lockdown'] = False
        status['red_until'] = None
        status['last_join'] = None
        await setup_raid_green(guild, status)
        layout = build_log_layout(
            "Антирейд: Нормальный режим",
            fields=[
                ("Сервер", guild.name),
                ("Статус", "Деактивирован режим антирейда"),
            ],
            footer=footer
        )
        await send_log_layout(layout, LOG_ALL_CHANNEL_ID, guild)


async def ensure_alert_role(guild, status):
    if not status['alert_role_id']:
        role = discord.utils.get(guild.roles, name="Raid Alert")
        if not role:
            role = await guild.create_role(name="Raid Alert", color=COLOR_INFO, hoist=True)
        status['alert_role_id'] = role.id


async def setup_raid_yellow(guild, status):
    try:
        await ensure_alert_role(guild, status)
        role = guild.get_role(status['alert_role_id'])
        if role:
            for member in guild.members:
                if not member.bot and not member.guild_permissions.administrator and role not in member.roles:
                    try:
                        await member.add_roles(role, reason="Антирейд: повышенная готовность")
                    except:
                        pass
    except:
        pass


async def setup_raid_red(guild, status):
    try:
        for invite in await guild.invites():
            try:
                await invite.delete(reason="Антирейд: блокировка")
            except:
                pass
        status['saved_overwrites'] = {}
        status['slowmode_channels'] = []
        everyone = guild.default_role
        for channel in guild.channels:
            try:
                saved = {perm: getattr(channel.overwrites_for(everyone), perm) for perm in LOCKDOWN_PERMS}
                status['saved_overwrites'][channel.id] = saved
                overwrite = channel.overwrites_for(everyone)
                for perm in LOCKDOWN_PERMS:
                    setattr(overwrite, perm, False)
                await channel.set_permissions(everyone, overwrite=overwrite, reason="Антирейд: блокировка")
                if isinstance(channel, (discord.TextChannel, discord.VoiceChannel)):
                    await channel.edit(slowmode_delay=SLOWMODE_DELAY, reason="Антирейд: блокировка")
                    status['slowmode_channels'].append(channel.id)
            except:
                pass
    except:
        pass


async def setup_raid_green(guild, status):
    try:
        if status['alert_role_id']:
            role = guild.get_role(status['alert_role_id'])
            if role:
                for member in role.members:
                    try:
                        await member.remove_roles(role, reason="Антирейд: снят")
                    except:
                        pass
                try:
                    await role.delete(reason="Антирейд: снят")
                except:
                    pass
            status['alert_role_id'] = None
        everyone = guild.default_role
        for channel_id, saved in status.get('saved_overwrites', {}).items():
            channel = guild.get_channel(channel_id)
            if not channel:
                continue
            try:
                overwrite = channel.overwrites_for(everyone)
                for perm, value in saved.items():
                    setattr(overwrite, perm, value)
                await channel.set_permissions(everyone, overwrite=overwrite if any(saved.values()) else None, reason="Антирейд: снят")
            except:
                pass
        for channel_id in status.get('slowmode_channels', []):
            channel = guild.get_channel(channel_id)
            if channel:
                try:
                    await channel.edit(slowmode_delay=0, reason="Антирейд: снят")
                except:
                    pass
        status['saved_overwrites'] = {}
        status['slowmode_channels'] = []
    except:
        pass


def build_open_complaint_container(ticket_number, ticket_data):
    is_moderation = ticket_data.get('type') == 'moderation'
    title_prefix = "Жалоба на персонал" if is_moderation else "Жалоба"
    user_label = "Имя модератора" if is_moderation else "Имя пользователя"

    container = discord.ui.Container()
    container.add_item(discord.ui.TextDisplay(f"## {title_prefix} {ticket_number}"))
    container.add_item(discord.ui.Separator())
    if is_moderation:
        container.add_item(discord.ui.TextDisplay(f"<@&{MODERATION_PING_ROLE}>"))
    else:
        container.add_item(discord.ui.TextDisplay(f"<@&{TICKET_PING_ROLE_1}> <@&{TICKET_PING_ROLE_2}>"))
    container.add_item(discord.ui.Separator())
    container.add_item(discord.ui.TextDisplay(
        f"Подал: <@{ticket_data.get('author_id')}>\n\n"
        f"Статус: Рассматривается\n\n"
        f"Описание:\n{ticket_data.get('description', '')[:1024]}\n\n"
        f"{user_label}: {ticket_data.get('user_name', '')}\n\n"
        f"Ссылка: {ticket_data.get('message_link', 'Не указано')}"
    ))
    container.add_item(discord.ui.Separator())
    container.add_item(discord.ui.ActionRow(
        VerdictButton(ticket_number, "complaint"),
        DeleteTicketButton(ticket_number, "complaint")
    ))
    return container


def build_closed_complaint_container(ticket_number, ticket_data):
    is_moderation = ticket_data.get('type') == 'moderation'
    title_prefix = "Жалоба на персонал" if is_moderation else "Жалоба"
    user_label = "Имя модератора" if is_moderation else "Имя пользователя"

    container = discord.ui.Container()
    container.add_item(discord.ui.TextDisplay(f"## {title_prefix} {ticket_number}"))
    container.add_item(discord.ui.Separator())
    if is_moderation:
        container.add_item(discord.ui.TextDisplay(f"<@&{MODERATION_PING_ROLE}>"))
    else:
        container.add_item(discord.ui.TextDisplay(f"<@&{TICKET_PING_ROLE_1}> <@&{TICKET_PING_ROLE_2}>"))
    container.add_item(discord.ui.Separator())
    container.add_item(discord.ui.TextDisplay(
        f"Подал: <@{ticket_data.get('author_id')}>\n\n"
        f"Статус: Закрыт\n\n"
        f"Описание:\n{ticket_data.get('description', '')[:1024]}\n\n"
        f"{user_label}: {ticket_data.get('user_name', '')}\n\n"
        f"Ссылка: {ticket_data.get('message_link', 'Не указано')}\n\n"
        f"Вердикт:\n{ticket_data.get('verdict', '')[:1024]}"
    ))
    container.add_item(discord.ui.Separator())
    mod_label = ticket_data.get('moderator_staff_label', 'Модератор')
    mod_name = ticket_data.get('moderator_name', 'Unknown')
    mod_id = ticket_data.get('moderator_id', 0)
    container.add_item(discord.ui.TextDisplay(f"{mod_label}: {mod_name} | {mod_id}"))
    container.add_item(discord.ui.Separator())
    container.add_item(discord.ui.ActionRow(
        ChangeVerdictButton(ticket_number, "complaint"),
        DeleteVerdictButton(ticket_number, "complaint")
    ))
    return container


def build_open_ticket_container(tiket_number, tiket_data):
    container = discord.ui.Container()
    container.add_item(discord.ui.TextDisplay(f"## Тикет {tiket_number}"))
    container.add_item(discord.ui.Separator())
    container.add_item(discord.ui.TextDisplay(f"<@&{TIKET_PING_ROLE}>"))
    container.add_item(discord.ui.Separator())
    container.add_item(discord.ui.TextDisplay(
        f"Автор: <@{tiket_data.get('author_id')}>\n\n"
        f"Тип: {tiket_data.get('type', '')}\n\n"
        f"Статус: Открыт\n\n"
        f"Описание:\n{tiket_data.get('description', '')[:1024]}"
    ))
    container.add_item(discord.ui.Separator())
    container.add_item(discord.ui.ActionRow(
        VerdictButton(tiket_number, "ticket"),
        DeleteTicketButton(tiket_number, "ticket")
    ))
    return container


def build_closed_ticket_container(tiket_number, tiket_data):
    container = discord.ui.Container()
    container.add_item(discord.ui.TextDisplay(f"## Тикет {tiket_number}"))
    container.add_item(discord.ui.Separator())
    container.add_item(discord.ui.TextDisplay(f"<@&{TIKET_PING_ROLE}>"))
    container.add_item(discord.ui.Separator())
    container.add_item(discord.ui.TextDisplay(
        f"Автор: <@{tiket_data.get('author_id')}>\n\n"
        f"Тип: {tiket_data.get('type', '')}\n\n"
        f"Статус: Закрыт\n\n"
        f"Описание:\n{tiket_data.get('description', '')[:1024]}\n\n"
        f"Вердикт:\n{tiket_data.get('verdict', '')[:1024]}"
    ))
    container.add_item(discord.ui.Separator())
    mod_label = tiket_data.get('moderator_staff_label', 'Агент поддержки')
    mod_name = tiket_data.get('moderator_name', 'Unknown')
    mod_id = tiket_data.get('moderator_id', 0)
    container.add_item(discord.ui.TextDisplay(f"{mod_label}: {mod_name} | {mod_id}"))
    container.add_item(discord.ui.Separator())
    container.add_item(discord.ui.ActionRow(
        ChangeVerdictButton(tiket_number, "ticket"),
        DeleteVerdictButton(tiket_number, "ticket")
    ))
    return container


def build_appeal_container(ticket_data):
    ticket_number = ticket_data.get('id', '')
    appeal_text = ticket_data.get('appeal', '') or ''
    appeal_verdict = ticket_data.get('appeal_verdict')
    appeal_mod_id = ticket_data.get('appeal_moderator_id')

    container = discord.ui.Container()
    container.add_item(discord.ui.TextDisplay(f"## Апелляция по жалобе {ticket_number}"))
    container.add_item(discord.ui.Separator())
    container.add_item(discord.ui.TextDisplay(f"<@&{MODERATION_PING_ROLE}>"))
    container.add_item(discord.ui.Separator())
    container.add_item(discord.ui.TextDisplay(appeal_text[:1024]))
    container.add_item(discord.ui.Separator())

    if appeal_verdict:
        container.add_item(discord.ui.TextDisplay(f"<:etiket:1555909701202616320> Вердикт по апелляции:"))
        container.add_item(discord.ui.Separator())
        container.add_item(discord.ui.TextDisplay(appeal_verdict[:1024]))
        container.add_item(discord.ui.Separator())
        container.add_item(discord.ui.TextDisplay(f"Администратор: <@{appeal_mod_id}>"))
        container.add_item(discord.ui.Separator())
        container.add_item(discord.ui.ActionRow(
            AppealChangeVerdictButton(ticket_number),
            AppealDeleteVerdictButton(ticket_number)
        ))
    else:
        container.add_item(discord.ui.ActionRow(AppealVerdictButton(ticket_number)))

    return container


def build_punishment_dm_container(record):
    container = discord.ui.Container()

    action_text = record.get('action_text', '')
    container.add_item(discord.ui.TextDisplay(f"{EMOJI_SHIELD} **{action_text}**"))
    container.add_item(discord.ui.TextDisplay(f"{record.get('id', '')}"))
    container.add_item(discord.ui.Separator())

    if record.get('warn_count') is not None and record.get('max_warns') is not None:
        container.add_item(discord.ui.TextDisplay(
            f"Всего предупреждений: {record['warn_count']}/{record['max_warns']}"
        ))

    if record.get('duration_text'):
        container.add_item(discord.ui.TextDisplay(f"Время: {record['duration_text']}"))

    for line in record.get('extra_lines', []) or []:
        if line:
            container.add_item(discord.ui.TextDisplay(line))

    container.add_item(discord.ui.TextDisplay(f"Причина: {record.get('reason', 'Не указана')}"))
    container.add_item(discord.ui.Separator())

    mod_label = record.get('moderator_label', 'Модератор')
    mod_name = record.get('moderator_name', 'Unknown')
    mod_id = record.get('moderator_id', 0)
    container.add_item(discord.ui.TextDisplay(f"{mod_label}: {mod_name} | {mod_id}"))
    container.add_item(discord.ui.Separator())

    if record.get('appeal_verdict'):
        title = "Вердикт по вашей апелляции (изменено)" if record.get('appeal_verdict_changed') else "Вердикт по вашей апелляции"
        container.add_item(discord.ui.TextDisplay(f"<:etiket:1555909701202616320> {title}"))
        container.add_item(discord.ui.Separator())
        container.add_item(discord.ui.TextDisplay(str(record['appeal_verdict'])))
        container.add_item(discord.ui.Separator())
        amn = record.get('appeal_moderator_name') or 'Unknown'
        container.add_item(discord.ui.TextDisplay(f"Администратор: {amn} | {record.get('appeal_moderator_id', 0)}"))
        container.add_item(discord.ui.Separator())
    elif record.get('appeal'):
        container.add_item(discord.ui.TextDisplay("Апелляция подана на рассмотрение администрации."))
        container.add_item(discord.ui.Separator())
    elif record.get('can_appeal', True):
        container.add_item(discord.ui.ActionRow(
            PunishmentAppealButton(record['id'])
        ))

    layout = discord.ui.LayoutView(timeout=None)
    layout.add_item(container)
    return layout


def build_punishment_appeal_container(record):
    p_id = record['id']
    appeal_text = record.get('appeal', '') or ''
    appeal_verdict = record.get('appeal_verdict')
    appeal_mod_id = record.get('appeal_moderator_id')

    container = discord.ui.Container()
    container.add_item(discord.ui.TextDisplay(f"## Апелляция по наказанию {p_id}"))
    container.add_item(discord.ui.Separator())
    container.add_item(discord.ui.TextDisplay(f"<@&{MODERATION_PING_ROLE}>"))
    container.add_item(discord.ui.Separator())

    type_labels = {
        'mute': 'Мут', 'warn': 'Предупреждение', 'kick': 'Кик',
        'ban': 'Бан', 'tempban': 'Временный бан',
        'auto_mute_spam': 'Автомут за спам', 'auto_ban_spam': 'Автобан за спам',
        'auto_mute_invite': 'Автомут за ссылку', 'auto_mute_warns': 'Автомут за 3 варна'
    }
    type_label = type_labels.get(record.get('type', ''), record.get('type', ''))

    info = f"Наказанный: <@{record['user_id']}>\n\n"
    info += f"Тип: {type_label}\n\n"
    if record.get('duration_text'):
        info += f"Время: {record['duration_text']}\n\n"
    info += f"Причина: {str(record.get('reason', ''))[:500]}\n\n"
    info += f"Выдал: {record.get('moderator_label', 'Модератор')} {record.get('moderator_name', 'Unknown')} | {record.get('moderator_id', 0)}"
    container.add_item(discord.ui.TextDisplay(info))
    container.add_item(discord.ui.Separator())

    container.add_item(discord.ui.TextDisplay(f"Апелляция от <@{record['appeal_author_id']}>:"))
    container.add_item(discord.ui.Separator())
    container.add_item(discord.ui.TextDisplay(str(appeal_text)[:1024]))
    container.add_item(discord.ui.Separator())

    if appeal_verdict:
        title = "Вердикт по апелляции (изменено):" if record.get('appeal_verdict_changed') else "Вердикт по апелляции:"
        container.add_item(discord.ui.TextDisplay(f"<:etiket:1555909701202616320> {title}"))
        container.add_item(discord.ui.Separator())
        container.add_item(discord.ui.TextDisplay(str(appeal_verdict)[:1024]))
        container.add_item(discord.ui.Separator())
        amn = record.get('appeal_moderator_name') or 'Unknown'
        container.add_item(discord.ui.TextDisplay(f"Администратор: {amn} | {appeal_mod_id}"))
        container.add_item(discord.ui.Separator())
        container.add_item(discord.ui.ActionRow(
            PunishmentAppealChangeVerdictButton(p_id),
            PunishmentAppealDeleteVerdictButton(p_id)
        ))
    else:
        container.add_item(discord.ui.ActionRow(PunishmentAppealVerdictButton(p_id)))

    return container


async def create_punishment_and_dm(
    guild, target_user, punishment_type, action_text, reason,
    moderator=None, duration_text=None, extra_lines=None,
    warn_count=None, max_warns=None, can_appeal=True
):
    if moderator is None or not isinstance(moderator, discord.Member):
        mod_id = bot.user.id
        mod_name = str(bot.user)
        mod_label = "Бот"
    else:
        mod_id = moderator.id
        mod_name = str(moderator)
        mod_label = get_staff_label(moderator)

    p_id = format_global_number(get_next_global_number())

    record = {
        'id': p_id,
        'user_id': target_user.id,
        'user_name': str(target_user),
        'type': punishment_type,
        'action_text': action_text,
        'reason': reason,
        'duration_text': duration_text,
        'extra_lines': extra_lines or [],
        'warn_count': warn_count,
        'max_warns': max_warns,
        'moderator_id': mod_id,
        'moderator_name': mod_name,
        'moderator_label': mod_label,
        'date': datetime.now(timezone.utc).timestamp(),
        'appeal': None,
        'appeal_author_id': None,
        'appeal_message_id': None,
        'appeal_verdict': None,
        'appeal_moderator_id': None,
        'appeal_moderator_name': None,
        'appeal_verdict_changed': False,
        'dm_message_id': None,
        'can_appeal': can_appeal
    }

    data = load_punishment_appeals()
    data['appeals'].append(record)
    save_punishment_appeals(data)

    layout = build_punishment_dm_container(record)
    try:
        dm_msg = await target_user.send(view=layout)
        data = load_punishment_appeals()
        for r in data['appeals']:
            if r['id'] == p_id:
                r['dm_message_id'] = dm_msg.id
                break
        save_punishment_appeals(data)
        record['dm_message_id'] = dm_msg.id
    except:
        pass

    if can_appeal:
        try:
            v = discord.ui.View(timeout=None)
            v.add_item(PunishmentAppealButton(p_id))
            bot.add_view(v)
        except:
            pass

    return record


def register_persistent_views():
    global _persistent_registered
    if _persistent_registered:
        return
    _persistent_registered = True

    try:
        v = discord.ui.View(timeout=None)
        v.add_item(ComplaintButton())
        v.add_item(ModerationComplaintButton())
        bot.add_view(v)
    except Exception as e:
        print(f"register formjb: {e}")

    try:
        v = discord.ui.View(timeout=None)
        v.add_item(TiketQuestionButton())
        v.add_item(TiketBugButton())
        v.add_item(TiketSuggestionButton())
        bot.add_view(v)
    except Exception as e:
        print(f"register formtik: {e}")

    try:
        tickets_data = load_tickets()
        for t in tickets_data.get('tickets', []):
            tid = t.get('id')
            if not tid:
                continue
            try:
                if t.get('status') == 'open':
                    v = discord.ui.View(timeout=None)
                    v.add_item(VerdictButton(tid, "complaint"))
                    v.add_item(DeleteTicketButton(tid, "complaint"))
                    bot.add_view(v)
                else:
                    v = discord.ui.View(timeout=None)
                    v.add_item(ChangeVerdictButton(tid, "complaint"))
                    v.add_item(DeleteVerdictButton(tid, "complaint"))
                    bot.add_view(v)

                if t.get('appeal_verdict'):
                    v = discord.ui.View(timeout=None)
                    v.add_item(AppealChangeVerdictButton(tid))
                    v.add_item(AppealDeleteVerdictButton(tid))
                    bot.add_view(v)
                elif t.get('appeal'):
                    v = discord.ui.View(timeout=None)
                    v.add_item(AppealVerdictButton(tid))
                    bot.add_view(v)

                if t.get('status') == 'closed' and not t.get('appeal'):
                    v = discord.ui.View(timeout=None)
                    v.add_item(AppealButton(tid))
                    bot.add_view(v)
            except Exception as e:
                print(f"register complaint {tid}: {e}")
    except Exception as e:
        print(f"load tickets: {e}")

    try:
        tikets_data = load_tikets()
        for t in tikets_data.get('tikets', []):
            tid = t.get('id')
            if not tid:
                continue
            try:
                if t.get('status') == 'open':
                    v = discord.ui.View(timeout=None)
                    v.add_item(VerdictButton(tid, "ticket"))
                    v.add_item(DeleteTicketButton(tid, "ticket"))
                    bot.add_view(v)
                else:
                    v = discord.ui.View(timeout=None)
                    v.add_item(ChangeVerdictButton(tid, "ticket"))
                    v.add_item(DeleteVerdictButton(tid, "ticket"))
                    bot.add_view(v)
            except Exception as e:
                print(f"register tiket {tid}: {e}")
    except Exception as e:
        print(f"load tikets: {e}")

    try:
        appeals_data = load_punishment_appeals()
        for r in appeals_data.get('appeals', []):
            pid = r.get('id')
            if not pid:
                continue
            try:
                if r.get('appeal_verdict'):
                    v = discord.ui.View(timeout=None)
                    v.add_item(PunishmentAppealChangeVerdictButton(pid))
                    v.add_item(PunishmentAppealDeleteVerdictButton(pid))
                    bot.add_view(v)
                elif r.get('appeal'):
                    v = discord.ui.View(timeout=None)
                    v.add_item(PunishmentAppealVerdictButton(pid))
                    bot.add_view(v)
                elif r.get('can_appeal', True):
                    v = discord.ui.View(timeout=None)
                    v.add_item(PunishmentAppealButton(pid))
                    bot.add_view(v)
            except Exception as e:
                print(f"register punishment appeal {pid}: {e}")
    except Exception as e:
        print(f"load punishment appeals: {e}")

    try:
        for guild in bot.guilds:
            if guild.id != TARGET_GUILD_ID:
                continue
            for role in guild.roles:
                try:
                    v = discord.ui.View(timeout=None)
                    v.add_item(RoleButton(role))
                    bot.add_view(v)
                except Exception as e:
                    pass
            break
    except Exception as e:
        print(f"register roles: {e}")


@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'✅ Бот {bot.user} запущен и готов к работе!')
    print(f'📊 На серверах: {len(bot.guilds)}')
    register_persistent_views()
    bot.loop.create_task(check_auto_unwarn())
    bot.loop.create_task(check_raid_status())

    for guild in bot.guilds:
        if not is_target_guild(guild):
            continue
        try:
            for invite in await guild.invites():
                _invite_cache[invite.code] = invite.uses
        except:
            pass


@bot.event
async def on_invite_create(invite):
    if not is_target_guild(invite.guild):
        return
    _invite_cache[invite.code] = invite.uses


@bot.event
async def on_invite_delete(invite):
    if not is_target_guild(invite.guild):
        return
    _invite_cache.pop(invite.code, None)


@bot.event
async def on_member_join(member):
    if not is_target_guild(member.guild):
        return
    get_join_tracker(member.guild.id).append(datetime.now(timezone.utc).timestamp())
    get_raid_status(member.guild.id)['last_join'] = datetime.now(timezone.utc).timestamp()

    invite_code = "Неизвестно"
    inviter_text = "Неизвестно"

    try:
        current_invites = {}
        for inv in await member.guild.invites():
            current_invites[inv.code] = inv.uses

        for code, uses in current_invites.items():
            old_uses = _invite_cache.get(code, 0)
            if uses > old_uses:
                invite_code = code
                for inv in await member.guild.invites():
                    if inv.code == code and inv.inviter:
                        inviter_text = f"{inv.inviter} | {inv.inviter.id}"
                        break
                break

        for code, uses in current_invites.items():
            _invite_cache[code] = uses
    except:
        pass

    layout = build_log_layout(
        "Участник присоединился к серверу",
        fields=[
            ("Участник", member.mention),
            ("Код приглашения", f"`{invite_code}`"),
            ("Создал приглашение", inviter_text),
        ]
    )
    await send_log_layout(layout, LOG_INVITE_CHANNEL_ID, member.guild)

    if get_raid_status(member.guild.id)['status'] == ANTI_RAID_RED:
        dm_embed = base_embed("🟣 Сервер в режиме антирейда", COLOR_ACCENT)
        dm_embed.add_field(name="Статус", value="Purple — полная блокировка", inline=True)
        dm_embed.add_field(name="Действие", value="Ваш аккаунт будет проверен администрацией", inline=False)
        await send_dm(member, dm_embed)
    elif get_raid_status(member.guild.id)['status'] == ANTI_RAID_YELLOW:
        dm_embed = base_embed("🔷 Сервер в режиме повышенной готовности", COLOR_INFO)
        dm_embed.add_field(name="Статус", value="Indigo — повышенная готовность", inline=True)
        await send_dm(member, dm_embed)


@bot.event
async def on_member_remove(member):
    if not is_target_guild(member.guild):
        return
    layout = build_log_layout(
        "Участник покинул сервер",
        fields=[
            ("Участник", member.mention),
        ]
    )
    await send_log_layout(layout, LOG_INVITE_CHANNEL_ID, member.guild)


@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return
    if not is_target_guild(message.guild):
        return

    if message.content.startswith('!'):
        await bot.process_commands(message)
        return

    status = get_raid_status(message.guild.id)
    if status['status'] == ANTI_RAID_RED and not message.author.guild_permissions.administrator:
        return
    if message.author.guild_permissions.administrator:
        return
    content = message.content
    if re.search(r'(?:https?://)?(?:www\.)?(?:discord\.gg|discord(?:app)?\.com/invite)/[\w-]+', content, re.IGNORECASE):
        try:
            await message.delete()
            user_warns = get_user_warns(message.guild.id, message.author.id)
            user_warns.append({'reason': 'Ссылка на Discord-сервер', 'moderator': bot.user.id, 'timestamp': datetime.now(timezone.utc).timestamp()})
            save_user_warns(message.guild.id, message.author.id, user_warns)
            await message.author.timeout(discord.utils.utcnow() + timedelta(seconds=3 * 3600), reason="Ссылка на discord.gg")

            record = await create_punishment_and_dm(
                message.guild,
                message.author,
                'auto_mute_invite',
                'Вы получили мут',
                'Отправка ссылки на Discord-сервер',
                moderator=None,
                duration_text='3 часа',
                can_appeal=True
            )

            layout = build_log_layout(
                "Выдан мут за ссылку на Discord-сервер",
                fields=[
                    ("Номер", record['id']),
                    ("Участник", message.author.mention),
                    ("Время", "3 часа"),
                    ("Причина", "Отправка ссылки на Discord-сервер"),
                ],
                footer=f"Модератор: {bot.user} | {bot.user.id}"
            )
            await send_log_layout(layout, LOG_ALL_CHANNEL_ID, message.guild)
        except:
            pass
        return
    if len(content) < 1:
        return
    normalized_content = normalize_text(content) or content.strip()
    user_spam = get_user_spam(message.guild.id, message.author.id)
    current_time = datetime.now(timezone.utc).timestamp()
    user_spam['messages'] = [msg for msg in user_spam['messages'] if current_time - msg['timestamp'] <= SPAM_TIME_WINDOW]
    same_messages = [msg for msg in user_spam['messages'] if msg['content'] == normalized_content]
    user_spam['messages'].append({'content': normalized_content, 'timestamp': current_time})
    save_user_spam(message.guild.id, message.author.id, user_spam)
    if len(same_messages) >= SPAM_LIMIT - 1:
        user_warns = get_user_warns(message.guild.id, message.author.id)
        spam_count = user_spam.get('spam_count', 0) + 1
        user_spam['spam_count'] = spam_count
        user_spam['last_spam_time'] = current_time
        save_user_spam(message.guild.id, message.author.id, user_spam)
        mute_duration, mute_text = (
            (SPAM_MUTE_1, "30 минут") if spam_count == 1 else
            (SPAM_MUTE_2, "12 часов") if spam_count == 2 else
            (SPAM_MUTE_3, "5 дней")
        )
        try:
            await message.channel.purge(limit=SPAM_LIMIT, check=lambda m: m.author == message.author and normalize_text(m.content) == normalized_content)
        except:
            pass
        user_warns.append({'reason': f'Спам ({spam_count} нарушение)', 'moderator': bot.user.id, 'timestamp': current_time})
        save_user_warns(message.guild.id, message.author.id, user_warns)
        try:
            await message.author.timeout(discord.utils.utcnow() + timedelta(seconds=mute_duration), reason=f"Спам (нарушение {spam_count})")

            record = await create_punishment_and_dm(
                message.guild,
                message.author,
                'auto_mute_spam',
                'Вы получили мут за спам',
                'Отправка одинаковых сообщений',
                moderator=None,
                duration_text=mute_text,
                extra_lines=[f"Нарушение: {spam_count}/3"],
                can_appeal=True
            )

            layout = build_log_layout(
                "Выдан мут за спам",
                fields=[
                    ("Номер", record['id']),
                    ("Участник", message.author.mention),
                    ("Время", mute_text),
                    ("Нарушение", f"{spam_count}/3"),
                    ("Причина", "Отправка одинаковых сообщений"),
                ],
                footer=f"Модератор: {bot.user} | {bot.user.id}"
            )
            await send_log_layout(layout, LOG_ALL_CHANNEL_ID, message.guild)

            if spam_count >= 3:
                try:
                    await message.author.ban(reason="3 нарушения спама")

                    record2 = await create_punishment_and_dm(
                        message.guild,
                        message.author,
                        'auto_ban_spam',
                        'Вы были забанены',
                        '3 нарушения спама',
                        moderator=None,
                        can_appeal=True
                    )

                    layout = build_log_layout(
                        "Выдан бан за спам",
                        fields=[
                            ("Номер", record2['id']),
                            ("Участник", message.author.mention),
                            ("Причина", "3 нарушения спама"),
                        ],
                        footer=f"Модератор: {bot.user} | {bot.user.id}"
                    )
                    await send_log_layout(layout, LOG_ALL_CHANNEL_ID, message.guild)
                except:
                    pass
        except:
            pass


@bot.event
async def on_message_edit(before, after):
    if before.author.bot or not before.guild:
        return
    if not is_target_guild(before.guild):
        return
    if before.content == after.content:
        return

    before_text = before.content if before.content else "*(пусто)*"
    after_text = after.content if after.content else "*(пусто)*"

    layout = build_log_layout(
        "Сообщение изменено",
        fields=[
            ("Участник", before.author.mention),
            ("Канал", before.channel.mention),
            ("Было", before_text),
            ("Стало", after_text),
        ]
    )
    await send_log_layout(layout, LOG_CHAT_CHANNEL_ID, before.guild)


@bot.event
async def on_message_delete(message):
    if message.author.bot or not message.guild:
        return
    if not is_target_guild(message.guild):
        return

    deleter_text = "Неизвестно"
    try:
        async for entry in message.guild.audit_logs(limit=5, action=discord.AuditLogAction.message_delete):
            if entry.target and entry.target.id == message.author.id:
                deleter_text = f"{entry.user} | {entry.user.id}"
                break
    except:
        pass

    content = message.content if message.content else "*(нет текста / вложение)*"

    layout = build_log_layout(
        "Сообщение удалено",
        fields=[
            ("Участник", message.author.mention),
            ("Кто удалил", deleter_text),
            ("Канал", message.channel.mention),
            ("Содержимое", content),
        ]
    )
    await send_log_layout(layout, LOG_CHAT_CHANNEL_ID, message.guild)


@bot.event
async def on_member_update(before, after):
    if not is_target_guild(before.guild):
        return

    if before.nick != after.nick:
        layout = build_log_layout(
            "Никнейм изменён",
            fields=[
                ("Участник", after.mention),
                ("Старый ник", before.nick or before.name),
                ("Новый ник", after.nick or after.name),
            ]
        )
        await send_log_layout(layout, LOG_CHAT_CHANNEL_ID, before.guild)


@bot.event
async def on_guild_channel_create(channel):
    if not is_target_guild(channel.guild):
        return
    actor = await get_audit_log_actor(channel.guild, discord.AuditLogAction.channel_create, channel)
    layout = build_log_layout(
        "Канал создан",
        fields=[
            ("Канал", channel.mention),
            ("Тип", str(channel.type).split('.')[-1]),
        ],
        footer=staff_footer(actor) if actor else "Модератор: Неизвестно"
    )
    await send_log_layout(layout, LOG_ALL_CHANNEL_ID, channel.guild)


@bot.event
async def on_guild_channel_delete(channel):
    if not is_target_guild(channel.guild):
        return
    actor = await get_audit_log_actor(channel.guild, discord.AuditLogAction.channel_delete, channel)
    layout = build_log_layout(
        "Канал удалён",
        fields=[
            ("Канал", channel.name),
            ("Тип", str(channel.type).split('.')[-1]),
        ],
        footer=staff_footer(actor) if actor else "Модератор: Неизвестно"
    )
    await send_log_layout(layout, LOG_ALL_CHANNEL_ID, channel.guild)


@bot.event
async def on_guild_channel_update(before, after):
    if not is_target_guild(before.guild):
        return
    if before.name != after.name:
        actor = await get_audit_log_actor(before.guild, discord.AuditLogAction.channel_update, after)
        layout = build_log_layout(
            "Канал переименован",
            fields=[
                ("Старый канал", before.name),
                ("Новый канал", after.name),
            ],
            footer=staff_footer(actor) if actor else "Модератор: Неизвестно"
        )
        await send_log_layout(layout, LOG_ALL_CHANNEL_ID, before.guild)


@bot.event
async def on_guild_role_create(role):
    if not is_target_guild(role.guild):
        return
    actor = await get_audit_log_actor(role.guild, discord.AuditLogAction.role_create, role)
    layout = build_log_layout(
        "Роль создана",
        fields=[
            ("Роль", role.mention),
            ("Цвет", str(role.color)),
        ],
        footer=staff_footer(actor) if actor else "Модератор: Неизвестно"
    )
    await send_log_layout(layout, LOG_ALL_CHANNEL_ID, role.guild)


@bot.event
async def on_guild_role_delete(role):
    if not is_target_guild(role.guild):
        return
    actor = await get_audit_log_actor(role.guild, discord.AuditLogAction.role_delete, role)
    layout = build_log_layout(
        "Роль удалена",
        fields=[
            ("Роль", role.name),
        ],
        footer=staff_footer(actor) if actor else "Модератор: Неизвестно"
    )
    await send_log_layout(layout, LOG_ALL_CHANNEL_ID, role.guild)


@bot.event
async def on_guild_role_update(before, after):
    if not is_target_guild(before.guild):
        return
    actor = await get_audit_log_actor(before.guild, discord.AuditLogAction.role_update, after)
    if before.name != after.name:
        layout = build_log_layout(
            "Роль переименована",
            fields=[
                ("Старая роль", before.name),
                ("Новая роль", after.name),
            ],
            footer=staff_footer(actor) if actor else "Модератор: Неизвестно"
        )
        await send_log_layout(layout, LOG_ALL_CHANNEL_ID, before.guild)


class TicketModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="📝 Подача жалобы")

        self.description = discord.ui.TextInput(
            label="Описание ситуации",
            placeholder="Опишите ситуацию и укажите пункты правил",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=1000
        )
        self.add_item(self.description)

        self.user_name = discord.ui.TextInput(
            label="Имя пользователя (UserName)",
            placeholder="Введите имя пользователя",
            style=discord.TextStyle.short,
            required=True,
            max_length=100
        )
        self.add_item(self.user_name)

        self.message_link = discord.ui.TextInput(
            label="Ссылка на сообщение (необязательно)",
            placeholder="Вставьте ссылку на сообщение",
            style=discord.TextStyle.short,
            required=False,
            max_length=200
        )
        self.add_item(self.message_link)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=False)

        if not is_target_guild(interaction.guild):
            return

        ticket_number = format_global_number(get_next_global_number())
        link_value = self.message_link.value if self.message_link.value else "Не указано"

        ticket_data = {
            'id': ticket_number,
            'author_id': interaction.user.id,
            'author_name': str(interaction.user),
            'description': self.description.value,
            'user_name': self.user_name.value,
            'message_link': link_value,
            'status': 'open',
            'created_at': datetime.now(timezone.utc).timestamp(),
            'message_id': None,
            'channel_id': TICKET_CHANNEL_ID,
            'type': 'complaint',
            'verdict': None,
            'moderator_id': None,
            'moderator_name': None,
            'moderator_staff_label': None,
            'dm_message_id': None,
            'appeal': None,
            'appeal_author_id': None,
            'appeal_message_id': None,
            'appeal_verdict': None,
            'appeal_moderator_id': None,
            'appeal_verdict_changed': False
        }

        tickets_data = load_tickets()
        tickets_data['tickets'].append(ticket_data)
        save_tickets(tickets_data)

        container = build_open_complaint_container(ticket_number, ticket_data)
        layout = discord.ui.LayoutView(timeout=None)
        layout.add_item(container)

        channel = bot.get_channel(TICKET_CHANNEL_ID)
        if channel:
            message = await channel.send(view=layout)
            for ticket in tickets_data['tickets']:
                if ticket['id'] == ticket_number:
                    ticket['message_id'] = message.id
                    break
            save_tickets(tickets_data)

        try:
            v = discord.ui.View(timeout=None)
            v.add_item(VerdictButton(ticket_number, "complaint"))
            v.add_item(DeleteTicketButton(ticket_number, "complaint"))
            bot.add_view(v)
        except:
            pass


class ModerationTicketModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="📝 Жалоба на персонал")

        self.description = discord.ui.TextInput(
            label="Описание ситуации",
            placeholder="Опишите ситуацию и укажите пункты правил",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=1000
        )
        self.add_item(self.description)

        self.moderator_name = discord.ui.TextInput(
            label="Имя модератора (UserName)",
            placeholder="Введите имя модератора",
            style=discord.TextStyle.short,
            required=True,
            max_length=100
        )
        self.add_item(self.moderator_name)

        self.message_link = discord.ui.TextInput(
            label="Ссылка на сообщение (необязательно)",
            placeholder="Вставьте ссылку на сообщение",
            style=discord.TextStyle.short,
            required=False,
            max_length=200
        )
        self.add_item(self.message_link)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=False)

        if not is_target_guild(interaction.guild):
            return

        ticket_number = format_global_number(get_next_global_number())
        link_value = self.message_link.value if self.message_link.value else "Не указано"

        ticket_data = {
            'id': ticket_number,
            'author_id': interaction.user.id,
            'author_name': str(interaction.user),
            'description': self.description.value,
            'user_name': self.moderator_name.value,
            'message_link': link_value,
            'status': 'open',
            'created_at': datetime.now(timezone.utc).timestamp(),
            'message_id': None,
            'channel_id': MODERATION_CHANNEL_ID,
            'type': 'moderation',
            'verdict': None,
            'moderator_id': None,
            'moderator_name': None,
            'moderator_staff_label': None,
            'dm_message_id': None,
            'appeal': None,
            'appeal_author_id': None,
            'appeal_message_id': None,
            'appeal_verdict': None,
            'appeal_moderator_id': None,
            'appeal_verdict_changed': False
        }

        tickets_data = load_tickets()
        tickets_data['tickets'].append(ticket_data)
        save_tickets(tickets_data)

        container = build_open_complaint_container(ticket_number, ticket_data)
        layout = discord.ui.LayoutView(timeout=None)
        layout.add_item(container)

        channel = bot.get_channel(MODERATION_CHANNEL_ID)
        if channel:
            message = await channel.send(view=layout)
            for ticket in tickets_data['tickets']:
                if ticket['id'] == ticket_number:
                    ticket['message_id'] = message.id
                    break
            save_tickets(tickets_data)

        try:
            v = discord.ui.View(timeout=None)
            v.add_item(VerdictButton(ticket_number, "complaint"))
            v.add_item(DeleteTicketButton(ticket_number, "complaint"))
            bot.add_view(v)
        except:
            pass


class VerdictModal(discord.ui.Modal):
    def __init__(self, ticket_number, ticket_data, user, ticket_author):
        super().__init__(title=f"⚖️ Вердикт по жалобе {ticket_number}")
        self.ticket_number = ticket_number
        self.ticket_data = ticket_data
        self.user = user
        self.ticket_author = ticket_author

        self.verdict = discord.ui.TextInput(
            label="Вердикт",
            placeholder="Введите решение по жалобе",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=1000
        )
        self.add_item(self.verdict)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=False)

        tickets_data = load_tickets()
        message_id = None
        channel_id = TICKET_CHANNEL_ID
        updated_data = None
        found = False
        for ticket in tickets_data.get('tickets', []):
            if ticket['id'] == self.ticket_number:
                found = True
                ticket['status'] = 'closed'
                ticket['verdict'] = self.verdict.value
                ticket['moderator_id'] = interaction.user.id
                ticket['moderator_name'] = str(interaction.user)
                ticket['moderator_staff_label'] = get_staff_label(interaction.user)
                message_id = ticket.get('message_id')
                channel_id = ticket.get('channel_id', TICKET_CHANNEL_ID)
                updated_data = ticket
                break

        if not found:
            return

        save_tickets(tickets_data)

        if message_id and updated_data:
            channel = bot.get_channel(channel_id)
            if channel:
                try:
                    message = await channel.fetch_message(message_id)
                    if message:
                        new_container = build_closed_complaint_container(self.ticket_number, updated_data)
                        new_layout = discord.ui.LayoutView(timeout=None)
                        new_layout.add_item(new_container)
                        await message.edit(view=new_layout)
                except:
                    pass

        if self.ticket_author:
            dm_id = await send_or_edit_verdict_dm(
                self.ticket_author,
                updated_data
            )
            if dm_id:
                for ticket in tickets_data['tickets']:
                    if ticket['id'] == self.ticket_number:
                        ticket['dm_message_id'] = dm_id
                        break
                save_tickets(tickets_data)

        try:
            v = discord.ui.View(timeout=None)
            v.add_item(ChangeVerdictButton(self.ticket_number, "complaint"))
            v.add_item(DeleteVerdictButton(self.ticket_number, "complaint"))
            bot.add_view(v)
        except:
            pass

        try:
            v = discord.ui.View(timeout=None)
            v.add_item(AppealButton(self.ticket_number))
            bot.add_view(v)
        except:
            pass


class VerdictButton(discord.ui.Button):
    def __init__(self, ticket_number, kind="complaint"):
        super().__init__(
            label="Вынести вердикт",
            emoji=EMOJI_JUDGE,
            style=discord.ButtonStyle.secondary,
            custom_id=f"verdict_{kind}_{ticket_number}"
        )
        self.ticket_number = ticket_number
        self.kind = kind

    async def callback(self, interaction: discord.Interaction):
        if not is_mod(interaction.user):
            await interaction.response.send_message(ERR_UNAVAILABLE, ephemeral=True)
            return

        if self.kind == "ticket":
            data = load_tikets()
            key = 'tikets'
        else:
            data = load_tickets()
            key = 'tickets'

        ticket_data = None
        ticket_author = None
        for t in data.get(key, []):
            if t.get('id') == self.ticket_number:
                ticket_data = t
                ticket_author = t.get('author_id')
                break

        if not ticket_data:
            await interaction.response.send_message(ERR_UNAVAILABLE, ephemeral=True)
            return

        if ticket_data['status'] == 'closed':
            await interaction.response.send_message(ERR_UNAVAILABLE, ephemeral=True)
            return

        if self.kind == "ticket":
            modal = TiketVerdictModal(self.ticket_number, ticket_author, ticket_data)
        else:
            modal = VerdictModal(self.ticket_number, ticket_data, interaction.user, ticket_author)
        await interaction.response.send_modal(modal)


class ChangeVerdictModal(discord.ui.Modal):
    def __init__(self, ticket_number, ticket_data, kind):
        super().__init__(title=f"✏️ Изменить вердикт {ticket_number}")
        self.ticket_number = ticket_number
        self.ticket_data = ticket_data
        self.kind = kind

        self.new_verdict = discord.ui.TextInput(
            label="Новый вердикт",
            placeholder="Введите новый вердикт",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=1000,
            default=ticket_data.get('verdict', '') or ''
        )
        self.add_item(self.new_verdict)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=False)

        if self.kind == "ticket":
            data = load_tikets()
            key = 'tikets'
            save_fn = save_tikets
            channel_id = TIKET_CHANNEL_ID
        else:
            data = load_tickets()
            key = 'tickets'
            save_fn = save_tickets
            channel_id = TICKET_CHANNEL_ID

        updated = None
        message_id = None
        author_id = None
        dm_id = None
        for t in data.get(key, []):
            if t.get('id') == self.ticket_number:
                t['verdict'] = self.new_verdict.value
                t['moderator_id'] = interaction.user.id
                t['moderator_name'] = str(interaction.user)
                t['moderator_staff_label'] = get_staff_label(interaction.user)
                message_id = t.get('message_id')
                channel_id = t.get('channel_id', channel_id)
                author_id = t.get('author_id')
                dm_id = t.get('dm_message_id')
                updated = t
                break
        save_fn(data)

        if message_id and updated:
            channel = bot.get_channel(channel_id)
            if channel:
                try:
                    message = await channel.fetch_message(message_id)
                    if message:
                        if self.kind == "ticket":
                            new_container = build_closed_ticket_container(self.ticket_number, updated)
                        else:
                            new_container = build_closed_complaint_container(self.ticket_number, updated)
                        new_layout = discord.ui.LayoutView(timeout=None)
                        new_layout.add_item(new_container)
                        await message.edit(view=new_layout)
                except:
                    pass

        if author_id:
            new_dm_id = await send_or_edit_verdict_dm(
                author_id,
                updated,
                existing_message_id=dm_id
            )
            if new_dm_id and new_dm_id != dm_id:
                for t in data.get(key, []):
                    if t.get('id') == self.ticket_number:
                        t['dm_message_id'] = new_dm_id
                        break
                save_fn(data)


class ChangeVerdictButton(discord.ui.Button):
    def __init__(self, ticket_number, kind):
        super().__init__(
            label="Изменить вердикт",
            emoji=EMOJI_WRITING,
            style=discord.ButtonStyle.success,
            custom_id=f"change_verdict_{kind}_{ticket_number}"
        )
        self.ticket_number = ticket_number
        self.kind = kind

    async def callback(self, interaction: discord.Interaction):
        if not is_admin(interaction.user):
            await interaction.response.send_message(ERR_UNAVAILABLE, ephemeral=True)
            return

        if self.kind == "ticket":
            data = load_tikets()
            key = 'tikets'
        else:
            data = load_tickets()
            key = 'tickets'

        ticket_data = None
        for t in data.get(key, []):
            if t.get('id') == self.ticket_number:
                ticket_data = t
                break

        if not ticket_data:
            await interaction.response.send_message(ERR_UNAVAILABLE, ephemeral=True)
            return

        await interaction.response.send_modal(ChangeVerdictModal(self.ticket_number, ticket_data, self.kind))


class DeleteTicketModal(discord.ui.Modal):
    def __init__(self, ticket_number, ticket_data, kind):
        super().__init__(title=f"🗑️ Удаление {ticket_number}")
        self.ticket_number = ticket_number
        self.ticket_data = ticket_data
        self.kind = kind

        self.reason = discord.ui.TextInput(
            label="Причина удаления",
            placeholder="Укажите причину удаления (обязательно)",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=1000
        )
        self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=False)

        author_id = self.ticket_data.get('author_id')
        type_word = "тикет" if self.kind == "ticket" else "жалоба"

        if self.kind == "ticket":
            data = load_tikets()
            key = 'tikets'
            save_fn = save_tikets
        else:
            data = load_tickets()
            key = 'tickets'
            save_fn = save_tickets

        data[key] = [t for t in data.get(key, []) if t.get('id') != self.ticket_number]
        save_fn(data)

        try:
            await interaction.message.delete()
        except:
            pass

        if author_id:
            await send_delete_dm(author_id, type_word, self.ticket_number, self.reason.value)


class DeleteTicketButton(discord.ui.Button):
    def __init__(self, ticket_number, kind="complaint"):
        label = "Удалить тикет" if kind == "ticket" else "Удалить жалобу"
        super().__init__(
            label=label,
            emoji=EMOJI_TRASH,
            style=discord.ButtonStyle.danger,
            custom_id=f"delete_ticket_{kind}_{ticket_number}"
        )
        self.ticket_number = ticket_number
        self.kind = kind

    async def callback(self, interaction: discord.Interaction):
        if not is_admin(interaction.user):
            await interaction.response.send_message(ERR_UNAVAILABLE, ephemeral=True)
            return

        if self.kind == "ticket":
            data = load_tikets()
            key = 'tikets'
        else:
            data = load_tickets()
            key = 'tickets'

        ticket_data = None
        for t in data.get(key, []):
            if t.get('id') == self.ticket_number:
                ticket_data = t
                break

        if not ticket_data:
            await interaction.response.send_message(ERR_UNAVAILABLE, ephemeral=True)
            return

        if ticket_data.get('status') == 'closed':
            await interaction.response.send_message(ERR_UNAVAILABLE, ephemeral=True)
            return

        await interaction.response.send_modal(DeleteTicketModal(self.ticket_number, ticket_data, self.kind))


class DeleteVerdictButton(discord.ui.Button):
    def __init__(self, ticket_number, kind="complaint"):
        super().__init__(
            label="Удалить вердикт",
            emoji=EMOJI_TRASH,
            style=discord.ButtonStyle.danger,
            custom_id=f"delete_verdict_{kind}_{ticket_number}"
        )
        self.ticket_number = ticket_number
        self.kind = kind

    async def callback(self, interaction: discord.Interaction):
        if not is_admin(interaction.user):
            await interaction.response.send_message(ERR_UNAVAILABLE, ephemeral=True)
            return

        await interaction.response.defer()

        if self.kind == "ticket":
            data = load_tikets()
            key = 'tikets'
            save_fn = save_tikets
            channel_id_default = TIKET_CHANNEL_ID
        else:
            data = load_tickets()
            key = 'tickets'
            save_fn = save_tickets
            channel_id_default = TICKET_CHANNEL_ID

        updated = None
        message_id = None
        channel_id = channel_id_default
        author_id = None
        dm_id = None
        for t in data.get(key, []):
            if t.get('id') == self.ticket_number:
                t['status'] = 'open'
                t['verdict'] = None
                t['moderator_id'] = None
                t['moderator_name'] = None
                t['moderator_staff_label'] = None
                message_id = t.get('message_id')
                channel_id = t.get('channel_id', channel_id_default)
                author_id = t.get('author_id')
                dm_id = t.get('dm_message_id')
                t['dm_message_id'] = None
                updated = t
                break
        save_fn(data)

        if message_id and updated:
            channel = bot.get_channel(channel_id)
            if channel:
                try:
                    message = await channel.fetch_message(message_id)
                    if message:
                        if self.kind == "ticket":
                            new_container = build_open_ticket_container(self.ticket_number, updated)
                        else:
                            new_container = build_open_complaint_container(self.ticket_number, updated)
                        new_layout = discord.ui.LayoutView(timeout=None)
                        new_layout.add_item(new_container)
                        await message.edit(view=new_layout)
                except:
                    pass

        if author_id and dm_id:
            await delete_dm_message(author_id, dm_id)

        try:
            if self.kind == "ticket":
                v = discord.ui.View(timeout=None)
                v.add_item(VerdictButton(self.ticket_number, "ticket"))
                v.add_item(DeleteTicketButton(self.ticket_number, "ticket"))
                bot.add_view(v)
            else:
                v = discord.ui.View(timeout=None)
                v.add_item(VerdictButton(self.ticket_number, "complaint"))
                v.add_item(DeleteTicketButton(self.ticket_number, "complaint"))
                bot.add_view(v)
        except:
            pass


class AppealButton(discord.ui.Button):
    def __init__(self, ticket_number):
        super().__init__(
            label="Апелляция",
            emoji=EMOJI_APPEAL_BTN,
            style=discord.ButtonStyle.secondary,
            custom_id=f"appeal_{ticket_number}"
        )
        self.ticket_number = ticket_number

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(AppealModal(self.ticket_number))


class AppealModal(discord.ui.Modal):
    def __init__(self, ticket_number):
        super().__init__(title=f"Апелляция {ticket_number}")
        self.ticket_number = ticket_number

        self.content = discord.ui.TextInput(
            label="Содержание",
            placeholder="Опишите причину апелляции",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=1000
        )
        self.add_item(self.content)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=False)

        tickets_data = load_tickets()
        ticket_data = None
        for t in tickets_data.get('tickets', []):
            if t.get('id') == self.ticket_number:
                ticket_data = t
                break

        if not ticket_data:
            return

        if ticket_data.get('appeal'):
            return

        ticket_data['appeal'] = self.content.value
        ticket_data['appeal_author_id'] = interaction.user.id
        save_tickets(tickets_data)

        container = build_appeal_container(ticket_data)
        layout = discord.ui.LayoutView(timeout=None)
        layout.add_item(container)

        channel = bot.get_channel(APPEAL_CHANNEL_ID)
        if channel:
            msg = await channel.send(view=layout)
            ticket_data['appeal_message_id'] = msg.id
            save_tickets(tickets_data)

        dm_id = ticket_data.get('dm_message_id')
        if dm_id:
            await send_or_edit_verdict_dm(
                ticket_data.get('author_id'),
                ticket_data,
                existing_message_id=dm_id
            )

        try:
            v = discord.ui.View(timeout=None)
            v.add_item(AppealVerdictButton(self.ticket_number))
            bot.add_view(v)
        except:
            pass


class AppealVerdictButton(discord.ui.Button):
    def __init__(self, ticket_number):
        super().__init__(
            label="Вынести вердикт",
            emoji=EMOJI_JUDGE,
            style=discord.ButtonStyle.secondary,
            custom_id=f"appeal_verdict_{ticket_number}"
        )
        self.ticket_number = ticket_number

    async def callback(self, interaction: discord.Interaction):
        if not is_admin(interaction.user):
            await interaction.response.send_message(ERR_UNAVAILABLE, ephemeral=True)
            return

        await interaction.response.send_modal(AppealVerdictModal(self.ticket_number))


class AppealVerdictModal(discord.ui.Modal):
    def __init__(self, ticket_number):
        super().__init__(title=f"Вердикт по апелляции {ticket_number}")
        self.ticket_number = ticket_number

        self.verdict = discord.ui.TextInput(
            label="Вердикт",
            placeholder="Введите решение по апелляции",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=1000
        )
        self.add_item(self.verdict)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=False)

        tickets_data = load_tickets()
        ticket_data = None
        for t in tickets_data.get('tickets', []):
            if t.get('id') == self.ticket_number:
                ticket_data = t
                break

        if not ticket_data:
            return

        ticket_data['appeal_verdict'] = self.verdict.value
        ticket_data['appeal_moderator_id'] = interaction.user.id
        ticket_data['appeal_verdict_changed'] = False
        save_tickets(tickets_data)

        try:
            message_id = ticket_data.get('appeal_message_id')
            if message_id:
                channel = bot.get_channel(APPEAL_CHANNEL_ID)
                if channel:
                    msg = await channel.fetch_message(message_id)
                    if msg:
                        new_container = build_appeal_container(ticket_data)
                        new_layout = discord.ui.LayoutView(timeout=None)
                        new_layout.add_item(new_container)
                        await msg.edit(view=new_layout)
        except:
            pass

        dm_id = ticket_data.get('dm_message_id')
        if dm_id:
            await send_or_edit_verdict_dm(
                ticket_data.get('author_id'),
                ticket_data,
                existing_message_id=dm_id
            )

        try:
            v = discord.ui.View(timeout=None)
            v.add_item(AppealChangeVerdictButton(self.ticket_number))
            v.add_item(AppealDeleteVerdictButton(self.ticket_number))
            bot.add_view(v)
        except:
            pass


class AppealChangeVerdictButton(discord.ui.Button):
    def __init__(self, ticket_number):
        super().__init__(
            label="Изменить вердикт",
            emoji=EMOJI_WRITING,
            style=discord.ButtonStyle.success,
            custom_id=f"appeal_change_verdict_{ticket_number}"
        )
        self.ticket_number = ticket_number

    async def callback(self, interaction: discord.Interaction):
        if not is_admin(interaction.user):
            await interaction.response.send_message(ERR_UNAVAILABLE, ephemeral=True)
            return

        tickets_data = load_tickets()
        ticket_data = None
        for t in tickets_data.get('tickets', []):
            if t.get('id') == self.ticket_number:
                ticket_data = t
                break

        if not ticket_data:
            await interaction.response.send_message(ERR_UNAVAILABLE, ephemeral=True)
            return

        await interaction.response.send_modal(AppealChangeVerdictModal(self.ticket_number, ticket_data))


class AppealChangeVerdictModal(discord.ui.Modal):
    def __init__(self, ticket_number, ticket_data):
        super().__init__(title=f"✏️ Изменить вердикт апелляции {ticket_number}")
        self.ticket_number = ticket_number
        self.ticket_data = ticket_data

        self.new_verdict = discord.ui.TextInput(
            label="Новый вердикт",
            placeholder="Введите новый вердикт",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=1000,
            default=ticket_data.get('appeal_verdict', '') or ''
        )
        self.add_item(self.new_verdict)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=False)

        tickets_data = load_tickets()
        updated = None
        for t in tickets_data.get('tickets', []):
            if t.get('id') == self.ticket_number:
                t['appeal_verdict'] = self.new_verdict.value
                t['appeal_moderator_id'] = interaction.user.id
                t['appeal_verdict_changed'] = True
                updated = t
                break
        save_tickets(tickets_data)

        if updated:
            message_id = updated.get('appeal_message_id')
            if message_id:
                channel = bot.get_channel(APPEAL_CHANNEL_ID)
                if channel:
                    try:
                        msg = await channel.fetch_message(message_id)
                        if msg:
                            new_container = build_appeal_container(updated)
                            new_layout = discord.ui.LayoutView(timeout=None)
                            new_layout.add_item(new_container)
                            await msg.edit(view=new_layout)
                    except:
                        pass

            dm_id = updated.get('dm_message_id')
            if dm_id:
                await send_or_edit_verdict_dm(
                    updated.get('author_id'),
                    updated,
                    existing_message_id=dm_id
                )


class AppealDeleteVerdictButton(discord.ui.Button):
    def __init__(self, ticket_number):
        super().__init__(
            label="Удалить вердикт",
            emoji=EMOJI_TRASH,
            style=discord.ButtonStyle.danger,
            custom_id=f"appeal_delete_verdict_{ticket_number}"
        )
        self.ticket_number = ticket_number

    async def callback(self, interaction: discord.Interaction):
        if not is_admin(interaction.user):
            await interaction.response.send_message(ERR_UNAVAILABLE, ephemeral=True)
            return

        await interaction.response.defer()

        tickets_data = load_tickets()
        updated = None
        for t in tickets_data.get('tickets', []):
            if t.get('id') == self.ticket_number:
                t['appeal_verdict'] = None
                t['appeal_moderator_id'] = None
                t['appeal_verdict_changed'] = False
                updated = t
                break
        save_tickets(tickets_data)

        if updated:
            message_id = updated.get('appeal_message_id')
            if message_id:
                channel = bot.get_channel(APPEAL_CHANNEL_ID)
                if channel:
                    try:
                        msg = await channel.fetch_message(message_id)
                        if msg:
                            new_container = build_appeal_container(updated)
                            new_layout = discord.ui.LayoutView(timeout=None)
                            new_layout.add_item(new_container)
                            await msg.edit(view=new_layout)
                    except:
                        pass

            dm_id = updated.get('dm_message_id')
            if dm_id:
                await send_or_edit_verdict_dm(
                    updated.get('author_id'),
                    updated,
                    existing_message_id=dm_id
                )

        try:
            v = discord.ui.View(timeout=None)
            v.add_item(AppealVerdictButton(self.ticket_number))
            bot.add_view(v)
        except:
            pass


class ComplaintButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Подать жалобу",
            emoji=EMOJI_FORM,
            style=discord.ButtonStyle.danger,
            custom_id="complaint_button"
        )

    async def callback(self, interaction: discord.Interaction):
        if not is_target_guild(interaction.guild):
            await interaction.response.send_message(ERR_UNAVAILABLE, ephemeral=True)
            return
        modal = TicketModal()
        await interaction.response.send_modal(modal)


class ModerationComplaintButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Жалоба на персонал",
            emoji=EMOJI_FORMULARIO,
            style=discord.ButtonStyle.secondary,
            custom_id="moderation_complaint_button"
        )

    async def callback(self, interaction: discord.Interaction):
        if not is_target_guild(interaction.guild):
            await interaction.response.send_message(ERR_UNAVAILABLE, ephemeral=True)
            return
        modal = ModerationTicketModal()
        await interaction.response.send_modal(modal)


@bot.command(name="formjb")
async def formjb(ctx):
    if not is_target_guild(ctx.guild):
        await ctx.send(ERR_UNAVAILABLE)
        return

    container = discord.ui.Container()
    container.add_item(discord.ui.TextDisplay("## <:Support:1555909739068526722> Подача жалобы"))
    container.add_item(discord.ui.Separator())
    container.add_item(discord.ui.TextDisplay("Если действия пользователя или персонала нарушают правила сервера, вы можете сообщить об этом администрации."))
    container.add_item(discord.ui.Separator())
    container.add_item(discord.ui.TextDisplay("Чтобы подать жалобу необходимо нажать на кнопку ниже. В открывшемся окне кратко опишите суть нарушения и прикрепите доказательства (ссылку на сообщение/скриншот)."))
    container.add_item(discord.ui.Separator())
    container.add_item(discord.ui.ActionRow(
        ComplaintButton(),
        ModerationComplaintButton()
    ))

    layout = discord.ui.LayoutView(timeout=None)
    layout.add_item(container)

    await ctx.send(view=layout)
    await ctx.message.delete()


class TiketModal(discord.ui.Modal):
    def __init__(self, tiket_type):
        super().__init__(title=f"📝 {tiket_type}")
        self.tiket_type = tiket_type

        self.description = discord.ui.TextInput(
            label="Описание",
            placeholder="Опишите суть обращения",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=1000
        )
        self.add_item(self.description)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=False)

        if not is_target_guild(interaction.guild):
            return

        tiket_number = format_global_number(get_next_global_number())

        tiket_data = {
            'id': tiket_number,
            'author_id': interaction.user.id,
            'author_name': str(interaction.user),
            'type': self.tiket_type,
            'description': self.description.value,
            'status': 'open',
            'created_at': datetime.now(timezone.utc).timestamp(),
            'message_id': None,
            'channel_id': TIKET_CHANNEL_ID,
            'verdict': None,
            'moderator_id': None,
            'moderator_name': None,
            'moderator_staff_label': None,
            'dm_message_id': None
        }

        tikets_data = load_tikets()
        tikets_data['tikets'].append(tiket_data)
        save_tikets(tikets_data)

        container = build_open_ticket_container(tiket_number, tiket_data)
        layout = discord.ui.LayoutView(timeout=None)
        layout.add_item(container)

        channel = bot.get_channel(TIKET_CHANNEL_ID)
        if channel:
            message = await channel.send(view=layout)
            for tiket in tikets_data['tikets']:
                if tiket['id'] == tiket_number:
                    tiket['message_id'] = message.id
                    break
            save_tikets(tikets_data)

        try:
            v = discord.ui.View(timeout=None)
            v.add_item(VerdictButton(tiket_number, "ticket"))
            v.add_item(DeleteTicketButton(tiket_number, "ticket"))
            bot.add_view(v)
        except:
            pass


class TiketVerdictModal(discord.ui.Modal):
    def __init__(self, tiket_number, tiket_author, tiket_data):
        super().__init__(title=f"⚖️ Закрытие тикета {tiket_number}")
        self.tiket_number = tiket_number
        self.tiket_author = tiket_author
        self.tiket_data = tiket_data

        self.verdict = discord.ui.TextInput(
            label="Решение",
            placeholder="Введите решение по тикету",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=1000
        )
        self.add_item(self.verdict)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=False)

        tikets_data = load_tikets()
        message_id = None
        updated_data = None
        found = False
        for tiket in tikets_data.get('tikets', []):
            if tiket['id'] == self.tiket_number:
                found = True
                tiket['status'] = 'closed'
                tiket['verdict'] = self.verdict.value
                tiket['moderator_id'] = interaction.user.id
                tiket['moderator_name'] = str(interaction.user)
                tiket['moderator_staff_label'] = "Агент поддержки"
                message_id = tiket.get('message_id')
                updated_data = tiket
                break

        if not found:
            return

        save_tikets(tikets_data)

        if message_id and updated_data:
            channel = bot.get_channel(TIKET_CHANNEL_ID)
            if channel:
                try:
                    message = await channel.fetch_message(message_id)
                    if message:
                        new_container = build_closed_ticket_container(self.tiket_number, updated_data)
                        new_layout = discord.ui.LayoutView(timeout=None)
                        new_layout.add_item(new_container)
                        await message.edit(view=new_layout)
                except:
                    pass

        if self.tiket_author:
            dm_id = await send_or_edit_verdict_dm(
                self.tiket_author,
                updated_data
            )
            if dm_id:
                for tiket in tikets_data['tikets']:
                    if tiket['id'] == self.tiket_number:
                        tiket['dm_message_id'] = dm_id
                        break
                save_tikets(tikets_data)

        try:
            v = discord.ui.View(timeout=None)
            v.add_item(ChangeVerdictButton(self.tiket_number, "ticket"))
            v.add_item(DeleteVerdictButton(self.tiket_number, "ticket"))
            bot.add_view(v)
        except:
            pass


class TiketQuestionButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Вопрос",
            emoji=EMOJI_QUESTION,
            style=discord.ButtonStyle.primary,
            custom_id="tiket_question_button"
        )

    async def callback(self, interaction: discord.Interaction):
        if not is_target_guild(interaction.guild):
            await interaction.response.send_message(ERR_UNAVAILABLE, ephemeral=True)
            return
        modal = TiketModal("Вопрос")
        await interaction.response.send_modal(modal)


class TiketBugButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Баг",
            emoji=EMOJI_APPEAL,
            style=discord.ButtonStyle.danger,
            custom_id="tiket_bug_button"
        )

    async def callback(self, interaction: discord.Interaction):
        if not is_target_guild(interaction.guild):
            await interaction.response.send_message(ERR_UNAVAILABLE, ephemeral=True)
            return
        modal = TiketModal("Баг")
        await interaction.response.send_modal(modal)


class TiketSuggestionButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Предложение",
            emoji=EMOJI_STAFF,
            style=discord.ButtonStyle.success,
            custom_id="tiket_suggestion_button"
        )

    async def callback(self, interaction: discord.Interaction):
        if not is_target_guild(interaction.guild):
            await interaction.response.send_message(ERR_UNAVAILABLE, ephemeral=True)
            return
        modal = TiketModal("Предложение")
        await interaction.response.send_modal(modal)


@bot.command(name="formtik")
async def formtik(ctx):
    if not is_target_guild(ctx.guild):
        await ctx.send(ERR_UNAVAILABLE)
        return

    container = discord.ui.Container()
    container.add_item(discord.ui.TextDisplay("## <:Support:1555909739068526722> Создание тикета"))
    container.add_item(discord.ui.Separator())
    container.add_item(discord.ui.TextDisplay("Если у вас есть вопросы, предложения или обнаружили баг - вы можете открыть тикет."))
    container.add_item(discord.ui.Separator())
    container.add_item(discord.ui.TextDisplay("Чтобы открыть тикет необходимо нажать на кнопку ниже. В открывшемся окне опишите суть."))
    container.add_item(discord.ui.Separator())
    container.add_item(discord.ui.ActionRow(
        TiketQuestionButton(),
        TiketBugButton(),
        TiketSuggestionButton()
    ))

    layout = discord.ui.LayoutView(timeout=None)
    layout.add_item(container)

    await ctx.send(view=layout)
    await ctx.message.delete()


class RoleButton(discord.ui.Button):
    def __init__(self, role, emoji=None):
        label = role.name
        if len(label) > 80:
            label = label[:77] + "..."
        super().__init__(
            label=label,
            style=discord.ButtonStyle.primary,
            custom_id=f"role_{role.id}",
            emoji=emoji
        )
        self.role = role

    async def callback(self, interaction: discord.Interaction):
        if not is_target_guild(interaction.guild):
            await interaction.response.send_message(ERR_UNAVAILABLE, ephemeral=True)
            return

        if self.role >= interaction.guild.me.top_role:
            await interaction.response.send_message(ERR_ACTION, ephemeral=True)
            return

        try:
            if self.role in interaction.user.roles:
                await interaction.user.remove_roles(self.role, reason="Снятие роли через кнопку")
                embed = discord.Embed(
                    title="Роль снята",
                    description=f"С вас снята роль {self.role.mention}",
                    color=COLOR_ACCENT
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.user.add_roles(self.role, reason="Выдача роли через кнопку")
                embed = discord.Embed(
                    title="Роль выдана",
                    description=f"Вам выдана роль {self.role.mention}",
                    color=COLOR_LIGHT
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
        except discord.Forbidden:
            try:
                await interaction.response.send_message(ERR_ACTION, ephemeral=True)
            except:
                pass
        except Exception:
            try:
                await interaction.response.send_message(ERR_ACTION, ephemeral=True)
            except:
                pass


@bot.tree.command(name="roleassignment", description="Создать сообщение с кнопками для выдачи ролей")
@app_commands.describe(
    title="Заголовок сообщения (обязательно)",
    text="Текст сообщения (обязательно)",
    role1="Роль 1 (обязательно)",
    role2="Роль 2 (необязательно)",
    role3="Роль 3 (необязательно)",
    role4="Роль 4 (необязательно)",
    role5="Роль 5 (необязательно)",
    role6="Роль 6 (необязательно)",
    emoji1="Эмоджи для кнопки 1 (необязательно)",
    emoji2="Эмоджи для кнопки 2 (необязательно)",
    emoji3="Эмоджи для кнопки 3 (необязательно)",
    emoji4="Эмоджи для кнопки 4 (необязательно)",
    emoji5="Эмоджи для кнопки 5 (необязательно)",
    emoji6="Эмоджи для кнопки 6 (необязательно)",
    channel="Канал для отправки (по умолчанию текущий)",
    color="Цвет эмбеда (необязательно)"
)
@app_commands.choices(
    color=[
        app_commands.Choice(name="🔵 Синий", value="blue"),
        app_commands.Choice(name="🟢 Зелёный", value="green"),
        app_commands.Choice(name="🔴 Красный", value="red"),
        app_commands.Choice(name="🟡 Жёлтый", value="yellow"),
        app_commands.Choice(name="🟣 Фиолетовый", value="purple"),
        app_commands.Choice(name="🟠 Оранжевый", value="orange"),
        app_commands.Choice(name="⚪ Белый", value="white"),
    ]
)
async def roleassignment(
    interaction: discord.Interaction,
    title: str,
    text: str,
    role1: discord.Role,
    role2: discord.Role = None,
    role3: discord.Role = None,
    role4: discord.Role = None,
    role5: discord.Role = None,
    role6: discord.Role = None,
    emoji1: str = None,
    emoji2: str = None,
    emoji3: str = None,
    emoji4: str = None,
    emoji5: str = None,
    emoji6: str = None,
    channel: discord.TextChannel = None,
    color: app_commands.Choice[str] = None
):
    if not is_target_guild(interaction.guild):
        await interaction.response.send_message(ERR_UNAVAILABLE, ephemeral=True)
        return

    if not is_mod(interaction.user):
        await interaction.response.send_message(ERR_UNAVAILABLE, ephemeral=True)
        return

    roles = [role1]
    emojis = [emoji1]

    if role2:
        roles.append(role2)
        emojis.append(emoji2)
    if role3:
        roles.append(role3)
        emojis.append(emoji3)
    if role4:
        roles.append(role4)
        emojis.append(emoji4)
    if role5:
        roles.append(role5)
        emojis.append(emoji5)
    if role6:
        roles.append(role6)
        emojis.append(emoji6)

    if not channel:
        channel = interaction.channel

    colors = {
        "blue": discord.Color.blue(),
        "green": discord.Color.green(),
        "red": discord.Color.red(),
        "yellow": discord.Color.gold(),
        "purple": discord.Color.purple(),
        "orange": discord.Color.orange(),
        "white": discord.Color.light_gray()
    }

    embed_color = colors.get(color.value if color else "blue", discord.Color.blue())

    embed = discord.Embed(
        title=title,
        description=text,
        color=embed_color
    )

    view = discord.ui.View(timeout=None)

    for i, role in enumerate(roles):
        emoji = emojis[i] if i < len(emojis) and emojis[i] else None
        button = RoleButton(role, emoji)
        view.add_item(button)

    await interaction.response.defer(ephemeral=True, thinking=False)

    await channel.send(embed=embed, view=view)

    for role in roles:
        try:
            v = discord.ui.View(timeout=None)
            v.add_item(RoleButton(role))
            bot.add_view(v)
        except:
            pass


@bot.tree.command(name="lockdown", description="Активировать режим полной блокировки (Purple)")
async def lockdown(interaction: discord.Interaction):
    if not is_target_guild(interaction.guild):
        await interaction.response.send_message(ERR_UNAVAILABLE, ephemeral=True)
        return
    if not is_mod(interaction.user):
        await interaction.response.send_message(ERR_UNAVAILABLE, ephemeral=True)
        return
    status = get_raid_status(interaction.guild_id)
    if status['status'] == ANTI_RAID_RED:
        await interaction.response.send_message(ERR_UNAVAILABLE, ephemeral=True)
        return
    status['manual_lockdown'] = True
    await set_raid_status(interaction.guild, ANTI_RAID_RED, status, moderator=interaction.user)
    layout = build_log_layout(
        "Режим полной блокировки активирован",
        fields=[
            ("Длительность", f"{RED_DURATION // 60} минут"),
            ("Меры", "Каналы заблокированы, инвайты удалены, slowmode включён"),
        ],
        footer=staff_footer(interaction.user)
    )
    await interaction.response.send_message(view=layout, ephemeral=True)


@bot.tree.command(name="unlockdown", description="Деактивировать режим полной блокировки")
async def unlockdown(interaction: discord.Interaction):
    if not is_target_guild(interaction.guild):
        await interaction.response.send_message(ERR_UNAVAILABLE, ephemeral=True)
        return
    if not is_mod(interaction.user):
        await interaction.response.send_message(ERR_UNAVAILABLE, ephemeral=True)
        return
    status = get_raid_status(interaction.guild_id)
    if status['status'] != ANTI_RAID_RED:
        await interaction.response.send_message(ERR_UNAVAILABLE, ephemeral=True)
        return
    await set_raid_status(interaction.guild, ANTI_RAID_GREEN, status, moderator=interaction.user)
    layout = build_log_layout(
        "Режим блокировки деактивирован",
        fields=[
            ("Статус", "Blue — нормальный режим"),
        ],
        footer=staff_footer(interaction.user)
    )
    await interaction.response.send_message(view=layout, ephemeral=True)


@bot.tree.command(name="raidstatus", description="Показать текущий статус антирейда")
async def raidstatus(interaction: discord.Interaction):
    if not is_target_guild(interaction.guild):
        await interaction.response.send_message(ERR_UNAVAILABLE, ephemeral=True)
        return
    if not is_mod(interaction.user):
        await interaction.response.send_message(ERR_UNAVAILABLE, ephemeral=True)
        return
    status = get_raid_status(interaction.guild_id)
    tracker = prune_tracker(interaction.guild_id)
    views = {
        ANTI_RAID_GREEN: ("Blue", "Нормальный режим"),
        ANTI_RAID_YELLOW: ("Indigo", "Повышенная готовность"),
        ANTI_RAID_RED: ("Purple", "Полная блокировка")
    }
    title, description = views[status['status']]
    fields = [
        ("Режим", description),
        (f"Join'ов за {RAID_JOIN_TIMEFRAME} сек", str(len(tracker))),
        ("Пороги", f"Indigo: {RAID_JOIN_THRESHOLD} | Purple: {RAID_RED_THRESHOLD}"),
    ]
    if status['status'] == ANTI_RAID_RED and status['red_until']:
        fields.append(("Блокировка до", discord.utils.format_dt(datetime.fromtimestamp(status['red_until'], tz=timezone.utc), 'f')))
    if status['manual_lockdown']:
        fields.append(("Режим", "Активирован вручную"))
    layout = build_log_layout(f"Антирейд: {title}", fields=fields)
    await interaction.response.send_message(view=layout, ephemeral=True)


@bot.tree.command(name="botmsg", description="Отправить сообщение в формате Embed")
@app_commands.describe(
    channel="Канал для отправки",
    title="Заголовок эмбеда (необязательно)",
    text="Текст сообщения (обязательно)",
    role="Роль для тега (необязательно)",
    image="Изображение для эмбеда (необязательно)"
)
async def botmsg(interaction: discord.Interaction, channel: discord.TextChannel, text: str, title: str = None, role: discord.Role = None, image: discord.Attachment = None):
    if not is_target_guild(interaction.guild):
        await interaction.response.send_message(ERR_UNAVAILABLE, ephemeral=True)
        return
    if not is_admin(interaction.user):
        await interaction.response.send_message(ERR_UNAVAILABLE, ephemeral=True)
        return
    embed = discord.Embed(title=title, description=text, color=discord.Color.blue())
    if image:
        embed.set_image(url=image.url)
    try:
        await channel.send(content=role.mention if role else None, embed=embed)
        layout = build_log_layout(
            "Сообщение отправлено",
            fields=[
                ("Канал", channel.mention),
                ("Статус", "Успешно"),
            ] + ([("Тег", role.mention)] if role else []),
            footer=staff_footer(interaction.user)
        )
        await interaction.response.send_message(view=layout, ephemeral=True)
    except:
        await interaction.response.send_message(ERR_ACTION, ephemeral=True)


@bot.tree.command(name="infoid", description="Получить информацию по номеру объекта (наказание / жалоба / тикет)")
@app_commands.describe(number="Номер (например 00001)")
async def infoid(interaction: discord.Interaction, number: str):
    if not is_target_guild(interaction.guild):
        await interaction.response.send_message(ERR_UNAVAILABLE, ephemeral=True)
        return
    if not is_admin(interaction.user):
        await interaction.response.send_message(ERR_UNAVAILABLE, ephemeral=True)
        return

    clean = re.sub(r'[^0-9]', '', number or '')
    if not clean:
        await interaction.response.send_message(ERR_UNAVAILABLE, ephemeral=True)
        return
    num = int(clean)
    target_id = format_global_number(num)

    punishment = None
    pdata = load_punishment_appeals()
    for r in pdata.get('appeals', []):
        if r.get('id') == target_id:
            punishment = r
            break

    complaint = None
    cdata = load_tickets()
    for t in cdata.get('tickets', []):
        if t.get('id') == target_id:
            complaint = t
            break

    ticket = None
    tdata = load_tikets()
    for t in tdata.get('tikets', []):
        if t.get('id') == target_id:
            ticket = t
            break

    if not punishment and not complaint and not ticket:
        await interaction.response.send_message(ERR_UNAVAILABLE, ephemeral=True)
        return

    type_labels = {
        'mute': 'Мут', 'warn': 'Предупреждение', 'kick': 'Кик',
        'ban': 'Бан', 'tempban': 'Временный бан',
        'auto_mute_spam': 'Автомут за спам', 'auto_ban_spam': 'Автобан за спам',
        'auto_mute_invite': 'Автомут за ссылку', 'auto_mute_warns': 'Автомут за 3 варна'
    }

    if punishment:
        type_label = type_labels.get(punishment.get('type', ''), punishment.get('type', ''))
        fields = [
            ("Пользователь", f"<@{punishment['user_id']}>"),
            ("Тип", type_label),
            ("Причина", punishment.get('reason', 'Не указана')),
        ]
        if punishment.get('duration_text'):
            fields.append(("Время", punishment['duration_text']))
        if punishment.get('appeal_verdict'):
            fields.append(("Вердикт по апелляции", str(punishment['appeal_verdict'])[:500]))
        elif punishment.get('appeal'):
            fields.append(("Апелляция", "Подана на рассмотрение"))
        else:
            fields.append(("Апелляция", "Не подана"))
        layout = build_log_layout(
            f"Наказание {target_id}",
            fields=fields,
            footer=f"Модератор: {punishment.get('moderator_label', 'Модератор')} {punishment.get('moderator_name', 'Unknown')} | {punishment.get('moderator_id', 0)}"
        )
        await interaction.response.send_message(view=layout, ephemeral=True)
    elif complaint:
        is_mod = complaint.get('type') == 'moderation'
        title = "Жалоба на персонал" if is_mod else "Жалоба"
        fields = [
            ("Подал", f"<@{complaint['author_id']}>"),
            ("Описание", complaint.get('description', '')[:500]),
            ("Статус", 'Закрыт' if complaint.get('status') == 'closed' else 'Открыт'),
        ]
        footer = None
        if complaint.get('verdict'):
            fields.append(("Вердикт", str(complaint['verdict'])[:500]))
            if complaint.get('moderator_id'):
                footer = f"Модератор: <@{complaint['moderator_id']}>"
        layout = build_log_layout(f"{title} {target_id}", fields=fields, footer=footer)
        await interaction.response.send_message(view=layout, ephemeral=True)
    elif ticket:
        fields = [
            ("Автор", f"<@{ticket['author_id']}>"),
            ("Тип", ticket.get('type', '')),
            ("Описание", ticket.get('description', '')[:500]),
            ("Статус", 'Закрыт' if ticket.get('status') == 'closed' else 'Открыт'),
        ]
        footer = None
        if ticket.get('verdict'):
            fields.append(("Вердикт", str(ticket['verdict'])[:500]))
            if ticket.get('moderator_id'):
                footer = f"Агент поддержки: <@{ticket['moderator_id']}>"
        layout = build_log_layout(f"Тикет {target_id}", fields=fields, footer=footer)
        await interaction.response.send_message(view=layout, ephemeral=True)


@bot.tree.command(name="mute", description="Замутить участника на определённое время")
@app_commands.describe(user="Участник, которого нужно замутить", amount="Количество времени", unit="Единица времени", reason="Причина мута (обязательно)")
@app_commands.choices(unit=[
    app_commands.Choice(name="Секунды", value="seconds"),
    app_commands.Choice(name="Минуты", value="minutes"),
    app_commands.Choice(name="Часы", value="hours"),
    app_commands.Choice(name="Дни", value="days"),
])
async def mute(interaction: discord.Interaction, user: discord.Member, amount: int, unit: app_commands.Choice[str], reason: str):
    if not is_target_guild(interaction.guild):
        await interaction.response.send_message(ERR_UNAVAILABLE, ephemeral=True)
        return
    if not is_ticket_mod(interaction.user):
        await interaction.response.send_message(ERR_UNAVAILABLE, ephemeral=True)
        return
    if user == interaction.user or user.bot:
        await interaction.response.send_message(ERR_ACTION, ephemeral=True)
        return

    if user.guild_permissions.administrator:
        await interaction.response.send_message(ERR_ACTION, ephemeral=True)
        return

    if user.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
        await interaction.response.send_message(ERR_ACTION, ephemeral=True)
        return

    bot_member = interaction.guild.me
    if not bot_member.guild_permissions.moderate_members:
        await interaction.response.send_message(ERR_ACTION, ephemeral=True)
        return

    if user.top_role >= bot_member.top_role:
        await interaction.response.send_message(ERR_ACTION, ephemeral=True)
        return

    time_multipliers = {"seconds": 1, "minutes": 60, "hours": 3600, "days": 86400}
    unit_map = {"seconds": "second", "minutes": "minute", "hours": "hour", "days": "day"}
    duration_seconds = amount * time_multipliers[unit.value]
    if duration_seconds > 28 * 24 * 3600 or duration_seconds < 1:
        await interaction.response.send_message(ERR_UNAVAILABLE, ephemeral=True)
        return
    try:
        await interaction.response.defer(ephemeral=True, thinking=False)
        until = discord.utils.utcnow() + timedelta(seconds=duration_seconds)
        await user.timeout(until, reason=reason)
        time_text = pluralize_time(amount, unit_map[unit.value])

        record = await create_punishment_and_dm(
            interaction.guild,
            user,
            'mute',
            'Вы получили мут',
            reason,
            moderator=interaction.user,
            duration_text=time_text,
            can_appeal=True
        )

        layout = build_log_layout(
            "Выдан мут",
            fields=[
                ("Номер", record['id']),
                ("Участник", user.mention),
                ("Время", time_text),
                ("Причина", reason),
            ],
            footer=staff_footer(interaction.user)
        )
        await send_log_layout(layout, LOG_ALL_CHANNEL_ID, interaction.guild)
    except:
        try:
            await interaction.followup.send(ERR_ACTION, ephemeral=True)
        except:
            pass


@bot.tree.command(name="unmute", description="Снять мут с участника")
@app_commands.describe(user="Участник, с которого нужно снять мут", reason="Причина снятия мута (обязательно)")
async def unmute(interaction: discord.Interaction, user: discord.Member, reason: str):
    if not is_target_guild(interaction.guild):
        await interaction.response.send_message(ERR_UNAVAILABLE, ephemeral=True)
        return
    if not is_ticket_mod(interaction.user):
        await interaction.response.send_message(ERR_UNAVAILABLE, ephemeral=True)
        return

    if user.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
        await interaction.response.send_message(ERR_ACTION, ephemeral=True)
        return

    try:
        await interaction.response.defer(ephemeral=True, thinking=False)
        await user.timeout(None, reason=reason)
        layout = build_log_layout(
            "Мут снят",
            fields=[
                ("Участник", user.mention),
                ("Причина", reason),
            ],
            footer=staff_footer(interaction.user)
        )
        await send_log_layout(layout, LOG_ALL_CHANNEL_ID, interaction.guild)
    except:
        try:
            await interaction.followup.send(ERR_ACTION, ephemeral=True)
        except:
            pass


@bot.tree.command(name="kick", description="Выгнать участника с сервера")
@app_commands.describe(user="Участник, которого нужно выгнать", reason="Причина выгона (обязательно)")
async def kick(interaction: discord.Interaction, user: discord.Member, reason: str):
    if not is_target_guild(interaction.guild):
        await interaction.response.send_message(ERR_UNAVAILABLE, ephemeral=True)
        return
    if not is_admin(interaction.user):
        await interaction.response.send_message(ERR_UNAVAILABLE, ephemeral=True)
        return
    if user == interaction.user:
        await interaction.response.send_message(ERR_ACTION, ephemeral=True)
        return
    if user == interaction.guild.me:
        await interaction.response.send_message(ERR_ACTION, ephemeral=True)
        return
    if user.guild_permissions.administrator:
        await interaction.response.send_message(ERR_ACTION, ephemeral=True)
        return
    if user.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
        await interaction.response.send_message(ERR_ACTION, ephemeral=True)
        return

    bot_member = interaction.guild.me
    if not bot_member.guild_permissions.kick_members:
        await interaction.response.send_message(ERR_ACTION, ephemeral=True)
        return

    if user.top_role >= bot_member.top_role:
        await interaction.response.send_message(ERR_ACTION, ephemeral=True)
        return

    try:
        await interaction.response.defer(ephemeral=True, thinking=False)

        record = await create_punishment_and_dm(
            interaction.guild,
            user,
            'kick',
            'Вы были кикнуты с сервера',
            reason,
            moderator=interaction.user,
            can_appeal=True
        )

        layout = build_log_layout(
            "Выдан кик",
            fields=[
                ("Номер", record['id']),
                ("Участник", str(user)),
                ("Причина", reason),
            ],
            footer=staff_footer(interaction.user)
        )
        await send_log_layout(layout, LOG_ALL_CHANNEL_ID, interaction.guild)

        await user.kick(reason=reason)
    except discord.Forbidden:
        try:
            await interaction.followup.send(ERR_ACTION, ephemeral=True)
        except:
            pass
    except Exception:
        try:
            await interaction.followup.send(ERR_ACTION, ephemeral=True)
        except:
            pass


@bot.tree.command(name="ban", description="Забанить участника на сервере (вечный бан)")
@app_commands.describe(user="Участник, которого нужно забанить", reason="Причина бана (обязательно)", delete_message_days="Количество дней сообщений для удаления (0-7)")
async def ban(interaction: discord.Interaction, user: discord.Member, reason: str, delete_message_days: int = 0):
    if not is_target_guild(interaction.guild):
        await interaction.response.send_message(ERR_UNAVAILABLE, ephemeral=True)
        return
    if not is_admin(interaction.user):
        await interaction.response.send_message(ERR_UNAVAILABLE, ephemeral=True)
        return
    if user == interaction.user:
        await interaction.response.send_message(ERR_ACTION, ephemeral=True)
        return
    if user == interaction.guild.me:
        await interaction.response.send_message(ERR_ACTION, ephemeral=True)
        return
    if user.guild_permissions.administrator:
        await interaction.response.send_message(ERR_ACTION, ephemeral=True)
        return
    if user.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
        await interaction.response.send_message(ERR_ACTION, ephemeral=True)
        return

    bot_member = interaction.guild.me
    if not bot_member.guild_permissions.ban_members:
        await interaction.response.send_message(ERR_ACTION, ephemeral=True)
        return

    if user.top_role >= bot_member.top_role:
        await interaction.response.send_message(ERR_ACTION, ephemeral=True)
        return

    if delete_message_days < 0 or delete_message_days > 7:
        await interaction.response.send_message(ERR_UNAVAILABLE, ephemeral=True)
        return
    try:
        await interaction.response.defer(ephemeral=True, thinking=False)

        record = await create_punishment_and_dm(
            interaction.guild,
            user,
            'ban',
            'Вы были забанены',
            reason,
            moderator=interaction.user,
            extra_lines=[f"Удалено сообщений: {delete_message_days} дней"],
            can_appeal=True
        )

        layout = build_log_layout(
            "Выдан бан",
            fields=[
                ("Номер", record['id']),
                ("Участник", str(user)),
                ("Удалено сообщений", f"{delete_message_days} дней"),
                ("Причина", reason),
            ],
            footer=staff_footer(interaction.user)
        )
        await send_log_layout(layout, LOG_ALL_CHANNEL_ID, interaction.guild)

        await user.ban(reason=reason, delete_message_days=delete_message_days)
    except discord.Forbidden:
        try:
            await interaction.followup.send(ERR_ACTION, ephemeral=True)
        except:
            pass
    except Exception:
        try:
            await interaction.followup.send(ERR_ACTION, ephemeral=True)
        except:
            pass


@bot.tree.command(name="unban", description="Разбанить участника на сервере")
@app_commands.describe(user_id="ID пользователя, которого нужно разбанить", reason="Причина разбана")
async def unban(interaction: discord.Interaction, user_id: str, reason: str = "Не указана"):
    if not is_target_guild(interaction.guild):
        await interaction.response.send_message(ERR_UNAVAILABLE, ephemeral=True)
        return
    if not is_admin(interaction.user):
        await interaction.response.send_message(ERR_UNAVAILABLE, ephemeral=True)
        return
    try:
        await interaction.response.defer(ephemeral=True, thinking=False)
        user = await bot.fetch_user(int(user_id))
        await interaction.guild.unban(user, reason=reason)

        layout = build_log_layout(
            "Пользователь разбанен",
            fields=[
                ("Участник", f"{user}"),
                ("Причина", reason),
            ],
            footer=staff_footer(interaction.user)
        )
        await send_log_layout(layout, LOG_ALL_CHANNEL_ID, interaction.guild)
    except:
        try:
            await interaction.followup.send(ERR_ACTION, ephemeral=True)
        except:
            pass


@bot.tree.command(name="tempban", description="Забанить участника на определённое время")
@app_commands.describe(user="Участник, которого нужно забанить", days="Количество дней бана", reason="Причина бана (обязательно)")
async def tempban(interaction: discord.Interaction, user: discord.Member, days: int, reason: str):
    if not is_target_guild(interaction.guild):
        await interaction.response.send_message(ERR_UNAVAILABLE, ephemeral=True)
        return
    if not is_ticket_mod(interaction.user):
        await interaction.response.send_message(ERR_UNAVAILABLE, ephemeral=True)
        return
    if user == interaction.user:
        await interaction.response.send_message(ERR_ACTION, ephemeral=True)
        return
    if user == interaction.guild.me:
        await interaction.response.send_message(ERR_ACTION, ephemeral=True)
        return
    if user.guild_permissions.administrator:
        await interaction.response.send_message(ERR_ACTION, ephemeral=True)
        return
    if user.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
        await interaction.response.send_message(ERR_ACTION, ephemeral=True)
        return

    bot_member = interaction.guild.me
    if not bot_member.guild_permissions.ban_members:
        await interaction.response.send_message(ERR_ACTION, ephemeral=True)
        return

    if user.top_role >= bot_member.top_role:
        await interaction.response.send_message(ERR_ACTION, ephemeral=True)
        return

    if days < 1:
        await interaction.response.send_message(ERR_UNAVAILABLE, ephemeral=True)
        return
    try:
        await interaction.response.defer(ephemeral=True, thinking=False)

        time_text = pluralize_time(days, 'day')

        record = await create_punishment_and_dm(
            interaction.guild,
            user,
            'tempban',
            'Вы были забанены',
            reason,
            moderator=interaction.user,
            duration_text=time_text,
            extra_lines=["Тип: Временный бан"],
            can_appeal=True
        )

        layout = build_log_layout(
            "Выдан временный бан",
            fields=[
                ("Номер", record['id']),
                ("Участник", str(user)),
                ("Время", time_text),
                ("Причина", reason),
            ],
            footer=staff_footer(interaction.user)
        )
        await send_log_layout(layout, LOG_ALL_CHANNEL_ID, interaction.guild)

        await user.ban(reason=reason)

        async def unban_later():
            await asyncio.sleep(days * 24 * 3600)
            try:
                await interaction.guild.unban(user, reason="Автоматический разбан")
                auto_layout = build_log_layout(
                    "Автоматический разбан",
                    fields=[
                        ("Участник", f"{user}"),
                        ("Причина", "Истечение времени бана"),
                    ]
                )
                await send_log_layout(auto_layout, LOG_ALL_CHANNEL_ID, interaction.guild)
            except:
                pass
        bot.loop.create_task(unban_later())
    except discord.Forbidden:
        try:
            await interaction.followup.send(ERR_ACTION, ephemeral=True)
        except:
            pass
    except Exception:
        try:
            await interaction.followup.send(ERR_ACTION, ephemeral=True)
        except:
            pass


@bot.tree.command(name="warn", description="Выдать предупреждение участнику")
@app_commands.describe(user="Участник, которому нужно выдать предупреждение", reason="Причина предупреждения (обязательно)")
async def warn(interaction: discord.Interaction, user: discord.Member, reason: str):
    if not is_target_guild(interaction.guild):
        await interaction.response.send_message(ERR_UNAVAILABLE, ephemeral=True)
        return
    if not is_ticket_mod(interaction.user):
        await interaction.response.send_message(ERR_UNAVAILABLE, ephemeral=True)
        return
    if user == interaction.user or user.bot:
        await interaction.response.send_message(ERR_ACTION, ephemeral=True)
        return
    if user.guild_permissions.administrator:
        await interaction.response.send_message(ERR_ACTION, ephemeral=True)
        return
    if user.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
        await interaction.response.send_message(ERR_ACTION, ephemeral=True)
        return
    try:
        await interaction.response.defer(ephemeral=True, thinking=False)
        user_warns = get_user_warns(interaction.guild_id, user.id)
        if len(user_warns) >= MAX_WARNS:
            await interaction.followup.send(ERR_UNAVAILABLE, ephemeral=True)
            return
        user_warns.append({'reason': reason, 'moderator': interaction.user.id, 'timestamp': datetime.now(timezone.utc).timestamp()})
        save_user_warns(interaction.guild_id, user.id, user_warns)
        warn_count = len(user_warns)

        record = await create_punishment_and_dm(
            interaction.guild,
            user,
            'warn',
            'Вы получили предупреждение',
            reason,
            moderator=interaction.user,
            warn_count=warn_count,
            max_warns=MAX_WARNS,
            can_appeal=True
        )

        layout = build_log_layout(
            "Выдано предупреждение",
            fields=[
                ("Номер", record['id']),
                ("Участник", user.mention),
                ("Всего предупреждений", f"{warn_count}/{MAX_WARNS}"),
                ("Причина", reason),
            ],
            footer=staff_footer(interaction.user)
        )
        await send_log_layout(layout, LOG_ALL_CHANNEL_ID, interaction.guild)

        if warn_count >= MAX_WARNS:
            try:
                await user.timeout(discord.utils.utcnow() + timedelta(seconds=WARN_MUTE_DURATION), reason="Автоматический мут за 3 предупреждения")
                clear_user_warns(interaction.guild_id, user.id)

                record2 = await create_punishment_and_dm(
                    interaction.guild,
                    user,
                    'auto_mute_warns',
                    'Вы получили автоматический мут',
                    'Получено 3 предупреждения',
                    moderator=interaction.user,
                    duration_text='12 часов',
                    can_appeal=True
                )

                auto_layout = build_log_layout(
                    "Автоматический мут за 3 предупреждения",
                    fields=[
                        ("Номер", record2['id']),
                        ("Участник", user.mention),
                        ("Время", "12 часов"),
                        ("Причина", "Получено 3 предупреждения"),
                    ]
                )
                await send_log_layout(auto_layout, LOG_ALL_CHANNEL_ID, interaction.guild)
            except:
                pass
    except:
        try:
            await interaction.followup.send(ERR_ACTION, ephemeral=True)
        except:
            pass


@bot.tree.command(name="unwarn", description="Снять одно предупреждение с участника")
@app_commands.describe(user="Участник, у которого нужно снять предупреждение", reason="Причина снятия предупреждения (обязательно)")
async def unwarn(interaction: discord.Interaction, user: discord.Member, reason: str):
    if not is_target_guild(interaction.guild):
        await interaction.response.send_message(ERR_UNAVAILABLE, ephemeral=True)
        return
    if not is_ticket_mod(interaction.user):
        await interaction.response.send_message(ERR_UNAVAILABLE, ephemeral=True)
        return
    if user.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
        await interaction.response.send_message(ERR_ACTION, ephemeral=True)
        return
    try:
        await interaction.response.defer(ephemeral=True, thinking=False)
        user_warns = get_user_warns(interaction.guild_id, user.id)
        if not user_warns:
            await interaction.followup.send(ERR_UNAVAILABLE, ephemeral=True)
            return
        removed_warn = user_warns.pop()
        save_user_warns(interaction.guild_id, user.id, user_warns)

        layout = build_log_layout(
            "Предупреждение снято",
            fields=[
                ("Участник", user.mention),
                ("Осталось предупреждений", f"{len(user_warns)}/{MAX_WARNS}"),
                ("Снятое предупреждение", removed_warn['reason']),
                ("Причина снятия", reason),
            ],
            footer=staff_footer(interaction.user)
        )
        await send_log_layout(layout, LOG_ALL_CHANNEL_ID, interaction.guild)
    except:
        try:
            await interaction.followup.send(ERR_ACTION, ephemeral=True)
        except:
            pass


@bot.tree.command(name="warns", description="Показать количество предупреждений пользователя")
@app_commands.describe(user="Пользователь, у которого нужно проверить предупреждения")
async def warns(interaction: discord.Interaction, user: discord.Member):
    if not is_target_guild(interaction.guild):
        await interaction.response.send_message(ERR_UNAVAILABLE, ephemeral=True)
        return
    if not is_admin(interaction.user):
        await interaction.response.send_message(ERR_UNAVAILABLE, ephemeral=True)
        return
    try:
        user_warns = get_user_warns(interaction.guild_id, user.id)
        warn_count = len(user_warns)
        fields = [
            ("Пользователь", user.mention),
            ("Количество", f"{warn_count}/{MAX_WARNS}"),
        ]
        if user_warns:
            warns_text = ""
            for i, warn_data in enumerate(user_warns, 1):
                try:
                    moderator = await bot.fetch_user(warn_data['moderator'])
                    moderator_text = moderator.name
                except:
                    moderator_text = "Неизвестно"
                timestamp = datetime.fromtimestamp(warn_data['timestamp']).strftime("%d.%m.%Y %H:%M")
                warns_text += f"**{i}.** {warn_data['reason']}\nМодератор: {moderator_text} | Дата: {timestamp}\n"
            fields.append(("Детали", warns_text[:1000]))
        else:
            fields.append(("Детали", "Нет предупреждений"))
        layout = build_log_layout("Предупреждения пользователя", fields=fields)
        await interaction.response.send_message(view=layout)
    except:
        await interaction.response.send_message(ERR_ACTION, ephemeral=True)


@bot.tree.command(name="clear", description="Очистить сообщения в канале")
@app_commands.describe(amount="Количество сообщений для удаления (1-100)", user="Удалить сообщения только от определённого пользователя")
async def clear(interaction: discord.Interaction, amount: int, user: discord.Member = None):
    if not is_target_guild(interaction.guild):
        await interaction.response.send_message(ERR_UNAVAILABLE, ephemeral=True)
        return
    if not is_admin(interaction.user):
        await interaction.response.send_message(ERR_UNAVAILABLE, ephemeral=True)
        return
    if amount < 1 or amount > 100:
        await interaction.response.send_message(ERR_UNAVAILABLE, ephemeral=True)
        return
    try:
        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=amount, check=lambda m: m.author == user if user else True)
        layout = build_log_layout(
            "Очистка канала",
            fields=[
                ("Канал", interaction.channel.mention),
                ("Удалено", f"{len(deleted)} сообщений"),
                ("Фильтр", user.mention if user else "Нет"),
            ],
            footer=staff_footer(interaction.user)
        )
        await send_log_layout(layout, LOG_ALL_CHANNEL_ID, interaction.guild)
        await interaction.followup.send("Готово", ephemeral=True)
    except:
        await interaction.followup.send(ERR_ACTION, ephemeral=True)


class PunishmentAppealButton(discord.ui.Button):
    def __init__(self, appeal_id):
        super().__init__(
            label="Апелляция",
            emoji=EMOJI_APPEAL_BTN,
            style=discord.ButtonStyle.secondary,
            custom_id=f"punishment_appeal_{appeal_id}"
        )
        self.appeal_id = appeal_id

    async def callback(self, interaction: discord.Interaction):
        data = load_punishment_appeals()
        record = None
        for r in data.get('appeals', []):
            if r.get('id') == self.appeal_id:
                record = r
                break
        if not record:
            await interaction.response.send_message(ERR_UNAVAILABLE, ephemeral=True)
            return
        if record.get('appeal'):
            await interaction.response.send_message(ERR_UNAVAILABLE, ephemeral=True)
            return
        if record.get('appeal_verdict'):
            await interaction.response.send_message(ERR_UNAVAILABLE, ephemeral=True)
            return
        if interaction.user.id != record.get('user_id'):
            await interaction.response.send_message(ERR_UNAVAILABLE, ephemeral=True)
            return
        await interaction.response.send_modal(PunishmentAppealModal(self.appeal_id))


class PunishmentAppealModal(discord.ui.Modal):
    def __init__(self, appeal_id):
        super().__init__(title=f"Апелляция {appeal_id}")
        self.appeal_id = appeal_id

        self.content = discord.ui.TextInput(
            label="Содержание",
            placeholder="Опишите причину апелляции",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=1000
        )
        self.add_item(self.content)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=False)

        data = load_punishment_appeals()
        record = None
        for r in data.get('appeals', []):
            if r.get('id') == self.appeal_id:
                record = r
                break

        if not record:
            return

        if record.get('appeal'):
            return

        record['appeal'] = self.content.value
        record['appeal_author_id'] = interaction.user.id
        save_punishment_appeals(data)

        container = build_punishment_appeal_container(record)
        layout = discord.ui.LayoutView(timeout=None)
        layout.add_item(container)

        channel = bot.get_channel(APPEAL_CHANNEL_ID)
        if channel:
            msg = await channel.send(view=layout)
            data = load_punishment_appeals()
            for r in data.get('appeals', []):
                if r.get('id') == self.appeal_id:
                    r['appeal_message_id'] = msg.id
                    break
            save_punishment_appeals(data)
            record['appeal_message_id'] = msg.id

        dm_id = record.get('dm_message_id')
        if dm_id:
            try:
                user = await bot.fetch_user(record['user_id'])
                dm_channel = user.dm_channel
                if dm_channel is None:
                    dm_channel = await user.create_dm()
                msg = await dm_channel.fetch_message(dm_id)
                await msg.edit(view=build_punishment_dm_container(record))
            except:
                pass

        try:
            v = discord.ui.View(timeout=None)
            v.add_item(PunishmentAppealVerdictButton(self.appeal_id))
            bot.add_view(v)
        except:
            pass


class PunishmentAppealVerdictButton(discord.ui.Button):
    def __init__(self, appeal_id):
        super().__init__(
            label="Вынести вердикт",
            emoji=EMOJI_JUDGE,
            style=discord.ButtonStyle.secondary,
            custom_id=f"punishment_appeal_verdict_{appeal_id}"
        )
        self.appeal_id = appeal_id

    async def callback(self, interaction: discord.Interaction):
        if not is_admin(interaction.user):
            await interaction.response.send_message(ERR_UNAVAILABLE, ephemeral=True)
            return
        await interaction.response.send_modal(PunishmentAppealVerdictModal(self.appeal_id))


class PunishmentAppealVerdictModal(discord.ui.Modal):
    def __init__(self, appeal_id):
        super().__init__(title=f"Вердикт по апелляции {appeal_id}")
        self.appeal_id = appeal_id

        self.verdict = discord.ui.TextInput(
            label="Вердикт",
            placeholder="Введите решение по апелляции",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=1000
        )
        self.add_item(self.verdict)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=False)

        data = load_punishment_appeals()
        record = None
        for r in data.get('appeals', []):
            if r.get('id') == self.appeal_id:
                record = r
                break
        if not record:
            return

        record['appeal_verdict'] = self.verdict.value
        record['appeal_moderator_id'] = interaction.user.id
        record['appeal_moderator_name'] = str(interaction.user)
        record['appeal_verdict_changed'] = False
        save_punishment_appeals(data)

        message_id = record.get('appeal_message_id')
        if message_id:
            channel = bot.get_channel(APPEAL_CHANNEL_ID)
            if channel:
                try:
                    msg = await channel.fetch_message(message_id)
                    if msg:
                        new_container = build_punishment_appeal_container(record)
                        new_layout = discord.ui.LayoutView(timeout=None)
                        new_layout.add_item(new_container)
                        await msg.edit(view=new_layout)
                except:
                    pass

        dm_id = record.get('dm_message_id')
        if dm_id:
            try:
                user = await bot.fetch_user(record['user_id'])
                dm_channel = user.dm_channel
                if dm_channel is None:
                    dm_channel = await user.create_dm()
                msg = await dm_channel.fetch_message(dm_id)
                await msg.edit(view=build_punishment_dm_container(record))
            except:
                pass

        try:
            v = discord.ui.View(timeout=None)
            v.add_item(PunishmentAppealChangeVerdictButton(self.appeal_id))
            v.add_item(PunishmentAppealDeleteVerdictButton(self.appeal_id))
            bot.add_view(v)
        except:
            pass


class PunishmentAppealChangeVerdictButton(discord.ui.Button):
    def __init__(self, appeal_id):
        super().__init__(
            label="Изменить вердикт",
            emoji=EMOJI_WRITING,
            style=discord.ButtonStyle.success,
            custom_id=f"punishment_appeal_change_{appeal_id}"
        )
        self.appeal_id = appeal_id

    async def callback(self, interaction: discord.Interaction):
        if not is_admin(interaction.user):
            await interaction.response.send_message(ERR_UNAVAILABLE, ephemeral=True)
            return

        data = load_punishment_appeals()
        record = None
        for r in data.get('appeals', []):
            if r.get('id') == self.appeal_id:
                record = r
                break
        if not record:
            await interaction.response.send_message(ERR_UNAVAILABLE, ephemeral=True)
            return

        await interaction.response.send_modal(PunishmentAppealChangeVerdictModal(self.appeal_id, record))


class PunishmentAppealChangeVerdictModal(discord.ui.Modal):
    def __init__(self, appeal_id, record):
        super().__init__(title=f"Изменить вердикт апелляции {appeal_id}")
        self.appeal_id = appeal_id
        self.record = record

        self.new_verdict = discord.ui.TextInput(
            label="Новый вердикт",
            placeholder="Введите новый вердикт",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=1000,
            default=record.get('appeal_verdict', '') or ''
        )
        self.add_item(self.new_verdict)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=False)

        data = load_punishment_appeals()
        updated = None
        for r in data.get('appeals', []):
            if r.get('id') == self.appeal_id:
                r['appeal_verdict'] = self.new_verdict.value
                r['appeal_moderator_id'] = interaction.user.id
                r['appeal_moderator_name'] = str(interaction.user)
                r['appeal_verdict_changed'] = True
                updated = r
                break
        save_punishment_appeals(data)

        if updated:
            message_id = updated.get('appeal_message_id')
            if message_id:
                channel = bot.get_channel(APPEAL_CHANNEL_ID)
                if channel:
                    try:
                        msg = await channel.fetch_message(message_id)
                        if msg:
                            new_container = build_punishment_appeal_container(updated)
                            new_layout = discord.ui.LayoutView(timeout=None)
                            new_layout.add_item(new_container)
                            await msg.edit(view=new_layout)
                    except:
                        pass

            dm_id = updated.get('dm_message_id')
            if dm_id:
                try:
                    user = await bot.fetch_user(updated['user_id'])
                    dm_channel = user.dm_channel
                    if dm_channel is None:
                        dm_channel = await user.create_dm()
                    msg = await dm_channel.fetch_message(dm_id)
                    await msg.edit(view=build_punishment_dm_container(updated))
                except:
                    pass


class PunishmentAppealDeleteVerdictButton(discord.ui.Button):
    def __init__(self, appeal_id):
        super().__init__(
            label="Удалить вердикт",
            emoji=EMOJI_TRASH,
            style=discord.ButtonStyle.danger,
            custom_id=f"punishment_appeal_delete_{appeal_id}"
        )
        self.appeal_id = appeal_id

    async def callback(self, interaction: discord.Interaction):
        if not is_admin(interaction.user):
            await interaction.response.send_message(ERR_UNAVAILABLE, ephemeral=True)
            return

        await interaction.response.defer()

        data = load_punishment_appeals()
        updated = None
        for r in data.get('appeals', []):
            if r.get('id') == self.appeal_id:
                r['appeal_verdict'] = None
                r['appeal_moderator_id'] = None
                r['appeal_moderator_name'] = None
                r['appeal_verdict_changed'] = False
                updated = r
                break
        save_punishment_appeals(data)

        if updated:
            message_id = updated.get('appeal_message_id')
            if message_id:
                channel = bot.get_channel(APPEAL_CHANNEL_ID)
                if channel:
                    try:
                        msg = await channel.fetch_message(message_id)
                        if msg:
                            new_container = build_punishment_appeal_container(updated)
                            new_layout = discord.ui.LayoutView(timeout=None)
                            new_layout.add_item(new_container)
                            await msg.edit(view=new_layout)
                    except:
                        pass

            dm_id = updated.get('dm_message_id')
            if dm_id:
                try:
                    user = await bot.fetch_user(updated['user_id'])
                    dm_channel = user.dm_channel
                    if dm_channel is None:
                        dm_channel = await user.create_dm()
                    msg = await dm_channel.fetch_message(dm_id)
                    await msg.edit(view=build_punishment_dm_container(updated))
                except:
                    pass

        try:
            v = discord.ui.View(timeout=None)
            v.add_item(PunishmentAppealVerdictButton(self.appeal_id))
            bot.add_view(v)
        except:
            pass


if __name__ == "__main__":
    TOKEN = os.getenv ("DISCORD_TOKEN")
    if not TOKEN:
        print("Коля пизда.")
    else:
        bot.run(TOKEN)