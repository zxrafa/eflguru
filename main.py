# -*- coding: utf-8 -*-
"""
EFL Guru - Versão 44.0 (MODO CARREIRA COM JOGADORES REAIS DO DB)
----------------------------------------------------------------------
- CÓDIGO COMPLETO: Nenhuma linha removida. Nenhuma linha comprimida.
- INTEGRAÇÃO GLOBAL (A PEDIDO): O Modo Carreira agora utiliza EXCLUSIVAMENTE
  os jogadores do banco de dados oficial (Roblox Cards).
- INÍCIO REALISTA: Ao escolher um time Tier 3, você começa com um elenco
  formado pelos jogadores reais de menor OVR do seu banco.
- MERCADO VIVO: Os olheiros trazem jogadores reais do DB que não estão no seu time.
- SIMULAÇÃO AO VIVO: Narração em tempo real das partidas.
- CÓDIGO EXPANDIDO: Todas as quebras de linha e indentações restauradas rigorosamente.
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
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter
from io import BytesIO
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client
from flask import Flask
from threading import Thread
import math

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
INITIAL_MONEY = 1000000
SALE_PERCENTAGE = 0.5

# --- SISTEMA DE PERMISSÕES SUPREMAS ---
BOT_ADMINS = [338704196180115458, 1076957467935789056]

def is_bot_admin():
    async def predicate(ctx):
        return ctx.author.id in BOT_ADMINS
    return commands.check(predicate)

def calculate_player_value(ovr):
    base_value = 150000
    adjusted_ovr = max(70, ovr)
    return int(base_value * (1.3 ** (adjusted_ovr - 70)))

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
    if formation == "4-4-2":
        coords = {
            0: (420, 1060),
            1: (120, 820), 2: (320, 830), 3: (520, 830), 4: (720, 820),
            5: (150, 530), 6: (330, 560), 7: (510, 560), 8: (690, 530),
            9: (300, 200), 10: (540, 200)
        }
        mapping = {
            "PO": [0], "GK": [0], "GOL": [0],
            "DFC": [1, 2, 3, 4], "CB": [1, 2, 3, 4], "ZAG": [1, 2, 3, 4],
            "MDC": [5, 6, 7, 8], "MC": [5, 6, 7, 8], "MCO": [5, 6, 7, 8], "VOL": [5, 6, 7, 8],
            "DC": [9, 10], "ST": [9, 10], "CA": [9, 10]
        }
    elif formation == "3-4-3":
        coords = {
            0: (420, 1060),
            1: (200, 830), 2: (420, 850), 3: (640, 830),
            4: (150, 530), 5: (330, 560), 6: (510, 560), 7: (690, 530),
            8: (170, 240), 9: (420, 190), 10: (670, 240)
        }
        mapping = {
            "PO": [0], "GK": [0], "GOL": [0],
            "DFC": [1, 2, 3], "CB": [1, 2, 3], "ZAG": [1, 2, 3],
            "MDC": [4, 5, 6, 7], "MC": [4, 5, 6, 7], "MCO": [4, 5, 6, 7], "VOL": [4, 5, 6, 7],
            "DC": [8, 9, 10], "ST": [8, 9, 10], "CA": [8, 9, 10]
        }
    else:
        coords = {
            0: (420, 1060),
            1: (120, 820), 2: (320, 830), 3: (520, 830), 4: (720, 820),
            5: (200, 530), 6: (420, 560), 7: (640, 530),
            8: (170, 240), 9: (420, 190), 10: (670, 240)
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
career_lock = asyncio.Lock()
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

# =====================================================================
# 🚀 MODO CARREIRA: DADOS BASE E GERAÇÃO COM JOGADORES REAIS DO DB
# =====================================================================

CAREER_CLUBS = {
    1: [
        {"name": "EFL Elite FC", "budget": 150000000, "expect": "Vencer a Liga"}, 
        {"name": "Supremos AC", "budget": 120000000, "expect": "Classificar para Continental"}
    ],
    2: [
        {"name": "União Cidadã", "budget": 40000000, "expect": "Terminar no Top 6"}, 
        {"name": "Real Sindicato", "budget": 35000000, "expect": "Fugir do Rebaixamento"}
    ],
    3: [
        {"name": "Operário FC", "budget": 8000000, "expect": "Subir de Divisão"}, 
        {"name": "Várzea Rovers", "budget": 5000000, "expect": "Sobreviver"}
    ]
}

TACTICAL_STYLES = {
    "Tiki-Taka": {
        "desc": "Posse de bola e passes curtos. Cansaço médio.", 
        "atk_bonus": 1.1, 
        "def_bonus": 1.0, 
        "stam_cost": 5
    },
    "Gegenpressing": {
        "desc": "Pressão alta absurda. Ataque letal, mas drena o físico.", 
        "atk_bonus": 1.25, 
        "def_bonus": 1.05, 
        "stam_cost": 12
    },
    "Retranca": {
        "desc": "Defesa sólida e contra-ataque. Pouco desgaste.", 
        "atk_bonus": 0.8, 
        "def_bonus": 1.3, 
        "stam_cost": 3
    },
    "Equilibrado": {
        "desc": "Abordagem padrão. Bom balanço geral.", 
        "atk_bonus": 1.0, 
        "def_bonus": 1.0, 
        "stam_cost": 6
    }
}

async def get_career_data(user_id):
    uid = f"CAREER_{user_id}"
    res = supabase.table("jogadores").select("data").eq("id", uid).execute()
    
    if not res.data: 
        return None
        
    return res.data[0]["data"]

async def save_career_data(user_id, data):
    uid = f"CAREER_{user_id}"
    res = supabase.table("jogadores").select("id").eq("id", uid).execute()
    
    if res.data:
        supabase.table("jogadores").update({"data": data}).eq("id", uid).execute()
    else:
        supabase.table("jogadores").insert({"id": uid, "data": data}).execute()

def generate_initial_squad(tier):
    """
    Gera um elenco de 25 jogadores para o Modo Carreira utilizando EXCLUSIVAMENTE
    os jogadores reais do banco de dados global (ALL_PLAYERS).
    Se o time for ruim (Tier 3), pega os piores jogadores disponíveis.
    """
    global ALL_PLAYERS
    squad = []
    
    pool = list(ALL_PLAYERS)
    
    # Prevenção caso o banco de dados esteja vazio
    if not pool:
        pool = [{"name": "Jogador Genérico", "overall": 60, "position": "MC", "value": 150000, "image": ""}]
        
    # Define o OVR alvo baseado na força do clube escolhido
    if tier == 3:
        max_ovr = 74
    elif tier == 2:
        max_ovr = 82
    else:
        max_ovr = 999
        
    # Organiza o banco de dados do pior para o melhor
    pool_ordenado = sorted(pool, key=lambda x: x.get('overall', 70))
    
    # Filtra os jogadores que se encaixam no teto do time
    filtered_pool = []
    for p in pool_ordenado:
        if p.get('overall', 70) <= max_ovr:
            filtered_pool.append(p)
            
    # Se não houver jogadores ruins suficientes, pega os piores disponíveis de qualquer jeito
    if len(filtered_pool) < 25:
        filtered_pool = pool_ordenado[:25]
        
    # Embaralha as opções válidas para o time não ser sempre exatamente igual
    random.shuffle(filtered_pool)
    
    for i in range(25):
        # Se o banco global tiver menos de 25 jogadores no total, ele repete para completar o elenco
        base_p = filtered_pool[i % len(filtered_pool)]
        
        # Pega a posição primária se houver múltiplas (ex: "DC/MC" vira "DC")
        pos_str = base_p.get("position", "MC").split('/')[0]
        
        # Calcula dados extras exclusivos do modo carreira
        idade_mock = random.randint(18, 32)
        potencial = base_p.get("overall", 70)
        
        if idade_mock < 24:
            potencial = potencial + random.randint(2, 8)
            
        valor = base_p.get("value", calculate_player_value(base_p.get("overall", 70)))
        salario = int(valor * 0.005)
        
        if i < 11:
            status_jogador = "Titular"
        else:
            status_jogador = "Reserva"
            
        career_p = {
            "id": base_p.get("name"),
            "name": base_p.get("name"),
            "image": base_p.get("image", ""),
            "pos": pos_str,
            "age": idade_mock,
            "ovr": base_p.get("overall", 70),
            "pot": potencial,
            "fitness": 100,
            "morale": 80,
            "value": valor,
            "wage": salario,
            "status": status_jogador
        }
        squad.append(career_p)
        
    return squad

def get_market_players(type_search, exclude_names):
    """Busca jogadores reais do banco de dados para aparecerem como opções no olheiro"""
    global ALL_PLAYERS
    pool = list(ALL_PLAYERS)
    
    if not pool:
        pool = [{"name": "Jogador Genérico", "overall": 60, "position": "MC", "value": 150000, "image": ""}]
        
    available = []
    for p in pool:
        if p.get("name") not in exclude_names:
            available.append(p)
            
    filtered = []
    if type_search == "base":
        for p in available:
            if p.get('overall', 70) <= 75:
                filtered.append(p)
    else:
        for p in available:
            if p.get('overall', 70) >= 76:
                filtered.append(p)
                
    if len(filtered) < 3:
        filtered = available
        
    random.shuffle(filtered)
    
    chosen = []
    limit = min(3, len(filtered))
    
    for i in range(limit):
        base_p = filtered[i]
        pos_str = base_p.get("position", "MC").split('/')[0]
        
        if type_search == "base":
            idade_mock = random.randint(16, 20)
            potencial = base_p.get("overall", 70) + random.randint(5, 12)
        else:
            idade_mock = random.randint(22, 32)
            potencial = base_p.get("overall", 70) + random.randint(0, 3)
            
        valor = base_p.get("value", calculate_player_value(base_p.get("overall", 70)))
        salario = int(valor * 0.005)
        
        career_p = {
            "id": base_p.get("name"),
            "name": base_p.get("name"),
            "image": base_p.get("image", ""),
            "pos": pos_str,
            "age": idade_mock,
            "ovr": base_p.get("overall", 70),
            "pot": potencial,
            "fitness": 100,
            "morale": 80,
            "value": valor,
            "wage": salario,
            "status": "Reserva"
        }
        chosen.append(career_p)
        
    return chosen

# =====================================================================
# 🚀 MODO CARREIRA: TELAS E LÓGICA DE FIM DE TEMPORADA / MERCADO
# =====================================================================

class CareerSeasonEndView(discord.ui.View):
    def __init__(self, ctx, data):
        super().__init__(timeout=600)
        self.ctx = ctx
        self.data = data
        
        self.new_tier_offer = None
        current_tier = self.data['club']['tier']
        rep = self.data['coach']['reputation']
        
        if current_tier == 3 and rep >= 30:
            self.new_tier_offer = 2
        elif current_tier == 2 and rep >= 60:
            self.new_tier_offer = 1
            
        if self.new_tier_offer:
            self.offer_club = random.choice(CAREER_CLUBS[self.new_tier_offer])
            
            btn_accept = discord.ui.Button(label=f"Assinar com {self.offer_club['name']}", style=discord.ButtonStyle.success, emoji="📝")
            btn_accept.callback = self.accept_offer
            self.add_item(btn_accept)
            
        btn_stay = discord.ui.Button(label=f"Renovar com {self.data['club']['name']}", style=discord.ButtonStyle.primary, emoji="🤝")
        btn_stay.callback = self.stay_club
        self.add_item(btn_stay)

    def build_embed(self):
        s = self.data['season']
        c = self.data['coach']
        
        e = discord.Embed(title="🏁 FIM DE TEMPORADA!", color=discord.Color.gold())
        e.add_field(name="Desempenho Final", value=f"Vitórias: {s['wins']}\nEmpates: {s['draws']}\nDerrotas: {s['losses']}\n**Pontos: {s['pts']}**", inline=False)
        e.add_field(name="Status do Treinador", value=f"Reputação: {c['reputation']}/100\nConfiança da Diretoria: {self.data['club']['confidence']}%", inline=False)
        
        if self.new_tier_offer:
            e.description = f"**🔥 PROPOSTA NA MESA!**\nSeu ótimo desempenho chamou a atenção de clubes maiores. O **{self.offer_club['name']}** (Tier {self.new_tier_offer}) quer você como treinador na próxima temporada!"
        else:
            e.description = "A temporada acabou. Avalie seu desempenho e assine sua renovação para a próxima temporada."
            
        return e

    async def accept_offer(self, inter: discord.Interaction):
        if inter.user != self.ctx.author: 
            return
            
        await inter.response.defer()
        
        self.data['club']['name'] = self.offer_club['name']
        self.data['club']['budget'] = self.offer_club['budget']
        self.data['club']['tier'] = self.new_tier_offer
        self.data['club']['confidence'] = 80
        
        self.data['squad'] = generate_initial_squad(self.new_tier_offer)
        
        self.data['season'] = {
            "week": 1, 
            "wins": 0, 
            "draws": 0, 
            "losses": 0, 
            "pts": 0, 
            "history": []
        }
        
        await save_career_data(self.ctx.author.id, self.data)
        await inter.message.edit(content="⚽ **Contrato assinado com o novo clube!** Preparando nova temporada...", embed=None, view=None)
        await asyncio.sleep(2)
        
        hub_view = CareerHubView(self.ctx, self.data)
        await inter.message.edit(content=None, embed=hub_view.build_embed(), view=hub_view)

    async def stay_club(self, inter: discord.Interaction):
        if inter.user != self.ctx.author: 
            return
            
        await inter.response.defer()
        
        self.data['club']['budget'] += int(self.data['club']['budget'] * 0.2)
        
        self.data['season'] = {
            "week": 1, 
            "wins": 0, 
            "draws": 0, 
            "losses": 0, 
            "pts": 0, 
            "history": []
        }
        
        await save_career_data(self.ctx.author.id, self.data)
        await inter.message.edit(content="🤝 **Contrato renovado!** Iniciando a próxima temporada...", embed=None, view=None)
        await asyncio.sleep(2)
        
        hub_view = CareerHubView(self.ctx, self.data)
        await inter.message.edit(content=None, embed=hub_view.build_embed(), view=hub_view)

class CareerMarketPlayerSelect(discord.ui.View):
    def __init__(self, ctx, data, players_generated, hub_view):
        super().__init__(timeout=120)
        self.ctx = ctx
        self.data = data
        self.players = players_generated
        self.hub_view = hub_view
        
        options = []
        for i, p in enumerate(self.players):
            options.append(discord.SelectOption(
                label=f"{p['name']} ({p['pos']})",
                value=str(i),
                description=f"OVR: {p['ovr']} | POT: {p['pot']} | Idade: {p['age']}"
            ))
            
        select = discord.ui.Select(placeholder="Escolha o jogador para assinar", options=options)
        
        async def select_callback(inter: discord.Interaction):
            if inter.user != self.ctx.author: 
                return
                
            await inter.response.defer()
            
            chosen_idx = int(select.values[0])
            chosen_player = self.players[chosen_idx]
            
            self.data['squad'].append(chosen_player)
            await save_career_data(self.ctx.author.id, self.data)
            
            await inter.message.edit(content=f"✅ **{chosen_player['name']}** assinou com o clube e já está integrado ao elenco!", embed=None, view=None)
            await self.hub_view.message.edit(embed=self.hub_view.build_embed())
            
        select.callback = select_callback
        self.add_item(select)

class CareerMarketView(discord.ui.View):
    def __init__(self, ctx, data, hub_view):
        super().__init__(timeout=120)
        self.ctx = ctx
        self.data = data
        self.hub_view = hub_view

    def build_embed(self):
        e = discord.Embed(title="🛒 Central de Transferências", description="Gaste seu orçamento para enviar olheiros pelo mundo.", color=discord.Color.purple())
        e.add_field(name="💰 Orçamento Atual", value=f"R$ {self.data['club']['budget']:,}", inline=False)
        e.add_field(name="Opções de Busca", value="• **Base (Promessas):** Traz 3 jovens talentos da EFL com OVR menor.\n• **Profissional (Estrelas):** Traz 3 atletas prontos e de alto OVR.", inline=False)
        return e

    @discord.ui.button(label="Olheiro de Promessas (R$ 500k)", style=discord.ButtonStyle.success, emoji="👦")
    async def btn_youth(self, inter: discord.Interaction, b):
        if inter.user != self.ctx.author: 
            return
            
        if self.data['club']['budget'] < 500000:
            return await inter.response.send_message("❌ Orçamento insuficiente para esta ação.", ephemeral=True)
            
        await inter.response.defer()
        self.data['club']['budget'] -= 500000
        
        current_squad_names = []
        for p in self.data['squad']:
            current_squad_names.append(p['name'])
            
        players = get_market_players("base", current_squad_names)
        
        e = discord.Embed(title="👦 Relatório da Base (Promessas)", description="Seu olheiro encontrou estes 3 talentos no banco de dados. Escolha UM para assinar:", color=discord.Color.green())
        for i, p in enumerate(players):
            e.add_field(name=f"Opção {i+1}: {p['name']}", value=f"Idade: {p['age']}\nPosição: {p['pos']}\nOVR: {p['ovr']} | Potencial: {p['pot']}", inline=False)
            
        view = CareerMarketPlayerSelect(self.ctx, self.data, players, self.hub_view)
        await inter.message.edit(embed=e, view=view)

    @discord.ui.button(label="Olheiro Profissional (R$ 3 Milhões)", style=discord.ButtonStyle.primary, emoji="👨")
    async def btn_pro(self, inter: discord.Interaction, b):
        if inter.user != self.ctx.author: 
            return
            
        cost = 3000000
        if self.data['club']['budget'] < cost:
            return await inter.response.send_message("❌ Orçamento insuficiente para esta ação.", ephemeral=True)
            
        await inter.response.defer()
        self.data['club']['budget'] -= cost
        
        current_squad_names = []
        for p in self.data['squad']:
            current_squad_names.append(p['name'])
            
        players = get_market_players("pro", current_squad_names)
        
        e = discord.Embed(title="👨 Relatório Profissional (Estrelas)", description="Seu olheiro encontrou estes 3 atletas no banco de dados. Escolha UM para assinar:", color=discord.Color.blue())
        for i, p in enumerate(players):
            e.add_field(name=f"Opção {i+1}: {p['name']}", value=f"Idade: {p['age']}\nPosição: {p['pos']}\nOVR: {p['ovr']}", inline=False)
            
        view = CareerMarketPlayerSelect(self.ctx, self.data, players, self.hub_view)
        await inter.message.edit(embed=e, view=view)


# --- VIEWS DO MODO CARREIRA (TELA INICIAL E HUB) ---

class CareerSetupView(discord.ui.View):
    def __init__(self, ctx):
        super().__init__(timeout=300)
        self.ctx = ctx
        self.coach_name = ctx.author.display_name
        self.style = "Equilibrado"
        self.mental = "Estrategista"

    @discord.ui.button(label="Nome do Técnico", style=discord.ButtonStyle.secondary, emoji="🧑‍💼")
    async def btn_name(self, inter: discord.Interaction, b):
        if inter.user != self.ctx.author: 
            return
            
        modal = CareerNameModal(self)
        await inter.response.send_modal(modal)

    @discord.ui.select(placeholder="Estilo de Jogo", options=[
        discord.SelectOption(label="Tiki-Taka", description="Posse de bola, passes curtos."),
        discord.SelectOption(label="Gegenpressing", description="Pressão alta, perde muita energia."),
        discord.SelectOption(label="Retranca", description="Defesa fechada, contra-ataques."),
        discord.SelectOption(label="Equilibrado", description="Balanceado sem fraquezas extremas.")
    ])
    async def sel_style(self, inter: discord.Interaction, select: discord.ui.Select):
        if inter.user != self.ctx.author: 
            return
            
        self.style = select.values[0]
        await inter.response.edit_message(embed=self.build_embed())

    @discord.ui.select(placeholder="Mentalidade do Treinador", options=[
        discord.SelectOption(label="Estrategista", description="Bônus de OVR temporário em jogos chave."),
        discord.SelectOption(label="Disciplinador", description="Jogadores recuperam Moral e Forma mais rápido."),
        discord.SelectOption(label="Desenvolvedor", description="Jogadores jovens sobem de OVR mais rápido.")
    ])
    async def sel_mental(self, inter: discord.Interaction, select: discord.ui.Select):
        if inter.user != self.ctx.author: 
            return
            
        self.mental = select.values[0]
        await inter.response.edit_message(embed=self.build_embed())

    @discord.ui.button(label="Avançar para Escolha de Clube", style=discord.ButtonStyle.success, row=3)
    async def btn_next(self, inter: discord.Interaction, b):
        if inter.user != self.ctx.author: 
            return
            
        club_view = CareerClubSelectView(self.ctx, self.coach_name, self.style, self.mental)
        emb = discord.Embed(
            title="🏢 Mercado de Trabalho", 
            description="Escolha o clube onde você iniciará sua carreira. Como técnico iniciante, apenas clubes de divisões inferiores (Tier 3) aceitam você.", 
            color=discord.Color.dark_teal()
        )
        await inter.response.edit_message(embed=emb, view=club_view)

    def build_embed(self):
        e = discord.Embed(title="📋 Criação de Técnico - EFL Career", color=discord.Color.blue())
        e.add_field(name="Nome do Treinador", value=f"**{self.coach_name}**", inline=False)
        e.add_field(name="Estilo Tático", value=f"`{self.style}`", inline=True)
        e.add_field(name="Mentalidade", value=f"`{self.mental}`", inline=True)
        return e

class CareerNameModal(discord.ui.Modal, title="Definir Nome do Treinador"):
    name_input = discord.ui.TextInput(label="Nome Sobrenome", placeholder="Ex: Pep Guardiola")
    
    def __init__(self, view_ref):
        super().__init__()
        self.view_ref = view_ref
        
    async def on_submit(self, inter: discord.Interaction):
        self.view_ref.coach_name = self.name_input.value
        await inter.response.edit_message(embed=self.view_ref.build_embed())

class CareerClubSelectView(discord.ui.View):
    def __init__(self, ctx, c_name, c_style, c_mental):
        super().__init__(timeout=300)
        self.ctx = ctx
        self.c_name = c_name
        self.c_style = c_style
        self.c_mental = c_mental
        
        for c in CAREER_CLUBS[3]:
            btn = discord.ui.Button(label=f"Assinar com {c['name']}", style=discord.ButtonStyle.primary)
            btn.callback = self.make_callback(c)
            self.add_item(btn)

    def make_callback(self, club_data):
        async def callback(inter: discord.Interaction):
            if inter.user != self.ctx.author: 
                return
                
            await inter.response.defer()
            
            squad = generate_initial_squad(3)
            
            data = {
                "coach": {
                    "name": self.c_name, 
                    "style": self.c_style, 
                    "mental": self.c_mental, 
                    "reputation": 10
                },
                "club": {
                    "name": club_data['name'], 
                    "budget": club_data['budget'], 
                    "confidence": 80, 
                    "tier": 3
                },
                "squad": squad,
                "season": {
                    "week": 1, 
                    "wins": 0, 
                    "draws": 0, 
                    "losses": 0, 
                    "pts": 0, 
                    "history": []
                },
                "formation": "4-3-3"
            }
            
            await save_career_data(self.ctx.author.id, data)
            
            await inter.message.edit(content="⚽ **Contrato assinado!** Gerando instalações, buscando jogadores reais na base de dados...", embed=None, view=None)
            await asyncio.sleep(2)
            
            hub_view = CareerHubView(self.ctx, data)
            await inter.message.edit(content=None, embed=hub_view.build_embed(), view=hub_view)
            
        return callback

class CareerHubView(discord.ui.View):
    def __init__(self, ctx, data):
        super().__init__(timeout=600)
        self.ctx = ctx
        self.data = data

    def build_embed(self):
        c = self.data['coach']
        cl = self.data['club']
        s = self.data['season']
        
        wage_bill = sum(p['wage'] for p in self.data['squad'])
        
        titulares_count = len([p for p in self.data['squad'] if p['status'] == 'Titular'])
        
        if titulares_count == 11:
            avg_ovr = int(sum(p['ovr'] for p in self.data['squad'] if p['status'] == 'Titular') / 11)
        else:
            avg_ovr = 0

        e = discord.Embed(title=f"🏟️ Hub do Manager: {cl['name']} (Semana {s['week']}/38)", color=discord.Color.dark_theme())
        e.add_field(name="🧑‍💼 Treinador", value=f"**{c['name']}**\nReputação: {c['reputation']}/100\nEstilo: {c['style']}", inline=True)
        e.add_field(name="📊 Campanha Atual", value=f"Vitórias: {s['wins']} | Empates: {s['draws']} | Derrotas: {s['losses']}\nPontos: **{s['pts']}**", inline=True)
        e.add_field(name="💼 Finanças & Diretoria", value=f"Orçamento: R$ {cl['budget']:,}\nFolha Salarial: R$ {wage_bill:,}\nConfiança da Diretoria: {cl['confidence']}%", inline=False)
        e.add_field(name="👥 Visão Geral do Elenco", value=f"Titulares Definidos: {titulares_count}/11\nOVR Médio Titular: {avg_ovr}\nTática: {self.data['formation']}", inline=False)
        return e

    @discord.ui.button(label="Avançar Semana (Simular)", style=discord.ButtonStyle.success, emoji="⏩", row=0)
    async def btn_advance(self, inter: discord.Interaction, b):
        if inter.user != self.ctx.author: 
            return
            
        titulares = [p for p in self.data['squad'] if p['status'] == 'Titular']
        if len(titulares) != 11:
            return await inter.response.send_message("❌ Você precisa de exatamente 11 titulares para jogar! Vá em Elenco.", ephemeral=True)

        if self.data['season']['week'] > 38:
            await inter.response.defer()
            view = CareerSeasonEndView(self.ctx, self.data)
            await inter.message.edit(embed=view.build_embed(), view=view)
            return

        for child in self.children:
            child.disabled = True
            
        await inter.response.edit_message(view=self)

        async with career_lock:
            if self.data['club']['tier'] == 3:
                adv_ovr = random.randint(60, 75) 
            else:
                adv_ovr = random.randint(70, 85)
                
            meu_ovr = sum(p['ovr'] for p in titulares) / 11
            
            fatigue_pen = sum((100 - p['fitness']) * 0.1 for p in titulares)
            morale_bonus = sum((p['morale'] - 50) * 0.05 for p in titulares)
            style_data = TACTICAL_STYLES[self.data['coach']['style']]
            
            forca_final = (meu_ovr - fatigue_pen + morale_bonus) * style_data['atk_bonus']
            
            meus_gols = 0
            adv_gols = 0
            eventos = []
            
            for m in range(0, 91, 15):
                for p in titulares:
                    p['fitness'] = max(30, p['fitness'] - style_data['stam_cost'])
                
                chances = random.randint(1, 100)
                
                if chances < (forca_final / (forca_final + adv_ovr) * 100):
                    if random.random() > 0.6: 
                        meus_gols += 1
                        eventos.append(f"[{m}'] ⚽ Gol do {self.data['club']['name']}! Lindo lance.")
                elif chances > 80:
                    if random.random() > 0.6:
                        adv_gols += 1
                        eventos.append(f"[{m}'] ❌ Gol do adversário. Falha na marcação.")
                        
                if eventos:
                    log_temp = "\n".join(eventos)
                else:
                    log_temp = "A bola rola e os times se estudam..."
                    
                live_embed = discord.Embed(title=f"🔴 AO VIVO: {m}' Minutos", description=f"## 🔵 {self.data['club']['name']} {meus_gols} x {adv_gols} Adversário 🔴\n\n```\n{log_temp}\n```", color=discord.Color.red())
                await inter.message.edit(embed=live_embed)
                await asyncio.sleep(1.5) 
            
            res_str = ""
            if meus_gols > adv_gols:
                self.data['season']['wins'] += 1
                self.data['season']['pts'] += 3
                self.data['club']['confidence'] = min(100, self.data['club']['confidence'] + 5)
                self.data['coach']['reputation'] += 1
                res_str = "Vitória 🟢"
                
                for p in self.data['squad']: 
                    p['morale'] = min(100, p['morale'] + 10)
                    
            elif adv_gols > meus_gols:
                self.data['season']['losses'] += 1
                self.data['club']['confidence'] -= 8
                res_str = "Derrota 🔴"
                
                for p in self.data['squad']: 
                    p['morale'] = max(0, p['morale'] - 15)
                    
            else:
                self.data['season']['draws'] += 1
                self.data['season']['pts'] += 1
                res_str = "Empate 🟡"
                
                for p in self.data['squad']: 
                    p['morale'] = min(100, p['morale'] + 2)

            self.data['season']['week'] += 1
            
            if self.data['season']['week'] % 4 == 0:
                wage_bill = sum(p['wage'] for p in self.data['squad'])
                self.data['club']['budget'] -= wage_bill
                
                for p in self.data['squad']:
                    if p['status'] != 'Titular': 
                        p['fitness'] = min(100, p['fitness'] + 40)
                    
            await save_career_data(self.ctx.author.id, self.data)
            
            if self.data['club']['confidence'] <= 25:
                await inter.message.edit(content="🚨 **VOCÊ FOI DEMITIDO!** A diretoria perdeu a confiança no seu trabalho.", embed=None, view=None)
                supabase.table("jogadores").delete().eq("id", f"CAREER_{self.ctx.author.id}").execute()
                return

            for child in self.children:
                child.disabled = False
                
            await inter.message.edit(embed=self.build_embed(), view=self)

    @discord.ui.button(label="Gerenciar Elenco", style=discord.ButtonStyle.primary, emoji="👥", row=0)
    async def btn_squad(self, inter: discord.Interaction, b):
        if inter.user != self.ctx.author: 
            return
            
        await inter.response.send_message(embed=CareerSquadView.build_embed(self.data), view=CareerSquadView(self.ctx, self.data, self), ephemeral=True)

    @discord.ui.button(label="Mercado & Base", style=discord.ButtonStyle.secondary, emoji="💰", row=0)
    async def btn_market(self, inter: discord.Interaction, b):
        if inter.user != self.ctx.author: 
            return
            
        view = CareerMarketView(self.ctx, self.data, self)
        await inter.response.send_message(embed=view.build_embed(), view=view, ephemeral=True)

class CareerSquadView(discord.ui.View):
    def __init__(self, ctx, data, hub_view):
        super().__init__(timeout=120)
        self.ctx = ctx
        self.data = data
        self.hub_view = hub_view

    @staticmethod
    def build_embed(data):
        tits = []
        res = []
        
        for p in data['squad']:
            if p['status'] == 'Titular':
                tits.append(p)
            else:
                res.append(p)
        
        t_str_list = []
        for p in tits:
            t_str_list.append(f"`{p['pos']}` **{p['name']}** | ⭐{p['ovr']} | 🔋{p['fitness']}% | 😃{p['morale']}%")
        t_str = "\n".join(t_str_list)
        
        r_str_list = []
        for p in res[:10]:
            r_str_list.append(f"`{p['pos']}` {p['name']} | ⭐{p['ovr']} | 🔋{p['fitness']}%")
        r_str = "\n".join(r_str_list)
        
        e = discord.Embed(title="📋 Seu Elenco Atual", color=discord.Color.green())
        
        if t_str:
            e.add_field(name=f"Titulares ({len(tits)}/11)", value=t_str, inline=False)
        else:
            e.add_field(name=f"Titulares (0/11)", value="Nenhum titular escalado.", inline=False)
            
        if r_str:
            e.add_field(name="Reservas (Top 10)", value=r_str, inline=False)
        else:
            e.add_field(name="Reservas", value="Sem reservas.", inline=False)
            
        return e

    @discord.ui.button(label="Auto-Escalar Melhor Time", style=discord.ButtonStyle.success)
    async def btn_auto(self, inter: discord.Interaction, b):
        if inter.user != self.ctx.author: 
            return
        
        for p in self.data['squad']: 
            p['status'] = "Reserva"
        
        squad_sorted = sorted(self.data['squad'], key=lambda x: (x['ovr'], x['fitness']), reverse=True)
        coords, mapping = get_formation_config(self.data['formation'])
        
        vagas = {
            "GOL": 1, 
            "ZAG": 2, 
            "LAT": 2, 
            "MEI": 3, 
            "ATA": 3
        }
        
        for p in squad_sorted:
            pos_cat = p['pos']
            if pos_cat in ["PO", "GK", "GOL"]: 
                cat = "GOL"
            elif pos_cat in ["DFC", "CB", "ZAG"]: 
                cat = "ZAG"
            elif pos_cat in ["LD", "LE", "RB", "LB"]: 
                cat = "LAT"
            elif pos_cat in ["MDC", "MC", "MCO", "VOL"]: 
                cat = "MEI"
            else: 
                cat = "ATA"
            
            if vagas.get(cat, 0) > 0:
                p['status'] = 'Titular'
                vagas[cat] -= 1
                
        tits = []
        for p in self.data['squad']:
            if p['status'] == 'Titular':
                tits.append(p)
                
        if len(tits) < 11:
            for p in squad_sorted:
                if p['status'] == 'Reserva':
                    p['status'] = 'Titular'
                    tits.append(p)
                if len(tits) == 11: 
                    break

        await save_career_data(self.ctx.author.id, self.data)
        await inter.response.edit_message(embed=self.build_embed(self.data), view=self)
        await self.hub_view.message.edit(embed=self.hub_view.build_embed())

# --- COMANDO MODO CARREIRA ---

@bot.command(name='carreira')
async def carreira_cmd(ctx):
    """Comando de Entrada do Modo Carreira FIFA"""
    data = await get_career_data(ctx.author.id)
    if not data:
        view = CareerSetupView(ctx)
        emb = discord.Embed(
            title="🏆 Bem-vindo ao Modo Carreira EFL!", 
            description="Crie o seu perfil de treinador para começar sua jornada rumo ao topo do futebol mundial.", 
            color=discord.Color.gold()
        )
        await ctx.send(embed=emb, view=view)
    else:
        view = CareerHubView(ctx, data)
        msg = await ctx.send(embed=view.build_embed(), view=view)
        view.message = msg


# =====================================================================
# SISTEMAS ORIGINAIS (TEXTOS, MOTOR DE PARTIDA SIMPLES, MERCADO GLOBAL)
# =====================================================================

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

def draw_metallic_text(draw, pos, text, font, base_color, shadow_color, highlight_color, anchor):
    x, y = pos
    draw.text((x + 2, y + 2), text, font=font, fill=shadow_color, anchor=anchor)
    draw.text((x, y), text, font=font, fill=base_color, anchor=anchor)
    draw.text((x - 1, y - 1), text, font=font, fill=highlight_color, anchor=anchor)

def render_single_card_sync(player):
    c_w, c_h = 300, 450
    card = Image.new("RGBA", (c_w, c_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(card)
    
    ovr = player.get('overall', 70)
    
    if ovr >= 90: 
        c_top = (70, 15, 90)
        c_bot = (30, 5, 40)
    elif ovr >= 80: 
        c_top = (184, 134, 11)
        c_bot = (60, 50, 20)
    elif ovr >= 75: 
        c_top = (192, 192, 192)
        c_bot = (128, 128, 128)
    else: 
        c_top = (160, 82, 45)
        c_bot = (60, 30, 15)

    bg_img = Image.new("RGBA", (c_w, c_h))
    draw_bg = ImageDraw.Draw(bg_img)
    
    for y in range(c_h):
        ratio = y / c_h
        r = int(c_top[0] * (1 - ratio) + c_bot[0] * ratio)
        g = int(c_top[1] * (1 - ratio) + c_bot[1] * ratio)
        b = int(c_top[2] * (1 - ratio) + c_bot[2] * ratio)
        draw_bg.line([(0, y), (c_w, y)], fill=(r, g, b, 255))
        
    pattern_color = (255, 255, 255, 30)
    spacing = 25
    
    for x in range(0, c_w + spacing, spacing):
        for y in range(0, c_h + spacing, spacing):
            if (y // spacing) % 2 == 0:
                offset_x = (spacing // 2)
            else:
                offset_x = 0
                
            draw_bg.polygon([
                (x + offset_x, y - 4), 
                (x + offset_x + 4, y), 
                (x + offset_x, y + 4), 
                (x + offset_x - 4, y)
            ], fill=pattern_color)

    mask = Image.new("L", (c_w, c_h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([5, 5, c_w-5, c_h-5], radius=25, fill=255)
    card.paste(bg_img, (0, 0), mask)

    try:
        p_img_res = requests.get(player["image"], timeout=5)
        p_img = Image.open(BytesIO(p_img_res.content)).convert("RGBA")
        p_img = p_img.resize((240, 240), Image.Resampling.LANCZOS)
        
        glow = p_img.filter(ImageFilter.GaussianBlur(radius=3))
        r, g, b, a = glow.split()
        glow = Image.merge("RGBA", (Image.new("L", a.size, 220), Image.new("L", a.size, 220), Image.new("L", a.size, 220), a))
        
        card.paste(glow, (int(c_w/2 - 120), 80), glow)
        card.paste(p_img, (int(c_w/2 - 120), 80), p_img)
    except Exception: 
        pass

    border_shades = [(100, 100, 100), (140, 140, 140), (180, 180, 180), (220, 220, 220), (160, 160, 160)]
    widths = [10, 8, 6, 4, 2] 
    
    for i, shade in enumerate(border_shades):
        draw.rounded_rectangle([5+i, 5+i, c_w-5-i, c_h-5-i], radius=25-i, outline=shade, width=widths[i])

    try:
        f_ovr = ImageFont.truetype(FONT_PATH, 90)
        f_pos = ImageFont.truetype(FONT_PATH, 45)
        f_name = ImageFont.truetype(FONT_PATH, 35)
    except:
        f_ovr = f_pos = f_name = ImageFont.load_default()

    silver_base = (200, 200, 200)
    silver_shadow = (80, 80, 80)
    silver_highlight = (240, 240, 240)

    draw_metallic_text(draw, (35, 30), str(ovr), f_ovr, silver_base, silver_shadow, silver_highlight, "la")
    draw_metallic_text(draw, (35, 120), player['position'], f_pos, silver_base, silver_shadow, silver_highlight, "la")

    nome_cru = player['name'].split()[-1].upper()
    max_text_width = c_w - 40
    current_font_size = 35
    
    try:
        while f_name.getlength(nome_cru) > max_text_width and current_font_size > 18:
            current_font_size -= 2
            f_name = ImageFont.truetype(FONT_PATH, current_font_size)
    except: 
        pass
        
    draw.text((c_w/2 + 2, 385 + 2), nome_cru, font=f_name, fill=(0, 0, 0), anchor="mm")
    draw.text((c_w/2, 385), nome_cru, font=f_name, fill=(255, 255, 255), anchor="mm")

    buf = BytesIO()
    card.save(buf, format='PNG')
    buf.seek(0)
    return buf

class AddPlayerModal(discord.ui.Modal, title='Definir Status da Carta'):
    def __init__(self, rbx_name, img_url):
        super().__init__()
        self.rbx_name = rbx_name
        self.img_url = img_url
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
                
                if res.data:
                    cards = res.data[0]["data"]
                else:
                    cards = []
                    
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
                
            await inter.response.send_message(f"✅ **{self.nick}** atualizado para {o} OVR e Posição {p_str}!")
        except:
            await inter.response.send_message("❌ Erro na edição.", ephemeral=True)

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
                
                if res.data:
                    cards = res.data[0]["data"]
                else:
                    cards = []
                    
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
            emb = discord.Embed(title="✅ Análise Concluída", description="Todos da fila foram avaliados.", color=discord.Color.green())
            await self.message.edit(embed=emb, view=None)
            return
            
        p = self.queue[self.index]
        emb = discord.Embed(title="🔍 Olheiro de Base - Análise", color=discord.Color.purple())
        emb.add_field(name="📛 Discord", value=p['discord_name'], inline=True)
        emb.add_field(name="🎮 Roblox Nick", value=f"**{p['nick']}**", inline=True)
        emb.set_image(url=p['image'])
        emb.set_footer(text=f"Membro {self.index + 1} de {len(self.queue)}")
        
        self.children[0].disabled = (self.index == 0)
        self.children[1].disabled = (self.index == len(self.queue) - 1)
        
        await self.message.edit(embed=emb, view=self)

    @discord.ui.button(label="⏪", style=discord.ButtonStyle.grey)
    async def prev(self, inter: discord.Interaction, b):
        if inter.user != self.ctx.author: 
            return
            
        await inter.response.defer()
        self.index -= 1
        await self.update_view()

    @discord.ui.button(label="⏩", style=discord.ButtonStyle.grey)
    async def next(self, inter: discord.Interaction, b):
        if inter.user != self.ctx.author: 
            return
            
        await inter.response.defer()
        self.index += 1
        await self.update_view()

    @discord.ui.button(label="➕ Cadastrar", style=discord.ButtonStyle.success)
    async def add(self, inter: discord.Interaction, b):
        if inter.user != self.ctx.author: 
            return
            
        p = self.queue[self.index]
        modal = AnalyzeAddModal(self, p['nick'], p['image'])
        await inter.response.send_modal(modal)

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
            return await inter.response.send_message("❌ Alguém já está jogando!", ephemeral=True)
            
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
            
        await inter.response.edit_message(content=f"🚫 O desafio foi recusado por {self.opponent.mention}.", view=self)

async def simulate_match(ctx, challenger, opponent, d1, d2, message):
    try:
        f1 = sum(x['overall'] for x in d1['team'] if x)
        f2 = sum(x['overall'] for x in d2['team'] if x)
        
        diff = f1 - f2
        prob_t1 = max(20, min(80, 50 + diff))
        
        s1 = 0
        s2 = 0
        minuto_atual = 0
        meio_tempo_feito = False
        event_log = ["🎙️ O juiz apita e a bola está rolando!"]
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
                evento_str = f"[{minuto_atual}'] ⏱️ Intervalo na EFL! Fim do primeiro tempo."
            else:
                event_type = random.randint(1, 100)
                
                try:
                    jogador_ataque = random.choice(players_attack)['name']
                except:
                    jogador_ataque = "Atacante"
                    
                try:
                    goleiro_defesa = next((p['name'] for p in players_defend if p['position'] in ['PO', 'GK', 'GOL']), random.choice(players_defend)['name'])
                except:
                    goleiro_defesa = "Goleiro"
                
                if event_type <= 18:
                    evento_str = f"[{minuto_atual}'] " + random.choice(GOAL_NARRATIONS).format(attacker=jogador_ataque)
                    if atacante_id == 1: 
                        s1 += 1
                    else: 
                        s2 += 1
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
            emb.description = f"{placar}\n\n**Lances:**\n```\n{log_text}\n```"
            
            await message.edit(content="", embed=emb, view=None)
            await asyncio.sleep(3.0)

        if s1 > s2: 
            d1['wins'] += 1
            d2['losses'] += 1
            res = f"Fim de papo! A vitória é do {challenger.display_name}!"
        elif s2 > s1: 
            d2['wins'] += 1
            d1['losses'] += 1
            res = f"Fim de papo! O {opponent.display_name} leva a melhor fora de casa!"
        else: 
            res = "Fim de jogo! Empate!"
            
        await save_user_data(challenger.id, d1)
        await save_user_data(opponent.id, d2)
        
        event_log.append(f"🏁 FIM: {res}")
        if len(event_log) > 7: 
            event_log.pop(0)
            
        log_text = "\n\n".join(event_log)
        emb.description = f"## 🔵 {challenger.display_name} {s1} x {s2} {opponent.display_name} 🔴\n\n**Lances:**\n```\n{log_text}\n```"
        
        await message.edit(embed=emb)
        
    finally:
        active_matches.discard(challenger.id)
        active_matches.discard(opponent.id)

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
                
            ALL_PLAYERS.extend(comunidade)
    except Exception as e: 
        pass

async def get_user_data(user_id):
    uid = str(user_id)
    try:
        res = supabase.table("jogadores").select("data").eq("id", uid).execute()
        
        if not res.data:
            initial = {
                "money": INITIAL_MONEY, 
                "squad": [], 
                "team": [None]*11, 
                "wins": 0, 
                "losses": 0, 
                "match_history": [], 
                "achievements": [], 
                "contracted_players": [], 
                "club_name": None, 
                "club_sigla": "EFL", 
                "formation": "4-3-3", 
                "captain": None, 
                "last_caixa_use": None, 
                "last_obter_use": None
            }
            supabase.table("jogadores").insert({"id": uid, "data": initial}).execute()
            return initial
            
        data = res.data[0]["data"]
        defaults = [
            ("losses", 0), 
            ("achievements", []), 
            ("match_history", []), 
            ("contracted_players", []), 
            ("club_name", None), 
            ("club_sigla", "EFL"), 
            ("formation", "4-3-3"), 
            ("captain", None), 
            ("last_caixa_use", None), 
            ("last_obter_use", None)
        ]
        
        for key, val in defaults:
            if key not in data: 
                data[key] = val
                
        if "team" not in data or len(data["team"]) != 11:
            old_team = data.get("team", [])
            new_team = [None] * 11
            
            for idx, p in enumerate(old_team):
                if p and idx < 11: 
                    new_team[idx] = p
                    
            data["team"] = new_team

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

def create_team_image_sync(team_players, club_name, club_sigla, user_money, formation, captain_name):
    width = 840
    height = 1240 
    
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
        if i not in coords: 
            continue
            
        cx, cy = coords[i]
        cw = 120
        ch = 180 
        card_box = [cx - cw//2, cy - ch//2, cx + cw//2, cy + ch//2]
        
        if player:
            player = add_player_defaults(player)
            eff_ovr = get_player_effective_overall(player)
            total_overall += eff_ovr
            
            if eff_ovr >= 90: 
                card_bg = (45, 10, 60, 240)
                border = "#e74c3c" 
            elif eff_ovr >= 80: 
                card_bg = (30, 30, 30, 240)
                border = "#f1c40f" 
            elif eff_ovr >= 70: 
                card_bg = (50, 50, 50, 240)
                border = "#bdc3c7" 
            else: 
                card_bg = (60, 40, 30, 240)
                border = "#cd7f32" 
            
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

class TeamManagerView(discord.ui.View):
    def __init__(self, ctx, user_data):
        super().__init__(timeout=300)
        self.ctx = ctx
        self.user_data = user_data

    async def refresh_board(self, inter, content_msg):
        buf = await generate_team_image(self.user_data, self.ctx.author)
        await inter.message.edit(content=content_msg, attachments=[discord.File(buf, "team.png")], view=self)

    @discord.ui.select(placeholder="📋 Mudar Formação", min_values=1, max_values=1, options=[
        discord.SelectOption(label="4-3-3 (Padrão)", value="4-3-3", description="Ataque total com 3 Meias e 3 DC"),
        discord.SelectOption(label="4-4-2", value="4-4-2", description="Equilíbrio com 4 Meias e 2 DC"),
        discord.SelectOption(label="3-4-3", value="3-4-3", description="Ofensivo com 3 DFC, 4 Meias e 3 DC")
    ])
    async def select_formation(self, inter: discord.Interaction, select: discord.ui.Select):
        if inter.user != self.ctx.author: 
            return
            
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
        if inter.user != self.ctx.author: 
            return
            
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
            
        await self.refresh_board(inter, "⚡ **Escalação Automática:** Os melhores jogadores escalados nas vagas livres!")

    @discord.ui.button(label="🎖️ Escolher Capitão", style=discord.ButtonStyle.primary)
    async def btn_captain(self, inter: discord.Interaction, button: discord.ui.Button):
        if inter.user != self.ctx.author: 
            return
            
        team_players = [p for p in self.user_data['team'] if p]
        
        if not team_players: 
            return await inter.response.send_message("❌ Você precisa ter jogadores escalados na prancheta.", ephemeral=True)
            
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
        if inter.user != self.ctx.author: 
            return
            
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
        self.author = author
        self.rbx = rbx
        self.img = img

    @discord.ui.button(label="Definir Status", style=discord.ButtonStyle.success, emoji="⚙️")
    async def btn(self, inter, b): 
        if inter.user == self.author: 
            await inter.response.send_modal(AddPlayerModal(self.rbx, self.img))

class EditPlayerView(discord.ui.View):
    def __init__(self, author, nick): 
        super().__init__(timeout=120)
        self.author = author
        self.nick = nick

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
        if inter.user != self.author: 
            return
            
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
        if inter.user != self.author: 
            return
            
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
        if inter.user != self.ctx.author: 
            return
            
        self.i -= 1
        await self.update_view(inter)

    @discord.ui.button(label="⏩", style=discord.ButtonStyle.grey)
    async def next(self, inter, b): 
        if inter.user != self.ctx.author: 
            return
            
        self.i += 1
        await self.update_view(inter)

    @discord.ui.button(label="Ação", style=discord.ButtonStyle.primary)
    async def act(self, inter, b): 
        if inter.user != self.ctx.author: 
            return
            
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
                    if done: 
                        break
                        
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
    if ctx.command and ctx.command.name == 'disableall': 
        return True
        
    if MAINTENANCE_MODE and not ctx.author.guild_permissions.administrator:
        await ctx.send("🛠️ **SISTEMA EM MANUTENÇÃO.**")
        return False
        
    return True

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        horas = int(error.retry_after // 3600)
        minutos = int((error.retry_after % 3600) // 60)
        segundos = int(error.retry_after % 60)
        return await ctx.send(f"⏳ **Calma aí, chefinho!** O comando está em tempo de recarga.\n\nTente usar novamente em **{horas}h {minutos}m {segundos}s**.")
        
    if isinstance(error, commands.CommandNotFound): 
        return
        
    if isinstance(error, commands.CheckFailure): 
        return
        
    print(f"Erro detectado: {error}")

# --- 9. COMANDOS DE ADMINISTRAÇÃO E FIX ROBLOX ---

@bot.command(name='disableall')
@is_bot_admin()
async def disableall_cmd(ctx):
    await ctx.send("⚠️ **ATENÇÃO!** Digite exatamente:\n`DESABILITAR EFL GURU BOT`\n*(Você tem 30 segundos)*")
    
    def check(m): 
        return m.author.id == ctx.author.id and m.channel == ctx.channel
        
    try:
        msg = await bot.wait_for('message', check=check, timeout=30.0)
        
        if msg.content == "DESABILITAR EFL GURU BOT":
            await ctx.send("🛑 **Recebido.** Fechando as portas do servidor desta versão e morrendo com honra... Pode mandar a nova versão, mestre!")
            await bot.close()
            os._exit(0) 
        else: 
            await ctx.send("❌ Confirmação incorreta. O bot continuará online e rodando.")
            
    except asyncio.TimeoutError: 
        await ctx.send("⏳ Tempo esgotado. A operação de autodestruição foi cancelada.")

@bot.command(name='lock')
@is_bot_admin()
async def lock_cmd(ctx):
    global MAINTENANCE_MODE
    MAINTENANCE_MODE = True
    await ctx.send("🛑 **SISTEMA BLOQUEADO.**")

@bot.command(name='unlock')
@is_bot_admin()
async def unlock_cmd(ctx):
    global MAINTENANCE_MODE
    MAINTENANCE_MODE = False
    await ctx.send("🟢 **SISTEMA LIBERADO.**")

# =====================================================================
# COMANDOS DE GERENCIAMENTO GERAL DO BOT E ROBLOX
# =====================================================================
