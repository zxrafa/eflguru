# -*- coding: utf-8 -*-
"""
EFL Guru - Versão 30.9 (A MURALHA INQUEBRÁVEL - FONTES AUTO-DOWNLOAD FIX)
----------------------------------------------------------------------
- CÓDIGO BRUTO: Sem otimizações, mantendo toda a base original.
- SINTAXE E WEB SERVER: Flask integrado para UptimeRobot na Render.
- AJUSTE DE NOMES: Fonte adaptável com DOWNLOAD AUTOMÁTICO DE FONTE.
- VISUAL DO CARD: Fundo em gradiente, fontes GIGANTES garantidas e Fade.
- FORMATO 6v6: Prancheta reduzida para 6 slots.
- POSIÇÕES OFICIAIS: GK, CB, MCD, MC, MCO, ST.
- VISUAL DO TIME: Formação 6v6 usando a fonte baixada para máxima qualidade.
- BULK ADD: Comando --bulkadd via arquivo .txt (NOVO FORMATO: Nick OVR Pos)
- ADMINISTRAÇÃO: --lock, --unlock, --addplayer, --editplayer.
- JOGABILIDADE: --confrontar (exige 6 titulares), --ranking, --team.
- ECONOMIA E GESTÃO: --cofre, --donate, --contratar, --sell, --elenco.
- PAGINAÇÃO PRO: Embeds detalhados com navegação visual.
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

# --- SISTEMA DE FONTE AUTOMÁTICA ---
FONT_PATH = "EFL_Font.ttf"
FONT_URL = "https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Black.ttf"

def ensure_font_exists():
    if not os.path.exists(FONT_PATH):
        try:
            print("⬇️ Baixando fonte profissional para o servidor...")
            r = requests.get(FONT_URL, allow_redirects=True)
            open(FONT_PATH, 'wb').write(r.content)
            print("✅ Fonte baixada com sucesso!")
        except Exception as e:
            print(f"❌ Erro ao baixar fonte: {e}")

# Garante que a fonte existe antes de começar
ensure_font_exists()

# --- MAPEAMENTO 6v6 ---
SLOT_MAPPING = {
    "GK": [0], 
    "CB": [1], 
    "MCD": [2], 
    "MC": [3], 
    "MCO": [4], 
    "ST": [5]
}

# --- COORDENADAS DA PRANCHETA (Formação Diamante 6v6) ---
POSITIONS_COORDS = {
    0: (210, 485),  # GK
    1: (210, 395),  # CB
    2: (210, 295),  # MCD
    3: (95, 205),   # MC
    4: (325, 205),  # MCO
    5: (210, 95)    # ST
}

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

# --- 3. MOTOR GRÁFICO (CARD RENDER + AJUSTE DE NOME E FADE) ---

def render_single_card_sync(player):
    """Gera uma imagem de card individual estilo EA FC com fade e fontes robustas"""
    c_w, c_h = 300, 450
    card = Image.new("RGBA", (c_w, c_h), (0, 0, 0, 0))
    
    ovr = player.get('overall', 60)
    
    if ovr >= 90: # Special
        c_top = (70, 15, 90); c_bot = (30, 5, 40); border_color = "#f39c12"; txt_color = "#f1c40f"
    elif ovr >= 80: # Gold
        c_top = (60, 50, 20); c_bot = (20, 18, 5); border_color = "#f1c40f"; txt_color = "white"
    elif ovr >= 75: # Prata
        c_top = (85, 85, 85); c_bot = (30, 30, 30); border_color = "#bdc3c7"; txt_color = "white"
    else: # Bronze
        c_top = (100, 70, 45); c_bot = (40, 25, 15); border_color = "#cd7f32"; txt_color = "white"

    bg_img = Image.new("RGBA", (c_w, c_h))
    draw_bg = ImageDraw.Draw(bg_img)
    for y in range(c_h):
        r = int(c_top[0] + (c_bot[0] - c_top[0]) * (y / c_h))
        g = int(c_top[1] + (c_bot[1] - c_top[1]) * (y / c_h))
        b = int(c_top[2] + (c_bot[2] - c_top[2]) * (y / c_h))
        draw_bg.line([(0, y), (c_w, y)], fill=(r, g, b, 255))
        
    draw_bg.line([(0, 150), (c_w, 100)], fill=(255, 255, 255, 15), width=40)
    draw_bg.line([(0, 300), (c_w, 250)], fill=(255, 255, 255, 10), width=60)

    mask = Image.new("L", (c_w, c_h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([5, 5, c_w-5, c_h-5], radius=25, fill=255)
    card.paste(bg_img, (0, 0), mask)
    
    draw = ImageDraw.Draw(card)
    draw.rounded_rectangle([5, 5, c_w-5, c_h-5], radius=25, outline=border_color, width=6)
    
    try:
        p_img_res = requests.get(player["image"], timeout=3)
        p_img = Image.open(BytesIO(p_img_res.content)).convert("RGBA")
        p_img = p_img.resize((240, 240), Image.Resampling.LANCZOS)
        
        r_c, g_c, b_c, a_c = p_img.split()
        fade = Image.new("L", (1, p_img.height))
        for y in range(p_img.height):
            if y < p_img.height * 0.60:
                fade.putpixel((0, y), 255)
            else:
                alpha = int(255 * (1.0 - (y - p_img.height * 0.60) / (p_img.height * 0.40)))
                fade.putpixel((0, y), max(0, min(255, alpha)))
        
        fade = fade.resize(p_img.size)
        a_data = a_c.load()
        f_data = fade.load()
        for y in range(p_img.height):
            for x in range(p_img.width):
                a_data[x, y] = int((a_data[x, y] * f_data[x, y]) / 255)
        
        p_img = Image.merge("RGBA", (r_c, g_c, b_c, a_c))
        card.paste(p_img, (int(c_w/2 - 120), 80), p_img)
    except Exception:
        pass

    # CARREGAMENTO GARANTIDO DA FONTE BAIXADA
    try:
        f_ovr = ImageFont.truetype(FONT_PATH, 90) # OVR Gigante
        f_pos = ImageFont.truetype(FONT_PATH, 45) # Posição Gigante
    except:
        f_ovr = f_pos = ImageFont.load_default()

    draw.text((35, 30), str(ovr), font=f_ovr, fill=border_color, anchor="la")
    
    # A posição da Posição também ajustada com a nova fonte
    draw.text((35, 120), player['position'], font=f_pos, fill="white", anchor="la")
    
    draw.line([40, 310, c_w-40, 310], fill=border_color, width=2)
    
    nome_cru = player['name'].split()[-1].upper()
    max_text_width = c_w - 40
    current_font_size = 50 
    
    try:
        f_name = ImageFont.truetype(FONT_PATH, current_font_size)
        while f_name.getlength(nome_cru) > max_text_width and current_font_size > 18:
            current_font_size -= 2
            f_name = ImageFont.truetype(FONT_PATH, current_font_size)
    except:
        f_name = ImageFont.load_default()

    draw.text((c_w/2, 345), nome_cru, font=f_name, fill=txt_color, anchor="mm")
    draw.line([c_w/2 - 50, 385, c_w/2 + 50, 385], fill=border_color, width=4)

    buf = BytesIO()
    card.save(buf, format='PNG')
    buf.seek(0)
    return buf

# --- 4. CLASSES DE FORMULÁRIOS (MODALS) ---

class AddPlayerModal(discord.ui.Modal, title='Definir Status da Carta'):
    def __init__(self, rbx_name, img_url):
        super().__init__()
        self.rbx_name, self.img_url = rbx_name, img_url
        self.ovr = discord.ui.TextInput(label='Overall (OVR)', placeholder='85', min_length=1, max_length=2)
        self.pos = discord.ui.TextInput(label='Posição (GK, CB, MCD, MC, MCO, ST)', placeholder='Ex: ST', min_length=2, max_length=3)
        self.add_item(self.ovr)
        self.add_item(self.pos)

    async def on_submit(self, inter: discord.Interaction):
        try:
            o_int = int(self.ovr.value)
            p_str = self.pos.value.upper().strip()
            if p_str not in SLOT_MAPPING:
                return await inter.response.send_message(f"❌ Posição `{p_str}` inválida. Use: GK, CB, MCD, MC, MCO ou ST.", ephemeral=True)
            v_int = o_int * 25000
            new_p = {"name": self.rbx_name, "image": self.img_url, "overall": o_int, "position": p_str, "value": v_int}
            async with data_lock:
                res = supabase.table("jogadores").select("data").eq("id", "ROBLOX_CARDS").execute()
                cards = res.data[0]["data"] if res.data else []
                cards.append(new_p)
                supabase.table("jogadores").upsert({"id": "ROBLOX_CARDS", "data": cards}).execute()
                global ALL_PLAYERS
                fetch_and_parse_players()
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
            o = int(self.ovr.value)
            v = o * 25000
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
                "team": [None] * 6,
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
            if key not in data: 
                data[key] = val
                
        if "team" not in data or len(data["team"]) != 6:
            data["team"] = [None] * 6
            
        return data
    except Exception: 
        return None

async def save_user_data(user_id, data):
    try:
        supabase.table("jogadores").update({"data": data}).eq("id", str(user_id)).execute()
    except Exception:
        pass

def normalize_str(s): 
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn').lower()
    
def get_player_effective_overall(player): 
    if not player: 
        return 0
    return player.get('overall', 0) + player.get('training_level', 0)
    
def add_player_defaults(player):
    if 'nickname' not in player: 
        player['nickname'] = None
    if 'training_level' not in player: 
        player['training_level'] = 0
    return player

# --- 6. GERADOR DE IMAGEM DA PRANCHETA (6v6 REVAMPED) ---

def create_team_image_sync(team_players, club_name):
    width, height = 420, 550 
    field_img = Image.new("RGB", (width, height), color="#2E7D32")
    draw = ImageDraw.Draw(field_img, "RGBA")
    
    for i in range(0, height, 25):
        if (i // 25) % 2 == 0: 
            draw.rectangle([0, i, width, i+25], fill="#388E3C")
            
    line_color = (255, 255, 255, 180)
    draw.rectangle([10, 10, width-10, height-10], outline=line_color, width=3) 
    draw.line([10, height//2, width-10, height//2], fill=line_color, width=3) 
    draw.ellipse([width//2 - 50, height//2 - 50, width//2 + 50, height//2 + 50], outline=line_color, width=3) 
    draw.rectangle([width//2 - 90, 10, width//2 + 90, 100], outline=line_color, width=3) 
    draw.rectangle([width//2 - 90, height-100, width//2 + 90, height-10], outline=line_color, width=3) 
    
    draw.rectangle([0, 0, width, 45], fill=(0, 0, 0, 220))
    draw.rectangle([0, height-35, width, height], fill=(0, 0, 0, 220))

    try: 
        title_font = ImageFont.truetype(FONT_PATH, 24)
        name_font = ImageFont.truetype(FONT_PATH, 11)
        stat_font = ImageFont.truetype(FONT_PATH, 13)
        overall_font = ImageFont.truetype(FONT_PATH, 16)
        pos_font = ImageFont.truetype(FONT_PATH, 12)
    except Exception: 
        title_font = name_font = stat_font = overall_font = pos_font = ImageFont.load_default()

    nome_time = club_name or "Clube Sem Nome"
    draw.text((width//2, 22), nome_time.upper(), font=title_font, fill="#f1c40f", anchor="mm")
    
    total_overall = 0
    total_value = 0
    
    for i, player in enumerate(team_players):
        cx, cy = POSITIONS_COORDS[i]
        cw, ch = 54, 84
        card_box = [cx - cw//2, cy - ch//2, cx + cw//2, cy + ch//2]
        
        if player:
            player = add_player_defaults(player)
            eff_ovr = get_player_effective_overall(player)
            total_overall += eff_ovr
            total_value += player['value']
            
            if eff_ovr >= 90: card_bg = (45, 10, 60, 240); border = "#e74c3c" 
            elif eff_ovr >= 80: card_bg = (30, 30, 30, 240); border = "#f1c40f" 
            elif eff_ovr >= 70: card_bg = (50, 50, 50, 240); border = "#bdc3c7" 
            else: card_bg = (60, 40, 30, 240); border = "#cd7f32" 
            
            draw.rounded_rectangle(card_box, radius=5, fill=card_bg, outline=border, width=2)
            
            try:
                p_img_res = requests.get(player["image"], timeout=3)
                p_img = Image.open(BytesIO(p_img_res.content)).convert("RGBA")
                p_img.thumbnail((44, 44), Image.Resampling.LANCZOS)
                field_img.paste(p_img, (int(cx - p_img.width//2), int(cy - 30)), p_img)
            except: 
                pass
            
            disp_name = player.get('nickname') or player['name'].split(' ')[-1]
            disp_name = disp_name[:11] 
            
            draw.rounded_rectangle([cx - cw//2 + 2, cy + 20, cx + cw//2 - 2, cy + 36], radius=2, fill=(0,0,0,180))
            draw.text((cx, cy + 28), disp_name.upper(), font=name_font, fill="white", anchor="mm") 
            draw.text((cx - cw//2 + 5, cy - ch//2 + 5), player['position'], font=pos_font, fill=border, anchor="la") 
            draw.text((cx + cw//2 - 4, cy - ch//2 + 4), str(eff_ovr), font=overall_font, fill=border, anchor="ra") 
        else:
            draw.rounded_rectangle(card_box, radius=5, fill=(0,0,0,100), outline=(255,255,255,50), width=2)
            draw.text((cx, cy), "+", font=title_font, fill=(255,255,255,100), anchor="mm")

    draw.text((15, height - 17), f"⭐ OVR: {total_overall}", font=stat_font, fill="#f1c40f", anchor="lm")
    draw.text((width - 15, height - 17), f"💰 R$ {total_value:,}", font=stat_font, fill="#2ecc71", anchor="rm")
    
    buffer = BytesIO()
    field_img.save(buffer, format='PNG', optimize=True)
    buffer.seek(0)
    return buffer

async def generate_team_image(team_players, user):
    user_data = await get_user_data(user.id)
    club_name = user_data.get('club_name') or f"Clube de {user.display_name}"
    return await asyncio.to_thread(create_team_image_sync, team_players, club_name)

# --- 7. CLASSES DE INTERAÇÃO (VIEWS & PAGINATORS) ---

class AddPlayerView(discord.ui.View):
    def __init__(self, author, rbx, img): 
        super().__init__(timeout=120)
        self.author, self.rbx, self.img = author, rbx, img

    @discord.ui.button(label="Definir Status", style=discord.ButtonStyle.success, emoji="⚙️")
    async def btn(self, inter, b): 
        if inter.user == self.author: 
            await inter.response.send_modal(AddPlayerModal(self.rbx, self.img))

class EditPlayerView(discord.ui.View):
    def __init__(self, author, nick): 
        super().__init__(timeout=120)
        self.author, self.nick = author, nick

    @discord.ui.button(label="Editar OVR", style=discord.ButtonStyle.primary, emoji="📝")
    async def btn(self, inter, b): 
        if inter.user == self.author: 
            await inter.response.send_modal(EditPlayerModal(self.nick))

class KeepOrSellView(discord.ui.View):
    def __init__(self, author, player): 
        super().__init__(timeout=60)
        self.author, self.player = author, player

    @discord.ui.button(label="Manter no Elenco", style=discord.ButtonStyle.green)
    async def keep(self, inter, btn):
        if inter.user != self.author: return
        async with data_lock:
            u = await get_user_data(self.author.id)
            if self.player['name'] in u["contracted_players"]: 
                return await inter.response.send_message("Já possui!", ephemeral=True)
            u['squad'].append(self.player)
            u['contracted_players'].append(self.player['name'])
            await save_user_data(self.author.id, u)
        await inter.response.edit_message(content=f"✅ **{self.player['name']}** guardado!", embed=None, view=None)

    @discord.ui.button(label="Vender Rápido", style=discord.ButtonStyle.red)
    async def sell(self, inter, btn):
        if inter.user != self.author: return
        p = int(self.player['value'] * SALE_PERCENTAGE)
        async with data_lock:
            u = await get_user_data(self.author.id)
            u['money'] += p
            await save_user_data(self.author.id, u)
        await inter.response.edit_message(content=f"💰 Vendido por **R$ {p:,}**.", embed=None, view=None)

class ActionView(discord.ui.View):
    def __init__(self, ctx, res, action_type, user_data):
        super().__init__(timeout=120)
        self.ctx = ctx
        self.res = res
        self.action_type = action_type 
        self.user_data = user_data
        self.i = 0
        
        if self.action_type == 'escalar':
            self.children[2].label = "Escalar Titular"
            self.children[2].style = discord.ButtonStyle.primary
        elif self.action_type == 'vender':
            self.children[2].label = "Vender Atleta"
            self.children[2].style = discord.ButtonStyle.danger
        elif self.action_type == 'contratar':
            self.children[2].label = "Assinar Contrato"
            self.children[2].style = discord.ButtonStyle.success

    async def get_page(self):
        p = self.res[self.i]
        
        if self.action_type == 'contratar':
            title = "🛒 Mercado de Transferências"
            color = discord.Color.blue()
            desc = "Avalie as opções e feche a contratação!"
        elif self.action_type == 'vender':
            title = "💰 Venda de Jogador"
            color = discord.Color.red()
            desc = "Tem certeza que deseja liberar este atleta?"
        else:
            title = "📋 Escalar Jogador"
            color = discord.Color.green()
            desc = "Selecione a melhor peça para sua prancheta."

        emb = discord.Embed(title=title, description=desc, color=color)
        emb.add_field(name="👤 Atleta", value=f"**{p['name']}**", inline=True)
        emb.add_field(name="⭐ OVR", value=f"`{p['overall']}`", inline=True)
        emb.add_field(name="📍 Posição", value=f"`{p['position']}`", inline=True)
        
        if self.action_type == 'contratar':
            emb.add_field(name="💰 Custo de Contrato", value=f"R$ **{p['value']:,}**", inline=False)
        elif self.action_type == 'vender':
            emb.add_field(name="💰 Valor de Venda", value=f"R$ **{int(p['value'] * SALE_PERCENTAGE):,}**", inline=False)
        
        emb.set_footer(text=f"Página {self.i + 1}/{len(self.res)} | Seu Saldo: R$ {self.user_data['money']:,}")
        
        buf = await asyncio.to_thread(render_single_card_sync, p)
        file = discord.File(buf, "card.png")
        emb.set_image(url="attachment://card.png")
        
        return emb, file

    async def update_view(self, inter=None):
        self.children[0].disabled = (self.i == 0)
        self.children[1].disabled = (self.i == len(self.res) - 1)
        emb, file = await self.get_page()
        if inter:
            await inter.response.edit_message(embed=emb, attachments=[file], view=self)
        else:
            return emb, file

    @discord.ui.button(label="⏪", style=discord.ButtonStyle.grey, disabled=True)
    async def prev(self, inter, b): 
        if inter.user != self.ctx.author: return
        self.i -= 1
        await self.update_view(inter)

    @discord.ui.button(label="⏩", style=discord.ButtonStyle.grey)
    async def next(self, inter, b): 
        if inter.user != self.ctx.author: return
        self.i += 1
        await self.update_view(inter)

    @discord.ui.button(label="Ação", style=discord.ButtonStyle.primary)
    async def act(self, inter, b): 
        if inter.user != self.ctx.author: return
        p = self.res[self.i]
        
        if self.action_type == 'contratar':
            async with data_lock:
                u_data = await get_user_data(self.ctx.author.id)
                if p['name'] in u_data["contracted_players"]: 
                    return await inter.response.send_message("❌ Você já possui este atleta no elenco!", ephemeral=True)
                if u_data['money'] < p['value']: 
                    return await inter.response.send_message(f"💸 Saldo insuficiente! Faltam R$ {(p['value'] - u_data['money']):,}", ephemeral=True)
                
                u_data['money'] -= p['value']
                u_data['squad'].append(p)
                u_data['contracted_players'].append(p['name'])
                await save_user_data(self.ctx.author.id, u_data)
                
            success_emb = discord.Embed(title="🤝 NEGÓCIO FECHADO!", description=f"Você contratou **{p['name']}** com sucesso!", color=discord.Color.green())
            success_emb.add_field(name="💰 Preço Pago", value=f"R$ {p['value']:,}", inline=True)
            success_emb.add_field(name="🏦 Saldo Restante", value=f"R$ {u_data['money']:,}", inline=True)
            await inter.response.edit_message(embed=success_emb, attachments=[], view=None)

        elif self.action_type == 'vender':
            async with data_lock:
                u_data = await get_user_data(self.ctx.author.id)
                if p['name'] not in u_data['contracted_players']:
                    return await inter.response.send_message("❌ Este atleta não está mais no seu elenco.", ephemeral=True)
                u_data['squad'] = [x for x in u_data['squad'] if x['name'] != p['name']]
                u_data['contracted_players'].remove(p['name'])
                for idx, x in enumerate(u_data['team']): 
                    if x and x['name'] == p['name']: 
                        u_data['team'][idx] = None
                cash = int(p['value'] * SALE_PERCENTAGE)
                u_data['money'] += cash
                await save_user_data(self.ctx.author.id, u_data)
            
            emb = discord.Embed(title="💰 VENDA CONCLUÍDA!", description=f"**{p['name']}** deixou o clube.", color=discord.Color.green())
            emb.add_field(name="💵 Valor Recebido", value=f"R$ {cash:,}", inline=False)
            await inter.response.edit_message(embed=emb, attachments=[], view=None)

        elif self.action_type == 'escalar':
            async with data_lock:
                d = await get_user_data(self.ctx.author.id)
                t = d['team']
                if any(x and x['name'] == p['name'] for x in t): 
                    return await inter.response.send_message("❌ Já é titular.", ephemeral=True)
                done = False
                for pos in p['position'].split('/'):
                    if pos in SLOT_MAPPING:
                        for idx in SLOT_MAPPING[pos]:
                            if t[idx] is None: 
                                t[idx] = p
                                done = True
                                break
                    if done: break
                if done: 
                    await save_user_data(self.ctx.author.id, d)
                    emb = discord.Embed(title="✅ JOGADOR ESCALADO!", description=f"**{p['name']}** agora é o dono da posição.", color=discord.Color.green())
                    await inter.response.edit_message(embed=emb, attachments=[], view=None)
                else: 
                    await inter.response.send_message("❌ Sem vaga livre para essa posição na prancheta 6v6.", ephemeral=True)

# --- 8. EVENTOS DO BOT ---

@bot.event
async def on_ready():
    print(f'🟢 EFL Guru ONLINE! Todas as linhas carregadas e Render ativado.')
    fetch_and_parse_players()
    await bot.change_presence(activity=discord.Game(name=f"{BOT_PREFIX}help | EFL Pro 6v6"))

@bot.check
async def maintenance_check(ctx):
    global MAINTENANCE_MODE
    if MAINTENANCE_MODE and not ctx.author.guild_permissions.administrator:
        await ctx.send("🛠️ **SISTEMA EM MANUTENÇÃO.**")
        return False
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
    global MAINTENANCE_MODE
    MAINTENANCE_MODE = True
    await ctx.send("🛑 **SISTEMA BLOQUEADO.**")

@bot.command(name='unlock')
@commands.has_permissions(administrator=True)
async def unlock_cmd(ctx):
    global MAINTENANCE_MODE
    MAINTENANCE_MODE = False
    await ctx.send("🟢 **SISTEMA LIBERADO.**")

def get_roblox_data_sync(username):
    try:
        res = requests.post("https://users.roblox.com/v1/usernames/users", json={"usernames": [username]}, timeout=5).json()
        if not res.get("data"): return None
        uid = res["data"][0]["id"]
        res2 = requests.get(f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={uid}&size=420x420&format=Png&isCircular=false", timeout=5).json()
        return res2["data"][0]["imageUrl"] if res2.get("data") else None
    except: 
        return None

@bot.command(name='addplayer')
@commands.has_permissions(administrator=True)
async def add_player_cmd(ctx, *, query: str):
    msg = await ctx.send("🔄 Verificando Roblox...")
    try:
        member = await commands.MemberConverter().convert(ctx, query)
        rbx_name = member.display_name.split()[-1].strip()
    except: 
        rbx_name = query.strip()
    
    img = await asyncio.to_thread(get_roblox_data_sync, rbx_name)
    if not img: 
        return await msg.edit(content=f"❌ Nick `{rbx_name}` não existe.")
    
    view = AddPlayerView(ctx.author, rbx_name, img)
    emb = discord.Embed(title="📸 Perfil Encontrado", color=discord.Color.green())
    emb.set_thumbnail(url=img)
    await msg.edit(content=None, embed=emb, view=view)

@bot.command(name='bulkadd')
@commands.has_permissions(administrator=True)
async def bulk_add_cmd(ctx):
    if not ctx.message.attachments: 
        return await ctx.send("❌ Anexe um arquivo `.txt`.")
    att = ctx.message.attachments[0]
    status = await ctx.send("⏳ **Iniciando Bulk Add...**")
    try:
        content = (await att.read()).decode('utf-8')
        lines = content.strip().split('\n')
        res = supabase.table("jogadores").select("data").eq("id", "ROBLOX_CARDS").execute()
        cards = res.data[0]["data"] if res.data else []
        names = [p['name'].lower() for p in cards]
        added = []
        for line in lines:
            parts = line.split()
            if len(parts) < 3: 
                continue
                
            n = parts[0].strip()
            ovr = int(parts[1].strip())
            pos = parts[2].strip().upper()
            
            if n.lower() in names or pos not in SLOT_MAPPING: 
                continue
                
            img = await asyncio.to_thread(get_roblox_data_sync, n)
            if img:
                cards.append({"name": n, "image": img, "overall": ovr, "position": pos, "value": ovr*25000})
                names.append(n.lower())
                added.append(n)
                await asyncio.sleep(0.4)
                
        if added: 
            supabase.table("jogadores").upsert({"id": "ROBLOX_CARDS", "data": cards}).execute()
            fetch_and_parse_players()
        await status.edit(content=f"✅ Adicionados: **{len(added)}** atletas.")
    except Exception as e: 
        await status.edit(content=f"❌ Erro no formato. Use: Nick OVR Pos\nDetalhe: {e}")

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
    if not livres: 
        return await ctx.send("❌ Mercado vazio!")
    p = random.choice(livres)
    async with image_lock: 
        buf = await asyncio.to_thread(render_single_card_sync, p)
    await ctx.send(content="🃏 **OLHEIRO:** Você encontrou um talento solto pelo mundo!", file=discord.File(buf, "card.png"), view=KeepOrSellView(ctx.author, p))

@bot.command(name='contratar')
async def contratar_cmd(ctx, *, q: str):
    sq = normalize_str(q)
    u = await get_user_data(ctx.author.id)
    matches = [p for p in ALL_PLAYERS if sq in normalize_str(p['name']) or sq.upper() in p['position']]
    
    if not matches: 
        return await ctx.send("❌ Nenhum atleta encontrado no mercado com esse nome ou posição.")
    
    v = ActionView(ctx, matches, 'contratar', u)
    emb, file = await v.update_view()
    await ctx.send(embed=emb, file=file, view=v)

@bot.command(name='cofre')
async def cofre_cmd(ctx):
    d = await get_user_data(ctx.author.id)
    await ctx.send(f"🏦 **SALDO DA CONTA:** R$ {d['money']:,}")

@bot.command(name='donate')
async def donate_cmd(ctx, target: discord.Member, amount: int):
    if ctx.author == target or amount <= 0: return
    async with data_lock:
        s_data = await get_user_data(ctx.author.id)
        t_data = await get_user_data(target.id)
        if s_data['money'] < amount: 
            return await ctx.send("❌ Saldo insuficiente para essa doação.")
        s_data['money'] -= amount
        t_data['money'] += amount
        await save_user_data(ctx.author.id, s_data)
        await save_user_data(target.id, t_data)
    await ctx.send(f"💸 **TRANSFERÊNCIA CONCLUÍDA:** R$ {amount:,} enviados para {target.display_name}!")

@bot.command(name='sell')
async def sell_cmd(ctx, *, q: str):
    sq = normalize_str(q)
    d = await get_user_data(ctx.author.id)
    matches = [p for p in d['squad'] if sq in normalize_str(p['name'])]
    
    if not matches: 
        return await ctx.send("❌ Este atleta não foi encontrado no seu elenco atual.")
    
    v = ActionView(ctx, matches, 'vender', d)
    emb, file = await v.update_view()
    await ctx.send(embed=emb, file=file, view=v)

@bot.command(name='escalar')
async def escalar_cmd(ctx, *, q: str):
    sq = normalize_str(q)
    d = await get_user_data(ctx.author.id)
    matches = [p for p in d['squad'] if sq in normalize_str(p['name'])]
    
    if not matches: 
        return await ctx.send("❌ Atleta não encontrado no seu elenco. Contrate-o primeiro!")
    
    v = ActionView(ctx, matches, 'escalar', d)
    emb, file = await v.update_view()
    await ctx.send(embed=emb, file=file, view=v)

@bot.command(name='elenco')
async def elenco_cmd(ctx):
    d = await get_user_data(ctx.author.id)
    if not d['squad']: 
        return await ctx.send("❌ Seu elenco está vazio. Digite `--obter` ou `--contratar` para buscar atletas.")
        
    txt = "\n".join([f"**{p['position']}** | {p['name']} | ⭐ {p['overall']}" for p in sorted(d['squad'], key=lambda x: x['overall'], reverse=True)[:25]])
    
    emb = discord.Embed(title=f"🎽 Elenco de {ctx.author.display_name}", description=txt, color=discord.Color.blue())
    emb.set_footer(text=f"Total de atletas no clube: {len(d['squad'])}")
    await ctx.send(embed=emb)

@bot.command(name='team')
async def team_cmd(ctx):
    d = await get_user_data(ctx.author.id)
    if not any(d['team']): 
        return await ctx.send("❌ Sua prancheta está vazia. Use `--escalar <nome>` para montar o time.")
    msg = await ctx.send("⚙️ Desenhando prancheta 6v6...")
    async with image_lock:
        try:
            buf = await asyncio.to_thread(create_team_image_sync, d['team'], d.get('club_name') or ctx.author.name)
            await ctx.send(file=discord.File(buf, "team.png"))
            await msg.delete()
        except: 
            await msg.edit(content="❌ Erro na geração do gráfico.")

@bot.command(name='confrontar')
async def confrontar_cmd(ctx, oponente: discord.Member):
    if ctx.author == oponente or oponente.bot: 
        return
    d1 = await get_user_data(ctx.author.id)
    d2 = await get_user_data(oponente.id)
    if None in d1['team'] or None in d2['team']: 
        return await ctx.send("🚨 Para iniciar a partida, AMBOS os times precisam ter os 6 titulares na prancheta!")
        
    s1, s2 = 0, 0
    log = ["🎙️ **O árbitro apita e rola a bola pro jogo 6v6!**"]
    emb = discord.Embed(title=f"🏟️ {ctx.author.name} x {oponente.name}", description="0 - 0", color=discord.Color.dark_grey())
    msg = await ctx.send(embed=emb)
    
    for min in [30, 60, 90]:
        await asyncio.sleep(2.5)
        f1 = sum(x['overall'] for x in d1['team'] if x)
        f2 = sum(x['overall'] for x in d2['team'] if x)
        
        if f1 + random.randint(0,40) > f2 + random.randint(0,40):
            at = random.choice([p for p in d1['team'] if p])['name']
            log.append(f"{min}' " + random.choice(GOAL_NARRATIONS).format(attacker=at))
            s1 += 1
        elif f2 + random.randint(0,40) > f1 + random.randint(0,40):
            at = random.choice([p for p in d2['team'] if p])['name']
            log.append(f"{min}' " + random.choice(GOAL_NARRATIONS).format(attacker=at))
            s2 += 1
        else:
            gk = random.choice([p for p in d2['team'] if p and p['position'] == 'GK'] or [p for p in d2['team'] if p])['name']
            log.append(f"{min}' " + random.choice(SAVE_NARRATIONS).format(keeper=gk, attacker="adv"))
            
        emb.description = f"### Placar: {s1} - {s2}\n" + "\n".join(log[-3:])
        await msg.edit(embed=emb)
        
    if s1 > s2: 
        d1['wins'] += 1
        d2['losses'] += 1
        res = f"Fim de jogo! Vitória absoluta de **{ctx.author.name}**!"
    elif s2 > s1: 
        d2['wins'] += 1
        d1['losses'] += 1
        res = f"Fim de jogo! O time de **{oponente.name}** amassa e leva a vitória!"
    else: 
        res = "Fim de papo! Jogo muito pegado que termina em Empate!"
        
    await save_user_data(ctx.author.id, d1)
    await save_user_data(oponente.id, d2)
    await ctx.send(f"🏁 **FIM:** {res}")

@bot.command(name='ranking')
async def ranking_cmd(ctx):
    res = supabase.table("jogadores").select("id", "data").execute()
    users = sorted([x for x in res.data if x['id'] != "ROBLOX_CARDS"], key=lambda u: u["data"].get("wins", 0), reverse=True)[:10]
    txt = "\n".join([f"**{i+1}.** <@{u['id']}> — `{u['data'].get('wins',0)}` Vitórias" for i, u in enumerate(users)])
    await ctx.send(embed=discord.Embed(title="🏆 Ranking LTPS", description=txt or "Ainda não houve partidas registradas.", color=discord.Color.gold()))

@bot.command(name='help')
async def help_cmd(ctx):
    emb = discord.Embed(title="📜 Painel de Ajuda", description="Seja bem-vindo ao mercado EFL Pro! Abaixo estão os comandos disponíveis:", color=discord.Color.gold())
    emb.add_field(name="💰 Gestão & Economia", value="`--cofre`, `--donate`, `--contratar`, `--sell`, `--obter`", inline=False)
    emb.add_field(name="📋 Vestiário & Tática", value="`--elenco`, `--escalar`, `--team` ", inline=False)
    emb.add_field(name="⚽ Partidas", value="`--confrontar`, `--ranking` ")
    emb.add_field(name="⚙️ Administração", value="`--addplayer`, `--bulkadd`, `--editplayer`, `--lock`, `--unlock` ")
    emb.set_footer(text="Versão 30.9 - Desenvolvido para a comunidade LTPS")
    await ctx.send(embed=emb)

# --- INICIALIZAÇÃO ---
if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if token: 
        keep_alive() # INICIA O SERVIDOR WEB PARA O UPTIMEROBOT
        bot.run(token)
    else: 
        print("❌ Token ausente no arquivo .env.")
