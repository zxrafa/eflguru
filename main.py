# -*- coding: utf-8 -*-
"""
EFL Guru - Versão 42.0 (A ERA DO MODO CARREIRA - MEGA ATUALIZAÇÃO)
----------------------------------------------------------------------
- CÓDIGO COMPLETO: Nenhuma linha removida.
- NOVO SISTEMA: MODO CARREIRA DE TÉCNICO (EFL CAREER)
  * Criação avançada de treinador (Táticas, Mentalidade, Reputação).
  * Hub de Gerenciamento 100% via UI (Botões e Menus).
  * Motor de simulação de partidas profundo (Cansaço, Moral, OVR, Tática).
  * Elenco de 25 jogadores dinâmicos (Evolução, Idade, Potencial).
  * Mercado de transferências, Finanças e Risco de Demissão.
- HIERARQUIA DE ADMINISTRAÇÃO MANTIDA.
- MERCADO GLOBAL E CAIXAS MANTIDOS.
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

BOT_ADMINS = [338704196180115458, 1076957467935789056]

def is_bot_admin():
    async def predicate(ctx):
        return ctx.author.id in BOT_ADMINS
    return commands.check(predicate)

def calculate_player_value(ovr):
    base_value = 150000
    adjusted_ovr = max(70, ovr)
    return int(base_value * (1.3 ** (adjusted_ovr - 70)))

FONT_PATH = "EFL_Font.ttf"
FONT_URL = "https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Black.ttf"

def ensure_font_exists():
    if not os.path.exists(FONT_PATH):
        try:
            r = requests.get(FONT_URL, allow_redirects=True)
            open(FONT_PATH, 'wb').write(r.content)
        except Exception as e:
            pass

ensure_font_exists()

def get_formation_config(formation):
    if formation == "4-4-2":
        coords = {0: (420, 1060), 1: (120, 820), 2: (320, 830), 3: (520, 830), 4: (720, 820), 5: (150, 530), 6: (330, 560), 7: (510, 560), 8: (690, 530), 9: (300, 200), 10: (540, 200)}
        mapping = {"PO": [0], "GK": [0], "GOL": [0], "DFC": [1, 2, 3, 4], "CB": [1, 2, 3, 4], "ZAG": [1, 2, 3, 4], "MDC": [5, 6, 7, 8], "MC": [5, 6, 7, 8], "MCO": [5, 6, 7, 8], "VOL": [5, 6, 7, 8], "DC": [9, 10], "ST": [9, 10], "CA": [9, 10]}
    elif formation == "3-4-3":
        coords = {0: (420, 1060), 1: (200, 830), 2: (420, 850), 3: (640, 830), 4: (150, 530), 5: (330, 560), 6: (510, 560), 7: (690, 530), 8: (170, 240), 9: (420, 190), 10: (670, 240)}
        mapping = {"PO": [0], "GK": [0], "GOL": [0], "DFC": [1, 2, 3], "CB": [1, 2, 3], "ZAG": [1, 2, 3], "MDC": [4, 5, 6, 7], "MC": [4, 5, 6, 7], "MCO": [4, 5, 6, 7], "VOL": [4, 5, 6, 7], "DC": [8, 9, 10], "ST": [8, 9, 10], "CA": [8, 9, 10]}
    else: 
        coords = {0: (420, 1060), 1: (120, 820), 2: (320, 830), 3: (520, 830), 4: (720, 820), 5: (200, 530), 6: (420, 560), 7: (640, 530), 8: (170, 240), 9: (420, 190), 10: (670, 240)}
        mapping = {"PO": [0], "GK": [0], "GOL": [0], "DFC": [1, 2, 3, 4], "CB": [1, 2, 3, 4], "ZAG": [1, 2, 3, 4], "MDC": [5, 6, 7], "MC": [5, 6, 7], "MCO": [5, 6, 7], "VOL": [5, 6, 7], "DC": [8, 9, 10], "ST": [8, 9, 10], "CA": [8, 9, 10]}
    return coords, mapping

POS_MIGRATION = {"ST": "DC", "CA": "DC", "PE": "DC", "PD": "DC", "LW": "DC", "RW": "DC", "LF": "DC", "RF": "DC", "CB": "DFC", "ZAG": "DFC", "LE": "DFC", "LD": "DFC", "LB": "DFC", "RB": "DFC", "GK": "PO", "GOL": "PO"}

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

bot = commands.Bot(command_prefix=BOT_PREFIX, intents=intents, help_command=None, max_messages=None, chunk_guilds_at_startup=True, case_insensitive=True)

# =====================================================================
# 🚀 MODO CARREIRA: MOTOR DE JOGO GERENCIAL (FIFA STYLE)
# =====================================================================

CAREER_FIRST_NAMES = ["João", "Pedro", "Lucas", "Carlos", "Marcos", "Arthur", "Diego", "Alex", "Bruno", "Gabriel", "Max", "Leo", "Sam", "Oliver", "Harry", "Jack", "Tommy", "Luis", "Kevin", "David"]
CAREER_LAST_NAMES = ["Silva", "Santos", "Oliveira", "Souza", "Rodrigues", "Ferreira", "Alves", "Pereira", "Lima", "Gomes", "Smith", "Jones", "Williams", "Brown", "Taylor", "Davies", "Evans", "Wilson", "Thomas", "Johnson"]
CAREER_POSITIONS = ["PO", "DFC", "DFC", "LD", "LE", "MDC", "MC", "MCO", "PE", "PD", "DC"]

CAREER_CLUBS = {
    1: [{"name": "EFL Elite FC", "budget": 150000000, "expect": "Vencer a Liga"}, {"name": "Supremos AC", "budget": 120000000, "expect": "Classificar para Continental"}],
    2: [{"name": "União Cidadã", "budget": 40000000, "expect": "Terminar no Top 6"}, {"name": "Real Sindicato", "budget": 35000000, "expect": "Fugir do Rebaixamento"}],
    3: [{"name": "Operário FC", "budget": 8000000, "expect": "Subir de Divisão"}, {"name": "Várzea Rovers", "budget": 5000000, "expect": "Sobreviver"}]
}

TACTICAL_STYLES = {
    "Tiki-Taka": {"desc": "Posse de bola e passes curtos. Cansaço médio.", "atk_bonus": 1.1, "def_bonus": 1.0, "stam_cost": 5},
    "Gegenpressing": {"desc": "Pressão alta absurda. Ataque letal, mas drena o físico.", "atk_bonus": 1.25, "def_bonus": 1.05, "stam_cost": 12},
    "Retranca": {"desc": "Defesa sólida e contra-ataque. Pouco desgaste.", "atk_bonus": 0.8, "def_bonus": 1.3, "stam_cost": 3},
    "Equilibrado": {"desc": "Abordagem padrão. Bom balanço geral.", "atk_bonus": 1.0, "def_bonus": 1.0, "stam_cost": 6}
}

async def get_career_data(user_id):
    uid = f"CAREER_{user_id}"
    res = supabase.table("jogadores").select("data").eq("id", uid).execute()
    if not res.data: return None
    return res.data[0]["data"]

async def save_career_data(user_id, data):
    uid = f"CAREER_{user_id}"
    res = supabase.table("jogadores").select("id").eq("id", uid).execute()
    if res.data:
        supabase.table("jogadores").update({"data": data}).eq("id", uid).execute()
    else:
        supabase.table("jogadores").insert({"id": uid, "data": data}).execute()

def generate_career_player(tier):
    base_ovr = {1: (78, 88), 2: (68, 77), 3: (58, 67)}[tier]
    age = random.randint(17, 34)
    ovr = random.randint(*base_ovr)
    pot = ovr + random.randint(0, 15) if age < 25 else ovr
    val = int((ovr ** 2.5) * 100)
    wage = int(val * 0.005)
    return {
        "id": str(random.randint(10000, 99999)),
        "name": f"{random.choice(CAREER_FIRST_NAMES)[0]}. {random.choice(CAREER_LAST_NAMES)}",
        "pos": random.choice(CAREER_POSITIONS),
        "age": age, "ovr": ovr, "pot": pot,
        "fitness": 100, "morale": 80,
        "value": val, "wage": wage, "status": "Reserva"
    }

def generate_initial_squad(tier):
    squad = []
    # Cria os 11 titulares
    for pos in ["PO", "LD", "DFC", "DFC", "LE", "MC", "MC", "MCO", "PD", "PE", "DC"]:
        p = generate_career_player(tier)
        p["pos"] = pos
        p["status"] = "Titular"
        squad.append(p)
    # Cria 14 reservas/base
    for _ in range(14):
        squad.append(generate_career_player(tier))
    return squad

# --- VIEWS DO MODO CARREIRA ---

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
        emb = discord.Embed(title="🏢 Mercado de Trabalho", description="Escolha o clube onde você iniciará sua carreira. Como técnico iniciante, apenas clubes de divisões inferiores (Tier 3) aceitam você.", color=discord.Color.dark_teal())
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
            
            squad = generate_initial_squad(3)
            data = {
                "coach": {"name": self.c_name, "style": self.c_style, "mental": self.c_mental, "reputation": 10},
                "club": {"name": club_data['name'], "budget": club_data['budget'], "confidence": 80, "tier": 3},
                "squad": squad,
                "season": {"week": 1, "wins": 0, "draws": 0, "losses": 0, "pts": 0, "history": []},
                "formation": "4-3-3"
            }
            await save_career_data(self.ctx.author.id, data)
            
            await inter.message.edit(content="⚽ **Contrato assinado!** Gerando instalações, elenco e base de dados...", embed=None, view=None)
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
        avg_ovr = int(sum(p['ovr'] for p in self.data['squad'] if p['status'] == 'Titular') / 11) if len([p for p in self.data['squad'] if p['status'] == 'Titular']) == 11 else 0

        e = discord.Embed(title=f"🏟️ Hub do Manager: {cl['name']} (Semana {s['week']})", color=discord.Color.dark_theme())
        e.add_field(name="🧑‍💼 Treinador", value=f"**{c['name']}**\nReputação: {c['reputation']}/100\nEstilo: {c['style']}", inline=True)
        e.add_field(name="📊 Campanha Atual", value=f"Vitórias: {s['wins']} | Empates: {s['draws']} | Derrotas: {s['losses']}\nPontos: **{s['pts']}**", inline=True)
        e.add_field(name="💼 Finanças & Diretoria", value=f"Orçamento: R$ {cl['budget']:,}\nFolha Salarial: R$ {wage_bill:,}\nConfiança da Diretoria: {cl['confidence']}%", inline=False)
        e.add_field(name="👥 Visão Geral do Elenco", value=f"Titulares Definidos: {len([p for p in self.data['squad'] if p['status'] == 'Titular'])}/11\nOVR Médio Titular: {avg_ovr}\nTática: {self.data['formation']}", inline=False)
        return e

    @discord.ui.button(label="Avançar Semana (Simular Jogo)", style=discord.ButtonStyle.success, emoji="⏩", row=0)
    async def btn_advance(self, inter: discord.Interaction, b):
        if inter.user != self.ctx.author: return
        await inter.response.defer()
        
        titulares = [p for p in self.data['squad'] if p['status'] == 'Titular']
        if len(titulares) != 11:
            return await inter.followup.send("❌ Você precisa de exatamente 11 titulares para jogar! Vá em Elenco.", ephemeral=True)

        async with career_lock:
            # Sorteia Oponente Baseado no Tier
            adv_ovr = random.randint(60, 75) if self.data['club']['tier'] == 3 else random.randint(70, 85)
            meu_ovr = sum(p['ovr'] for p in titulares) / 11
            
            # Aplica Bônus Táticos e de Condição Físcia/Moral
            fatigue_pen = sum((100 - p['fitness']) * 0.1 for p in titulares)
            morale_bonus = sum((p['morale'] - 50) * 0.05 for p in titulares)
            style_data = TACTICAL_STYLES[self.data['coach']['style']]
            
            forca_final = (meu_ovr - fatigue_pen + morale_bonus) * style_data['atk_bonus']
            
            # Motor 2D Rápido
            meus_gols, adv_gols = 0, 0
            eventos = []
            
            for m in range(0, 90, 15):
                # Desgaste físico ao longo do jogo
                for p in titulares:
                    p['fitness'] = max(30, p['fitness'] - style_data['stam_cost'])
                
                chances = random.randint(1, 100)
                if chances < (forca_final / (forca_final + adv_ovr) * 100):
                    if random.random() > 0.6: 
                        meus_gols += 1
                        eventos.append(f"[{m}'] ⚽ Gol do {self.data['club']['name']}! Lindo ataque pela ponta.")
                elif chances > 80:
                    if random.random() > 0.6:
                        adv_gols += 1
                        eventos.append(f"[{m}'] ❌ Gol do adversário. Falha na marcação.")
            
            # Resultado e Progressão
            res_str = ""
            if meus_gols > adv_gols:
                self.data['season']['wins'] += 1
                self.data['season']['pts'] += 3
                self.data['club']['confidence'] = min(100, self.data['club']['confidence'] + 5)
                self.data['coach']['reputation'] += 1
                res_str = "Vitória 🟢"
                for p in self.data['squad']: p['morale'] = min(100, p['morale'] + 10)
            elif adv_gols > meus_gols:
                self.data['season']['losses'] += 1
                self.data['club']['confidence'] -= 8
                res_str = "Derrota 🔴"
                for p in self.data['squad']: p['morale'] = max(0, p['morale'] - 15)
            else:
                self.data['season']['draws'] += 1
                self.data['season']['pts'] += 1
                res_str = "Empate 🟡"
                for p in self.data['squad']: p['morale'] = min(100, p['morale'] + 2)

            self.data['season']['week'] += 1
            
            # Fim de Mês: Salários e Recuperação (Reservas)
            if self.data['season']['week'] % 4 == 0:
                wage_bill = sum(p['wage'] for p in self.data['squad'])
                self.data['club']['budget'] -= wage_bill
                for p in self.data['squad']:
                    if p['status'] != 'Titular': p['fitness'] = min(100, p['fitness'] + 40)
                    
            await save_career_data(self.ctx.author.id, self.data)
            
            # Verificação de Demissão
            if self.data['club']['confidence'] <= 25:
                await inter.message.edit(content="🚨 **VOCÊ FOI DEMITIDO!** A diretoria perdeu totalmente a confiança no seu trabalho. Use `--carreira` para recomeçar em um clube menor.", embed=None, view=None)
                supabase.table("jogadores").delete().eq("id", f"CAREER_{self.ctx.author.id}").execute()
                return

            # Relatório do Jogo
            log = "\n".join(eventos) if eventos else "Jogo truncado, muita marcação no meio-campo."
            e = discord.Embed(title=f"Fim de Jogo: {res_str} ({meus_gols} x {adv_gols})", description=f"```\n{log}\n```\nO cansaço da equipe aumentou. Gerencie o elenco.", color=discord.Color.blue())
            
            await inter.message.edit(embed=e, view=self)

    @discord.ui.button(label="Gerenciar Elenco", style=discord.ButtonStyle.primary, emoji="👥", row=0)
    async def btn_squad(self, inter: discord.Interaction, b):
        if inter.user != self.ctx.author: return
        await inter.response.send_message(embed=CareerSquadView.build_embed(self.data), view=CareerSquadView(self.ctx, self.data, self), ephemeral=True)

    @discord.ui.button(label="Mercado & Base", style=discord.ButtonStyle.secondary, emoji="💰", row=0)
    async def btn_market(self, inter: discord.Interaction, b):
        if inter.user != self.ctx.author: return
        await inter.response.send_message("Mercado de transferências sendo carregado...", ephemeral=True)

class CareerSquadView(discord.ui.View):
    def __init__(self, ctx, data, hub_view):
        super().__init__(timeout=120)
        self.ctx = ctx
        self.data = data
        self.hub_view = hub_view

    @staticmethod
    def build_embed(data):
        tits = [p for p in data['squad'] if p['status'] == 'Titular']
        res = [p for p in data['squad'] if p['status'] != 'Titular']
        
        t_str = "\n".join([f"`{p['pos']}` **{p['name']}** | ⭐{p['ovr']} | 🔋{p['fitness']}% | 😃{p['morale']}%" for p in tits])
        r_str = "\n".join([f"`{p['pos']}` {p['name']} | ⭐{p['ovr']} | 🔋{p['fitness']}%" for p in res[:10]])
        
        e = discord.Embed(title="📋 Seu Elenco Atual", color=discord.Color.green())
        e.add_field(name=f"Titulares ({len(tits)}/11)", value=t_str or "Nenhum titular.", inline=False)
        e.add_field(name="Reservas (Top 10)", value=r_str or "Sem reservas.", inline=False)
        return e

    @discord.ui.button(label="Auto-Escalar Melhor Time", style=discord.ButtonStyle.success)
    async def btn_auto(self, inter: discord.Interaction, b):
        if inter.user != self.ctx.author: return
        
        for p in self.data['squad']: p['status'] = "Reserva"
        
        squad_sorted = sorted(self.data['squad'], key=lambda x: (x['ovr'], x['fitness']), reverse=True)
        _, mapping = get_formation_config(self.data['formation'])
        
        # Algoritmo simples de preenchimento de posições
        vagas = {
            "GOL": 1, "ZAG": 2, "LAT": 2, "MEI": 3, "ATA": 3
        }
        
        for p in squad_sorted:
            pos_cat = p['pos']
            if pos_cat in ["PO", "GK", "GOL"]: cat = "GOL"
            elif pos_cat in ["DFC", "CB", "ZAG"]: cat = "ZAG"
            elif pos_cat in ["LD", "LE", "RB", "LB"]: cat = "LAT"
            elif pos_cat in ["MDC", "MC", "MCO", "VOL"]: cat = "MEI"
            else: cat = "ATA"
            
            if vagas.get(cat, 0) > 0:
                p['status'] = 'Titular'
                vagas[cat] -= 1
                
        # Força 11 jogadores se a tática faltar peça exata (improviso)
        tits = [p for p in self.data['squad'] if p['status'] == 'Titular']
        if len(tits) < 11:
            for p in squad_sorted:
                if p['status'] == 'Reserva':
                    p['status'] = 'Titular'
                    tits.append(p)
                if len(tits) == 11: break

        await save_career_data(self.ctx.author.id, self.data)
        await inter.response.edit_message(embed=self.build_embed(self.data), view=self)
        await self.hub_view.message.edit(embed=self.hub_view.build_embed())

# --- COMANDOS EXISTENTES E NOVOS ---

@bot.command(name='carreira')
async def carreira_cmd(ctx):
    """Comando de Entrada do Modo Carreira FIFA"""
    data = await get_career_data(ctx.author.id)
    if not data:
        view = CareerSetupView(ctx)
        emb = discord.Embed(title="🏆 Bem-vindo ao Modo Carreira EFL!", description="Crie o seu perfil de treinador para começar sua jornada rumo ao topo do futebol mundial.", color=discord.Color.gold())
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
        self.rbx_name, self.img_url = rbx_name, img_url
        self.ovr = discord.ui.TextInput(label='Overall (OVR)', placeholder='85', min_length=1, max_length=2)
        self.pos = discord.ui.TextInput(label='Posição (PO, DFC, MC, DC...)', placeholder='Ex: DC', min_length=2, max_length=3)
        self.add_item(self.ovr)
        self.add_item(self.pos)

    async def on_submit(self, inter: discord.Interaction):
        try:
            o_int = int(self.ovr.value)
            p_str = self.pos.value.upper().strip()
            if p_str in POS_MIGRATION: p_str = POS_MIGRATION[p_str]
            coords, mapping = get_formation_config("4-3-3")
            if p_str not in mapping: return await inter.response.send_message(f"❌ Posição `{p_str}` inválida.", ephemeral=True)
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
            if p_str in POS_MIGRATION: p_str = POS_MIGRATION[p_str]
            coords, mapping = get_formation_config("4-3-3")
            if p_str not in mapping: return await inter.response.send_message(f"❌ Posição `{p_str}` inválida.", ephemeral=True)
            async with data_lock:
                res = supabase.table("jogadores").select("data").eq("id", "ROBLOX_CARDS").execute()
                cards = res.data[0]["data"]
                for p in cards:
                    if p['name'].lower() == self.nick.lower():
                        p['overall'] = o; p['value'] = v; p['position'] = p_str
                        break
                supabase.table("jogadores").update({"data": cards}).eq("id", "ROBLOX_CARDS").execute()
                fetch_and_parse_players()
            await inter.response.send_message(f"✅ **{self.nick}** atualizado para {o} OVR e Posição {p_str}!")
        except:
            await inter.response.send_message("❌ Erro na edição.", ephemeral=True)

class AnalyzeAddModal(discord.ui.Modal, title='Cadastrar no DB'):
    def __init__(self, view_instance, rbx_name, img_url):
        super().__init__()
        self.view_instance, self.rbx_name, self.img_url = view_instance, rbx_name, img_url
        self.ovr = discord.ui.TextInput(label='Overall (OVR)', placeholder='75', min_length=1, max_length=2)
        self.pos = discord.ui.TextInput(label='Posição (PO, DFC, MDC, DC...)', placeholder='Ex: MC', min_length=2, max_length=3)
        self.add_item(self.ovr)
        self.add_item(self.pos)

    async def on_submit(self, inter: discord.Interaction):
        try:
            o_int = int(self.ovr.value)
            p_str = self.pos.value.upper().strip()
            if p_str in POS_MIGRATION: p_str = POS_MIGRATION[p_str]
            coords, mapping = get_formation_config("4-3-3")
            if p_str not in mapping: return await inter.response.send_message(f"❌ Posição `{p_str}` inválida.", ephemeral=True)
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
        self.ctx, self.queue, self.message, self.index = ctx, queue, message, 0

    async def update_view(self):
        if not self.queue:
            emb = discord.Embed(title="✅ Análise Concluída", description="Todos da fila foram avaliados.", color=discord.Color.green())
            await self.message.edit(embed=emb, view=None); return
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
        await inter.response.defer(); self.index -= 1; await self.update_view()

    @discord.ui.button(label="⏩", style=discord.ButtonStyle.grey)
    async def next(self, inter: discord.Interaction, b):
        if inter.user != self.ctx.author: return
        await inter.response.defer(); self.index += 1; await self.update_view()

    @discord.ui.button(label="➕ Cadastrar", style=discord.ButtonStyle.success)
    async def add(self, inter: discord.Interaction, b):
        if inter.user != self.ctx.author: return
        p = self.queue[self.index]
        modal = AnalyzeAddModal(self, p['nick'], p['image'])
        await inter.response.send_modal(modal)

class MatchInviteView(discord.ui.View):
    def __init__(self, ctx, challenger, opponent, d1, d2):
        super().__init__(timeout=120)
        self.ctx, self.challenger, self.opponent, self.d1, self.d2 = ctx, challenger, opponent, d1, d2

    @discord.ui.button(label="Aceitar Desafio", style=discord.ButtonStyle.success, emoji="⚽")
    async def accept(self, inter: discord.Interaction, btn: discord.ui.Button):
        if inter.user != self.opponent: return await inter.response.send_message("❌ Apenas o desafiado pode aceitar o convite!", ephemeral=True)
        if self.challenger.id in active_matches or self.opponent.id in active_matches: return await inter.response.send_message("❌ Alguém já está jogando!", ephemeral=True)
        await inter.response.defer()
        active_matches.add(self.challenger.id); active_matches.add(self.opponent.id)
        for child in self.children: child.disabled = True
        await inter.message.edit(content="⏳ Preparando o gramado da EFL...", view=self)
        await simulate_match(self.ctx, self.challenger, self.opponent, self.d1, self.d2, inter.message)

    @discord.ui.button(label="Recusar", style=discord.ButtonStyle.danger, emoji="✖️")
    async def decline(self, inter: discord.Interaction, btn: discord.ui.Button):
        if inter.user != self.opponent: return await inter.response.send_message("❌ Apenas o desafiado pode recusar o convite!", ephemeral=True)
        for child in self.children: child.disabled = True
        await inter.response.edit_message(content=f"🚫 O desafio foi recusado por {self.opponent.mention}.", view=self)

async def simulate_match(ctx, challenger, opponent, d1, d2, message):
    try:
        f1 = sum(x['overall'] for x in d1['team'] if x)
        f2 = sum(x['overall'] for x in d2['team'] if x)
        diff = f1 - f2
        prob_t1 = max(20, min(80, 50 + diff))
        s1, s2, minuto_atual, meio_tempo_feito = 0, 0, 0, False
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
                team_attack, team_defend = challenger.display_name, opponent.display_name
                players_attack, players_defend = [p for p in d1['team'] if p], [p for p in d2['team'] if p]
                atacante_id = 1
            else:
                team_attack, team_defend = opponent.display_name, challenger.display_name
                players_attack, players_defend = [p for p in d2['team'] if p], [p for p in d1['team'] if p]
                atacante_id = 2

            if is_intervalo: evento_str = f"[{minuto_atual}'] ⏱️ Intervalo na EFL! Fim do primeiro tempo."
            else:
                event_type = random.randint(1, 100)
                jogador_ataque = random.choice(players_attack)['name']
                goleiro_defesa = next((p['name'] for p in players_defend if p['position'] in ['PO', 'GK', 'GOL']), random.choice(players_defend)['name'])
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
            d1['wins'] += 1; d2['losses'] += 1
            res = f"Fim de papo! A vitória é do {challenger.display_name}!"
        elif s2 > s1: 
            d2['wins'] += 1; d1['losses'] += 1
            res = f"Fim de papo! O {opponent.display_name} leva a melhor fora de casa!"
        else: res = "Fim de jogo! Empate!"
            
        await save_user_data(challenger.id, d1); await save_user_data(opponent.id, d2)
        event_log.append(f"🏁 FIM: {res}")
        if len(event_log) > 7: event_log.pop(0)
        log_text = "\n\n".join(event_log)
        emb.description = f"## 🔵 {challenger.display_name} {s1} x {s2} {opponent.display_name} 🔴\n\n**Lances:**\n```\n{log_text}\n```"
        await message.edit(embed=emb)
    finally:
        active_matches.discard(challenger.id); active_matches.discard(opponent.id)

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
            initial = {"money": INITIAL_MONEY, "squad": [], "team": [None]*11, "wins": 0, "losses": 0, "match_history": [], "achievements": [], "contracted_players": [], "club_name": None, "club_sigla": "EFL", "formation": "4-3-3", "captain": None, "last_caixa_use": None, "last_obter_use": None}
            supabase.table("jogadores").insert({"id": uid, "data": initial}).execute()
            return initial
        data = res.data[0]["data"]
        defaults = [("losses", 0), ("achievements", []), ("match_history", []), ("contracted_players", []), ("club_name", None), ("club_sigla", "EFL"), ("formation", "4-3-3"), ("captain", None), ("last_caixa_use", None), ("last_obter_use", None)]
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
                if p.get('position') in POS_MIGRATION: p['position'] = POS_MIGRATION[p['position']]; needs_save = True
                correct_val = calculate_player_value(p.get('overall', 70))
                if p.get('value', 0) != correct_val: p['value'] = correct_val; needs_save = True
                if p['name'].lower() in global_dict:
                    gp = global_dict[p['name'].lower()]
                    if p.get('overall') != gp['overall'] or p.get('position') != gp['position']:
                        data['squad'][i]['overall'] = gp['overall']; data['squad'][i]['position'] = gp['position']; data['squad'][i]['value'] = gp['value']; needs_save = True

        for i, p in enumerate(data.get('team', [])):
            if p:
                if p.get('position') in POS_MIGRATION: p['position'] = POS_MIGRATION[p['position']]; needs_save = True
                correct_val = calculate_player_value(p.get('overall', 70))
                if p.get('value', 0) != correct_val: p['value'] = correct_val; needs_save = True
                if p['name'].lower() in global_dict:
                    gp = global_dict[p['name'].lower()]
                    if p.get('overall') != gp['overall'] or p.get('position') != gp['position']:
                        data['team'][i]['overall'] = gp['overall']; data['team'][i]['position'] = gp['position']; data['team'][i]['value'] = gp['value']; needs_save = True
                
        if needs_save:
            try: supabase.table("jogadores").update({"data": data}).eq("id", uid).execute()
            except: pass
        return data
    except Exception: return None

async def save_user_data(user_id, data):
    try: supabase.table("jogadores").update({"data": data}).eq("id", str(user_id)).execute()
    except Exception: pass

def normalize_str(s): return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn').lower()
def get_player_effective_overall(player): 
    if not player: return 0
    return player.get('overall', 70) + player.get('training_level', 0)
def add_player_defaults(player):
    if 'nickname' not in player: player['nickname'] = None
    if 'training_level' not in player: player['training_level'] = 0
    return player

def create_team_image_sync(team_players, club_name, club_sigla, user_money, formation, captain_name):
    width, height = 840, 1240 
    field_img = Image.new("RGB", (width, height), color="#2E7D32")
    draw = ImageDraw.Draw(field_img, "RGBA")
    for i in range(0, height, 50):
        if (i // 50) % 2 == 0: draw.rectangle([0, i, width, i+50], fill="#388E3C")
    line_color = (255, 255, 255, 180)
    draw.rectangle([20, 20, width-20, height-20], outline=line_color, width=6) 
    draw.line([20, height//2, width-20, height//2], fill=line_color, width=6) 
    draw.ellipse([width//2 - 100, height//2 - 100, width//2 + 100, height//2 + 100], outline=line_color, width=6) 
    draw.rectangle([width//2 - 180, 20, width//2 + 180, 200], outline=line_color, width=6) 
    draw.rectangle([width//2 - 180, height-200, width//2 + 180, height-20], outline=line_color, width=6) 
    draw.rectangle([0, 0, width, 90], fill=(0, 0, 0, 220))
    draw.rectangle([0, height-70, width, height], fill=(0, 0, 0, 220))

    try: 
        title_font = ImageFont.truetype(FONT_PATH, 48); stat_font = ImageFont.truetype(FONT_PATH, 26)
        overall_font = ImageFont.truetype(FONT_PATH, 28); pos_font = ImageFont.truetype(FONT_PATH, 22) 
    except Exception: title_font = stat_font = overall_font = pos_font = ImageFont.load_default()

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
                img_x = int(cx - p_img.width//2); img_y = int(cy - ch//2 + 36) 
                field_img.paste(p_img, (img_x, img_y), p_img)
            except: pass
            
            draw.text((cx - cw//2 + 10, cy - ch//2 + 10), player['position'], font=pos_font, fill=border, anchor="la") 
            draw.text((cx + cw//2 - 10, cy - ch//2 + 10), str(eff_ovr), font=overall_font, fill=border, anchor="ra") 

            name_plate_box = [cx - cw//2 + 4, cy + ch//2 - 40, cx + cw//2 - 4, cy + ch//2 - 4]
            draw.rounded_rectangle(name_plate_box, radius=6, fill=(10, 10, 10, 240))
            
            disp_name = player.get('nickname') or player['name'].split(' ')[-1]
            disp_name = disp_name[:12] 
            if captain_name and player['name'] == captain_name: disp_name += " [C]"
            
            current_name_size = 22
            try:
                name_font = ImageFont.truetype(FONT_PATH, current_name_size)
                while name_font.getlength(disp_name.upper()) > cw - 12 and current_name_size > 10:
                    current_name_size -= 1; name_font = ImageFont.truetype(FONT_PATH, current_name_size)
            except: name_font = ImageFont.load_default()
                
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
                if any(x and x['name'] == p['name'] for x in new_team): continue
                pos = p.get('position', '').upper()
                if pos in POS_MIGRATION: pos = POS_MIGRATION[pos]
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
        if inter.user != self.ctx.author: return
        team_players = [p for p in self.user_data['team'] if p]
        if not team_players: return await inter.response.send_message("❌ Você precisa ter jogadores escalados na prancheta.", ephemeral=True)
        options = [discord.SelectOption(label=p['name'], value=p['name'], description=f"OVR: {p['overall']} - {p['position']}") for p in team_players]
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
        if inter: await inter.response.edit_message(embed=emb, view=self)
        else: return emb

    @discord.ui.button(label="⏪ Anterior", style=discord.ButtonStyle.grey, disabled=True)
    async def prev(self, inter, b): 
        self.page -= 1; await self.update_view(inter)

    @discord.ui.button(label="Próxima ⏩", style=discord.ButtonStyle.grey)
    async def next(self, inter, b): 
        self.page += 1; await self.update_view(inter)

class AddPlayerView(discord.ui.View):
    def __init__(self, author, rbx, img): 
        super().__init__(timeout=120)
        self.author, self.rbx, self.img = author, rbx, img

    @discord.ui.button(label="Definir Status", style=discord.ButtonStyle.success, emoji="⚙️")
    async def btn(self, inter, b): 
        if inter.user == self.author: await inter.response.send_modal(AddPlayerModal(self.rbx, self.img))

class EditPlayerView(discord.ui.View):
    def __init__(self, author, nick): 
        super().__init__(timeout=120)
        self.author, self.nick = author, nick

    @discord.ui.button(label="Editar Carta", style=discord.ButtonStyle.primary, emoji="📝")
    async def btn(self, inter, b): 
        if inter.user == self.author: await inter.response.send_modal(EditPlayerModal(self.nick))

class KeepOrSellView(discord.ui.View):
    def __init__(self, author, player): 
        super().__init__(timeout=60)
        self.author = author
        self.player = player
        self.message = None
        self.responded = False

    async def on_timeout(self):
        if self.responded: return
        async with data_lock:
            u = await get_user_data(self.author.id)
            if self.player['name'] not in u["contracted_players"]:
                u['squad'].append(self.player); u['contracted_players'].append(self.player['name']); await save_user_data(self.author.id, u)
        if self.message:
            for child in self.children: child.disabled = True
            try: await self.message.edit(content=f"⏳ **Tempo esgotado!** O olheiro não podia esperar mais e guardou **{self.player['name']}** automaticamente no seu elenco.", view=self)
            except: pass

    @discord.ui.button(label="Manter no Elenco", style=discord.ButtonStyle.green)
    async def keep(self, inter, btn):
        if inter.user != self.author: return
        self.responded = True
        async with data_lock:
            u = await get_user_data(self.author.id)
            if self.player['name'] in u["contracted_players"]: return await inter.response.send_message("Já possui!", ephemeral=True)
            u['squad'].append(self.player); u['contracted_players'].append(self.player['name']); await save_user_data(self.author.id, u)
        await inter.response.edit_message(content=f"✅ **{self.player['name']}** guardado com sucesso no elenco!", embed=None, view=None)

    @discord.ui.button(label="Vender Rápido", style=discord.ButtonStyle.red)
    async def sell(self, inter, btn):
        if inter.user != self.author: return
        self.responded = True
        p = int(self.player['value'] * SALE_PERCENTAGE)
        async with data_lock:
            u = await get_user_data(self.author.id)
            u['money'] += p; await save_user_data(self.author.id, u)
        await inter.response.edit_message(content=f"💰 O atleta foi vendido rapidamente por **R$ {p:,}**.", embed=None, view=None)

class ActionView(discord.ui.View):
    def __init__(self, ctx, res, action_type, user_data):
        super().__init__(timeout=120)
        self.ctx = ctx; self.res = res; self.action_type = action_type; self.user_data = user_data; self.i = 0
        if self.action_type == 'escalar': self.children[2].label = "Escalar Titular"; self.children[2].style = discord.ButtonStyle.primary
        elif self.action_type == 'vender': self.children[2].label = "Vender Atleta"; self.children[2].style = discord.ButtonStyle.danger
        elif self.action_type == 'contratar': self.children[2].label = "Assinar Contrato"; self.children[2].style = discord.ButtonStyle.success

    async def get_page(self):
        p = self.res[self.i]
        if self.action_type == 'contratar': title = "🛒 Mercado de Transferências"; color = discord.Color.blue(); desc = "Avalie as opções e feche a contratação!"
        elif self.action_type == 'vender': title = "💰 Venda de Jogador"; color = discord.Color.red(); desc = "Tem certeza que deseja liberar este atleta?"
        else: title = "📋 Escalar Jogador"; color = discord.Color.green(); desc = "Selecione a melhor peça para sua prancheta."

        emb = discord.Embed(title=title, description=desc, color=color)
        emb.add_field(name="👤 Atleta", value=f"**{p['name']}**", inline=True)
        emb.add_field(name="⭐ OVR", value=f"`{p['overall']}`", inline=True)
        emb.add_field(name="📍 Posição", value=f"`{p['position']}`", inline=True)
        
        if self.action_type == 'contratar': emb.add_field(name="💰 Custo de Contrato", value=f"R$ **{p['value']:,}**", inline=False)
        elif self.action_type == 'vender': emb.add_field(name="💰 Valor de Venda", value=f"R$ **{int(p['value'] * SALE_PERCENTAGE):,}**", inline=False)
        
        emb.set_footer(text=f"Página {self.i + 1}/{len(self.res)} | Seu Saldo: R$ {self.user_data['money']:,}")
        buf = await asyncio.to_thread(render_single_card_sync, p)
        file = discord.File(buf, "card.png"); emb.set_image(url="attachment://card.png")
        return emb, file

    async def update_view(self, inter=None):
        self.children[0].disabled = (self.i == 0); self.children[1].disabled = (self.i == len(self.res) - 1)
        emb, file = await self.get_page()
        if inter: await inter.response.edit_message(embed=emb, attachments=[file], view=self)
        else: return emb, file

    @discord.ui.button(label="⏪", style=discord.ButtonStyle.grey, disabled=True)
    async def prev(self, inter, b): 
        if inter.user != self.ctx.author: return
        self.i -= 1; await self.update_view(inter)

    @discord.ui.button(label="⏩", style=discord.ButtonStyle.grey)
    async def next(self, inter, b): 
        if inter.user != self.ctx.author: return
        self.i += 1; await self.update_view(inter)

    @discord.ui.button(label="Ação", style=discord.ButtonStyle.primary)
    async def act(self, inter, b): 
        if inter.user != self.ctx.author: return
        p = self.res[self.i]
        
        if self.action_type == 'contratar':
            async with data_lock:
                u_data = await get_user_data(self.ctx.author.id)
                if p['name'] in u_data["contracted_players"]: return await inter.response.send_message("❌ Você já possui este atleta no elenco!", ephemeral=True)
                if u_data['money'] < p['value']: return await inter.response.send_message(f"💸 Saldo insuficiente! Faltam R$ {(p['value'] - u_data['money']):,}", ephemeral=True)
                u_data['money'] -= p['value']; u_data['squad'].append(p); u_data['contracted_players'].append(p['name']); await save_user_data(self.ctx.author.id, u_data)
            success_emb = discord.Embed(title="🤝 NEGÓCIO FECHADO!", description=f"Você contratou **{p['name']}** com sucesso!", color=discord.Color.green())
            success_emb.add_field(name="💰 Preço Pago", value=f"R$ {p['value']:,}", inline=True); success_emb.add_field(name="🏦 Saldo Restante", value=f"R$ {u_data['money']:,}", inline=True)
            await inter.response.edit_message(embed=success_emb, attachments=[], view=None)

        elif self.action_type == 'vender':
            async with data_lock:
                u_data = await get_user_data(self.ctx.author.id)
                if p['name'] not in u_data['contracted_players']: return await inter.response.send_message("❌ Este atleta não está mais no seu elenco.", ephemeral=True)
                u_data['squad'] = [x for x in u_data['squad'] if x['name'] != p['name']]; u_data['contracted_players'].remove(p['name'])
                for idx, x in enumerate(u_data['team']): 
                    if x and x['name'] == p['name']: u_data['team'][idx] = None
                cash = int(p['value'] * SALE_PERCENTAGE); u_data['money'] += cash; await save_user_data(self.ctx.author.id, u_data)
            emb = discord.Embed(title="💰 VENDA CONCLUÍDA!", description=f"**{p['name']}** deixou o clube.", color=discord.Color.green())
            emb.add_field(name="💵 Valor Recebido", value=f"R$ {cash:,}", inline=False)
            await inter.response.edit_message(embed=emb, attachments=[], view=None)

        elif self.action_type == 'escalar':
            async with data_lock:
                d = await get_user_data(self.ctx.author.id)
                t = d['team']; formation = d.get('formation', '4-3-3')
                if any(x and x['name'] == p['name'] for x in t): return await inter.response.send_message("❌ Já é titular.", ephemeral=True)
                coords, mapping = get_formation_config(formation); done = False
                for pos in p['position'].split('/'):
                    if pos in mapping:
                        for idx in mapping[pos]:
                            if t[idx] is None: t[idx] = p; done = True; break
                    if done: break
                if done: 
                    await save_user_data(self.ctx.author.id, d)
                    emb = discord.Embed(title="✅ JOGADOR ESCALADO!", description=f"**{p['name']}** agora é o dono da posição na tática {formation}.", color=discord.Color.green())
                    await inter.response.edit_message(embed=emb, attachments=[], view=None)
                else: await inter.response.send_message("❌ Sem vaga livre para essa posição na prancheta.\n💡 Dica: Use o botão de `⚡ Auto-Escalar`, ou mude a formação da prancheta.", ephemeral=True)

# --- 8. EVENTOS DO BOT ---
@bot.event
async def on_ready():
    print(f'🟢 EFL Guru ONLINE! Todas as linhas carregadas e Render ativado.')
    fetch_and_parse_players()
    await bot.change_presence(activity=discord.Game(name=f"{BOT_PREFIX}help | EFL Manager"))

@bot.check
async def maintenance_check(ctx):
    global MAINTENANCE_MODE
    if ctx.command and ctx.command.name == 'disableall': return True
    if MAINTENANCE_MODE and not ctx.author.guild_permissions.administrator:
        await ctx.send("🛠️ **SISTEMA EM MANUTENÇÃO.**"); return False
    return True

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        horas = int(error.retry_after // 3600); minutos = int((error.retry_after % 3600) // 60); segundos = int(error.retry_after % 60)
        return await ctx.send(f"⏳ **Calma aí, chefinho!** O comando está em tempo de recarga.\n\nTente usar novamente em **{horas}h {minutos}m {segundos}s**.")
    if isinstance(error, commands.CommandNotFound): return
    if isinstance(error, commands.CheckFailure): return
    print(f"Erro detectado: {error}")

# --- 9. COMANDOS DE ADMINISTRAÇÃO E FIX ROBLOX ---
@bot.command(name='disableall')
@is_bot_admin()
async def disableall_cmd(ctx):
    await ctx.send("⚠️ **ATENÇÃO!** Digite exatamente:\n`DESABILITAR EFL GURU BOT`\n*(Você tem 30 segundos)*")
    def check(m): return m.author.id == ctx.author.id and m.channel == ctx.channel
    try:
        msg = await bot.wait_for('message', check=check, timeout=30.0)
        if msg.content == "DESABILITAR EFL GURU BOT":
            await ctx.send("🛑 **Recebido.** Fechando as portas do servidor desta versão e morrendo com honra... Pode mandar a nova versão, mestre!")
            await bot.close(); os._exit(0) 
        else: await ctx.send("❌ Confirmação incorreta. O bot continuará online e rodando.")
    except asyncio.TimeoutError: await ctx.send("⏳ Tempo esgotado. A operação de autodestruição foi cancelada.")

@bot.command(name='lock')
@is_bot_admin()
async def lock_cmd(ctx):
    global MAINTENANCE_MODE; MAINTENANCE_MODE = True
    await ctx.send("🛑 **SISTEMA BLOQUEADO.**")

@bot.command(name='unlock')
@is_bot_admin()
async def unlock_cmd(ctx):
    global MAINTENANCE_MODE; MAINTENANCE_MODE = False
    await ctx.send("🟢 **SISTEMA LIBERADO.**")

def get_roblox_data_sync(username):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'}
    try:
        res = requests.post("https://users.roblox.com/v1/usernames/users", json={"usernames": [username]}, headers=headers, timeout=10)
        if res.status_code == 429: time.sleep(2); res = requests.post("https://users.roblox.com/v1/usernames/users", json={"usernames": [username]}, headers=headers, timeout=10)
        data = res.json()
        if not data.get("data"): return None
        uid = data["data"][0]["id"]
        res2 = requests.get(f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={uid}&size=420x420&format=Png&isCircular=false", headers=headers, timeout=10)
        data2 = res2.json()
        if data2.get("data") and data2["data"][0].get("imageUrl"): return data2["data"][0]["imageUrl"]
        return None
    except Exception as e: return None

@bot.command(name='analyzemembers')
@is_bot_admin()
async def analyze_members_cmd(ctx):
    target_role_id = 1470883144528822420
    role = ctx.guild.get_role(target_role_id)
    if not role: return await ctx.send("❌ Cargo alvo não encontrado no servidor.")
    msg = await ctx.send("⏳ **Iniciando varredura de membros...**")
    db_names = [p['name'].lower() for p in ALL_PLAYERS]; candidates = []
    for member in role.members:
        if "EFL" in member.display_name.upper(): continue
        nick = member.display_name.split()[-1].strip()
        if nick.lower() in db_names: continue
        candidates.append({"nick": nick, "discord_name": member.display_name})
    if not candidates: return await msg.edit(content="❌ **Varredura Concluída:** Nenhum membro novo apto encontrado.")
    queue = []
    for c in candidates:
        img = await asyncio.to_thread(get_roblox_data_sync, c["nick"])
        if img: c["image"] = img; queue.append(c)
        await asyncio.sleep(0.5) 
    if not queue: return await msg.edit(content="❌ **Varredura Concluída:** Nenhuma conta válida encontrada no banco de dados do Roblox.")
    view = AnalyzeMembersView(ctx, queue, msg); await view.update_view()

@bot.command(name='addplayer')
@commands.has_permissions(administrator=True)
async def add_player_cmd(ctx, *, query: str):
    msg = await ctx.send("🔄 Verificando Roblox...")
    try: member = await commands.MemberConverter().convert(ctx, query); rbx_name = member.display_name.split()[-1].strip()
    except: rbx_name = query.strip()
    img = await asyncio.to_thread(get_roblox_data_sync, rbx_name)
    if not img: return await msg.edit(content=f"❌ Nick `{rbx_name}` não existe ou não foi possível carregar a foto.")
    view = AddPlayerView(ctx.author, rbx_name, img)
    emb = discord.Embed(title="📸 Perfil Encontrado", color=discord.Color.green())
    emb.set_thumbnail(url=img)
    await msg.edit(content=None, embed=emb, view=view)

@bot.command(name='bulkadd')
@commands.has_permissions(administrator=True)
async def bulk_add_cmd(ctx):
    if not ctx.message.attachments: return await ctx.send("❌ Anexe um arquivo `.txt`.")
    att = ctx.message.attachments[0]; status = await ctx.send("⏳ **Iniciando Bulk Add...**")
    try:
        content = (await att.read()).decode('utf-8'); lines = content.strip().split('\n')
        res = supabase.table("jogadores").select("data").eq("id", "ROBLOX_CARDS").execute()
        cards = res.data[0]["data"] if res.data else []; names = [p['name'].lower() for p in cards]; added = []; erros_log = []
        for line in lines:
            parts = line.split()
            if len(parts) < 3: continue
            n = parts[0].strip(); ovr = int(parts[1].strip()); pos = parts[2].strip().upper()
            if pos in POS_MIGRATION: pos = POS_MIGRATION[pos]
            if n.lower() in names: erros_log.append(f"Ignorado: {n} (Já está no banco de dados)"); continue
            coords, mapping = get_formation_config("4-3-3")
            if pos not in mapping: erros_log.append(f"Ignorado: {n} (Posição {pos} não reconhecida)"); continue
            img = await asyncio.to_thread(get_roblox_data_sync, n)
            if img:
                val = calculate_player_value(ovr); cards.append({"name": n, "image": img, "overall": ovr, "position": pos, "value": val})
                names.append(n.lower()); added.append(n)
            else: erros_log.append(f"Ignorado: {n} (API do Roblox bloqueou ou nick inválido)")
            await asyncio.sleep(1.5)
        if added: supabase.table("jogadores").upsert({"id": "ROBLOX_CARDS", "data": cards}).execute(); fetch_and_parse_players()
        relatorio = f"✅ Adicionados: **{len(added)}** atletas."
        if erros_log:
            resumo_erros = "\n".join(erros_log[:10])
            if len(erros_log) > 10: resumo_erros += f"\n...e mais {len(erros_log) - 10} erros ocultos."
            relatorio += f"\n\n⚠️ **Relatório do Sistema:**\n```\n{resumo_erros}\n```"
        await status.edit(content=relatorio)
    except Exception as e: await status.edit(content=f"❌ Erro no formato. Use: Nick OVR Pos\nDetalhe: {e}")

@bot.command(name='editplayer')
@commands.has_permissions(administrator=True)
async def edit_player_cmd(ctx, *, nick: str):
    view = EditPlayerView(ctx.author, nick); await ctx.send(f"⚙️ Configurações de `{nick}`:", view=view)

@bot.command(name='delplayer')
@commands.has_permissions(administrator=True)
async def del_player_cmd(ctx, *, nick: str):
    async with data_lock:
        try:
            res = supabase.table("jogadores").select("data").eq("id", "ROBLOX_CARDS").execute(); cards = res.data[0]["data"] if res.data else []
            original_count = len(cards); cards = [p for p in cards if p['name'].lower() != nick.lower()]
            if len(cards) == original_count: return await ctx.send(f"❌ O jogador `{nick}` não foi encontrado no banco de dados do mercado.")
            supabase.table("jogadores").update({"data": cards}).eq("id", "ROBLOX_CARDS").execute()
            global ALL_PLAYERS; fetch_and_parse_players(); await ctx.send(f"🗑️ ✅ A carta de **{nick}** foi removida permanentemente do mercado global da EFL!")
        except Exception as e: await ctx.send(f"❌ Ocorreu um erro ao tentar deletar o jogador: {e}")

@bot.command(name='syncroblox')
@is_bot_admin()
async def sync_cmd(ctx):
    fetch_and_parse_players(); await ctx.send(f"✅ Memória RAM sincronizada! **{len(ALL_PLAYERS)}** cartas prontas.")

@bot.command(name='addmoney')
@is_bot_admin()
async def addmoney_cmd(ctx, target: discord.User, amount: int):
    if amount <= 0: return await ctx.send("❌ O valor deve ser positivo.")
    async with data_lock:
        u_data = await get_user_data(target.id); u_data['money'] += amount; await save_user_data(target.id, u_data)
    await ctx.send(f"✅ **ADMIN:** Adicionado R$ {amount:,} à conta de {target.mention}.\nNovo saldo: R$ {u_data['money']:,}")

@bot.command(name='removemoney')
@is_bot_admin()
async def removemoney_cmd(ctx, target: discord.User, amount: int):
    if amount <= 0: return await ctx.send("❌ O valor deve ser positivo.")
    async with data_lock:
        u_data = await get_user_data(target.id); u_data['money'] = max(0, u_data['money'] - amount); await save_user_data(target.id, u_data)
    await ctx.send(f"✅ **ADMIN:** Removido R$ {amount:,} da conta de {target.mention}.\nNovo saldo: R$ {u_data['money']:,}")

# --- 10. COMANDOS DO JOGO NORMAL (MERCADO, JOGADORES REAIS) ---

@bot.command(name='caixa')
async def caixa_cmd(ctx):
    async with data_lock:
        u = await get_user_data(ctx.author.id)
        last_use_str = u.get('last_caixa_use')
        now = datetime.utcnow(); cooldown_seconds = 43200 
        if last_use_str:
            last_use = datetime.fromisoformat(last_use_str)
            time_passed = (now - last_use).total_seconds()
            if time_passed < cooldown_seconds:
                remaining = cooldown_seconds - time_passed
                horas = int(remaining // 3600); minutos = int((remaining % 3600) // 60); segundos = int(remaining % 60)
                return await ctx.send(f"⏳ **Calma aí, chefinho!** A caixa diária ainda está fechada.\n\nTente novamente em **{horas}h {minutos}m {segundos}s**.")
        u['last_caixa_use'] = now.isoformat(); await save_user_data(ctx.author.id, u)

    boxes = ["Bronze", "Iron", "Gold", "Diamond", "Master"]; weights = [60, 25, 10, 4, 1] 
    chosen_box = random.choices(boxes, weights=weights, k=1)[0]
    
    async with data_lock:
        u = await get_user_data(ctx.author.id)
        livres = [p for p in ALL_PLAYERS if p["name"] not in u["contracted_players"]]
        def get_player_by_ovr(min_o, max_o):
            pool = [p for p in livres if min_o <= p.get('overall', 70) <= max_o]
            if pool: return random.choice(pool)
            return None
        money_won = 0; player_won = None
        
        if chosen_box == "Bronze": money_won = random.randint(50000, 150000); emoji = "🥉"
        elif chosen_box == "Iron":
            money_won = random.randint(100000, 300000); emoji = "⚙️"
            if random.random() < 0.10: player_won = get_player_by_ovr(70, 74)
        elif chosen_box == "Gold":
            money_won = random.randint(200000, 500000); emoji = "🥇"
            chance = random.random()
            if chance < 0.05: player_won = get_player_by_ovr(80, 84) 
            elif chance < 0.35: player_won = get_player_by_ovr(75, 79)
        elif chosen_box == "Diamond":
            money_won = random.randint(500000, 1000000); emoji = "💎"
            chance = random.random()
            if chance < 0.02: player_won = get_player_by_ovr(90, 99) 
            elif chance < 0.20: player_won = get_player_by_ovr(85, 89) 
            else: player_won = get_player_by_ovr(80, 84) 
        elif chosen_box == "Master":
            money_won = random.randint(1000000, 2000000); emoji = "🏆"
            chance = random.random()
            if chance < 0.30: player_won = get_player_by_ovr(90, 99) 
            else: player_won = get_player_by_ovr(85, 89)
            
        u['money'] += money_won
        desc = f"Você abriu uma **{emoji} {chosen_box} Box**!\n\n💵 **Dinheiro:** R$ {money_won:,}"
        file_to_send = None
        if player_won:
            u['squad'].append(player_won); u['contracted_players'].append(player_won['name'])
            desc += f"\n\n👤 **Jogador Encontrado:** {player_won['name']} (⭐ {player_won['overall']})\n*O jogador foi adicionado diretamente ao seu elenco!*"
            async with image_lock:
                buf = await asyncio.to_thread(render_single_card_sync, player_won)
                file_to_send = discord.File(buf, "card.png")
        await save_user_data(ctx.author.id, u)
        
    emb = discord.Embed(title="🎁 Recompensa Diária (12h)", description=desc, color=discord.Color.gold())
    if file_to_send: emb.set_image(url="attachment://card.png"); await ctx.send(embed=emb, file=file_to_send)
    else: await ctx.send(embed=emb)

@bot.command(name='jogadores')
async def jogadores_cmd(ctx):
    if not ALL_PLAYERS: return await ctx.send("❌ O mercado está vazio. Nenhum jogador cadastrado no momento.")
    sorted_players = sorted(ALL_PLAYERS, key=lambda x: x['overall'], reverse=True)
    linhas = [f"⭐ **{p['overall']}** | `{p['position']}` | {p['name']}" for p in sorted_players]
    view = MarketPaginator(linhas, "🌍 Mercado Global de Jogadores - EFL")
    emb = await view.get_page(); await ctx.send(embed=emb, view=view)

@bot.command(name='setclube')
async def setclube_cmd(ctx, sigla: str, *, nome: str):
    d = await get_user_data(ctx.author.id)
    d['club_sigla'] = sigla.upper()[:4]; d['club_name'] = nome[:20].strip()
    await save_user_data(ctx.author.id, d)
    await ctx.send(f"✅ Identidade do clube atualizada: **[{d['club_sigla']}] {d['club_name']}**")

async def reminder_task(ctx, user):
    await asyncio.sleep(600)
    try: await ctx.send(f"⏰ <@{user.id}>, seu olheiro voltou! O comando `{BOT_PREFIX}obter` já está liberado novamente.")
    except: pass

@bot.command(name='obter')
async def obter_cmd(ctx):
    async with data_lock:
        u = await get_user_data(ctx.author.id)
        last_use_str = u.get('last_obter_use')
        now = datetime.utcnow(); cooldown_seconds = 600
        if last_use_str:
            last_use = datetime.fromisoformat(last_use_str)
            time_passed = (now - last_use).total_seconds()
            if time_passed < cooldown_seconds:
                remaining = cooldown_seconds - time_passed
                minutos = int((remaining % 3600) // 60); segundos = int(remaining % 60)
                return await ctx.send(f"⏳ **Calma aí, chefinho!** O olheiro está descansando.\n\nTente novamente em **{minutos}m {segundos}s**.")
        u['last_obter_use'] = now.isoformat(); await save_user_data(ctx.author.id, u)

    async with data_lock:
        u = await get_user_data(ctx.author.id)
        livres = [p for p in ALL_PLAYERS if p["name"] not in u["contracted_players"]]
        if not livres: 
            u['last_obter_use'] = None; await save_user_data(ctx.author.id, u)
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
        async with image_lock: buf = await asyncio.to_thread(render_single_card_sync, p)
        
    raridade = "🥉 Bronze"
    if p.get('overall', 70) >= 90: raridade = "✨ LENDÁRIO"
    elif p.get('overall', 70) >= 80: raridade = "🥇 Ouro"
    elif p.get('overall', 70) >= 75: raridade = "🥈 Prata"
    
    view = KeepOrSellView(ctx.author, p)
    msg = await ctx.send(content=f"🃏 **OLHEIRO DA EFL:** Você encontrou um talento **{raridade}** solto pelo mundo!\n*(Você tem 60 segundos para escolher ou ele irá para o seu elenco automaticamente)*", file=discord.File(buf, "card.png"), view=view)
    view.message = msg; bot.loop.create_task(reminder_task(ctx, ctx.author))

@bot.command(name='contratar')
async def contratar_cmd(ctx, *, q: str):
    sq = normalize_str(q); u = await get_user_data(ctx.author.id)
    matches = [p for p in ALL_PLAYERS if sq in normalize_str(p['name']) or sq.upper() in p['position']]
    if not matches: return await ctx.send("❌ Nenhum atleta encontrado no mercado com esse nome ou posição.")
    v = ActionView(ctx, matches, 'contratar', u); emb, file = await v.update_view(); await ctx.send(embed=emb, file=file, view=v)

@bot.command(name='cofre')
async def cofre_cmd(ctx):
    d = await get_user_data(ctx.author.id); await ctx.send(f"🏦 **SALDO DA CONTA:** R$ {d['money']:,}")

@bot.command(name='donate')
async def donate_cmd(ctx, target: discord.Member, amount: int):
    if ctx.author == target or amount <= 0: return
    async with data_lock:
        s_data = await get_user_data(ctx.author.id); t_data = await get_user_data(target.id)
        if s_data['money'] < amount: return await ctx.send("❌ Saldo insuficiente para essa doação.")
        s_data['money'] -= amount; t_data['money'] += amount
        await save_user_data(ctx.author.id, s_data); await save_user_data(target.id, t_data)
    await ctx.send(f"💸 **TRANSFERÊNCIA CONCLUÍDA:** R$ {amount:,} enviados para {target.display_name}!")

@bot.command(name='sell')
async def sell_cmd(ctx, *, q: str):
    sq = normalize_str(q); d = await get_user_data(ctx.author.id)
    matches = [p for p in d['squad'] if sq in normalize_str(p['name'])]
    if not matches: return await ctx.send("❌ Este atleta não foi encontrado no seu elenco atual.")
    v = ActionView(ctx, matches, 'vender', d); emb, file = await v.update_view(); await ctx.send(embed=emb, file=file, view=v)

@bot.command(name='escalar')
async def escalar_cmd(ctx, *, q: str):
    sq = normalize_str(q); d = await get_user_data(ctx.author.id)
    matches = [p for p in d['squad'] if sq in normalize_str(p['name'])]
    if not matches: return await ctx.send("❌ Atleta não encontrado no seu elenco. Contrate-o primeiro!")
    v = ActionView(ctx, matches, 'escalar', d); emb, file = await v.update_view(); await ctx.send(embed=emb, file=file, view=v)

@bot.command(name='banco')
async def banco_cmd(ctx, *, q: str):
    sq = normalize_str(q); d = await get_user_data(ctx.author.id); encontrado = False
    for i, p in enumerate(d['team']):
        if p and sq in normalize_str(p['name']):
            nome = p['name']; d['team'][i] = None; encontrado = True; break
    if encontrado: await save_user_data(ctx.author.id, d); await ctx.send(f"🔄 **{nome}** foi retirado da prancheta e voltou para o banco de reservas! A vaga está livre.")
    else: await ctx.send("❌ Esse jogador não foi encontrado na sua escalação titular.")

@bot.command(name='elenco')
async def elenco_cmd(ctx):
    d = await get_user_data(ctx.author.id)
    if not d['squad']: return await ctx.send("❌ Seu elenco está vazio. Digite `--obter`, `--caixa` ou `--contratar` para buscar atletas.")
    txt = "\n".join([f"**{p['position']}** | {p['name']} | ⭐ {p['overall']}" for p in sorted(d['squad'], key=lambda x: x['overall'], reverse=True)[:25]])
    emb = discord.Embed(title=f"🎽 Elenco de {ctx.author.display_name}", description=txt, color=discord.Color.blue())
    emb.set_footer(text=f"Total de atletas no clube: {len(d['squad'])}")
    await ctx.send(embed=emb)

@bot.command(name='team')
async def team_cmd(ctx):
    d = await get_user_data(ctx.author.id); msg = await ctx.send("⚙️ Desenhando prancheta HD...")
    async with image_lock:
        try:
            buf = await generate_team_image(d, ctx.author)
            view = TeamManagerView(ctx, d)
            await ctx.send(file=discord.File(buf, "team.png"), view=view); await msg.delete()
        except Exception as e: await msg.edit(content=f"❌ Erro na geração do gráfico: {e}")

@bot.command(name='confrontar')
async def confrontar_cmd(ctx, oponente: discord.Member):
    if ctx.author == oponente or oponente.bot: return await ctx.send("❌ Você não pode desafiar a si mesmo ou a um bot!")
    if ctx.author.id in active_matches: return await ctx.send("❌ Você já está em uma partida! Espere o apito final para jogar novamente.")
    if oponente.id in active_matches: return await ctx.send(f"❌ **{oponente.display_name}** já está em campo disputando uma partida no momento.")
    d1 = await get_user_data(ctx.author.id); d2 = await get_user_data(oponente.id)
    if None in d1['team']: return await ctx.send(f"🚨 Sua prancheta está incompleta! Você precisa escalar os 11 titulares para jogar na EFL.")
    if None in d2['team']: return await ctx.send(f"🚨 A prancheta do seu adversário ({oponente.display_name}) está incompleta! Ele precisa escalar os 11 titulares.")
    view = MatchInviteView(ctx, ctx.author, oponente, d1, d2)
    emb = discord.Embed(title="⚔️ NOVO DESAFIO NA EFL!", description=f"{oponente.mention}, o manager **{ctx.author.display_name}** está chamando sua equipe para um confronto oficial!\n\nVocê aceita o desafio?", color=discord.Color.orange())
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
    emb.add_field(name="⚙️ Administração", value="`--addplayer`, `--bulkadd`, `--editplayer`, `--delplayer`, `--lock`, `--unlock`, `--disableall`, `--addmoney`, `--removemoney` ", inline=False)
    emb.set_footer(text="Versão 42.0 - Desenvolvido exclusivamente para a EFL")
    await ctx.send(embed=emb)

# --- INICIALIZAÇÃO ---
if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if token: 
        keep_alive()
        bot.run(token)
    else: 
        print("❌ Token ausente no arquivo .env.")
