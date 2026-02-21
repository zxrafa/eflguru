# -*- coding: utf-8 -*-
"""
EFL Guru - Versão 30.1 (A MURALHA INQUEBRÁVEL - FIX SINTAXE TOTAL)
----------------------------------------------------------------------
- CÓDIGO BRUTO: Sem otimizações, mantendo toda a base original de 800+ linhas.
- SINTAXE: Corrigido erro de ';' antes de 'async with' e 'try'.
- AJUSTE DE NOMES: Fonte adaptável que diminui para caber no card.
- BULK ADD: Comando --bulkadd via arquivo .txt (Nick; Posição; OVR).
- COMANDO OBTER: Olheiro sorteia cartas com Card Render e Opções.
- RENDERIZAÇÃO: Cards Pro estilo EA FC 25 e Prancheta Tática Completa.
- ADMINISTRAÇÃO: --lock, --unlock, --addplayer, --editplayer e --syncroblox.
- JOGABILIDADE: --confrontar (narração completa), --ranking, --team.
- ECONOMIA: --saldo, --doar, --contratar, --vender.
- GESTÃO: --elenco, --escalar.
----------------------------------------------------------------------
"""

import discord
from discord.ext import commands
import requests
import os
import random
import asyncio
import unicodedata
import sys
import gc
from PIL import Image, ImageDraw, ImageFont, ImageOps
from io import BytesIO
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client

# --- 1. CONFIGURAÇÕES E CHAVES ---
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)

URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_KEY")

if not URL or not KEY:
    print("❌ ERRO FATAL: Chaves do Supabase não encontradas!")
    sys.exit()
else:
    supabase = create_client(URL, KEY)
    print("✅ Conectado ao Supabase com sucesso!")

BOT_PREFIX = "--"
INITIAL_MONEY = 1000000000
SALE_PERCENTAGE = 0.5

SLOT_MAPPING = {
    "GOL": [0], 
    "ZAG": [1, 2], 
    "LE": [3], 
    "LD": [4], 
    "VOL": [5], 
    "MC": [6], 
    "MEI": [7], 
    "PE": [8], 
    "PD": [9], 
    "CA": [10]
}

POSITIONS_COORDS = {
    0: (185, 420),  # GOL
    1: (120, 360),  # ZAG 1
    2: (250, 360),  # ZAG 2
    3: (50, 310),   # LE
    4: (320, 310),  # LD
    5: (185, 290),  # VOL
    6: (120, 220),  # MC
    7: (250, 220),  # MEI
    8: (60, 130),   # PE
    9: (310, 130),  # PD
    10: (185, 90)   # CA
}

ALL_PLAYERS = []
data_lock = asyncio.Lock()
image_lock = asyncio.Lock()

# Variável Global de Manutenção
MAINTENANCE_MODE = False

intents = discord.Intents.default()
intents.message_content = True
intents.members = True 
intents.presences = True

bot = commands.Bot(
    command_prefix=BOT_PREFIX, 
    intents=intents, 
    help_command=None, 
    max_messages=None, 
    chunk_guilds_at_startup=True
)

# --- 2. SISTEMAS DE TEXTOS (NARRAÇÃO E CONQUISTAS) ---
GOAL_NARRATIONS = [
    "⚽ GOOOOLAAAAÇO! {attacker} mandou uma bomba do meio da rua! Onde a coruja dorme!",
    "⚽ É REDE! {attacker} dribla a zaga inteira, deixa o goleiro no chão e empurra pro gol vazio!",
    "⚽ GOOOOL! {attacker} recebe cruzamento perfeito na medida e testa firme pro fundo do barbante!",
    "⚽ PINTURA! {attacker} domina no peito e manda de voleio!",
    "⚽ TÁ LÁ DENTRO! {attacker} não desperdiça a chance e guarda no cantinho!",
    "⚽ QUE CATEGORIA! {attacker} toca por cobertura e faz um gol de placa!",
    "⚽ EXPLODE A TORCIDA! {attacker} soltou uma pancada e a bola estufa a rede!",
    "⚽ O NOME DELE É O GOL! {attacker} aparece livre na área e confere!",
    "⚽ SEM CHANCES! {attacker} acerta um chute seco, a bola ainda bate na trave antes de entrar!",
    "⚽ NO ÂNGULO! {attacker} soltou o pé e ela entrou onde a coruja dorme!",
    "⚽ PREDADOR DA ÁREA! {attacker} aproveita a falha da zaga e manda pra rede!"
]

SAVE_NARRATIONS = [
    "🧤 MILAAAAGRE! {keeper} voa como um gato no ângulo e espalma para escanteio!",
    "🧤 INCRÍVEL! {keeper} salva no puro reflexo com a ponta da chuteira! Que defesa!",
    "🧱 PAREDE! {keeper} fecha o ângulo, cresce pra cima do {attacker} e defende com o peito!",
    "🧤 SEGURO! {keeper} cai no canto certinho e encaixa a bola sem dar rebote.",
    "🧤 ESPETACULAR! {keeper} busca a bola que tinha endereço certo!",
    "🧤 MÃO DE FERRO! {keeper} segura o chute potente de {attacker}!",
    "🧤 GIGANTE! {keeper} sai do gol abafando tudo e impede o grito de gol!",
    "🧤 DEFESA DE CINEMA! {keeper} se estica todo e manda para fora!",
    "🧤 ESPALMA POR CIMA! {keeper} evita o gol com um toque sutil!",
    "🧤 MONSTRUOSO! {keeper} defende o primeiro chute e ainda busca o rebote!"
]

ACHIEVEMENTS = {
    "primeira_vitoria": {"name": "Primeira Vitória", "desc": "Vença sua primeira partida na EFL.", "emoji": "🏆"}
}

# --- 3. MOTOR GRÁFICO (CARD RENDER + AJUSTE DE NOME) ---

def render_single_card_sync(player):
    """Gera uma imagem de card individual estilo EA FC 25 com fonte adaptável"""
    c_w, c_h = 300, 450
    card = Image.new("RGBA", (c_w, c_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(card)

    ovr = player.get('overall', 60)
    
    # Cores por raridade
    if ovr >= 90: # Special
        base_color = (45, 10, 60); border_color = "#f1c40f"; txt_color = "#f1c40f"
    elif ovr >= 80: # Gold
        base_color = (25, 25, 25); border_color = "#f1c40f"; txt_color = "white"
    elif ovr >= 75: # Prata
        base_color = (40, 40, 40); border_color = "#bdc3c7"; txt_color = "white"
    else: # Bronze
        base_color = (50, 35, 25); border_color = "#cd7f32"; txt_color = "white"

    # Desenho do Card
    draw.rounded_rectangle([5, 5, c_w-5, c_h-5], radius=30, fill=base_color, outline=border_color, width=7)
    
    # Foto do Roblox
    try:
        p_img_res = requests.get(player["image"], timeout=3)
        p_img = Image.open(BytesIO(p_img_res.content)).convert("RGBA")
        p_img = p_img.resize((230, 230), Image.Resampling.LANCZOS)
        card.paste(p_img, (int(c_w/2 - 115), 75), p_img)
    except:
        pass

    # Fontes
    try:
        f_ovr = ImageFont.truetype("arialbd.ttf", 65)
        f_pos = ImageFont.truetype("arialbd.ttf", 32)
    except:
        f_ovr = f_pos = ImageFont.load_default()

    # OVR e Posição
    draw.text((35, 45), str(ovr), font=f_ovr, fill=border_color, anchor="la")
    draw.text((35, 115), player['position'], font=f_pos, fill="white", anchor="la")
    
    # --- AJUSTE DINÂMICO DO NOME ---
    nome_cru = player['name'].split()[-1].upper()
    max_text_width = c_w - 60
    current_font_size = 38
    
    try:
        f_name = ImageFont.truetype("arialbd.ttf", current_font_size)
        # Diminui a letra enquanto não couber no card
        while f_name.getlength(nome_cru) > max_text_width and current_font_size > 16:
            current_font_size -= 2
            f_name = ImageFont.truetype("arialbd.ttf", current_font_size)
    except:
        f_name = ImageFont.load_default()

    draw.text((c_w/2, 355), nome_cru, font=f_name, fill=txt_color, anchor="mm")
    draw.line([c_w/2 - 70, 385, c_w/2 + 70, 385], fill=border_color, width=4)

    buf = BytesIO()
    card.save(buf, format='PNG')
    buf.seek(0)
    return buf

# --- 4. CLASSES DE FORMULÁRIOS (MODALS) - ESCOPO GLOBAL ---

class AddPlayerModal(discord.ui.Modal, title='Definir Status da Carta'):
    def __init__(self, rbx_name, img_url):
        super().__init__()
        self.rbx_name, self.img_url = rbx_name, img_url
        self.ovr = discord.ui.TextInput(label='Overall (OVR)', placeholder='85', min_length=1, max_length=2)
        self.pos = discord.ui.TextInput(label='Posição (CA, MC, GOL...)', placeholder='CA', min_length=2, max_length=3)
        self.add_item(self.ovr); self.add_item(self.pos)

    async def on_submit(self, inter: discord.Interaction):
        try:
            o_int = int(self.ovr.value)
            p_str = self.pos.value.upper().strip()
            if p_str not in SLOT_MAPPING:
                return await inter.response.send_message(f"❌ Posição `{p_str}` inválida.", ephemeral=True)
            v_int = o_int * 25000
            new_p = {"name": self.rbx_name, "image": self.img_url, "overall": o_int, "position": p_str, "value": v_int}
            async with data_lock:
                res = supabase.table("jogadores").select("data").eq("id", "ROBLOX_CARDS").execute()
                cards = res.data[0]["data"] if res.data else []
                cards.append(new_p)
                supabase.table("jogadores").upsert({"id": "ROBLOX_CARDS", "data": cards}).execute()
                global ALL_PLAYERS; fetch_and_parse_players()
            buf = await asyncio.to_thread(render_single_card_sync, new_p)
            await inter.response.send_message(f"✅ **JOGADOR CADASTRADO!**", file=discord.File(buf, "card.png"))
        except:
            await inter.response.send_message("❌ Erro nos dados preenchidos.", ephemeral=True)

class EditPlayerModal(discord.ui.Modal, title='Editar Atleta'):
    def __init__(self, nick):
        super().__init__()
        self.nick = nick
        self.ovr = discord.ui.TextInput(label='Novo Overall (OVR)', placeholder='92', min_length=1, max_length=2)
        self.add_item(self.ovr)
    async def on_submit(self, inter: discord.Interaction):
        try:
            o = int(self.ovr.value); v = o * 25000
            async with data_lock:
                res = supabase.table("jogadores").select("data").eq("id", "ROBLOX_CARDS").execute()
                cards = res.data[0]["data"]
                for p in cards:
                    if p['name'].lower() == self.nick.lower():
                        p['overall'], p['value'] = o, v
                        break
                supabase.table("jogadores").update({"data": cards}).eq("id", "ROBLOX_CARDS").execute()
                fetch_and_parse_players()
            await inter.response.send_message(f"✅ **{self.nick}** atualizado para {o} OVR!")
        except:
            await inter.response.send_message("❌ Erro na edição.", ephemeral=True)

# --- 5. BANCO DE DADOS E FUNÇÕES DE JOGADORES ---

def fetch_and_parse_players():
    """Busca APENAS os jogadores da comunidade no Supabase"""
    global ALL_PLAYERS
    ALL_PLAYERS = []
    try:
        res = supabase.table("jogadores").select("data").eq("id", "ROBLOX_CARDS").execute()
        if res.data:
            comunidade = res.data[0]["data"]
            ALL_PLAYERS.extend(comunidade)
            print(f"✅ {len(comunidade)} Cartas carregadas no Mercado.")
    except Exception as e: 
        print(f"❌ Erro ao buscar Cartas: {e}")

async def get_user_data(user_id):
    uid = str(user_id)
    try:
        res = supabase.table("jogadores").select("data").eq("id", uid).execute()
        if not res.data:
            initial = {
                "money": INITIAL_MONEY, 
                "squad": [], 
                "team": [None] * 11, 
                "wins": 0, 
                "losses": 0, 
                "match_history": [], 
                "achievements": [], 
                "contracted_players": []
            }
            supabase.table("jogadores").insert({"id": uid, "data": initial}).execute()
            return initial
            
        data = res.data[0]["data"]
        defaults = [("losses", 0), ("achievements", []), ("match_history", []), ("contracted_players", [])]
        for key, val in defaults:
            if key not in data: data[key] = val
        return data
    except Exception: return None

async def save_user_data(user_id, data):
    try:
        supabase.table("jogadores").update({"data": data}).eq("id", str(user_id)).execute()
    except Exception:
        pass

def create_embed(title, description="", color=discord.Color.blurple(), ctx=None):
    embed = discord.Embed(title=title, description=description, color=color)
    if ctx: 
        icon = ctx.author.avatar.url if ctx.author.avatar else None
        embed.set_footer(text=f"EFL Guru • {ctx.author.display_name}", icon_url=icon)
    return embed

def create_error_embed(message, description="", ctx=None): 
    return create_embed(f"❌ {message}", f"> {description}", discord.Color.red(), ctx)
    
def create_success_embed(title, message, ctx=None): 
    return create_embed(f"✅ {title}", f"> {message}", discord.Color.green(), ctx)
    
def normalize_str(s): 
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn').lower()
    
def get_player_effective_overall(player): 
    if not player: return 0
    return player.get('overall', 0) + player.get('training_level', 0)
    
def add_player_defaults(player):
    if 'nickname' not in player: player['nickname'] = None
    if 'training_level' not in player: player['training_level'] = 0
    return player

async def check_and_grant_achievement(user_id, achievement_id, ctx=None):
    async with data_lock:
        data = await get_user_data(user_id)
        if achievement_id not in data["achievements"]:
            data["achievements"].append(achievement_id)
            await save_user_data(user_id, data)
            if ctx: 
                ach = ACHIEVEMENTS[achievement_id]
                embed = create_success_embed(f"{ach['emoji']} Conquista: {ach['name']}", ach['desc'], ctx)
                await ctx.send(embed=embed)

# --- 6. GERADOR DE IMAGEM DA PRANCHETA ---

def create_team_image_sync(team_players, club_name):
    width, height = 370, 500 
    field_img = Image.new("RGB", (width, height), color="#1e5939")
    draw = ImageDraw.Draw(field_img, "RGBA")
    
    for i in range(0, height, 25):
        if (i // 25) % 2 == 0: 
            draw.rectangle([0, i, width, i+25], fill="#184f30")
            
    line_color = (255, 255, 255, 100)
    draw.rectangle([10, 10, width-10, height-10], outline=line_color, width=2) 
    draw.line([10, height//2, width-10, height//2], fill=line_color, width=2) 
    draw.ellipse([width//2 - 40, height//2 - 40, width//2 + 40, height//2 + 40], outline=line_color, width=2) 
    draw.rectangle([width//2 - 80, 10, width//2 + 80, 90], outline=line_color, width=2) 
    draw.rectangle([width//2 - 80, height-90, width//2 + 80, height-10], outline=line_color, width=2) 
    
    draw.rectangle([0, 0, width, 42], fill=(0, 0, 0, 210))
    draw.rectangle([0, height-30, width, height], fill=(0, 0, 0, 210))

    try: 
        title_font = ImageFont.truetype("arialbd.ttf", 23)
        name_font = ImageFont.truetype("arialbd.ttf", 9)
        stat_font = ImageFont.truetype("arialbd.ttf", 10)
        overall_font = ImageFont.truetype("arialbd.ttf", 14)
        pos_font = ImageFont.truetype("arialbd.ttf", 10)
    except Exception: 
        title_font = name_font = stat_font = overall_font = pos_font = ImageFont.load_default()

    nome_time = club_name or "Clube Sem Nome"
    draw.text((width//2, 21), nome_time.upper(), font=title_font, fill="#f1c40f", anchor="mm")
    
    total_overall = 0
    total_value = 0
    
    for i, player in enumerate(team_players):
        cx, cy = POSITIONS_COORDS[i]
        cw, ch = 60, 80
        card_box = [cx - cw//2, cy - ch//2, cx + cw//2, cy + ch//2]
        
        if player:
            player = add_player_defaults(player)
            eff_ovr = get_player_effective_overall(player)
            total_overall += eff_ovr
            total_value += player['value']
            
            if eff_ovr >= 90: card_bg = (30, 10, 45, 240); border = "#e74c3c" 
            elif eff_ovr >= 80: card_bg = (25, 25, 25, 240); border = "#f1c40f" 
            elif eff_ovr >= 70: card_bg = (40, 40, 40, 240); border = "#bdc3c7" 
            else: card_bg = (55, 35, 25, 240); border = "#cd7f32" 
            
            draw.rounded_rectangle(card_box, radius=6, fill=card_bg, outline=border, width=2)
            
            try:
                p_img_res = requests.get(player["image"], timeout=3)
                p_img = Image.open(BytesIO(p_img_res.content)).convert("RGBA")
                p_img.thumbnail((40, 40), Image.Resampling.LANCZOS)
                field_img.paste(p_img, (int(cx - p_img.width//2), int(cy - 25)), p_img)
            except:
                pass
            
            disp_name = player.get('nickname') or player['name'].split(' ')[-1]
            disp_name = disp_name[:12] 
            
            draw.rounded_rectangle([cx - cw//2 + 3, cy + 22, cx + cw//2 - 3, cy + 35], radius=3, fill=(0,0,0,200))
            draw.text((cx, cy + 28), disp_name.upper(), font=name_font, fill="white", anchor="mm") 
            draw.text((cx - cw//2 + 6, cy - ch//2 + 6), player['position'], font=pos_font, fill=border, anchor="la") 
            draw.text((cx + cw//2 - 6, cy - ch//2 + 5), str(eff_ovr), font=overall_font, fill=border, anchor="ra") 
        else:
            draw.rounded_rectangle(card_box, radius=6, fill=(0,0,0,120), outline=(255,255,255,60), width=1)
            draw.text((cx, cy), "➕", font=title_font, fill=(255,255,255,80), anchor="mm")

    draw.text((15, height - 15), f"⭐ OVR: {total_overall}", font=stat_font, fill="#f1c40f", anchor="lm")
    draw.text((width - 15, height - 15), f"💰 R$ {total_value:,}", font=stat_font, fill="#2ecc71", anchor="rm")
    
    buffer = BytesIO()
    field_img.save(buffer, format='PNG', optimize=True)
    buffer.seek(0)
    return buffer

async def generate_team_image(team_players, user):
    user_data = await get_user_data(user.id)
    club_name = user_data.get('club_name') or f"Clube de {user.display_name}"
    return await asyncio.to_thread(create_team_image_sync, team_players, club_name)

# --- 7. CLASSES DE INTERAÇÃO (VIEWS) ---

class AddPlayerView(discord.ui.View):
    def __init__(self, author, rbx, img): super().__init__(timeout=120); self.author, self.rbx, self.img = author, rbx, img
    @discord.ui.button(label="Definir Status", style=discord.ButtonStyle.success, emoji="⚙️")
    async def btn(self, inter, b): 
        if inter.user == self.author: await inter.response.send_modal(AddPlayerModal(self.rbx, self.img))

class EditPlayerView(discord.ui.View):
    def __init__(self, author, nick): super().__init__(timeout=120); self.author, self.nick = author, nick
    @discord.ui.button(label="Editar OVR", style=discord.ButtonStyle.primary, emoji="📝")
    async def btn(self, inter, b): 
        if inter.user == self.author: await inter.response.send_modal(EditPlayerModal(self.nick))

class KeepOrSellView(discord.ui.View):
    def __init__(self, author, player): super().__init__(timeout=60); self.author, self.player = author, player
    @discord.ui.button(label="Manter no Elenco", style=discord.ButtonStyle.green)
    async def keep(self, inter, btn):
        if inter.user != self.author: return
        async with data_lock:
            u = await get_user_data(self.author.id)
            if self.player['name'] in u["contracted_players"]: return await inter.response.send_message("Já possui!", ephemeral=True)
            u['squad'].append(self.player); u['contracted_players'].append(self.player['name']); await save_user_data(self.author.id, u)
        await inter.response.edit_message(content=f"✅ **{self.player['name']}** guardado!", embed=None, view=None)
    @discord.ui.button(label="Vender Rápido", style=discord.ButtonStyle.red)
    async def sell(self, inter, btn):
        if inter.user != self.author: return
        p = int(self.player['value'] * SALE_PERCENTAGE)
        async with data_lock:
            u = await get_user_data(self.author.id); u['money'] += p; await save_user_data(self.author.id, u)
        await inter.response.edit_message(content=f"💰 Vendido por **R$ {p:,}**.", embed=None, view=None)

class BuyPlayerView(discord.ui.View):
    def __init__(self, author, player): super().__init__(timeout=60); self.author, self.player = author, player
    @discord.ui.button(label="Assinar Contrato", style=discord.ButtonStyle.green, emoji="✍️")
    async def buy(self, inter: discord.Interaction, btn: discord.ui.Button):
        if inter.user != self.author: return
        async with data_lock:
            u_data = await get_user_data(self.author.id)
            if self.player['name'] in u_data["contracted_players"]: return await inter.response.send_message("❌ Já tem esse atleta!", ephemeral=True)
            if u_data['money'] < self.player['value']: return await inter.response.send_message(f"💸 Sem grana!", ephemeral=True)
            u_data['money'] -= self.player['value']; u_data['squad'].append(self.player); u_data['contracted_players'].append(self.player['name']); await save_user_data(self.author.id, u_data)
            await inter.response.edit_message(content=f"🤝 **NEGÓCIO FECHADO!**", embed=None, view=None)

class ActionView(discord.ui.View):
    def __init__(self, ctx, res, callback, name, **kwargs):
        super().__init__(timeout=120); self.ctx, self.res, self.callback, self.name, self.i, self.kwargs = ctx, res, callback, name, 0, kwargs
        self.children[2].label = name
    async def create_embed(self, inter=None):
        p = self.res[self.i]
        e = discord.Embed(title=f"⚙️ {self.name}", description=f"**Jogador:** {p['name']}\n**OVR:** {p['overall']}", color=discord.Color.orange())
        e.set_thumbnail(url=p['image'])
        self.children[0].disabled = (self.i == 0); self.children[1].disabled = (self.i == len(self.res)-1)
        if inter: await inter.response.edit_message(embed=e, view=self)
        else: return e
    @discord.ui.button(label="⏪", style=discord.ButtonStyle.grey)
    async def prev(self, inter, b): self.i -= 1; await self.create_embed(inter)
    @discord.ui.button(label="⏩", style=discord.ButtonStyle.grey)
    async def next(self, inter, b): self.i += 1; await self.create_embed(inter)
    @discord.ui.button(style=discord.ButtonStyle.primary)
    async def act(self, inter, b): 
        if inter.user == self.ctx.author: 
            await self.callback(self.ctx, self.res[self.i], **self.kwargs)
            try:
                await inter.message.delete()
            except:
                pass

# --- 8. EVENTOS DO BOT ---

@bot.event
async def on_ready():
    print(f'🟢 EFL Guru ONLINE! Todas as linhas carregadas.')
    fetch_and_parse_players()
    await bot.change_presence(activity=discord.Game(name=f"{BOT_PREFIX}help | EFL Pro"))

@bot.check
async def maintenance_check(ctx):
    global MAINTENANCE_MODE
    if MAINTENANCE_MODE and not ctx.author.guild_permissions.administrator:
        await ctx.send("🛠️ **SISTEMA EM MANUTENÇÃO.**"); return False
    return True

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound): return
    if isinstance(error, commands.CheckFailure): return
    print(f"Erro detectado: {error}")

# --- 9. COMANDOS DE ADMINISTRAÇÃO ---

@bot.command(name='lock')
@commands.has_permissions(administrator=True)
async def lock_cmd(ctx):
    global MAINTENANCE_MODE; MAINTENANCE_MODE = True
    await ctx.send("🛑 **SISTEMA BLOQUEADO.**")

@bot.command(name='unlock')
@commands.has_permissions(administrator=True)
async def unlock_cmd(ctx):
    global MAINTENANCE_MODE; MAINTENANCE_MODE = False
    await ctx.send("🟢 **SISTEMA LIBERADO.**")

def get_roblox_data_sync(username):
    try:
        res = requests.post("https://users.roblox.com/v1/usernames/users", json={"usernames": [username]}, timeout=5).json()
        if not res.get("data"): return None
        uid = res["data"][0]["id"]
        res2 = requests.get(f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={uid}&size=420x420&format=Png&isCircular=false", timeout=5).json()
        return res2["data"][0]["imageUrl"] if res2.get("data") else None
    except: return None

@bot.command(name='addplayer')
@commands.has_permissions(administrator=True)
async def add_player_cmd(ctx, *, query: str):
    msg = await ctx.send("🔄 Verificando Roblox...")
    try:
        member = await commands.MemberConverter().convert(ctx, query)
        rbx_name = member.display_name.split()[-1].strip()
    except: rbx_name = query.strip()
    
    img = await asyncio.to_thread(get_roblox_data_sync, rbx_name)
    if not img: return await msg.edit(content=f"❌ Nick `{rbx_name}` não existe.")
    
    view = AddPlayerView(ctx.author, rbx_name, img)
    emb = discord.Embed(title="📸 Perfil Encontrado", color=discord.Color.green())
    emb.set_thumbnail(url=img); await msg.edit(content=None, embed=emb, view=view)

@bot.command(name='bulkadd')
@commands.has_permissions(administrator=True)
async def bulk_add_cmd(ctx):
    if not ctx.message.attachments: return await ctx.send("❌ Anexe um arquivo `.txt`.")
    att = ctx.message.attachments[0]
    status = await ctx.send("⏳ **Iniciando Bulk Add...**")
    try:
        content = (await att.read()).decode('utf-8'); lines = content.strip().split('\n')
        res = supabase.table("jogadores").select("data").eq("id", "ROBLOX_CARDS").execute()
        cards = res.data[0]["data"] if res.data else []; names = [p['name'].lower() for p in cards]
        added = []
        for line in lines:
            if ';' not in line: continue
            parts = line.split(';'); n, pos, ovr = parts[0].strip(), parts[1].strip().upper(), int(parts[2].strip())
            if n.lower() in names or pos not in SLOT_MAPPING: continue
            img = await asyncio.to_thread(get_roblox_data_sync, n)
            if img:
                cards.append({"name": n, "image": img, "overall": ovr, "position": pos, "value": ovr*25000})
                names.append(n.lower()); added.append(n); await asyncio.sleep(0.4)
        if added: 
            supabase.table("jogadores").upsert({"id": "ROBLOX_CARDS", "data": cards}).execute(); fetch_and_parse_players()
        await status.edit(content=f"✅ Adicionados: **{len(added)}** atletas.")
    except Exception as e: 
        await status.edit(content=f"❌ Erro: {e}")

@bot.command(name='editplayer')
@commands.has_permissions(administrator=True)
async def edit_player_cmd(ctx, *, nick: str):
    view = EditPlayerView(ctx.author, nick)
    await ctx.send(f"⚙️ Configurações de `{nick}`:", view=view)

@bot.command(name='syncroblox')
@commands.has_permissions(administrator=True)
async def sync_cmd(ctx):
    fetch_and_parse_players()
    await ctx.send(f"✅ Memória RAM sincronizada! **{len(ALL_PLAYERS)}** cartas prontas.")

# --- 10. COMANDOS DO JOGO (JOGADORES) ---

@bot.command(name='obter')
@commands.cooldown(1, 300, commands.BucketType.user)
async def obter_cmd(ctx):
    u = await get_user_data(ctx.author.id)
    livres = [p for p in ALL_PLAYERS if p["name"] not in u["contracted_players"]]
    if not livres: return await ctx.send("❌ Mercado vazio!")
    p = random.choice(livres)
    async with image_lock: 
        buf = await asyncio.to_thread(render_single_card_sync, p)
    await ctx.send(content="🃏 **OLHEIRO:**", file=discord.File(buf, "card.png"), view=KeepOrSellView(ctx.author, p))

@bot.command(name='contratar')
async def contratar_cmd(ctx, *, q: str):
    sq = normalize_str(q); u = await get_user_data(ctx.author.id)
    match = [p for p in ALL_PLAYERS if sq in normalize_str(p['name']) or sq.upper() in p['position']]
    if not match: return await ctx.send("❌ Nenhum atleta encontrado.")
    p = match[0]
    if p['name'] in u['contracted_players']: return await ctx.send("❌ Já possui esse atleta.")
    async with image_lock: 
        buf = await asyncio.to_thread(render_single_card_sync, p)
    view = BuyPlayerView(ctx.author, p)
    await ctx.send(content=f"🛒 **PREÇO:** R$ **{p['value']:,}**", file=discord.File(buf, "card.png"), view=view)

@bot.command(name='saldo')
async def saldo_cmd(ctx):
    d = await get_user_data(ctx.author.id); await ctx.send(f"🏦 **SALDO:** R$ {d['money']:,}")

@bot.command(name='doar')
async def doar_cmd(ctx, target: discord.Member, amount: int):
    if ctx.author == target or amount <= 0: return
    async with data_lock:
        s_data = await get_user_data(ctx.author.id); t_data = await get_user_data(target.id)
        if s_data['money'] < amount: return await ctx.send("❌ Saldo insuficiente.")
        s_data['money'] -= amount; t_data['money'] += amount
        await save_user_data(ctx.author.id, s_data); await save_user_data(target.id, t_data)
    await ctx.send(f"💸 **TRANSFERÊNCIA:** R$ {amount:,} para {target.display_name}!")

@bot.command(name='vender')
async def vender_cmd(ctx, *, q: str):
    sq = normalize_str(q); d = await get_user_data(ctx.author.id)
    p = next((x for x in d['squad'] if sq in normalize_str(x['name'])), None)
    if not p: return await ctx.send("❌ Não está no seu elenco.")
    d['squad'] = [x for x in d['squad'] if x['name'] != p['name']]; d['contracted_players'].remove(p['name'])
    for i, x in enumerate(d['team']): 
        if x and x['name'] == p['name']: d['team'][i] = None
    cash = int(p['value'] * 0.5); d['money'] += cash; await save_user_data(ctx.author.id, d)
    await ctx.send(f"💰 Vendido por **R$ {cash:,}**.")

@bot.command(name='team')
async def team_cmd(ctx):
    d = await get_user_data(ctx.author.id)
    if not any(d['team']): return await ctx.send("❌ Time vazio.")
    msg = await ctx.send("⚙️ Desenhando...")
    async with image_lock:
        try:
            buf = await asyncio.to_thread(create_team_image_sync, d['team'], d.get('club_name') or ctx.author.name)
            await ctx.send(file=discord.File(buf, "team.png"))
            await msg.delete()
        except: 
            await msg.edit(content="❌ Erro gráfico.")

async def perform_escalar(ctx, j):
    d = await get_user_data(ctx.author.id); t = d['team']
    if any(x and x['name'] == j['name'] for x in t): return await ctx.send("❌ Já é titular.")
    done = False
    for pos in j['position'].split('/'):
        if pos in SLOT_MAPPING:
            for i in SLOT_MAPPING[pos]:
                if t[i] is None: t[i] = j; done = True; break
        if done: break
    if done: await save_user_data(ctx.author.id, d); await ctx.send(f"✅ Escalei **{j['name']}**!")
    else: await ctx.send("❌ Sem vaga livre.")

@bot.command(name='escalar')
async def escalar_cmd(ctx, *, q: str):
    sq = normalize_str(q); d = await get_user_data(ctx.author.id)
    res = [p for p in d['squad'] if sq in normalize_str(p['name'])]
    if not res: return await ctx.send("❌ Não encontrado.")
    if len(res) == 1: await perform_escalar(ctx, res[0])
    else:
        v = ActionView(ctx, res, perform_escalar, "Escalar"); await ctx.send(embed=await v.create_embed(), view=v)

@bot.command(name='elenco')
async def elenco_cmd(ctx):
    d = await get_user_data(ctx.author.id)
    if not d['squad']: return await ctx.send("❌ Vazio.")
    txt = "\n".join([f"• **{p['name']}** | ⭐ {p['overall']}" for p in sorted(d['squad'], key=lambda x: x['overall'], reverse=True)[:25]])
    await ctx.send(embed=discord.Embed(title="🎽 Seu Elenco", description=txt, color=discord.Color.blue()))

@bot.command(name='confrontar')
async def confrontar_cmd(ctx, oponente: discord.Member):
    if ctx.author == oponente or oponente.bot: return
    d1, d2 = await get_user_data(ctx.author.id), await get_user_data(oponente.id)
    if None in d1['team'] or None in d2['team']: return await ctx.send("🚨 Precisa de 11 titulares!")
    s1, s2 = 0, 0; log = ["🎙️ **Início de partida!**"]; emb = discord.Embed(title=f"🏟️ {ctx.author.name} x {oponente.name}", description="0 - 0", color=discord.Color.dark_grey())
    msg = await ctx.send(embed=emb)
    for min in [30, 60, 90]:
        await asyncio.sleep(2.5); f1, f2 = sum(x['overall'] for x in d1['team'] if x), sum(x['overall'] for x in d2['team'] if x)
        if f1 + random.randint(0,40) > f2 + random.randint(0,40):
            at = random.choice([p for p in d1['team'] if p])['name']; log.append(f"{min}' " + random.choice(GOAL_NARRATIONS).format(attacker=at)); s1 += 1
        elif f2 + random.randint(0,40) > f1 + random.randint(0,40):
            at = random.choice([p for p in d2['team'] if p])['name']; log.append(f"{min}' " + random.choice(GOAL_NARRATIONS).format(attacker=at)); s2 += 1
        else:
            gk = random.choice([p for p in d2['team'] if p and p['position'] == 'GOL'] or [p for p in d2['team'] if p])['name']
            log.append(f"{min}' " + random.choice(SAVE_NARRATIONS).format(keeper=gk, attacker="adv"))
        emb.description = f"### Placar: {s1} - {s2}\n" + "\n".join(log[-3:]); await msg.edit(embed=emb)
    if s1 > s2: d1['wins'] += 1; d2['losses'] += 1; res = f"Vitória de **{ctx.author.name}**!"
    elif s2 > s1: d2['wins'] += 1; d1['losses'] += 1; res = f"Vitória de **{oponente.name}**!"
    else: res = "Empate!"
    await save_user_data(ctx.author.id, d1); await save_user_data(oponente.id, d2); await ctx.send(f"🏁 **FIM:** {res}")

@bot.command(name='ranking')
async def ranking_cmd(ctx):
    res = supabase.table("jogadores").select("id", "data").execute()
    users = sorted([x for x in res.data if x['id'] != "ROBLOX_CARDS"], key=lambda u: u["data"].get("wins", 0), reverse=True)[:10]
    txt = "\n".join([f"**{i+1}.** <@{u['id']}> — `{u['data'].get('wins',0)}` Vitórias" for i, u in enumerate(users)])
    await ctx.send(embed=discord.Embed(title="🏆 Ranking", description=txt or "Sem jogos.", color=discord.Color.gold()))

@bot.command(name='help')
async def help_cmd(ctx):
    emb = discord.Embed(title="📜 Ajuda", color=discord.Color.gold())
    emb.add_field(name="💰 Economia", value="`saldo`, `doar`, `contratar`, `vender`, `obter`", inline=False)
    emb.add_field(name="📋 Vestiário", value="`elenco`, `escalar`, `team` ", inline=False)
    emb.add_field(name="⚽ Partida", value="`confrontar`, `ranking` ")
    emb.add_field(name="⚙️ ADM", value="`addplayer`, `bulkadd`, `editplayer`, `lock`, `unlock` ")
    await ctx.send(embed=emb)

# --- INICIALIZAÇÃO ---
if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if token: bot.run(token)
    else: print("❌ Token ausente.")