import discord
from discord.ext import commands
from datetime import datetime, timedelta, timezone
import json
import os
import re
import asyncio
from typing import List
from discord.ui import Button, View, Modal, TextInput

TOKEN = 'MTQ5MDQyMTU3OTU5Nzc0NjE4Ng.GDAk31.dXnGpCCjCtmShzWocLglhibjHDvJbt2KWab7D4'

intents = discord.Intents.all()

bot = commands.Bot(command_prefix='!', intents=intents)

WARNS_FILE = 'warns.json'
LOGS_FILE = 'logs.json'
VERIFY_FILE = 'verify.json'
SPAM_COUNT_FILE = 'spam_count.json'
COMMANDS_ACCESS_FILE = 'commands_access.json'
RAID_CONFIG_FILE = 'raid_config.json'
ROLE_PERMISSIONS_FILE = 'role_permissions.json'
CHANNEL_BACKUP_FILE = 'channel_backup.json'
TICKETS_FILE = 'tickets.json'
SUPPORT_CONFIG_FILE = 'support_config.json'
SUPPORT_ADMINS_FILE = 'support_admins.json'
VERIFY_ROLES_FILE = 'verify_roles.json'

if os.path.exists(WARNS_FILE):
    with open(WARNS_FILE, 'r', encoding='utf-8') as f:
        warns = json.load(f)
else:
    warns = {}

if os.path.exists(LOGS_FILE):
    with open(LOGS_FILE, 'r', encoding='utf-8') as f:
        logs_config = json.load(f)
else:
    logs_config = {}

if os.path.exists(VERIFY_FILE):
    with open(VERIFY_FILE, 'r', encoding='utf-8') as f:
        verify_config = json.load(f)
else:
    verify_config = {}

if os.path.exists(SPAM_COUNT_FILE):
    with open(SPAM_COUNT_FILE, 'r', encoding='utf-8') as f:
        spam_count = json.load(f)
else:
    spam_count = {}

if os.path.exists(COMMANDS_ACCESS_FILE):
    with open(COMMANDS_ACCESS_FILE, 'r', encoding='utf-8') as f:
        commands_access = json.load(f)
else:
    commands_access = {}

if os.path.exists(RAID_CONFIG_FILE):
    with open(RAID_CONFIG_FILE, 'r', encoding='utf-8') as f:
        raid_config = json.load(f)
else:
    raid_config = {}

if os.path.exists(ROLE_PERMISSIONS_FILE):
    with open(ROLE_PERMISSIONS_FILE, 'r', encoding='utf-8') as f:
        role_permissions = json.load(f)
else:
    role_permissions = {}

if os.path.exists(CHANNEL_BACKUP_FILE):
    with open(CHANNEL_BACKUP_FILE, 'r', encoding='utf-8') as f:
        channel_backup = json.load(f)
else:
    channel_backup = {}

if os.path.exists(TICKETS_FILE):
    with open(TICKETS_FILE, 'r', encoding='utf-8') as f:
        tickets_data = json.load(f)
else:
    tickets_data = {
        'ticket_counter': 0,
        'complaint_counter': 0,
        'tickets': {},
        'complaints': {}
    }

if os.path.exists(SUPPORT_CONFIG_FILE):
    with open(SUPPORT_CONFIG_FILE, 'r', encoding='utf-8') as f:
        support_config = json.load(f)
else:
    support_config = {}

if os.path.exists(SUPPORT_ADMINS_FILE):
    with open(SUPPORT_ADMINS_FILE, 'r', encoding='utf-8') as f:
        support_admins = json.load(f)
else:
    support_admins = {}

if os.path.exists(VERIFY_ROLES_FILE):
    with open(VERIFY_ROLES_FILE, 'r', encoding='utf-8') as f:
        verify_roles_data = json.load(f)
else:
    verify_roles_data = {}

message_history = {}
join_history = {}
raid_active = {}
raid_level = {}
lockdown_active = {}
suspicion_active = {}

def save_warns():
    with open(WARNS_FILE, 'w', encoding='utf-8') as f:
        json.dump(warns, f, indent=4, ensure_ascii=False)

def save_logs_config():
    with open(LOGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(logs_config, f, indent=4, ensure_ascii=False)

def save_verify_config():
    with open(VERIFY_FILE, 'w', encoding='utf-8') as f:
        json.dump(verify_config, f, indent=4, ensure_ascii=False)

def save_spam_count():
    with open(SPAM_COUNT_FILE, 'w', encoding='utf-8') as f:
        json.dump(spam_count, f, indent=4, ensure_ascii=False)

def save_commands_access():
    with open(COMMANDS_ACCESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(commands_access, f, indent=4, ensure_ascii=False)

def save_raid_config():
    with open(RAID_CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(raid_config, f, indent=4, ensure_ascii=False)

def save_role_permissions():
    with open(ROLE_PERMISSIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(role_permissions, f, indent=4, ensure_ascii=False)

def save_channel_backup():
    with open(CHANNEL_BACKUP_FILE, 'w', encoding='utf-8') as f:
        json.dump(channel_backup, f, indent=4, ensure_ascii=False)

def save_tickets():
    with open(TICKETS_FILE, 'w', encoding='utf-8') as f:
        json.dump(tickets_data, f, indent=4, ensure_ascii=False)

def save_support_config():
    with open(SUPPORT_CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(support_config, f, indent=4, ensure_ascii=False)

def save_support_admins():
    with open(SUPPORT_ADMINS_FILE, 'w', encoding='utf-8') as f:
        json.dump(support_admins, f, indent=4, ensure_ascii=False)

def save_verify_roles():
    with open(VERIFY_ROLES_FILE, 'w', encoding='utf-8') as f:
        json.dump(verify_roles_data, f, indent=4, ensure_ascii=False)

def format_ticket_number(num):
    return f"Т-{str(num // 100).zfill(2)}-{str(num % 100).zfill(2)}"

def format_complaint_number(num):
    return f"Ж-{str(num // 100).zfill(2)}-{str(num % 100).zfill(2)}"

async def send_log(guild_id, embed):
    if str(guild_id) in logs_config:
        channel_id = logs_config[str(guild_id)]
        channel = bot.get_channel(channel_id)
        if channel:
            await channel.send(embed=embed)

async def send_dm(user, title, reason, warn_count=None):
    try:
        embed = discord.Embed(
            title=title,
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        if warn_count is not None:
            embed.add_field(name='📊 Предупреждений', value=f'{warn_count}/3', inline=False)
        embed.add_field(name='📝 Причина', value=reason, inline=False)
        await user.send(embed=embed)
    except:
        pass

def has_command_access(user, command_name):
    if user.guild_permissions.administrator:
        return True
    
    guild_id_str = str(user.guild.id)
    if guild_id_str in commands_access:
        if 'all' in commands_access[guild_id_str]:
            if str(user.id) in commands_access[guild_id_str]['all'].get('users', []):
                return True
            for role in user.roles:
                if str(role.id) in commands_access[guild_id_str]['all'].get('roles', []):
                    return True
        
        if command_name in commands_access[guild_id_str]:
            access = commands_access[guild_id_str][command_name]
            if str(user.id) in access.get('users', []):
                return True
            for role in user.roles:
                if str(role.id) in access.get('roles', []):
                    return True
    return False

def can_target(user, target):
    if user.guild_permissions.administrator:
        return True
    
    if target.guild_permissions.administrator:
        return False
    
    if user.top_role <= target.top_role:
        return False
    
    return True

def can_mute_target(user, target):
    if user.guild_permissions.administrator:
        return True
    
    if target.guild_permissions.administrator:
        return False
    
    if target == user.guild.owner:
        return False
    
    if user.top_role <= target.top_role:
        return False
    
    return True

def can_manage_support(user, guild_id):
    if user.guild_permissions.administrator:
        return True
    
    guild_id_str = str(guild_id)
    if guild_id_str in support_admins:
        for role_id in support_admins[guild_id_str].get('roles', []):
            role = user.guild.get_role(int(role_id))
            if role and role in user.roles:
                return True
    return False

def is_night_time():
    current_hour = datetime.now().hour
    return current_hour >= 0 and current_hour < 6

def is_new_account(created_at):
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    account_age = datetime.now(timezone.utc) - created_at
    return account_age.days

def get_support_channel(guild):
    if str(guild.id) in support_config:
        channel_id = support_config[str(guild.id)].get('ticket_channel')
        if channel_id:
            return guild.get_channel(channel_id)
    
    for channel in guild.text_channels:
        if channel.name == "tikety-podderzhki":
            return channel
    return None

def get_moderation_channel(guild):
    if str(guild.id) in support_config:
        channel_id = support_config[str(guild.id)].get('complaint_channel')
        if channel_id:
            return guild.get_channel(channel_id)
    
    for channel in guild.text_channels:
        if channel.name == "zhaloby-moderacii":
            return channel
    return None

async def backup_channel(channel):
    if isinstance(channel, discord.TextChannel):
        backup_data = {
            'name': channel.name,
            'type': 'text',
            'position': channel.position,
            'topic': channel.topic,
            'slowmode_delay': channel.slowmode_delay,
            'is_nsfw': channel.is_nsfw(),
            'category_id': channel.category.id if channel.category else None,
            'permissions': [],
            'messages': []
        }
        
        for target, overwrite in channel.overwrites.items():
            perm_data = {
                'target_type': 'role' if isinstance(target, discord.Role) else 'member',
                'target_id': target.id,
                'target_name': target.name if isinstance(target, discord.Role) else str(target),
                'allow': overwrite.pair()[0].value,
                'deny': overwrite.pair()[1].value
            }
            backup_data['permissions'].append(perm_data)
        
        try:
            async for message in channel.history(limit=200):
                msg_data = {
                    'id': message.id,
                    'author_id': message.author.id,
                    'author_name': str(message.author),
                    'content': message.content,
                    'created_at': message.created_at.isoformat(),
                    'attachments': [a.url for a in message.attachments]
                }
                backup_data['messages'].append(msg_data)
        except:
            pass
        
        channel_backup[str(channel.id)] = backup_data
        save_channel_backup()
        return True
    return False

async def restore_channel(guild, channel_id):
    if str(channel_id) not in channel_backup:
        return None
    
    backup = channel_backup[str(channel_id)]
    
    category = None
    if backup.get('category_id'):
        category = guild.get_channel(backup['category_id'])
    
    try:
        if backup['type'] == 'text':
            new_channel = await guild.create_text_channel(
                name=backup['name'],
                category=category,
                position=backup['position'],
                topic=backup.get('topic', ''),
                slowmode_delay=backup.get('slowmode_delay', 0),
                nsfw=backup.get('is_nsfw', False)
            )
            
            for perm_data in backup.get('permissions', []):
                try:
                    if perm_data['target_type'] == 'role':
                        target = guild.get_role(perm_data['target_id'])
                    else:
                        target = guild.get_member(perm_data['target_id'])
                    
                    if target:
                        allow = discord.Permissions(perm_data['allow'])
                        deny = discord.Permissions(perm_data['deny'])
                        await new_channel.set_permissions(target, overwrite=discord.PermissionOverwrite.from_pair(allow, deny))
                except:
                    pass
            
            for msg_data in reversed(backup.get('messages', [])):
                try:
                    await new_channel.send(msg_data['content'])
                    await asyncio.sleep(0.2)
                except:
                    pass
            
            return new_channel
    except Exception as e:
        print(f'Ошибка восстановления канала: {e}')
        return None

async def check_raid(guild_id):
    global raid_active, raid_level, suspicion_active
    
    current_time = datetime.now()
    
    if guild_id not in join_history:
        join_history[guild_id] = []
    
    join_history[guild_id] = [t for t in join_history[guild_id] if (current_time - t).total_seconds() < 120]
    
    joins_15s = len([t for t in join_history[guild_id] if (current_time - t).total_seconds() < 15])
    joins_30s = len([t for t in join_history[guild_id] if (current_time - t).total_seconds() < 30])
    joins_60s = len([t for t in join_history[guild_id] if (current_time - t).total_seconds() < 60])
    joins_120s = len([t for t in join_history[guild_id] if (current_time - t).total_seconds() < 120])
    
    if guild_id not in raid_active:
        raid_active[guild_id] = False
        raid_level[guild_id] = 0
        suspicion_active[guild_id] = False
    
    night_multiplier = 1.5 if is_night_time() else 1
    suspicion_threshold = int(5 * night_multiplier)
    
    if not raid_active[guild_id]:
        if joins_15s >= suspicion_threshold:
            if not suspicion_active[guild_id]:
                suspicion_active[guild_id] = True
                embed = discord.Embed(
                    title='⚠️ ПОДОЗРЕНИЕ НА РЕЙД',
                    color=discord.Color.orange(),
                    timestamp=datetime.now()
                )
                embed.add_field(name='📊 Статистика', value=f'{joins_15s} человек за 15 секунд', inline=False)
                embed.add_field(name='📋 Действие', value='Включен медленный режим (slowmode 5 секунд)', inline=False)
                await send_log(guild_id, embed)
                
                guild = bot.get_guild(guild_id)
                if guild:
                    for channel in guild.text_channels:
                        try:
                            if channel.permissions_for(guild.me).manage_channels:
                                await channel.edit(slowmode_delay=5)
                        except:
                            pass
        
        if joins_60s >= 15:
            raid_active[guild_id] = True
            raid_level[guild_id] = 2
            await activate_lockdown(guild_id, 'рейд')
            
            embed = discord.Embed(
                title='🚨 ОБНАРУЖЕН РЕЙД!',
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            embed.add_field(name='📊 Статистика', value=f'{joins_60s} человек за 60 секунд', inline=False)
            embed.add_field(name='📋 Действие', value='Активирован режим LOCKDOWN', inline=False)
            await send_log(guild_id, embed)
        
        elif joins_120s >= 20:
            raid_active[guild_id] = True
            raid_level[guild_id] = 3
            await activate_lockdown(guild_id, 'жесткий рейд')
            
            guild = bot.get_guild(guild_id)
            if guild:
                for member in guild.members:
                    if (datetime.now(timezone.utc) - member.created_at.replace(tzinfo=timezone.utc)).days < 1:
                        try:
                            await member.ban(reason='Анти-рейд: аккаунт младше 1 дня')
                            embed = discord.Embed(
                                title='🔨 АВТОМАТИЧЕСКИЙ БАН',
                                color=discord.Color.dark_red(),
                                timestamp=datetime.now()
                            )
                            embed.add_field(name='👤 Участник', value=f'{member.mention}\n`{member}`', inline=True)
                            embed.add_field(name='📝 Причина', value='Аккаунт младше 1 дня во время рейда', inline=False)
                            await send_log(guild_id, embed)
                        except:
                            pass
                    elif (datetime.now(timezone.utc) - member.created_at.replace(tzinfo=timezone.utc)).days < 7:
                        try:
                            await member.kick(reason='Анти-рейд: аккаунт младше 7 дней')
                            embed = discord.Embed(
                                title='👢 АВТОМАТИЧЕСКИЙ КИК',
                                color=discord.Color.orange(),
                                timestamp=datetime.now()
                            )
                            embed.add_field(name='👤 Участник', value=f'{member.mention}\n`{member}`', inline=True)
                            embed.add_field(name='📝 Причина', value='Аккаунт младше 7 дней во время рейда', inline=False)
                            await send_log(guild_id, embed)
                        except:
                            pass
            
            embed = discord.Embed(
                title='🚨 ЖЕСТКИЙ РЕЙД ОБНАРУЖЕН!',
                color=discord.Color.dark_red(),
                timestamp=datetime.now()
            )
            embed.add_field(name='📊 Статистика', value=f'{joins_120s} человек за 120 секунд', inline=False)
            embed.add_field(name='📋 Действие', value='Активирован жесткий режим защиты. Новые аккаунты банились/кикались.', inline=False)
            await send_log(guild_id, embed)

async def activate_lockdown(guild_id, reason):
    global lockdown_active
    
    guild = bot.get_guild(guild_id)
    if not guild:
        return
    
    lockdown_active[guild_id] = True
    
    raid_config[str(guild_id)] = {
        'active': True,
        'start_time': datetime.now().isoformat(),
        'reason': reason,
        'original_perms': {}
    }
    save_raid_config()
    
    for channel in guild.channels:
        if isinstance(channel, discord.TextChannel):
            is_admin_channel = False
            for target, overwrite in channel.overwrites.items():
                if isinstance(target, discord.Role) and target.permissions.administrator:
                    is_admin_channel = True
                    break
                elif isinstance(target, discord.Member) and target.guild_permissions.administrator:
                    is_admin_channel = True
                    break
            
            is_news_channel = channel.is_news()
            
            if is_admin_channel or is_news_channel:
                continue
            
            try:
                overwrite = channel.overwrites_for(guild.default_role)
                raid_config[str(guild_id)]['original_perms'][str(channel.id)] = {
                    'send_messages': overwrite.send_messages,
                    'add_reactions': overwrite.add_reactions
                }
                
                overwrite.send_messages = False
                overwrite.add_reactions = False
                await channel.set_permissions(guild.default_role, overwrite=overwrite)
                
                await channel.edit(slowmode_delay=600)
            except:
                pass
    
    for channel in guild.voice_channels:
        try:
            overwrite = channel.overwrites_for(guild.default_role)
            raid_config[str(guild_id)]['original_perms'][str(channel.id)] = {
                'connect': overwrite.connect
            }
            overwrite.connect = False
            await channel.set_permissions(guild.default_role, overwrite=overwrite)
        except:
            pass
    
    try:
        invites = await guild.invites()
        for invite in invites:
            try:
                await invite.delete()
            except:
                pass
        raid_config[str(guild_id)]['invites_deleted'] = True
        save_raid_config()
    except:
        pass
    
    embed = discord.Embed(
        title='🔒 РЕЖИМ LOCKDOWN АКТИВИРОВАН',
        color=discord.Color.dark_red(),
        timestamp=datetime.now()
    )
    embed.add_field(name='📋 Причина', value=reason, inline=False)
    embed.add_field(name='⏰ Длительность', value='35 минут', inline=False)
    embed.add_field(name='📌 Что заблокировано', value='• Отправка сообщений\n• Реакции\n• Создание инвайтов\n• Slowmode 10 минут\n• Новые участники не могут писать', inline=False)
    embed.add_field(name='🛡️ Кто может писать', value='Администраторы', inline=False)
    
    await send_log(guild_id, embed)
    
    await asyncio.sleep(35 * 60)
    
    if lockdown_active.get(guild_id, False):
        await deactivate_lockdown(guild_id)

async def deactivate_lockdown(guild_id):
    global lockdown_active
    
    guild = bot.get_guild(guild_id)
    if not guild:
        return
    
    lockdown_active[guild_id] = False
    
    if str(guild_id) in raid_config:
        config = raid_config[str(guild_id)]
        
        for channel_id, perms in config.get('original_perms', {}).items():
            channel = guild.get_channel(int(channel_id))
            if channel:
                try:
                    overwrite = channel.overwrites_for(guild.default_role)
                    if 'send_messages' in perms:
                        overwrite.send_messages = perms['send_messages']
                    if 'add_reactions' in perms:
                        overwrite.add_reactions = perms['add_reactions']
                    if 'connect' in perms:
                        overwrite.connect = perms['connect']
                    await channel.set_permissions(guild.default_role, overwrite=overwrite)
                    
                    await channel.edit(slowmode_delay=0)
                except:
                    pass
        
        raid_config.pop(str(guild_id))
        save_raid_config()
    
    embed = discord.Embed(
        title='🔓 РЕЖИМ LOCKDOWN ОТКЛЮЧЕН',
        color=discord.Color.green(),
        timestamp=datetime.now()
    )
    embed.add_field(name='📋 Статус', value='Сервер вернулся в обычный режим работы', inline=False)
    
    await send_log(guild_id, embed)

class RoleButtonView(View):
    def __init__(self, roles_data: list, message_id: int):
        super().__init__(timeout=None)
        self.roles_data = roles_data
        self.message_id = message_id
        
        for item in roles_data:
            button = Button(label=item['label'], style=discord.ButtonStyle.primary, emoji=item['emoji'], custom_id=f"role_{item['role_id']}")
            button.callback = self.create_callback(item['role_id'])
            self.add_item(button)
    
    def create_callback(self, role_id):
        async def callback(interaction: discord.Interaction):
            role = interaction.guild.get_role(role_id)
            if role:
                if role in interaction.user.roles:
                    await interaction.user.remove_roles(role)
                    await interaction.response.send_message(f"✅ Роль {role.mention} снята!", ephemeral=True)
                else:
                    await interaction.user.add_roles(role)
                    await interaction.response.send_message(f"✅ Вам выдана роль {role.mention}!", ephemeral=True)
            else:
                await interaction.response.send_message("❌ Роль не найдена", ephemeral=True)
        return callback

class SupportModal(Modal):
    def __init__(self):
        super().__init__(title="Создание обращения в поддержку")
        
        self.topic = TextInput(
            label="📌 Тема обращения",
            placeholder="Кратко опишите проблему...",
            required=True,
            max_length=100
        )
        self.add_item(self.topic)
        
        self.description = TextInput(
            label="📝 Подробное описание",
            placeholder="Опишите ситуацию подробно...\nЧто произошло? Когда? Какие ошибки?",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=1500
        )
        self.add_item(self.description)
        
        self.attachments = TextInput(
            label="🔗 Доказательства (опционально)",
            placeholder="Ссылки на скриншоты, видео или ID сообщений...",
            required=False,
            max_length=500
        )
        self.add_item(self.attachments)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        tickets_data['ticket_counter'] += 1
        ticket_num = tickets_data['ticket_counter']
        ticket_id = format_ticket_number(ticket_num)
        
        tickets_data['tickets'][ticket_id] = {
            'user_id': interaction.user.id,
            'user_name': str(interaction.user),
            'topic': self.topic.value,
            'description': self.description.value,
            'attachments': self.attachments.value,
            'status': 'open',
            'created_at': datetime.now().isoformat(),
            'has_response': False,
            'messages': []
        }
        save_tickets()
        
        embed = discord.Embed(
            title=f"🎫 {ticket_id}",
            description=f"**Тема:** {self.topic.value}\n"
                       f"**Статус:** 🟡 Ожидает рассмотрения\n"
                       f"**Создатель:** {interaction.user.mention}\n"
                       f"**Создан:** <t:{int(datetime.now().timestamp())}:F>",
            color=discord.Color.orange(),
            timestamp=datetime.now()
        )
        embed.add_field(name="📝 Описание", value=self.description.value[:1024], inline=False)
        if self.attachments.value:
            embed.add_field(name="🔗 Доказательства", value=self.attachments.value, inline=False)
        embed.set_footer(text=f"ID: {ticket_id}")
        
        support_channel = get_support_channel(interaction.guild)
        if support_channel:
            view = TicketControlView(ticket_id, interaction.user.id, interaction.guild.id, is_complaint=False)
            await support_channel.send(embed=embed, view=view)
            await interaction.followup.send(f"✅ Обращение **{ticket_id}** создано! Специалисты скоро ответят.", ephemeral=True)
        else:
            await interaction.followup.send("❌ Канал для тикетов не настроен. Обратитесь к администратору.", ephemeral=True)

class ComplaintModal(Modal):
    def __init__(self, target_user: discord.Member = None):
        super().__init__(title="Подача жалобы")
        
        self.target_user_id = TextInput(
            label="👤 Тег пользователя (или укажите в описании)",
            placeholder="Введите тег пользователя или напишите 'в описании'",
            required=True,
            max_length=20
        )
        self.add_item(self.target_user_id)
        
        self.reason = TextInput(
            label="📋 Причина жалобы",
            placeholder="Оскорбления / Спам / Нарушение правил / Другое...",
            required=True,
            max_length=200
        )
        self.add_item(self.reason)
        
        self.description = TextInput(
            label="📝 Подробное описание",
            placeholder="Что именно произошло? Где? Когда? Приложите доказательства...",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=1500
        )
        self.add_item(self.description)
        
        self.evidence = TextInput(
            label="🔗 Доказательства",
            placeholder="Ссылки на скриншоты, ID сообщений, видео...",
            required=False,
            max_length=500
        )
        self.add_item(self.evidence)
        
        if target_user:
            self.target_user_id.default = str(target_user.id)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        tickets_data['complaint_counter'] += 1
        complaint_num = tickets_data['complaint_counter']
        complaint_id = format_complaint_number(complaint_num)
        
        target_id = self.target_user_id.value
        target_user = None
        if target_id.isdigit():
            target_user = interaction.guild.get_member(int(target_id))
        
        tickets_data['complaints'][complaint_id] = {
            'user_id': interaction.user.id,
            'user_name': str(interaction.user),
            'target_id': int(target_id) if target_id.isdigit() else None,
            'target_name': target_user.name if target_user else target_id,
            'reason': self.reason.value,
            'description': self.description.value,
            'evidence': self.evidence.value,
            'status': 'open',
            'created_at': datetime.now().isoformat(),
            'has_response': False,
            'messages': []
        }
        save_tickets()
        
        embed = discord.Embed(
            title=f"⚠️ {complaint_id}",
            description=f"**Жалоба на:** {target_user.mention if target_user else target_id}\n"
                       f"**Причина:** {self.reason.value}\n"
                       f"**Статус:** 🟡 Рассматривается\n"
                       f"**Жалобщик:** {interaction.user.mention}",
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        embed.add_field(name="📝 Описание", value=self.description.value[:1024], inline=False)
        if self.evidence.value:
            embed.add_field(name="🔗 Доказательства", value=self.evidence.value, inline=False)
        embed.set_footer(text=f"ID: {complaint_id}")
        
        mod_channel = get_moderation_channel(interaction.guild)
        if mod_channel:
            view = TicketControlView(complaint_id, interaction.user.id, interaction.guild.id, is_complaint=True)
            await mod_channel.send(embed=embed, view=view)
            await interaction.followup.send(f"✅ Жалоба **{complaint_id}** передана модераторам!", ephemeral=True)
        else:
            await interaction.followup.send("❌ Канал для жалоб не настроен. Обратитесь к администратору.", ephemeral=True)

class SupportView(View):
    def __init__(self, guild_id: int):
        super().__init__(timeout=None)
        self.guild_id = guild_id
    
    @discord.ui.button(label="📨 Обратиться в поддержку", style=discord.ButtonStyle.primary, emoji="📨")
    async def support_button(self, interaction: discord.Interaction, button: Button):
        modal = SupportModal()
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="⚠️ Пожаловаться на пользователя", style=discord.ButtonStyle.danger, emoji="⚠️")
    async def complaint_button(self, interaction: discord.Interaction, button: Button):
        modal = ComplaintModal()
        await interaction.response.send_modal(modal)

class TicketControlView(View):
    def __init__(self, item_id: str, user_id: int, guild_id: int, is_complaint: bool = False):
        super().__init__(timeout=None)
        self.item_id = item_id
        self.user_id = user_id
        self.guild_id = guild_id
        self.is_complaint = is_complaint
    
    @discord.ui.button(label="✅ Принять в работу", style=discord.ButtonStyle.success, emoji="✅")
    async def accept_button(self, interaction: discord.Interaction, button: Button):
        if not can_manage_support(interaction.user, self.guild_id):
            await interaction.response.send_message("❌ У вас нет прав для этого", ephemeral=True)
            return
        
        if self.is_complaint:
            tickets_data['complaints'][self.item_id]['status'] = 'in_progress'
            tickets_data['complaints'][self.item_id]['moderator_id'] = interaction.user.id
            tickets_data['complaints'][self.item_id]['moderator_name'] = str(interaction.user)
        else:
            tickets_data['tickets'][self.item_id]['status'] = 'in_progress'
            tickets_data['tickets'][self.item_id]['moderator_id'] = interaction.user.id
            tickets_data['tickets'][self.item_id]['moderator_name'] = str(interaction.user)
        save_tickets()
        
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.blue()
        if self.is_complaint:
            embed.description = embed.description.replace("🟡 Рассматривается", "🔵 В работе (принято)")
        else:
            embed.description = embed.description.replace("🟡 Ожидает рассмотрения", "🔵 В работе (принято)")
        
        await interaction.message.edit(embed=embed)
        await interaction.response.send_message("✅ Вы приняли обращение в работу", ephemeral=True)
        
        user = interaction.guild.get_member(self.user_id)
        if user:
            try:
                await user.send(f"✅ Ваше обращение **{self.item_id}** принято в работу специалистом")
            except:
                pass
    
    @discord.ui.button(label="💬 Написать ответ", style=discord.ButtonStyle.secondary, emoji="💬")
    async def reply_button(self, interaction: discord.Interaction, button: Button):
        if not can_manage_support(interaction.user, self.guild_id):
            await interaction.response.send_message("❌ У вас нет прав для этого", ephemeral=True)
            return
        
        modal = ReplyModal(self.item_id, self.user_id, self.guild_id, self.is_complaint)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="🔒 Закрыть", style=discord.ButtonStyle.danger, emoji="🔒")
    async def close_button(self, interaction: discord.Interaction, button: Button):
        if not can_manage_support(interaction.user, self.guild_id):
            await interaction.response.send_message("❌ У вас нет прав для этого", ephemeral=True)
            return
        
        if self.is_complaint:
            if not tickets_data['complaints'][self.item_id].get('has_response', False):
                await interaction.response.send_message("❌ Нельзя закрыть жалобу без ответа пользователю!", ephemeral=True)
                return
            tickets_data['complaints'][self.item_id]['status'] = 'closed'
            tickets_data['complaints'][self.item_id]['closed_at'] = datetime.now().isoformat()
            tickets_data['complaints'][self.item_id]['closed_by'] = interaction.user.id
        else:
            if not tickets_data['tickets'][self.item_id].get('has_response', False):
                await interaction.response.send_message("❌ Нельзя закрыть тикет без ответа пользователю!", ephemeral=True)
                return
            tickets_data['tickets'][self.item_id]['status'] = 'closed'
            tickets_data['tickets'][self.item_id]['closed_at'] = datetime.now().isoformat()
            tickets_data['tickets'][self.item_id]['closed_by'] = interaction.user.id
        save_tickets()
        
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.green()
        if self.is_complaint:
            embed.description = embed.description.replace("🟡 Рассматривается", "✅ Закрыто")
            if "🔵 В работе" in embed.description:
                embed.description = embed.description.replace("🔵 В работе (принято)", "✅ Закрыто")
        else:
            embed.description = embed.description.replace("🟡 Ожидает рассмотрения", "✅ Закрыт")
            if "🔵 В работе" in embed.description:
                embed.description = embed.description.replace("🔵 В работе (принято)", "✅ Закрыт")
        
        await interaction.message.edit(embed=embed, view=None)
        await interaction.response.send_message("✅ Обращение закрыто", ephemeral=True)
        
        user = interaction.guild.get_member(self.user_id)
        if user:
            reply_embed = discord.Embed(
                title=f"🔒 Ваше обращение {self.item_id} закрыто",
                description=f"Ваше обращение закрыто.\nЕсли у вас остались вопросы, создайте новое.",
                color=discord.Color.green()
            )
            try:
                await user.send(embed=reply_embed)
            except:
                pass

class ReplyModal(Modal):
    def __init__(self, item_id: str, user_id: int, guild_id: int, is_complaint: bool):
        super().__init__(title="💬 Ответ пользователю")
        self.item_id = item_id
        self.user_id = user_id
        self.guild_id = guild_id
        self.is_complaint = is_complaint
        
        self.message = TextInput(
            label="📝 Текст ответа",
            placeholder="Напишите ответ пользователю...",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=1500
        )
        self.add_item(self.message)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        if self.is_complaint:
            if 'messages' not in tickets_data['complaints'][self.item_id]:
                tickets_data['complaints'][self.item_id]['messages'] = []
            
            tickets_data['complaints'][self.item_id]['messages'].append({
                'from': 'moderator',
                'moderator_id': interaction.user.id,
                'message': self.message.value,
                'timestamp': datetime.now().isoformat()
            })
            tickets_data['complaints'][self.item_id]['has_response'] = True
        else:
            if 'messages' not in tickets_data['tickets'][self.item_id]:
                tickets_data['tickets'][self.item_id]['messages'] = []
            
            tickets_data['tickets'][self.item_id]['messages'].append({
                'from': 'moderator',
                'moderator_id': interaction.user.id,
                'message': self.message.value,
                'timestamp': datetime.now().isoformat()
            })
            tickets_data['tickets'][self.item_id]['has_response'] = True
        save_tickets()
        
        user = interaction.guild.get_member(self.user_id)
        if user:
            reply_embed = discord.Embed(
                title=f"📩 Ответ по обращению {self.item_id}",
                description=self.message.value,
                color=discord.Color.blue()
            )
            
            try:
                await user.send(embed=reply_embed)
                await interaction.followup.send("✅ Ответ отправлен пользователю в личные сообщения", ephemeral=True)
            except:
                await interaction.followup.send("⚠️ Не удалось отправить сообщение пользователю (закрыты личные сообщения)", ephemeral=True)
        else:
            await interaction.followup.send("❌ Пользователь не найден на сервере", ephemeral=True)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'Бот {bot.user} запущен')
    print(f'Загружено команд: {len(bot.tree.get_commands())}')
    
    if 'ticket_counter' not in tickets_data:
        tickets_data['ticket_counter'] = 0
    if 'complaint_counter' not in tickets_data:
        tickets_data['complaint_counter'] = 0
    if 'tickets' not in tickets_data:
        tickets_data['tickets'] = {}
    if 'complaints' not in tickets_data:
        tickets_data['complaints'] = {}
    save_tickets()
    
    for guild_id in list(raid_config.keys()):
        if raid_config[guild_id].get('active', False):
            start_time = datetime.fromisoformat(raid_config[guild_id]['start_time'])
            elapsed = (datetime.now() - start_time).total_seconds()
            if elapsed < 35 * 60:
                remaining = 35 * 60 - elapsed
                asyncio.create_task(delayed_deactivate(int(guild_id), remaining))
            else:
                await deactivate_lockdown(int(guild_id))

async def delayed_deactivate(guild_id, delay):
    await asyncio.sleep(delay)
    await deactivate_lockdown(guild_id)

@bot.event
async def on_member_join(member):
    if member.bot and member != bot.user:
        guild = member.guild
        
        async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.member_add):
            if entry.target.id == member.id:
                adder = entry.user
                
                if adder != guild.owner:
                    try:
                        await member.kick(reason='Автозащита: добавление бота не владельцем сервера')
                    except:
                        pass
                    
                    removed_roles = []
                    for role in adder.roles:
                        if role.permissions.administrator or role.permissions.manage_guild or role.permissions.manage_channels:
                            try:
                                await adder.remove_roles(role, reason='Автозащита: попытка добавления бота')
                                removed_roles.append(role.name)
                            except:
                                pass
                    
                    embed = discord.Embed(
                        title='🤖 ЗАЩИТА ОТ БОТОВ',
                        color=discord.Color.dark_red(),
                        timestamp=datetime.now()
                    )
                    embed.add_field(name='🤖 Бот', value=f'{member.name}\n`{member.id}`', inline=True)
                    embed.add_field(name='👤 Добавил', value=f'{adder.mention}\n`{adder}`', inline=True)
                    embed.add_field(name='📋 Действие', value='• Бот удален\n• Сняты административные роли', inline=False)
                    if removed_roles:
                        embed.add_field(name='🗑️ Снятые роли', value=', '.join(removed_roles), inline=False)
                    await send_log(guild.id, embed)
                    
                    try:
                        await adder.send(f'🚫 Вы были наказаны на сервере **{guild.name}** за попытку добавления бота.\nС вас сняты все административные роли.')
                    except:
                        pass
                    
                    return
        
        return
    
    guild_id = member.guild.id
    
    if guild_id not in join_history:
        join_history[guild_id] = []
    
    join_history[guild_id].append(datetime.now())
    
    embed = discord.Embed(
        title='👤 ПОЛЬЗОВАТЕЛЬ ЗАШЕЛ',
        color=discord.Color.green(),
        timestamp=datetime.now()
    )
    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
    embed.add_field(name='📝 Имя', value=f'{member.mention}\n`{member}`', inline=True)
    embed.add_field(name='🆔 ID', value=member.id, inline=True)
    embed.add_field(name='📅 Аккаунт создан', value=f'<t:{int(member.created_at.timestamp())}:R>', inline=True)
    
    account_age_days = is_new_account(member.created_at)
    embed.add_field(name='👶 Возраст аккаунта', value=f'{account_age_days} дней', inline=True)
    await send_log(guild_id, embed)
    
    if lockdown_active.get(guild_id, False):
        try:
            overwrite = member.guild.default_role
            await member.guild.default_role.edit(send_messages=False)
        except:
            pass
    
    await check_raid(guild_id)

@bot.event
async def on_message(message):
    if message.author.bot:
        await bot.process_commands(message)
        return
    
    if not message.guild:
        await bot.process_commands(message)
        return
    
    if lockdown_active.get(message.guild.id, False):
        if not message.author.guild_permissions.administrator:
            try:
                await message.delete()
            except:
                pass
            await bot.process_commands(message)
            return
    
    content_to_check = message.content
    
    if message.reference:
        try:
            referenced_msg = await message.channel.fetch_message(message.reference.message_id)
            if referenced_msg and referenced_msg.content:
                content_to_check += ' ' + referenced_msg.content
                if has_link(referenced_msg.content):
                    await add_warn_and_check(message.guild.id, message.author.id, bot.user.id, 'Пересланное сообщение с запрещенной ссылкой', True)
                    try:
                        await message.author.edit(timed_out_until=discord.utils.utcnow() + timedelta(hours=1), reason='Пересланная ссылка на другой сервер')
                    except:
                        await message.author.timeout(discord.utils.utcnow() + timedelta(hours=1), reason='Пересланная ссылка на другой сервер')
                    await message.delete()
                    
                    log_mute_embed = discord.Embed(
                        title='🔇 МУТ ЗА ПЕРЕСЛАННУЮ ССЫЛКУ',
                        color=discord.Color.dark_red(),
                        timestamp=datetime.now()
                    )
                    log_mute_embed.add_field(name='👤 Участник', value=f'{message.author.mention}\n`{message.author}`', inline=True)
                    log_mute_embed.add_field(name='⏰ Длительность', value='1 час', inline=True)
                    log_mute_embed.add_field(name='⚠️ Причина', value='Пересланное сообщение со ссылкой на другой сервер', inline=False)
                    await send_log(message.guild.id, log_mute_embed)
                    await bot.process_commands(message)
                    return
        except:
            pass
    
    user_id = str(message.author.id)
    current_time = datetime.now()
    
    if user_id not in message_history:
        message_history[user_id] = []
    
    message_history[user_id].append({
        'content': message.content,
        'time': current_time
    })
    
    message_history[user_id] = [msg for msg in message_history[user_id] if (current_time - msg['time']).seconds < 10]
    
    if len(message_history[user_id]) >= 4:
        last_messages = message_history[user_id][-4:]
        if all(msg['content'] == last_messages[0]['content'] for msg in last_messages):
            spam_count[user_id] = spam_count.get(user_id, 0) + 1
            save_spam_count()
            
            await add_warn_and_check(message.guild.id, message.author.id, bot.user.id, f'Спам: 4 одинаковых сообщения подряд (нарушение {spam_count[user_id]})', True)
            await message.delete()
            
            if message.author.bot and raid_active.get(message.guild.id, False):
                try:
                    await message.author.ban(reason='Анти-рейд: бот спамит во время рейда')
                    embed = discord.Embed(
                        title='🔨 АВТОМАТИЧЕСКИЙ БАН БОТА',
                        color=discord.Color.dark_red(),
                        timestamp=datetime.now()
                    )
                    embed.add_field(name='👤 Бот', value=f'{message.author.mention}\n`{message.author}`', inline=True)
                    embed.add_field(name='📝 Причина', value='Спам во время рейда', inline=False)
                    await send_log(message.guild.id, embed)
                except:
                    pass
            
            if spam_count[user_id] >= 4:
                try:
                    await message.author.edit(timed_out_until=discord.utils.utcnow() + timedelta(hours=6), reason=f'Многократный спам')
                except:
                    await message.author.timeout(discord.utils.utcnow() + timedelta(hours=6), reason=f'Многократный спам')
                
                log_mute_embed = discord.Embed(
                    title='🔇 МУТ ЗА СПАМ',
                    color=discord.Color.dark_red(),
                    timestamp=datetime.now()
                )
                log_mute_embed.add_field(name='👤 Участник', value=f'{message.author.mention}\n`{message.author}`', inline=True)
                log_mute_embed.add_field(name='⏰ Длительность', value='6 часов', inline=True)
                log_mute_embed.add_field(name='⚠️ Причина', value='Многократный спам (4+ раза)', inline=False)
                await send_log(message.guild.id, log_mute_embed)
                
                spam_count[user_id] = 0
                save_spam_count()
            
            await bot.process_commands(message)
            return
    
    mention_count = len(message.mentions)
    if mention_count >= 4:
        await add_warn_and_check(message.guild.id, message.author.id, bot.user.id, f'Массовые упоминания: {mention_count} упоминаний', True)
        
        try:
            await message.author.edit(timed_out_until=discord.utils.utcnow() + timedelta(hours=1), reason=f'Массовые упоминания: {mention_count}')
        except:
            await message.author.timeout(discord.utils.utcnow() + timedelta(hours=1), reason=f'Массовые упоминания: {mention_count}')
        
        log_mute_embed = discord.Embed(
            title='🔇 МУТ ЗА МАССОВЫЕ УПОМИНАНИЯ',
            color=discord.Color.dark_red(),
            timestamp=datetime.now()
        )
        log_mute_embed.add_field(name='👤 Участник', value=f'{message.author.mention}\n`{message.author}`', inline=True)
        log_mute_embed.add_field(name='⏰ Длительность', value='1 час', inline=True)
        log_mute_embed.add_field(name='⚠️ Причина', value=f'Массовые упоминания ({mention_count} упоминаний)', inline=False)
        await send_log(message.guild.id, log_mute_embed)
        
        await message.delete()
        await bot.process_commands(message)
        return
    
    if has_link(content_to_check):
        await add_warn_and_check(message.guild.id, message.author.id, bot.user.id, 'Запрещенная ссылка', True)
        await message.delete()
        await bot.process_commands(message)
        return
    
    await bot.process_commands(message)

def has_link(text):
    url_pattern = r'(https?://[^\s]+|www\.[^\s]+|discord\.gg/[^\s]+|discord\.com/invite/[^\s]+)'
    return re.search(url_pattern, text.lower()) is not None

@bot.event
async def on_invite_create(invite):
    async for entry in invite.guild.audit_logs(limit=1, action=discord.AuditLogAction.invite_create):
        creator = entry.user
        embed = discord.Embed(
            title='🔗 СОЗДАНА ССЫЛКА-ПРИГЛАШЕНИЕ',
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        embed.add_field(name='👤 Создатель', value=f'{creator.mention}\n`{creator}`', inline=True)
        embed.add_field(name='🔗 Код', value=f'`{invite.code}`', inline=True)
        embed.add_field(name='📊 Макс использований', value=invite.max_uses if invite.max_uses else 'Безлимит', inline=True)
        embed.add_field(name='⏰ Истекает', value=f'<t:{int(invite.expires_at.timestamp())}:R>' if invite.expires_at else 'Никогда', inline=True)
        await send_log(invite.guild.id, embed)
        break

async def auto_unwarn_after_5_days(guild_id, user_id, warn_id):
    await asyncio.sleep(5 * 24 * 60 * 60)
    
    guild_id_str = str(guild_id)
    user_id_str = str(user_id)
    
    if guild_id_str in warns and user_id_str in warns[guild_id_str]:
        user_warns = warns[guild_id_str][user_id_str]
        warn_to_remove = None
        
        for warn in user_warns:
            if warn['id'] == warn_id:
                warn_to_remove = warn
                break
        
        if warn_to_remove:
            user_warns.remove(warn_to_remove)
            
            for i, warn in enumerate(user_warns, 1):
                warn['id'] = i
            
            if not user_warns:
                del warns[guild_id_str][user_id_str]
            
            save_warns()
            
            guild = bot.get_guild(guild_id)
            if guild and guild_id_str in logs_config:
                user = guild.get_member(user_id)
                if user:
                    embed = discord.Embed(
                        title='✅ АВТОМАТИЧЕСКОЕ СНЯТИЕ ПРЕДУПРЕЖДЕНИЯ',
                        color=discord.Color.green(),
                        timestamp=datetime.now()
                    )
                    embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
                    embed.add_field(name='👤 Участник', value=f'{user.mention}\n`{user}`', inline=True)
                    embed.add_field(name='⚠️ Снято предупреждение', value=f'№{warn_id}', inline=True)
                    embed.add_field(name='📊 Предупреждений осталось', value=f'{len(user_warns)}/3', inline=True)
                    embed.add_field(name='📝 Причина снятия', value='Истекло 5 дней', inline=False)
                    await send_log(guild_id, embed)

async def add_warn_and_check(guild_id, user_id, moderator_id, reason, is_auto=False):
    user_id_str = str(user_id)
    guild_id_str = str(guild_id)
    
    if guild_id_str not in warns:
        warns[guild_id_str] = {}
    
    if user_id_str not in warns[guild_id_str]:
        warns[guild_id_str][user_id_str] = []
    
    warn_count = len(warns[guild_id_str][user_id_str])
    
    if warn_count >= 3:
        return False, warn_count
    
    warn_id = warn_count + 1
    warn_data = {
        'id': warn_id,
        'reason': reason,
        'moderator': moderator_id,
        'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    warns[guild_id_str][user_id_str].append(warn_data)
    save_warns()
    
    asyncio.create_task(auto_unwarn_after_5_days(guild_id, user_id, warn_id))
    
    new_warn_count = len(warns[guild_id_str][user_id_str])
    
    guild = bot.get_guild(guild_id)
    user = guild.get_member(user_id)
    moderator = guild.get_member(moderator_id)
    
    if user:
        await send_dm(user, '⚠️ ВЫ ПОЛУЧИЛИ ПРЕДУПРЕЖДЕНИЕ', reason, new_warn_count)
    
    if moderator and not is_auto:
        log_embed = discord.Embed(
            title='⚠️ ВЫДАНО ПРЕДУПРЕЖДЕНИЕ',
            color=discord.Color.orange(),
            timestamp=datetime.now()
        )
        log_embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
        log_embed.add_field(name='👤 Участник', value=f'{user.mention}\n`{user}`', inline=True)
        log_embed.add_field(name='🛡️ Модератор', value=f'{moderator.mention}\n`{moderator}`', inline=True)
        log_embed.add_field(name='⚠️ Предупреждений', value=f'**{new_warn_count}/3**', inline=True)
        log_embed.add_field(name='📝 Причина', value=f'```{reason}```', inline=False)
        log_embed.add_field(name='⏰ Автоснятие', value='Через 5 дней', inline=False)
        log_embed.set_footer(text=f'ID предупреждения: {warn_id}')
        await send_log(guild_id, log_embed)
    
    if new_warn_count >= 3:
        try:
            await user.edit(timed_out_until=discord.utils.utcnow() + timedelta(hours=6), reason=f'3/3 предупреждений: {reason}')
        except:
            await user.timeout(discord.utils.utcnow() + timedelta(hours=6), reason=f'3/3 предупреждений: {reason}')
        
        await send_dm(user, '🔇 ВЫ ЗАМУЧЕНЫ АВТОМАТИЧЕСКИ', f'3/3 предупреждений. Причина: {reason}', 3)
        
        warns[guild_id_str][user_id_str] = []
        save_warns()
        
        log_mute_embed = discord.Embed(
            title='🔇 АВТОМАТИЧЕСКИЙ МУТ',
            color=discord.Color.dark_red(),
            timestamp=datetime.now()
        )
        log_mute_embed.add_field(name='👤 Участник', value=f'{user.mention}\n`{user}`', inline=True)
        log_mute_embed.add_field(name='⏰ Длительность', value='6 часов', inline=True)
        log_mute_embed.add_field(name='⚠️ Причина', value='Достигнуто 3 предупреждения', inline=False)
        log_mute_embed.add_field(name='📝 Последняя причина', value=f'```{reason}```', inline=False)
        await send_log(guild_id, log_mute_embed)
        
        return True, new_warn_count
    
    return False, new_warn_count

@bot.event
async def on_message_delete(message):
    if message.author.bot:
        return
    
    if str(message.guild.id) in logs_config:
        embed = discord.Embed(
            title='🗑️ УДАЛЕНИЕ СООБЩЕНИЯ',
            color=discord.Color.dark_red(),
            timestamp=datetime.now()
        )
        embed.set_thumbnail(url=message.author.avatar.url if message.author.avatar else message.author.default_avatar.url)
        embed.add_field(name='📝 Автор', value=f'{message.author.mention}\n`{message.author}`', inline=True)
        embed.add_field(name='📌 Канал', value=message.channel.mention, inline=True)
        
        if message.content:
            content = message.content[:1024]
            embed.add_field(name='💬 Текст сообщения', value=f'```{content}```', inline=False)
        
        if message.attachments:
            files = '\n'.join([f'📎 {a.filename}' for a in message.attachments])
            embed.add_field(name='📎 Вложения', value=files, inline=False)
        
        embed.set_footer(text=f'ID: {message.id}')
        
        await send_log(message.guild.id, embed)

@bot.event
async def on_message_edit(before, after):
    if before.author.bot:
        return
    
    if before.content == after.content:
        return
    
    if str(before.guild.id) in logs_config:
        embed = discord.Embed(
            title='✏️ ИЗМЕНЕНИЕ СООБЩЕНИЯ',
            color=discord.Color.gold(),
            timestamp=datetime.now()
        )
        embed.set_thumbnail(url=before.author.avatar.url if before.author.avatar else before.author.default_avatar.url)
        embed.add_field(name='📝 Автор', value=f'{before.author.mention}\n`{before.author}`', inline=True)
        embed.add_field(name='📌 Канал', value=before.channel.mention, inline=True)
        
        embed.add_field(name='📋 ДО изменения', value=f'```{before.content[:1024] if before.content else "Пусто"}```', inline=False)
        embed.add_field(name='📋 ПОСЛЕ изменения', value=f'```{after.content[:1024] if after.content else "Пусто"}```', inline=False)
        
        embed.set_footer(text=f'ID: {before.id}')
        
        await send_log(before.guild.id, embed)

@bot.event
async def on_member_update(before, after):
    if str(before.guild.id) not in logs_config:
        return
    
    if before.roles != after.roles:
        old_roles = set(before.roles)
        new_roles = set(after.roles)
        
        added_roles = new_roles - old_roles
        removed_roles = old_roles - new_roles
        
        async for entry in before.guild.audit_logs(limit=1, action=discord.AuditLogAction.member_role_update):
            if entry.target.id == after.id:
                moderator = entry.user
                break
        else:
            moderator = None
        
        for role in added_roles:
            embed = discord.Embed(
                title='🎭 ВЫДАНА РОЛЬ',
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            embed.set_thumbnail(url=after.avatar.url if after.avatar else after.default_avatar.url)
            embed.add_field(name='👤 Участник', value=f'{after.mention}\n`{after}`', inline=True)
            embed.add_field(name='🎭 Роль', value=role.mention, inline=True)
            embed.add_field(name='🛡️ Кто выдал', value=f'{moderator.mention}\n`{moderator}`' if moderator else 'Неизвестно', inline=True)
            await send_log(before.guild.id, embed)
        
        for role in removed_roles:
            embed = discord.Embed(
                title='🎭 СНЯТА РОЛЬ',
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            embed.set_thumbnail(url=after.avatar.url if after.avatar else after.default_avatar.url)
            embed.add_field(name='👤 Участник', value=f'{after.mention}\n`{after}`', inline=True)
            embed.add_field(name='🎭 Роль', value=role.mention, inline=True)
            embed.add_field(name='🛡️ Кто снял', value=f'{moderator.mention}\n`{moderator}`' if moderator else 'Неизвестно', inline=True)
            await send_log(before.guild.id, embed)
    
    if before.voice is not None and after.voice is not None:
        if before.voice.deaf != after.voice.deaf:
            async for entry in before.guild.audit_logs(limit=1, action=discord.AuditLogAction.member_update):
                if entry.target.id == after.id:
                    moderator = entry.user
                    break
            else:
                moderator = None
            
            if after.voice.deaf:
                embed = discord.Embed(
                    title='🔇 ЗАГЛУШЕН В ГОЛОСОВОМ КАНАЛЕ (НАУШНИКИ)',
                    color=discord.Color.orange(),
                    timestamp=datetime.now()
                )
                embed.set_thumbnail(url=after.avatar.url if after.avatar else after.default_avatar.url)
                embed.add_field(name='👤 Участник', value=f'{after.mention}\n`{after}`', inline=True)
                embed.add_field(name='📌 Канал', value=after.voice.channel.mention, inline=True)
                embed.add_field(name='🛡️ Кто заглушил', value=f'{moderator.mention}\n`{moderator}`' if moderator else 'Неизвестно', inline=True)
                await send_log(before.guild.id, embed)
            else:
                embed = discord.Embed(
                    title='🔊 РАЗГЛУШЕН В ГОЛОСОВОМ КАНАЛЕ (НАУШНИКИ)',
                    color=discord.Color.green(),
                    timestamp=datetime.now()
                )
                embed.set_thumbnail(url=after.avatar.url if after.avatar else after.default_avatar.url)
                embed.add_field(name='👤 Участник', value=f'{after.mention}\n`{after}`', inline=True)
                embed.add_field(name='📌 Канал', value=after.voice.channel.mention, inline=True)
                embed.add_field(name='🛡️ Кто разглушил', value=f'{moderator.mention}\n`{moderator}`' if moderator else 'Неизвестно', inline=True)
                await send_log(before.guild.id, embed)
        
        if before.voice.mute != after.voice.mute:
            async for entry in before.guild.audit_logs(limit=1, action=discord.AuditLogAction.member_update):
                if entry.target.id == after.id:
                    moderator = entry.user
                    break
            else:
                moderator = None
            
            if after.voice.mute:
                embed = discord.Embed(
                    title='🔇 ОТОБРАН СЛУХ (МИКРОФОН)',
                    color=discord.Color.orange(),
                    timestamp=datetime.now()
                )
                embed.set_thumbnail(url=after.avatar.url if after.avatar else after.default_avatar.url)
                embed.add_field(name='👤 Участник', value=f'{after.mention}\n`{after}`', inline=True)
                embed.add_field(name='📌 Канал', value=after.voice.channel.mention, inline=True)
                embed.add_field(name='🛡️ Кто отобрал слух', value=f'{moderator.mention}\n`{moderator}`' if moderator else 'Неизвестно', inline=True)
                await send_log(before.guild.id, embed)
            else:
                embed = discord.Embed(
                    title='🔊 ВЕРНУЛ СЛУХ (МИКРОФОН)',
                    color=discord.Color.green(),
                    timestamp=datetime.now()
                )
                embed.set_thumbnail(url=after.avatar.url if after.avatar else after.default_avatar.url)
                embed.add_field(name='👤 Участник', value=f'{after.mention}\n`{after}`', inline=True)
                embed.add_field(name='📌 Канал', value=after.voice.channel.mention, inline=True)
                embed.add_field(name='🛡️ Кто вернул слух', value=f'{moderator.mention}\n`{moderator}`' if moderator else 'Неизвестно', inline=True)
                await send_log(before.guild.id, embed)

@bot.event
async def on_guild_channel_create(channel):
    async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_create):
        creator = entry.user
        
        if not creator.guild_permissions.administrator and creator != channel.guild.owner:
            await backup_channel(channel)
            
            removed_roles = []
            for role in creator.roles:
                try:
                    await creator.remove_roles(role, reason='Нарушение: создание канала без прав')
                    removed_roles.append(role.name)
                except:
                    pass
            
            try:
                await channel.delete(reason='Автозащита: создание канала неадминистратором')
            except:
                pass
            
            embed = discord.Embed(
                title='⚠️ НАРУШЕНИЕ БЕЗОПАСНОСТИ',
                color=discord.Color.dark_red(),
                timestamp=datetime.now()
            )
            embed.add_field(name='👤 Нарушитель', value=f'{creator.mention}\n`{creator}`', inline=True)
            embed.add_field(name='📂 Действие', value='Попытка создания канала', inline=False)
            embed.add_field(name='🗑️ Созданный канал', value=channel.name, inline=True)
            embed.add_field(name='📋 Результат', value='• Канал удален\n• Все роли сняты', inline=False)
            if removed_roles:
                embed.add_field(name='🎭 Снятые роли', value=', '.join(removed_roles), inline=False)
            await send_log(channel.guild.id, embed)
            
            try:
                await creator.send(f'🚫 Вы были наказаны на сервере **{channel.guild.name}** за создание канала без прав.\nС вас сняты все роли.')
            except:
                pass
            
            return
    
    if str(channel.guild.id) in logs_config:
        embed = discord.Embed(
            title='🆕 СОЗДАН КАНАЛ',
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        embed.add_field(name='📌 Название', value=channel.mention, inline=True)
        embed.add_field(name='🆔 ID', value=channel.id, inline=True)
        embed.add_field(name='📂 Тип', value=str(channel.type).split('.')[-1], inline=True)
        embed.set_footer(text=f'Сервер: {channel.guild.name}')
        await send_log(channel.guild.id, embed)

@bot.event
async def on_guild_channel_delete(channel):
    await backup_channel(channel)
    
    async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
        deleter = entry.user
        
        if not deleter.guild_permissions.administrator and deleter != channel.guild.owner:
            removed_roles = []
            for role in deleter.roles:
                try:
                    await deleter.remove_roles(role, reason='Нарушение: удаление канала без прав')
                    removed_roles.append(role.name)
                except:
                    pass
            
            restored_channel = await restore_channel(channel.guild, channel.id)
            
            embed = discord.Embed(
                title='⚠️ НАРУШЕНИЕ БЕЗОПАСНОСТИ',
                color=discord.Color.dark_red(),
                timestamp=datetime.now()
            )
            embed.add_field(name='👤 Нарушитель', value=f'{deleter.mention}\n`{deleter}`', inline=True)
            embed.add_field(name='📂 Действие', value='Попытка удаления канала', inline=False)
            embed.add_field(name='🗑️ Удаленный канал', value=channel.name, inline=True)
            embed.add_field(name='📋 Результат', value='• Канал восстановлен\n• Все роли сняты', inline=False)
            if removed_roles:
                embed.add_field(name='🎭 Снятые роли', value=', '.join(removed_roles), inline=False)
            if restored_channel:
                embed.add_field(name='🔄 Восстановленный канал', value=restored_channel.mention, inline=True)
            await send_log(channel.guild.id, embed)
            
            try:
                await deleter.send(f'🚫 Вы были наказаны на сервере **{channel.guild.name}** за удаление канала без прав.\nС вас сняты все роли, канал восстановлен.')
            except:
                pass
            
            return
    
    if str(channel.guild.id) in logs_config:
        embed = discord.Embed(
            title='🗑️ УДАЛЕН КАНАЛ',
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        embed.add_field(name='📌 Название', value=channel.name, inline=True)
        embed.add_field(name='🆔 ID', value=channel.id, inline=True)
        embed.add_field(name='📂 Тип', value=str(channel.type).split('.')[-1], inline=True)
        embed.set_footer(text=f'Сервер: {channel.guild.name}')
        await send_log(channel.guild.id, embed)

@bot.event
async def on_guild_role_create(role):
    if str(role.guild.id) in logs_config:
        async for entry in role.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_create):
            moderator = entry.user
            break
        else:
            moderator = None
        
        embed = discord.Embed(
            title='🆕 СОЗДАНА РОЛЬ',
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        embed.add_field(name='🎭 Название роли', value=role.mention, inline=True)
        embed.add_field(name='🆔 ID', value=role.id, inline=True)
        embed.add_field(name='🎨 Цвет', value=str(role.color), inline=True)
        embed.add_field(name='🛡️ Кто создал', value=f'{moderator.mention}\n`{moderator}`' if moderator else 'Неизвестно', inline=True)
        embed.set_footer(text=f'Сервер: {role.guild.name}')
        await send_log(role.guild.id, embed)

@bot.event
async def on_guild_role_delete(role):
    if str(role.guild.id) in logs_config:
        async for entry in role.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_delete):
            moderator = entry.user
            break
        else:
            moderator = None
        
        embed = discord.Embed(
            title='🗑️ УДАЛЕНА РОЛЬ',
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        embed.add_field(name='🎭 Название роли', value=role.name, inline=True)
        embed.add_field(name='🆔 ID', value=role.id, inline=True)
        embed.add_field(name='🛡️ Кто удалил', value=f'{moderator.mention}\n`{moderator}`' if moderator else 'Неизвестно', inline=True)
        embed.set_footer(text=f'Сервер: {role.guild.name}')
        await send_log(role.guild.id, embed)

@bot.event
async def on_guild_role_update(before, after):
    if str(before.guild.id) in logs_config:
        changes = []
        
        if before.name != after.name:
            changes.append(f'📝 **Название:** {before.name} → {after.name}')
        
        if before.color != after.color:
            changes.append(f'🎨 **Цвет:** {before.color} → {after.color}')
        
        if before.permissions != after.permissions:
            changes.append(f'🔧 **Права:** были изменены')
        
        if changes:
            async for entry in before.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_update):
                moderator = entry.user
                break
            else:
                moderator = None
            
            embed = discord.Embed(
                title='✏️ ИЗМЕНЕНА РОЛЬ',
                color=discord.Color.gold(),
                timestamp=datetime.now()
            )
            embed.add_field(name='🎭 Роль', value=after.mention, inline=True)
            embed.add_field(name='📋 Изменения', value='\n'.join(changes), inline=False)
            embed.add_field(name='🛡️ Кто изменил', value=f'{moderator.mention}\n`{moderator}`' if moderator else 'Неизвестно', inline=True)
            embed.set_footer(text=f'Сервер: {before.guild.name}')
            await send_log(before.guild.id, embed)

@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id == bot.user.id:
        return
    
    if lockdown_active.get(payload.guild_id, False):
        guild = bot.get_guild(payload.guild_id)
        if guild:
            member = guild.get_member(payload.user_id)
            if member and not member.guild_permissions.administrator:
                try:
                    channel = guild.get_channel(payload.channel_id)
                    message = await channel.fetch_message(payload.message_id)
                    await message.remove_reaction(payload.emoji, member)
                except:
                    pass
                return
    
    guild_id = str(payload.guild_id)
    if guild_id in verify_config:
        verify_data = verify_config[guild_id]
        if payload.channel_id == verify_data['channel'] and payload.message_id == verify_data['message_id'] and str(payload.emoji) == verify_data['emoji']:
            guild = bot.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id)
            role = guild.get_role(verify_data['role'])
            
            if role not in member.roles:
                await member.add_roles(role)

@bot.event
async def on_raw_reaction_remove(payload):
    if payload.user_id == bot.user.id:
        return
    
    guild_id = str(payload.guild_id)
    if guild_id in verify_config:
        verify_data = verify_config[guild_id]
        if payload.channel_id == verify_data['channel'] and payload.message_id == verify_data['message_id'] and str(payload.emoji) == verify_data['emoji']:
            guild = bot.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id)
            role = guild.get_role(verify_data['role'])
            
            if role in member.roles:
                await member.remove_roles(role)

@bot.tree.command(name='log', description='Установить канал для логов')
async def log(interaction: discord.Interaction, канал: discord.TextChannel):
    await interaction.response.defer(ephemeral=True)
    
    if not interaction.user.guild_permissions.administrator:
        await interaction.followup.send('❌ У вас нет прав для настройки логов', ephemeral=True)
        return
    
    logs_config[str(interaction.guild.id)] = канал.id
    save_logs_config()
    
    embed = discord.Embed(
        title='✅ ЛОГИ НАСТРОЕНЫ',
        color=discord.Color.green(),
        timestamp=datetime.now()
    )
    embed.add_field(name='📌 Канал логов', value=канал.mention, inline=True)
    embed.add_field(name='👤 Настроил', value=interaction.user.mention, inline=True)
    embed.add_field(name='📋 Статус', value='Все события будут логироваться', inline=True)
    embed.set_footer(text=f'Сервер: {interaction.guild.name}')
    
    await interaction.followup.send(embed=embed, ephemeral=True)
    
    test_embed = discord.Embed(
        title='📋 СИСТЕМА ЛОГОВ АКТИВИРОВАНА',
        color=discord.Color.green(),
        timestamp=datetime.now()
    )
    test_embed.add_field(name='📌 Информация', value='Бот будет отправлять логи следующих событий:', inline=False)
    test_embed.add_field(name='🗑️', value='Удаление/изменение сообщений', inline=True)
    test_embed.add_field(name='🎭', value='Выдача/снятие ролей, создание/удаление/изменение ролей', inline=True)
    test_embed.add_field(name='📂', value='Создание/удаление каналов (с защитой)', inline=True)
    test_embed.add_field(name='🔇', value='Заглушка/разглушка (наушники/микрофон)', inline=True)
    test_embed.add_field(name='👢', value='Кики', inline=True)
    test_embed.add_field(name='🔨', value='Баны/разбаны', inline=True)
    test_embed.add_field(name='🤖', value='Автомодерация (спам/ссылки/упоминания) и защита от ботов', inline=True)
    test_embed.add_field(name='⏰', value='Каждое предупреждение снимается через 5 дней', inline=True)
    test_embed.add_field(name='🚨', value='Анти-рейд система (обнаружение и защита)', inline=True)
    test_embed.add_field(name='🔒', value='Защита каналов (только админы/овнер могут создавать/удалять)', inline=True)
    test_embed.add_field(name='🔗', value='Логи создания ссылок-приглашений', inline=True)
    test_embed.set_footer(text='Для отключения логов используйте /unlog')
    
    await канал.send(embed=test_embed)

@bot.tree.command(name='unlog', description='Отключить логи на сервере')
async def unlog(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    
    if not interaction.user.guild_permissions.administrator:
        await interaction.followup.send('❌ У вас нет прав для отключения логов', ephemeral=True)
        return
    
    if str(interaction.guild.id) in logs_config:
        del logs_config[str(interaction.guild.id)]
        save_logs_config()
        
        embed = discord.Embed(
            title='❌ ЛОГИ ОТКЛЮЧЕНЫ',
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        embed.add_field(name='👤 Отключил', value=interaction.user.mention, inline=True)
        embed.add_field(name='📋 Статус', value='Логи больше не отправляются', inline=True)
        embed.set_footer(text=f'Сервер: {interaction.guild.name}')
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    else:
        await interaction.followup.send('❌ Логи не были настроены на этом сервере', ephemeral=True)

async def log_punishment(guild_id, embed):
    await send_log(guild_id, embed)

@bot.tree.command(name='warn', description='Выдать предупреждение участнику')
async def warn(interaction: discord.Interaction, участник: discord.Member, причина: str):
    await interaction.response.defer(ephemeral=True)
    
    if not has_command_access(interaction.user, 'warn'):
        await interaction.followup.send('❌ У вас нет прав на выдачу предупреждений', ephemeral=True)
        return
    
    if not can_target(interaction.user, участник):
        await interaction.followup.send('❌ Вы не можете выдать предупреждение участнику с такой же или высшей ролью', ephemeral=True)
        return
    
    is_muted, warn_count = await add_warn_and_check(interaction.guild.id, участник.id, interaction.user.id, причина, False)
    
    if warn_count >= 3 and not is_muted:
        await interaction.followup.send(f'❌ У {участник.mention} уже есть 3 предупреждения. Нельзя выдать больше 3.', ephemeral=True)
        return
    
    embed = discord.Embed(
        title='⚠️ ПРЕДУПРЕЖДЕНИЕ ВЫДАНО',
        color=discord.Color.orange(),
        timestamp=datetime.now()
    )
    embed.add_field(name='👤 Участник', value=участник.mention, inline=True)
    embed.add_field(name='🛡️ Модератор', value=interaction.user.mention, inline=True)
    embed.add_field(name='📝 Причина', value=причина, inline=False)
    embed.add_field(name='⚠️ Предупреждения', value=f'{warn_count}/3', inline=True)
    
    await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(name='unwarn', description='Снять предупреждение с участника')
async def unwarn(interaction: discord.Interaction, участник: discord.Member, номер_предупреждения: int):
    await interaction.response.defer(ephemeral=True)
    
    if not has_command_access(interaction.user, 'unwarn'):
        await interaction.followup.send('❌ У вас нет прав на снятие предупреждений', ephemeral=True)
        return
    
    if not can_target(interaction.user, участник):
        await interaction.followup.send('❌ Вы не можете снять предупреждение участнику с такой же или высшей ролью', ephemeral=True)
        return
    
    user_id = str(участник.id)
    guild_id = str(interaction.guild.id)
    
    if guild_id not in warns or user_id not in warns[guild_id]:
        await interaction.followup.send('❌ У этого участника нет предупреждений', ephemeral=True)
        return
    
    user_warns = warns[guild_id][user_id]
    warn_to_remove = None
    
    for warn in user_warns:
        if warn['id'] == номер_предупреждения:
            warn_to_remove = warn
            break
    
    if warn_to_remove is None:
        await interaction.followup.send(f'❌ Предупреждение с номером {номер_предупреждения} не найдено', ephemeral=True)
        return
    
    user_warns.remove(warn_to_remove)
    
    for i, warn in enumerate(user_warns, 1):
        warn['id'] = i
    
    if not user_warns:
        del warns[guild_id][user_id]
    
    save_warns()
    
    log_embed = discord.Embed(
        title='✅ СНЯТО ПРЕДУПРЕЖДЕНИЕ',
        color=discord.Color.green(),
        timestamp=datetime.now()
    )
    log_embed.set_thumbnail(url=участник.avatar.url if участник.avatar else участник.default_avatar.url)
    log_embed.add_field(name='👤 Участник', value=f'{участник.mention}\n`{участник}`', inline=True)
    log_embed.add_field(name='🛡️ Модератор', value=f'{interaction.user.mention}\n`{interaction.user}`', inline=True)
    log_embed.add_field(name='✅ Снято', value=f'Предупреждение №{номер_предупреждения}', inline=True)
    log_embed.add_field(name='📝 Причина предупреждения', value=f'```{warn_to_remove["reason"]}```', inline=False)
    await log_punishment(interaction.guild.id, log_embed)
    
    embed = discord.Embed(
        title='✅ ПРЕДУПРЕЖДЕНИЕ СНЯТО',
        color=discord.Color.green(),
        timestamp=datetime.now()
    )
    embed.add_field(name='👤 Участник', value=участник.mention, inline=True)
    embed.add_field(name='🛡️ Модератор', value=interaction.user.mention, inline=True)
    embed.add_field(name='✅ Снято предупреждение', value=f'№{номер_предупреждения}', inline=True)
    
    await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(name='warns', description='Показать актуальные предупреждения участника')
async def warns_command(interaction: discord.Interaction, участник: discord.Member = None):
    await interaction.response.defer(ephemeral=True)
    
    if not has_command_access(interaction.user, 'warns'):
        await interaction.followup.send('❌ У вас нет прав на просмотр предупреждений', ephemeral=True)
        return
    
    if участник is None:
        участник = interaction.user
    
    user_id = str(участник.id)
    guild_id = str(interaction.guild.id)
    
    if guild_id not in warns or user_id not in warns[guild_id]:
        await interaction.followup.send(f'📋 У {участник.mention} нет предупреждений **0/3**', ephemeral=True)
        return
    
    user_warns = warns[guild_id][user_id]
    
    if len(user_warns) == 0:
        await interaction.followup.send(f'📋 У {участник.mention} нет предупреждений **0/3**', ephemeral=True)
        return
    
    embed = discord.Embed(
        title=f'⚠️ ПРЕДУПРЕЖДЕНИЯ {участник.name}',
        color=discord.Color.orange(),
        timestamp=datetime.now()
    )
    embed.set_thumbnail(url=участник.avatar.url if участник.avatar else участник.default_avatar.url)
    
    for warn in user_warns:
        moderator = interaction.guild.get_member(warn['moderator'])
        if moderator and moderator.id == bot.user.id:
            mod_name = 'Автомодерация'
        else:
            mod_name = moderator.name if moderator else 'Неизвестен'
        embed.add_field(
            name=f'⚠️ Предупреждение №{warn["id"]}',
            value=f'📝 **Причина:** {warn["reason"]}\n🛡️ **Модератор:** {mod_name}\n📅 **Дата:** {warn["date"]}',
            inline=False
        )
    
    embed.set_footer(text=f'Всего: {len(user_warns)}/3 предупреждений | Каждое предупреждение снимается через 5 дней')
    await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(name='mute', description='Выдать мут участнику')
async def mute(interaction: discord.Interaction, участник: discord.Member, время: str, причина: str):
    await interaction.response.defer(ephemeral=True)
    
    if not has_command_access(interaction.user, 'mute'):
        await interaction.followup.send('❌ У вас нет прав на выдачу мута', ephemeral=True)
        return
    
    if not can_mute_target(interaction.user, участник):
        await interaction.followup.send('❌ Вы не можете выдать мут участнику с такой же или высшей ролью', ephemeral=True)
        return
    
    if not interaction.guild.me.guild_permissions.moderate_members:
        await interaction.followup.send('❌ У бота нет права "Управлять участниками" (Moderate Members)', ephemeral=True)
        return
    
    time_seconds = 0
    
    if время.endswith('с'):
        time_seconds = int(время[:-1])
    elif время.endswith('м'):
        time_seconds = int(время[:-1]) * 60
    elif время.endswith('ч'):
        time_seconds = int(время[:-1]) * 3600
    elif время.endswith('д'):
        time_seconds = int(время[:-1]) * 86400
    else:
        await interaction.followup.send('❌ Неверный формат времени. Используйте: 10с, 5м, 2ч, 1д', ephemeral=True)
        return
    
    if time_seconds > 2419200:
        await interaction.followup.send('❌ Максимальное время мута - 28 дней', ephemeral=True)
        return
    
    days = time_seconds // 86400
    hours = (time_seconds % 86400) // 3600
    minutes = (time_seconds % 3600) // 60
    seconds = time_seconds % 60
    
    time_text = []
    if days > 0: time_text.append(f'{days}д')
    if hours > 0: time_text.append(f'{hours}ч')
    if minutes > 0: time_text.append(f'{minutes}м')
    if seconds > 0: time_text.append(f'{seconds}с')
    time_string = ' '.join(time_text) if time_text else '0с'
    
    try:
        await участник.timeout(discord.utils.utcnow() + timedelta(seconds=time_seconds), reason=причина)
    except discord.Forbidden:
        await interaction.followup.send('❌ Боту не хватает прав для выдачи мута. Убедитесь, что роль бота выше роли участника', ephemeral=True)
        return
    
    await send_dm(участник, '🔇 ВЫ ЗАМУЧЕНЫ', f'Время: {time_string}\nПричина: {причина}', None)
    
    log_embed = discord.Embed(
        title='🔇 ВЫДАН МУТ',
        color=discord.Color.dark_red(),
        timestamp=datetime.now()
    )
    log_embed.set_thumbnail(url=участник.avatar.url if участник.avatar else участник.default_avatar.url)
    log_embed.add_field(name='👤 Участник', value=f'{участник.mention}\n`{участник}`', inline=True)
    log_embed.add_field(name='🛡️ Модератор', value=f'{interaction.user.mention}\n`{interaction.user}`', inline=True)
    log_embed.add_field(name='⏰ Длительность', value=f'**{time_string}**', inline=True)
    log_embed.add_field(name='📝 Причина', value=f'```{причина}```', inline=False)
    await log_punishment(interaction.guild.id, log_embed)
    
    embed = discord.Embed(
        title='🔇 ПОЛЬЗОВАТЕЛЬ ЗАМУЧЕН',
        color=discord.Color.red(),
        timestamp=datetime.now()
    )
    embed.add_field(name='👤 Участник', value=участник.mention, inline=True)
    embed.add_field(name='🛡️ Модератор', value=interaction.user.mention, inline=True)
    embed.add_field(name='⏰ Время', value=time_string, inline=True)
    embed.add_field(name='📝 Причина', value=причина, inline=False)
    
    await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(name='unmute', description='Снять мут с участника')
async def unmute(interaction: discord.Interaction, участник: discord.Member):
    await interaction.response.defer(ephemeral=True)
    
    if not has_command_access(interaction.user, 'unmute'):
        await interaction.followup.send('❌ У вас нет прав на снятие мута', ephemeral=True)
        return
    
    if not can_target(interaction.user, участник):
        await interaction.followup.send('❌ Вы не можете снять мут участнику с такой же или высшей ролью', ephemeral=True)
        return
    
    if участник.timed_out_until is None:
        await interaction.followup.send('❌ У этого участника нет мута', ephemeral=True)
        return
    
    try:
        await участник.timeout(None)
    except discord.Forbidden:
        await interaction.followup.send('❌ Боту не хватает прав для снятия мута', ephemeral=True)
        return
    
    log_embed = discord.Embed(
        title='🔊 СНЯТ МУТ',
        color=discord.Color.green(),
        timestamp=datetime.now()
    )
    log_embed.set_thumbnail(url=участник.avatar.url if участник.avatar else участник.default_avatar.url)
    log_embed.add_field(name='👤 Участник', value=f'{участник.mention}\n`{участник}`', inline=True)
    log_embed.add_field(name='🛡️ Модератор', value=f'{interaction.user.mention}\n`{interaction.user}`', inline=True)
    await log_punishment(interaction.guild.id, log_embed)
    
    embed = discord.Embed(
        title='🔊 МУТ СНЯТ',
        color=discord.Color.green(),
        timestamp=datetime.now()
    )
    embed.add_field(name='👤 Участник', value=участник.mention, inline=True)
    embed.add_field(name='🛡️ Модератор', value=interaction.user.mention, inline=True)
    
    await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(name='kick', description='Выдать кик участнику')
async def kick(interaction: discord.Interaction, участник: discord.Member, причина: str):
    await interaction.response.defer(ephemeral=True)
    
    if not has_command_access(interaction.user, 'kick'):
        await interaction.followup.send('❌ У вас нет прав на выдачу кика', ephemeral=True)
        return
    
    if not can_target(interaction.user, участник):
        await interaction.followup.send('❌ Вы не можете кикнуть участника с такой же или высшей ролью', ephemeral=True)
        return
    
    await send_dm(участник, '👢 ВАС КИКНУЛИ С СЕРВЕРА', f'Причина: {причина}', None)
    
    await участник.kick(reason=причина)
    
    log_embed = discord.Embed(
        title='👢 ВЫДАН КИК',
        color=discord.Color.orange(),
        timestamp=datetime.now()
    )
    log_embed.set_thumbnail(url=участник.avatar.url if участник.avatar else участник.default_avatar.url)
    log_embed.add_field(name='👤 Участник', value=f'{участник.mention}\n`{участник}`', inline=True)
    log_embed.add_field(name='🛡️ Модератор', value=f'{interaction.user.mention}\n`{interaction.user}`', inline=True)
    log_embed.add_field(name='📝 Причина', value=f'```{причина}```', inline=False)
    await log_punishment(interaction.guild.id, log_embed)
    
    embed = discord.Embed(
        title='👢 ПОЛЬЗОВАТЕЛЬ КИКНУТ',
        color=discord.Color.orange(),
        timestamp=datetime.now()
    )
    embed.add_field(name='👤 Участник', value=участник.mention, inline=True)
    embed.add_field(name='🛡️ Модератор', value=interaction.user.mention, inline=True)
    embed.add_field(name='📝 Причина', value=причина, inline=False)
    
    await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(name='ban', description='Выдать бан участнику')
async def ban(interaction: discord.Interaction, участник: discord.Member, причина: str):
    await interaction.response.defer(ephemeral=True)
    
    if not has_command_access(interaction.user, 'ban'):
        await interaction.followup.send('❌ У вас нет прав на выдачу бана', ephemeral=True)
        return
    
    if not can_target(interaction.user, участник):
        await interaction.followup.send('❌ Вы не можете забанить участника с такой же или высшей ролью', ephemeral=True)
        return
    
    await send_dm(участник, '🔨 ВАС ЗАБАНИЛИ НА СЕРВЕРЕ', f'Причина: {причина}', None)
    
    await участник.ban(reason=причина)
    
    log_embed = discord.Embed(
        title='🔨 ВЫДАН БАН',
        color=discord.Color.dark_red(),
        timestamp=datetime.now()
    )
    log_embed.set_thumbnail(url=участник.avatar.url if участник.avatar else участник.default_avatar.url)
    log_embed.add_field(name='👤 Участник', value=f'{участник.mention}\n`{участник}`', inline=True)
    log_embed.add_field(name='🛡️ Модератор', value=f'{interaction.user.mention}\n`{interaction.user}`', inline=True)
    log_embed.add_field(name='📝 Причина', value=f'```{причина}```', inline=False)
    await log_punishment(interaction.guild.id, log_embed)
    
    embed = discord.Embed(
        title='🔨 ПОЛЬЗОВАТЕЛЬ ЗАБАНЕН',
        color=discord.Color.dark_red(),
        timestamp=datetime.now()
    )
    embed.add_field(name='👤 Участник', value=участник.mention, inline=True)
    embed.add_field(name='🛡️ Модератор', value=interaction.user.mention, inline=True)
    embed.add_field(name='📝 Причина', value=причина, inline=False)
    
    await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(name='unban', description='Снять бан с участника')
async def unban(interaction: discord.Interaction, user_id: str, причина: str):
    await interaction.response.defer(ephemeral=True)
    
    if not has_command_access(interaction.user, 'unban'):
        await interaction.followup.send('❌ У вас нет прав на снятие бана', ephemeral=True)
        return
    
    try:
        user = await bot.fetch_user(int(user_id))
        await interaction.guild.unban(user, reason=причина)
        
        log_embed = discord.Embed(
            title='✅ СНЯТ БАН',
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        log_embed.add_field(name='👤 Пользователь', value=f'{user.mention}\n`{user}`', inline=True)
        log_embed.add_field(name='🛡️ Модератор', value=f'{interaction.user.mention}\n`{interaction.user}`', inline=True)
        log_embed.add_field(name='📝 Причина', value=f'```{причина}```', inline=False)
        await log_punishment(interaction.guild.id, log_embed)
        
        embed = discord.Embed(
            title='✅ БАН СНЯТ',
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        embed.add_field(name='👤 Пользователь', value=user.mention, inline=True)
        embed.add_field(name='🛡️ Модератор', value=interaction.user.mention, inline=True)
        embed.add_field(name='📝 Причина', value=причина, inline=False)
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    except:
        await interaction.followup.send('❌ Неверный ID пользователя или пользователь не забанен', ephemeral=True)

@bot.tree.command(name='clear', description='Очистить сообщения в канале')
async def clear(interaction: discord.Interaction, количество: int):
    await interaction.response.defer(ephemeral=True)
    
    if not has_command_access(interaction.user, 'clear'):
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.followup.send('❌ У вас нет прав на очистку сообщений', ephemeral=True)
            return
    
    if количество <= 0:
        await interaction.followup.send('❌ Укажите число больше 0', ephemeral=True)
        return
    
    if количество > 500:
        await interaction.followup.send('❌ Максимум можно очистить 500 сообщений', ephemeral=True)
        return
    
    deleted = await interaction.channel.purge(limit=количество)
    
    log_embed = discord.Embed(
        title='🧹 ОЧИЩЕНЫ СООБЩЕНИЯ',
        color=discord.Color.purple(),
        timestamp=datetime.now()
    )
    log_embed.add_field(name='📌 Канал', value=interaction.channel.mention, inline=True)
    log_embed.add_field(name='🛡️ Модератор', value=f'{interaction.user.mention}\n`{interaction.user}`', inline=True)
    log_embed.add_field(name='📊 Количество', value=f'**{len(deleted)}** сообщений', inline=True)
    await log_punishment(interaction.guild.id, log_embed)
    
    await interaction.followup.send(f'✅ Очищено {len(deleted)} сообщений', ephemeral=True)

@bot.tree.command(name='verification', description='Настроить систему верификации')
async def verification(interaction: discord.Interaction, канал: discord.TextChannel, роль: discord.Role, сообщение: str, эмоция: str):
    await interaction.response.defer(ephemeral=True)
    
    if not interaction.user.guild_permissions.administrator:
        await interaction.followup.send('❌ У вас нет прав для настройки верификации', ephemeral=True)
        return
    
    embed = discord.Embed(
        description=сообщение,
        color=discord.Color.blue()
    )
    
    msg = await канал.send(embed=embed)
    await msg.add_reaction(эмоция)
    
    verify_config[str(interaction.guild.id)] = {
        'channel': канал.id,
        'role': роль.id,
        'emoji': эмоция,
        'message_id': msg.id
    }
    save_verify_config()
    
    result_embed = discord.Embed(
        title='✅ ВЕРИФИКАЦИЯ НАСТРОЕНА',
        color=discord.Color.green(),
        timestamp=datetime.now()
    )
    result_embed.add_field(name='📌 Канал', value=канал.mention, inline=True)
    result_embed.add_field(name='🎭 Роль', value=роль.mention, inline=True)
    result_embed.add_field(name='😀 Эмодзи', value=эмоция, inline=True)
    
    await interaction.followup.send(embed=result_embed, ephemeral=True)

@bot.tree.command(name='msg', description='Отправить сообщение от имени бота в несколько каналов')
async def msg(interaction: discord.Interaction, каналы: str, сообщение: str, заголовок: str = None, тег: discord.Role = None, фото: discord.Attachment = None):
    await interaction.response.defer(ephemeral=True)
    
    if not has_command_access(interaction.user, 'msg'):
        if not interaction.user.guild_permissions.administrator:
            await interaction.followup.send('❌ У вас нет прав для отправки сообщений от имени бота', ephemeral=True)
            return
    
    channel_mentions = re.findall(r'<#(\d+)>', каналы)
    channels_to_send = []
    
    for channel_id_str in channel_mentions:
        channel = interaction.guild.get_channel(int(channel_id_str))
        if channel and isinstance(channel, discord.TextChannel):
            channels_to_send.append(channel)
    
    if not channels_to_send:
        await interaction.followup.send('❌ Не найдено ни одного валидного текстового канала. Упомяните каналы через #', ephemeral=True)
        return
    
    if заголовок:
        embed = discord.Embed(
            title=заголовок,
            description=сообщение,
            color=discord.Color.blue()
        )
    else:
        embed = discord.Embed(
            description=сообщение,
            color=discord.Color.blue()
        )
    
    if фото:
        embed.set_image(url=фото.url)
    
    success_count = 0
    fail_count = 0
    
    for channel in channels_to_send:
        try:
            if тег:
                await channel.send(embed=embed)
                await channel.send(тег.mention, allowed_mentions=discord.AllowedMentions(roles=True))
            else:
                await channel.send(embed=embed)
            success_count += 1
        except Exception as e:
            fail_count += 1
            print(f'Ошибка отправки в {channel.name}: {e}')
    
    channel_list = '\n'.join([f'• {ch.mention}' for ch in channels_to_send[:10]])
    if len(channels_to_send) > 10:
        channel_list += f'\n• ... и ещё {len(channels_to_send) - 10} каналов'
    
    response_embed = discord.Embed(
        title='✅ СООБЩЕНИЕ ОТПРАВЛЕНО',
        color=discord.Color.green(),
        timestamp=datetime.now()
    )
    response_embed.add_field(name='📌 Каналы', value=channel_list, inline=False)
    response_embed.add_field(name='✅ Успешно', value=str(success_count), inline=True)
    response_embed.add_field(name='❌ Ошибок', value=str(fail_count), inline=True)
    if заголовок:
        response_embed.add_field(name='📝 Заголовок', value=заголовок, inline=True)
    if тег:
        response_embed.add_field(name='🔔 Тег', value=тег.mention, inline=True)
    if фото:
        response_embed.add_field(name='🖼️ Фото', value='Прикреплено', inline=True)
    
    await interaction.followup.send(embed=response_embed, ephemeral=True)

@bot.tree.command(name='lockdown', description='Включить режим Lockdown вручную')
async def lockdown(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    
    if not interaction.user.guild_permissions.administrator:
        await interaction.followup.send('❌ У вас нет прав для включения lockdown', ephemeral=True)
        return
    
    if lockdown_active.get(interaction.guild.id, False):
        await interaction.followup.send('❌ Режим lockdown уже активен', ephemeral=True)
        return
    
    await activate_lockdown(interaction.guild.id, 'ручное включение')
    
    embed = discord.Embed(
        title='🔒 РЕЖИМ LOCKDOWN ВКЛЮЧЕН ВРУЧНУЮ',
        color=discord.Color.dark_red(),
        timestamp=datetime.now()
    )
    embed.add_field(name='👤 Модератор', value=interaction.user.mention, inline=True)
    embed.add_field(name='⏰ Длительность', value='35 минут', inline=False)
    
    await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(name='unlockdown', description='Отключить режим Lockdown')
async def unlockdown(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    
    if not interaction.user.guild_permissions.administrator:
        await interaction.followup.send('❌ У вас нет прав для отключения lockdown', ephemeral=True)
        return
    
    if not lockdown_active.get(interaction.guild.id, False):
        await interaction.followup.send('❌ Режим lockdown не активен', ephemeral=True)
        return
    
    await deactivate_lockdown(interaction.guild.id)
    
    embed = discord.Embed(
        title='🔓 РЕЖИМ LOCKDOWN ОТКЛЮЧЕН',
        color=discord.Color.green(),
        timestamp=datetime.now()
    )
    embed.add_field(name='👤 Модератор', value=interaction.user.mention, inline=True)
    
    await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(name='commands', description='Выдать доступ к командам')
async def commands_access_cmd(interaction: discord.Interaction, команды: str, пользователь: discord.Member = None, роль: discord.Role = None):
    await interaction.response.defer(ephemeral=True)
    
    if not interaction.user.guild_permissions.administrator:
        await interaction.followup.send('❌ У вас нет прав для выдачи доступа к командам', ephemeral=True)
        return
    
    guild_id_str = str(interaction.guild.id)
    
    if guild_id_str not in commands_access:
        commands_access[guild_id_str] = {}
    
    command_list = [cmd.strip() for cmd in команды.split(',')]
    
    if пользователь:
        for command_name in command_list:
            if command_name not in commands_access[guild_id_str]:
                commands_access[guild_id_str][command_name] = {'users': [], 'roles': []}
            
            if str(пользователь.id) not in commands_access[guild_id_str][command_name]['users']:
                commands_access[guild_id_str][command_name]['users'].append(str(пользователь.id))
        
        save_commands_access()
        embed = discord.Embed(
            title='✅ ДОСТУП ВЫДАН',
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        embed.add_field(name='👤 Пользователь', value=пользователь.mention, inline=True)
        embed.add_field(name='📋 Команды', value=f'/{", /".join(command_list)}', inline=False)
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    elif роль:
        for command_name in command_list:
            if command_name not in commands_access[guild_id_str]:
                commands_access[guild_id_str][command_name] = {'users': [], 'roles': []}
            
            if str(роль.id) not in commands_access[guild_id_str][command_name]['roles']:
                commands_access[guild_id_str][command_name]['roles'].append(str(роль.id))
        
        save_commands_access()
        embed = discord.Embed(
            title='✅ ДОСТУП ВЫДАН',
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        embed.add_field(name='🎭 Роль', value=роль.mention, inline=True)
        embed.add_field(name='📋 Команды', value=f'/{", /".join(command_list)}', inline=False)
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    else:
        await interaction.followup.send('❌ Укажите пользователя или роль для выдачи доступа', ephemeral=True)

@bot.tree.command(name='uncommands', description='Забрать доступ к командам')
async def uncommands_cmd(interaction: discord.Interaction, команды: str, пользователь: discord.Member = None, роль: discord.Role = None):
    await interaction.response.defer(ephemeral=True)
    
    if not interaction.user.guild_permissions.administrator:
        await interaction.followup.send('❌ У вас нет прав для удаления доступа к командам', ephemeral=True)
        return
    
    guild_id_str = str(interaction.guild.id)
    
    if guild_id_str not in commands_access:
        commands_access[guild_id_str] = {}
    
    command_list = [cmd.strip() for cmd in команды.split(',')]
    
    if пользователь:
        for command_name in command_list:
            if command_name in commands_access[guild_id_str]:
                if str(пользователь.id) in commands_access[guild_id_str][command_name].get('users', []):
                    commands_access[guild_id_str][command_name]['users'].remove(str(пользователь.id))
        
        save_commands_access()
        embed = discord.Embed(
            title='✅ ДОСТУП УДАЛЕН',
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        embed.add_field(name='👤 Пользователь', value=пользователь.mention, inline=True)
        embed.add_field(name='📋 Команды', value=f'/{", /".join(command_list)}', inline=False)
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    elif роль:
        for command_name in command_list:
            if command_name in commands_access[guild_id_str]:
                if str(роль.id) in commands_access[guild_id_str][command_name].get('roles', []):
                    commands_access[guild_id_str][command_name]['roles'].remove(str(роль.id))
        
        save_commands_access()
        embed = discord.Embed(
            title='✅ ДОСТУП УДАЛЕН',
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        embed.add_field(name='🎭 Роль', value=роль.mention, inline=True)
        embed.add_field(name='📋 Команды', value=f'/{", /".join(command_list)}', inline=False)
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    else:
        await interaction.followup.send('❌ Укажите пользователя или роль для удаления доступа', ephemeral=True)

@bot.tree.command(name='infcommands', description='Показать команды доступные игроку или роли')
async def infcommands(interaction: discord.Interaction, игрок: discord.Member = None, роль: discord.Role = None):
    await interaction.response.defer(ephemeral=True)
    
    if not interaction.user.guild_permissions.administrator:
        await interaction.followup.send('❌ У вас нет прав для просмотра этой информации', ephemeral=True)
        return
    
    guild_id_str = str(interaction.guild.id)
    
    if guild_id_str not in commands_access:
        commands_access[guild_id_str] = {}
    
    available_commands = []
    
    if игрок:
        target_name = f'{игрок.display_name}'
        target_type = 'пользователя'
        
        for cmd_name, access_data in commands_access[guild_id_str].items():
            if cmd_name == 'all':
                continue
            
            if str(игрок.id) in access_data.get('users', []):
                available_commands.append(cmd_name)
                continue
            
            for role in игрок.roles:
                if str(role.id) in access_data.get('roles', []):
                    available_commands.append(cmd_name)
                    break
        
        if 'all' in commands_access[guild_id_str]:
            if str(игрок.id) in commands_access[guild_id_str]['all'].get('users', []):
                for cmd_name in commands_access[guild_id_str].keys():
                    if cmd_name != 'all' and cmd_name not in available_commands:
                        available_commands.append(cmd_name)
            for role in игрок.roles:
                if str(role.id) in commands_access[guild_id_str]['all'].get('roles', []):
                    for cmd_name in commands_access[guild_id_str].keys():
                        if cmd_name != 'all' and cmd_name not in available_commands:
                            available_commands.append(cmd_name)
    
    elif роль:
        target_name = f'{роль.name}'
        target_type = 'роли'
        
        for cmd_name, access_data in commands_access[guild_id_str].items():
            if cmd_name == 'all':
                continue
            
            if str(роль.id) in access_data.get('roles', []):
                available_commands.append(cmd_name)
        
        if 'all' in commands_access[guild_id_str]:
            if str(роль.id) in commands_access[guild_id_str]['all'].get('roles', []):
                for cmd_name in commands_access[guild_id_str].keys():
                    if cmd_name != 'all' and cmd_name not in available_commands:
                        available_commands.append(cmd_name)
    else:
        await interaction.followup.send('❌ Укажите игрока или роль для просмотра доступных команд', ephemeral=True)
        return
    
    if not available_commands:
        embed = discord.Embed(
            title=f'📋 ДОСТУПНЫЕ КОМАНДЫ ДЛЯ {target_type.upper()} {target_name}',
            color=discord.Color.orange(),
            timestamp=datetime.now()
        )
        embed.add_field(name='❌ Нет доступных команд', value='У данного пользователя/роли нет доступа ни к одной команде', inline=False)
    else:
        embed = discord.Embed(
            title=f'📋 ДОСТУПНЫЕ КОМАНДЫ ДЛЯ {target_type.upper()} {target_name}',
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        
        commands_list = '\n'.join([f'• `/{cmd}`' for cmd in sorted(available_commands)])
        embed.add_field(name=f'📊 Всего: {len(available_commands)} команд', value=commands_list, inline=False)
        
        if игрок and игрок.guild_permissions.administrator:
            embed.add_field(name='👑 Примечание', value='Пользователь является администратором, поэтому имеет доступ ко ВСЕМ командам', inline=False)
    
    embed.set_footer(text=f'Запросил: {interaction.user.display_name}')
    await interaction.followup.send(embed=embed, ephemeral=True)

def can_manage_role(user: discord.Member, target_role: discord.Role, guild_id: str):
    if user.guild_permissions.administrator:
        return True
    
    guild_id_str = str(guild_id)
    
    if guild_id_str not in role_permissions:
        return False
    
    if str(user.id) in role_permissions[guild_id_str].get('users', {}):
        if str(target_role.id) in role_permissions[guild_id_str]['users'][str(user.id)]:
            return True
    
    for role in user.roles:
        if str(role.id) in role_permissions[guild_id_str].get('roles', {}):
            if str(target_role.id) in role_permissions[guild_id_str]['roles'][str(role.id)]:
                return True
    
    return False

@bot.tree.command(name='onrole', description='Выдать роль участнику')
async def onrole(interaction: discord.Interaction, игрок: discord.Member, роль: discord.Role):
    await interaction.response.defer(ephemeral=True)
    
    if not can_manage_role(interaction.user, роль, interaction.guild.id):
        await interaction.followup.send('❌ У вас нет права выдавать эту роль', ephemeral=True)
        return
    
    if роль in игрок.roles:
        await interaction.followup.send(f'❌ У {игрок.mention} уже есть роль {роль.mention}', ephemeral=True)
        return
    
    if not interaction.guild.me.guild_permissions.manage_roles:
        await interaction.followup.send('❌ У бота нет права "Управлять ролями"', ephemeral=True)
        return
    
    if роль >= interaction.guild.me.top_role:
        await interaction.followup.send('❌ Роль бота ниже или равна выдаваемой роли', ephemeral=True)
        return
    
    try:
        await игрок.add_roles(роль, reason=f'Выдана {interaction.user.display_name} через /onrole')
        
        log_embed = discord.Embed(
            title='🎭 ВЫДАНА РОЛЬ',
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        log_embed.add_field(name='👤 Игрок', value=f'{игрок.mention}\n`{игрок}`', inline=True)
        log_embed.add_field(name='🎭 Роль', value=роль.mention, inline=True)
        log_embed.add_field(name='🛡️ Выдал', value=f'{interaction.user.mention}\n`{interaction.user}`', inline=True)
        await send_log(interaction.guild.id, log_embed)
        
        embed = discord.Embed(
            title='✅ РОЛЬ ВЫДАНА',
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        embed.add_field(name='👤 Игрок', value=игрок.mention, inline=True)
        embed.add_field(name='🎭 Роль', value=роль.mention, inline=True)
        
        await interaction.followup.send(embed=embed, ephemeral=True)
        
    except discord.Forbidden:
        await interaction.followup.send('❌ Боту не хватает прав для выдачи этой роли', ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f'❌ Ошибка: {e}', ephemeral=True)

@bot.tree.command(name='offrole', description='Снять роль с участника')
async def offrole(interaction: discord.Interaction, игрок: discord.Member, роль: discord.Role):
    await interaction.response.defer(ephemeral=True)
    
    if not can_manage_role(interaction.user, роль, interaction.guild.id):
        await interaction.followup.send('❌ У вас нет права снимать эту роль', ephemeral=True)
        return
    
    if роль not in игрок.roles:
        await interaction.followup.send(f'❌ У {игрок.mention} нет роли {роль.mention}', ephemeral=True)
        return
    
    if not interaction.guild.me.guild_permissions.manage_roles:
        await interaction.followup.send('❌ У бота нет права "Управлять ролями"', ephemeral=True)
        return
    
    try:
        await игрок.remove_roles(роль, reason=f'Снята {interaction.user.display_name} через /offrole')
        
        log_embed = discord.Embed(
            title='🎭 СНЯТА РОЛЬ',
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        log_embed.add_field(name='👤 Игрок', value=f'{игрок.mention}\n`{игрок}`', inline=True)
        log_embed.add_field(name='🎭 Роль', value=роль.mention, inline=True)
        log_embed.add_field(name='🛡️ Снял', value=f'{interaction.user.mention}\n`{interaction.user}`', inline=True)
        await send_log(interaction.guild.id, log_embed)
        
        embed = discord.Embed(
            title='✅ РОЛЬ СНЯТА',
            color=discord.Color.orange(),
            timestamp=datetime.now()
        )
        embed.add_field(name='👤 Игрок', value=игрок.mention, inline=True)
        embed.add_field(name='🎭 Роль', value=роль.mention, inline=True)
        
        await interaction.followup.send(embed=embed, ephemeral=True)
        
    except discord.Forbidden:
        await interaction.followup.send('❌ Боту не хватает прав для снятия этой роли', ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f'❌ Ошибка: {e}', ephemeral=True)

@bot.tree.command(name='role', description='Выдать право выдавать определенную роль')
async def role_permission_cmd(interaction: discord.Interaction, кому: str, роль: discord.Role):
    await interaction.response.defer(ephemeral=True)
    
    if not interaction.user.guild_permissions.administrator:
        await interaction.followup.send('❌ Только администраторы могут выдавать права', ephemeral=True)
        return
    
    guild_id_str = str(interaction.guild.id)
    
    if guild_id_str not in role_permissions:
        role_permissions[guild_id_str] = {'users': {}, 'roles': {}}
    
    user_match = re.search(r'<@!?(\d+)>', кому)
    role_match = re.search(r'<@&(\d+)>', кому)
    
    if user_match:
        user_id = user_match.group(1)
        user = interaction.guild.get_member(int(user_id))
        
        if not user:
            await interaction.followup.send('❌ Пользователь не найден', ephemeral=True)
            return
        
        if str(user.id) not in role_permissions[guild_id_str]['users']:
            role_permissions[guild_id_str]['users'][str(user.id)] = []
        
        if str(роль.id) not in role_permissions[guild_id_str]['users'][str(user.id)]:
            role_permissions[guild_id_str]['users'][str(user.id)].append(str(роль.id))
        
        save_role_permissions()
        
        embed = discord.Embed(
            title='✅ ПРАВО ВЫДАНО',
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        embed.add_field(name='👤 Кому', value=user.mention, inline=True)
        embed.add_field(name='🎭 Может выдавать роль', value=роль.mention, inline=True)
        
        await interaction.followup.send(embed=embed, ephemeral=True)
        
    elif role_match:
        role_id = role_match.group(1)
        target_role = interaction.guild.get_role(int(role_id))
        
        if not target_role:
            await interaction.followup.send('❌ Роль не найдена', ephemeral=True)
            return
        
        if str(target_role.id) not in role_permissions[guild_id_str]['roles']:
            role_permissions[guild_id_str]['roles'][str(target_role.id)] = []
        
        if str(роль.id) not in role_permissions[guild_id_str]['roles'][str(target_role.id)]:
            role_permissions[guild_id_str]['roles'][str(target_role.id)].append(str(роль.id))
        
        save_role_permissions()
        
        embed = discord.Embed(
            title='✅ ПРАВО ВЫДАНО',
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        embed.add_field(name='🎭 Кому (роль)', value=target_role.mention, inline=True)
        embed.add_field(name='🎭 Может выдавать роль', value=роль.mention, inline=True)
        
        await interaction.followup.send(embed=embed, ephemeral=True)
        
    else:
        await interaction.followup.send('❌ Укажите пользователя (@user) или роль (@role)', ephemeral=True)

@bot.tree.command(name='unrole', description='Забрать право выдавать определенную роль')
async def unrole_permission_cmd(interaction: discord.Interaction, у_кого: str, роль: discord.Role):
    await interaction.response.defer(ephemeral=True)
    
    if not interaction.user.guild_permissions.administrator:
        await interaction.followup.send('❌ Только администраторы могут забирать права', ephemeral=True)
        return
    
    guild_id_str = str(interaction.guild.id)
    
    if guild_id_str not in role_permissions:
        role_permissions[guild_id_str] = {'users': {}, 'roles': {}}
    
    user_match = re.search(r'<@!?(\d+)>', у_кого)
    role_match = re.search(r'<@&(\d+)>', у_кого)
    
    if user_match:
        user_id = user_match.group(1)
        user = interaction.guild.get_member(int(user_id))
        
        if not user:
            await interaction.followup.send('❌ Пользователь не найден', ephemeral=True)
            return
        
        if str(user.id) in role_permissions[guild_id_str]['users']:
            if str(роль.id) in role_permissions[guild_id_str]['users'][str(user.id)]:
                role_permissions[guild_id_str]['users'][str(user.id)].remove(str(роль.id))
                
                if not role_permissions[guild_id_str]['users'][str(user.id)]:
                    del role_permissions[guild_id_str]['users'][str(user.id)]
        
        save_role_permissions()
        
        embed = discord.Embed(
            title='✅ ПРАВО ЗАБРАНО',
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        embed.add_field(name='👤 У кого', value=user.mention, inline=True)
        embed.add_field(name='🎭 Больше не может выдавать', value=роль.mention, inline=True)
        
        await interaction.followup.send(embed=embed, ephemeral=True)
        
    elif role_match:
        role_id = role_match.group(1)
        target_role = interaction.guild.get_role(int(role_id))
        
        if not target_role:
            await interaction.followup.send('❌ Роль не найдена', ephemeral=True)
            return
        
        if str(target_role.id) in role_permissions[guild_id_str]['roles']:
            if str(роль.id) in role_permissions[guild_id_str]['roles'][str(target_role.id)]:
                role_permissions[guild_id_str]['roles'][str(target_role.id)].remove(str(роль.id))
                
                if not role_permissions[guild_id_str]['roles'][str(target_role.id)]:
                    del role_permissions[guild_id_str]['roles'][str(target_role.id)]
        
        save_role_permissions()
        
        embed = discord.Embed(
            title='✅ ПРАВО ЗАБРАНО',
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        embed.add_field(name='🎭 У кого (роль)', value=target_role.mention, inline=True)
        embed.add_field(name='🎭 Больше не может выдавать', value=роль.mention, inline=True)
        
        await interaction.followup.send(embed=embed, ephemeral=True)
        
    else:
        await interaction.followup.send('❌ Укажите пользователя (@user) или роль (@role)', ephemeral=True)

@bot.tree.command(name='sup_adm', description='👑 Назначить роль для управления поддержкой')
async def sup_adm(interaction: discord.Interaction, роль: discord.Role):
    await interaction.response.defer(ephemeral=True)
    
    if not interaction.user.guild_permissions.administrator:
        await interaction.followup.send('❌ Только администраторы могут настраивать поддержку', ephemeral=True)
        return
    
    guild_id_str = str(interaction.guild.id)
    
    if guild_id_str not in support_admins:
        support_admins[guild_id_str] = {'roles': []}
    
    if str(роль.id) not in support_admins[guild_id_str]['roles']:
        support_admins[guild_id_str]['roles'].append(str(роль.id))
        save_support_admins()
        
        embed = discord.Embed(
            title='✅ РОЛЬ НАЗНАЧЕНА',
            description=f'Роль {роль.mention} теперь может управлять системой поддержки и жалоб',
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
    else:
        await interaction.followup.send(f'❌ Роль {роль.mention} уже имеет доступ к поддержке', ephemeral=True)

@bot.tree.command(name='sup_rem', description='👑 Убрать роль из управления поддержкой')
async def sup_rem(interaction: discord.Interaction, роль: discord.Role):
    await interaction.response.defer(ephemeral=True)
    
    if not interaction.user.guild_permissions.administrator:
        await interaction.followup.send('❌ Только администраторы могут настраивать поддержку', ephemeral=True)
        return
    
    guild_id_str = str(interaction.guild.id)
    
    if guild_id_str in support_admins:
        if str(роль.id) in support_admins[guild_id_str].get('roles', []):
            support_admins[guild_id_str]['roles'].remove(str(роль.id))
            save_support_admins()
            
            embed = discord.Embed(
                title='✅ РОЛЬ УБРАНА',
                description=f'Роль {роль.mention} больше не может управлять системой поддержки',
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.followup.send(f'❌ Роль {роль.mention} не имеет доступа к поддержке', ephemeral=True)
    else:
        await interaction.followup.send('❌ Нет настроенных ролей для поддержки', ephemeral=True)

@bot.tree.command(name='support', description='Открыть панель поддержки и жалоб (только админ)')
async def support_panel(interaction: discord.Interaction):
    await interaction.response.defer()
    
    if not interaction.user.guild_permissions.administrator:
        await interaction.followup.send("❌ У вас нет прав для использования этой команды", ephemeral=True)
        return
    
    embed = discord.Embed(
        title="🛡️ Техническая поддержка",
        description="Добро пожаловать в техническую поддержку проекта!\n\n"
                   "**📨 Обратиться в поддержку** — если у вас есть вопросы по игре или серверу, "
                   "проблемы с функционалом или нужна помощь.\n\n"
                   "**⚠️ Пожаловаться на пользователя** — если кто-то нарушает правила, "
                   "оскорбляет или спамит.\n\n"
                   "> Наши специалисты рассмотрят ваше обращение в ближайшее время.",
        color=discord.Color.red()
    )
    
    view = SupportView(interaction.guild.id)
    
    await interaction.followup.send(embed=embed, view=view)

@bot.tree.command(name='setup-support', description='⚙️ Настроить каналы для поддержки (админ)')
async def setup_support(interaction: discord.Interaction, канал_тикетов: discord.TextChannel, канал_жалоб: discord.TextChannel):
    await interaction.response.defer(ephemeral=True)
    
    if not interaction.user.guild_permissions.administrator:
        await interaction.followup.send("❌ У вас нет прав для настройки", ephemeral=True)
        return
    
    support_config[str(interaction.guild.id)] = {
        'ticket_channel': канал_тикетов.id,
        'complaint_channel': канал_жалоб.id
    }
    save_support_config()
    
    embed = discord.Embed(
        title="✅ Система поддержки настроена",
        color=discord.Color.green(),
        timestamp=datetime.now()
    )
    embed.add_field(name="Канал тикетов", value=канал_тикетов.mention, inline=True)
    embed.add_field(name="Канал жалоб", value=канал_жалоб.mention, inline=True)
    
    await interaction.followup.send(embed=embed, ephemeral=True)
    
    panel_embed = discord.Embed(
        title="🛡️ Техническая поддержка",
        description="Нажмите на кнопку ниже, чтобы создать обращение в поддержку или пожаловаться на пользователя.",
        color=discord.Color.blue()
    )
    await канал_тикетов.send(embed=panel_embed, view=SupportView(interaction.guild.id))

@bot.tree.command(name='ticket-stats', description='📊 Статистика тикетов и жалоб')
async def ticket_stats(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    
    if not can_manage_support(interaction.user, interaction.guild.id):
        await interaction.followup.send("❌ У вас нет прав", ephemeral=True)
        return
    
    open_tickets = sum(1 for t in tickets_data['tickets'].values() if t.get('status') == 'open')
    in_progress = sum(1 for t in tickets_data['tickets'].values() if t.get('status') == 'in_progress')
    closed_tickets = sum(1 for t in tickets_data['tickets'].values() if t.get('status') == 'closed')
    open_complaints = sum(1 for c in tickets_data['complaints'].values() if c.get('status') == 'open')
    in_progress_complaints = sum(1 for c in tickets_data['complaints'].values() if c.get('status') == 'in_progress')
    accepted = sum(1 for c in tickets_data['complaints'].values() if c.get('status') == 'accepted')
    rejected = sum(1 for c in tickets_data['complaints'].values() if c.get('status') == 'rejected')
    closed_complaints = sum(1 for c in tickets_data['complaints'].values() if c.get('status') == 'closed')
    
    embed = discord.Embed(
        title="📊 Статистика обращений",
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )
    embed.add_field(name="🎫 ТИКЕТЫ", value="─────────", inline=False)
    embed.add_field(name="🟡 Открытых", value=str(open_tickets), inline=True)
    embed.add_field(name="🔵 В работе", value=str(in_progress), inline=True)
    embed.add_field(name="✅ Закрытых", value=str(closed_tickets), inline=True)
    embed.add_field(name="📊 Всего тикетов", value=str(tickets_data['ticket_counter']), inline=True)
    embed.add_field(name="⚠️ ЖАЛОБЫ", value="─────────", inline=False)
    embed.add_field(name="🟡 На рассмотрении", value=str(open_complaints), inline=True)
    embed.add_field(name="🔵 В работе", value=str(in_progress_complaints), inline=True)
    embed.add_field(name="✅ Принятых", value=str(accepted), inline=True)
    embed.add_field(name="❌ Отклонённых", value=str(rejected), inline=True)
    embed.add_field(name="🔒 Закрытых", value=str(closed_complaints), inline=True)
    embed.add_field(name="📊 Всего жалоб", value=str(tickets_data['complaint_counter']), inline=True)
    
    await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(name='my-tickets', description='🎫 Показать мои активные тикеты')
async def my_tickets(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    
    user_tickets = []
    
    for ticket_id, ticket_data in tickets_data['tickets'].items():
        if ticket_data.get('user_id') == interaction.user.id:
            if ticket_data.get('status') in ['open', 'in_progress']:
                user_tickets.append((ticket_id, ticket_data, 'ticket'))
    
    for complaint_id, complaint_data in tickets_data['complaints'].items():
        if complaint_data.get('user_id') == interaction.user.id:
            if complaint_data.get('status') in ['open', 'in_progress']:
                user_tickets.append((complaint_id, complaint_data, 'complaint'))
    
    if not user_tickets:
        embed = discord.Embed(
            title="🎫 Ваши активные обращения",
            description="У вас нет активных обращений.\nОбратитесь в поддержку через панель",
            color=discord.Color.blue()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
        return
    
    embed = discord.Embed(
        title=f"🎫 Ваши активные обращения ({len(user_tickets)})",
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )
    
    for item_id, item_data, item_type in user_tickets:
        status_emoji = "🟡" if item_data.get('status') == 'open' else "🔵"
        status_text = "Ожидает ответа" if item_data.get('status') == 'open' else "В работе у специалиста"
        type_emoji = "🎫" if item_type == 'ticket' else "⚠️"
        
        created_at = datetime.fromisoformat(item_data['created_at'])
        
        embed.add_field(
            name=f"{type_emoji} {status_emoji} {item_id}",
            value=f"**Тема/Причина:** {item_data.get('topic', item_data.get('reason', 'Нет темы'))[:50]}\n"
                  f"**Статус:** {status_text}\n"
                  f"**Создан:** <t:{int(created_at.timestamp())}:R>",
            inline=False
        )
    
    embed.set_footer(text="Специалисты ответят вам в личные сообщения")
    await interaction.followup.send(embed=embed, ephemeral=True)

@bot.tree.command(name='v-role', description='🎭 Создать меню для выдачи ролей с кнопками')
async def v_role(interaction: discord.Interaction, заголовок: str, текст: str, эмоджи1: str, роль1: discord.Role, эмоджи2: str = None, роль2: discord.Role = None, эмоджи3: str = None, роль3: discord.Role = None, эмоджи4: str = None, роль4: discord.Role = None, эмоджи5: str = None, роль5: discord.Role = None):
    await interaction.response.defer()
    
    if not interaction.user.guild_permissions.administrator:
        await interaction.followup.send("❌ У вас нет прав для использования этой команды", ephemeral=True)
        return
    
    roles_data = []
    
    if эмоджи1 and роль1:
        roles_data.append({'emoji': эмоджи1, 'role_id': роль1.id, 'label': роль1.name})
    if эмоджи2 and роль2:
        roles_data.append({'emoji': эмоджи2, 'role_id': роль2.id, 'label': роль2.name})
    if эмоджи3 and роль3:
        roles_data.append({'emoji': эмоджи3, 'role_id': роль3.id, 'label': роль3.name})
    if эмоджи4 and роль4:
        roles_data.append({'emoji': эмоджи4, 'role_id': роль4.id, 'label': роль4.name})
    if эмоджи5 and роль5:
        roles_data.append({'emoji': эмоджи5, 'role_id': роль5.id, 'label': роль5.name})
    
    if not roles_data:
        await interaction.followup.send("❌ Укажите хотя бы одну пару эмодзи и роль", ephemeral=True)
        return
    
    embed = discord.Embed(
        title=заголовок,
        description=текст,
        color=discord.Color.blue()
    )
    
    for item in roles_data:
        embed.add_field(name=f"{item['emoji']} {item['label']}", value="─" * 20, inline=False)
    
    view = RoleButtonView(roles_data, 0)
    message = await interaction.channel.send(embed=embed, view=view)
    
    await interaction.followup.send(f"✅ Панель выдачи ролей создана: {message.jump_url}", ephemeral=True)

if __name__ == '__main__':
    bot.run(TOKEN)