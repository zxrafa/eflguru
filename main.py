# -*- coding: utf-8 -*-
"""
EFL Guru - Versão 47.0 (MODO CARREIRA DEFINITIVO - FUT7, LIGA REAL E HUB)
----------------------------------------------------------------------
- CÓDIGO COMPLETO: Nenhuma linha removida ou otimizada.
- NOVA ESTRUTURA DE ELENCO: Modo carreira agora é Fut7 (7 titulares, 7 reservas).
- SISTEMA DE LIGA: Tabela de classificação real com 20 times simulados simultaneamente.
- MENU HUB: Navegação profissional por abas (Dropdown Menu).
- EVENTOS ALEATÓRIOS: Decisões narrativas que afetam moral e finanças.
- MERCADO AVANÇADO: Busca por nome e negociação direta de passes.
- PRANCHETA CARREIRA: Gera a imagem do time HD com a formação de 7 jogadores.
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
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

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

# --- SISTEMA DE PERMISSÕES SUPREMAS E TRAVAS ---
BOT_ADMINS = [338704196180115458, 1076957467935789056]
MAINTENANCE_MODE = False
GLOBAL_DISABLED = False

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

# --- MOTOR TÁTICO DINÂMICO (11v11 PADRÃO E 7v7 CARREIRA) ---
def get_formation_config(formation, is_7v7=False):
    if is_7v7:
        if formation == "2-2-2":
            coords = {
                0: (420, 1060), # GK
                1: (280, 830), 2: (560, 830), # 2 DEF
                3: (280, 530), 4: (560, 530), # 2 MID
                5: (280, 230), 6: (560, 230)  # 2 ATT
            }
            mapping = {
                "GOL": [0],
                "ZAG": [1, 2], "LAT": [1, 2],
                "MEI": [3, 4], "VOL": [3, 4],
                "ATA": [5, 6]
            }
        elif formation == "3-2-1":
            coords = {
                0: (420, 1060), # GK
                1: (200, 830), 2: (420, 850), 3: (640, 830), # 3 DEF
                4: (280, 530), 5: (560, 530), # 2 MID
                6: (420, 230) # 1 ATT
            }
            mapping = {
                "GOL": [0],
                "ZAG": [1, 2, 3], "LAT": [1, 2, 3],
                "MEI": [4, 5], "VOL": [4, 5],
                "ATA": [6]
            }
        else: # Padrão Fut7: 2-3-1
            coords = {
                0: (420, 1060), # GK
                1: (280, 830), 2: (560, 830), # 2 DEF
                3: (200, 530), 4: (420, 560), 5: (640, 530), # 3 MID
                6: (420, 230) # 1 ATT
            }
            mapping = {
                "GOL": [0],
                "ZAG": [1, 2], "LAT": [1, 2],
                "MEI": [3, 4, 5], "VOL": [3, 4, 5],
                "ATA": [6]
            }
        return coords, mapping
    else:
        # Configuração original de 11 jogadores
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
# 🚀 MODO CARREIRA V2: LIGA REAL, EVENTOS E HUB COMPLETO (7v7)
# =====================================================================

CAREER_CLUBS = {
    1: [
        {"name": "EFL Elite FC", "budget": 150000000, "expect": "Vencer a Liga", "base_ovr": 85}, 
        {"name": "Supremos AC", "budget": 120000000, "expect": "Top 3", "base_ovr": 84}
    ],
    2: [
        {"name": "União Cidadã", "budget": 40000000, "expect": "Subir de Divisão", "base_ovr": 78}, 
        {"name": "Real Sindicato", "budget": 35000000, "expect": "Meio de Tabela", "base_ovr": 76}
    ],
    3: [
        {"name": "Operário FC", "budget": 8000000, "expect": "Subir de Divisão", "base_ovr": 68}, 
        {"name": "Várzea Rovers", "budget": 5000000, "expect": "Sobreviver", "base_ovr": 66}
    ]
}

AI_TEAM_NAMES = [
    "Galáticos FC", "Titãs United", "Sporting Clube", "Dragões City", "Legião FC", 
    "Sparta AC", "Nova Era", "Imperiais", "Lobos FC", "Atlético Central",
    "Vanguarda", "Fênix United", "Aliança", "Invictos FC", "Falcões City",
    "Cometas AC", "Pioneiros", "Guardiões", "Realeza FC", "Norte City"
]

TACTICAL_STYLES = {
    "Tiki-Taka": {"desc": "Posse de bola e passes. Cansaço médio.", "atk_bonus": 1.1, "def_bonus": 1.0, "stam_cost": 5},
    "Gegenpressing": {"desc": "Pressão alta absurda. Ataque letal, drena físico.", "atk_bonus": 1.25, "def_bonus": 1.05, "stam_cost": 12},
    "Retranca": {"desc": "Defesa sólida e contra-ataque. Pouco desgaste.", "atk_bonus": 0.8, "def_bonus": 1.3, "stam_cost": 3},
    "Equilibrado": {"desc": "Abordagem padrão. Bom balanço geral.", "atk_bonus": 1.0, "def_bonus": 1.0, "stam_cost": 6}
}

CAREER_EVENTS = [
    {
        "title": "🤬 Jogador Insatisfeito",
        "desc": "Um dos seus reservas reclamou publicamente da falta de minutos em campo. Como você lida com isso?",
        "options": [
            {"label": "Dar uma bronca severa", "cost": 0, "morale": -15, "confidence": +5, "response": "Você mostrou quem manda. A diretoria gostou, mas o elenco ficou tenso."},
            {"label": "Prometer mais tempo (Acalmar)", "cost": 0, "morale": +10, "confidence": -5, "response": "Você apaziguou a situação, mas pareceu fraco para a diretoria."}
        ]
    },
    {
        "title": "💼 Reforma nas Instalações",
        "desc": "A diretoria sugeriu reformar o CT para melhorar a recuperação física dos atletas, mas vão descontar do seu orçamento.",
        "options": [
            {"label": "Aprovar reforma", "cost": 1500000, "morale": +15, "confidence": +10, "response": "O CT ficou moderno! Jogadores mais felizes e diretoria satisfeita."},
            {"label": "Recusar (Economizar)", "cost": 0, "morale": -5, "confidence": -5, "response": "Você poupou dinheiro, mas o elenco ficou decepcionado com a estrutura."}
        ]
    },
    {
        "title": "🎉 Noitada Clandestina",
        "desc": "Parte do elenco foi flagrada numa festa na véspera do jogo. O clima pesou.",
        "options": [
            {"label": "Multar jogadores", "cost": -200000, "morale": -20, "confidence": +15, "response": "Você aplicou multas pesadas. Dinheiro no cofre, mas o clima está horrível."},
            {"label": "Acobertar o caso", "cost": 50000, "morale": +5, "confidence": -20, "response": "Você pagou a mídia para abafar o caso. O elenco te adora, a diretoria desconfia."}
        ]
    }
]

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

def simplify_position(pos):
    """Converte posições complexas para categorias simples do Fut7"""
    pos_upper = pos.upper()
    if pos_upper in ["PO", "GK", "GOL"]: return "GOL"
    elif pos_upper in ["DFC", "CB", "ZAG", "LD", "LE", "RB", "LB"]: return "ZAG"
    elif pos_upper in ["MDC", "MC", "MCO", "VOL"]: return "MEI"
    else: return "ATA"

def generate_initial_squad_7v7(tier):
    """Gera elenco de 14 jogadores (7 tit / 7 res) usando o banco de dados global"""
    global ALL_PLAYERS
    squad = []
    pool = list(ALL_PLAYERS)
    
    if not pool:
        pool = [{"name": "Jogador Genérico", "overall": 60, "position": "MC", "value": 150000, "image": ""}]
        
    if tier == 3: max_ovr = 74
    elif tier == 2: max_ovr = 82
    else: max_ovr = 999
        
    pool_ordenado = sorted(pool, key=lambda x: x.get('overall', 70))
    filtered_pool = [p for p in pool_ordenado if p.get('overall', 70) <= max_ovr]
            
    if len(filtered_pool) < 14:
        filtered_pool = pool_ordenado[:14]
        if len(filtered_pool) < 14:
            # Se ainda faltar, preenche duplicando
            filtered_pool = filtered_pool * (14 // len(filtered_pool) + 1)
        
    random.shuffle(filtered_pool)
    
    for i in range(14):
        base_p = filtered_pool[i]
        pos_str = base_p.get("position", "MC").split('/')[0]
        pos_cat = simplify_position(pos_str)
        
        idade_mock = random.randint(18, 32)
        potencial = base_p.get("overall", 70)
        
        if idade_mock < 24:
            potencial = potencial + random.randint(2, 8)
            
        valor = base_p.get("value", calculate_player_value(base_p.get("overall", 70)))
        salario = int(valor * 0.005)
        
        career_p = {
            "id": base_p.get("name") + str(i),
            "name": base_p.get("name"),
            "image": base_p.get("image", ""),
            "pos": pos_cat,
            "age": idade_mock,
            "ovr": base_p.get("overall", 70),
            "pot": potencial,
            "fitness": 100,
            "morale": 80,
            "value": valor,
            "wage": salario,
            "status": "Reserva"
        }
        squad.append(career_p)
        
    return squad

def generate_league_table(player_club_name, tier):
    """Cria a tabela de classificação com 20 times (1 player + 19 bots)"""
    table = {}
    base_ovr = {1: 85, 2: 76, 3: 66}[tier]
    
    # Adiciona o player
    table[player_club_name] = {"pts": 0, "w": 0, "d": 0, "l": 0, "gf": 0, "ga": 0, "is_player": True, "ovr": base_ovr}
    
    # Sorteia 19 times bot
    bot_names = random.sample(AI_TEAM_NAMES, 19)
    for name in bot_names:
        # Cria variações de força entre os bots
        bot_ovr = base_ovr + random.randint(-4, 5)
        table[name] = {"pts": 0, "w": 0, "d": 0, "l": 0, "gf": 0, "ga": 0, "is_player": False, "ovr": bot_ovr}
        
    return table

def generate_fixtures(teams):
    """Gera uma lista de adversários para as 38 rodadas (Turno e Returno)"""
    teams_list = list(teams.keys())
    random.shuffle(teams_list)
    fixtures = []
    
    # Simplificação algorítmica para a Liga:
    # Para o player, apenas listamos os 19 adversários, duas vezes (38 rodadas).
    opponents = [t for t in teams_list if not teams[t]['is_player']]
    
    turno = list(opponents)
    random.shuffle(turno)
    returno = list(opponents)
    random.shuffle(returno)
    
    return turno + returno

def simulate_bot_matches(table):
    """Simula os resultados da rodada para os times da IA"""
    bots = [name for name, data in table.items() if not data['is_player']]
    random.shuffle(bots)
    
    # Simula partidas em pares
    for i in range(0, len(bots)-1, 2):
        t1 = bots[i]
        t2 = bots[i+1]
        
        ovr1 = table[t1]['ovr']
        ovr2 = table[t2]['ovr']
        
        diff = ovr1 - ovr2
        prob_t1 = 50 + diff
        
        g1 = 0
        g2 = 0
        
        for _ in range(5): # 5 lances capitais simulados
            roll = random.randint(1, 100)
            if roll <= prob_t1:
                if random.random() > 0.5: g1 += 1
            else:
                if random.random() > 0.5: g2 += 1
                
        table[t1]['gf'] += g1
        table[t1]['ga'] += g2
        table[t2]['gf'] += g2
        table[t2]['ga'] += g1
        
        if g1 > g2:
            table[t1]['w'] += 1
            table[t1]['pts'] += 3
            table[t2]['l'] += 1
        elif g2 > g1:
            table[t2]['w'] += 1
            table[t2]['pts'] += 3
            table[t1]['l'] += 1
        else:
            table[t1]['d'] += 1
            table[t2]['d'] += 1
            table[t1]['pts'] += 1
            table[t2]['pts'] += 1

def sort_table(table):
    """Retorna a tabela ordenada por pontos, depois vitórias, depois saldo de gols"""
    def sorter(item):
        name, stats = item
        sg = stats['gf'] - stats['ga']
        return (stats['pts'], stats['w'], sg)
        
    return sorted(table.items(), key=sorter, reverse=True)


# =====================================================================
# 🚀 MODO CARREIRA: UI (HUB, TABS E VIEWS)
# =====================================================================

class CareerSetupView(discord.ui.View):
    def __init__(self, ctx):
        super().__init__(timeout=300)
        self.ctx = ctx
        self.coach_name = ctx.author.display_name
        self.style = "Equilibrado"
        self.mental = "Estrategista"

    @discord.ui.button(label="Nome do Técnico", style=discord.ButtonStyle.secondary, emoji="🧑‍💼")
    async def btn_name(self, inter: discord.Interaction, b):
        if inter.user != self.ctx.author: return
        modal = CareerNameModal(self)
        await inter.response.send_modal(modal)

    @discord.ui.select(placeholder="Estilo de Jogo", options=[
        discord.SelectOption(label="Tiki-Taka", description="Posse de bola, passes curtos."),
        discord.SelectOption(label="Gegenpressing", description="Pressão alta, perde muita energia."),
        discord.SelectOption(label="Retranca", description="Defesa fechada, contra-ataques."),
        discord.SelectOption(label="Equilibrado", description="Balanceado sem fraquezas extremas.")
    ])
    async def sel_style(self, inter: discord.Interaction, select: discord.ui.Select):
        if inter.user != self.ctx.author: return
        self.style = select.values[0]
        await inter.response.edit_message(embed=self.build_embed())

    @discord.ui.select(placeholder="Mentalidade do Treinador", options=[
        discord.SelectOption(label="Estrategista", description="Bônus de OVR temporário em jogos chave."),
        discord.SelectOption(label="Disciplinador", description="Jogadores recuperam Moral e Forma mais rápido."),
        discord.SelectOption(label="Desenvolvedor", description="Jogadores jovens sobem de OVR mais rápido.")
    ])
    async def sel_mental(self, inter: discord.Interaction, select: discord.ui.Select):
        if inter.user != self.ctx.author: return
        self.mental = select.values[0]
        await inter.response.edit_message(embed=self.build_embed())

    @discord.ui.button(label="Avançar para Escolha de Clube", style=discord.ButtonStyle.success, row=3)
    async def btn_next(self, inter: discord.Interaction, b):
        if inter.user != self.ctx.author: return
        club_view = CareerClubSelectView(self.ctx, self.coach_name, self.style, self.mental)
        emb = discord.Embed(
            title="🏢 Mercado de Trabalho", 
            description="Como técnico iniciante, apenas clubes de divisões inferiores (Tier 3) confiam em você. Escolha onde iniciar sua jornada:", 
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
        self.c_name, self.c_style, self.c_mental = c_name, c_style, c_mental
        
        for c in CAREER_CLUBS[3]:
            btn = discord.ui.Button(label=f"Assinar com {c['name']}", style=discord.ButtonStyle.primary)
            btn.callback = self.make_callback(c)
            self.add_item(btn)

    def make_callback(self, club_data):
        async def callback(inter: discord.Interaction):
            if inter.user != self.ctx.author: return
            await inter.response.defer()
            
            squad = generate_initial_squad_7v7(3)
            league_table = generate_league_table(club_data['name'], 3)
            fixtures = generate_fixtures(league_table)
            
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
                    "year": "2026/27",
                    "week": 1, 
                    "table": league_table,
                    "fixtures": fixtures
                },
                "formation": "2-3-1", # Padrão Fut7
                "pending_event": None
            }
            
            await save_career_data(self.ctx.author.id, data)
            await inter.message.edit(content="⚽ **Contrato assinado!** Gerando tabela da liga, buscando jogadores reais do banco de dados...", embed=None, view=None)
            await asyncio.sleep(2)
            
            hub_view = CareerMainView(self.ctx, data)
            await inter.message.edit(content=None, embed=hub_view.build_dashboard_embed(), view=hub_view)
        return callback

class CareerMainView(discord.ui.View):
    def __init__(self, ctx, data):
        super().__init__(timeout=600)
        self.ctx = ctx
        self.data = data
        self.current_tab = "dashboard"
        
        # Setup do Menu Dropdown Principal
        self.nav_select = discord.ui.Select(
            placeholder="Navegar pelo Clube",
            options=[
                discord.SelectOption(label="Painel Geral", value="dashboard", emoji="🏠", description="Visão geral e avançar tempo"),
                discord.SelectOption(label="Elenco & Tática", value="squad", emoji="👥", description="Gerencie seus titulares"),
                discord.SelectOption(label="Prancheta HD", value="board", emoji="🖼️", description="Gera a imagem do seu time 7v7"),
                discord.SelectOption(label="Classificação", value="table", emoji="🏆", description="Tabela da Liga Atual"),
                discord.SelectOption(label="Mercado", value="market", emoji="🛒", description="Compre e venda jogadores"),
                discord.SelectOption(label="Decisões", value="events", emoji="🚨", description="Problemas do clube (Vida Real)")
            ],
            row=0
        )
        self.nav_select.callback = self.nav_callback
        self.add_item(self.nav_select)
        
        self.setup_tab_buttons()

    def setup_tab_buttons(self):
        # Remove botões dinâmicos (mantém apenas o select no índice 0)
        while len(self.children) > 1:
            self.remove_item(self.children[-1])

        if self.current_tab == "dashboard":
            btn_play = discord.ui.Button(label="Avançar Semana (Jogar)", style=discord.ButtonStyle.success, emoji="⏩", row=1)
            btn_play.callback = self.play_match
            self.add_item(btn_play)
            
        elif self.current_tab == "squad":
            btn_auto = discord.ui.Button(label="Auto-Escalar Time", style=discord.ButtonStyle.primary, emoji="⚡", row=1)
            btn_auto.callback = self.auto_squad
            self.add_item(btn_auto)
            
            btn_form = discord.ui.Button(label="Mudar Formação", style=discord.ButtonStyle.secondary, emoji="📋", row=1)
            btn_form.callback = self.change_formation
            self.add_item(btn_form)
            
        elif self.current_tab == "market":
            btn_scout = discord.ui.Button(label="Buscar Jogador por Nome", style=discord.ButtonStyle.success, emoji="🔍", row=1)
            btn_scout.callback = self.search_player_market
            self.add_item(btn_scout)

    async def nav_callback(self, inter: discord.Interaction):
        if inter.user != self.ctx.author: return
        await inter.response.defer()
        
        self.current_tab = self.nav_select.values[0]
        self.setup_tab_buttons()
        
        if self.current_tab == "dashboard":
            await inter.message.edit(embed=self.build_dashboard_embed(), attachments=[], view=self)
        elif self.current_tab == "squad":
            await inter.message.edit(embed=self.build_squad_embed(), attachments=[], view=self)
        elif self.current_tab == "table":
            await inter.message.edit(embed=self.build_table_embed(), attachments=[], view=self)
        elif self.current_tab == "market":
            await inter.message.edit(embed=self.build_market_embed(), attachments=[], view=self)
        elif self.current_tab == "events":
            await self.handle_events_tab(inter)
        elif self.current_tab == "board":
            await self.handle_board_tab(inter)

    # --- RENDERIZADORES DE EMBEDS (ABAS) ---
    def build_dashboard_embed(self):
        c = self.data['coach']
        cl = self.data['club']
        s = self.data['season']
        
        my_stats = s['table'][cl['name']]
        
        titulares_count = len([p for p in self.data['squad'] if p['status'] == 'Titular'])
        
        if s['week'] <= 38:
            next_opp = s['fixtures'][s['week']-1]
            status_text = f"Próximo Jogo: **vs {next_opp}**"
        else:
            status_text = "Fim de Temporada. Aguarde as propostas."

        e = discord.Embed(title=f"🏢 Hub do Manager: {cl['name']}", description=status_text, color=discord.Color.dark_theme())
        e.add_field(name="📅 Temporada", value=f"{s['year']} - Semana {s['week']}/38", inline=True)
        e.add_field(name="📊 Campanha", value=f"Pts: {my_stats['pts']} | V: {my_stats['w']} | E: {my_stats['d']} | D: {my_stats['l']}", inline=True)
        e.add_field(name="🧑‍💼 Treinador", value=f"Reputação: {c['reputation']}/100\nEstilo: {c['style']}", inline=True)
        e.add_field(name="💼 Finanças", value=f"Orçamento: R$ {cl['budget']:,}\nConfiança: {cl['confidence']}%", inline=True)
        e.add_field(name="👥 Elenco", value=f"Titulares: {titulares_count}/7\nTática: {self.data['formation']}", inline=True)
        
        if self.data.get('pending_event'):
            e.description += "\n\n🚨 **ATENÇÃO: Você tem decisões pendentes na aba de Eventos!**"
            
        return e

    def build_squad_embed(self):
        tits = [p for p in self.data['squad'] if p['status'] == 'Titular']
        res = [p for p in self.data['squad'] if p['status'] != 'Titular']
        
        t_str_list = [f"`{p['pos']}` **{p['name']}** | ⭐{p['ovr']} | 🔋{p['fitness']}% | 😃{p['morale']}%" for p in tits]
        t_str = "\n".join(t_str_list)
        
        r_str_list = [f"`{p['pos']}` {p['name']} | ⭐{p['ovr']} | 🔋{p['fitness']}%" for p in res[:10]]
        r_str = "\n".join(r_str_list)
        
        e = discord.Embed(title="📋 Seu Elenco Atual (Fut7)", color=discord.Color.green())
        e.add_field(name=f"Titulares ({len(tits)}/7)", value=t_str or "Nenhum titular.", inline=False)
        e.add_field(name="Reservas", value=r_str or "Sem reservas.", inline=False)
        return e

    def build_table_embed(self):
        table_sorted = sort_table(self.data['season']['table'])
        
        desc = "```\nPos | Clube                | Pts | V  | E  | D  | SG\n"
        desc += "-"*55 + "\n"
        
        for idx, (name, stats) in enumerate(table_sorted):
            if name == self.data['club']['name']:
                name_disp = f"⭐ {name[:14]}"
            else:
                name_disp = name[:18]
                
            sg = stats['gf'] - stats['ga']
            
            # Limita para não estourar o limite do Discord, mostra topo, player e zona rebaixamento
            if idx < 6 or idx > 16 or name == self.data['club']['name']:
                desc += f"{idx+1:02d}. | {name_disp:<18} | {stats['pts']:<3} | {stats['w']:<2} | {stats['d']:<2} | {stats['l']:<2} | {sg:>2}\n"
            elif idx == 6:
                desc += "... | ...                  | ... | .. | .. | .. | ..\n"
                
        desc += "```"
        e = discord.Embed(title=f"🏆 Classificação da Liga (Tier {self.data['club']['tier']})", description=desc, color=discord.Color.gold())
        return e

    def build_market_embed(self):
        e = discord.Embed(title="🛒 Mercado de Transferências", description="Gaste seu orçamento para melhorar seu elenco buscando jogadores reais do banco de dados da EFL.", color=discord.Color.purple())
        e.add_field(name="💰 Orçamento Atual", value=f"R$ {self.data['club']['budget']:,}", inline=False)
        e.add_field(name="Como Contratar?", value="Clique no botão abaixo para buscar um jogador do banco de dados global pelo nome. Você fará uma oferta de compra direta para o clube dele.", inline=False)
        return e

    # --- LÓGICA DAS ABAS ESPECÍFICAS ---
    
    async def handle_board_tab(self, inter: discord.Interaction):
        await inter.message.edit(embed=discord.Embed(title="🖼️ Gerando Prancheta HD...", color=discord.Color.blue()))
        
        team_players = [None]*7
        titulares = [p for p in self.data['squad'] if p['status'] == 'Titular']
        
        # Mapeamento estúpido simples para a imagem
        for i in range(min(7, len(titulares))):
            team_players[i] = titulares[i]
            
        async with image_lock:
            try:
                # Adaptação para passar 7 jogadores para a função de 11 (os últimos slots ficam None)
                fake_11_squad = team_players + [None]*4
                buf = await asyncio.to_thread(create_team_image_sync, fake_11_squad, self.data['club']['name'], "EFL", self.data['club']['budget'], self.data['formation'], None)
                await inter.message.edit(content="Sua Prancheta Tática 7v7:", embed=None, attachments=[discord.File(buf, "board.png")], view=self)
            except Exception as e:
                await inter.message.edit(embed=discord.Embed(title="Erro ao gerar imagem", description=str(e)))

    async def handle_events_tab(self, inter: discord.Interaction):
        if not self.data.get('pending_event'):
            e = discord.Embed(title="🚨 Departamento Pessoal", description="Tudo tranquilo no clube. Sem problemas ou crises recentes no elenco.", color=discord.Color.light_grey())
            await inter.message.edit(embed=e, attachments=[], view=self)
            return
            
        ev = self.data['pending_event']
        e = discord.Embed(title=ev['title'], description=f"⚠️ **SITUAÇÃO NA VIDA REAL:**\n{ev['desc']}", color=discord.Color.orange())
        
        # Limpa botões antigos e coloca as opções de escolha
        while len(self.children) > 1:
            self.remove_item(self.children[-1])
            
        for idx, opt in enumerate(ev['options']):
            btn = discord.ui.Button(label=opt['label'], style=discord.ButtonStyle.danger if idx == 0 else discord.ButtonStyle.primary, row=1)
            btn.callback = self.make_event_callback(opt)
            self.add_item(btn)
            
        await inter.message.edit(embed=e, attachments=[], view=self)

    def make_event_callback(self, option):
        async def callback(inter: discord.Interaction):
            if inter.user != self.ctx.author: return
            await inter.response.defer()
            
            # Aplica consequências
            self.data['club']['budget'] -= option['cost']
            self.data['club']['confidence'] = min(100, max(0, self.data['club']['confidence'] + option.get('confidence', 0)))
            for p in self.data['squad']:
                p['morale'] = min(100, max(0, p['morale'] + option.get('morale', 0)))
                
            self.data['pending_event'] = None
            await save_career_data(self.ctx.author.id, self.data)
            
            e = discord.Embed(title="✅ Decisão Tomada", description=option['response'], color=discord.Color.green())
            
            # Restaura botões padrão
            self.current_tab = "dashboard"
            self.nav_select.values = ["dashboard"]
            self.setup_tab_buttons()
            
            await inter.message.edit(embed=e, view=self)
        return callback

    # --- BOTÕES DE AÇÃO ---

    async def auto_squad(self, inter: discord.Interaction):
        if inter.user != self.ctx.author: return
        await inter.response.defer()
        
        for p in self.data['squad']: 
            p['status'] = "Reserva"
        
        squad_sorted = sorted(self.data['squad'], key=lambda x: (x['ovr'], x['fitness']), reverse=True)
        _, mapping = get_formation_config(self.data['formation'], is_7v7=True)
        
        # Define vagas baseado no mapeamento 7v7 atual
        vagas = {"GOL": len(mapping.get("GOL", [])), "ZAG": len(mapping.get("ZAG", [])), "MEI": len(mapping.get("MEI", [])), "ATA": len(mapping.get("ATA", []))}
        
        for p in squad_sorted:
            cat = p['pos']
            if vagas.get(cat, 0) > 0:
                p['status'] = 'Titular'
                vagas[cat] -= 1
                
        # Força 7 jogadores se faltar posição exata
        tits = [p for p in self.data['squad'] if p['status'] == 'Titular']
        if len(tits) < 7:
            for p in squad_sorted:
                if p['status'] == 'Reserva':
                    p['status'] = 'Titular'
                    tits.append(p)
                if len(tits) == 7: break

        await save_career_data(self.ctx.author.id, self.data)
        await inter.message.edit(embed=self.build_squad_embed(), view=self)

    async def change_formation(self, inter: discord.Interaction):
        if inter.user != self.ctx.author: return
        
        view = discord.ui.View()
        select = discord.ui.Select(placeholder="Escolha a Tática Fut7", options=[
            discord.SelectOption(label="2-3-1 (Padrão Fut7)"),
            discord.SelectOption(label="2-2-2 (Ofensivo)"),
            discord.SelectOption(label="3-2-1 (Defensivo)")
        ])
        
        async def form_callback(i: discord.Interaction):
            await i.response.defer()
            self.data['formation'] = select.values[0]
            for p in self.data['squad']: p['status'] = 'Reserva' # Limpa escalação para evitar bug de posições
            await save_career_data(self.ctx.author.id, self.data)
            await inter.message.edit(embed=self.build_squad_embed(), view=self)
            
        select.callback = form_callback
        view.add_item(select)
        await inter.response.send_message("Mude sua formação abaixo (Seu time foi mandado pro banco para reorganizar):", view=view, ephemeral=True)

    async def search_player_market(self, inter: discord.Interaction):
        if inter.user != self.ctx.author: return
        
        class PlayerSearchModal(discord.ui.Modal, title='Buscar Jogador (ALL_PLAYERS)'):
            search_input = discord.ui.TextInput(label="Nome do Jogador", placeholder="Ex: Neymar")
            
            def __init__(self, view_ref):
                super().__init__()
                self.view_ref = view_ref
                
            async def on_submit(self, i: discord.Interaction):
                await i.response.defer(ephemeral=True)
                query = normalize_str(self.search_input.value)
                
                # Busca no BD global
                matches = [p for p in ALL_PLAYERS if query in normalize_str(p['name'])]
                
                if not matches:
                    return await i.followup.send("❌ Nenhum jogador encontrado com esse nome no mercado global.", ephemeral=True)
                    
                target = matches[0] # Pega o primeiro match
                target_value = calculate_player_value(target.get('overall', 70))
                premium_price = int(target_value * 1.2) # Clube inflaciona o preço
                
                # Verifica se já tem o cara
                if any(p['name'] == target['name'] for p in self.view_ref.data['squad']):
                    return await i.followup.send("❌ Você já tem este jogador no seu elenco!", ephemeral=True)
                
                emb = discord.Embed(title="🤝 Negociação de Transferência", description=f"O clube dono do passe de **{target['name']}** pede R$ {premium_price:,} para liberá-lo.", color=discord.Color.blue())
                emb.add_field(name="OVR", value=str(target.get('overall', 70)), inline=True)
                emb.add_field(name="Posição", value=target.get('position', 'MC'), inline=True)
                emb.add_field(name="Seu Orçamento", value=f"R$ {self.view_ref.data['club']['budget']:,}", inline=False)
                
                buy_view = discord.ui.View()
                btn_buy = discord.ui.Button(label="Comprar e Assinar Contrato", style=discord.ButtonStyle.success)
                
                async def buy_callback(buy_i: discord.Interaction):
                    if self.view_ref.data['club']['budget'] < premium_price:
                        return await buy_i.response.send_message("❌ Orçamento insuficiente.", ephemeral=True)
                        
                    self.view_ref.data['club']['budget'] -= premium_price
                    
                    # Converte pra player do Modo Carreira
                    new_career_player = {
                        "id": target['name'] + str(random.randint(100,999)),
                        "name": target['name'],
                        "image": target.get("image", ""),
                        "pos": simplify_position(target.get('position', 'MC')),
                        "age": random.randint(20, 32),
                        "ovr": target.get('overall', 70),
                        "pot": target.get('overall', 70) + random.randint(0, 5),
                        "fitness": 100,
                        "morale": 90, # Chega feliz
                        "value": target_value,
                        "wage": int(target_value * 0.005),
                        "status": "Reserva"
                    }
                    
                    self.view_ref.data['squad'].append(new_career_player)
                    await save_career_data(self.view_ref.ctx.author.id, self.view_ref.data)
                    
                    await buy_i.response.edit_message(content=f"✅ TRANSFERÊNCIA CONCLUÍDA! **{target['name']}** veste a camisa do seu clube.", embed=None, view=None)
                    await self.view_ref.message.edit(embed=self.view_ref.build_market_embed())
                    
                btn_buy.callback = buy_callback
                buy_view.add_item(btn_buy)
                
                await i.followup.send(embed=emb, view=buy_view, ephemeral=True)
                
        await inter.response.send_modal(PlayerSearchModal(self))

    async def play_match(self, inter: discord.Interaction):
        if inter.user != self.ctx.author: return
        
        titulares = [p for p in self.data['squad'] if p['status'] == 'Titular']
        if len(titulares) != 7:
            return await inter.response.send_message("❌ No Fut7 você precisa de EXATAMENTE 7 titulares para jogar! Vá na aba Elenco e auto-escale seu time.", ephemeral=True)

        if self.data['season']['week'] > 38:
            await inter.response.defer()
            view = CareerSeasonEndView(self.ctx, self.data)
            await inter.message.edit(embed=view.build_embed(), attachments=[], view=view)
            return

        for child in self.children:
            child.disabled = True
        await inter.response.edit_message(view=self)

        async with career_lock:
            # 1. PEGA O ADVERSÁRIO DA LIGA
            my_club_name = self.data['club']['name']
            current_week = self.data['season']['week']
            adv_name = self.data['season']['fixtures'][current_week - 1]
            adv_ovr = self.data['season']['table'][adv_name]['ovr']
                
            meu_ovr = sum(p['ovr'] for p in titulares) / 7
            
            fatigue_pen = sum((100 - p['fitness']) * 0.1 for p in titulares)
            morale_bonus = sum((p['morale'] - 50) * 0.05 for p in titulares)
            style_data = TACTICAL_STYLES[self.data['coach']['style']]
            
            forca_final = (meu_ovr - fatigue_pen + morale_bonus) * style_data['atk_bonus']
            
            meus_gols = 0
            adv_gols = 0
            eventos = []
            
            # SIMULAÇÃO LIVE
            for m in range(0, 91, 15):
                for p in titulares:
                    p['fitness'] = max(30, p['fitness'] - style_data['stam_cost'])
                
                chances = random.randint(1, 100)
                if chances < (forca_final / (forca_final + adv_ovr) * 100):
                    if random.random() > 0.6: 
                        meus_gols += 1
                        eventos.append(f"[{m}'] ⚽ Gol do {my_club_name}! Lindo lance de equipe.")
                elif chances > 80:
                    if random.random() > 0.6:
                        adv_gols += 1
                        eventos.append(f"[{m}'] ❌ Gol do {adv_name}. A defesa bobeou feio.")
                        
                log_temp = "\n".join(eventos) if eventos else "A bola rola e os times se estudam no meio-campo..."
                live_embed = discord.Embed(title=f"🔴 AO VIVO - Rodada {current_week}: {m}' Minutos", description=f"## 🔵 {my_club_name} {meus_gols} x {adv_gols} {adv_name} 🔴\n\n```\n{log_temp}\n```", color=discord.Color.red())
                await inter.message.edit(embed=live_embed)
                await asyncio.sleep(1.5) 
            
            # RESULTADOS E TABELA
            res_str = ""
            
            my_stats = self.data['season']['table'][my_club_name]
            adv_stats = self.data['season']['table'][adv_name]
            
            my_stats['gf'] += meus_gols
            my_stats['ga'] += adv_gols
            adv_stats['gf'] += adv_gols
            adv_stats['ga'] += meus_gols
            
            if meus_gols > adv_gols:
                self.data['season']['wins'] += 1
                my_stats['pts'] += 3
                my_stats['w'] += 1
                adv_stats['l'] += 1
                self.data['club']['confidence'] = min(100, self.data['club']['confidence'] + 5)
                self.data['coach']['reputation'] += 1
                res_str = "Vitória 🟢"
                for p in self.data['squad']: p['morale'] = min(100, p['morale'] + 10)
            elif adv_gols > meus_gols:
                self.data['season']['losses'] += 1
                my_stats['l'] += 1
                adv_stats['w'] += 1
                adv_stats['pts'] += 3
                self.data['club']['confidence'] -= 8
                res_str = "Derrota 🔴"
                for p in self.data['squad']: p['morale'] = max(0, p['morale'] - 15)
            else:
                self.data['season']['draws'] += 1
                my_stats['pts'] += 1
                adv_stats['pts'] += 1
                my_stats['d'] += 1
                adv_stats['d'] += 1
                res_str = "Empate 🟡"
                for p in self.data['squad']: p['morale'] = min(100, p['morale'] + 2)

            self.data['season']['week'] += 1
            
            # Simula a rodada pros bots
            simulate_bot_matches(self.data['season']['table'])
            
            # Eventos Aleatórios (Vida Real)
            if not self.data.get('pending_event') and random.random() < 0.20: # 20% chance por semana
                self.data['pending_event'] = random.choice(CAREER_EVENTS)
            
            if self.data['season']['week'] % 4 == 0:
                wage_bill = sum(p['wage'] for p in self.data['squad'])
                self.data['club']['budget'] -= wage_bill
                for p in self.data['squad']:
                    if p['status'] != 'Titular': p['fitness'] = min(100, p['fitness'] + 50)
                    
            await save_career_data(self.ctx.author.id, self.data)
            
            if self.data['club']['confidence'] <= 25 or self.data['club']['budget'] < -5000000:
                await inter.message.edit(content="🚨 **VOCÊ FOI DEMITIDO!** O clube faliu ou a diretoria não aguenta mais você.", embed=None, view=None)
                supabase.table("jogadores").delete().eq("id", f"CAREER_{self.ctx.author.id}").execute()
                return

            for child in self.children:
                child.disabled = False
                
            await inter.message.edit(embed=self.build_dashboard_embed(), view=self)


# --- COMANDOS MODO CARREIRA START ---
@bot.command(name='carreira')
async def carreira_cmd(ctx):
    if GLOBAL_DISABLED: return
    data = await get_career_data(ctx.author.id)
    if not data:
        view = CareerSetupView(ctx)
        emb = discord.Embed(title="🏆 Bem-vindo ao Modo Carreira EFL (Fut7)!", description="Crie o seu perfil de treinador para começar sua jornada gerencial realista no Discord.", color=discord.Color.gold())
        await ctx.send(embed=emb, view=view)
    else:
        view = CareerMainView(ctx, data)
        msg = await ctx.send(embed=view.build_dashboard_embed(), view=view)
        view.message = msg


# =====================================================================
# SISTEMAS ORIGINAIS INTACTOS (MERCADO, CARDS GERAIS)
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
    
    if ovr >= 90: c_top = (70, 15, 90); c_bot = (30, 5, 40)
    elif ovr >= 80: c_top = (184, 134, 11); c_bot = (60, 50, 20)
    elif ovr >= 75: c_top = (192, 192, 192); c_bot = (128, 128, 128)
    else: c_top = (160, 82, 45); c_bot = (60, 30, 15)

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
            offset_x = (spacing // 2) if (y // spacing) % 2 == 0 else 0
            draw_bg.polygon([(x + offset_x, y - 4), (x + offset_x + 4, y), (x + offset_x, y + 4), (x + offset_x - 4, y)], fill=pattern_color)

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
    except Exception: pass

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

    silver_base = (200, 200, 200); silver_shadow = (80, 80, 80); silver_highlight = (240, 240, 240)
    draw_metallic_text(draw, (35, 30), str(ovr), f_ovr, silver_base, silver_shadow, silver_highlight, "la")
    draw_metallic_text(draw, (35, 120), player['position'], f_pos, silver_base, silver_shadow, silver_highlight, "la")

    nome_cru = player['name'].split()[-1].upper()
    max_text_width = c_w - 40; current_font_size = 35
    try:
        while f_name.getlength(nome_cru) > max_text_width and current_font_size > 18:
            current_font_size -= 2; f_name = ImageFont.truetype(FONT_PATH, current_font_size)
    except: pass
        
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
        self.pos = discord.ui.TextInput(label='Posição (PO, ZAG, MEI, ATA...)', placeholder='Ex: MEI', min_length=2, max_length=3)
        self.add_item(self.ovr)
        self.add_item(self.pos)

    async def on_submit(self, inter: discord.Interaction):
        try:
            o_int = int(self.ovr.value)
            p_str = self.pos.value.upper().strip()
            if p_str in POS_MIGRATION: p_str = POS_MIGRATION[p_str]
            coords, mapping = get_formation_config("2-3-1", is_7v7=True) # Posições genericas do Fut7
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
        self.pos = discord.ui.TextInput(label='Nova Posição (ZAG, MEI, PO)', placeholder='Ex: ZAG', min_length=2, max_length=3)
        self.add_item(self.ovr)
        self.add_item(self.pos)
        
    async def on_submit(self, inter: discord.Interaction):
        try:
            o = int(self.ovr.value)
            v = calculate_player_value(o)
            p_str = self.pos.value.upper().strip()
            if p_str in POS_MIGRATION: p_str = POS_MIGRATION[p_str]
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
        self.pos = discord.ui.TextInput(label='Posição (PO, ZAG, MEI, ATA...)', placeholder='Ex: MEI', min_length=2, max_length=3)
        self.add_item(self.ovr)
        self.add_item(self.pos)

    async def on_submit(self, inter: discord.Interaction):
        try:
            o_int = int(self.ovr.value)
            p_str = self.pos.value.upper().strip()
            if p_str in POS_MIGRATION: p_str = POS_MIGRATION[p_str]
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
            if self.view_instance.index >= len(self.view_instance.queue): self.view_instance.index = max(0, len(self.view_instance.queue) - 1)
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

# Simulação de jogo normal (Original mantida intacta)
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
        if inter.user != self.opponent: return await inter.response.send_message("❌ Apenas o desafiado pode aceitar o convite!", ephemeral=True)
        if self.challenger.id in active_matches or self.opponent.id in active_matches: return await inter.response.send_message("❌ Alguém já está jogando!", ephemeral=True)
        await inter.response.defer()
        active_matches.add(self.challenger.id)
        active_matches.add(self.opponent.id)
        for child in self.children: child.disabled = True
        await inter.message.edit(content="⏳ Preparando o gramado da EFL...", view=self)
        await simulate_match_normal(self.ctx, self.challenger, self.opponent, self.d1, self.d2, inter.message)

    @discord.ui.button(label="Recusar", style=discord.ButtonStyle.danger, emoji="✖️")
    async def decline(self, inter: discord.Interaction, btn: discord.ui.Button):
        if inter.user != self.opponent: return await inter.response.send_message("❌ Apenas o desafiado pode recusar o convite!", ephemeral=True)
        for child in self.children: child.disabled = True
        await inter.response.edit_message(content=f"🚫 O desafio foi recusado por {self.opponent.mention}.", view=self)

async def simulate_match_normal(ctx, challenger, opponent, d1, d2, message):
    try:
        f1 = sum(x['overall'] for x in d1['team'] if x)
        f2 = sum(x['overall'] for x in d2['team'] if x)
        diff = f1 - f2
        prob_t1 = max(20, min(80, 50 + diff))
        s1 = 0; s2 = 0; minuto_atual = 0; meio_tempo_feito = False
        event_log = ["🎙️ O juiz apita e a bola está rolando!"]
        emb = discord.Embed(title=f"🏟️ EFL: {challenger.display_name} x {opponent.display_name}", color=discord.Color.blue())
        
        while minuto_atual < 90:
            salto = random.randint(4, 13)
            minuto_atual += salto
            is_intervalo = False
            if minuto_atual >= 45 and not meio_tempo_feito:
                minuto_atual = 45; meio_tempo_feito = True; is_intervalo = True
            elif minuto_atual > 90: minuto_atual = 90
                
            rnd_attack = random.randint(1, 100)
            if rnd_attack <= prob_t1:
                team_attack = challenger.display_name; team_defend = opponent.display_name
                players_attack = [p for p in d1['team'] if p]; players_defend = [p for p in d2['team'] if p]
                atacante_id = 1
            else:
                team_attack = opponent.display_name; team_defend = challenger.display_name
                players_attack = [p for p in d2['team'] if p]; players_defend = [p for p in d1['team'] if p]
                atacante_id = 2

            if is_intervalo: evento_str = f"[{minuto_atual}'] ⏱️ Intervalo na EFL! Fim do primeiro tempo."
            else:
                event_type = random.randint(1, 100)
                try: jogador_ataque = random.choice(players_attack)['name']
                except: jogador_ataque = "Atacante"
                try: goleiro_defesa = next((p['name'] for p in players_defend if p['position'] in ['PO', 'GK', 'GOL']), random.choice(players_defend)['name'])
                except: goleiro_defesa = "Goleiro"
                
                if event_type <= 18:
                    evento_str = f"[{minuto_atual}'] " + random.choice(GOAL_NARRATIONS).format(attacker=jogador_ataque)
                    if atacante_id == 1: s1 += 1
                    else: s2 += 1
                elif event_type <= 40: evento_str = f"[{minuto_atual}'] " + random.choice(SAVE_NARRATIONS).format(keeper=goleiro_defesa, attacker=jogador_ataque)
                elif event_type <= 65: evento_str = f"[{minuto_atual}'] " + random.choice(MISS_NARRATIONS).format(attacker=jogador_ataque)
                elif event_type <= 80: evento_str = f"[{minuto_atual}'] " + random.choice(FOUL_NARRATIONS)
                else: evento_str = f"[{minuto_atual}'] " + random.choice(BUILD_NARRATIONS)

            event_log.append(evento_str)
            if len(event_log) > 6: event_log.pop(0)
            log_text = "\n\n".join(event_log)
            placar = f"## 🔵 {challenger.display_name} {s1} x {s2} {opponent.display_name} 🔴"
            emb.description = f"{placar}\n\n**Lances:**\n```\n{log_text}\n```"
            await message.edit(content="", embed=emb, view=None)
            await asyncio.sleep(3.0)

        if s1 > s2: 
            d1['wins'] += 1; d2['losses'] += 1; res = f"Fim de papo! A vitória é do {challenger.display_name}!"
        elif s2 > s1: 
            d2['wins'] += 1; d1['losses'] += 1; res = f"Fim de papo! O {opponent.display_name} leva a melhor fora de casa!"
        else: res = "Fim de jogo! Empate!"
            
        await save_user_data(challenger.id, d1)
        await save_user_data(opponent.id, d2)
        event_log.append(f"🏁 FIM: {res}")
        if len(event_log) > 7: event_log.pop(0)
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
    except Exception as e: pass

async def get_user_data(user_id):
    uid = str(user_id)
    try:
        res = supabase.table("jogadores").select("data").eq("id", uid).execute()
        if not res.data:
            initial = {
                "money": INITIAL_MONEY, "squad": [], "team": [None]*11, "wins": 0, "losses": 0, "match_history": [], 
                "achievements": [], "contracted_players": [], "club_name": None, "club_sigla": "EFL", 
                "formation": "4-3-3", "captain": None, "last_caixa_use": None, "last_obter_use": None
            }
            supabase.table("jogadores").insert({"id": uid, "data": initial}).execute()
            return initial
            
        data = res.data[0]["data"]
        defaults = [
            ("losses", 0), ("achievements", []), ("match_history", []), ("contracted_players", []), 
            ("club_name", None), ("club_sigla", "EFL"), ("formation", "4-3-3"), ("captain", None), 
            ("last_caixa_use", None), ("last_obter_use", None)
        ]
        
        for key, val in defaults:
            if key not in data: data[key] = val
                
        if "team" not in data or len(data["team"]) != 11:
            old_team = data.get("team", [])
            new_team = [None] * 11
            for idx, p in enumerate(old_team):
                if p and idx < 11: new_team[idx] = p
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
            try: supabase.table("jogadores").update({"data": data}).eq("id", uid).execute()
            except: pass
        return data
    except Exception: return None

# EVENTOS BASE BOT
@bot.event
async def on_ready():
    print(f'🟢 EFL Guru ONLINE! Todas as linhas carregadas e Render ativado.')
    fetch_and_parse_players()
    await bot.change_presence(activity=discord.Game(name=f"{BOT_PREFIX}help | EFL Manager"))

@bot.check
async def global_check(ctx):
    global MAINTENANCE_MODE
    global GLOBAL_DISABLED

    if GLOBAL_DISABLED:
        if ctx.command and ctx.command.name == 'enableall':
            return True
        return False

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

# COMANDOS DE ADMINISTRAÇÃO E ECONOMIA GLOBAL

@bot.command(name='disableall')
@is_bot_admin()
async def disableall_cmd(ctx):
    await ctx.send("⚠️ **ATENÇÃO!** Você está prestes a desativar TODOS os comandos do bot.\nEle continuará online, mas ignorará qualquer interação.\n\nPara confirmar, digite exatamente:\n`DESATIVAR COMANDOS`\n*(Você tem 30 segundos)*")
    
    def check(m): 
        return m.author.id == ctx.author.id and m.channel == ctx.channel
        
    try:
        msg = await bot.wait_for('message', check=check, timeout=30.0)
        
        if msg.content == "DESATIVAR COMANDOS":
            global GLOBAL_DISABLED
            GLOBAL_DISABLED = True
            await ctx.send("🛑 **Recebido.** Todos os comandos foram desativados com sucesso! O bot agora é apenas um fantasma online.\n*(Dica de dev: use `--enableall` para reativar, caso precise)*")
        else: 
            await ctx.send("❌ Confirmação incorreta. O bot continuará funcionando normalmente.")
            
    except asyncio.TimeoutError: 
        await ctx.send("⏳ Tempo esgotado. A desativação foi cancelada.")

@bot.command(name='enableall')
@is_bot_admin()
async def enableall_cmd(ctx):
    global GLOBAL_DISABLED
    GLOBAL_DISABLED = False
    await ctx.send("🟢 **SISTEMA REATIVADO.** O bot voltou à vida e os comandos estão funcionando novamente!")

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

def get_roblox_data_sync(username):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'}
    try:
        res = requests.post("https://users.roblox.com/v1/usernames/users", json={"usernames": [username]}, headers=headers, timeout=10)
        
        if res.status_code == 429: 
            time.sleep(2)
            res = requests.post("https://users.roblox.com/v1/usernames/users", json={"usernames": [username]}, headers=headers, timeout=10)
            
        data = res.json()
        if not data.get("data"): 
            return None
            
        uid = data["data"][0]["id"]
        res2 = requests.get(f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={uid}&size=420x420&format=Png&isCircular=false", headers=headers, timeout=10)
        data2 = res2.json()
        
        if data2.get("data") and data2["data"][0].get("imageUrl"): 
            return data2["data"][0]["imageUrl"]
            
        return None
    except Exception as e: 
        return None

@bot.command(name='analyzemembers')
@is_bot_admin()
async def analyze_members_cmd(ctx):
    target_role_id = 1470883144528822420
    role = ctx.guild.get_role(target_role_id)
    
    if not role: 
        return await ctx.send("❌ Cargo alvo não encontrado no servidor.")
        
    msg = await ctx.send("⏳ **Iniciando varredura de membros...**")
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
        return await msg.edit(content="❌ **Varredura Concluída:** Nenhum membro novo apto encontrado.")
        
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
@is_bot_admin()
async def sync_cmd(ctx):
    fetch_and_parse_players()
    await ctx.send(f"✅ Memória RAM sincronizada! **{len(ALL_PLAYERS)}** cartas prontas.")

@bot.command(name='addmoney')
@is_bot_admin()
async def addmoney_cmd(ctx, target: discord.User, amount: int):
    if amount <= 0: 
        return await ctx.send("❌ O valor deve ser positivo.")
        
    async with data_lock:
        u_data = await get_user_data(target.id)
        u_data['money'] += amount
        await save_user_data(target.id, u_data)
        
    await ctx.send(f"✅ **ADMIN:** Adicionado R$ {amount:,} à conta de {target.mention}.\nNovo saldo: R$ {u_data['money']:,}")

@bot.command(name='removemoney')
@is_bot_admin()
async def removemoney_cmd(ctx, target: discord.User, amount: int):
    if amount <= 0: 
        return await ctx.send("❌ O valor deve ser positivo.")
        
    async with data_lock:
        u_data = await get_user_data(target.id)
        u_data['money'] = max(0, u_data['money'] - amount)
        await save_user_data(target.id, u_data)
        
    await ctx.send(f"✅ **ADMIN:** Removido R$ {amount:,} da conta de {target.mention}.\nNovo saldo: R$ {u_data['money']:,}")


# --- COMANDOS MODO NORMAL / CAIXAS ---
@bot.command(name='caixa')
async def caixa_cmd(ctx):
    async with data_lock:
        u = await get_user_data(ctx.author.id)
        last_use_str = u.get('last_caixa_use')
        now = datetime.utcnow()
        cooldown_seconds = 43200 
        
        if last_use_str:
            last_use = datetime.fromisoformat(last_use_str)
            time_passed = (now - last_use).total_seconds()
            
            if time_passed < cooldown_seconds:
                remaining = cooldown_seconds - time_passed
                horas = int(remaining // 3600)
                minutos = int((remaining % 3600) // 60)
                segundos = int(remaining % 60)
                return await ctx.send(f"⏳ **Calma aí, chefinho!** A caixa diária ainda está fechada.\n\nTente novamente em **{horas}h {minutos}m {segundos}s**.")
                
        u['last_caixa_use'] = now.isoformat()
        await save_user_data(ctx.author.id, u)

    boxes = ["Bronze", "Iron", "Gold", "Diamond", "Master"]
    weights = [60, 25, 10, 4, 1] 
    chosen_box = random.choices(boxes, weights=weights, k=1)[0]
    
    async with data_lock:
        u = await get_user_data(ctx.author.id)
        livres = [p for p in ALL_PLAYERS if p["name"] not in u["contracted_players"]]
        
        def get_player_by_ovr(min_o, max_o):
            pool = [p for p in livres if min_o <= p.get('overall', 70) <= max_o]
            if pool: 
                return random.choice(pool)
            return None
            
        money_won = 0
        player_won = None
        
        if chosen_box == "Bronze": 
            money_won = random.randint(50000, 150000)
            emoji = "🥉"
        elif chosen_box == "Iron":
            money_won = random.randint(100000, 300000)
            emoji = "⚙️"
            if random.random() < 0.10: 
                player_won = get_player_by_ovr(70, 74)
        elif chosen_box == "Gold":
            money_won = random.randint(200000, 500000)
            emoji = "🥇"
            chance = random.random()
            if chance < 0.05: 
                player_won = get_player_by_ovr(80, 84) 
            elif chance < 0.35: 
                player_won = get_player_by_ovr(75, 79)
        elif chosen_box == "Diamond":
            money_won = random.randint(500000, 1000000)
            emoji = "💎"
            chance = random.random()
            if chance < 0.02: 
                player_won = get_player_by_ovr(90, 99) 
            elif chance < 0.20: 
                player_won = get_player_by_ovr(85, 89) 
            else: 
                player_won = get_player_by_ovr(80, 84) 
        elif chosen_box == "Master":
            money_won = random.randint(1000000, 2000000)
            emoji = "🏆"
            chance = random.random()
            if chance < 0.30: 
                player_won = get_player_by_ovr(90, 99) 
            else: 
                player_won = get_player_by_ovr(85, 89)
            
        u['money'] += money_won
        desc = f"Você abriu uma **{emoji} {chosen_box} Box**!\n\n💵 **Dinheiro:** R$ {money_won:,}"
        file_to_send = None
        
        if player_won:
            u['squad'].append(player_won)
            u['contracted_players'].append(player_won['name'])
            desc += f"\n\n👤 **Jogador Encontrado:** {player_won['name']} (⭐ {player_won['overall']})\n*O jogador foi adicionado diretamente ao seu elenco!*"
            
            async with image_lock:
                buf = await asyncio.to_thread(render_single_card_sync, player_won)
                file_to_send = discord.File(buf, "card.png")
                
        await save_user_data(ctx.author.id, u)
        
    emb = discord.Embed(title="🎁 Recompensa Diária (12h)", description=desc, color=discord.Color.gold())
    
    if file_to_send: 
        emb.set_image(url="attachment://card.png")
        await ctx.send(embed=emb, file=file_to_send)
    else: 
        await ctx.send(embed=emb)

@bot.command(name='jogadores')
async def jogadores_cmd(ctx):
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

@bot.command(name='obter')
async def obter_cmd(ctx):
    async with data_lock:
        u = await get_user_data(ctx.author.id)
        last_use_str = u.get('last_obter_use')
        now = datetime.utcnow()
        cooldown_seconds = 600
        
        if last_use_str:
            last_use = datetime.fromisoformat(last_use_str)
            time_passed = (now - last_use).total_seconds()
            
            if time_passed < cooldown_seconds:
                remaining = cooldown_seconds - time_passed
                minutos = int((remaining % 3600) // 60)
                segundos = int(remaining % 60)
                return await ctx.send(f"⏳ **Calma aí, chefinho!** O olheiro está descansando.\n\nTente novamente em **{minutos}m {segundos}s**.")
                
        u['last_obter_use'] = now.isoformat()
        await save_user_data(ctx.author.id, u)

    async with data_lock:
        u = await get_user_data(ctx.author.id)
        livres = [p for p in ALL_PLAYERS if p["name"] not in u["contracted_players"]]
        
        if not livres: 
            u['last_obter_use'] = None
            await save_user_data(ctx.author.id, u)
            return await ctx.send("❌ Mercado vazio! (Seu tempo de recarga não foi gasto).")
        
        pesos = []
        for p in livres:
            ovr = p.get('overall', 70)
            if ovr >= 90: pesos.append(2)       
            elif ovr >= 85: pesos.append(8)    
            elif ovr >= 80: pesos.append(20)    
            elif ovr >= 75: pesos.append(60)    
            else: pesos.append(10)              
            
        p = random.choices(livres, weights=pesos, k=1)[0]
        
        async with image_lock: 
            buf = await asyncio.to_thread(render_single_card_sync, p)
        
    raridade = "🥉 Bronze"
    if p.get('overall', 70) >= 90: 
        raridade = "✨ LENDÁRIO"
    elif p.get('overall', 70) >= 80: 
        raridade = "🥇 Ouro"
    elif p.get('overall', 70) >= 75: 
        raridade = "🥈 Prata"
    
    view = KeepOrSellView(ctx.author, p)
    msg = await ctx.send(content=f"🃏 **OLHEIRO DA EFL:** Você encontrou um talento **{raridade}** solto pelo mundo!\n*(Você tem 60 segundos para escolher ou ele irá para o seu elenco automaticamente)*", file=discord.File(buf, "card.png"), view=view)
    view.message = msg

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
    if ctx.author == target or amount <= 0: 
        return
        
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
        return await ctx.send("❌ Seu elenco está vazio. Digite `--obter`, `--caixa` ou `--contratar` para buscar atletas.")
        
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
    users = sorted([x for x in res.data if not x['id'].startswith("CAREER_") and x['id'] != "ROBLOX_CARDS"], key=lambda u: u["data"].get("wins", 0), reverse=True)[:10]
    txt = "\n".join([f"**{i+1}.** <@{u['id']}> — `{u['data'].get('wins',0)}` Vitórias" for i, u in enumerate(users)])
    
    await ctx.send(embed=discord.Embed(title="🏆 Ranking Oficial EFL", description=txt or "Ainda não houve partidas registradas.", color=discord.Color.gold()))

@bot.command(name='help')
async def help_cmd(ctx):
    emb = discord.Embed(title="📜 Painel de Ajuda EFL Pro", description="Seja bem-vindo ao mercado EFL Pro! Abaixo estão os comandos disponíveis:", color=discord.Color.gold())
    emb.add_field(name="💼 Modo Carreira Técnico (NOVO)", value="`--carreira`", inline=False)
    emb.add_field(name="💰 Gestão Ultimate Team", value="`--caixa`, `--cofre`, `--donate`, `--contratar`, `--sell`, `--obter`, `--jogadores`", inline=False)
    emb.add_field(name="📋 Vestiário & Tática", value="`--setclube`, `--elenco`, `--escalar`, `--banco`, `--team` ", inline=False)
    emb.add_field(name="⚽ Partidas", value="`--confrontar`, `--ranking` ")
    emb.add_field(name="⚙️ Administração", value="`--addplayer`, `--bulkadd`, `--editplayer`, `--delplayer`, `--lock`, `--unlock`, `--disableall`, `--enableall`, `--addmoney`, `--removemoney` ", inline=False)
    emb.set_footer(text="Versão 47.0 - Desenvolvido exclusivamente para a EFL")
    
    await ctx.send(embed=emb)

# --- INICIALIZAÇÃO ---
if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    
    if token: 
        try:
            keep_alive()
            bot.run(token.strip()) 
        except discord.errors.PrivilegedIntentsRequired:
            print("❌ ERRO FATAL: Intents não ativados! Vá no Discord Developer Portal e ative: Presence, Server Members e Message Content.")
        except discord.errors.LoginFailure:
            print("❌ ERRO FATAL: O Token do Discord é inválido. Verifique se copiou certo na Render.")
        except Exception as e:
            print(f"❌ ERRO CRÍTICO DESCONHECIDO NO STARTUP: {e}")
    else: 
        print("❌ ERRO FATAL: Variável DISCORD_TOKEN não encontrada na Render.")
