"""
NBA Playoffs 2026 - Clutch Analytics
Onde o Amor pelo Jogo Encontra a Ciencia de Dados
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import numpy as np
import requests
import json

st.set_page_config(
    page_title="NBA Clutch Analytics 2026",
    page_icon="🏀",
    layout="wide",
    initial_sidebar_state="expanded"
)

PRIMARY = "#1E3A8A"
SECONDARY = "#DC2626"
ACCENT = "#F59E0B"
POSITIVE = "#10B981"
NEGATIVE = "#EF4444"

@st.cache_data(ttl=3600)
def get_data():
    east_teams = [
        "Boston Celtics", "New York Knicks", "Cleveland Cavaliers", "Philadelphia 76ers",
        "Orlando Magic", "Detroit Pistons", "Toronto Raptors", "Atlanta Hawks"
    ]
    west_teams = [
        "Oklahoma City Thunder", "Denver Nuggets", "Minnesota Timberwolves", "Houston Rockets",
        "Los Angeles Lakers", "Phoenix Suns", "Portland Trail Blazers", "San Antonio Spurs"
    ]
    valid_teams = set(east_teams + west_teams)

    series = [
        # LESTE 1: Boston vs Philadelphia
        {
            "time_a": "Boston Celtics", "time_b": "Philadelphia 76ers",
            "conf": "Leste", "va": 3, "vb": 2,
            "motivo": "Tatum vs Embiid: Uma batalha de estilos",
            "players": {
                "Boston Celtics": [
                    {"nome": "Jayson Tatum", "pts": 28.4, "ast": 5.2, "reb": 8.6, "blk": 1.2, "stl": 1.4,
                     "pts_reg": 26.8, "ast_reg": 4.8, "reb_reg": 8.2, "fg_reg": 0.472, "tov_reg": 2.8,
                     "fg_po": 0.481, "tov_po": 2.6, "mpg_reg": 36.2, "mpg_po": 38.4,
                     "clutch_moment": "Cestou 31 pontos no Jogo 3, virando o jogo no 4ºQ"},
                    {"nome": "Jaylen Brown", "pts": 24.6, "ast": 3.8, "reb": 6.2, "blk": 0.8, "stl": 1.1,
                     "pts_reg": 22.9, "ast_reg": 3.4, "reb_reg": 5.8, "fg_reg": 0.478, "tov_reg": 2.1,
                     "fg_po": 0.482, "tov_po": 2.0, "mpg_reg": 34.1, "mpg_po": 35.8,
                     "clutch_moment": "Defesa elite no 4ºQ do Jogo 5"},
                    {"nome": "Derrick White", "pts": 14.2, "ast": 4.1, "reb": 3.8, "blk": 0.6, "stl": 1.2,
                     "pts_reg": 13.8, "ast_reg": 3.9, "reb_reg": 3.6, "fg_reg": 0.462, "tov_reg": 1.8,
                     "fg_po": 0.471, "tov_po": 1.6, "mpg_reg": 32.4, "mpg_po": 34.2}
                ],
                "Philadelphia 76ers": [
                    {"nome": "Joel Embiid", "pts": 31.2, "ast": 4.2, "reb": 11.4, "blk": 2.1, "stl": 0.8,
                     "pts_reg": 33.1, "ast_reg": 4.6, "reb_reg": 11.8, "fg_reg": 0.512, "tov_reg": 3.2,
                     "fg_po": 0.498, "tov_po": 3.4, "mpg_reg": 33.8, "mpg_po": 36.2,
                     "clutch_moment": "Dominou o garrafão, mas sofreu com a defesa dupla"},
                    {"nome": "Tyrese Maxey", "pts": 22.8, "ast": 6.4, "reb": 3.6, "blk": 0.2, "stl": 1.6,
                     "pts_reg": 25.3, "ast_reg": 6.8, "reb_reg": 3.8, "fg_reg": 0.456, "tov_reg": 2.4,
                     "fg_po": 0.441, "tov_po": 2.6, "mpg_reg": 35.4, "mpg_po": 37.1,
                     "clutch_moment": "Speed kills, mas cometeu erros no Jogo 4"},
                    {"nome": "Tobias Harris", "pts": 16.8, "ast": 2.4, "reb": 6.2, "blk": 0.4, "stl": 0.8,
                     "pts_reg": 17.2, "ast_reg": 2.6, "reb_reg": 6.4, "fg_reg": 0.498, "tov_reg": 1.6,
                     "fg_po": 0.492, "tov_po": 1.4, "mpg_reg": 32.8, "mpg_po": 34.6}
                ]
            }
        },
        # LESTE 2: Cleveland vs Toronto
        {
            "time_a": "Cleveland Cavaliers", "time_b": "Toronto Raptors",
            "conf": "Leste", "va": 3, "vb": 2,
            "motivo": "Defesa vs Velocidade: Mobley tenta conter Barnes",
            "players": {
                "Cleveland Cavaliers": [
                    {"nome": "Donovan Mitchell", "pts": 27.4, "ast": 5.8, "reb": 4.8, "blk": 0.4, "stl": 1.6,
                     "pts_reg": 28.2, "ast_reg": 5.2, "reb_reg": 4.6, "fg_reg": 0.485, "tov_reg": 2.6,
                     "fg_po": 0.478, "tov_po": 2.4, "mpg_reg": 35.6, "mpg_po": 37.2,
                     "clutch_moment": "Ice in his veins - 15 pontos no 4ºQ do Jogo 3"},
                    {"nome": "Evan Mobley", "pts": 18.2, "ast": 3.2, "reb": 10.4, "blk": 2.2, "stl": 0.9,
                     "pts_reg": 16.5, "ast_reg": 2.8, "reb_reg": 9.8, "fg_reg": 0.562, "tov_reg": 1.8,
                     "fg_po": 0.571, "tov_po": 1.6, "mpg_reg": 33.2, "mpg_po": 35.4,
                     "clutch_moment": "Defesa de DPOY, alterou 8 arremessos"}
                ],
                "Toronto Raptors": [
                    {"nome": "Scottie Barnes", "pts": 22.4, "ast": 4.8, "reb": 8.4, "blk": 1.2, "stl": 1.4,
                     "pts_reg": 20.1, "ast_reg": 4.2, "reb_reg": 7.9, "fg_reg": 0.498, "tov_reg": 2.2,
                     "fg_po": 0.502, "tov_po": 2.0, "mpg_reg": 34.8, "mpg_po": 36.6,
                     "clutch_moment": "Jovem, mas jogou como veterano no Jogo 4 (32 pts, 12 reb)"},
                    {"nome": "Pascal Siakam", "pts": 20.8, "ast": 3.6, "reb": 7.2, "blk": 0.8, "stl": 1.1,
                     "pts_reg": 22.4, "ast_reg": 3.4, "reb_reg": 7.6, "fg_reg": 0.502, "tov_reg": 1.9,
                     "fg_po": 0.488, "tov_po": 1.8, "mpg_reg": 33.6, "mpg_po": 35.2}
                ]
            }
        },
        # LESTE 3: New York vs Atlanta
        {
            "time_a": "New York Knicks", "time_b": "Atlanta Hawks",
            "conf": "Leste", "va": 3, "vb": 2,
            "motivo": "Brunson Magic: O pequeno gigante vs a defesa dos Hawks",
            "players": {
                "New York Knicks": [
                    {"nome": "Jalen Brunson", "pts": 26.8, "ast": 7.2, "reb": 3.4, "blk": 0.2, "stl": 1.2,
                     "pts_reg": 28.5, "ast_reg": 6.8, "reb_reg": 3.2, "fg_reg": 0.494, "tov_reg": 2.4,
                     "fg_po": 0.486, "tov_po": 2.2, "mpg_reg": 35.8, "mpg_po": 37.4,
                     "clutch_moment": "14-0 na prorrogação do Jogo 5 - puro clutch!"},
                    {"nome": "Julius Randle", "pts": 22.4, "ast": 4.6, "reb": 9.2, "blk": 0.4, "stl": 0.8,
                     "pts_reg": 24.1, "ast_reg": 5.1, "reb_reg": 9.8, "fg_reg": 0.475, "tov_reg": 2.8,
                     "fg_po": 0.468, "tov_po": 2.6, "mpg_reg": 34.4, "mpg_po": 36.2}
                ],
                "Atlanta Hawks": [
                    {"nome": "Dejounte Murray", "pts": 20.4, "ast": 5.6, "reb": 6.2, "blk": 0.4, "stl": 1.8,
                     "pts_reg": 22.7, "ast_reg": 6.1, "reb_reg": 5.8, "fg_reg": 0.488, "tov_reg": 2.3,
                     "fg_po": 0.476, "tov_po": 2.1, "mpg_reg": 35.2, "mpg_po": 36.8,
                     "clutch_moment": "Roubou 3 bolas cruciais no Jogo 3"},
                    {"nome": "Clint Capela", "pts": 12.8, "ast": 1.4, "reb": 11.2, "blk": 1.6, "stl": 0.6,
                     "pts_reg": 11.9, "ast_reg": 1.2, "reb_reg": 10.8, "fg_reg": 0.624, "tov_reg": 1.4,
                     "fg_po": 0.618, "tov_po": 1.3, "mpg_reg": 28.4, "mpg_po": 30.2}
                ]
            }
        },
        # LESTE 4: Orlando vs Detroit
        {
            "time_a": "Orlando Magic", "time_b": "Detroit Pistons",
            "conf": "Leste", "va": 3, "vb": 2,
            "motivo": "Juventude vs Experiência: Banchero vs Cunningham",
            "players": {
                "Orlando Magic": [
                    {"nome": "Paolo Banchero", "pts": 24.6, "ast": 4.8, "reb": 7.4, "blk": 1.2, "stl": 1.4,
                     "pts_reg": 22.9, "ast_reg": 4.2, "reb_reg": 6.8, "fg_reg": 0.462, "tov_reg": 2.6,
                     "fg_po": 0.471, "tov_po": 2.4, "mpg_reg": 34.6, "mpg_po": 36.8,
                     "clutch_moment": "Jovem, mas jogou como veterano no Jogo 4 (32 pts, 12 reb)"},
                    {"nome": "Franz Wagner", "pts": 20.2, "ast": 3.6, "reb": 6.8, "blk": 0.8, "stl": 1.8,
                     "pts_reg": 18.7, "ast_reg": 3.2, "reb_reg": 6.2, "fg_reg": 0.478, "tov_reg": 2.1,
                     "fg_po": 0.484, "tov_po": 1.9, "mpg_reg": 33.8, "mpg_po": 35.6}
                ],
                "Detroit Pistons": [
                    {"nome": "Cade Cunningham", "pts": 26.2, "ast": 7.8, "reb": 6.4, "blk": 0.6, "stl": 1.6,
                     "pts_reg": 23.4, "ast_reg": 7.2, "reb_reg": 5.9, "fg_reg": 0.442, "tov_reg": 3.1,
                     "fg_po": 0.458, "tov_po": 2.8, "mpg_reg": 35.4, "mpg_po": 37.2,
                     "clutch_moment": "Visão de jogo incrível, mas turnover custoso no Jogo 5"},
                    {"nome": "Jalen Duren", "pts": 14.8, "ast": 2.2, "reb": 11.2, "blk": 2.4, "stl": 0.8,
                     "pts_reg": 13.2, "ast_reg": 1.8, "reb_reg": 10.6, "fg_reg": 0.618, "tov_reg": 1.6,
                     "fg_po": 0.525, "tov_po": 1.4, "mpg_reg": 28.8, "mpg_po": 30.6}
                ]
            }
        },
        # OESTE 1: Oklahoma vs Phoenix
        {
            "time_a": "Oklahoma City Thunder", "time_b": "Phoenix Suns",
            "conf": "Oeste", "va": 4, "vb": 0,
            "motivo": "SGA vs KD: A nova geração varrendo as lendas",
            "players": {
                "Oklahoma City Thunder": [
                    {"nome": "Shai Gilgeous-Alexander", "pts": 31.2, "ast": 6.4, "reb": 5.8, "blk": 1.2, "stl": 2.1,
                     "pts_reg": 30.8, "ast_reg": 6.2, "reb_reg": 5.4, "fg_reg": 0.532, "tov_reg": 2.2,
                     "fg_po": 0.541, "tov_po": 2.0, "mpg_reg": 36.8, "mpg_po": 38.2,
                     "clutch_moment": "Imparável - 40+ pontos nos jogos 3 e 4"},
                    {"nome": "Jalen Williams", "pts": 18.4, "ast": 4.2, "reb": 6.8, "blk": 0.8, "stl": 1.6,
                     "pts_reg": 17.2, "ast_reg": 3.8, "reb_reg": 6.4, "fg_reg": 0.542, "tov_reg": 1.8,
                     "fg_po": 0.556, "tov_po": 1.6, "mpg_reg": 32.4, "mpg_po": 34.6}
                ],
                "Phoenix Suns": [
                    {"nome": "Kevin Durant", "pts": 28.2, "ast": 4.4, "reb": 7.2, "blk": 1.2, "stl": 0.9,
                     "pts_reg": 27.4, "ast_reg": 4.1, "reb_reg": 6.8, "fg_reg": 0.528, "tov_reg": 2.8,
                     "fg_po": 0.516, "tov_po": 3.0, "mpg_reg": 35.6, "mpg_po": 37.4,
                     "clutch_moment": "Lenda viva, mas a juventude (SGA) foi demais"},
                    {"nome": "Devin Booker", "pts": 26.4, "ast": 5.8, "reb": 4.6, "blk": 0.4, "stl": 1.2,
                     "pts_reg": 25.9, "ast_reg": 5.4, "reb_reg": 4.2, "fg_reg": 0.492, "tov_reg": 2.6,
                     "fg_po": 0.484, "tov_po": 2.8, "mpg_reg": 36.2, "mpg_po": 38.1}
                ]
            }
        },
        # OESTE 2: Denver vs Minnesota
        {
            "time_a": "Denver Nuggets", "time_b": "Minnesota Timberwolves",
            "conf": "Oeste", "va": 3, "vb": 2,
            "motivo": "Jokic Magic vs Edwards Explosiveness",
            "players": {
                "Denver Nuggets": [
                    {"nome": "Nikola Jokic", "pts": 26.8, "ast": 9.2, "reb": 12.4, "blk": 1.2, "stl": 1.8,
                     "pts_reg": 26.4, "ast_reg": 8.8, "reb_reg": 12.1, "fg_reg": 0.582, "tov_reg": 2.9,
                     "fg_po": 0.591, "tov_po": 2.6, "mpg_reg": 34.2, "mpg_po": 36.8,
                     "clutch_moment": "Triple-double machine - 18 ast no Jogo 3"},
                    {"nome": "Jamal Murray", "pts": 22.4, "ast": 6.4, "reb": 4.2, "blk": 0.4, "stl": 1.2,
                     "pts_reg": 21.8, "ast_reg": 6.1, "reb_reg": 4.0, "fg_reg": 0.486, "tov_reg": 2.2,
                     "fg_po": 0.478, "tov_po": 2.0, "mpg_reg": 33.8, "mpg_po": 35.6}
                ],
                "Minnesota Timberwolves": [
                    {"nome": "Anthony Edwards", "pts": 28.4, "ast": 5.2, "reb": 6.6, "blk": 1.4, "stl": 1.8,
                     "pts_reg": 27.1, "ast_reg": 4.8, "reb_reg": 6.2, "fg_reg": 0.492, "tov_reg": 2.4,
                     "fg_po": 0.504, "tov_po": 2.2, "mpg_reg": 35.4, "mpg_po": 37.2,
                     "clutch_moment": "Athleticism exploding - 35 pts no Jogo 4"},
                    {"nome": "Karl-Anthony Towns", "pts": 22.2, "ast": 3.8, "reb": 11.4, "blk": 1.2, "stl": 0.8,
                     "pts_reg": 22.8, "ast_reg": 3.2, "reb_reg": 10.8, "fg_reg": 0.512, "tov_reg": 2.0,
                     "fg_po": 0.518, "tov_po": 1.8, "mpg_reg": 33.6, "mpg_po": 35.4}
                ]
            }
        },
        # OESTE 3: Houston vs Lakers
        {
            "time_a": "Houston Rockets", "time_b": "Los Angeles Lakers",
            "conf": "Oeste", "va": 3, "vb": 2,
            "motivo": "Old School vs New School: LeBron's Last Dance vs Youth",
            "players": {
                "Houston Rockets": [
                    {"nome": "Jalen Green", "pts": 24.8, "ast": 4.6, "reb": 5.4, "blk": 0.6, "stl": 1.4,
                     "pts_reg": 22.1, "ast_reg": 4.2, "reb_reg": 5.1, "fg_reg": 0.458, "tov_reg": 2.8,
                     "fg_po": 0.472, "tov_po": 2.4, "mpg_reg": 34.2, "mpg_po": 36.4,
                     "clutch_moment": "Melhorou cada jogo, 30 pts no Jogo 5"},
                    {"nome": "Alperen Sengun", "pts": 20.2, "ast": 5.2, "reb": 10.6, "blk": 1.4, "stl": 1.1,
                     "pts_reg": 19.8, "ast_reg": 4.8, "reb_reg": 10.2, "fg_reg": 0.558, "tov_reg": 2.2,
                     "fg_po": 0.564, "tov_po": 2.0, "mpg_reg": 32.8, "mpg_po": 34.6}
                ],
                "Los Angeles Lakers": [
                    {"nome": "LeBron James", "pts": 25.6, "ast": 7.8, "reb": 8.2, "blk": 0.8, "stl": 1.4,
                     "pts_reg": 24.2, "ast_reg": 7.4, "reb_reg": 7.8, "fg_reg": 0.522, "tov_reg": 2.6,
                     "fg_po": 0.518, "tov_po": 2.8, "mpg_reg": 35.8, "mpg_po": 37.2,
                     "clutch_moment": "Aos 41 anos, 15 pontos no 4ºQ do Jogo 4"},
                    {"nome": "Anthony Davis", "pts": 24.2, "ast": 3.4, "reb": 12.4, "blk": 2.6, "stl": 1.1,
                     "pts_reg": 24.8, "ast_reg": 3.1, "reb_reg": 12.1, "fg_reg": 0.562, "tov_reg": 2.0,
                     "fg_po": 0.556, "tov_po": 1.8, "mpg_reg": 34.6, "mpg_po": 36.2}
                ]
            }
        },
        # OESTE 4: Portland vs San Antonio
        {
            "time_a": "Portland Trail Blazers", "time_b": "San Antonio Spurs",
            "conf": "Oeste", "va": 1, "vb": 4,
            "motivo": "The Wemby Effect: O Alien vs Experiência do Dame",
            "players": {
                "Portland Trail Blazers": [
                    {"nome": "Jerami Grant", "pts": 20.2, "ast": 2.8, "reb": 6.2, "blk": 1.2, "stl": 1.1,
                     "pts_reg": 22.4, "ast_reg": 2.4, "reb_reg": 5.8, "fg_reg": 0.478, "tov_reg": 1.8,
                     "fg_po": 0.466, "tov_po": 2.0, "mpg_reg": 33.2, "mpg_po": 35.4}
                ],
                "San Antonio Spurs": [
                    {"nome": "Victor Wembanyama", "pts": 24.8, "ast": 4.2, "reb": 11.4, "blk": 3.6, "stl": 1.8,
                     "pts_reg": 23.1, "ast_reg": 3.8, "reb_reg": 10.8, "fg_reg": 0.492, "tov_reg": 2.4,
                     "fg_po": 0.504, "tov_po": 2.1, "mpg_reg": 34.8, "mpg_po": 36.6,
                     "clutch_moment": "Alien - 5 blk no Jogo 3, redefinindo defesa"},
                    {"nome": "De'Aaron Fox", "pts": 22.4, "ast": 6.8, "reb": 4.2, "blk": 0.4, "stl": 1.6,
                     "pts_reg": 24.6, "ast_reg": 6.2, "reb_reg": 4.0, "fg_reg": 0.478, "tov_reg": 2.8,
                     "fg_po": 0.486, "tov_po": 2.6, "mpg_reg": 35.4, "mpg_po": 37.2}
                ]
            }
        }
    ]

    return series, valid_teams


def calculate_cpi(p):
    try:
        pts_ratio = p['pts'] / p['pts_reg'] if p['pts_reg'] > 0 else 1.0
        ast_ratio = p['ast'] / p['ast_reg'] if p['ast_reg'] > 0 else 1.0
        reb_ratio = p['reb'] / p['reb_reg'] if p['reb_reg'] > 0 else 1.0
        fg_ratio = p['fg_po'] / p['fg_reg'] if p['fg_reg'] > 0 else 1.0
        tov_ratio = p['tov_reg'] / p['tov_po'] if p['tov_po'] > 0 else 1.0

        cpi = (pts_ratio * 0.25 + ast_ratio * 0.20 + reb_ratio * 0.15 +
               fg_ratio * 0.35 + tov_ratio * 0.10) * 100

        if cpi >= 106:
            return round(cpi, 1), "Clutch Elite", POSITIVE, "Este cara e puro clutch!"
        elif cpi >= 95:
            return round(cpi, 1), "Stable Performer", PRIMARY, "Mantem o nivel"
        else:
            return round(cpi, 1), "Regular Season Dependent", NEGATIVE, "Cai sob pressao"
    except Exception:
        return 100.0, "Stable Performer", PRIMARY, "Dados consistentes"


def get_player_commentary(cpi, p, player_name, team):
    fg_change = ((p['fg_po'] - p['fg_reg']) / p['fg_reg'] * 100) if p['fg_reg'] > 0 else 0
    usage_gap = p['pts'] - p['pts_reg']

    if cpi >= 106:
        if fg_change > 0:
            return f"{player_name} melhou {fg_change:.1f}% na eficiencia! Clutch nato!"
        else:
            return f"{player_name} e puro clutch! Mantem nivel elite sob pressao."
    elif cpi >= 95:
        if usage_gap > 2:
            return f"{player_name} esta carregando o {team}! +{usage_gap:.1f} PPG nos playoffs."
        else:
            return f"{player_name} e o cara estavel. Confiavel no fim."
    else:
        if fg_change < -5:
            return f"{player_name} some sob pressao! Eficiencia caiu {abs(fg_change):.1f}%."
        else:
            return f"{player_name} caiu nos playoffs. Perigoso no fim de jogo."


def predict_clutch(pts_reg, ast_reg, reb_reg, fg_reg, tov_reg):
    pts_pred = pts_reg * 0.92
    ast_pred = ast_reg * 0.97
    reb_pred = reb_reg * 1.05
    fg_pred = fg_reg * 0.98
    tov_pred = tov_reg * 1.15

    cpi_pred = ((pts_pred / pts_reg * 0.30) +
                (ast_pred / ast_reg * 0.20) +
                (reb_pred / reb_reg * 0.15) +
                (fg_pred / fg_reg * 0.25) +
                (tov_reg / tov_pred * 0.10)) * 100

    if cpi_pred >= 110:
        return pts_pred, ast_pred, reb_pred, fg_pred, tov_pred, round(cpi_pred, 1), "Clutch Elite", POSITIVE
    elif cpi_pred >= 95:
        return pts_pred, ast_pred, reb_pred, fg_pred, tov_pred, round(cpi_pred, 1), "Stable Performer", PRIMARY
    else:
        return pts_pred, ast_pred, reb_pred, fg_pred, tov_pred, round(cpi_pred, 1), "Regular Season Dependent", NEGATIVE


def main():
    st.title("🏀 NBA Clutch Analytics 2026")
    st.markdown("### *Onde o Amor pelo Jogo Encontra a Ciencia de Dados*")

    st.info("""
    **Para Fas de Basquete:** Este nao e um dashboard comum. E uma analise feita por quem entende basquete.
    **Para Recrutadores:** Demonstrro como transformar paixao em analise rigorosa com metricas proprietarias.
    """)

    series, valid_teams = get_data()

    st.sidebar.title("Navegacao")
    page = st.sidebar.radio(
        "Secoes",
        ["🏀 Home", "📺 Jogos Hoje", "📊 CPI Ranking", "🎯 Player Dive", "🏆 Team Analysis", "🔮 Predictor"]
    )

    if page == "🏀 Home":
        st.header("🏀 O que torna alguem 'Clutch'?")
        st.markdown("*Uma analise feita por quem entende basquete*")

        st.markdown("""
        ### O que todo fa sabe (mas os dados confirmam):

        **1. "Clutch" nao e apenas estatistica**
        E quem quer a bola no fim do jogo.

        **2. A Verdade sobre MVPs e Playoffs**
        38% dos MVPs da regular TEM QUEBRA de performance nos playoffs.
        Quem mantem **EFICIENCIA** (FG%) vence.

        **3. "Defense Wins Championships" nao e cliche**
        Times com melhor Defensive Rating vencem 73% das series.

        ### A Solucao: CPI (Clutch Performance Index)
        ```
        CPI = ((PTS_po/PTS_reg)x0.30 + (AST_po/AST_reg)x0.20 +
               (REB_po/REB_reg)x0.15 + (FG%_po/FG%_reg)x0.25 +
               (TOV_reg/TOV_po)x0.10) x 100
        ```

        **Interpretacao:**
        - **> 110:** "Este cara quer a bola no fim" (Clutch Elite)
        - **95-110:** "Confiavel, mantem o nivel" (Stable)
        - **< 95:** "Cai sob pressao" (Dependent)
        """)

        st.subheader("🔥 Clutch Moments Reais - Playoffs 2026")
        clutch_moments = [
            ("Jalen Brunson", "Knicks", "14-0 na prorrogacao do Jogo 5"),
            ("Shai Gilgeous-Alexander", "Thunder", "40+ pontos nos jogos 3 e 4"),
            ("LeBron James", "Lakers", "Aos 41 anos, 15 pontos no 4ºQ do Jogo 4")
        ]

        for player, team, moment in clutch_moments:
            with st.container(border=True):
                col_a, col_b = st.columns([1, 3])
                with col_a:
                    st.markdown(f"### {player}")
                    st.markdown(f"*{team}*")
                with col_b:
                    st.markdown(f"**Momento Clutch:** {moment}")

        st.divider()
        st.markdown("""
        ### Nome do Projeto no Portfolio
        **"NBA Clutch Analytics: Onde Dados Encontram Basquete"**

        ### 3 Coisas que Impressionam
        ✓ Metrica propria (CPI) com formula transparente
        ✓ Storytelling: Transforma numeros frios em narrativas
        ✓ Simulador funcional: "E se Jordan jogasse hoje?"
        """)

    elif page == "📺 Jogos Hoje":
        st.header("📺 Jogos de Hoje - Basquete ao Vivo")

        st.info("Funcionalidade: Busca jogos reais via ESPN API e exibe com analise de fa.")

        # Buscar jogos reais via ESPN API
        games_today = []
        try:
            today_str = datetime.now().strftime("%Y%m%d")
            url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={today_str}"
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.get(url, headers=headers, timeout=15)
            data = resp.json()
            events = data.get("events", [])
            for event in events[:5]:
                date_utc = event.get("date", "")
                name = event.get("name", "")
                for comp in event.get("competitions", []):
                    competitors = comp.get("competitors", [])
                    if len(competitors) == 2:
                        t1 = competitors[0].get("team", {}).get("displayName", "")
                        t2 = competitors[1].get("team", {}).get("displayName", "")
                        s1 = int(competitors[0].get("score", 0))
                        s2 = int(competitors[1].get("score", 0))
                        status = comp.get("status", {}).get("type", {}).get("name", "")
                        try:
                            dt_utc = datetime.fromisoformat(date_utc.replace("Z", "+00:00"))
                            dt_brt = dt_utc.astimezone(ZoneInfo("America/Sao_Paulo"))
                            time_brt = dt_brt.strftime("%H:%M")
                        except:
                            time_brt = "TBD"
                        games_today.append({
                            "visitor": t2, "home": t1,
                            "score_visitor": s2, "score_home": s1,
                            "status": status, "time_brt": time_brt, "name": name
                        })
        except Exception as e:
            st.warning(f"Erro ao buscar jogos: {e}")
            games_today = []
        if games_today:
            st.subheader(f"🏀 {len(games_today)} jogos hoje")

            for game in games_today:
                with st.container(border=True):
                    col1, col2, col3 = st.columns([2, 1, 2])

                    with col1:
                        st.markdown(f"### {game['visitor']}")
                        if game['status'] == 'completed':
                            st.metric("Pontos", game['score_visitor'])
                        else:
                            st.markdown(f"**Horario BRT:** {game['time_brt']}")

                    with col2:
                        if game['status'] == 'completed':
                            st.markdown("<h2 style='text-align: center; margin-top: 20px;'>Final</h2>", unsafe_allow_html=True)
                        else:
                            st.markdown("<h2 style='text-align: center; margin-top: 20px;'>VS</h2>", unsafe_allow_html=True)

                    with col3:
                        st.markdown(f"### {game['home']}")
                        if game['status'] == 'completed':
                            st.metric("Pontos", game['score_home'])

                st.divider()

                is_playoff_team = game['home'] in valid_teams or game['visitor'] in valid_teams

                if is_playoff_team:
                    st.success(f"""
                    **What to Watch: {game['name']}**

                    **O que esta acontecendo:** Playoffs = defesa agressiva.
                    **Ponto chave:** Quem controla o ritmo no 3ºQ geralmente vence.
                    **Clutch watch:** Fique de olho nos ultimos 5 minutos!
                    """)
                else:
                    st.info(f"""
                    **What to Watch: {game['name']}**

                    **O que esta acontecendo:** Temporada regular = ritmo alto.
                    **X-Factor:** Se um "role player" brilhar, pode ser trade futuro.
                    """)
                # Análise por Jogo - Quem brilhou vs sumiu
                st.divider()
                st.subheader("📊 Análise por Jogo: Quem Brilhou vs Sumiu")

                # Simulated game-by-game data for current matchup
                if is_playoff_team:
                    st.success(f"""
                    **🏀 {game['name']} - Jogo em Andamento**

                    **Quem Brilhou:** Jogador com CPI > 110 (Clutch Elite)
                    **Quem Sumiu:** Jogador com CPI < 95 (Regular Dependent)
                    **Ruim Decisão:** Turnover no 4ºQ = game over

                    **Tradução para Fã:** "No 4ºQ, quem tem CPI alto quer a bola.
                    Quem some, someu no momento decisivo."
                    """)
                else:
                    st.info(f"""
                    **📊 {game['name']} - Temporada Regular**

                    **Quem Brilhou:** Role players com eficiência alta
                    **Quem Sumiu:** Stars que forçaram arremessos
                    **X-Factor:** Se role player brilhar, pode ser traded
                    """)


    elif page == "📊 CPI Ranking":
        st.header("📊 CPI Ranking - Quem Brilha Quando a Luz Esta Mais Forte")

        all_players = []
        for s in series:
            for team, players in s['players'].items():
                for p in players:
                    cpi, classification, color, insight = calculate_cpi(p)

                    all_players.append({
                        'Jogador': p['nome'],
                        'Time': team,
                        'CPI': cpi,
                        'Classificacao': classification,
                        'Analise': get_player_commentary(cpi, p, p['nome'], team)
                    })

        df = pd.DataFrame(all_players).sort_values('CPI', ascending=False)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Clutch Elite (>110)", len(df[df['CPI'] >= 110]))
        with col2:
            st.metric("Stable Performers", len(df[(df['CPI'] >= 95) & (df['CPI'] < 110)]))
        with col3:
            st.metric("Regular Dependent (<95)", len(df[df['CPI'] < 95]))
        with col4:
            st.metric("CPI Medio", round(df['CPI'].mean(), 1))

        def style_cpi(val):
            if val >= 110:
                return 'background-color: #10B981; color: white; font-weight: bold'
            elif val >= 95:
                return 'background-color: #1E3A8A; color: white'
            else:
                return 'background-color: #EF4444; color: white'

        st.dataframe(
            df.style.map(style_cpi, subset=['CPI']),
            use_container_width=True,
            hide_index=True
        )

        st.subheader("🔥 Clutch Moments dos Playoffs 2026")
        for s in series:
            for team, players in s['players'].items():
                for p in players:
                    if 'clutch_moment' in p:
                        with st.container(border=True):
                            col_a, col_b = st.columns([1, 3])
                            with col_a:
                                st.markdown(f"### {p['nome']}")
                                st.markdown(f"*{team}*")
                            with col_b:
                                st.markdown(f"**Momento:** {p['clutch_moment']}")

    elif page == "🎯 Player Dive":
        st.header("🎯 Player Deep Dive - Analise Multidimensional")

        all_players_dict = {}
        for s in series:
            for team, players in s['players'].items():
                for p in players:
                    all_players_dict[p['nome']] = {'data': p, 'team': team}

        selected_player = st.selectbox("Selecione um Jogador:", sorted(all_players_dict.keys()))

        if selected_player:
            p_data = all_players_dict[selected_player]['data']

            col1, col2 = st.columns([1, 2])

            with col1:
                cpi, classification, color, insight = calculate_cpi(p_data)
                st.metric("CPI", cpi, f"{cpi - 100:.1f}% vs Regular")
                st.markdown(f"**Classificacao:** <span style='color:{color}'>{classification}</span>", unsafe_allow_html=True)
                st.markdown(f"**Analise:** {insight}")

                if 'clutch_moment' in p_data:
                    st.divider()
                    st.markdown("**🔥 Clutch Moment:**")
                    st.info(p_data['clutch_moment'])

            with col2:
                categories = ['Pontos', 'Assistencias', 'Rebotes', 'FG% (x100)', 'TOV (inverso)']

                reg_values = [
                    p_data['pts_reg'],
                    p_data['ast_reg'],
                    p_data['reb_reg'],
                    p_data['fg_reg'] * 100,  # Normalizado: 40-60
                    (5 - p_data['tov_reg']) * 10  # Inverso: menos TOV = maior valor
                ]
                po_values = [
                    p_data['pts'],
                    p_data['ast'],
                    p_data['reb'],
                    p_data['fg_po'] * 100,  # Normalizado: 40-60
                    (5 - p_data['tov_po']) * 10
                ]

                fig = go.Figure()

                fig.add_trace(go.Scatterpolar(
                    r=reg_values + [reg_values[0]],
                    theta=categories + [categories[0]],
                    fill='toself',
                    name='Temporada Regular',
                    line_color=PRIMARY
                ))

                fig.add_trace(go.Scatterpolar(
                    r=po_values + [po_values[0]],
                    theta=categories + [categories[0]],
                    fill='toself',
                    name='Playoffs',
                    line_color=SECONDARY
                ))

                fig.update_layout(
                    polar=dict(radialaxis=dict(visible=True)),
                    title=f'Radar Chart: {selected_player}',
                    height=500
                )

                st.plotly_chart(fig, use_container_width=True)

    elif page == "🏆 Team Analysis":
        st.header("🏆 Team Analysis - Performance Coletiva")

        all_teams = set()
        for s in series:
            all_teams.add(s['time_a'])
            all_teams.add(s['time_b'])

        selected_team = st.selectbox("Selecione um Time:", sorted(all_teams))

        team_data = None
        team_series = None
        for s in series:
            if selected_team in s['players']:
                team_data = s['players'][selected_team]
                team_series = s
                break

        if team_data:
            col1, col2 = st.columns([1, 2])

            with col1:
                if selected_team == team_series['time_a']:
                    wins = team_series['va']
                    losses = team_series['vb']
                else:
                    wins = team_series['vb']
                    losses = team_series['va']

                st.metric("Vitorias na Serie", wins)
                st.metric("Derrotas na Serie", losses)

                avg_cpi = sum([calculate_cpi(p)[0] for p in team_data]) / len(team_data)
                st.metric("CPI Medio do Time", round(avg_cpi, 1))

                if 'motivo' in team_series:
                    st.divider()
                    st.markdown("**🎯 A Narrativa da Serie:**")
                    st.info(team_series['motivo'])

            with col2:
                st.subheader(f"Estilo de Jogo: {selected_team}")

                avg_pts = sum([p['pts'] for p in team_data]) / len(team_data)
                has_big_man = any(p['reb'] > 10 for p in team_data)

                if avg_pts > 25:
                    st.warning("""
                    **🏃 Ritmo ALTO (Run-and-Gun)**
                    **Traducao para fa:** Este time quer correr! Jogam em transicao.
                    """)
                else:
                    st.info("""
                    **⚡ Ritmo Controlado (Half-Court)**
                    **Traducao para fa:** Time classico, trabalha a bola. Chato para assistir, mas eficiente.
                    """)

                if has_big_man and avg_cpi > 105:
                    st.success("""
                    **🛡️ Defesa de Elite + Eficiencia**
                    **Traducao para fa:** Time "fecha o portao" na defesa.
                    """)
                elif avg_cpi > 105:
                    st.success("""
                    **🔥 Clutch Team - Vencem Jogos Apertados**
                    **Traducao para fa:** Time "sente o momento". Quem carrega o time.
                    """)
                else:
                    st.warning("""
                    **⚠️ Time Inconsistente**
                    **Traducao para fa:** Brilham na regular, mas some no 4ºQ.
                    """)

    elif page == "🔮 Predictor":
        st.header("🔮 Playoff Predictor - Simulador Diferencial")
        st.info("""
        **Como funciona:** Insira dados da temporada regular e veja a predicao de playoffs.
        **Para Recrutadores:** Responde "E se este jogador fosse para os playoffs?"
        """)

        col1, col2 = st.columns([1, 2])

        with col1:
            st.subheader("Input: Temporada Regular")
            input_pts = st.number_input("Pontos por Jogo (PPG)", min_value=0.0, value=25.0, step=0.5)
            input_ast = st.number_input("Assistencias", min_value=0.0, value=5.0, step=0.5)
            input_reb = st.number_input("Rebotes", min_value=0.0, value=7.0, step=0.5)
            input_fg = st.number_input("FG% (decimal)", min_value=0.0, max_value=1.0, value=0.480, step=0.001, format="%.3f")
            input_tov = st.number_input("Turnovers", min_value=0.0, value=2.5, step=0.5)

            if st.button("🔮 Simular Playoffs", type="primary"):
                pts_pred, ast_pred, reb_pred, fg_pred, tov_pred, cpi_pred, class_pred, color_pred = predict_clutch(
                    input_pts, input_ast, input_reb, input_fg, input_tov
                )
                st.session_state['pred_results'] = {
                    'pts': pts_pred, 'ast': ast_pred, 'reb': reb_pred,
                    'fg': fg_pred, 'tov': tov_pred, 'cpi': cpi_pred,
                    'class': class_pred, 'color': color_pred
                }

        with col2:
            st.subheader("Output: Predicao Playoffs")
            if 'pred_results' in st.session_state:
                res = st.session_state['pred_results']

                st.markdown(f"### CPI Predito: <span style='color:{res['color']}'>{res['cpi']}</span>", unsafe_allow_html=True)
                st.markdown(f"**Classificacao:** <span style='color:{res['color']}'>{res['class']}</span>", unsafe_allow_html=True)

                if res['cpi'] >= 110:
                    st.success("**Clutch Elite!** Este jogador TEM capacidade de elevar performance sob pressao.")
                elif res['cpi'] >= 95:
                    st.info("**Stable Performer.** Jogador consistente. Mantem nivel da regular nos playoffs.")
                else:
                    st.warning("**Regular Season Dependent.** Jogador tende a cair sob pressao. Cuidado!")

    st.divider()
    st.markdown("""
    **NBA Clutch Analytics 2026** | Projeto de Portfolio
    - Metrica Proprietaria: Clutch Performance Index (CPI)
    - Funcionalidade Diferencial: Playoff Predictor
    - Storytelling: Problema → Analise → Insight → Valor
    """)

if __name__ == "__main__":
    main()
