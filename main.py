# -*- coding: utf-8 -*-
"""
EFL Guru - Versão 34.0 (A MURALHA INQUEBRÁVEL - AUTO-ESCALAR E LIVE UPDATE)
----------------------------------------------------------------------
- CÓDIGO BRUTO: Formatação original preservada. NENHUMA linha comprimida.
- NOVO BOTÃO AUTO-ESCALAR: Preenche a prancheta com os melhores do elenco.
- LIVE UPDATE NA PRANCHETA: Mudar tática, limpar, auto-escalar ou escolher capitão agora atualiza a imagem em tempo real na mesma mensagem.
- SISTEMA ANALYZEMEMBERS: Comando secreto para filtrar e cadastrar membros em massa.
- FIX DE ESPAÇAMENTO: Altura da imagem ampliada para 1240px.
- FIX GOLEIRO: Carta do PO descida para não sobrepor com os DFCs.
- OVR MÍNIMO: Base do sistema ajustada de 60 para 70.
- NOVA ECONOMIA: Saldo inicial reduzido para 1.000.000 (1 Milhão).
- VALORIZAÇÃO DE OVR: Cálculo de valor exponencial.
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
INITIAL_MONEY = 1000000  # Saldo Inicial ajustado para 1 Milhão
SALE_PERCENTAGE = 0.5

def calculate_player_value(ovr):
    """Calcula o valor do jogador com curva exponencial. Quanto maior o OVR, MUITO mais caro."""
    return int((ovr ** 3) * 1.5)

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

ensure_font_exists()

# --- MOTOR TÁTICO DINÂMICO ---
def get_formation_config(formation):
    """Retorna as coordenadas HD (x2) e o mapeamento de vagas dependendo da tática"""
    if formation == "4-4-2":
        coords = {
            0: (420, 1060),  # PO descido
            1: (120, 820), 2: (320, 830), 3: (520, 830), 4: (720, 820),  # 4 DFC alinhados
            5: (150, 530), 6: (330, 560), 7: (510, 560), 8: (690, 530),  # 4 Meias
            9: (300, 200), 10: (540, 200)  # 2 DC
        }
        mapping = {
            "PO": [0], "GK": [0], "GOL": [0],
            "DFC": [1, 2, 3, 4], "CB": [1, 2, 3, 4], "ZAG": [1, 2, 3, 4],
            "MDC": [5, 6, 7, 8], "MC": [5, 6, 7, 8], "MCO": [5, 6, 7, 8], "VOL": [5, 6, 7, 8],
            "DC": [9, 10], "ST": [9, 10], "CA": [9, 10]
        }
    elif formation == "3-4-3":
        coords = {
            0: (420, 1060),  # PO descido
            1: (200, 830), 2: (420, 850), 3: (640, 830),  # 3 DFC
            4: (150, 530), 5: (330, 560), 6: (510, 560), 7: (690, 530),  # 4 Meias
            8: (170, 240), 9: (420, 190), 10: (670, 240)  # 3 DC
        }
        mapping = {
            "PO": [0], "GK": [0], "GOL": [0],
            "DFC": [1, 2, 3], "CB": [1, 2, 3], "ZAG": [1, 2, 3],
            "MDC": [4, 5, 6, 7], "MC": [4, 5, 6, 7], "MCO": [4, 5, 6, 7], "VOL": [4, 5, 6, 7],
            "DC": [8, 9, 10], "ST": [8, 9, 10], "CA": [8, 9, 10]
        }
    else:  # Padrão: 4-3-3 Restrita
        coords = {
            0: (420, 1060),  # PO descido
            1: (120, 820), 2: (320, 830), 3: (520, 830), 4: (720, 820),  # 4 DFC alinhados
            5: (200, 530), 6: (420, 560), 7: (640, 530),  # 3 Meias
            8: (170, 240), 9: (420, 190), 10: (670, 240)  # 3 DC
        }
        mapping = {
            "PO": [0], "GK": [0], "GOL": [0],
            "DFC": [1, 2, 3, 4], "CB": [1, 2, 3, 4], "ZAG": [1, 2, 3, 4],
            "MDC": [5, 6, 7], "MC": [5, 6, 7], "MCO": [5, 6, 7], "VOL": [5, 6, 7],
            "DC": [8, 9, 10], "ST": [8, 9, 10], "CA": [8, 9, 10]
        }
    return coords, mapping

POS_MIGRATION = {
    "ST": "DC", "CA": "DC", "PE": "DC", "PD": "DC", "LW": "DC", "RW": "DC", "LF": "DC", "RF": "DC",
    "CB": "DFC", "ZAG": "DFC", "LE": "DFC", "LD": "DFC", "LB": "DFC", "RB": "DFC",
    "GK": "PO", "GOL": "PO"
}

ALL_PLAYERS = []
data_lock = asyncio.Lock()
image_lock = asyncio.Lock()

MAINTENANCE_MODE = False
active_matches = set()

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

# --- 2. SISTEMAS DE TEXTOS (NARRAÇÃO) ---
GOAL_NARRATIONS = [
    "⚽ GOOOOLAAAAÇO! {attacker} mandou uma bomba do meio da rua! Onde a coruja dorme!",
    "⚽ É REDE! {attacker} dribla a zaga inteira, deixa o goleiro no chão e empurra pro gol vazio!",
    "⚽ GOOOOL! {attacker} recebe cruzamento perfeito na medida e testa firme pro fundo do barbante!",
    "⚽ PINTURA! {attacker} domina no peito na entrada da área e emenda um lindo voleio!",
    "⚽ TÁ LÁ DENTRO! {attacker} sai cara a cara, não desperdiça a chance e guarda no cantinho!"
]

SAVE_NARRATIONS = [
    "🧤 MILAAAAGRE! {keeper} voa como um gato no ângulo e espalma o chute cruzado para escanteio!",
    "🧤 INCRÍVEL! {keeper} salva no puro reflexo com a ponta da chuteira! Que defesa espetacular!",
    "🧱 PAREDE! {keeper} sai bem do gol, fecha o ângulo, cresce pra cima de {attacker} e defende com o peito!",
    "🧤 SEGURO! {keeper} cai no canto certinho e encaixa a cobrança de falta sem dar rebote."
]

MISS_NARRATIONS = [
    "💥 NA TRAAAAVE! {attacker} solta um foguete de fora da área que explode no poste superior!",
    "❌ PRA FOOORA! {attacker} tenta tirar demais do goleiro e a bola vai pela linha de fundo."
]

FOUL_NARRATIONS = [
    "🟨 Cartão amarelo! Falta dura no meio de campo parando o contra-ataque adversário.",
    "🛑 Jogo parado. O juiz marca falta muito perigosa na entrada da área! Tensão no estádio."
]

BUILD_NARRATIONS = [
    "👟 O time troca passes curtos no meio-campo, estudando a defesa adversária com paciência...",
    "🔄 Posse de bola, tentativa de inversão de jogo que acaba saindo forte demais e sai pela lateral."
]

ACHIEVEMENTS = {
    "primeira_vitoria": {"name": "Primeira Vitória", "desc": "Vença sua primeira partida na EFL.", "emoji": "🏆"}
}

# --- 3. MOTOR GRÁFICO (CARD RENDER GERAL) ---

def render_single_card_sync(player):
    """Gera uma imagem de card individual estilo EA FC com fade e fontes robustas"""
    c_w, c_h = 300, 450
    card = Image.new("RGBA", (c_w, c_h), (0, 0, 0, 0))
    
    ovr = player.get('overall', 70)
    
    if ovr >= 90: # Special
        c_top = (70, 15, 90)
        c_bot = (30, 5, 40)
        border_color = "#f39c12"
        txt_color = "#f1c40f"
    elif ovr >= 80: # Gold
        c_top = (60, 50, 20)
        c_bot = (20, 18, 5)
        border_color = "#f1c40f"
        txt_color = "white"
    elif ovr >= 75: # Prata
        c_top = (85, 85, 85)
        c_bot = (30, 30, 30)
        border_color = "#bdc3c7"
        txt_color = "white"
    else: # Bronze
        c_top = (100, 70, 45)
        c_bot = (40, 25, 15)
        border_color = "#cd7f32"
        txt_color = "white"

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
        p_img_res = requests.get(player["image"], timeout=5)
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

    try:
        f_ovr = ImageFont.truetype(FONT_PATH, 90)
        f_pos = ImageFont.truetype(FONT_PATH, 45)
    except:
        f_ovr = f_pos = ImageFont.load_default()

    draw.text((35, 30), str(ovr), font=f_ovr, fill=border_color, anchor="la")
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

# --- 4. CLASSES DE FORMULÁRIOS E PARTIDA (VIEWS E MODALS) ---

class AddPlayerModal(discord.ui.Modal, title='Definir Status da Carta'):
    def __init__(self, rbx_name, img_url):
        super().__init__()
        self.rbx_name, self.img_url = rbx_name, img_url
        self.ovr = discord.ui.TextInput(label='Overall (OVR)', placeholder='85', min_length=1, max_length=2)
        self.pos = discord.ui.TextInput(label='Posição (PO, DFC, MC, DC...)', placeholder='Ex: DC', min_length=2, max_length=3)
        self.add_item(self.ovr)
        self.add_item(self.pos)

    async def on_submit(self, inter: discord.Interaction):
        try:
            o_int = int(self.ovr.value)
            p_str = self.pos.value.upper().strip()
            
            if p_str in POS_MIGRATION:
                p_str = POS_MIGRATION[p_str]
                
            coords, mapping = get_formation_config("4-3-3")
            if p_str not in mapping:
                return await inter.response.send_message(f"❌ Posição `{p_str}` inválida.", ephemeral=True)
                
            v_int = calculate_player_value(o_int)
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
        self.pos = discord.ui.TextInput(label='Nova Posição (DC, DFC, PO)', placeholder='Ex: DC', min_length=2, max_length=3)
        self.add_item(self.ovr)
        self.add_item(self.pos)
        
    async def on_submit(self, inter: discord.Interaction):
        try:
            o = int(self.ovr.value)
            v = calculate_player_value(o)
            p_str = self.pos.value.upper().strip()
            
            if p_str in POS_MIGRATION:
                p_str = POS_MIGRATION[p_str]
                
            coords, mapping = get_formation_config("4-3-3")
            if p_str not in mapping:
                return await inter.response.send_message(f"❌ Posição `{p_str}` inválida.", ephemeral=True)

            async with data_lock:
                res = supabase.table("jogadores").select("data").eq("id", "ROBLOX_CARDS").execute()
                cards = res.data[0]["data"]
                for p in cards:
                    if p['name'].lower() == self.nick.lower():
                        p['overall'] = o
                        p['value'] = v
                        p['position'] = p_str
                        break
                supabase.table("jogadores").update({"data": cards}).eq("id", "ROBLOX_CARDS").execute()
                fetch_and_parse_players()
            await inter.response.send_message(f"✅ **{self.nick}** atualizado para {o} OVR e Posição {p_str}! (A atualização no time dos jogadores ocorrerá automaticamente).")
        except:
            await inter.response.send_message("❌ Erro na edição.", ephemeral=True)

# --- NOVO SISTEMA ANALYZEMEMBERS (MODAL E VIEW) ---

class AnalyzeAddModal(discord.ui.Modal, title='Cadastrar no DB'):
    def __init__(self, view_instance, rbx_name, img_url):
        super().__init__()
        self.view_instance = view_instance
        self.rbx_name = rbx_name
        self.img_url = img_url
        self.ovr = discord.ui.TextInput(label='Overall (OVR)', placeholder='75', min_length=1, max_length=2)
        self.pos = discord.ui.TextInput(label='Posição (PO, DFC, MDC, DC...)', placeholder='Ex: MC', min_length=2, max_length=3)
        self.add_item(self.ovr)
        self.add_item(self.pos)

    async def on_submit(self, inter: discord.Interaction):
        try:
            o_int = int(self.ovr.value)
            p_str = self.pos.value.upper().strip()
            
            if p_str in POS_MIGRATION:
                p_str = POS_MIGRATION[p_str]
                
            coords, mapping = get_formation_config("4-3-3")
            if p_str not in mapping:
                return await inter.response.send_message(f"❌ Posição `{p_str}` inválida.", ephemeral=True)
                
            v_int = calculate_player_value(o_int)
            new_p = {"name": self.rbx_name, "image": self.img_url, "overall": o_int, "position": p_str, "value": v_int}
            
            async with data_lock:
                res = supabase.table("jogadores").select("data").eq("id", "ROBLOX_CARDS").execute()
                cards = res.data[0]["data"] if res.data else []
                cards.append(new_p)
                supabase.table("jogadores").upsert({"id": "ROBLOX_CARDS", "data": cards}).execute()
                global ALL_PLAYERS
                fetch_and_parse_players()
                
            await inter.response.send_message(f"✅ **{self.rbx_name}** adicionado ao banco global!", ephemeral=True)
            
            self.view_instance.queue.pop(self.view_instance.index)
            
            if self.view_instance.index >= len(self.view_instance.queue):
                self.view_instance.index = max(0, len(self.view_instance.queue) - 1)
                
            await self.view_instance.update_view()
            
        except Exception as e:
            await inter.response.send_message(f"❌ Erro ao salvar: {e}", ephemeral=True)


class AnalyzeMembersView(discord.ui.View):
    def __init__(self, ctx, queue, message):
        super().__init__(timeout=600)
        self.ctx = ctx
        self.queue = queue
        self.message = message
        self.index = 0

    async def update_view(self):
        if not self.queue:
            emb = discord.Embed(title="✅ Análise Concluída", description="Todos os jogadores da fila foram avaliados ou adicionados.", color=discord.Color.green())
            await self.message.edit(embed=emb, view=None)
            return

        p = self.queue[self.index]
        emb = discord.Embed(title="🔍 Olheiro de Base - Análise", color=discord.Color.purple())
        emb.add_field(name="📛 Discord", value=p['discord_name'], inline=True)
        emb.add_field(name="🎮 Roblox Nick", value=f"**{p['nick']}**", inline=True)
        emb.set_image(url=p['image'])
        emb.set_footer(text=f"Membro {self.index + 1} de {len(self.queue)} na fila de espera.")

        self.children[0].disabled = (self.index == 0)
        self.children[1].disabled = (self.index == len(self.queue) - 1)
        
        await self.message.edit(embed=emb, view=self)

    @discord.ui.button(label="⏪", style=discord.ButtonStyle.grey)
    async def prev(self, inter: discord.Interaction, b):
        if inter.user != self.ctx.author: return
        await inter.response.defer()
        self.index -= 1
        await self.update_view()

    @discord.ui.button(label="⏩", style=discord.ButtonStyle.grey)
    async def next(self, inter: discord.Interaction, b):
        if inter.user != self.ctx.author: return
        await inter.response.defer()
        self.index += 1
        await self.update_view()

    @discord.ui.button(label="➕ Cadastrar", style=discord.ButtonStyle.success)
    async def add(self, inter: discord.Interaction, b):
        if inter.user != self.ctx.author: return
        p = self.queue[self.index]
        modal = AnalyzeAddModal(self, p['nick'], p['image'])
        await inter.response.send_modal(modal)

# --- SISTEMA DE PARTIDAS CONTINUAÇÃO ---

class MatchInviteView(discord.ui.View):
    def __init__(self, ctx, challenger, opponent, d1, d2):
        super().__init__(timeout=120)
        self.ctx = ctx
        self.challenger = challenger
        self.opponent = opponent
        self.d1 = d1
        self.d2 = d2

    @discord.ui.button(label="Aceitar Desafio", style=discord.ButtonStyle.success, emoji="⚽")
    async def accept(self, inter: discord.Interaction, btn: discord.ui.Button):
        if inter.user != self.opponent:
            return await inter.response.send_message("❌ Apenas o desafiado pode aceitar o convite!", ephemeral=True)
        
        if self.challenger.id in active_matches or self.opponent.id in active_matches:
            return await inter.response.send_message("❌ Um de vocês já está em uma partida ativa! Aguarde o fim do jogo.", ephemeral=True)
        
        await inter.response.defer()
        
        active_matches.add(self.challenger.id)
        active_matches.add(self.opponent.id)
        
        for child in self.children:
            child.disabled = True
        await inter.message.edit(content="⏳ Preparando o gramado da EFL...", view=self)
        
        await simulate_match(self.ctx, self.challenger, self.opponent, self.d1, self.d2, inter.message)

    @discord.ui.button(label="Recusar", style=discord.ButtonStyle.danger, emoji="✖️")
    async def decline(self, inter: discord.Interaction, btn: discord.ui.Button):
        if inter.user != self.opponent:
            return await inter.response.send_message("❌ Apenas o desafiado pode recusar o convite!", ephemeral=True)
        
        for child in self.children:
            child.disabled = True
        await inter.response.edit_message(content=f"🚫 O desafio da EFL foi recusado por {self.opponent.mention}.", view=self)

# --- SISTEMA DE PARTIDA (MOTOR DE JOGO COM CAIXA DE CÓDIGO) ---
async def simulate_match(ctx, challenger, opponent, d1, d2, message):
    try:
        f1 = sum(x['overall'] for x in d1['team'] if x)
        f2 = sum(x['overall'] for x in d2['team'] if x)
        
        diff = f1 - f2
        prob_t1 = max(20, min(80, 50 + diff))

        s1, s2 = 0, 0
        minuto_atual = 0
        meio_tempo_feito = False
        
        event_log = ["🎙️ O juiz apita e a bola está rolando para o jogo da EFL!"]
        
        emb = discord.Embed(title=f"🏟️ EFL: {challenger.display_name} x {opponent.display_name}", color=discord.Color.blue())
        
        while minuto_atual < 90:
            salto = random.randint(4, 13)
            minuto_atual += salto
            
            is_intervalo = False
            
            if minuto_atual >= 45 and not meio_tempo_feito:
                minuto_atual = 45
                meio_tempo_feito = True
                is_intervalo = True
                
            elif minuto_atual > 90:
                minuto_atual = 90
                
            rnd_attack = random.randint(1, 100)
            if rnd_attack <= prob_t1:
                team_attack = challenger.display_name
                team_defend = opponent.display_name
                players_attack = [p for p in d1['team'] if p]
                players_defend = [p for p in d2['team'] if p]
                atacante_id = 1
            else:
                team_attack = opponent.display_name
                team_defend = challenger.display_name
                players_attack = [p for p in d2['team'] if p]
                players_defend = [p for p in d1['team'] if p]
                atacante_id = 2

            if is_intervalo:
                evento_str = f"[{minuto_atual}'] ⏱️ Intervalo na EFL! Fim do primeiro tempo. O juiz aponta o centro e as equipes vão para o vestiário."
            else:
                event_type = random.randint(1, 100)
                jogador_ataque = random.choice(players_attack)['name']
                goleiro_defesa = next((p['name'] for p in players_defend if p['position'] in ['PO', 'GK', 'GOL']), random.choice(players_defend)['name'])
                
                if event_type <= 18:
                    evento_str = f"[{minuto_atual}'] " + random.choice(GOAL_NARRATIONS).format(attacker=jogador_ataque)
                    if atacante_id == 1: s1 += 1
                    else: s2 += 1
                elif event_type <= 40:
                    evento_str = f"[{minuto_atual}'] " + random.choice(SAVE_NARRATIONS).format(keeper=goleiro_defesa, attacker=jogador_ataque)
                elif event_type <= 65:
                    evento_str = f"[{minuto_atual}'] " + random.choice(MISS_NARRATIONS).format(attacker=jogador_ataque)
                elif event_type <= 80:
                    evento_str = f"[{minuto_atual}'] " + random.choice(FOUL_NARRATIONS)
                else:
                    evento_str = f"[{minuto_atual}'] " + random.choice(BUILD_NARRATIONS)

            event_log.append(evento_str)
            if len(event_log) > 6:
                event_log.pop(0)
                
            log_text = "\n\n".join(event_log)
            placar = f"## 🔵 {challenger.display_name} {s1} x {s2} {opponent.display_name} 🔴"
            
            emb.description = f"{placar}\n\n**Lances da Partida:**\n```\n{log_text}\n```"
            await message.edit(content="", embed=emb, view=None)
            
            await asyncio.sleep(3.0)

        if s1 > s2: 
            d1['wins'] += 1
            d2['losses'] += 1
            res = f"Fim de papo na EFL! O árbitro encerra a partida e a vitória é do {challenger.display_name}!"
        elif s2 > s1: 
            d2['wins'] += 1
            d1['losses'] += 1
            res = f"Fim de papo na EFL! O árbitro encerra a partida e o {opponent.display_name} leva a melhor fora de casa!"
        else: 
            res = "Fim de jogo na EFL! Partida disputada no detalhe que termina em Empate!"
            
        await save_user_data(challenger.id, d1)
        await save_user_data(opponent.id, d2)
        
        event_log.append(f"🏁 FIM: {res}")
        if len(event_log) > 7: event_log.pop(0)
        
        log_text = "\n\n".join(event_log)
        emb.description = f"## 🔵 {challenger.display_name} {s1} x {s2} {opponent.display_name} 🔴\n\n**Lances da Partida:**\n```\n{log_text}\n```"
        await message.edit(embed=emb)
        
    finally:
        active_matches.discard(challenger.id)
        active_matches.discard(opponent.id)

# --- 5. BANCO DE DADOS E FUNÇÕES DE JOGADORES (COM AUTO-SYNC GLOBAL) ---

def fetch_and_parse_players():
    global ALL_PLAYERS
    ALL_PLAYERS = []
    try:
        res = supabase.table("jogadores").select("data").eq("id", "ROBLOX_CARDS").execute()
        if res.data:
            comunidade = res.data[0]["data"]
            
            needs_update = False
            for p in comunidade:
                if p.get('position') in POS_MIGRATION:
                    p['position'] = POS_MIGRATION[p['position']]
                    needs_update = True
                
                correct_val = calculate_player_value(p.get('overall', 70))
                if p.get('value', 0) != correct_val:
                    p['value'] = correct_val
                    needs_update = True
            
            if needs_update:
                supabase.table("jogadores").update({"data": comunidade}).eq("id", "ROBLOX_CARDS").execute()
                print("🔄 Mercado atualizado automaticamente com as novas nomenclaturas de posição e curva de economia.")

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
                "contracted_players": [],
                "club_name": None,
                "club_sigla": "EFL",
                "formation": "4-3-3",
                "captain": None
            }
            supabase.table("jogadores").insert({"id": uid, "data": initial}).execute()
            return initial
            
        data = res.data[0]["data"]
        defaults = [
            ("losses", 0), ("achievements", []), ("match_history", []), 
            ("contracted_players", []), ("club_name", None), ("club_sigla", "EFL"),
            ("formation", "4-3-3"), ("captain", None)
        ]
        for key, val in defaults:
            if key not in data: 
                data[key] = val
                
        if "team" not in data or len(data["team"]) != 11:
            old_team = data.get("team", [])
            new_team = [None] * 11
            for idx, p in enumerate(old_team):
                if p and idx < 11: new_team[idx] = p
            data["team"] = new_team

        # --- AUTO-SYNC: ATUALIZA AS CARTAS DO USUÁRIO SE O ADM EDITOU NO BANCO GLOBAL ---
        global ALL_PLAYERS
        global_dict = {p['name'].lower(): p for p in ALL_PLAYERS}
        needs_save = False
        
        for i, p in enumerate(data.get('squad', [])):
            if p:
                if p.get('position') in POS_MIGRATION:
                    p['position'] = POS_MIGRATION[p['position']]
                    needs_save = True
                
                correct_val = calculate_player_value(p.get('overall', 70))
                if p.get('value', 0) != correct_val:
                    p['value'] = correct_val
                    needs_save = True
                    
                if p['name'].lower() in global_dict:
                    gp = global_dict[p['name'].lower()]
                    if p.get('overall') != gp['overall'] or p.get('position') != gp['position']:
                        data['squad'][i]['overall'] = gp['overall']
                        data['squad'][i]['position'] = gp['position']
                        data['squad'][i]['value'] = gp['value']
                        needs_save = True

        for i, p in enumerate(data.get('team', [])):
            if p:
                if p.get('position') in POS_MIGRATION:
                    p['position'] = POS_MIGRATION[p['position']]
                    needs_save = True
                
                correct_val = calculate_player_value(p.get('overall', 70))
                if p.get('value', 0) != correct_val:
                    p['value'] = correct_val
                    needs_save = True
                    
                if p['name'].lower() in global_dict:
                    gp = global_dict[p['name'].lower()]
                    if p.get('overall') != gp['overall'] or p.get('position') != gp['position']:
                        data['team'][i]['overall'] = gp['overall']
                        data['team'][i]['position'] = gp['position']
                        data['team'][i]['value'] = gp['value']
                        needs_save = True
                
        if needs_save:
            try: 
                supabase.table("jogadores").update({"data": data}).eq("id", uid).execute()
            except: 
                pass
            
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
    return player.get('overall', 70) + player.get('training_level', 0)

def add_player_defaults(player):
    if 'nickname' not in player: 
        player['nickname'] = None
    if 'training_level' not in player: 
        player['training_level'] = 0
    return player

# --- 6. GERADOR DE IMAGEM DA PRANCHETA EM HD (840x1240) ---

def create_team_image_sync(team_players, club_name, club_sigla, user_money, formation, captain_name):
    width, height = 840, 1240 
    field_img = Image.new("RGB", (width, height), color="#2E7D32")
    draw = ImageDraw.Draw(field_img, "RGBA")
    
    for i in range(0, height, 50):
        if (i // 50) % 2 == 0: 
            draw.rectangle([0, i, width, i+50], fill="#388E3C")
            
    line_color = (255, 255, 255, 180)
    draw.rectangle([20, 20, width-20, height-20], outline=line_color, width=6) 
    draw.line([20, height//2, width-20, height//2], fill=line_color, width=6) 
    draw.ellipse([width//2 - 100, height//2 - 100, width//2 + 100, height//2 + 100], outline=line_color, width=6) 
    draw.rectangle([width//2 - 180, 20, width//2 + 180, 200], outline=line_color, width=6) 
    draw.rectangle([width//2 - 180, height-200, width//2 + 180, height-20], outline=line_color, width=6) 
    
    draw.rectangle([0, 0, width, 90], fill=(0, 0, 0, 220))
    draw.rectangle([0, height-70, width, height], fill=(0, 0, 0, 220))

    try: 
        title_font = ImageFont.truetype(FONT_PATH, 48)
        stat_font = ImageFont.truetype(FONT_PATH, 26)
        overall_font = ImageFont.truetype(FONT_PATH, 28) 
        pos_font = ImageFont.truetype(FONT_PATH, 22) 
    except Exception: 
        title_font = stat_font = overall_font = pos_font = ImageFont.load_default()

    header_text = f"[{club_sigla or 'EFL'}] {(club_name or 'MEU CLUBE').upper()}"
    draw.text((width//2, 45), header_text, font=title_font, fill="#f1c40f", anchor="mm")
    
    total_overall = 0
    
    coords, mapping = get_formation_config(formation)
    
    for i, player in enumerate(team_players):
        if i not in coords: continue
        cx, cy = coords[i]
        
        cw, ch = 120, 180 
        card_box = [cx - cw//2, cy - ch//2, cx + cw//2, cy + ch//2]
        
        if player:
            player = add_player_defaults(player)
            eff_ovr = get_player_effective_overall(player)
            total_overall += eff_ovr
            
            if eff_ovr >= 90: card_bg = (45, 10, 60, 240); border = "#e74c3c" 
            elif eff_ovr >= 80: card_bg = (30, 30, 30, 240); border = "#f1c40f" 
            elif eff_ovr >= 70: card_bg = (50, 50, 50, 240); border = "#bdc3c7" 
            else: card_bg = (60, 40, 30, 240); border = "#cd7f32" 
            
            shadow_box = [card_box[0] + 6, card_box[1] + 6, card_box[2] + 6, card_box[3] + 6]
            draw.rounded_rectangle(shadow_box, radius=12, fill=(0, 0, 0, 150))
            
            draw.rounded_rectangle(card_box, radius=12, fill=card_bg, outline=border, width=4)
            
            try:
                p_img_res = requests.get(player["image"], timeout=5)
                p_img = Image.open(BytesIO(p_img_res.content)).convert("RGBA")
                p_img.thumbnail((96, 96), Image.Resampling.LANCZOS)
                img_x = int(cx - p_img.width//2)
                img_y = int(cy - ch//2 + 36) 
                field_img.paste(p_img, (img_x, img_y), p_img)
            except: 
                pass
            
            draw.text((cx - cw//2 + 10, cy - ch//2 + 10), player['position'], font=pos_font, fill=border, anchor="la") 
            draw.text((cx + cw//2 - 10, cy - ch//2 + 10), str(eff_ovr), font=overall_font, fill=border, anchor="ra") 

            name_plate_box = [cx - cw//2 + 4, cy + ch//2 - 40, cx + cw//2 - 4, cy + ch//2 - 4]
            draw.rounded_rectangle(name_plate_box, radius=6, fill=(10, 10, 10, 240))
            
            disp_name = player.get('nickname') or player['name'].split(' ')[-1]
            disp_name = disp_name[:12] 
            
            if captain_name and player['name'] == captain_name:
                disp_name += " [C]"
            
            current_name_size = 22
            try:
                name_font = ImageFont.truetype(FONT_PATH, current_name_size)
                while name_font.getlength(disp_name.upper()) > cw - 12 and current_name_size > 10:
                    current_name_size -= 1
                    name_font = ImageFont.truetype(FONT_PATH, current_name_size)
            except:
                name_font = ImageFont.load_default()
                
            color_text = "#f1c40f" if (captain_name and player['name'] == captain_name) else "white"
            draw.text((cx, cy + ch//2 - 22), disp_name.upper(), font=name_font, fill=color_text, anchor="mm") 
        else:
            draw.rounded_rectangle(card_box, radius=10, fill=(0,0,0,100), outline=(255,255,255,50), width=4)
            draw.text((cx, cy), "+", font=title_font, fill=(255,255,255,100), anchor="mm")

    draw.text((30, height - 35), f"OVR: {total_overall} | TATICA: {formation}", font=stat_font, fill="#f1c40f", anchor="lm")
    draw.text((width - 30, height - 35), f"COFRE: R$ {user_money:,}", font=stat_font, fill="#2ecc71", anchor="rm")
    
    buffer = BytesIO()
    field_img.save(buffer, format='PNG', optimize=True)
    buffer.seek(0)
    return buffer

async def generate_team_image(user_data, user):
    team_players = user_data.get('team', [None]*11)
    club_name = user_data.get('club_name') or f"Clube de {user.display_name}"
    club_sigla = user_data.get('club_sigla') or "EFL"
    money = user_data.get('money') or 0
    formation = user_data.get('formation', '4-3-3')
    captain = user_data.get('captain')
    
    return await asyncio.to_thread(create_team_image_sync, team_players, club_name, club_sigla, money, formation, captain)

# --- 7. CLASSES DE INTERAÇÃO E TEAM MANAGER ---

class TeamManagerView(discord.ui.View):
    def __init__(self, ctx, user_data):
        super().__init__(timeout=300)
        self.ctx = ctx
        self.user_data = user_data

    async def refresh_board(self, inter, content_msg):
        """Atualiza a imagem da prancheta na hora, sem mandar outra mensagem"""
        buf = await generate_team_image(self.user_data, self.ctx.author)
        await inter.message.edit(content=content_msg, attachments=[discord.File(buf, "team.png")], view=self)

    @discord.ui.select(placeholder="📋 Mudar Formação", min_values=1, max_values=1, options=[
        discord.SelectOption(label="4-3-3 (Padrão)", value="4-3-3", description="Ataque total com 3 Meias e 3 DC"),
        discord.SelectOption(label="4-4-2", value="4-4-2", description="Equilíbrio com 4 Meias e 2 DC"),
        discord.SelectOption(label="3-4-3", value="3-4-3", description="Ofensivo com 3 DFC, 4 Meias e 3 DC")
    ])
    async def select_formation(self, inter: discord.Interaction, select: discord.ui.Select):
        if inter.user != self.ctx.author: return
        await inter.response.defer()
        
        val = select.values[0]
        
        async with data_lock:
            d = await get_user_data(self.ctx.author.id)
            d['formation'] = val
            d['team'] = [None] * 11 
            await save_user_data(self.ctx.author.id, d)
            self.user_data = d
            
        await self.refresh_board(inter, f"✅ Tática alterada para **{val}**! Sua prancheta foi limpa para evitar erros de posicionamento.")

    @discord.ui.button(label="⚡ Auto-Escalar", style=discord.ButtonStyle.success)
    async def btn_autofill(self, inter: discord.Interaction, button: discord.ui.Button):
        if inter.user != self.ctx.author: return
        await inter.response.defer()
        
        async with data_lock:
            d = await get_user_data(self.ctx.author.id)
            squad = d.get('squad', [])
            formation = d.get('formation', '4-3-3')
            coords, mapping = get_formation_config(formation)
            
            sorted_squad = sorted(squad, key=lambda p: get_player_effective_overall(p), reverse=True)
            new_team = d.get('team', [None] * 11)
            
            for p in sorted_squad:
                if any(x and x['name'] == p['name'] for x in new_team):
                    continue
                    
                pos = p.get('position', '').upper()
                if pos in POS_MIGRATION: 
                    pos = POS_MIGRATION[pos]
                    
                allowed_slots = mapping.get(pos, [])
                for slot in allowed_slots:
                    if new_team[slot] is None:
                        new_team[slot] = p
                        break
                        
            d['team'] = new_team
            await save_user_data(self.ctx.author.id, d)
            self.user_data = d
            
        await self.refresh_board(inter, "⚡ **Escalação Automática:** Os melhores jogadores disponíveis no seu elenco foram escalados nas vagas livres!")

    @discord.ui.button(label="🎖️ Escolher Capitão", style=discord.ButtonStyle.primary)
    async def btn_captain(self, inter: discord.Interaction, button: discord.ui.Button):
        if inter.user != self.ctx.author: return
        
        team_players = [p for p in self.user_data['team'] if p]
        if not team_players:
            return await inter.response.send_message("❌ Você precisa ter jogadores escalados na prancheta para escolher um capitão.", ephemeral=True)
            
        options = []
        for p in team_players:
            options.append(discord.SelectOption(label=p['name'], value=p['name'], description=f"OVR: {p['overall']} - {p['position']}"))
            
        select = discord.ui.Select(placeholder="Selecione o Capitão", options=options)
        
        async def captain_callback(i: discord.Interaction):
            await i.response.defer()
            val = select.values[0]
            async with data_lock:
                d = await get_user_data(self.ctx.author.id)
                d['captain'] = val
                await save_user_data(self.ctx.author.id, d)
                self.user_data = d
            await self.refresh_board(inter, f"🎖️ **{val}** recebeu a braçadeira de Capitão e liderará a equipe em campo!")
            
        select.callback = captain_callback
        view = discord.ui.View()
        view.add_item(select)
        
        await inter.response.send_message("Selecione na lista abaixo quem será o capitão do time:", view=view, ephemeral=True)

    @discord.ui.button(label="🧹 Limpar Prancheta", style=discord.ButtonStyle.danger)
    async def btn_clear(self, inter: discord.Interaction, button: discord.ui.Button):
        if inter.user != self.ctx.author: return
        await inter.response.defer()
        
        async with data_lock:
            d = await get_user_data(self.ctx.author.id)
            d['team'] = [None] * 11
            await save_user_data(self.ctx.author.id, d)
            self.user_data = d
            
        await self.refresh_board(inter, "✅ Todos os jogadores foram mandados para o banco de reservas!")


class MarketPaginator(discord.ui.View):
    def __init__(self, items, title):
        super().__init__(timeout=120)
        self.items = items
        self.title = title
        self.page = 0
        self.per_page = 15

    async def get_page(self):
        start = self.page * self.per_page
        end = start + self.per_page
        page_items = self.items[start:end]
        
        txt = "\n".join(page_items)
        emb = discord.Embed(title=self.title, description=txt, color=discord.Color.gold())
        
        total_pages = (len(self.items) - 1) // self.per_page + 1
        emb.set_footer(text=f"Página {self.page + 1}/{total_pages} | Total de Atletas: {len(self.items)}")
        return emb

    async def update_view(self, inter=None):
        self.children[0].disabled = (self.page == 0)
        self.children[1].disabled = (self.page == (len(self.items) - 1) // self.per_page)
        emb = await self.get_page()
        if inter:
            await inter.response.edit_message(embed=emb, view=self)
        else:
            return emb

    @discord.ui.button(label="⏪ Anterior", style=discord.ButtonStyle.grey, disabled=True)
    async def prev(self, inter, b): 
        self.page -= 1
        await self.update_view(inter)

    @discord.ui.button(label="Próxima ⏩", style=discord.ButtonStyle.grey)
    async def next(self, inter, b): 
        self.page += 1
        await self.update_view(inter)

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

    @discord.ui.button(label="Editar Carta", style=discord.ButtonStyle.primary, emoji="📝")
    async def btn(self, inter, b): 
        if inter.user == self.author: 
            await inter.response.send_modal(EditPlayerModal(self.nick))

class KeepOrSellView(discord.ui.View):
    def __init__(self, author, player): 
        super().__init__(timeout=60)
        self.author = author
        self.player = player
        self.message = None
        self.responded = False

    async def on_timeout(self):
        if self.responded:
            return
        
        async with data_lock:
            u = await get_user_data(self.author.id)
            if self.player['name'] not in u["contracted_players"]:
                u['squad'].append(self.player)
                u['contracted_players'].append(self.player['name'])
                await save_user_data(self.author.id, u)
        
        if self.message:
            for child in self.children:
                child.disabled = True
            try:
                await self.message.edit(content=f"⏳ **Tempo esgotado!** O olheiro não podia esperar mais e guardou **{self.player['name']}** automaticamente no seu elenco.", view=self)
            except:
                pass

    @discord.ui.button(label="Manter no Elenco", style=discord.ButtonStyle.green)
    async def keep(self, inter, btn):
        if inter.user != self.author: return
        self.responded = True
        async with data_lock:
            u = await get_user_data(self.author.id)
            if self.player['name'] in u["contracted_players"]: 
                return await inter.response.send_message("Já possui!", ephemeral=True)
            u['squad'].append(self.player)
            u['contracted_players'].append(self.player['name'])
            await save_user_data(self.author.id, u)
        await inter.response.edit_message(content=f"✅ **{self.player['name']}** guardado com sucesso no elenco!", embed=None, view=None)

    @discord.ui.button(label="Vender Rápido", style=discord.ButtonStyle.red)
    async def sell(self, inter, btn):
        if inter.user != self.author: return
        self.responded = True
        p = int(self.player['value'] * SALE_PERCENTAGE)
        async with data_lock:
            u = await get_user_data(self.author.id)
            u['money'] += p
            await save_user_data(self.author.id, u)
        await inter.response.edit_message(content=f"💰 O atleta foi vendido rapidamente por **R$ {p:,}**.", embed=None, view=None)

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
                formation = d.get('formation', '4-3-3')
                
                if any(x and x['name'] == p['name'] for x in t): 
                    return await inter.response.send_message("❌ Já é titular.", ephemeral=True)
                    
                coords, mapping = get_formation_config(formation)
                done = False
                
                for pos in p['position'].split('/'):
                    if pos in mapping:
                        for idx in mapping[pos]:
                            if t[idx] is None: 
                                t[idx] = p
                                done = True
                                break
                    if done: break
                    
                if done: 
                    await save_user_data(self.ctx.author.id, d)
                    emb = discord.Embed(title="✅ JOGADOR ESCALADO!", description=f"**{p['name']}** agora é o dono da posição na tática {formation}.", color=discord.Color.green())
                    await inter.response.edit_message(embed=emb, attachments=[], view=None)
                else: 
                    await inter.response.send_message("❌ Sem vaga livre para essa posição na prancheta.\n💡 Dica: Use o botão de `⚡ Auto-Escalar`, ou mude a formação da prancheta.", ephemeral=True)

# --- 8. EVENTOS DO BOT ---

@bot.event
async def on_ready():
    print(f'🟢 EFL Guru ONLINE! Todas as linhas carregadas e Render ativado.')
    fetch_and_parse_players()
    await bot.change_presence(activity=discord.Game(name=f"{BOT_PREFIX}help | EFL Manager"))

@bot.check
async def maintenance_check(ctx):
    global MAINTENANCE_MODE
    if MAINTENANCE_MODE and not ctx.author.guild_permissions.administrator:
        await ctx.send("🛠️ **SISTEMA EM MANUTENÇÃO.**")
        return False
    return True

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        minutos = int(error.retry_after // 60)
        segundos = int(error.retry_after % 60)
        await ctx.send(f"⏳ **Calma aí, chefinho!** O olheiro está viajando pelo mundo atrás de talentos.\n\nTente usar o comando novamente em **{minutos} minutos e {segundos} segundos**.")
        return
    if isinstance(error, commands.CommandNotFound): return
    if isinstance(error, commands.CheckFailure): return
    print(f"Erro detectado: {error}")

# --- 9. COMANDOS DE ADMINISTRAÇÃO E FIX ROBLOX ---

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
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'}
    try:
        res = requests.post("https://users.roblox.com/v1/usernames/users", json={"usernames": [username]}, headers=headers, timeout=10)
        if res.status_code == 429:
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

@bot.command(name='analyzemembers')
@commands.has_permissions(administrator=True)
async def analyze_members_cmd(ctx):
    """Comando Secreto: Analisa membros de um cargo e permite adicionar um por um."""
    target_role_id = 1470883144528822420
    role = ctx.guild.get_role(target_role_id)
    
    if not role:
        return await ctx.send("❌ Cargo alvo não encontrado no servidor.")
        
    msg = await ctx.send("⏳ **Iniciando varredura de membros...**\nIsso pode levar alguns segundos, dependendo da quantidade de jogadores e da API do Roblox.")
    
    db_names = [p['name'].lower() for p in ALL_PLAYERS]
    candidates = []
    
    for member in role.members:
        if "EFL" in member.display_name.upper():
            continue
            
        nick = member.display_name.split()[-1].strip()
        
        if nick.lower() in db_names:
            continue
            
        candidates.append({"nick": nick, "discord_name": member.display_name})
        
    if not candidates:
        return await msg.edit(content="❌ **Varredura Concluída:** Nenhum membro novo apto encontrado (Todos já cadastrados ou com nome bloqueado).")
        
    queue = []
    for c in candidates:
        img = await asyncio.to_thread(get_roblox_data_sync, c["nick"])
        if img:
            c["image"] = img
            queue.append(c)
        await asyncio.sleep(0.5) 
        
    if not queue:
        return await msg.edit(content="❌ **Varredura Concluída:** Nenhuma conta válida encontrada no banco de dados do Roblox.")
        
    view = AnalyzeMembersView(ctx, queue, msg)
    await view.update_view()

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
        return await msg.edit(content=f"❌ Nick `{rbx_name}` não existe ou não foi possível carregar a foto.")
    
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
        erros_log = []
        
        for line in lines:
            parts = line.split()
            if len(parts) < 3: 
                continue
                
            n = parts[0].strip()
            ovr = int(parts[1].strip())
            pos = parts[2].strip().upper()
            
            if pos in POS_MIGRATION:
                pos = POS_MIGRATION[pos]
            
            if n.lower() in names:
                erros_log.append(f"Ignorado: {n} (Já está no banco de dados)")
                continue
                
            coords, mapping = get_formation_config("4-3-3")
            if pos not in mapping: 
                erros_log.append(f"Ignorado: {n} (Posição {pos} não reconhecida)")
                continue
                
            img = await asyncio.to_thread(get_roblox_data_sync, n)
            if img:
                val = calculate_player_value(ovr)
                cards.append({"name": n, "image": img, "overall": ovr, "position": pos, "value": val})
                names.append(n.lower())
                added.append(n)
            else:
                erros_log.append(f"Ignorado: {n} (API do Roblox bloqueou ou nick inválido)")
                
            await asyncio.sleep(1.5)
                
        if added: 
            supabase.table("jogadores").upsert({"id": "ROBLOX_CARDS", "data": cards}).execute()
            fetch_and_parse_players()
            
        relatorio = f"✅ Adicionados: **{len(added)}** atletas."
        if erros_log:
            resumo_erros = "\n".join(erros_log[:10])
            if len(erros_log) > 10: 
                resumo_erros += f"\n...e mais {len(erros_log) - 10} erros ocultos."
            relatorio += f"\n\n⚠️ **Relatório do Sistema:**\n```\n{resumo_erros}\n```"
            
        await status.edit(content=relatorio)
    except Exception as e: 
        await status.edit(content=f"❌ Erro no formato. Use: Nick OVR Pos\nDetalhe: {e}")

@bot.command(name='editplayer')
@commands.has_permissions(administrator=True)
async def edit_player_cmd(ctx, *, nick: str):
    view = EditPlayerView(ctx.author, nick)
    await ctx.send(f"⚙️ Configurações de `{nick}`:", view=view)

@bot.command(name='delplayer')
@commands.has_permissions(administrator=True)
async def del_player_cmd(ctx, *, nick: str):
    async with data_lock:
        try:
            res = supabase.table("jogadores").select("data").eq("id", "ROBLOX_CARDS").execute()
            cards = res.data[0]["data"] if res.data else []

            original_count = len(cards)
            cards = [p for p in cards if p['name'].lower() != nick.lower()]

            if len(cards) == original_count:
                return await ctx.send(f"❌ O jogador `{nick}` não foi encontrado no banco de dados do mercado.")

            supabase.table("jogadores").update({"data": cards}).eq("id", "ROBLOX_CARDS").execute()
            
            global ALL_PLAYERS
            fetch_and_parse_players()
            
            await ctx.send(f"🗑️ ✅ A carta de **{nick}** foi removida permanentemente do mercado global da EFL!")
        except Exception as e:
            await ctx.send(f"❌ Ocorreu um erro ao tentar deletar o jogador: {e}")

@bot.command(name='syncroblox')
@commands.has_permissions(administrator=True)
async def sync_cmd(ctx):
    fetch_and_parse_players()
    await ctx.send(f"✅ Memória RAM sincronizada! **{len(ALL_PLAYERS)}** cartas prontas.")

# --- 10. COMANDOS DO JOGO E GESTÃO ---

@bot.command(name='jogadores')
async def jogadores_cmd(ctx):
    """Lista todos os jogadores cadastrados no banco de dados da EFL"""
    if not ALL_PLAYERS:
        return await ctx.send("❌ O mercado está vazio. Nenhum jogador cadastrado no momento.")
        
    sorted_players = sorted(ALL_PLAYERS, key=lambda x: x['overall'], reverse=True)
    linhas = [f"⭐ **{p['overall']}** | `{p['position']}` | {p['name']}" for p in sorted_players]
    
    view = MarketPaginator(linhas, "🌍 Mercado Global de Jogadores - EFL")
    emb = await view.get_page()
    await ctx.send(embed=emb, view=view)

@bot.command(name='setclube')
async def setclube_cmd(ctx, sigla: str, *, nome: str):
    d = await get_user_data(ctx.author.id)
    d['club_sigla'] = sigla.upper()[:4]
    d['club_name'] = nome[:20].strip()
    await save_user_data(ctx.author.id, d)
    await ctx.send(f"✅ Identidade do clube atualizada: **[{d['club_sigla']}] {d['club_name']}**")

async def reminder_task(ctx, user):
    await asyncio.sleep(900)
    try: 
        await ctx.send(f"⏰ <@{user.id}>, seu olheiro voltou! O comando `{BOT_PREFIX}obter` já está liberado novamente.")
    except: 
        pass

@bot.command(name='obter')
@commands.cooldown(1, 900, commands.BucketType.user)
async def obter_cmd(ctx):
    u = await get_user_data(ctx.author.id)
    livres = [p for p in ALL_PLAYERS if p["name"] not in u["contracted_players"]]
    if not livres: 
        ctx.command.reset_cooldown(ctx)
        return await ctx.send("❌ Mercado vazio!")
    
    pesos = []
    for p in livres:
        ovr = p.get('overall', 70)
        if ovr >= 90: pesos.append(3)      
        elif ovr >= 80: pesos.append(12)   
        elif ovr >= 75: pesos.append(25)   
        else: pesos.append(60)             
        
    p = random.choices(livres, weights=pesos, k=1)[0]
    
    async with image_lock: 
        buf = await asyncio.to_thread(render_single_card_sync, p)
        
    raridade = "🥉 Bronze"
    if p.get('overall', 70) >= 90: raridade = "✨ LENDÁRIO"
    elif p.get('overall', 70) >= 80: raridade = "🥇 Ouro"
    elif p.get('overall', 70) >= 75: raridade = "🥈 Prata"
    
    view = KeepOrSellView(ctx.author, p)
    msg = await ctx.send(content=f"🃏 **OLHEIRO DA EFL:** Você encontrou um talento **{raridade}** solto pelo mundo!\n*(Você tem 60 segundos para escolher ou ele irá para o seu elenco automaticamente)*", file=discord.File(buf, "card.png"), view=view)
    view.message = msg
    
    bot.loop.create_task(reminder_task(ctx, ctx.author))

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

@bot.command(name='banco')
async def banco_cmd(ctx, *, q: str):
    sq = normalize_str(q)
    d = await get_user_data(ctx.author.id)
    
    encontrado = False
    for i, p in enumerate(d['team']):
        if p and sq in normalize_str(p['name']):
            nome = p['name']
            d['team'][i] = None
            encontrado = True
            break
            
    if encontrado:
        await save_user_data(ctx.author.id, d)
        await ctx.send(f"🔄 **{nome}** foi retirado da prancheta e voltou para o banco de reservas! A vaga está livre.")
    else:
        await ctx.send("❌ Esse jogador não foi encontrado na sua escalação titular.")

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
    msg = await ctx.send("⚙️ Desenhando prancheta HD...")
    
    async with image_lock:
        try:
            buf = await generate_team_image(d, ctx.author)
            view = TeamManagerView(ctx, d)
            await ctx.send(file=discord.File(buf, "team.png"), view=view)
            await msg.delete()
        except Exception as e: 
            await msg.edit(content=f"❌ Erro na geração do gráfico: {e}")

@bot.command(name='confrontar')
async def confrontar_cmd(ctx, oponente: discord.Member):
    if ctx.author == oponente or oponente.bot:
        return await ctx.send("❌ Você não pode desafiar a si mesmo ou a um bot!")
        
    if ctx.author.id in active_matches:
        return await ctx.send("❌ Você já está em uma partida! Espere o apito final para jogar novamente.")
        
    if oponente.id in active_matches:
        return await ctx.send(f"❌ **{oponente.display_name}** já está em campo disputando uma partida no momento.")

    d1 = await get_user_data(ctx.author.id)
    d2 = await get_user_data(oponente.id)

    if None in d1['team']:
        return await ctx.send(f"🚨 Sua prancheta está incompleta! Você precisa escalar os 11 titulares para jogar na EFL.")
    if None in d2['team']:
        return await ctx.send(f"🚨 A prancheta do seu adversário ({oponente.display_name}) está incompleta! Ele precisa escalar os 11 titulares.")

    view = MatchInviteView(ctx, ctx.author, oponente, d1, d2)
    emb = discord.Embed(
        title="⚔️ NOVO DESAFIO NA EFL!",
        description=f"{oponente.mention}, o manager **{ctx.author.display_name}** está chamando sua equipe para um confronto oficial!\n\nVocê aceita o desafio?",
        color=discord.Color.orange()
    )
    await ctx.send(content=oponente.mention, embed=emb, view=view)

@bot.command(name='ranking')
async def ranking_cmd(ctx):
    res = supabase.table("jogadores").select("id", "data").execute()
    users = sorted([x for x in res.data if x['id'] != "ROBLOX_CARDS"], key=lambda u: u["data"].get("wins", 0), reverse=True)[:10]
    txt = "\n".join([f"**{i+1}.** <@{u['id']}> — `{u['data'].get('wins',0)}` Vitórias" for i, u in enumerate(users)])
    await ctx.send(embed=discord.Embed(title="🏆 Ranking Oficial EFL", description=txt or "Ainda não houve partidas registradas.", color=discord.Color.gold()))

@bot.command(name='help')
async def help_cmd(ctx):
    emb = discord.Embed(title="📜 Painel de Ajuda EFL Pro", description="Seja bem-vindo ao mercado EFL Pro! Abaixo estão os comandos disponíveis:", color=discord.Color.gold())
    emb.add_field(name="💰 Gestão & Economia", value="`--cofre`, `--donate`, `--contratar`, `--sell`, `--obter`, `--jogadores`", inline=False)
    emb.add_field(name="📋 Vestiário & Tática", value="`--setclube`, `--elenco`, `--escalar`, `--banco`, `--team` ", inline=False)
    emb.add_field(name="⚽ Partidas", value="`--confrontar`, `--ranking` ")
    emb.add_field(name="⚙️ Administração", value="`--addplayer`, `--bulkadd`, `--editplayer`, `--delplayer`, `--lock`, `--unlock` ")
    emb.set_footer(text="Versão 34.0 - Desenvolvido exclusivamente para a EFL")
    await ctx.send(embed=emb)

# --- INICIALIZAÇÃO ---
if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if token: 
        keep_alive()
        bot.run(token)
    else: 
        print("❌ Token ausente no arquivo .env.")
