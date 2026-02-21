# -*- coding: utf-8 -*-
"""
EFL Guru - Versão 31.4 (A MURALHA INQUEBRÁVEL - FIX ROBLOX API & RELATÓRIO)
----------------------------------------------------------------------
- CÓDIGO BRUTO: Completo, sem cortar nada, mantendo 11v11 (4-3-3).
- FIX ROBLOX: Headers adicionados (User-Agent) e sistema de retry para evitar block 429.
- RELATÓRIO BULK ADD: Mostra exatamente o motivo se pular algum jogador.
- NOVAS SIGLAS: ST -> DC | CB -> DFC | GK -> PO.
- AUTO-ATUALIZAÇÃO: Converte cartas e elencos antigos automaticamente.
- SISTEMA DE OLHEIRO: Cooldown de 15 minutos no --obter com aviso automático.
- GESTÃO DE CLUBE: Comando --setclube <sigla> <nome> para personalizar.
- PRANCHETA TÁTICA: Mostra Sigla, Nome do Time e Cofre na imagem.
- WEB SERVER: Flask integrado para UptimeRobot na Render.
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
import time
from PIL import Image, ImageDraw, ImageFont, ImageOps
from io import BytesIO
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client
from flask import Flask
from threading import Thread

# --- 0. SISTEMA WEB (ANTI-SONO PARA A RENDER) ---
app = Flask('')

@app.route('/')
def home():
    return "Bot EFL Guru está ONLINE na Render!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

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

# --- MAPEAMENTO 4-3-3 COM AS NOVAS SIGLAS ---
SLOT_MAPPING = {
    "PO": [0], "GK": [0], "GOL": [0],
    "LE": [1], "LB": [1],
    "DFC": [2, 3], "CB": [2, 3], "ZAG": [2, 3],
    "LD": [4], "RB": [4],
    "VOL": [5, 6, 7], "MCD": [5, 6, 7], "CDM": [5, 6, 7],
    "MC": [5, 6, 7], "CM": [5, 6, 7],
    "MEI": [5, 6, 7], "MCO": [5, 6, 7], "CAM": [5, 6, 7],
    "PE": [8, 10], "LW": [8], "LF": [8],
    "DC": [9], "ST": [9], "CA": [9],
    "PD": [8, 10], "RW": [10], "RF": [10]
}

# --- COORDENADAS DA PRANCHETA (4-3-3) ---
POSITIONS_COORDS = {
    0: (185, 420),  # PO
    1: (60, 340),   # LE
    2: (140, 350),  # DFC 1
    3: (230, 350),  # DFC 2
    4: (310, 340),  # LD
    5: (100, 240),  # MC 1
    6: (185, 250),  # MC 2
    7: (270, 240),  # MC 3
    8: (70, 130),   # PE
    9: (185, 110),  # DC
    10: (300, 130)  # PD
}

# DICIONÁRIO DE ATUALIZAÇÃO AUTOMÁTICA
POS_MIGRATION = {"ST": "DC", "CA": "DC", "CB": "DFC", "ZAG": "DFC", "GK": "PO", "GOL": "PO"}

ALL_PLAYERS = []
data_lock = asyncio.Lock()
image_lock = asyncio.Lock()
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
    chunk_guilds_at_startup=True,
    case_insensitive=True
)

# --- 2. SISTEMAS DE TEXTOS (NARRAÇÕES) ---
GOAL_NARRATIONS = [
    "⚽ GOOOOLAAAAÇO! {attacker} mandou uma bomba do meio da rua! Onde a coruja dorme!",
    "⚽ É REDE! {attacker} dribla a zaga inteira, deixa o goleiro no chão e empurra pro gol vazio!",
    "⚽ GOOOOL! {attacker} recebe cruzamento perfeito na medida e testa firme pro fundo do barbante!",
    "⚽ PINTURA! {attacker} domina no peito e manda de voleio!",
    "⚽ TÁ LÁ DENTRO! {attacker} não desperdiça a chance e guarda no cantinho!",
    "⚽ QUE CATEGORIA! {attacker} toca por cobertura e faz um gol de placa!",
    "⚽ EXPLODE A TORCIDA! {attacker} soltou uma pancada e a bola estufa a rede!",
    "⚽ O NOME DELE É O GOL! {attacker} aparece livre na área e confere!"
]

SAVE_NARRATIONS = [
    "🧤 MILAAAAGRE! {keeper} voa como um gato no ângulo e espalma para escanteio!",
    "🧤 INCRÍVEL! {keeper} salva no puro reflexo com a ponta da chuteira! Que defesa!",
    "🧱 PAREDE! {keeper} fecha o ângulo, cresce pra cima do {attacker} e defende com o peito!",
    "🧤 SEGURO! {keeper} cai no canto certinho e encaixa a bola sem dar rebote.",
    "🧤 ESPETACULAR! {keeper} busca a bola que tinha endereço certo!",
    "🧤 MÃO DE FERRO! {keeper} segura o chute potente de {attacker}!",
    "🧤 GIGANTE! {keeper} sai do gol abafando tudo e impede o grito de gol!"
]

ACHIEVEMENTS = {
    "primeira_vitoria": {"name": "Primeira Vitória", "desc": "Vença sua primeira partida na EFL.", "emoji": "🏆"}
}

# --- 3. MOTOR GRÁFICO (CARD RENDER) ---

def render_single_card_sync(player):
    c_w, c_h = 300, 450
    card = Image.new("RGBA", (c_w, c_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(card)
    ovr = player.get('overall', 60)
    
    if ovr >= 90: base_color = (45, 10, 60); border_color = "#f1c40f"; txt_color = "#f1c40f"
    elif ovr >= 80: base_color = (25, 25, 25); border_color = "#f1c40f"; txt_color = "white"
    elif ovr >= 75: base_color = (40, 40, 40); border_color = "#bdc3c7"; txt_color = "white"
    else: base_color = (50, 35, 25); border_color = "#cd7f32"; txt_color = "white"

    draw.rounded_rectangle([5, 5, c_w-5, c_h-5], radius=30, fill=base_color, outline=border_color, width=7)
    
    try:
        p_img_res = requests.get(player["image"], timeout=5)
        p_img = Image.open(BytesIO(p_img_res.content)).convert("RGBA").resize((230, 230), Image.Resampling.LANCZOS)
        card.paste(p_img, (int(c_w/2 - 115), 75), p_img)
    except: pass

    try:
        f_ovr = ImageFont.truetype("arialbd.ttf", 65)
        f_pos = ImageFont.truetype("arialbd.ttf", 32)
    except:
        f_ovr = f_pos = ImageFont.load_default()

    draw.text((35, 45), str(ovr), font=f_ovr, fill=border_color, anchor="la")
    draw.text((35, 115), player['position'], font=f_pos, fill="white", anchor="la")
    
    nome_cru = player['name'].split()[-1].upper()
    max_w, curr_size = c_w - 60, 38
    try:
        f_name = ImageFont.truetype("arialbd.ttf", curr_size)
        while f_name.getlength(nome_cru) > max_w and curr_size > 16:
            curr_size -= 2
            f_name = ImageFont.truetype("arialbd.ttf", curr_size)
    except: f_name = ImageFont.load_default()

    draw.text((c_w/2, 355), nome_cru, font=f_name, fill=txt_color, anchor="mm")
    draw.line([c_w/2 - 70, 385, c_w/2 + 70, 385], fill=border_color, width=4)
    buf = BytesIO(); card.save(buf, format='PNG'); buf.seek(0)
    return buf

def create_team_image_sync(team_players, club_name, club_sigla, user_money):
    width, height = 370, 500 
    field = Image.new("RGB", (width, height), color="#1e5939")
    draw = ImageDraw.Draw(field, "RGBA")
    
    for i in range(0, height, 25):
        if (i // 25) % 2 == 0: draw.rectangle([0, i, width, i+25], fill="#184f30")
            
    line_c = (255, 255, 255, 100)
    draw.rectangle([10, 10, width-10, height-10], outline=line_c, width=2) 
    draw.line([10, height//2, width-10, height//2], fill=line_c, width=2) 
    draw.ellipse([width//2 - 40, height//2 - 40, width//2 + 40, height//2 + 40], outline=line_c, width=2) 
    draw.rectangle([width//2 - 80, 10, width//2 + 80, 90], outline=line_c, width=2) 
    draw.rectangle([width//2 - 80, height-90, width//2 + 80, height-10], outline=line_c, width=2) 
    
    draw.rectangle([0, 0, width, 42], fill=(0, 0, 0, 210))
    draw.rectangle([0, height-30, width, height], fill=(0, 0, 0, 210))

    try: 
        f_title = ImageFont.truetype("arialbd.ttf", 23)
        f_name = ImageFont.truetype("arialbd.ttf", 9)
        f_stat = ImageFont.truetype("arialbd.ttf", 10)
        f_ovr = ImageFont.truetype("arialbd.ttf", 14)
        f_pos = ImageFont.truetype("arialbd.ttf", 10)
    except: 
        f_title = f_name = f_stat = f_ovr = f_pos = ImageFont.load_default()

    header = f"[{club_sigla or 'EFL'}] {(club_name or 'MEU CLUBE').upper()}"
    draw.text((width//2, 21), header, font=f_title, fill="#f1c40f", anchor="mm")
    
    total_overall = 0
    for i, player in enumerate(team_players):
        cx, cy = POSITIONS_COORDS[i]
        cw, ch = 60, 80
        box = [cx - cw//2, cy - ch//2, cx + cw//2, cy + ch//2]
        
        if player:
            eff_ovr = player.get('overall', 0) + player.get('training_level', 0)
            total_overall += eff_ovr
            
            if eff_ovr >= 90: bg = (30, 10, 45, 240); border = "#e74c3c" 
            elif eff_ovr >= 80: bg = (25, 25, 25, 240); border = "#f1c40f" 
            elif eff_ovr >= 70: bg = (40, 40, 40, 240); border = "#bdc3c7" 
            else: bg = (55, 35, 25, 240); border = "#cd7f32" 
            
            draw.rounded_rectangle(box, radius=6, fill=bg, outline=border, width=2)
            
            try:
                p_img = Image.open(BytesIO(requests.get(player["image"], timeout=3).content)).convert("RGBA")
                p_img.thumbnail((40, 40), Image.Resampling.LANCZOS)
                field.paste(p_img, (int(cx - p_img.width//2), int(cy - 25)), p_img)
            except: pass
            
            disp_name = player.get('nickname') or player['name'].split(' ')[-1]
            disp_name = disp_name[:12] 
            
            draw.rounded_rectangle([cx - cw//2 + 3, cy + 22, cx + cw//2 - 3, cy + 35], radius=3, fill=(0,0,0,200))
            draw.text((cx, cy + 28), disp_name.upper(), font=f_name, fill="white", anchor="mm") 
            draw.text((cx - cw//2 + 6, cy - ch//2 + 6), player['position'], font=f_pos, fill=border, anchor="la") 
            draw.text((cx + cw//2 - 6, cy - ch//2 + 5), str(eff_ovr), font=f_ovr, fill=border, anchor="ra") 
        else:
            draw.rounded_rectangle(box, radius=6, fill=(0,0,0,120), outline=(255,255,255,60), width=1)
            draw.text((cx, cy), "➕", font=f_title, fill=(255,255,255,80), anchor="mm")

    draw.text((15, height - 15), f"⭐ OVR: {total_overall}", font=f_stat, fill="#f1c40f", anchor="lm")
    draw.text((width - 15, height - 15), f"🏦 Cofre: R$ {user_money:,}", font=f_stat, fill="#2ecc71", anchor="rm")
    
    buf = BytesIO(); field.save(buf, format='PNG'); buf.seek(0)
    return buf

# --- 4. CLASSES MODALS ---

class AddPlayerModal(discord.ui.Modal, title='Novo Atleta'):
    def __init__(self, rbx_name, img_url):
        super().__init__()
        self.rbx_name, self.img_url = rbx_name, img_url
        self.ovr = discord.ui.TextInput(label='Overall (OVR)', placeholder='85', min_length=1, max_length=2)
        self.pos = discord.ui.TextInput(label='Posição (DC, DFC, PO...)', placeholder='DC', min_length=2, max_length=3)
        self.add_item(self.ovr)
        self.add_item(self.pos)

    async def on_submit(self, inter: discord.Interaction):
        try:
            o_int = int(self.ovr.value)
            p_str = self.pos.value.upper().strip()
            if p_str in POS_MIGRATION: p_str = POS_MIGRATION[p_str]
            if p_str not in SLOT_MAPPING:
                return await inter.response.send_message(f"❌ Posição `{p_str}` inválida.", ephemeral=True)
            new_p = {"name": self.rbx_name, "image": self.img_url, "overall": o_int, "position": p_str, "value": o_int * 25000}
            async with data_lock:
                res = supabase.table("jogadores").select("data").eq("id", "ROBLOX_CARDS").execute()
                cards = res.data[0]["data"] if res.data else []
                cards.append(new_p)
                supabase.table("jogadores").upsert({"id": "ROBLOX_CARDS", "data": cards}).execute()
                fetch_and_parse_players()
            buf = await asyncio.to_thread(render_single_card_sync, new_p)
            await inter.response.send_message(f"✅ **CADASTRADO!**", file=discord.File(buf, "card.png"))
        except: await inter.response.send_message("❌ Erro.", ephemeral=True)

class EditPlayerModal(discord.ui.Modal, title='Editar Atleta'):
    def __init__(self, nick):
        super().__init__(); self.nick = nick
        self.ovr = discord.ui.TextInput(label='Novo Overall (OVR)', placeholder='92', min_length=1, max_length=2)
        self.add_item(self.ovr)
    async def on_submit(self, inter: discord.Interaction):
        try:
            o = int(self.ovr.value); v = o * 25000
            async with data_lock:
                res = supabase.table("jogadores").select("data").eq("id", "ROBLOX_CARDS").execute()
                cards = res.data[0]["data"]
                for p in cards:
                    if p['name'].lower() == self.nick.lower(): p['overall'], p['value'] = o, v; break
                supabase.table("jogadores").update({"data": cards}).eq("id", "ROBLOX_CARDS").execute()
                fetch_and_parse_players()
            await inter.response.send_message(f"✅ **{self.nick}** atualizado!")
        except: await inter.response.send_message("❌ Erro.", ephemeral=True)

# --- 5. BANCO DE DADOS E FUNÇÕES ---

def fetch_and_parse_players():
    global ALL_PLAYERS
    ALL_PLAYERS = []
    try:
        res = supabase.table("jogadores").select("data").eq("id", "ROBLOX_CARDS").execute()
        if res.data:
            cards = res.data[0]["data"]
            updated = False
            for p in cards:
                if p.get("position") in POS_MIGRATION:
                    p["position"] = POS_MIGRATION[p["position"]]
                    updated = True
            if updated:
                supabase.table("jogadores").update({"data": cards}).eq("id", "ROBLOX_CARDS").execute()
            ALL_PLAYERS.extend(cards)
            print(f"✅ {len(cards)} Cartas carregadas (Siglas atualizadas se necessário).")
    except Exception as e: print(f"❌ Erro ao buscar Cartas: {e}")

async def get_user_data(user_id):
    uid = str(user_id)
    try:
        res = supabase.table("jogadores").select("data").eq("id", uid).execute()
        if not res.data:
            initial = {
                "money": INITIAL_MONEY, "squad": [], "team": [None] * 11, "wins": 0, "losses": 0, 
                "match_history": [], "achievements": [], "contracted_players": [],
                "club_name": None, "club_sigla": "EFL"
            }
            supabase.table("jogadores").insert({"id": uid, "data": initial}).execute()
            return initial
            
        data = res.data[0]["data"]
        defaults = [("losses", 0), ("achievements", []), ("match_history", []), ("contracted_players", []), ("club_name", None), ("club_sigla", "EFL")]
        for key, val in defaults:
            if key not in data: data[key] = val
                
        if "team" not in data or len(data["team"]) != 11:
            old_team = data.get("team", [])
            new_team = [None] * 11
            for idx, p in enumerate(old_team):
                if p and idx < 11: new_team[idx] = p
            data["team"] = new_team

        needs_update = False
        for p in data.get("squad", []):
            if p.get("position") in POS_MIGRATION:
                p["position"] = POS_MIGRATION[p["position"]]
                needs_update = True
        for i in range(len(data.get("team", []))):
            p = data["team"][i]
            if p and p.get("position") in POS_MIGRATION:
                p["position"] = POS_MIGRATION[p["position"]]
                needs_update = True
        if needs_update:
            supabase.table("jogadores").update({"data": data}).eq("id", uid).execute()

        return data
    except Exception: return None

async def save_user_data(user_id, data):
    try: supabase.table("jogadores").update({"data": data}).eq("id", str(user_id)).execute()
    except Exception: pass

def normalize_str(s): return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn').lower()

# --- 7. VIEWS DE INTERAÇÃO ---

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
            if self.player['name'] in u_data["contracted_players"]: return await inter.response.send_message("❌ Já tem!", ephemeral=True)
            if u_data['money'] < self.player['value']: return await inter.response.send_message(f"💸 Sem grana!", ephemeral=True)
            u_data['money'] -= self.player['value']; u_data['squad'].append(self.player); u_data['contracted_players'].append(self.player['name']); await save_user_data(self.author.id, u_data)
            await inter.response.edit_message(content=f"🤝 **NEGÓCIO FECHADO!**", embed=None, view=None)

class ActionView(discord.ui.View):
    def __init__(self, ctx, res, callback, name, **kwargs):
        super().__init__(timeout=120); self.ctx, self.res, self.callback, self.name, self.i, self.kwargs = ctx, res, callback, name, 0, kwargs
        self.children[2].label = name
    async def create_embed(self, inter=None):
        p = self.res[self.i]
        e = discord.Embed(title=f"⚙️ {self.name}", description=f"**Jogador:** {p['name']}\n**OVR:** {p['overall']}", color=discord.Color.orange()); e.set_thumbnail(url=p['image'])
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
            try: await inter.message.delete()
            except: pass

# --- 8. EVENTOS E COMANDOS DE ADM (FIX ROBLOX API AQUI) ---

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
    if isinstance(error, commands.CommandOnCooldown):
        minutos = int(error.retry_after // 60)
        segundos = int(error.retry_after % 60)
        await ctx.send(f"⏳ Calma aí, chefinho! O olheiro está viajando. Tente novamente em **{minutos}m e {segundos}s**.")
        return
    if isinstance(error, commands.CommandNotFound) or isinstance(error, commands.CheckFailure): return
    print(f"Erro detectado: {error}")

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
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'}
    try:
        res = requests.post("https://users.roblox.com/v1/usernames/users", json={"usernames": [username]}, headers=headers, timeout=10)
        if res.status_code == 429: # Se a API bloquear, espera 2 segundos e tenta de novo
            time.sleep(2)
            res = requests.post("https://users.roblox.com/v1/usernames/users", json={"usernames": [username]}, headers=headers, timeout=10)
            
        data = res.json()
        if not data.get("data"): return None
        
        uid = data["data"][0]["id"]
        res2 = requests.get(f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={uid}&size=420x420&format=Png&isCircular=false", headers=headers, timeout=10)
        data2 = res2.json()
        
        if data2.get("data") and data2["data"][0].get("imageUrl"):
            return data2["data"][0]["imageUrl"]
        return None
    except Exception as e:
        print(f"Erro Roblox API para {username}: {e}")
        return None

@bot.command(name='addplayer')
@commands.has_permissions(administrator=True)
async def add_player_cmd(ctx, *, query: str):
    msg = await ctx.send("🔄 Verificando Roblox...")
    try: member = await commands.MemberConverter().convert(ctx, query); rbx_name = member.display_name.split()[-1].strip()
    except: rbx_name = query.strip()
    img = await asyncio.to_thread(get_roblox_data_sync, rbx_name)
    if not img: return await msg.edit(content=f"❌ O Roblox não achou o nick `{rbx_name}` ou a foto não carregou.")
    view = AddPlayerView(ctx.author, rbx_name, img); emb = discord.Embed(title="📸 Perfil Encontrado", color=discord.Color.green())
    emb.set_thumbnail(url=img); await msg.edit(content=None, embed=emb, view=view)

@bot.command(name='bulkadd')
@commands.has_permissions(administrator=True)
async def bulk_add_cmd(ctx):
    if not ctx.message.attachments: return await ctx.send("❌ Anexe um arquivo `.txt`.")
    att = ctx.message.attachments[0]
    status = await ctx.send("⏳ **Iniciando Bulk Add... Lendo arquivo...**")
    try:
        content = (await att.read()).decode('utf-8'); lines = content.strip().split('\n')
        res = supabase.table("jogadores").select("data").eq("id", "ROBLOX_CARDS").execute()
        cards = res.data[0]["data"] if res.data else []; names = [p['name'].lower() for p in cards]
        added = []
        erros_log = []
        
        for line in lines:
            parts = line.split()
            if len(parts) < 3: continue
            n, ovr, pos = parts[0].strip(), int(parts[1].strip()), parts[2].strip().upper()
            
            if pos in POS_MIGRATION: pos = POS_MIGRATION[pos]
            
            if n.lower() in names:
                erros_log.append(f"Ignorado: {n} (Já está no banco de dados)")
                continue
            if pos not in SLOT_MAPPING:
                erros_log.append(f"Ignorado: {n} (Posição {pos} não reconhecida)")
                continue
                
            img = await asyncio.to_thread(get_roblox_data_sync, n)
            if img:
                cards.append({"name": n, "image": img, "overall": ovr, "position": pos, "value": ovr*25000})
                names.append(n.lower()); added.append(n)
            else:
                erros_log.append(f"Ignorado: {n} (API do Roblox não achou o usuário ou a foto)")
            
            await asyncio.sleep(1.5) # Aumentei o sleep pra evitar bloqueio 429
            
        if added: supabase.table("jogadores").upsert({"id": "ROBLOX_CARDS", "data": cards}).execute(); fetch_and_parse_players()
        
        relatorio = f"✅ Adicionados: **{len(added)}** atletas."
        if erros_log:
            resumo_erros = "\n".join(erros_log[:10])
            if len(erros_log) > 10: resumo_erros += f"\n...e mais {len(erros_log) - 10} erros ocultos."
            relatorio += f"\n\n⚠️ **Relatório de Problemas:**\n```{resumo_erros}```"
            
        await status.edit(content=relatorio)
    except Exception as e: await status.edit(content=f"❌ Erro fatal no Bulk Add: {e}")

@bot.command(name='editplayer')
@commands.has_permissions(administrator=True)
async def edit_player_cmd(ctx, *, nick: str):
    view = EditPlayerView(ctx.author, nick); await ctx.send(f"⚙️ Configurações de `{nick}`:", view=view)

@bot.command(name='setclube')
async def setclube_cmd(ctx, sigla: str, *, nome: str):
    d = await get_user_data(ctx.author.id)
    d['club_sigla'] = sigla.upper()[:4]
    d['club_name'] = nome
    await save_user_data(ctx.author.id, d)
    await ctx.send(f"✅ Identidade do clube atualizada: **[{d['club_sigla']}] {d['club_name']}**")

# --- 10. COMANDOS DO JOGO ---

async def reminder_task(ctx, user):
    await asyncio.sleep(900)
    try: await ctx.send(f"⏰ <@{user.id}>, seu olheiro voltou! O comando `{BOT_PREFIX}obter` já está liberado novamente.")
    except: pass

@bot.command(name='obter')
@commands.cooldown(1, 900, commands.BucketType.user)
async def obter_cmd(ctx):
    u = await get_user_data(ctx.author.id)
    livres = [p for p in ALL_PLAYERS if p["name"] not in u["contracted_players"]]
    if not livres: 
        ctx.command.reset_cooldown(ctx)
        return await ctx.send("❌ Mercado vazio!")
    p = random.choice(livres)
    async with image_lock: buf = await asyncio.to_thread(render_single_card_sync, p)
    await ctx.send(content="🃏 **OLHEIRO:** Encontrou um atleta!", file=discord.File(buf, "card.png"), view=KeepOrSellView(ctx.author, p))
    bot.loop.create_task(reminder_task(ctx, ctx.author))

@bot.command(name='contratar')
async def contratar_cmd(ctx, *, q: str):
    sq = normalize_str(q); u = await get_user_data(ctx.author.id)
    match = [p for p in ALL_PLAYERS if sq in normalize_str(p['name']) or sq.upper() in p['position']]
    if not match: return await ctx.send("❌ Nenhum atleta encontrado.")
    p = match[0]
    if p['name'] in u['contracted_players']: return await ctx.send("❌ Já possui esse atleta.")
    async with image_lock: buf = await asyncio.to_thread(render_single_card_sync, p)
    await ctx.send(content=f"🛒 **PREÇO:** R$ **{p['value']:,}**", file=discord.File(buf, "card.png"), view=BuyPlayerView(ctx.author, p))

@bot.command(name='cofre')
async def cofre_cmd(ctx):
    d = await get_user_data(ctx.author.id); await ctx.send(f"🏦 **COFRE DO CLUBE:** R$ {d['money']:,}")

@bot.command(name='donate')
async def donate_cmd(ctx, target: discord.Member, amount: int):
    if ctx.author == target or amount <= 0: return
    async with data_lock:
        s_data = await get_user_data(ctx.author.id); t_data = await get_user_data(target.id)
        if s_data['money'] < amount: return await ctx.send("❌ Saldo insuficiente.")
        s_data['money'] -= amount; t_data['money'] += amount
        await save_user_data(ctx.author.id, s_data); await save_user_data(target.id, t_data)
    await ctx.send(f"💸 **TRANSFERÊNCIA:** R$ {amount:,} para {target.display_name}!")

@bot.command(name='sell')
async def sell_cmd(ctx, *, q: str):
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
    if not any(d['team']): return await ctx.send("❌ Sua prancheta tática está vazia.")
    msg = await ctx.send("⚙️ Desenhando prancheta 4-3-3...")
    money = d.get('money', 0); sigla = d.get('club_sigla', 'EFL'); nome = d.get('club_name') or ctx.author.display_name
    async with image_lock:
        try:
            buf = await asyncio.to_thread(create_team_image_sync, d['team'], nome, sigla, money)
            await ctx.send(file=discord.File(buf, "team.png")); await msg.delete()
        except Exception as e: await msg.edit(content=f"❌ Erro gráfico: {e}")

async def perform_escalar(ctx, j):
    d = await get_user_data(ctx.author.id); t = d['team']
    if any(x and x['name'] == j['name'] for x in t): return await ctx.send("❌ Já é titular.")
    done = False
    for pos in j['position'].split('/'):
        if pos in SLOT_MAPPING:
            for i in SLOT_MAPPING[pos]:
                if t[i] is None: t[i] = j; done = True; break
        if done: break
    if done: await save_user_data(ctx.author.id, d); await ctx.send(f"✅ Escalei **{j['name']}** na prancheta!")
    else: await ctx.send("❌ Sem vaga livre para essa posição.")

@bot.command(name='escalar')
async def escalar_cmd(ctx, *, q: str):
    sq = normalize_str(q); d = await get_user_data(ctx.author.id)
    res = [p for p in d['squad'] if sq in normalize_str(p['name'])]
    if not res: return await ctx.send("❌ Não encontrado no elenco.")
    if len(res) == 1: await perform_escalar(ctx, res[0])
    else:
        v = ActionView(ctx, res, perform_escalar, "Escalar"); await ctx.send(embed=await v.create_embed(), view=v)

@bot.command(name='elenco')
async def elenco_cmd(ctx):
    d = await get_user_data(ctx.author.id)
    if not d['squad']: return await ctx.send("❌ Seu elenco está vazio.")
    txt = "\n".join([f"• **{p['name']}** | ⭐ {p['overall']}" for p in sorted(d['squad'], key=lambda x: x['overall'], reverse=True)[:25]])
    await ctx.send(embed=discord.Embed(title="🎽 Seu Elenco", description=txt, color=discord.Color.blue()))

@bot.command(name='confrontar')
async def confrontar_cmd(ctx, oponente: discord.Member):
    if ctx.author == oponente or oponente.bot: return
    d1, d2 = await get_user_data(ctx.author.id), await get_user_data(oponente.id)
    if None in d1['team'] or None in d2['team']: return await ctx.send("🚨 A prancheta exige 11 titulares escalados de ambos os lados!")
    s1, s2 = 0, 0; log = ["🎙️ **Início de partida!**"]; emb = discord.Embed(title=f"🏟️ {ctx.author.name} x {oponente.name}", description="0 - 0", color=discord.Color.dark_grey())
    msg = await ctx.send(embed=emb)
    for min in [15, 30, 45, 60, 75, 90]:
        await asyncio.sleep(2.5)
        f1, f2 = sum(x['overall'] for x in d1['team'] if x), sum(x['overall'] for x in d2['team'] if x)
        if f1 + random.randint(0,40) > f2 + random.randint(0,40):
            at = random.choice([p for p in d1['team'] if p])['name']; log.append(f"{min}' " + random.choice(GOAL_NARRATIONS).format(attacker=at)); s1 += 1
        elif f2 + random.randint(0,40) > f1 + random.randint(0,40):
            at = random.choice([p for p in d2['team'] if p])['name']; log.append(f"{min}' " + random.choice(GOAL_NARRATIONS).format(attacker=at)); s2 += 1
        else:
            gk = random.choice([p for p in d2['team'] if p and p['position'] in ['PO','GK','GOL']] or [p for p in d2['team'] if p])['name']
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
    await ctx.send(embed=discord.Embed(title="🏆 Ranking Global", description=txt or "Sem jogos.", color=discord.Color.gold()))

@bot.command(name='help')
async def help_cmd(ctx):
    emb = discord.Embed(title="📜 Ajuda", color=discord.Color.gold())
    emb.add_field(name="💰 Economia & Clube", value="`cofre`, `donate`, `contratar`, `sell`, `obter`, `setclube`", inline=False)
    emb.add_field(name="📋 Vestiário", value="`elenco`, `escalar`, `team`", inline=False)
    emb.add_field(name="⚽ Partida", value="`confrontar`, `ranking`", inline=False)
    emb.add_field(name="⚙️ ADM", value="`addplayer`, `bulkadd`, `editplayer`, `lock`, `unlock`", inline=False)
    await ctx.send(embed=emb)

# --- INICIALIZAÇÃO ---
if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if token: 
        keep_alive()
        bot.run(token)
    else: print("❌ Token ausente.")
