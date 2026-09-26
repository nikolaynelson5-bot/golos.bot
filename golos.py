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

GROUP_TICKET_MOD = [TICKET_MODERATOR_ROLE_ID]
GROUP_ADMIN = [ADMIN_ROLE_ID]
GROUP_MOD = [MODERATOR_ROLE_ID]

raid_status = {}
join_tracker = {}

def has_role(member, role_id):
    if not isinstance(member, discord.Member):
        return False
    return any(role.id == role_id for role in member.roles)

def is_mod(member):
    """Роль 1508078492552663141 — видит всё (админ)"""
    return has_role(member, MODERATOR_ROLE_ID)

def is_admin(member):
    """Роль 1507395265215074434 — видит свои + команды тикет-модера"""
    return has_role(member, ADMIN_ROLE_ID) or is_mod(member)

def is_ticket_mod(member):
    """Роль 1543330529036996708 — только свои команды"""
    return has_role(member, TICKET_MODERATOR_ROLE_ID) or is_admin(member)

def is_admin_or_owner(interaction):
    return interaction.user.id == interaction.guild.owner_id or interaction.user.guild_permissions.administrator

def is_target_guild(guild):
    return guild.id == TARGET_GUILD_ID

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
                if 'counter' not in data:
                    data['counter'] = 0
                if 'tickets' not in data or not isinstance(data['tickets'], list):
                    data['tickets'] = []
                return data
        except:
            return {'counter': 0, 'tickets': []}
    return {'counter': 0, 'tickets': []}

def save_tickets(tickets_data):
    if not isinstance(tickets_data, dict):
        tickets_data = {'counter': 0, 'tickets': []}
    if 'counter' not in tickets_data:
        tickets_data['counter'] = 0
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
                if 'counter' not in data:
                    data['counter'] = 0
                if 'tikets' not in data or not isinstance(data['tikets'], list):
                    data['tikets'] = []
                return data
        except:
            return {'counter': 0, 'tikets': []}
    return {'counter': 0, 'tikets': []}

def save_tikets(tikets_data):
    if not isinstance(tikets_data, dict):
        tikets_data = {'counter': 0, 'tikets': []}
    if 'counter' not in tikets_data:
        tikets_data['counter'] = 0
    if 'tikets' not in tikets_data or not isinstance(tikets_data['tikets'], list):
        tikets_data['tikets'] = []
    try:
        with open(TIKET_FILE, 'w', encoding='utf-8') as f:
            json.dump(tikets_data, f, indent=4, ensure_ascii=False)
    except:
        pass

def get_ticket_number(counter):
    if counter < 10:
        return f"Ж-00-0{counter}"
    elif counter < 100:
        return f"Ж-00-{counter}"
    elif counter < 1000:
        return f"Ж-0{counter // 100}-{counter % 100:02d}"
    else:
        return f"Ж-{counter // 1000}-{counter % 1000:03d}"

def get_tiket_number(counter):
    if counter < 10:
        return f"T-00-0{counter}"
    elif counter < 100:
        return f"T-00-{counter}"
    elif counter < 1000:
        return f"T-0{counter // 100}-{counter % 100:02d}"
    else:
        return f"T-{counter // 1000}-{counter % 1000:03d}"

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

async def set_raid_status(guild, new_status, status):
    if not is_target_guild(guild):
        return
    status['status'] = new_status
    if new_status == ANTI_RAID_YELLOW:
        await setup_raid_yellow(guild, status)
        embed = base_embed("🔷 Антирейд: Повышенная готовность", COLOR_INFO)
        embed.add_field(name="Сервер", value=guild.name, inline=True)
        embed.add_field(name="Статус", value="Активирован Жёлтый режим", inline=True)
        embed.add_field(name="Действие", value="Выдана роль 'Raid Alert' всем пользователям", inline=False)
        role = guild.get_role(ALERT_ROLE_ID)
        if role:
            embed.add_field(name="Упоминание", value=role.mention, inline=False)
        await send_log(embed, LOG_ALL_CHANNEL_ID, guild)
    elif new_status == ANTI_RAID_RED:
        status['red_until'] = datetime.now(timezone.utc).timestamp() + RED_DURATION
        await setup_raid_red(guild, status)
        embed = base_embed("🟣 Антирейд: Полная блокировка", COLOR_ACCENT)
        embed.add_field(name="Сервер", value=guild.name, inline=True)
        embed.add_field(name="Статус", value="Активирован Красный режим", inline=True)
        embed.add_field(name="Действия", value="Каналы заблокированы, приглашения удалены, slowmode включён", inline=False)
        role = guild.get_role(ALERT_ROLE_ID)
        if role:
            embed.add_field(name="Упоминание", value=role.mention, inline=False)
        await send_log(embed, LOG_ALL_CHANNEL_ID, guild)
    elif new_status == ANTI_RAID_GREEN:
        status['manual_lockdown'] = False
        status['red_until'] = None
        status['last_join'] = None
        await setup_raid_green(guild, status)
        embed = base_embed("🟦 Антирейд: Нормальный режим", COLOR_LIGHT)
        embed.add_field(name="Сервер", value=guild.name, inline=True)
        embed.add_field(name="Статус", value="Деактивирован режим антирейда", inline=True)
        await send_log(embed, LOG_ALL_CHANNEL_ID, guild)

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

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'✅ Бот {bot.user} запущен и готов к работе!')
    print(f'📊 На серверах: {len(bot.guilds)}')
    bot.loop.create_task(check_auto_unwarn())
    bot.loop.create_task(check_raid_status())

@bot.event
async def on_member_join(member):
    if not is_target_guild(member.guild):
        return
    get_join_tracker(member.guild.id).append(datetime.now(timezone.utc).timestamp())
    get_raid_status(member.guild.id)['last_join'] = datetime.now(timezone.utc).timestamp()
    
    invite = None
    try:
        async for entry in member.guild.audit_logs(limit=1, action=discord.AuditLogAction.invite):
            if entry.target.id == member.id:
                invite = entry
                break
    except:
        pass
    
    embed = base_embed("🔹 Новый участник присоединился", COLOR_INFO)
    embed.add_field(name="Пользователь", value=member.mention, inline=True)
    if invite:
        embed.add_field(name="Приглашение", value=f"Код: `{invite.invite.code}` | Канал: {invite.invite.channel.mention}", inline=False)
        embed.add_field(name="Пригласил", value=invite.user.mention if invite.user else "Неизвестно", inline=True)
    else:
        embed.add_field(name="Приглашение", value="Неизвестно", inline=False)
    await send_log(embed, LOG_INVITE_CHANNEL_ID, member.guild)
    
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
    embed = base_embed("🔸 Участник покинул сервер", COLOR_INFO)
    embed.add_field(name="Пользователь", value=member.mention, inline=True)
    await send_log(embed, LOG_INVITE_CHANNEL_ID, member.guild)

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
            
            dm_embed = base_embed("🔇 Вы получили мут", COLOR_ACCENT)
            dm_embed.add_field(name="Тип", value="Мут", inline=True)
            dm_embed.add_field(name="Время", value="3 часа", inline=True)
            dm_embed.add_field(name="Причина", value="Отправка ссылки на Discord-сервер", inline=False)
            dm_embed.add_field(name="Модератор", value=bot.user.mention, inline=True)
            await send_dm(message.author, dm_embed)
            
            log_embed = base_embed("🔇 Выдан мут за ссылку на Discord-сервер", COLOR_ACCENT)
            log_embed.add_field(name="Пользователь", value=message.author.mention, inline=True)
            log_embed.add_field(name="Модератор", value=bot.user.mention, inline=True)
            log_embed.add_field(name="Время", value="3 часа", inline=True)
            log_embed.add_field(name="Причина", value="Отправка ссылки на Discord-сервер", inline=False)
            await send_log(log_embed, LOG_ALL_CHANNEL_ID, message.guild)
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
            
            dm_embed = base_embed("🔇 Вы получили мут за спам", COLOR_ACCENT)
            dm_embed.add_field(name="Тип", value="Мут", inline=True)
            dm_embed.add_field(name="Время", value=mute_text, inline=True)
            dm_embed.add_field(name="Нарушение", value=f"{spam_count}/3", inline=True)
            dm_embed.add_field(name="Причина", value="Отправка одинаковых сообщений", inline=False)
            dm_embed.add_field(name="Модератор", value=bot.user.mention, inline=True)
            await send_dm(message.author, dm_embed)
            
            log_embed = base_embed("🔇 Выдан мут за спам", COLOR_ACCENT)
            log_embed.add_field(name="Пользователь", value=message.author.mention, inline=True)
            log_embed.add_field(name="Время", value=mute_text, inline=True)
            log_embed.add_field(name="Нарушение", value=f"{spam_count}/3", inline=True)
            log_embed.add_field(name="Причина", value="Отправка одинаковых сообщений", inline=False)
            await send_log(log_embed, LOG_ALL_CHANNEL_ID, message.guild)
            if spam_count >= 3:
                try:
                    await message.author.ban(reason="3 нарушения спама")
                    dm_ban = base_embed("🔨 Вы были забанены", COLOR_ACCENT)
                    dm_ban.add_field(name="Тип", value="Бан", inline=True)
                    dm_ban.add_field(name="Причина", value="3 нарушения спама", inline=False)
                    dm_ban.add_field(name="Модератор", value=bot.user.mention, inline=True)
                    await send_dm(message.author, dm_ban)
                    
                    log_ban = base_embed("🔨 Выдан бан за спам", COLOR_ACCENT)
                    log_ban.add_field(name="Пользователь", value=message.author.mention, inline=True)
                    log_ban.add_field(name="Причина", value="3 нарушения спама", inline=False)
                    await send_log(log_ban, LOG_ALL_CHANNEL_ID, message.guild)
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
    embed = base_embed("✏️ Сообщение отредактировано", COLOR_INFO)
    embed.add_field(name="Пользователь", value=before.author.mention, inline=True)
    embed.add_field(name="Канал", value=before.channel.mention, inline=True)
    embed.add_field(name="До", value=before.content[:100] + "..." if len(before.content) > 100 else before.content, inline=False)
    embed.add_field(name="После", value=after.content[:100] + "..." if len(after.content) > 100 else after.content, inline=False)
    await send_log(embed, LOG_CHAT_CHANNEL_ID, before.guild)

@bot.event
async def on_message_delete(message):
    if message.author.bot or not message.guild:
        return
    if not is_target_guild(message.guild):
        return
    embed = base_embed("🗑️ Сообщение удалено", COLOR_INFO)
    embed.add_field(name="Пользователь", value=message.author.mention, inline=True)
    embed.add_field(name="Канал", value=message.channel.mention, inline=True)
    embed.add_field(name="Содержимое", value=message.content[:100] + "..." if len(message.content) > 100 else message.content, inline=False)
    await send_log(embed, LOG_CHAT_CHANNEL_ID, message.guild)

@bot.event
async def on_member_update(before, after):
    if not is_target_guild(before.guild):
        return
    
    if before.nick != after.nick:
        embed = base_embed("📛 Никнейм изменён", COLOR_INFO)
        embed.add_field(name="Пользователь", value=after.mention, inline=True)
        embed.add_field(name="Старый ник", value=before.nick or before.name, inline=True)
        embed.add_field(name="Новый ник", value=after.nick or after.name, inline=True)
        await send_log(embed, LOG_CHAT_CHANNEL_ID, before.guild)
    
    before_roles = set(before.roles)
    after_roles = set(after.roles)
    
    added_roles = after_roles - before_roles
    removed_roles = before_roles - after_roles
    
    for role in added_roles:
        actor = await get_audit_log_actor(before.guild, discord.AuditLogAction.member_role_update, before)
        embed = base_embed("✅ Выдана роль", COLOR_LIGHT)
        embed.add_field(name="Пользователь", value=after.mention, inline=True)
        embed.add_field(name="Роль", value=role.mention, inline=True)
        embed.add_field(name="Модератор", value=actor.mention if actor else "Неизвестно", inline=True)
        await send_log(embed, LOG_ALL_CHANNEL_ID, before.guild)
    
    for role in removed_roles:
        actor = await get_audit_log_actor(before.guild, discord.AuditLogAction.member_role_update, before)
        embed = base_embed("❌ Снята роль", COLOR_ACCENT)
        embed.add_field(name="Пользователь", value=after.mention, inline=True)
        embed.add_field(name="Роль", value=role.mention, inline=True)
        embed.add_field(name="Модератор", value=actor.mention if actor else "Неизвестно", inline=True)
        await send_log(embed, LOG_ALL_CHANNEL_ID, before.guild)

@bot.event
async def on_guild_channel_create(channel):
    if not is_target_guild(channel.guild):
        return
    actor = await get_audit_log_actor(channel.guild, discord.AuditLogAction.channel_create, channel)
    embed = base_embed("📢 Канал создан", COLOR_LIGHT)
    embed.add_field(name="Модератор", value=actor.mention if actor else "Неизвестно", inline=True)
    embed.add_field(name="Канал", value=channel.mention, inline=True)
    embed.add_field(name="Тип", value=str(channel.type).split('.')[-1], inline=True)
    await send_log(embed, LOG_ALL_CHANNEL_ID, channel.guild)

@bot.event
async def on_guild_channel_delete(channel):
    if not is_target_guild(channel.guild):
        return
    actor = await get_audit_log_actor(channel.guild, discord.AuditLogAction.channel_delete, channel)
    embed = base_embed("🗑️ Канал удалён", COLOR_ACCENT)
    embed.add_field(name="Модератор", value=actor.mention if actor else "Неизвестно", inline=True)
    embed.add_field(name="Канал", value=channel.name, inline=True)
    embed.add_field(name="Тип", value=str(channel.type).split('.')[-1], inline=True)
    await send_log(embed, LOG_ALL_CHANNEL_ID, channel.guild)

@bot.event
async def on_guild_channel_update(before, after):
    if not is_target_guild(before.guild):
        return
    if before.name != after.name:
        actor = await get_audit_log_actor(before.guild, discord.AuditLogAction.channel_update, after)
        embed = base_embed("🔄 Канал переименован", COLOR_INFO)
        embed.add_field(name="Модератор", value=actor.mention if actor else "Неизвестно", inline=True)
        embed.add_field(name="Старый канал", value=before.name, inline=True)
        embed.add_field(name="Новый канал", value=after.name, inline=True)
        await send_log(embed, LOG_ALL_CHANNEL_ID, before.guild)

@bot.event
async def on_guild_role_create(role):
    if not is_target_guild(role.guild):
        return
    actor = await get_audit_log_actor(role.guild, discord.AuditLogAction.role_create, role)
    embed = base_embed("🆕 Роль создана", COLOR_LIGHT)
    embed.add_field(name="Модератор", value=actor.mention if actor else "Неизвестно", inline=True)
    embed.add_field(name="Роль", value=role.mention, inline=True)
    embed.add_field(name="Цвет", value=str(role.color), inline=True)
    await send_log(embed, LOG_ALL_CHANNEL_ID, role.guild)

@bot.event
async def on_guild_role_delete(role):
    if not is_target_guild(role.guild):
        return
    actor = await get_audit_log_actor(role.guild, discord.AuditLogAction.role_delete, role)
    embed = base_embed("🗑️ Роль удалена", COLOR_ACCENT)
    embed.add_field(name="Модератор", value=actor.mention if actor else "Неизвестно", inline=True)
    embed.add_field(name="Роль", value=role.name, inline=True)
    await send_log(embed, LOG_ALL_CHANNEL_ID, role.guild)

@bot.event
async def on_guild_role_update(before, after):
    if not is_target_guild(before.guild):
        return
    actor = await get_audit_log_actor(before.guild, discord.AuditLogAction.role_update, after)
    if before.name != after.name:
        embed = base_embed("🔄 Роль переименована", COLOR_INFO)
        embed.add_field(name="Модератор", value=actor.mention if actor else "Неизвестно", inline=True)
        embed.add_field(name="Старая роль", value=before.name, inline=True)
        embed.add_field(name="Новая роль", value=after.name, inline=True)
        await send_log(embed, LOG_ALL_CHANNEL_ID, before.guild)
    if before.color != after.color:
        embed = base_embed("🎨 Цвет роли изменён", COLOR_INFO)
        embed.add_field(name="Модератор", value=actor.mention if actor else "Неизвестно", inline=True)
        embed.add_field(name="Роль", value=after.name, inline=True)
        embed.add_field(name="Старый цвет", value=str(before.color), inline=True)
        embed.add_field(name="Новый цвет", value=str(after.color), inline=True)
        await send_log(embed, LOG_ALL_CHANNEL_ID, before.guild)

# ==================== СИСТЕМА ЖАЛОБ ====================

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
        tickets_data = load_tickets()
        
        if not isinstance(tickets_data, dict):
            tickets_data = {'counter': 0, 'tickets': []}
        if 'counter' not in tickets_data:
            tickets_data['counter'] = 0
        if 'tickets' not in tickets_data or not isinstance(tickets_data['tickets'], list):
            tickets_data['tickets'] = []
        
        tickets_data['counter'] += 1
        ticket_number = get_ticket_number(tickets_data['counter'])
        
        ticket_data = {
            'id': ticket_number,
            'author_id': interaction.user.id,
            'author_name': str(interaction.user),
            'description': self.description.value,
            'user_name': self.user_name.value,
            'message_link': self.message_link.value if self.message_link.value else "Не указано",
            'status': 'open',
            'created_at': datetime.now(timezone.utc).timestamp(),
            'message_id': None
        }
        tickets_data['tickets'].append(ticket_data)
        save_tickets(tickets_data)
        
        embed = discord.Embed(
            title=f"📋 Жалоба {ticket_number}",
            color=COLOR_VIOLET
        )
        embed.add_field(name="👤 Подал", value=interaction.user.mention, inline=True)
        embed.add_field(name="📌 Статус", value="🟡 Рассматривается", inline=True)
        embed.add_field(name="📝 Описание", value=self.description.value[:1024], inline=False)
        embed.add_field(name="👤 Имя пользователя", value=self.user_name.value, inline=True)
        embed.add_field(name="🔗 Ссылка", value=self.message_link.value if self.message_link.value else "Не указано", inline=True)
        
        view = discord.ui.View(timeout=None)
        view.add_item(VerdictButton(ticket_number))
        
        channel = bot.get_channel(TICKET_CHANNEL_ID)
        if channel:
            role_mention = f"<@&{TICKET_MODERATOR_ROLE_ID}> <@&{ADMIN_ROLE_ID}>"
            message = await channel.send(content=role_mention, embed=embed, view=view)
            for ticket in tickets_data['tickets']:
                if ticket['id'] == ticket_number:
                    ticket['message_id'] = message.id
                    break
            save_tickets(tickets_data)
        
        await interaction.response.send_message("✅ Жалоба отправлена", ephemeral=True)

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
        tickets_data = load_tickets()
        
        if not isinstance(tickets_data, dict):
            tickets_data = {'counter': 0, 'tickets': []}
        if 'tickets' not in tickets_data or not isinstance(tickets_data['tickets'], list):
            tickets_data['tickets'] = []
        
        message_id = None
        for ticket in tickets_data['tickets']:
            if ticket['id'] == self.ticket_number:
                ticket['status'] = 'closed'
                message_id = ticket.get('message_id')
                break
        save_tickets(tickets_data)
        
        if message_id:
            channel = bot.get_channel(TICKET_CHANNEL_ID)
            if channel:
                try:
                    message = await channel.fetch_message(message_id)
                    if message:
                        old_embed = message.embeds[0] if message.embeds else None
                        if old_embed:
                            new_embed = discord.Embed(
                                title=old_embed.title,
                                color=COLOR_LIGHT
                            )
                            for field in old_embed.fields:
                                if field.name == "📌 Статус":
                                    new_embed.add_field(name=field.name, value="🟢 Рассмотрена", inline=field.inline)
                                else:
                                    new_embed.add_field(name=field.name, value=field.value, inline=field.inline)
                            
                            await message.edit(embed=new_embed, view=None)
                except:
                    pass
        
        log_embed = discord.Embed(
            title=f"⚖️ Вердикт по жалобе {self.ticket_number}",
            color=COLOR_ACCENT
        )
        log_embed.add_field(name="Модератор", value=interaction.user.mention, inline=True)
        log_embed.add_field(name="👤 Подал жалобу", value=f"<@{self.ticket_author}>", inline=True)
        log_embed.add_field(name="📝 Вердикт", value=self.verdict.value, inline=False)
        await send_log(log_embed, LOG_ALL_CHANNEL_ID, interaction.guild)
        
        await interaction.response.send_message("✅ Вердикт вынесен!", ephemeral=True)
        
        if self.ticket_author:
            try:
                user = await bot.fetch_user(self.ticket_author)
                user_dm_embed = discord.Embed(
                    title=f"Решение по вашей жалобе {self.ticket_number}",
                    description=self.verdict.value,
                    color=COLOR_ACCENT
                )
                await send_dm(user, user_dm_embed)
            except:
                pass

class VerdictButton(discord.ui.Button):
    def __init__(self, ticket_number):
        super().__init__(
            label="⚖️ Вынести вердикт",
            style=discord.ButtonStyle.primary,
            custom_id=f"verdict_{ticket_number}"
        )
        self.ticket_number = ticket_number

    async def callback(self, interaction: discord.Interaction):
        if not is_admin(interaction.user):
            await interaction.response.send_message("❌ У вас нет прав для вынесения вердикта!", ephemeral=True)
            return
        
        tickets_data = load_tickets()
        
        if not isinstance(tickets_data, dict):
            tickets_data = {'counter': 0, 'tickets': []}
        if 'tickets' not in tickets_data or not isinstance(tickets_data['tickets'], list):
            tickets_data['tickets'] = []
        
        ticket_data = None
        ticket_author = None
        for ticket in tickets_data['tickets']:
            if ticket['id'] == self.ticket_number:
                ticket_data = ticket
                ticket_author = ticket['author_id']
                break
        
        if not ticket_data:
            await interaction.response.send_message("❌ Жалоба не найдена!", ephemeral=True)
            return
        
        if ticket_data['status'] == 'closed':
            await interaction.response.send_message("❌ Эта жалоба уже закрыта!", ephemeral=True)
            return
        
        modal = VerdictModal(self.ticket_number, ticket_data, interaction.user, ticket_author)
        await interaction.response.send_modal(modal)

class ComplaintButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="⚠️ Подать жалобу",
            style=discord.ButtonStyle.danger,
            custom_id="complaint_button"
        )

    async def callback(self, interaction: discord.Interaction):
        modal = TicketModal()
        await interaction.response.send_modal(modal)

@bot.command(name="formjb")
async def formjb(ctx):
    if not is_target_guild(ctx.guild):
        await ctx.send("❌ Эта команда доступна только на целевом сервере!")
        return
    
    embed = discord.Embed(
        title="⚠️ Подача жалобы на участника",
        description="Если действия пользователя нарушают правила канала, вы можете сообщить об этом администрации.\n\n**Как это работает:** Нажмите на кнопку ниже. В открывшемся окне кратко опишите суть нарушения и прикрепите доказательства (ссылку на сообщение).\n\n⏳ Все обращения рассматриваются вручную в порядке очереди.",
        color=COLOR_VIOLET
    )
    
    view = discord.ui.View(timeout=None)
    view.add_item(ComplaintButton())
    
    await ctx.send(embed=embed, view=view)
    await ctx.message.delete()

# ==================== СИСТЕМА ТИКЕТОВ ====================

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
        tikets_data = load_tikets()
        
        if not isinstance(tikets_data, dict):
            tikets_data = {'counter': 0, 'tikets': []}
        if 'counter' not in tikets_data:
            tikets_data['counter'] = 0
        if 'tikets' not in tikets_data or not isinstance(tikets_data['tikets'], list):
            tikets_data['tikets'] = []
        
        tikets_data['counter'] += 1
        tiket_number = get_tiket_number(tikets_data['counter'])
        
        tiket_data = {
            'id': tiket_number,
            'author_id': interaction.user.id,
            'author_name': str(interaction.user),
            'type': self.tiket_type,
            'description': self.description.value,
            'status': 'open',
            'created_at': datetime.now(timezone.utc).timestamp(),
            'message_id': None
        }
        tikets_data['tikets'].append(tiket_data)
        save_tikets(tikets_data)
        
        embed = discord.Embed(
            title=f"🎫 Тикет {tiket_number}",
            color=COLOR_AZURE
        )
        embed.add_field(name="👤 Автор", value=interaction.user.mention, inline=True)
        embed.add_field(name="📌 Тип", value=self.tiket_type, inline=True)
        embed.add_field(name="📌 Статус", value="🟡 Открыт", inline=True)
        embed.add_field(name="📝 Описание", value=self.description.value[:1024], inline=False)
        
        view = discord.ui.View(timeout=None)
        view.add_item(TiketCloseButton(tiket_number))
        
        channel = bot.get_channel(TIKET_CHANNEL_ID)
        if channel:
            role_mention = f"<@&{TIKET_PING_ROLE_ID}>"
            message = await channel.send(content=role_mention, embed=embed, view=view)
            for tiket in tikets_data['tikets']:
                if tiket['id'] == tiket_number:
                    tiket['message_id'] = message.id
                    break
            save_tikets(tikets_data)
        
        await interaction.response.send_message(f"✅ Тикет {tiket_number} создан!", ephemeral=True)

class TiketVerdictModal(discord.ui.Modal):
    def __init__(self, tiket_number, tiket_author):
        super().__init__(title=f"⚖️ Закрытие тикета {tiket_number}")
        self.tiket_number = tiket_number
        self.tiket_author = tiket_author
        
        self.verdict = discord.ui.TextInput(
            label="Решение",
            placeholder="Введите решение по тикету",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=1000
        )
        self.add_item(self.verdict)

    async def on_submit(self, interaction: discord.Interaction):
        tikets_data = load_tikets()
        
        if not isinstance(tikets_data, dict):
            tikets_data = {'counter': 0, 'tikets': []}
        if 'tikets' not in tikets_data or not isinstance(tikets_data['tikets'], list):
            tikets_data['tikets'] = []
        
        message_id = None
        for tiket in tikets_data['tikets']:
            if tiket['id'] == self.tiket_number:
                tiket['status'] = 'closed'
                message_id = tiket.get('message_id')
                break
        save_tikets(tikets_data)
        
        if message_id:
            channel = bot.get_channel(TIKET_CHANNEL_ID)
            if channel:
                try:
                    message = await channel.fetch_message(message_id)
                    if message:
                        old_embed = message.embeds[0] if message.embeds else None
                        if old_embed:
                            new_embed = discord.Embed(
                                title=old_embed.title,
                                color=COLOR_LIGHT
                            )
                            for field in old_embed.fields:
                                if field.name == "📌 Статус":
                                    new_embed.add_field(name=field.name, value="🟢 Закрыт", inline=field.inline)
                                else:
                                    new_embed.add_field(name=field.name, value=field.value, inline=field.inline)
                            new_embed.add_field(name="⚖️ Решение", value=self.verdict.value[:1024], inline=False)
                            await message.edit(embed=new_embed, view=None)
                except:
                    pass
        
        log_embed = discord.Embed(
            title=f"⚖️ Закрытие тикета {self.tiket_number}",
            color=COLOR_ACCENT
        )
        log_embed.add_field(name="Модератор", value=interaction.user.mention, inline=True)
        log_embed.add_field(name="👤 Автор тикета", value=f"<@{self.tiket_author}>", inline=True)
        log_embed.add_field(name="📝 Решение", value=self.verdict.value, inline=False)
        await send_log(log_embed, LOG_ALL_CHANNEL_ID, interaction.guild)
        
        await interaction.response.send_message("✅ Тикет закрыт!", ephemeral=True)
        
        if self.tiket_author:
            try:
                user = await bot.fetch_user(self.tiket_author)
                user_dm_embed = discord.Embed(
                    title=f"Решение по вашему тикету {self.tiket_number}",
                    description=self.verdict.value,
                    color=COLOR_AZURE
                )
                await send_dm(user, user_dm_embed)
            except:
                pass

class TiketCloseButton(discord.ui.Button):
    def __init__(self, tiket_number):
        super().__init__(
            label="⚖️ Закрыть тикет",
            style=discord.ButtonStyle.primary,
            custom_id=f"tiket_close_{tiket_number}"
        )
        self.tiket_number = tiket_number

    async def callback(self, interaction: discord.Interaction):
        if not is_admin(interaction.user):
            await interaction.response.send_message("❌ У вас нет прав для закрытия тикета!", ephemeral=True)
            return
        
        tikets_data = load_tikets()
        
        if not isinstance(tikets_data, dict):
            tikets_data = {'counter': 0, 'tikets': []}
        if 'tikets' not in tikets_data or not isinstance(tikets_data['tikets'], list):
            tikets_data['tikets'] = []
        
        tiket_data = None
        tiket_author = None
        for tiket in tikets_data['tikets']:
            if tiket['id'] == self.tiket_number:
                tiket_data = tiket
                tiket_author = tiket['author_id']
                break
        
        if not tiket_data:
            await interaction.response.send_message("❌ Тикет не найден!", ephemeral=True)
            return
        
        if tiket_data['status'] == 'closed':
            await interaction.response.send_message("❌ Этот тикет уже закрыт!", ephemeral=True)
            return
        
        modal = TiketVerdictModal(self.tiket_number, tiket_author)
        await interaction.response.send_modal(modal)

class TiketQuestionButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Вопрос",
            emoji="❓",
            style=discord.ButtonStyle.primary,
            custom_id="tiket_question_button"
        )

    async def callback(self, interaction: discord.Interaction):
        modal = TiketModal("Вопрос")
        await interaction.response.send_modal(modal)

class TiketBugButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Баг",
            emoji="❗",
            style=discord.ButtonStyle.danger,
            custom_id="tiket_bug_button"
        )

    async def callback(self, interaction: discord.Interaction):
        modal = TiketModal("Баг")
        await interaction.response.send_modal(modal)

class TiketSuggestionButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Предложение",
            emoji="📋",
            style=discord.ButtonStyle.success,
            custom_id="tiket_suggestion_button"
        )

    async def callback(self, interaction: discord.Interaction):
        modal = TiketModal("Предложение")
        await interaction.response.send_modal(modal)

@bot.command(name="formtik")
async def formtik(ctx):
    if not is_target_guild(ctx.guild):
        await ctx.send("❌ Эта команда доступна только на целевом сервере!")
        return
    
    if not is_admin(ctx.author):
        await ctx.send("❌ У вас нет прав для использования этой команды!")
        return
    
    embed = discord.Embed(
        title="🎫 Создание тикета для обращения или сообщения об баге",
        description="Если у вас есть вопросы, предложения, требуется помощь или вы обнаружили баг - вы можете создать тикет.\n\n**Как это работает:**\nНажмите на кнопку ниже, чтобы открыть тикет. В открывшемся окне опишите суть (вопроса/бага/предложения) по форме.\n\n⏳ Все тикеты рассматриваются в порядке очереди.",
        color=COLOR_AZURE
    )
    
    view = discord.ui.View(timeout=None)
    view.add_item(TiketQuestionButton())
    view.add_item(TiketBugButton())
    view.add_item(TiketSuggestionButton())
    
    await ctx.send(embed=embed, view=view)
    await ctx.message.delete()

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
        await interaction.response.send_message("❌ Эта команда доступна только на целевом сервере!", ephemeral=True)
        return
    
    if not is_mod(interaction.user):
        await interaction.response.send_message("❌ У вас нет прав для использования этой команды!", ephemeral=True)
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
    
    await interaction.response.send_message("✅ Сообщение создаётся...", ephemeral=True)
    
    await channel.send(embed=embed, view=view)
    
    log_embed = base_embed("📋 Создано назначение ролей", COLOR_INFO)
    log_embed.add_field(name="Модератор", value=interaction.user.mention, inline=True)
    log_embed.add_field(name="Канал", value=channel.mention, inline=True)
    log_embed.add_field(name="Заголовок", value=title, inline=True)
    log_embed.add_field(name="Количество ролей", value=str(len(roles)), inline=True)
    roles_text = "\n".join([f"• {role.name}" for role in roles])
    log_embed.add_field(name="Роли", value=roles_text, inline=False)
    await send_log(log_embed, LOG_ALL_CHANNEL_ID, interaction.guild)
    
    await interaction.edit_original_response(content="✅ Сообщение с назначением ролей успешно создано!")

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
            await interaction.response.send_message("❌ Эта функция доступна только на целевом сервере!", ephemeral=True)
            return
        
        if self.role in interaction.user.roles:
            await interaction.user.remove_roles(self.role, reason="Снятие роли через кнопку")
            embed = discord.Embed(
                title="❌ Роль снята",
                description=f"С вас снята роль {self.role.mention}",
                color=COLOR_ACCENT
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            if self.role >= interaction.guild.me.top_role:
                await interaction.response.send_message("❌ У меня нет прав для выдачи этой роли!", ephemeral=True)
                return
            await interaction.user.add_roles(self.role, reason="Выдача роли через кнопку")
            embed = discord.Embed(
                title="✅ Роль выдана",
                description=f"Вам выдана роль {self.role.mention}",
                color=COLOR_LIGHT
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="lockdown", description="Активировать режим полной блокировки (Purple)")
async def lockdown(interaction: discord.Interaction):
    if not is_target_guild(interaction.guild):
        await interaction.response.send_message("❌ Эта команда доступна только на целевом сервере!", ephemeral=True)
        return
    if not is_mod(interaction.user):
        await interaction.response.send_message("❌ У вас нет прав для использования этой команды!", ephemeral=True)
        return
    status = get_raid_status(interaction.guild_id)
    if status['status'] == ANTI_RAID_RED:
        await interaction.response.send_message("⚠️ Режим блокировки уже активен!", ephemeral=True)
        return
    status['manual_lockdown'] = True
    await set_raid_status(interaction.guild, ANTI_RAID_RED, status)
    embed = base_embed("🟣 Режим полной блокировки активирован", COLOR_ACCENT)
    embed.add_field(name="Модератор", value=interaction.user.mention, inline=True)
    embed.add_field(name="Длительность", value=f"{RED_DURATION // 60} минут", inline=True)
    embed.add_field(name="Статус", value="Purple — полная блокировка", inline=False)
    embed.add_field(name="Меры", value="Каналы заблокированы, инвайты удалены, slowmode включён", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="unlockdown", description="Деактивировать режим полной блокировки")
async def unlockdown(interaction: discord.Interaction):
    if not is_target_guild(interaction.guild):
        await interaction.response.send_message("❌ Эта команда доступна только на целевом сервере!", ephemeral=True)
        return
    if not is_mod(interaction.user):
        await interaction.response.send_message("❌ У вас нет прав для использования этой команды!", ephemeral=True)
        return
    status = get_raid_status(interaction.guild_id)
    if status['status'] != ANTI_RAID_RED:
        await interaction.response.send_message("⚠️ Режим блокировки не активен!", ephemeral=True)
        return
    await set_raid_status(interaction.guild, ANTI_RAID_GREEN, status)
    embed = base_embed("🟦 Режим блокировки деактивирован", COLOR_LIGHT)
    embed.add_field(name="Модератор", value=interaction.user.mention, inline=True)
    embed.add_field(name="Статус", value="Blue — нормальный режим", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="raidstatus", description="Показать текущий статус антирейда")
async def raidstatus(interaction: discord.Interaction):
    if not is_target_guild(interaction.guild):
        await interaction.response.send_message("❌ Эта команда доступна только на целевом сервере!", ephemeral=True)
        return
    if not is_mod(interaction.user):
        await interaction.response.send_message("❌ У вас нет прав для использования этой команды!", ephemeral=True)
        return
    status = get_raid_status(interaction.guild_id)
    tracker = prune_tracker(interaction.guild_id)
    views = {
        ANTI_RAID_GREEN: ("🟦 Blue", COLOR_LIGHT, "Нормальный режим"),
        ANTI_RAID_YELLOW: ("🔷 Indigo", COLOR_INFO, "Повышенная готовность"),
        ANTI_RAID_RED: ("🟣 Purple", COLOR_ACCENT, "Полная блокировка")
    }
    title, color, description = views[status['status']]
    embed = base_embed(f"Антирейд: {title}", color)
    embed.add_field(name="Режим", value=description, inline=True)
    embed.add_field(name=f"Join'ов за {RAID_JOIN_TIMEFRAME} сек", value=str(len(tracker)), inline=True)
    embed.add_field(name="Пороги", value=f"Indigo: {RAID_JOIN_THRESHOLD} | Purple: {RAID_RED_THRESHOLD}", inline=True)
    if status['status'] == ANTI_RAID_RED and status['red_until']:
        embed.add_field(name="Блокировка до", value=discord.utils.format_dt(datetime.fromtimestamp(status['red_until'], tz=timezone.utc), 'f'), inline=False)
    if status['manual_lockdown']:
        embed.add_field(name="Режим", value="Активирован вручную", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

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
        await interaction.response.send_message("❌ Эта команда доступна только на целевом сервере!", ephemeral=True)
        return
    if not is_admin(interaction.user):
        await interaction.response.send_message("❌ У вас нет прав для использования этой команды!", ephemeral=True)
        return
    embed = discord.Embed(title=title, description=text, color=discord.Color.blue())
    if image:
        embed.set_image(url=image.url)
    try:
        await channel.send(content=role.mention if role else None, embed=embed)
        embed_success = discord.Embed(title="✅ Сообщение отправлено", color=COLOR_LIGHT)
        embed_success.add_field(name="Канал", value=channel.mention, inline=True)
        embed_success.add_field(name="Статус", value="Успешно", inline=True)
        if role:
            embed_success.add_field(name="Тег", value=role.mention, inline=True)
        await interaction.response.send_message(embed=embed_success, ephemeral=True)
    except:
        await interaction.response.send_message("❌ Ошибка при отправке сообщения!", ephemeral=True)

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
        await interaction.response.send_message("❌ Эта команда доступна только на целевом сервере!", ephemeral=True)
        return
    if not is_ticket_mod(interaction.user):
        await interaction.response.send_message("❌ У вас нет прав для использования этой команды!", ephemeral=True)
        return
    if user == interaction.user or user.bot:
        await interaction.response.send_message("❌ Нельзя замутить этого пользователя!", ephemeral=True)
        return
    
    if user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Нельзя замутить администратора!", ephemeral=True)
        return
    
    if user.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
        await interaction.response.send_message("❌ Вы не можете замутить пользователя с ролью выше или равной вашей!", ephemeral=True)
        return
    
    bot_member = interaction.guild.me
    if not bot_member.guild_permissions.moderate_members:
        await interaction.response.send_message("❌ У меня нет прав на выдачу таймаутов! Выдайте мне права 'Умеренные участники' (Moderate Members)!", ephemeral=True)
        return
    
    if user.top_role >= bot_member.top_role:
        await interaction.response.send_message("❌ Не могу замутить этого пользователя! Моя роль должна быть выше его роли!", ephemeral=True)
        return

    time_multipliers = {"seconds": 1, "minutes": 60, "hours": 3600, "days": 86400}
    duration_seconds = amount * time_multipliers[unit.value]
    if duration_seconds > 28 * 24 * 3600 or duration_seconds < 1:
        await interaction.response.send_message("❌ Некорректное время мута! Максимум 28 дней!", ephemeral=True)
        return
    try:
        until = discord.utils.utcnow() + timedelta(seconds=duration_seconds)
        await user.timeout(until, reason=reason)
        time_text = f"{amount} {unit.name.lower()}"
        embed = user_embed("🔇 Пользователь замучен", COLOR_ACCENT, user)
        embed.add_field(name="Пользователь", value=user.mention, inline=True)
        embed.add_field(name="Тип", value="Мут", inline=True)
        embed.add_field(name="Время", value=time_text, inline=True)
        embed.add_field(name="Модератор", value=interaction.user.mention, inline=True)
        embed.add_field(name="Причина", value=reason, inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
        dm_embed = base_embed("🔇 Вы получили мут", COLOR_ACCENT)
        dm_embed.add_field(name="Тип", value="Мут", inline=True)
        dm_embed.add_field(name="Время", value=time_text, inline=True)
        dm_embed.add_field(name="Причина", value=reason, inline=False)
        dm_embed.add_field(name="Модератор", value=interaction.user.mention, inline=True)
        await send_dm(user, dm_embed)
        
        log_embed = base_embed("🔇 Выдан мут", COLOR_ACCENT)
        log_embed.add_field(name="Пользователь", value=user.mention, inline=True)
        log_embed.add_field(name="Тип", value="Мут", inline=True)
        log_embed.add_field(name="Время", value=time_text, inline=True)
        log_embed.add_field(name="Модератор", value=interaction.user.mention, inline=True)
        log_embed.add_field(name="Причина", value=reason, inline=False)
        await send_log(log_embed, LOG_ALL_CHANNEL_ID, interaction.guild)
    except:
        await interaction.response.send_message("❌ Ошибка при выдаче мута!", ephemeral=True)

@bot.tree.command(name="unmute", description="Снять мут с участника")
@app_commands.describe(user="Участник, с которого нужно снять мут", reason="Причина снятия мута (обязательно)")
async def unmute(interaction: discord.Interaction, user: discord.Member, reason: str):
    if not is_target_guild(interaction.guild):
        await interaction.response.send_message("❌ Эта команда доступна только на целевом сервере!", ephemeral=True)
        return
    if not is_ticket_mod(interaction.user):
        await interaction.response.send_message("❌ У вас нет прав для использования этой команды!", ephemeral=True)
        return
    
    if user.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
        await interaction.response.send_message("❌ Вы не можете снять мут с пользователя с ролью выше или равной вашей!", ephemeral=True)
        return
    
    try:
        await user.timeout(None, reason=reason)
        embed = user_embed("🔊 Мут снят", COLOR_LIGHT, user)
        embed.add_field(name="Пользователь", value=user.mention, inline=True)
        embed.add_field(name="Модератор", value=interaction.user.mention, inline=True)
        embed.add_field(name="Причина", value=reason, inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        dm_embed = base_embed("🔊 С вас сняли мут", COLOR_LIGHT)
        dm_embed.add_field(name="Причина", value=reason, inline=False)
        dm_embed.add_field(name="Модератор", value=interaction.user.mention, inline=True)
        await send_dm(user, dm_embed)
        log_embed = base_embed("🔊 Мут снят", COLOR_LIGHT)
        log_embed.add_field(name="Пользователь", value=user.mention, inline=True)
        log_embed.add_field(name="Модератор", value=interaction.user.mention, inline=True)
        log_embed.add_field(name="Причина", value=reason, inline=False)
        await send_log(log_embed, LOG_ALL_CHANNEL_ID, interaction.guild)
    except:
        await interaction.response.send_message("❌ Ошибка при снятии мута!", ephemeral=True)

@bot.tree.command(name="kick", description="Выгнать участника с сервера")
@app_commands.describe(user="Участник, которого нужно выгнать", reason="Причина выгона (обязательно)")
async def kick(interaction: discord.Interaction, user: discord.Member, reason: str):
    if not is_target_guild(interaction.guild):
        await interaction.response.send_message("❌ Эта команда доступна только на целевом сервере!", ephemeral=True)
        return
    if not is_admin(interaction.user):
        await interaction.response.send_message("❌ У вас нет прав для использования этой команды!", ephemeral=True)
        return
    if user == interaction.user:
        await interaction.response.send_message("❌ Вы не можете выгнать себя!", ephemeral=True)
        return
    if user == interaction.guild.me:
        await interaction.response.send_message("❌ Вы не можете выгнать бота!", ephemeral=True)
        return
    if user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Нельзя выгнать администратора!", ephemeral=True)
        return
    if user.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
        await interaction.response.send_message("❌ Вы не можете выгнать пользователя с ролью выше или равной вашей!", ephemeral=True)
        return
    
    bot_member = interaction.guild.me
    if not bot_member.guild_permissions.kick_members:
        await interaction.response.send_message("❌ У меня нет прав на кик участников! Выдайте мне права 'Выгонять участников' (Kick Members)!", ephemeral=True)
        return
    
    if user.top_role >= bot_member.top_role:
        await interaction.response.send_message("❌ Не могу выгнать этого пользователя! Моя роль должна быть выше его роли!", ephemeral=True)
        return
    
    try:
        dm_embed = base_embed("👢 Вас выгнали с сервера", COLOR_ACCENT)
        dm_embed.add_field(name="Тип", value="Кик", inline=True)
        dm_embed.add_field(name="Причина", value=reason, inline=False)
        dm_embed.add_field(name="Модератор", value=interaction.user.mention, inline=True)
        await send_dm(user, dm_embed)
        
        await user.kick(reason=reason)
        
        embed = user_embed("👢 Пользователь выгнан", COLOR_ACCENT, user)
        embed.add_field(name="Пользователь", value=f"{user} ({user.mention})", inline=True)
        embed.add_field(name="Тип", value="Кик", inline=True)
        embed.add_field(name="Модератор", value=interaction.user.mention, inline=True)
        embed.add_field(name="Причина", value=reason, inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
        log_embed = base_embed("👢 Пользователь выгнан", COLOR_ACCENT)
        log_embed.add_field(name="Пользователь", value=f"{user} ({user.mention})", inline=True)
        log_embed.add_field(name="Тип", value="Кик", inline=True)
        log_embed.add_field(name="Модератор", value=interaction.user.mention, inline=True)
        log_embed.add_field(name="Причина", value=reason, inline=False)
        await send_log(log_embed, LOG_ALL_CHANNEL_ID, interaction.guild)
    except discord.Forbidden:
        await interaction.response.send_message("❌ Ошибка: недостаточно прав для выгона этого пользователя!", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Ошибка при выгоне: {str(e)}", ephemeral=True)

@bot.tree.command(name="ban", description="Забанить участника на сервере (вечный бан)")
@app_commands.describe(user="Участник, которого нужно забанить", reason="Причина бана (обязательно)", delete_message_days="Количество дней сообщений для удаления (0-7)")
async def ban(interaction: discord.Interaction, user: discord.Member, reason: str, delete_message_days: int = 0):
    if not is_target_guild(interaction.guild):
        await interaction.response.send_message("❌ Эта команда доступна только на целевом сервере!", ephemeral=True)
        return
    if not is_admin(interaction.user):
        await interaction.response.send_message("❌ У вас нет прав для использования этой команды!", ephemeral=True)
        return
    if user == interaction.user:
        await interaction.response.send_message("❌ Вы не можете забанить себя!", ephemeral=True)
        return
    if user == interaction.guild.me:
        await interaction.response.send_message("❌ Вы не можете забанить бота!", ephemeral=True)
        return
    if user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Нельзя забанить администратора!", ephemeral=True)
        return
    if user.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
        await interaction.response.send_message("❌ Вы не можете забанить пользователя с ролью выше или равной вашей!", ephemeral=True)
        return
    
    bot_member = interaction.guild.me
    if not bot_member.guild_permissions.ban_members:
        await interaction.response.send_message("❌ У меня нет прав на бан участников! Выдайте мне права 'Банить участников' (Ban Members)!", ephemeral=True)
        return
    
    if user.top_role >= bot_member.top_role:
        await interaction.response.send_message("❌ Не могу забанить этого пользователя! Моя роль должна быть выше его роли!", ephemeral=True)
        return
    
    if delete_message_days < 0 or delete_message_days > 7:
        await interaction.response.send_message("❌ Количество дней должно быть от 0 до 7!", ephemeral=True)
        return
    try:
        dm_embed = base_embed("🔨 Вы были забанены", COLOR_ACCENT)
        dm_embed.add_field(name="Тип", value="Бан", inline=True)
        dm_embed.add_field(name="Причина", value=reason, inline=False)
        dm_embed.add_field(name="Модератор", value=interaction.user.mention, inline=True)
        await send_dm(user, dm_embed)
        
        await user.ban(reason=reason, delete_message_days=delete_message_days)
        
        embed = user_embed("🔨 Пользователь забанен", COLOR_ACCENT, user)
        embed.add_field(name="Пользователь", value=f"{user} ({user.mention})", inline=True)
        embed.add_field(name="Тип", value="Бан", inline=True)
        embed.add_field(name="Модератор", value=interaction.user.mention, inline=True)
        embed.add_field(name="Удалено сообщений", value=f"{delete_message_days} дней", inline=True)
        embed.add_field(name="Причина", value=reason, inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
        log_embed = base_embed("🔨 Пользователь забанен", COLOR_ACCENT)
        log_embed.add_field(name="Пользователь", value=f"{user} ({user.mention})", inline=True)
        log_embed.add_field(name="Тип", value="Бан", inline=True)
        log_embed.add_field(name="Модератор", value=interaction.user.mention, inline=True)
        log_embed.add_field(name="Удалено сообщений", value=f"{delete_message_days} дней", inline=True)
        log_embed.add_field(name="Причина", value=reason, inline=False)
        await send_log(log_embed, LOG_ALL_CHANNEL_ID, interaction.guild)
    except discord.Forbidden:
        await interaction.response.send_message("❌ Ошибка: недостаточно прав для бана этого пользователя!", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Ошибка при бане: {str(e)}", ephemeral=True)

@bot.tree.command(name="unban", description="Разбанить участника на сервере")
@app_commands.describe(user_id="ID пользователя, которого нужно разбанить", reason="Причина разбана")
async def unban(interaction: discord.Interaction, user_id: str, reason: str = "Не указана"):
    if not is_target_guild(interaction.guild):
        await interaction.response.send_message("❌ Эта команда доступна только на целевом сервере!", ephemeral=True)
        return
    if not is_admin(interaction.user):
        await interaction.response.send_message("❌ У вас нет прав для использования этой команды!", ephemeral=True)
        return
    try:
        user = await bot.fetch_user(int(user_id))
        await interaction.guild.unban(user, reason=reason)
        embed = base_embed("✅ Пользователь разбанен", COLOR_LIGHT)
        embed.add_field(name="Пользователь", value=user.mention, inline=True)
        embed.add_field(name="Модератор", value=interaction.user.mention, inline=True)
        embed.add_field(name="Причина", value=reason, inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        dm_embed = base_embed("✅ Вас разбанили", COLOR_LIGHT)
        dm_embed.add_field(name="Причина", value=reason, inline=False)
        dm_embed.add_field(name="Модератор", value=interaction.user.mention, inline=True)
        await send_dm(user, dm_embed)
        log_embed = base_embed("✅ Пользователь разбанен", COLOR_LIGHT)
        log_embed.add_field(name="Пользователь", value=user.mention, inline=True)
        log_embed.add_field(name="Модератор", value=interaction.user.mention, inline=True)
        log_embed.add_field(name="Причина", value=reason, inline=False)
        await send_log(log_embed, LOG_ALL_CHANNEL_ID, interaction.guild)
    except:
        await interaction.response.send_message("❌ Ошибка при разбане!", ephemeral=True)

@bot.tree.command(name="tempban", description="Забанить участника на определённое время")
@app_commands.describe(user="Участник, которого нужно забанить", days="Количество дней бана", reason="Причина бана (обязательно)")
async def tempban(interaction: discord.Interaction, user: discord.Member, days: int, reason: str):
    if not is_target_guild(interaction.guild):
        await interaction.response.send_message("❌ Эта команда доступна только на целевом сервере!", ephemeral=True)
        return
    if not is_ticket_mod(interaction.user):
        await interaction.response.send_message("❌ У вас нет прав для использования этой команды!", ephemeral=True)
        return
    if user == interaction.user:
        await interaction.response.send_message("❌ Вы не можете забанить себя!", ephemeral=True)
        return
    if user == interaction.guild.me:
        await interaction.response.send_message("❌ Вы не можете забанить бота!", ephemeral=True)
        return
    if user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Нельзя забанить администратора!", ephemeral=True)
        return
    if user.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
        await interaction.response.send_message("❌ Вы не можете забанить пользователя с ролью выше или равной вашей!", ephemeral=True)
        return
    
    bot_member = interaction.guild.me
    if not bot_member.guild_permissions.ban_members:
        await interaction.response.send_message("❌ У меня нет прав на бан участников! Выдайте мне права 'Банить участников' (Ban Members)!", ephemeral=True)
        return
    
    if user.top_role >= bot_member.top_role:
        await interaction.response.send_message("❌ Не могу забанить этого пользователя! Моя роль должна быть выше его роли!", ephemeral=True)
        return
    
    if days < 1:
        await interaction.response.send_message("❌ Количество дней должно быть больше 0!", ephemeral=True)
        return
    try:
        dm_embed = base_embed("🔨 Вы были забанены", COLOR_ACCENT)
        dm_embed.add_field(name="Тип", value="Временный бан", inline=True)
        dm_embed.add_field(name="Время", value=f"{days} дней", inline=True)
        dm_embed.add_field(name="Причина", value=reason, inline=False)
        dm_embed.add_field(name="Модератор", value=interaction.user.mention, inline=True)
        await send_dm(user, dm_embed)
        
        await user.ban(reason=reason)
        
        embed = user_embed("🔨 Пользователь забанен (временно)", COLOR_ACCENT, user)
        embed.add_field(name="Пользователь", value=f"{user} ({user.mention})", inline=True)
        embed.add_field(name="Тип", value="Временный бан", inline=True)
        embed.add_field(name="Время", value=f"{days} дней", inline=True)
        embed.add_field(name="Модератор", value=interaction.user.mention, inline=True)
        embed.add_field(name="Причина", value=reason, inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
        log_embed = base_embed("🔨 Временный бан", COLOR_ACCENT)
        log_embed.add_field(name="Пользователь", value=f"{user} ({user.mention})", inline=True)
        log_embed.add_field(name="Тип", value="Временный бан", inline=True)
        log_embed.add_field(name="Время", value=f"{days} дней", inline=True)
        log_embed.add_field(name="Модератор", value=interaction.user.mention, inline=True)
        log_embed.add_field(name="Причина", value=reason, inline=False)
        await send_log(log_embed, LOG_ALL_CHANNEL_ID, interaction.guild)
        async def unban_later():
            await asyncio.sleep(days * 24 * 3600)
            try:
                await interaction.guild.unban(user, reason="Автоматический разбан")
                log_unban = base_embed("✅ Автоматический разбан", COLOR_LIGHT)
                log_unban.add_field(name="Пользователь", value=user.mention, inline=True)
                log_unban.add_field(name="Причина", value="Истечение времени бана", inline=False)
                await send_log(log_unban, LOG_ALL_CHANNEL_ID, interaction.guild)
            except:
                pass
        bot.loop.create_task(unban_later())
    except discord.Forbidden:
        await interaction.response.send_message("❌ Ошибка: недостаточно прав для бана этого пользователя!", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Ошибка при выдаче временного бана: {str(e)}", ephemeral=True)

@bot.tree.command(name="warn", description="Выдать предупреждение участнику")
@app_commands.describe(user="Участник, которому нужно выдать предупреждение", reason="Причина предупреждения (обязательно)")
async def warn(interaction: discord.Interaction, user: discord.Member, reason: str):
    if not is_target_guild(interaction.guild):
        await interaction.response.send_message("❌ Эта команда доступна только на целевом сервере!", ephemeral=True)
        return
    if not is_ticket_mod(interaction.user):
        await interaction.response.send_message("❌ У вас нет прав для использования этой команды!", ephemeral=True)
        return
    if user == interaction.user or user.bot:
        await interaction.response.send_message("❌ Нельзя выдать предупреждение этому пользователю!", ephemeral=True)
        return
    if user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Нельзя выдать предупреждение администратору!", ephemeral=True)
        return
    if user.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
        await interaction.response.send_message("❌ Вы не можете выдать предупреждение пользователю с ролью выше или равной вашей!", ephemeral=True)
        return
    try:
        user_warns = get_user_warns(interaction.guild_id, user.id)
        if len(user_warns) >= MAX_WARNS:
            await interaction.response.send_message(f"❌ У {user.mention} уже максимальное количество предупреждений ({MAX_WARNS}/{MAX_WARNS})!", ephemeral=True)
            return
        user_warns.append({'reason': reason, 'moderator': interaction.user.id, 'timestamp': datetime.now(timezone.utc).timestamp()})
        save_user_warns(interaction.guild_id, user.id, user_warns)
        warn_count = len(user_warns)
        embed = user_embed("⚠️ Предупреждение выдано", COLOR_ACCENT, user)
        embed.add_field(name="Пользователь", value=user.mention, inline=True)
        embed.add_field(name="Тип", value="Варн", inline=True)
        embed.add_field(name="Всего предупреждений", value=f"{warn_count}/{MAX_WARNS}", inline=True)
        embed.add_field(name="Модератор", value=interaction.user.mention, inline=True)
        embed.add_field(name="Причина", value=reason, inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
        dm_embed = base_embed("⚠️ Вы получили предупреждение", COLOR_ACCENT)
        dm_embed.add_field(name="Тип", value="Варн", inline=True)
        dm_embed.add_field(name="Всего предупреждений", value=f"{warn_count}/{MAX_WARNS}", inline=True)
        dm_embed.add_field(name="Причина", value=reason, inline=False)
        dm_embed.add_field(name="Модератор", value=interaction.user.mention, inline=True)
        await send_dm(user, dm_embed)
        
        log_embed = base_embed("⚠️ Выдано предупреждение", COLOR_ACCENT)
        log_embed.add_field(name="Пользователь", value=user.mention, inline=True)
        log_embed.add_field(name="Тип", value="Варн", inline=True)
        log_embed.add_field(name="Всего предупреждений", value=f"{warn_count}/{MAX_WARNS}", inline=True)
        log_embed.add_field(name="Модератор", value=interaction.user.mention, inline=True)
        log_embed.add_field(name="Причина", value=reason, inline=False)
        await send_log(log_embed, LOG_ALL_CHANNEL_ID, interaction.guild)
        if warn_count >= MAX_WARNS:
            try:
                await user.timeout(discord.utils.utcnow() + timedelta(seconds=WARN_MUTE_DURATION), reason="Автоматический мут за 3 предупреждения")
                clear_user_warns(interaction.guild_id, user.id)
                dm_mute = base_embed("🔇 Вы получили автоматический мут", COLOR_ACCENT)
                dm_mute.add_field(name="Тип", value="Автоматический мут", inline=True)
                dm_mute.add_field(name="Время", value="12 часов", inline=True)
                dm_mute.add_field(name="Причина", value="Получено 3 предупреждения", inline=False)
                dm_mute.add_field(name="Модератор", value=interaction.user.mention, inline=True)
                await send_dm(user, dm_mute)
                
                log_mute = base_embed("🔇 Автоматический мут за 3 варна", COLOR_ACCENT)
                log_mute.add_field(name="Пользователь", value=user.mention, inline=True)
                log_mute.add_field(name="Тип", value="Автоматический мут", inline=True)
                log_mute.add_field(name="Время", value="12 часов", inline=True)
                log_mute.add_field(name="Причина", value="Получено 3 предупреждения", inline=False)
                await send_log(log_mute, LOG_ALL_CHANNEL_ID, interaction.guild)
            except:
                pass
    except:
        await interaction.response.send_message("❌ Ошибка при выдаче предупреждения!", ephemeral=True)

@bot.tree.command(name="unwarn", description="Снять одно предупреждение с участника")
@app_commands.describe(user="Участник, у которого нужно снять предупреждение", reason="Причина снятия предупреждения (обязательно)")
async def unwarn(interaction: discord.Interaction, user: discord.Member, reason: str):
    if not is_target_guild(interaction.guild):
        await interaction.response.send_message("❌ Эта команда доступна только на целевом сервере!", ephemeral=True)
        return
    if not is_ticket_mod(interaction.user):
        await interaction.response.send_message("❌ У вас нет прав для использования этой команды!", ephemeral=True)
        return
    if user.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
        await interaction.response.send_message("❌ Вы не можете снять предупреждение с пользователя с ролью выше или равной вашей!", ephemeral=True)
        return
    try:
        user_warns = get_user_warns(interaction.guild_id, user.id)
        if not user_warns:
            await interaction.response.send_message(f"❌ У {user.mention} нет предупреждений!", ephemeral=True)
            return
        removed_warn = user_warns.pop()
        save_user_warns(interaction.guild_id, user.id, user_warns)
        embed = user_embed("✅ Предупреждение снято", COLOR_LIGHT, user)
        embed.add_field(name="Пользователь", value=user.mention, inline=True)
        embed.add_field(name="Осталось предупреждений", value=f"{len(user_warns)}/{MAX_WARNS}", inline=True)
        embed.add_field(name="Модератор", value=interaction.user.mention, inline=True)
        embed.add_field(name="Снятое предупреждение", value=removed_warn['reason'], inline=False)
        embed.add_field(name="Причина снятия", value=reason, inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        dm_embed = base_embed("✅ С вас сняли предупреждение", COLOR_LIGHT)
        dm_embed.add_field(name="Осталось предупреждений", value=f"{len(user_warns)}/{MAX_WARNS}", inline=True)
        dm_embed.add_field(name="Причина снятия", value=reason, inline=False)
        dm_embed.add_field(name="Модератор", value=interaction.user.mention, inline=True)
        await send_dm(user, dm_embed)
        log_embed = base_embed("✅ Предупреждение снято", COLOR_LIGHT)
        log_embed.add_field(name="Пользователь", value=user.mention, inline=True)
        log_embed.add_field(name="Осталось предупреждений", value=f"{len(user_warns)}/{MAX_WARNS}", inline=True)
        log_embed.add_field(name="Модератор", value=interaction.user.mention, inline=True)
        log_embed.add_field(name="Снятое предупреждение", value=removed_warn['reason'], inline=False)
        log_embed.add_field(name="Причина снятия", value=reason, inline=False)
        await send_log(log_embed, LOG_ALL_CHANNEL_ID, interaction.guild)
    except:
        await interaction.response.send_message("❌ Ошибка при снятии предупреждения!", ephemeral=True)

@bot.tree.command(name="warns", description="Показать количество предупреждений пользователя")
@app_commands.describe(user="Пользователь, у которого нужно проверить предупреждения")
async def warns(interaction: discord.Interaction, user: discord.Member):
    if not is_target_guild(interaction.guild):
        await interaction.response.send_message("❌ Эта команда доступна только на целевом сервере!", ephemeral=True)
        return
    if not is_admin(interaction.user):
        await interaction.response.send_message("❌ У вас нет прав для использования этой команды!", ephemeral=True)
        return
    try:
        user_warns = get_user_warns(interaction.guild_id, user.id)
        warn_count = len(user_warns)
        embed = user_embed("📊 Предупреждения пользователя", COLOR_MAIN, user)
        embed.add_field(name="Пользователь", value=user.mention, inline=True)
        embed.add_field(name="Количество", value=f"{warn_count}/{MAX_WARNS}", inline=True)
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
            split_embed(embed, "Детали", warns_text)
        else:
            embed.add_field(name="Детали", value="Нет предупреждений", inline=False)
        await interaction.response.send_message(embed=embed)
    except:
        await interaction.response.send_message("❌ Ошибка при получении предупреждений!", ephemeral=True)

@bot.tree.command(name="clear", description="Очистить сообщения в канале")
@app_commands.describe(amount="Количество сообщений для удаления (1-100)", user="Удалить сообщения только от определённого пользователя")
async def clear(interaction: discord.Interaction, amount: int, user: discord.Member = None):
    if not is_target_guild(interaction.guild):
        await interaction.response.send_message("❌ Эта команда доступна только на целевом сервере!", ephemeral=True)
        return
    if not is_admin(interaction.user):
        await interaction.response.send_message("❌ У вас нет прав для использования этой команды!", ephemeral=True)
        return
    if amount < 1 or amount > 100:
        await interaction.response.send_message("❌ Количество сообщений должно быть от 1 до 100!", ephemeral=True)
        return
    try:
        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=amount, check=lambda m: m.author == user if user else True)
        log_embed = base_embed("🧹 Очистка канала", COLOR_MAIN)
        log_embed.add_field(name="Канал", value=interaction.channel.mention, inline=True)
        log_embed.add_field(name="Модератор", value=interaction.user.mention, inline=True)
        log_embed.add_field(name="Удалено", value=f"{len(deleted)} сообщений", inline=True)
        log_embed.add_field(name="Фильтр", value=user.mention if user else "Нет", inline=True)
        await send_log(log_embed, LOG_ALL_CHANNEL_ID, interaction.guild)
        await interaction.followup.send("✅ Сообщения удалены!", ephemeral=True)
    except:
        await interaction.followup.send("❌ Ошибка при очистке!", ephemeral=True)

if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_TOKEN")
    if not TOKEN:
        print("Коля пизда.")
    else:
        bot.run(TOKEN)