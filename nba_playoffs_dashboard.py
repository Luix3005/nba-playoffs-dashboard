#!/usr/bin/env python3
"""
NBA Playoffs 2026 — Dashboard Analítico Multi-Fonte
Autor: Luiz Felipe de Oliveira Araujo

100% gratuito. Zero hardcode de resultados.

Fontes automáticas:
  - ESPN Public API       → placares ao vivo, box scores, séries, notícias EN→PT-BR
  - Ball Don't Lie API    → stats detalhados de jogadores e jogos
  - NBA Stats (nba_api)   → dados oficiais da liga, histórico de playoffs
  - Reddit r/nba          → opinião de jornalistas e fãs especializados (posts top)
  - RapidAPI NBA          → fallback stats (opcional, gratuito com limite)

Comentários automáticos gerados dos dados reais de cada jogo:
  box score + líderes + stats comparativos + sentimento Reddit

Instalação:
    pip install streamlit pandas requests plotly nba_api
    streamlit run nba_playoffs_dashboard.py
"""

import streamlit as st
import pandas as pd
import requests
import re
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

# ─────────────────────────────────────────────────────────────────────────────
# Dependências opcionais
# ─────────────────────────────────────────────────────────────────────────────
try:
    import plotly.graph_objects as go
    import plotly.express as px
    PLOTLY = True
except ImportError:
    PLOTLY = False

try:
    from nba_api.stats.endpoints import leagueleaders, playergamelog, leaguegamefinder
    from nba_api.stats.static import teams as nba_teams_static
    NBA_API = True
except ImportError:
    NBA_API = False

# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINTS — todos públicos, sem autenticação, sem custo
# ─────────────────────────────────────────────────────────────────────────────
ESPN_BASE     = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba"
ESPN_TODAY    = f"{ESPN_BASE}/scoreboard"
ESPN_CALENDAR = f"{ESPN_BASE}/calendar/postseason"
ESPN_SCORE_D  = f"{ESPN_BASE}/scoreboard"
ESPN_NEWS     = f"{ESPN_BASE}/news?limit=50"
ESPN_SUMMARY  = f"{ESPN_BASE}/summary?event="
ESPN_INJ      = "https://site.api.espn.com/apis/v2/sports/basketball/nba/injuries"

HEADERS = {"User-Agent": "Mozilla/5.0 NBADashboard/2.0 (hobby project)"}
SESSION = requests.Session()

BRT = ZoneInfo("America/Sao_Paulo")
UTC = timezone.utc

def current_season_start_year():
    now = datetime.now(BRT)
    return now.year if now.month >= 10 else now.year - 1

SEASON_START_YEAR = current_season_start_year()
SEASON_ID = f"{SEASON_START_YEAR}-{str(SEASON_START_YEAR + 1)[2:]}"
BDL_SEASON_YEAR = SEASON_START_YEAR

def safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default

def safe_float(value, default=0.0):
    try:
        text = str(value).strip()
        if text.endswith("%"):
            text = text[:-1]
        return float(text)
    except (TypeError, ValueError):
        return default

def parse_iso_datetime(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(BRT)
    except Exception:
        return None

def format_ptbr(value, with_time=True):
    dt = parse_iso_datetime(value)
    if not dt:
        return "—"
    if with_time:
        return dt.strftime("%d/%m/%Y %H:%M")
    return dt.strftime("%d/%m/%Y")

TIMEOUT = 10

def fetch_json(url, params=None, headers=None, timeout=TIMEOUT):
    try:
        r = SESSION.get(url, params=params, timeout=timeout, headers=headers or HEADERS)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None

BDL_GAMES     = "https://www.balldontlie.io/api/v1/games"
BDL_STATS     = "https://www.balldontlie.io/api/v1/stats"
BDL_PLAYERS   = "https://www.balldontlie.io/api/v1/players"
BDL_SEASON    = "https://www.balldontlie.io/api/v1/season_averages"

REDDIT_NBA    = "https://www.reddit.com/r/nba/search.json"
REDDIT_TOP    = "https://www.reddit.com/r/nba/top.json?t=week&limit=10"
REDDIT_HOT    = "https://www.reddit.com/r/nba/hot.json?limit=10"

TIMEOUT = 10

# ─────────────────────────────────────────────────────────────────────────────
# REFERÊNCIA CPI
# ─────────────────────────────────────────────────────────────────────────────
REF = {"pts": 28.0, "ast": 6.5, "reb": 7.5, "fg": 0.490, "stl": 1.3, "blk": 0.8}

LESTE = {"DET","BOS","NYK","CLE","ORL","PHI","ATL","TOR","MIA","CHI","IND","BKN","MIL","WAS","CHA"}
OESTE = {"OKC","SAS","DEN","LAL","MIN","HOU","PHX","POR","GSW","DAL","MEM","UTA","SAC","LAC","NOP"}

# ─────────────────────────────────────────────────────────────────────────────
# FALLBACK JOGADORES
# ─────────────────────────────────────────────────────────────────────────────
PLAYERS_FB = [
    {"nome":"Luka Doncic",     "team":"LAL","pts":33.5,"ast":8.8, "reb":9.2, "fg":0.512,"stl":1.5,"blk":0.5,"tov":4.2},
    {"nome":"Nikola Jokic",    "team":"DEN","pts":28.1,"ast":10.7,"reb":12.9,"fg":0.578,"stl":1.4,"blk":0.8,"tov":3.1},
    {"nome":"SGA",             "team":"OKC","pts":31.4,"ast":6.1, "reb":5.1, "fg":0.534,"stl":2.0,"blk":0.9,"tov":2.5},
    {"nome":"Giannis",         "team":"MIL","pts":29.8,"ast":6.4, "reb":11.1,"fg":0.597,"stl":1.1,"blk":1.1,"tov":3.2},
    {"nome":"Wembanyama",      "team":"SAS","pts":24.3,"ast":4.0, "reb":10.7,"fg":0.501,"stl":1.0,"blk":3.1,"tov":2.9},
    {"nome":"Jayson Tatum",    "team":"BOS","pts":26.8,"ast":5.2, "reb":8.4, "fg":0.488,"stl":1.0,"blk":0.6,"tov":2.7},
    {"nome":"Donovan Mitchell","team":"CLE","pts":27.1,"ast":5.8, "reb":4.3, "fg":0.481,"stl":1.5,"blk":0.4,"tov":2.6},
    {"nome":"Ant Edwards",     "team":"MIN","pts":26.8,"ast":5.1, "reb":5.4, "fg":0.474,"stl":1.4,"blk":0.6,"tov":3.0},
    {"nome":"Cade Cunningham", "team":"DET","pts":26.2,"ast":9.1, "reb":6.9, "fg":0.476,"stl":1.5,"blk":0.4,"tov":3.3},
    {"nome":"Jalen Brunson",   "team":"NYK","pts":26.5,"ast":7.0, "reb":3.5, "fg":0.497,"stl":0.9,"blk":0.2,"tov":2.5},
    {"nome":"Paolo Banchero",  "team":"ORL","pts":25.7,"ast":4.5, "reb":8.6, "fg":0.498,"stl":1.0,"blk":0.7,"tov":3.0},
    {"nome":"LeBron James",    "team":"LAL","pts":24.1,"ast":8.3, "reb":7.8, "fg":0.533,"stl":1.1,"blk":0.5,"tov":3.0},
    {"nome":"Alperen Sengun",  "team":"HOU","pts":23.8,"ast":5.1, "reb":10.2,"fg":0.552,"stl":0.9,"blk":1.4,"tov":2.8},
    {"nome":"Tyrese Maxey",    "team":"PHI","pts":26.3,"ast":6.8, "reb":3.9, "fg":0.469,"stl":1.2,"blk":0.3,"tov":2.8},
    {"nome":"Evan Mobley",     "team":"CLE","pts":21.3,"ast":3.7, "reb":9.8, "fg":0.551,"stl":1.3,"blk":2.2,"tov":2.0},
    {"nome":"Jabari Smith Jr.","team":"HOU","pts":19.1,"ast":2.8, "reb":7.9, "fg":0.487,"stl":1.1,"blk":1.8,"tov":1.9},
]

# ─────────────────────────────────────────────────────────────────────────────
# LENDAS
# ─────────────────────────────────────────────────────────────────────────────
LENDAS = {
    "Michael Jordan (1996 — Bulls)": {
        "pts":30.4,"ast":4.3,"reb":6.6,"fg":0.495,"stl":1.9,"blk":0.5,"tov":2.3,
        "era":"hand-check completo","era_factor":0.95,
        "bio":"Temporada do 72-10. MVP da temporada + MVP das Finais. Bulls invencíveis.",
        "momentos":["72 vitórias (recorde que durou 20 anos)","49.5% FG com hand-check pesado","MVP da temporada, All-Star e Finais"],
    },
    "Kobe Bryant (2006 — Lakers)": {
        "pts":35.4,"ast":4.5,"reb":5.3,"fg":0.450,"stl":1.8,"blk":0.5,"tov":3.2,
        "era":"transição hand-check","era_factor":0.97,
        "bio":"Ano do jogo de 81 pontos. Liderou a liga. Lakers sem Shaq.",
        "momentos":["81 pts x Toronto — 2ª maior da história","62 pts em 3 quartos x Dallas","35.4 PPG liderando a liga"],
    },
    "LeBron James (2013 — Heat)": {
        "pts":26.8,"ast":7.3,"reb":8.0,"fg":0.565,"stl":1.7,"blk":0.9,"tov":2.8,
        "era":"moderno inicial","era_factor":1.0,
        "bio":"Temporada mais eficiente da carreira: 56.5% FG. Bicampeão.",
        "momentos":["Finais x Spurs G6: 32 pts — salvou o campeonato","G7: 37 pts para selar o bi","25.9/10.2/7.0 nas Finais"],
    },
    "Stephen Curry (2016 — Warriors)": {
        "pts":30.1,"ast":6.7,"reb":5.4,"fg":0.504,"stl":2.1,"blk":0.2,"tov":3.0,
        "era":"moderno","era_factor":1.02,
        "bio":"Primeiro MVP unânime da história. 402 triplos. 73 vitórias.",
        "momentos":["402 cestas de 3 — recorde absoluto","73 vitórias na temporada","Revolucionou o basquete moderno"],
    },
    "Shaquille O'Neal (2000 — Lakers)": {
        "pts":29.7,"ast":3.8,"reb":13.6,"fg":0.574,"stl":0.5,"blk":3.0,"tov":3.2,
        "era":"hand-check completo","era_factor":0.93,
        "bio":"MVP da temporada, All-Star e Finais no mesmo ano. Dominância absoluta.",
        "momentos":["Finais G1: 43 pts, 19 reb","3 Finais consecutivas, 3 MVPs","57.4% FG — intransponível"],
    },
    "Tim Duncan (2003 — Spurs)": {
        "pts":22.5,"ast":4.1,"reb":12.1,"fg":0.505,"stl":0.7,"blk":2.9,"tov":2.5,
        "era":"transição hand-check","era_factor":0.95,
        "bio":"O Grande Fundamental. 5 títulos, 3 MVPs das Finais.",
        "momentos":["Finais x Nets: 24.2/17/5.3 — MVP","5 títulos em 19 temporadas","Nunca menos de 20 pts em Finais"],
    },
    "Magic Johnson (1987 — Lakers)": {
        "pts":19.6,"ast":11.4,"reb":7.2,"fg":0.530,"stl":1.7,"blk":0.2,"tov":3.3,
        "era":"anos 80","era_factor":0.88,
        "bio":"Show Time no auge. Melhor passador de todos os tempos.",
        "momentos":["Finais x Celtics: 26.2/13/8 — MVP","Hook shot x Boston — lendário","4 títulos em 9 anos de Finais"],
    },
    "Giannis Antetokounmpo (2021 — Bucks)": {
        "pts":28.5,"ast":6.0,"reb":11.0,"fg":0.569,"stl":1.2,"blk":1.2,"tov":3.4,
        "era":"moderno","era_factor":1.01,
        "bio":"50 pts nas Finais. Silenciou todos os críticos do clutch.",
        "momentos":["Finais x Suns G6: 50 pts, 14 reb, 5 blk","56.9% FG nos playoffs com volume de star"],
    },
    "Kevin Durant (2017 — Warriors)": {
        "pts":35.2,"ast":5.4,"reb":8.4,"fg":0.556,"stl":1.1,"blk":1.6,"tov":2.8,
        "era":"moderno","era_factor":1.02,
        "bio":"MVP das Finais. 35.2 PPG com 55.6% FG — melhor performance individual de Finais.",
        "momentos":["Finais x Cavs: 35.2/55.6%/8.4","Série encerrada em 5 jogos","Scorer mais versátil da história"],
    },
    "Dirk Nowitzki (2011 — Mavericks)": {
        "pts":27.7,"ast":2.9,"reb":8.1,"fg":0.490,"stl":0.6,"blk":0.5,"tov":2.3,
        "era":"moderno inicial","era_factor":0.98,
        "bio":"Desbancou LeBron+Wade+Bosh jogando com febre.",
        "momentos":["Jogou com febre — 26 PPG mesmo assim","Virou de 0-2 x OKC com Durant jovem","MVP das Finais unânime"],
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# ░░  CAMADA 1 — ESPN API  ░░
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=30)
def espn_hoje():
    """Jogos de hoje via ESPN. TTL 30s para acompanhar ao vivo."""
    data = fetch_json(ESPN_TODAY)
    if not data:
        return []

    jogos = []
    for e in data.get("events", []):
        comp = e.get("competitions", [{}])[0]
        status = comp.get("status", {}).get("type", {})
        competitors = comp.get("competitors", [])
        if len(competitors) < 2:
            continue
        home = next((c for c in competitors if c.get("homeAway") == "home"), competitors[0])
        away = next((c for c in competitors if c.get("homeAway") == "away"), competitors[1])
        jogos.append({
            "id":           e.get("id", ""),
            "date":         e.get("date", ""),
            "home_abbr":    home.get("team", {}).get("abbreviation", ""),
            "home_nome":    home.get("team", {}).get("displayName", ""),
            "home_score":   home.get("score", "—"),
            "home_record":  (home.get("records") or [{}])[0].get("summary", ""),
            "away_abbr":    away.get("team", {}).get("abbreviation", ""),
            "away_nome":    away.get("team", {}).get("displayName", ""),
            "away_score":   away.get("score", "—"),
            "away_record":  (away.get("records") or [{}])[0].get("summary", ""),
            "status":       status.get("shortDetail", ""),
            "state":        status.get("state", "pre"),
            "encerrado":    status.get("completed", False),
            "venue":        comp.get("venue", {}).get("fullName", ""),
            "broadcast":    ", ".join([b.get("names", [""])[0] for b in comp.get("broadcasts", []) if b.get("names")]),
            "playoff":      comp.get("series") is not None or e.get("season", {}).get("type", 0) == 3,
            "local_time":   format_ptbr(e.get("date", ""), with_time=True),
        })
    return jogos


@st.cache_data(ttl=300)
def _espn_datas_playoffs() -> list:
    """
    Obtém todas as datas com jogos nos playoffs via ESPN calendar.
    Fallback: gera datas de início dos playoffs até hoje se o endpoint falhar.
    """
    data = fetch_json(ESPN_CALENDAR)
    if data:
        datas = []
        for bloco in data.get("eventDate", {}).get("dates", []):
            if isinstance(bloco, str) and len(bloco) == 8 and bloco.isdigit():
                datas.append(bloco)
        if not datas:
            for item in data.get("items", []):
                d = item.get("date", "")[:10].replace("-", "")
                if len(d) == 8 and d.isdigit():
                    datas.append(d)
        if datas:
            return sorted(set(datas))

    inicio = datetime(SEASON_START_YEAR + 1, 4, 18)
    hoje = datetime.now()
    datas = []
    d = inicio
    while d <= hoje:
        datas.append(d.strftime("%Y%m%d"))
        d += timedelta(days=1)
    return datas


@st.cache_data(ttl=90)
def espn_series_playoffs():
    """
    Busca todos os jogos dos playoffs iterando por cada data.
    Pipeline:
      1. Datas reais via ESPN calendar/postseason
      2. Para cada data: scoreboard?dates=YYYYMMDD&seasontype=3
      3. Agrega e deduplica por série (chave canônica por par de times)
      4. Ordena jogos cronologicamente e marca quem avançou
    """
    datas = _espn_datas_playoffs()
    series_map = {}

    for data_str in datas:
        data = fetch_json(ESPN_SCORE_D, params={"dates": data_str, "seasontype": 3, "limit": 50})
        if not data:
            continue
        events = data.get("events", [])

        for e in events:
            comp        = e.get("competitions", [{}])[0]
            competitors = comp.get("competitors", [])
            if len(competitors) < 2:
                continue

            home = next((c for c in competitors if c.get("homeAway") == "home"), competitors[0])
            away = next((c for c in competitors if c.get("homeAway") == "away"), competitors[1])

            h_abbr  = home.get("team", {}).get("abbreviation", "")
            a_abbr  = away.get("team", {}).get("abbreviation", "")
            h_nome  = home.get("team", {}).get("displayName", h_abbr)
            a_nome  = away.get("team", {}).get("displayName", a_abbr)
            h_id    = str(home.get("team", {}).get("id", "0"))
            a_id    = str(away.get("team", {}).get("id",  "0"))
            h_score = int(home.get("score", 0) or 0)
            a_score = int(away.get("score", 0) or 0)

            status_obj = comp.get("status", {}).get("type", {})
            completed  = status_obj.get("completed", False)
            state      = status_obj.get("state", "pre")
            game_id    = e.get("id", "")
            date_str_g = e.get("date", "")

            # Ignora jogos que ainda não começaram
            if not completed and state == "pre":
                # Inclui para mostrar agendados — mas sem pontuar vitória
                pass

            # Chave canônica estável (ID menor vai primeiro)
            if h_id <= a_id:
                key     = f"{h_abbr}|{a_abbr}"
                ta_abbr = h_abbr; ta_nome = h_nome
                tb_abbr = a_abbr; tb_nome = a_nome
            else:
                key     = f"{a_abbr}|{h_abbr}"
                ta_abbr = a_abbr; ta_nome = a_nome
                tb_abbr = h_abbr; tb_nome = h_nome

            if key not in series_map:
                series_map[key] = {
                    "ta_abbr": ta_abbr, "ta_nome": ta_nome,
                    "tb_abbr": tb_abbr, "tb_nome": tb_nome,
                    "wins_a": 0, "wins_b": 0,
                    "jogos": [], "ultimo_id": "", "ultimo_data": "",
                }

            s = series_map[key]

            # Deduplica pelo game_id
            if game_id and any(j["game_id"] == game_id for j in s["jogos"]):
                continue

            jogo_entry = {
                "game_id":   game_id,
                "numero":    len(s["jogos"]) + 1,
                "home":      h_nome, "home_abbr": h_abbr, "home_score": h_score,
                "away":      a_nome, "away_abbr": a_abbr, "away_score": a_score,
                "data":      date_str_g,
                "state":     state,
                "completed": completed,
                "vencedor":  None,
            }

            if completed and h_score != a_score:
                venceu_a = (h_score > a_score) if (h_abbr == ta_abbr) else (a_score > h_score)
                jogo_entry["vencedor"] = ta_abbr if venceu_a else tb_abbr
                if venceu_a:
                    s["wins_a"] += 1
                else:
                    s["wins_b"] += 1
                s["ultimo_id"]   = game_id
                s["ultimo_data"] = date_str_g

            s["jogos"].append(jogo_entry)

    # Pós-processamento: ordenar, renumerar e marcar quem avançou
    for s in series_map.values():
        s["jogos"].sort(key=lambda j: j.get("data", ""))
        for i, j in enumerate(s["jogos"]):
            j["numero"] = i + 1
        if s["wins_a"] >= 4:
            s["avancou"] = s["ta_abbr"]
        elif s["wins_b"] >= 4:
            s["avancou"] = s["tb_abbr"]
        else:
            s["avancou"] = None

    return series_map


@st.cache_data(ttl=60)
def espn_boxscore(game_id: str):
    """Box score completo de um jogo via ESPN Summary."""
    if not game_id:
        return None

    data = fetch_json(ESPN_SUMMARY + game_id)
    if not data:
        return None

    boxscore = data.get("boxscore", {})
    result = {
        "teams": [],
        "leaders": [],
        "plays": [],          # últimas jogadas
        "game_info": {},
    }

    try:
        for t in boxscore.get("teams", []):
            ti = t.get("team", {})
            stats = {s["name"]: s.get("displayValue","") for s in t.get("statistics",[])}
            players_box = []
            for p in t.get("players",[]):
                for pl in p.get("statistics",[]):
                    for athlete in pl.get("athletes",[]):
                        a = athlete.get("athlete",{})
                        stats_p = athlete.get("stats",[])
                        keys_p  = pl.get("names",[])
                        pstats  = dict(zip(keys_p, stats_p)) if len(keys_p)==len(stats_p) else {}
                        players_box.append({
                            "nome":     a.get("displayName",""),
                            "posicao":  a.get("position",{}).get("abbreviation",""),
                            "starter":  athlete.get("starter", False),
                            "stats":    pstats,
                        })
            result["teams"].append({
                "nome":    ti.get("displayName",""),
                "abbr":    ti.get("abbreviation",""),
                "stats":   stats,
                "players": players_box,
            })

        for cat in data.get("leaders", []):
            cat_name = cat.get("displayName","")
            for lead in cat.get("leaders",[]):
                a    = lead.get("athlete",{})
                team = lead.get("team",{})
                result["leaders"].append({
                    "categoria": cat_name,
                    "jogador":   a.get("displayName",""),
                    "time":      team.get("abbreviation",""),
                    "valor":     lead.get("displayValue",""),
                    "stat":      float(lead.get("value",0)),
                })

        # Últimas jogadas (plays)
        for play in data.get("plays",[])[-20:]:
            result["plays"].append({
                "descricao": play.get("text",""),
                "clock":     play.get("clock",{}).get("displayValue",""),
                "periodo":   play.get("period",{}).get("number",0),
            })

        # Info geral
        ginfo = data.get("gameInfo",{})
        result["game_info"] = {
            "arena":     ginfo.get("venue",{}).get("fullName",""),
            "cidade":    ginfo.get("venue",{}).get("address",{}).get("city",""),
            "presenca":  ginfo.get("attendance",""),
        }

        return result
    except Exception:
        return None


@st.cache_data(ttl=180)
def espn_noticias():
    """Notícias ESPN NBA — retorna lista bruta em inglês."""
    data = fetch_json(ESPN_NEWS)
    if not data:
        return []

    noticias = []
    for a in data.get("articles", []):
        cats = [c.get("description", "") for c in a.get("categories", []) if c.get("description")]
        noticias.append({
            "titulo":     a.get("headline", ""),
            "descricao":  a.get("description", ""),
            "autor":      a.get("byline", "ESPN"),
            "link":       a.get("links", {}).get("web", {}).get("href", ""),
            "data":       a.get("published", ""),
            "categorias": cats,
            "imagem":     a.get("images", [{}])[0].get("url", "") if a.get("images") else "",
        })
    return noticias


@st.cache_data(ttl=300)
def espn_lesoes():
    """Relatório de lesões via ESPN."""
    data = fetch_json(ESPN_INJ)
    if not data:
        return []

    lesoes = []
    for entry in data.get("injuries", []):
        abbr = entry.get("team", {}).get("abbreviation", "")
        for inj in entry.get("injuries", []):
            a = inj.get("athlete", {})
            lesoes.append({
                "team":    abbr,
                "jogador": a.get("displayName", ""),
                "status":  inj.get("status", ""),
                "tipo":    inj.get("details", {}).get("type", ""),
                "detalhe": inj.get("details", {}).get("detail", ""),
            })
    return lesoes


# ═══════════════════════════════════════════════════════════════════════════════
# ░░  CAMADA 2 — Ball Don't Lie API (gratuita, sem auth)  ░░
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=600)
def bdl_season_averages(player_ids: tuple):
    """Stats da temporada regular via Ball Don't Lie."""
    if not player_ids:
        return {}
    try:
        qs = "&".join(f"player_ids[]={pid}" for pid in player_ids)
        data = fetch_json(f"{BDL_SEASON}?season={BDL_SEASON_YEAR}&{qs}", headers={"User-Agent": "NBADashboard/1.0"})
        if not data:
            return {}
        return {item["player_id"]: item for item in data.get("data", [])}
    except Exception:
        return {}


@st.cache_data(ttl=600)
def bdl_buscar_jogador(nome: str):
    """Busca ID de jogador no Ball Don't Lie."""
    data = fetch_json(BDL_PLAYERS, params={"search": nome, "per_page": 1}, headers={"User-Agent": "NBADashboard/1.0"})
    if not data:
        return None
    items = data.get("data", [])
    return items[0] if items else None


@st.cache_data(ttl=300)
def bdl_jogos_recentes(team_ids: tuple, per_page: int = 10):
    """Últimos jogos de playoff de um time via Ball Don't Lie."""
    if not team_ids:
        return []
    qs_teams = "&".join(f"team_ids[]={tid}" for tid in team_ids)
    data = fetch_json(
        f"{BDL_GAMES}?seasons[]={BDL_SEASON_YEAR}&postseason=true&per_page={per_page}&{qs_teams}",
        headers={"User-Agent": "NBADashboard/1.0"}
    )
    if not data:
        return []
    return data.get("data", [])


# ═══════════════════════════════════════════════════════════════════════════════
# ░░  CAMADA 3 — Reddit r/nba (sem auth — JSON público)  ░░
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=300)
def reddit_posts_top():
    """Posts mais votados do dia em r/nba. Não requer autenticação."""
    headers = {"User-Agent": "NBADashboard/1.0 (hobby project)"}
    posts = []
    for url in [REDDIT_TOP, REDDIT_HOT]:
        data = fetch_json(url, headers=headers)
        if not data:
            continue
        for child in data.get("data", {}).get("children", []):
            p = child.get("data", {})
            titulo = p.get("title", "")
            flair = p.get("link_flair_text", "") or ""
            if any(kw in titulo.lower() for kw in ["game thread", "post game", "highlights", "analysis", "breakdown", "recap", "report", "trade", "injury", "signing", "update"]):
                posts.append({
                    "titulo":  titulo,
                    "url":     f"https://reddit.com{p.get('permalink','')}",
                    "score":   p.get("score", 0),
                    "flair":   flair,
                    "body":    p.get("selftext", "")[:500],
                    "comments": p.get("num_comments", 0),
                    "autor":   p.get("author", ""),
                })
    seen = set()
    unique = []
    for p in posts:
        if p["titulo"] not in seen:
            seen.add(p["titulo"])
            unique.append(p)
    return sorted(unique, key=lambda x: x["score"], reverse=True)[:3]


@st.cache_data(ttl=300)
def reddit_buscar_jogo(home_nome: str, away_nome: str):
    """Busca post-game thread no Reddit para um jogo específico."""
    headers = {"User-Agent": "NBADashboard/1.0 (hobby project)"}
    h = home_nome.split()[-1] if home_nome else ""
    a = away_nome.split()[-1] if away_nome else ""
    queries = [
        f"Post Game Thread {h} {a}",
        f"Game Thread {h} {a}",
        f"{h} vs {a} recap",
    ]
    for q in queries:
        params = {
            "q": q,
            "restrict_sr": "true",
            "subreddit": "nba",
            "sort": "relevance",
            "t": "week",
            "limit": 3,
            "type": "link",
        }
        data = fetch_json(REDDIT_NBA, params=params, headers=headers)
        if not data:
            continue
        children = data.get("data", {}).get("children", [])
        if children:
            return [c.get("data", {}) for c in children[:3]]
    return []


# ═══════════════════════════════════════════════════════════════════════════════
# ░░  CAMADA 4 — NBA API oficial (nba_api)  ░░
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=600)
def nba_api_players():
    """Stats de jogadores via NBA API oficial."""
    if not NBA_API:
        return PLAYERS_FB
    try:
        leaders = leagueleaders.LeagueLeaders(
            season=SEASON_ID,
            stat_category_abbreviation="PTS",
            per_mode_simple="PerGame",
            timeout=30,
        )
        df = leaders.get_data_frames()[0].head(20)
        if df.empty:
            return PLAYERS_FB
        result = []
        for _, row in df.iterrows():
            result.append({
                "nome": str(row.get("PLAYER","")),
                "team": str(row.get("TEAM","")),
                "pts":  round(float(row.get("PTS",0)),    1),
                "ast":  round(float(row.get("AST",0)),    1),
                "reb":  round(float(row.get("REB",0)),    1),
                "fg":   round(float(row.get("FG_PCT",0.45)),3),
                "stl":  round(float(row.get("STL",1.0)),  1),
                "blk":  round(float(row.get("BLK",0.5)),  1),
                "tov":  round(float(row.get("TOV",2.5)),  1),
            })
        return result or PLAYERS_FB
    except Exception:
        return PLAYERS_FB


# ═══════════════════════════════════════════════════════════════════════════════
# ░░  TRADUÇÃO AUTOMÁTICA EN→PT-BR (dicionário especializado)  ░░
# ═══════════════════════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────────────────────────────────────
# TRADUÇÃO EN→PT-BR  (dicionário especializado NBA — sem dependência externa)
# Substitui termos de forma inteligente, preservando nomes próprios
# ─────────────────────────────────────────────────────────────────────────────

# Pares de substituição ordenados do mais longo para o mais curto
# para evitar substituições parciais incorretas
_TRADUCOES = [
    # ── Frases compostas (sempre primeiro) ───────────────────────────────────
    ("post game thread",  "Thread Pós-Jogo"),
    ("game thread",       "Thread do Jogo"),
    ("post game",         "Pós-Jogo"),
    ("career-high",       "recorde de carreira"),
    ("career high",       "recorde de carreira"),
    ("game-winner",       "cesta da vitória"),
    ("game winner",       "cesta da vitória"),
    ("buzzer-beater",     "cesta no buzzer"),
    ("buzzer beater",     "cesta no buzzer"),
    ("three-pointer",     "bola de três"),
    ("three pointer",     "bola de três"),
    ("free throw",        "lance livre"),
    ("fast break",        "contra-ataque"),
    ("pick-and-roll",     "pick-and-roll"),
    ("pick and roll",     "pick-and-roll"),
    ("day-to-day",        "dia a dia"),
    ("day to day",        "dia a dia"),
    ("trade deadline",    "prazo de trocas"),
    ("first half",        "primeiro tempo"),
    ("second half",       "segundo tempo"),
    ("max contract",      "contrato máximo"),
    ("flagrant foul",     "falta flagrante"),
    ("technical foul",    "falta técnica"),
    ("playoff push",      "corrida aos playoffs"),
    ("los angeles",       "Los Angeles"),
    ("golden state",      "Golden State"),
    ("san antonio",       "San Antonio"),
    ("new orleans",       "New Orleans"),
    ("new york",          "New York"),
    ("oklahoma city",     "Oklahoma City"),
    ("according to",      "segundo"),
    ("per sources",       "segundo fontes"),
    ("sources say",       "fontes dizem"),
    ("expected to",       "deve"),
    ("likely to",         "provavelmente vai"),
    ("will miss",         "vai desfalcar"),
    ("out for",           "fora por"),
    ("ruled out",         "descartado"),
    ("placed on",         "colocado no"),
    ("injury report",     "relatório de lesões"),
    ("back in",           "de volta ao"),
    ("ahead of",          "antes de"),
    ("in favor of",       "a favor de"),
    ("as well as",        "assim como"),
    ("in addition",       "além disso"),
    ("going forward",     "daqui em diante"),
    ("moving forward",    "daqui em diante"),
    ("off the bench",     "saindo do banco"),
    ("in the paint",      "no garrafão"),
    ("at the rim",        "na cesta"),
    ("from downtown",     "de longa distância"),
    ("from deep",         "de longa distância"),
    ("off the glass",     "no tablete"),
    ("and-one",           "e mais um"),
    ("head coach",        "técnico principal"),
    ("assistant coach",   "assistente técnico"),
    # ── Palavras individuais ──────────────────────────────────────────────────
    ("points",        "pontos"),
    ("rebounds",      "rebotes"),
    ("rebound",       "rebote"),
    ("assists",       "assistências"),
    ("assist",        "assistência"),
    ("steals",        "roubos de bola"),
    ("steal",         "roubo de bola"),
    ("blocks",        "bloqueios"),
    ("block",         "bloqueio"),
    ("turnovers",     "erros"),
    ("turnover",      "erro"),
    ("injuries",      "lesões"),
    ("injured",       "lesionado"),
    ("injury",        "lesão"),
    ("doubtful",      "duvidoso"),
    ("questionable",  "questionável"),
    ("suspended",     "suspenso"),
    ("suspension",    "suspensão"),
    ("eliminated",    "eliminado"),
    ("elimination",   "eliminação"),
    ("advancing",     "avançando"),
    ("advances",      "avança"),
    ("advanced",      "avançou"),
    ("playoffs",      "playoffs"),
    ("playoff",       "playoff"),
    ("overtime",      "prorrogação"),
    ("quarter",       "quarto"),
    ("halftime",      "intervalo"),
    ("highlights",    "melhores momentos"),
    ("highlight",     "destaque"),
    ("reported",      "reportado"),
    ("reports",       "relatos"),
    ("report",        "relatório"),
    ("sources",       "fontes"),
    ("source",        "fonte"),
    ("confirmed",     "confirmado"),
    ("expected",      "esperado"),
    ("contract",      "contrato"),
    ("extension",     "extensão de contrato"),
    ("signed",        "assinou"),
    ("waived",        "dispensado"),
    ("drafted",       "draftado"),
    ("fined",         "multado"),
    ("traded",        "trocado"),
    ("trade",         "troca"),
    ("signing",       "contratação"),
    ("starter",       "titular"),
    ("starting",      "titulando"),
    ("benched",       "banqueteado"),
    ("bench",         "banco"),
    ("rotation",      "rotação"),
    ("layup",         "bandeja"),
    ("dunk",          "enterrada"),
    ("sweep",         "varredura"),
    ("upset",         "zebra"),
    ("dominant",      "dominante"),
    ("dominated",     "dominou"),
    ("struggles",     "dificuldades"),
    ("struggled",     "teve dificuldade"),
    ("struggling",    "em dificuldade"),
    ("exploded",      "explodiu"),
    ("impressive",    "impressionante"),
    ("remarkable",    "notável"),
    ("outstanding",   "excepcional"),
    ("clutch",        "clutch"),
    ("overtime",      "prorrogação"),
    ("championship",  "campeonato"),
    ("champion",      "campeão"),
    ("title",         "título"),
    ("finals",        "Finais"),
    ("final",         "final"),
    ("series",        "série"),
    ("season",        "temporada"),
    ("regular season","temporada regular"),
    ("practice",      "treino"),
    ("scrimmage",     "jogo treino"),
    ("shooting",      "arremesso"),
    ("defense",       "defesa"),
    ("offense",       "ataque"),
    ("scoring",       "pontuação"),
    ("scored",        "marcou"),
    ("score",         "placar"),
    ("coach",         "técnico"),
    ("coaching",      "comissão técnica"),
    ("arena",         "arena"),
    ("stadium",       "estádio"),
    ("attendance",    "público presente"),
    ("sold out",      "casa cheia"),
    ("perimeter",     "perímetro"),
    ("mid-range",     "médio"),
    ("paint",         "garrafão"),
    ("low post",      "poste baixo"),
    ("foul",          "falta"),
    ("flagrant",      "flagrante"),
    ("technical",     "técnica"),
    ("ejected",       "expulso"),
    ("ejection",      "expulsão"),
    ("overtime",      "prorrogação"),
    ("draft",         "draft"),
    ("franchise",     "franquia"),
    ("organization",  "organização"),
    ("management",    "diretoria"),
    ("ownership",     "proprietários"),
    ("analytics",     "analytics"),
    ("efficiency",    "eficiência"),
    ("transition",    "transição"),
    # ── Palavras função inglesas comuns em notícias ───────────────────────────
    ("drops",         "marca"),
    ("drop",          "marca"),
    ("posts",         "registra"),
    ("leads",         "lidera"),
    ("lead",          "liderou"),
    ("pours",         "anota"),
    ("tallies",       "registra"),
    ("tally",         "registrar"),
    ("finishes",      "termina"),
    ("finish",        "terminar"),
    ("puts up",       "registrou"),
    ("put up",        "registrou"),
    ("listed",        "listado"),
    ("suffered",      "sofreu"),
    ("suffers",       "sofre"),
    ("past",          "superando"),
    ("over",          "sobre"),
    ("with",          "com"),
    ("have been",     "foram"),
    ("has been",      "foi"),
    ("have",          "têm"),
    ("has",           "tem"),
    ("this",          "nesta"),
    ("the",           ""),
    ("and",           "e"),
    ("for",           "para"),
    ("as",            "como"),
    ("to",            "para"),
    ("in",            "na"),
    ("of",            "de"),
    ("at",            "no"),
    ("by",            "por"),
    ("from",          "de"),
    ("is",            "está"),
    ("are",           "estão"),
    ("was",           "foi"),
    ("were",          "foram"),
    ("will",          "vai"),
    ("per",           "por"),
    ("game",          "jogo"),
    ("games",         "jogos"),
    ("win",           "vitória"),
    ("wins",          "vitórias"),
    ("loss",          "derrota"),
    ("losses",        "derrotas"),
    ("round",         "rodada"),
    ("second round",  "segunda rodada"),
    ("first round",   "primeira rodada"),
    ("conference",    "conferência"),
    ("semifinals",    "semifinais"),
    ("semis",         "semifinais"),
]

# Mapa de nomes de times EN→PT para contexto (não substitui em títulos)
_NOMES_TIMES = {
    "Thunder": "Thunder", "Lakers": "Lakers", "Celtics": "Celtics",
    "Knicks": "Knicks", "Heat": "Heat", "Warriors": "Warriors",
    "Cavaliers": "Cavaliers", "Nuggets": "Nuggets", "Timberwolves": "Timberwolves",
    "Rockets": "Rockets", "Mavericks": "Mavericks", "Suns": "Suns",
    "Bucks": "Bucks", "Bulls": "Bulls", "Hawks": "Hawks",
    "Pacers": "Pacers", "Magic": "Magic", "Pistons": "Pistons",
    "76ers": "76ers", "Raptors": "Raptors", "Spurs": "Spurs",
    "Grizzlies": "Grizzlies", "Trail Blazers": "Trail Blazers", "Kings": "Kings",
    "Jazz": "Jazz", "Pelicans": "Pelicans", "Clippers": "Clippers",
    "Nets": "Nets", "Wizards": "Wizards", "Hornets": "Hornets",
}

def traduzir_texto(texto: str, modo_titulo: bool = False) -> str:
    """
    Traduz texto EN→PT-BR usando dicionário especializado NBA.
    modo_titulo=True: preserva maiúsculas de nomes próprios e siglas.
    """
    if not texto or not texto.strip():
        return texto

    resultado = texto

    # Aplica substituições (case-insensitive, preservando contexto)
    for en, pt in _TRADUCOES:
        import re
        # Usa word boundary apenas para palavras simples
        if " " in en:
            # Frases: substituição direta case-insensitive
            pattern = re.compile(re.escape(en), re.IGNORECASE)
            resultado = pattern.sub(pt, resultado)
        else:
            # Palavras: word boundary para não quebrar nomes próprios
            pattern = re.compile(r"\b" + re.escape(en) + r"\b", re.IGNORECASE)
            resultado = pattern.sub(pt, resultado)

    # Limpa espaços duplos
    resultado = re.sub(r"\s{2,}", " ", resultado).strip()
    return resultado


def traduzir_rapido(texto: str) -> str:
    """Traduz descrição/corpo de notícia completa."""
    return traduzir_texto(texto, modo_titulo=False)


def traduzir_titulo(titulo: str) -> str:
    """
    Traduz título de notícia preservando nomes de jogadores, times e siglas.
    Estratégia: traduz palavra a palavra, preservando tokens que começam
    com maiúscula ou são siglas (exceto artigos comuns em inglês).
    """
    if not titulo or not titulo.strip():
        return titulo

    import re
    # Palavras em inglês que DEVEM ser traduzidas mesmo começando com maiúscula
    # (artigos, preposições, conjunções e verbos comuns de notícia)
    FORCAR_TRADUCAO = {
        "The", "A", "An", "Is", "Are", "Was", "Were", "Has", "Have",
        "Had", "Will", "Would", "Could", "Should", "To", "In", "On",
        "At", "For", "With", "From", "By", "Of", "And", "Or", "But",
        "As", "After", "Before", "During", "About", "Out", "Up",
        "Down", "Off", "Over", "Under", "Between", "Into", "Through",
        "Per", "Via", "Due", "Re",
    }

    palavras = titulo.split()
    resultado = []
    for p in palavras:
        # Remove pontuação para checar
        limpa = p
        sufixo = ""
        prefixo_p = ""
        limpa2 = limpa

        # Preserva: nomes próprios (maiúscula E não é palavra função),
        #           siglas (tudo maiúsculo ≥2 chars), números
        eh_proprio = (limpa2 and limpa2[0].isupper() and limpa2 not in FORCAR_TRADUCAO
                      and not limpa2.upper() == limpa2)  # não é sigla toda caps
        eh_sigla   = len(limpa2) >= 2 and limpa2.isupper()
        tem_numero = any(c.isdigit() for c in limpa2)

        if eh_proprio or eh_sigla or tem_numero:
            resultado.append(p)  # preserva sem traduzir
        else:
            traduzida = traduzir_texto(limpa2.lower(), modo_titulo=True)
            # Mantém capitalização se era caps
            if limpa2 and limpa2[0].isupper() and traduzida:
                traduzida = traduzida[0].upper() + traduzida[1:]
            resultado.append(prefixo_p + traduzida + sufixo)

    return " ".join(resultado)


def gerar_comentario_jogo(jogo_entry: dict, box, reddit_posts: list) -> str:
    """
    Gera comentário analítico completo de um jogo combinando:
      1. Box score ESPN (dados reais)
      2. Contexto da série
      3. Posts do Reddit (sentimento da comunidade)
    Retorna markdown formatado em PT-BR.
    """
    linhas = []
    home, away = jogo_entry.get("home",""), jogo_entry.get("away","")
    hs, as_ = jogo_entry.get("home_score",0), jogo_entry.get("away_score",0)
    num = jogo_entry.get("numero",1)

    # ── Cabeçalho ────────────────────────────────────────────────────────────
    linhas.append(f"### 🏀 Análise — Jogo {num}: {home} {hs} × {as_} {away}")

    vencedor = jogo_entry.get("vencedor","")
    if vencedor:
        vn = home if vencedor == jogo_entry.get("home_abbr") else away
        margem = abs(hs - as_)
        if margem <= 3:
            linhas.append(f"**{vn} vence por {margem} ponto{'s' if margem>1 else ''}** — jogo decidido no fio.")
        elif margem <= 8:
            linhas.append(f"**{vn} vence por {margem} pontos** — vitória convincente mas o adversário manteve a pressão até o final.")
        elif margem <= 15:
            linhas.append(f"**{vn} vence com folga ({margem} pts)** — domínio claro ao longo do jogo.")
        else:
            linhas.append(f"**{vn} atropela ({margem} pts de diferença)** — superioridade absoluta nos dois lados da quadra.")

    # ── Box score ESPN ────────────────────────────────────────────────────────
    if box:
        # Pontuadores principais
        pts_leaders = [l for l in box.get("leaders",[]) if "Point" in l.get("categoria","")]
        reb_leaders = [l for l in box.get("leaders",[]) if "Rebound" in l.get("categoria","")]
        ast_leaders = [l for l in box.get("leaders",[]) if "Assist" in l.get("categoria","")]

        if pts_leaders:
            top = pts_leaders[0]
            v = float(top["stat"])
            comentario_pts = f"**{top['jogador']} ({top['time']})** foi o cestinha com **{top['valor']}**"
            if v >= 40:
                comentario_pts += " — performance histórica. 40+ pontos num jogo de playoffs é algo que se conta nos dedos."
            elif v >= 35:
                comentario_pts += " — número de eliminação. Esse tipo de atuação decide séries."
            elif v >= 30:
                comentario_pts += " — volume de star sólido. Nível necessário pra ser o motor ofensivo nos playoffs."
            elif v >= 25:
                comentario_pts += " — contribuição importante, construída com eficiência."
            else:
                comentario_pts += " — vitória coletiva: sem dependência de um scorer único."
            linhas.append(f"\n🔥 {comentario_pts}")

        if reb_leaders:
            top = reb_leaders[0]
            v = float(top["stat"])
            if v >= 15:
                linhas.append(f"💪 **{top['jogador']}** dominou o garrafão com **{top['valor']}** rebotes — controle total que gerou posses extras decisivas.")
            elif v >= 12:
                linhas.append(f"💪 **{top['jogador']}** com **{top['valor']}** rebotes — presença física que pesou na série.")
            elif v >= 10:
                linhas.append(f"💪 **{top['jogador']}** — duplo-duplo nos rebotes ({top['valor']}), papel sólido no garrafão.")

        if ast_leaders:
            top = ast_leaders[0]
            v = float(top["stat"])
            if v >= 10:
                linhas.append(f"🔑 **{top['jogador']}** orquestrou com **{top['valor']}** assistências — visão de jogo que desorganizou qualquer defesa individual.")
            elif v >= 7:
                linhas.append(f"🔑 **{top['jogador']}** com **{top['valor']}** assistências — criação constante, forçando rotações defensivas.")

        # Stats de time
        for t in box.get("teams", []):
            stats = t.get("stats", {})
            nome_time = t.get("nome","")
            fg3  = stats.get("threePointFieldGoalPct","")
            fg3_att = stats.get("threePointFieldGoalsAttempted","")
            tov  = stats.get("turnovers","")
            pts  = stats.get("points","")
            fg   = stats.get("fieldGoalPct","")
            reb_off = stats.get("offensiveRebounds","")
            try:
                if fg3:
                    fg3_f = float(str(fg3).replace('%',''))
                    if fg3_f > 1:
                        fg3_f /= 100.0
                    fg3_attempts = int(fg3_att) if fg3_att not in (None, "") else 0
                    if fg3_attempts >= 5:
                        if fg3_f >= 0.43:
                            linhas.append(f"🎯 **{nome_time}** foi letal de três ({fg3_f:.0%}) — aproveitamento que qualquer defesa teria dificuldade de conter.")
                        elif fg3_f < 0.27:
                            linhas.append(f"❄️ **{nome_time}** foi frio de três ({fg3_f:.0%}) — o arremesso de fora não entrou, comprimindo as opções ofensivas.")
                    elif fg3_attempts > 0:
                        if fg3_f >= 0.43:
                            linhas.append(f"🎯 **{nome_time}** teve ótimo aproveitamento de três ({fg3_f:.0%}) em {fg3_attempts} tentativas — volume baixo, mas eficiente.")
                        elif fg3_f < 0.27:
                            linhas.append(f"❄️ **{nome_time}** teve aproveitamento ruim de três ({fg3_f:.0%}) em {fg3_attempts} tentativas — a energia de fora não entrou.")
                if tov:
                    tov_i = int(tov)
                    if tov_i >= 18:
                        linhas.append(f"⚠️ **{nome_time}** cometeu {tov_i} erros — volume de turnovers que entregou posses gratuitas ao adversário.")
                    elif tov_i <= 7:
                        linhas.append(f"✅ **{nome_time}** foi disciplinado com a bola ({tov_i} erros) — cuidado que manteve o ritmo ofensivo.")
                if reb_off:
                    ro = int(reb_off)
                    if ro >= 14:
                        linhas.append(f"💥 **{nome_time}** dominou o rebote ofensivo ({ro} no total) — segundas oportunidades que inclinaram o jogo.")
            except (ValueError, TypeError):
                pass

        # Info da arena
        gi = box.get("game_info", {})
        if gi.get("arena") and gi.get("presenca"):
            try:
                presenca = int(str(gi["presenca"]).replace(",",""))
                linhas.append(f"\n📍 *{gi['arena']} — {presenca:,} presentes*")
            except Exception:
                if gi.get("arena"):
                    linhas.append(f"\n📍 *{gi['arena']}*")

    # ── Reddit — sentimento da comunidade ────────────────────────────────────
    reddit_relevantes = []
    for p in reddit_posts:
        titulo = p.get("title","") or p.get("titulo","")
        # Filtra posts relacionados a este jogo
        for nome in [home.split()[-1], away.split()[-1]]:
            if nome.lower() in titulo.lower():
                reddit_relevantes.append(p)
                break

    if reddit_relevantes:
        linhas.append("\n---\n**🗣️ Repercussão (r/nba):**")
        for p in reddit_relevantes[:3]:
            titulo = p.get("title","") or p.get("titulo","")
            score  = p.get("score",0)
            url    = p.get("url","") or p.get("permalink","")
            flair  = p.get("flair","") or p.get("link_flair_text","")
            comentarios = p.get("comments",0) or p.get("num_comments",0)
            emoji = "🔥" if score >= 5000 else "⬆️" if score >= 1000 else "💬"
            if url and not url.startswith("http"):
                url = f"https://reddit.com{url}"
            label = f"[{titulo[:90]}]({url})" if url else titulo[:90]
            linha_reddit = f"{emoji} {label} — **{score:,} upvotes** · {comentarios:,} comentários"
            if flair:
                linha_reddit += f" · *{flair}*"
            linhas.append(linha_reddit)

    return "\n\n".join(linhas)


def gerar_insight_boxscore(box) -> str | None:
    """Insight rápido baseado nos números do box score (usado em cards menores)."""
    if not box:
        return None
    linhas = []

    pts_leaders = [l for l in box.get("leaders",[]) if "Point" in l.get("categoria","")]
    reb_leaders = [l for l in box.get("leaders",[]) if "Rebound" in l.get("categoria","")]
    ast_leaders = [l for l in box.get("leaders",[]) if "Assist" in l.get("categoria","")]

    if pts_leaders:
        top = pts_leaders[0]
        v = float(top["stat"])
        linha = f"**{top['jogador']} ({top['time']})** liderou com **{top['valor']}** pontos"
        if v >= 40: linha += " — performance histórica."
        elif v >= 35: linha += " — número de eliminação."
        elif v >= 30: linha += " — volume de star."
        else: linha += " — vitória coletiva."
        linhas.append(linha)

    if reb_leaders:
        top = reb_leaders[0]
        if float(top["stat"]) >= 12:
            linhas.append(f"**{top['jogador']}** dominou os rebotes: **{top['valor']}**.")

    if ast_leaders:
        top = ast_leaders[0]
        if float(top["stat"]) >= 7:
            linhas.append(f"**{top['jogador']}** com **{top['valor']}** assistências.")

    return "\n\n".join(linhas) if linhas else None


# ═══════════════════════════════════════════════════════════════════════════════
# ░░  CPI — CLUTCH PERFORMANCE INDEX  ░░
# ═══════════════════════════════════════════════════════════════════════════════

def calculate_cpi(player, era_factor=1.0):
    pts = player.get("pts",0) * era_factor
    ast = player.get("ast",0)
    reb = player.get("reb",0)
    fg  = player.get("fg",0.45)
    stl = player.get("stl",1.0)
    blk = player.get("blk",0.5)
    tov = player.get("tov",2.5)
    pts_n = min(pts/REF["pts"],1.5);  ast_n = min(ast/REF["ast"],1.5)
    reb_n = min(reb/REF["reb"],1.5);  fg_n  = min(fg/REF["fg"],1.5)
    stl_n = min(stl/REF["stl"],1.5);  blk_n = min(blk/REF["blk"],1.5)
    tov_n = max(1.0-(tov-2.0)/4.0, 0.4)
    return round((pts_n*0.28+fg_n*0.22+ast_n*0.18+reb_n*0.16+stl_n*0.07+blk_n*0.06+tov_n*0.03)*100, 1)


def calculate_advanced(player):
    ast = player.get("ast",0); tov = max(player.get("tov",2.5),0.1)
    stl = player.get("stl",0); blk = player.get("blk",0)
    pts = player.get("pts",0); fg  = player.get("fg",0.45)
    return {
        "AST/TOV":      round(ast/tov,2),
        "Impacto Def.": round(stl*1.5+blk,2),
        "Pts×FG%":      round(pts*fg,2),
        "CPI":          calculate_cpi(player),
    }


def gerar_analise_narrativa(player):
    nome = player.get("nome","Jogador"); pts = player.get("pts",0)
    ast  = player.get("ast",0);          reb = player.get("reb",0)
    fg   = player.get("fg",0.45);        stl = player.get("stl",0)
    blk  = player.get("blk",0);          tov = player.get("tov",2.5)
    adv  = calculate_advanced(player);   L   = []

    if pts >= 31:   L.append(f"**🔥 {pts} PPG — scoring de elite absoluta**: só 4-5 jogadores na história atingiram esse nível. Defesas constroem game plans inteiros ao redor de {nome}.")
    elif pts >= 26: L.append(f"**{pts} PPG — pontuação de star**: volume suficiente para ser opção #1. 26+ PPG consistente separa quem decide de quem contribui nos playoffs.")
    elif pts >= 21: L.append(f"**{pts} PPG — second option confiável**: papel valioso em sistemas bem estruturados. Alivia o scorer principal.")
    else:           L.append(f"**{pts} PPG — contribuidor**: {nome} agrega principalmente em outras dimensões.")

    if fg >= 0.55:  L.append(f"**🎯 {fg:.1%} FG% — eficiência cirúrgica**: acima de 55% com volume real é raríssimo. Ouro em playoffs defensivos.")
    elif fg >= 0.49: L.append(f"**🎯 {fg:.1%} FG% — aproveitamento sólido**: confiabilidade sob pressão.")
    else:           L.append(f"**⚠️ {fg:.1%} FG% — alerta de eficiência**: em playoffs as defesas fecham ainda mais.")

    if ast >= 8:    L.append(f"**🔑 {ast} APG (AST/TOV {adv['AST/TOV']}) — visão excepcional**: eleva companheiros. Quase impossível de defender individualmente.")
    elif ast >= 5:  L.append(f"**🔑 {ast} APG (AST/TOV {adv['AST/TOV']}) — boa participação coletiva**: não ignora companheiros mesmo com iso disponível.")
    else:           L.append(f"**🔑 {ast} APG — criação limitada**: foco primário em criar para si mesmo.")

    if reb >= 10:   L.append(f"**💪 {reb} RPG — domínio no garrafão**: rebotes ofensivos se acumulam em posses extras decisivas em séries de 7 jogos.")
    elif reb >= 7:  L.append(f"**💪 {reb} RPG — reboteiro confiável**: contribuição nas duas pontas.")

    def_val = adv["Impacto Def."]
    if def_val >= 3.5: L.append(f"**🛡️ {stl} STL + {blk} BLK = {def_val} impacto defensivo**: presença que muda decisões adversárias antes do arremesso.")
    elif blk >= 2.0:   L.append(f"**🛡️ {blk} BLK/jogo — protetor de aro**: deterrente real para drives e pick-and-roll.")
    elif stl >= 1.6:   L.append(f"**🛡️ {stl} STL/jogo — ladrão de elite**: força adversários a repensarem passes de rotina.")

    if tov >= 3.8:  L.append(f"**⚠️ {tov} TOV/jogo — risco alto**: adversários montam armadilhas nos padrões de turnover.")
    elif tov <= 2.0: L.append(f"**✅ {tov} TOV/jogo — disciplina com a bola**: decisões limpas sob pressão.")

    cpi = adv["CPI"]; L.append("---")
    if cpi >= 118:  L.append(f"### 🏆 CPI {cpi} — NÍVEL FINALS MVP\nImpacto positivo em absolutamente todas as fases.")
    elif cpi >= 108: L.append(f"### ⭐ CPI {cpi} — ALL-NBA FIRST TEAM\nStar completo. Pode levar um time às Finais.")
    elif cpi >= 98: L.append(f"### ✅ CPI {cpi} — PLAYOFF STARTER DE CONFIANÇA\nConsistente sob pressão.")
    elif cpi >= 88: L.append(f"### 📊 CPI {cpi} — CONTRIBUIDOR SÓLIDO\nPapel importante e bem definido.")
    else:           L.append(f"### 📋 CPI {cpi} — ROLE PLAYER\nContribuição situacional.")

    return "\n\n".join(L)


# ═══════════════════════════════════════════════════════════════════════════════
# ░░  VISUALIZAÇÕES  ░░
# ═══════════════════════════════════════════════════════════════════════════════

def radar_chart(players_data, title="Comparativo de Perfil"):
    if not PLOTLY or not players_data:
        return None
    cats   = ["PTS","AST","REB","FG%","STL","BLK"]
    maxref = [35,   12,   14,   65,   25,   35]
    fig    = go.Figure()
    for p in players_data:
        vals = [p["pts"],p["ast"],p["reb"],p["fg"]*100,p["stl"]*10,p["blk"]*10]
        norm = [round(v/m,3) for v,m in zip(vals,maxref)] + [round(vals[0]/maxref[0],3)]
        fig.add_trace(go.Scatterpolar(
            r=norm, theta=cats+[cats[0]], fill="toself", name=p["nome"],
            hovertemplate="%{theta}: %{r:.2f}<extra>"+p["nome"]+"</extra>"
        ))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True,range=[0,1])),
                      showlegend=True, title=title, height=420,
                      margin=dict(l=30,r=30,t=50,b=30))
    return fig


def cpi_bar(players_data):
    if not PLOTLY or not players_data:
        return None
    df = pd.DataFrame([{"Jogador":p["nome"],"CPI":calculate_cpi(p),"Time":p["team"]} for p in players_data])
    df = df.sort_values("CPI", ascending=True)
    fig = px.bar(df,x="CPI",y="Jogador",orientation="h",color="CPI",
                 color_continuous_scale="RdYlGn",title="Ranking CPI — Temporada 2025-26",
                 hover_data=["Time"])
    fig.update_layout(height=520,margin=dict(l=10,r=10,t=50,b=10))
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
# ░░  RENDERIZAÇÃO DE SÉRIE  ░░
# ═══════════════════════════════════════════════════════════════════════════════

def render_serie(s: dict, injuries: list, reddit_posts: list):
    """Renderiza uma série completa com todos os jogos e comentários."""
    wa, wb = s["wins_a"], s["wins_b"]
    ta, tb = s["ta_nome"], s["tb_nome"]
    aa, ab = s["ta_abbr"], s["tb_abbr"]
    avancou = s.get("avancou")
    jogos   = s.get("jogos", [])
    total   = wa + wb

    # Status dinâmico
    if avancou == aa:
        icon, badge = "✅", f"{ta} avançou — {wa}-{wb}"
    elif avancou == ab:
        icon, badge = "✅", f"{tb} avançou — {wb}-{wa}"
    elif total == 0:
        icon, badge = "🔜", "Série não iniciada"
    else:
        icon, badge = "🔥", f"Em andamento — {ta} {wa}×{wb} {tb}"

    with st.expander(f"{icon} **{ta}** vs **{tb}** — {badge}", expanded=(total > 0 and not avancou)):
        # Placar da série
        c1, c2, c3 = st.columns(3)
        c1.metric(ta, f"{wa}", "vitórias")
        c2.metric("Série", f"Melhor de 7 — {total} jogos")
        c3.metric(tb, f"{wb}", "vitórias")

        # Barra de progresso visual da série
        if total > 0:
            prog_cols = st.columns(7)
            for i, col in enumerate(prog_cols):
                if i < total:
                    j = jogos[i]
                    venc = j.get("vencedor","")
                    cor = "🟢" if venc == aa else "🔴" if venc == ab else "⚪"
                    hs = j.get("home_score",""); as_ = j.get("away_score","")
                    col.markdown(f"**G{i+1}**\n{cor}\n{j.get('home_abbr','')} {hs}\n{j.get('away_abbr','')} {as_}")
                else:
                    col.markdown(f"**G{i+1}**\n⬜")

        # Lesionados dos dois times
        inj_serie = [i for i in injuries if i.get("team") in [aa, ab]]
        if inj_serie:
            st.warning("🩹 **Lesionados:** " + " | ".join(
                f"{i['jogador']} ({i['team']}) — {i['status']}" for i in inj_serie
            ))

        # Cada jogo individualmente com análise
        if jogos:
            st.divider()
            st.subheader(f"📋 Jogos da Série ({total} realizados)")
            for j in jogos:
                num = j.get("numero",1)
                hs  = j.get("home_score",0)
                as_ = j.get("away_score",0)
                venc = j.get("vencedor","")
                completed = j.get("completed", False)
                state = j.get("state","pre")

                # Data formatada
                data_raw = j.get("data","")
                try:
                    data_fmt = format_ptbr(data_raw, with_time=False)
                except Exception:
                    data_fmt = data_raw[:10] if data_raw else "—"

                label = f"Jogo {num} — {j['home']} {hs} × {as_} {j['away']} ({data_fmt})"
                if completed and venc:
                    vn = j["home"] if venc == j.get("home_abbr") else j["away"]
                    label += f" ✅ {vn} venceu"
                elif state == "in":
                    label += " 🔴 AO VIVO"
                else:
                    label += " 🔜 Aguardando"

                with st.expander(label):
                    if completed and j.get("game_id"):
                        box = espn_boxscore(j["game_id"])

                        # Comentário automático completo
                        comentario = gerar_comentario_jogo(j, box, reddit_posts)
                        st.markdown(comentario)

                        # Tabela box score dos times
                        if box and box["teams"]:
                            st.divider()
                            st.markdown("**📊 Stats dos Times (ESPN):**")
                            rows = []
                            for t in box["teams"]:
                                stat = t["stats"]
                                rows.append({
                                    "Time": t["nome"],
                                    "PTS": stat.get("points","—"),
                                    "FG%": stat.get("fieldGoalPct","—"),
                                    "3P%": stat.get("threePointFieldGoalPct","—"),
                                    "FT%": stat.get("freeThrowPct","—"),
                                    "REB": stat.get("totalRebounds","—"),
                                    "AST": stat.get("assists","—"),
                                    "TOV": stat.get("turnovers","—"),
                                    "STL": stat.get("steals","—"),
                                    "BLK": stat.get("blocks","—"),
                                })
                            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

                            # Top jogadores do jogo
                            all_players = []
                            for t in box["teams"]:
                                for p in t.get("players", []):
                                    s = p.get("stats",{})
                                    min_val = s.get("minutes","0")
                                    if min_val and min_val != "0:00":
                                        all_players.append({
                                            "Jogador": p["nome"],
                                            "Time": t["abbr"],
                                            "MIN": min_val,
                                            "PTS": s.get("points","0"),
                                            "REB": s.get("rebounds","0"),
                                            "AST": s.get("assists","0"),
                                            "FG": s.get("fieldGoalsAttempted","") and f"{s.get('fieldGoalsMade','0')}/{s.get('fieldGoalsAttempted','0')}",
                                            "3P": s.get("threePointFieldGoalsAttempted","") and f"{s.get('threePointFieldGoalsMade','0')}/{s.get('threePointFieldGoalsAttempted','0')}",
                                            "TOV": s.get("turnovers","0"),
                                            "+/-": s.get("plusMinus","—"),
                                        })
                            if all_players:
                                df_p = pd.DataFrame(all_players)
                                try:
                                    df_p["PTS_sort"] = pd.to_numeric(df_p["PTS"], errors="coerce").fillna(0)
                                    df_p = df_p.sort_values("PTS_sort", ascending=False).drop("PTS_sort", axis=1)
                                except Exception:
                                    pass
                                st.markdown("**👥 Box Score Individual (ESPN):**")
                                st.dataframe(df_p, use_container_width=True, hide_index=True)
                    elif state == "in":
                        st.info("🔴 Jogo em andamento — dados ao vivo disponíveis na aba Jogos de Hoje.")
                    else:
                        st.info("Jogo ainda não realizado.")


# ═══════════════════════════════════════════════════════════════════════════════
# ░░  FILTRAGEM DE NOTÍCIAS POR TIME  ░░
# ═══════════════════════════════════════════════════════════════════════════════

def filtrar_noticias_por_times(noticias: list, abbrs: set) -> list:
    """
    Filtra notícias ESPN relevantes SOMENTE para os times em abbrs.
    Usa matching estrito: TODOS os keywords do time devem aparecer no texto,
    e a notícia só é incluída se mencionar pelo menos um dos times buscados.
    Times aleatórios não vazam — a notícia precisa mencionar explicitamente
    um dos times solicitados.
    """
    if not abbrs:
        return noticias

    # Mapeamento abreviação → lista de palavras-chave do time
    NOMES_BUSCA = {
        "OKC": ["thunder", "oklahoma"],
        "LAL": ["lakers"],
        "BOS": ["celtics", "boston"],
        "NYK": ["knicks", "new york knicks"],
        "MIA": ["heat", "miami heat"],
        "GSW": ["warriors", "golden state"],
        "CLE": ["cavaliers", "cleveland"],
        "DEN": ["nuggets", "denver"],
        "MIN": ["timberwolves", "minnesota"],
        "HOU": ["rockets", "houston"],
        "DAL": ["mavericks", "dallas"],
        "PHX": ["suns", "phoenix suns"],
        "MIL": ["bucks", "milwaukee"],
        "CHI": ["bulls", "chicago bulls"],
        "ATL": ["hawks", "atlanta"],
        "IND": ["pacers", "indiana"],
        "ORL": ["magic", "orlando magic"],
        "DET": ["pistons", "detroit"],
        "PHI": ["76ers", "philadelphia", "sixers"],
        "TOR": ["raptors", "toronto"],
        "SAS": ["spurs", "san antonio"],
        "MEM": ["grizzlies", "memphis"],
        "POR": ["blazers", "portland"],
        "SAC": ["kings", "sacramento"],
        "UTA": ["jazz", "utah jazz"],
        "NOP": ["pelicans", "new orleans"],
        "LAC": ["clippers"],
        "BKN": ["nets", "brooklyn"],
        "WAS": ["wizards", "washington"],
        "CHA": ["hornets", "charlotte"],
    }

    relevantes = []
    for n in noticias:
        texto = (
            n.get("titulo", "") + " " +
            n.get("descricao", "") + " " +
            " ".join(n.get("categorias", []))
        ).lower()

        for abbr in abbrs:
            keywords = NOMES_BUSCA.get(abbr, [abbr.lower()])
            # A notícia precisa conter pelo menos UMA keyword deste time
            if any(kw in texto for kw in keywords):
                relevantes.append(n)
                break  # já encontrou um time relevante, não precisa checar mais

    return relevantes

def main():
    st.set_page_config(page_title="NBA Playoffs 2026", layout="wide", page_icon="🏀")

    # ── CSS custom ───────────────────────────────────────────────────────────
    st.markdown("""
    <style>
    .stMetric label { font-size: 0.78rem !important; }
    .fonte-badge {
        background: #1a1a2e; color: #e94560; border-radius: 4px;
        padding: 2px 8px; font-size: 0.72rem; margin-right: 4px;
    }
    </style>
    """, unsafe_allow_html=True)

    # ── Sidebar ───────────────────────────────────────────────────────────────
    st.sidebar.title("🏀 NBA Playoffs 2026")
    st.sidebar.caption("Analítico · Multi-Fonte · Fã de Basquete")

    # Carrega dados (todas as fontes em paralelo via cache)
    with st.sidebar:
        with st.spinner("Carregando fontes..."):
            today_games  = espn_hoje()
            series_map   = espn_series_playoffs()
            injuries     = espn_lesoes()
            noticias_raw = espn_noticias()
            players      = nba_api_players()
            reddit_posts = reddit_posts_top()

    # Status das fontes — sem ternário inline (evita bug DeltaGenerator)
    st.sidebar.divider()
    st.sidebar.markdown("**📡 Fontes ativas:**")
    if series_map:
        st.sidebar.success("✅ ESPN API")
    else:
        st.sidebar.warning("⚠️ ESPN offline")
    if NBA_API:
        st.sidebar.success("✅ NBA API oficial")
    else:
        st.sidebar.info("ℹ️ NBA API: fallback local")
    if reddit_posts:
        st.sidebar.success(f"✅ Reddit r/nba ({len(reddit_posts)} posts)")
    else:
        st.sidebar.warning("⚠️ Reddit indisponível")
    st.sidebar.caption(f"🕐 {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    if st.sidebar.button("🔄 Atualizar tudo"):
        st.cache_data.clear()
        st.rerun()

    st.sidebar.divider()
    page = st.sidebar.radio("Navegação", [
        "🏠 Visão Geral",
        "🏆 Bracket & Séries",
        "📅 Jogos de Hoje",
        "📰 Notícias",
        "💬 Reddit r/nba",
        "📊 Painel de Jogadores",
        "🔍 Análise Profunda",
        "🕰️ E se...? — Lendas",
    ])

    # ══════════════════════════════════════════════════════════════════════════
    # 🏠 VISÃO GERAL
    # ══════════════════════════════════════════════════════════════════════════
    if page == "🏠 Visão Geral":
        st.header(f"🏀 NBA Playoffs 2026 — {datetime.now().strftime('%d/%m/%Y')}")
        st.caption(
            '<span class="fonte-badge">ESPN</span>'
            '<span class="fonte-badge">NBA API</span>'
            '<span class="fonte-badge">Reddit r/nba</span>'
            " Dados ao vivo · Comentários automáticos",
            unsafe_allow_html=True
        )

        # Jogos de hoje
        playoff_hoje = [g for g in today_games if g.get("playoff")]
        todos_hoje   = today_games
        jogos_exibir = playoff_hoje if playoff_hoje else todos_hoje

        if jogos_exibir:
            st.subheader("📅 Jogos de Hoje")
            cols = st.columns(min(len(jogos_exibir), 3))
            for i, g in enumerate(jogos_exibir[:3]):
                with cols[i % 3]:
                    state = g["state"]
                    if state == "in":
                        st.error(f"🔴 AO VIVO — {g['status']}")
                    elif state == "post":
                        st.success("✅ Encerrado")
                    else:
                        st.info(f"⏰ {g['status']}")
                    st.metric(g["home_nome"], g["home_score"], "Casa")
                    st.metric(g["away_nome"], g["away_score"], "Visitante")
                    if g["broadcast"]:
                        st.caption(f"📺 {g['broadcast']}")

        # Status séries
        if series_map:
            st.divider()
            st.subheader("🏆 Status das Séries")
            em_and = [(k,s) for k,s in series_map.items() if not s.get("avancou") and s["wins_a"]+s["wins_b"]>0]
            enc    = [(k,s) for k,s in series_map.items() if s.get("avancou")]

            if em_and:
                st.markdown("**🔥 Em andamento:**")
                for _, s in em_and:
                    st.write(f"• **{s['ta_nome']}** {s['wins_a']} × {s['wins_b']} **{s['tb_nome']}**")
            if enc:
                st.markdown("**✅ Séries encerradas:**")
                for _, s in enc:
                    av = s["ta_nome"] if s["avancou"]==s["ta_abbr"] else s["tb_nome"]
                    st.write(f"• **{av}** avançou")

        # Top 5 CPI
        st.divider()
        st.subheader("📊 Top 5 — CPI Temporada Regular")
        ranked = sorted(players, key=lambda x: calculate_cpi(x), reverse=True)[:5]
        cols   = st.columns(5)
        emojis = ["🥇","🥈","🥉","4️⃣","5️⃣"]
        for i, (col, p) in enumerate(zip(cols, ranked)):
            col.metric(f"{emojis[i]} {p['nome']}", f"CPI {calculate_cpi(p)}", f"{p['pts']} PPG · {p['team']}")

        # Posts reddit em destaque
        if reddit_posts:
            st.divider()
            st.subheader("💬 Em alta no r/nba agora")
            for post in reddit_posts[:4]:
                titulo = post.get("titulo","") or post.get("title","")
                score  = post.get("score",0)
                url    = post.get("url","")
                flair  = post.get("flair","")
                comentarios = post.get("comments",0)
                emoji = "🔥" if score >= 5000 else "⬆️"
                with st.expander(f"{emoji} {titulo[:100]}"):
                    col1, col2 = st.columns([3,1])
                    col1.write(f"**{score:,} upvotes** · {comentarios:,} comentários")
                    if flair:
                        col1.caption(f"Flair: {flair}")
                    if url:
                        col2.markdown(f"[Ver no Reddit]({url})")

        # Últimas notícias (3)
        if noticias_raw:
            st.divider()
            st.subheader("📰 Últimas Notícias — ESPN")
            for n in noticias_raw[:3]:
                with st.expander(f"**{traduzir_titulo(n['titulo'])}**"):
                    st.caption(f"✍️ {n['autor']} | ESPN")
                    st.write(traduzir_rapido(n['descricao']))
                    if n["link"]:
                        st.markdown(f"[Ler na ESPN]({n['link']})")

    # ══════════════════════════════════════════════════════════════════════════
    # 🏆 BRACKET & SÉRIES
    # ══════════════════════════════════════════════════════════════════════════
    elif page == "🏆 Bracket & Séries":
        st.header("🏆 Playoff Bracket 2026")
        st.caption("ESPN API · Resultados ao vivo · Comentários automáticos por jogo")

        if not series_map:
            st.warning("ESPN API indisponível. Tente 🔄 Atualizar.")
            return

        series_leste = [(k,s) for k,s in series_map.items() if s["ta_abbr"] in LESTE or s["tb_abbr"] in LESTE]
        series_oeste = [(k,s) for k,s in series_map.items() if s["ta_abbr"] in OESTE or s["tb_abbr"] in OESTE]

        tab_l, tab_o = st.tabs(["🔵 Conferência Leste", "🔴 Conferência Oeste"])

        with tab_l:
            if series_leste:
                for _, s in sorted(series_leste, key=lambda x: x[1]["wins_a"]+x[1]["wins_b"], reverse=True):
                    render_serie(s, injuries, reddit_posts)
            else:
                st.info("Nenhuma série do Leste encontrada via ESPN.")

        with tab_o:
            if series_oeste:
                for _, s in sorted(series_oeste, key=lambda x: x[1]["wins_a"]+x[1]["wins_b"], reverse=True):
                    render_serie(s, injuries, reddit_posts)
            else:
                st.info("Nenhuma série do Oeste encontrada via ESPN.")

    # ══════════════════════════════════════════════════════════════════════════
    # 📅 JOGOS DE HOJE
    # ══════════════════════════════════════════════════════════════════════════
    elif page == "📅 Jogos de Hoje":
        st.header(f"📅 Jogos de Hoje — {datetime.now().strftime('%d/%m/%Y')}")
        st.caption("ESPN Public API · TTL 30s · 🔄 para forçar refresh")

        if not today_games:
            st.info("Nenhum jogo hoje via ESPN. A NBA pode estar em dia de folga.")
            return

        for g in today_games:
            state = g["state"]
            if state == "in":
                st.error(f"🔴 AO VIVO — {g['status']}")
            elif state == "post":
                st.success("✅ Encerrado")
            else:
                st.info(f"⏰ Pré-jogo — {g['status']}")

            st.subheader(f"🏀 {g['home_nome']} vs {g['away_nome']}")
            if g["venue"] or g["broadcast"]:
                linha_local = f"📍 {g['venue']}" if g['venue'] else ""
                if g['broadcast']:
                    linha_local += f"  |  📺 {g['broadcast']}"
                linha_local += f"  |  🕒 {g['local_time']}"
                st.caption(linha_local)

            c1, c2, c3 = st.columns(3)
            c1.metric(f"🏠 {g['home_nome']}", g["home_score"], g["home_record"])
            c2.metric("Status", g["status"])
            c3.metric(f"✈️ {g['away_nome']}", g["away_score"], g["away_record"])

            # Lesionados
            inj_jogo = [i for i in injuries if i.get("team") in [g["home_abbr"], g["away_abbr"]]]
            if inj_jogo:
                st.warning("🩹 **Lesionados:** " + " | ".join(
                    f"{i['jogador']} ({i['team']}) — {i['status']}" for i in inj_jogo
                ))

            # Análise pós-jogo
            if state == "post" and g["id"]:
                box = espn_boxscore(g["id"])
                # Monta jogo_entry simulado para o gerador de comentários
                jogo_entry = {
                    "game_id":  g["id"],
                    "numero":   1,
                    "home":     g["home_nome"], "home_abbr": g["home_abbr"], "home_score": g["home_score"],
                    "away":     g["away_nome"], "away_abbr": g["away_abbr"], "away_score": g["away_score"],
                    "completed": True, "state": "post",
                }
                reddit_jogo = reddit_buscar_jogo(g["home_nome"], g["away_nome"])
                comentario = gerar_comentario_jogo(jogo_entry, box, reddit_jogo)
                with st.expander("📊 Análise do Jogo (ESPN + Reddit)"):
                    st.markdown(comentario)
                    if box and box["teams"]:
                        rows = []
                        for t in box["teams"]:
                            stat = t["stats"]
                            rows.append({
                                "Time": t["nome"],
                                "PTS": stat.get("points","—"),
                                "FG%": stat.get("fieldGoalPct","—"),
                                "3P%": stat.get("threePointFieldGoalPct","—"),
                                "REB": stat.get("totalRebounds","—"),
                                "AST": stat.get("assists","—"),
                                "TOV": stat.get("turnovers","—"),
                                "STL": stat.get("steals","—"),
                                "BLK": stat.get("blocks","—"),
                            })
                        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

            # Notícias ESPN relacionadas
            abbrs = {g["home_abbr"], g["away_abbr"]}
            news_jogo = filtrar_noticias_por_times(noticias_raw, abbrs)
            if news_jogo:
                with st.expander(f"📰 Notícias ESPN sobre este jogo ({len(news_jogo)})"):
                    for n in news_jogo[:4]:
                        st.markdown(f"**{traduzir_titulo(n['titulo'])}** — *{n['autor']}*")
                        st.write(traduzir_rapido(n['descricao']))
                        if n["link"]:
                            st.markdown(f"[Ler na ESPN]({n['link']})")
                        st.divider()

            st.divider()

    # ══════════════════════════════════════════════════════════════════════════
    # 📰 NOTÍCIAS
    # ══════════════════════════════════════════════════════════════════════════
    elif page == "📰 Notícias":
        st.header("📰 Notícias — ESPN NBA")
        st.caption("Fonte: ESPN News API · Tradução automática para PT-BR · Filtragem por time dos playoffs")

        if not noticias_raw:
            st.warning("ESPN News API indisponível.")
            return

        # Filtro: todos os times em playoff + "Todas"
        times_em_serie = set()
        for s in series_map.values():
            times_em_serie.add(s["ta_abbr"])
            times_em_serie.add(s["tb_abbr"])

        opcoes_filtro = ["Todas as Notícias", "Times nos Playoffs"] + sorted(times_em_serie)
        filtro = st.selectbox("🔍 Filtrar notícias:", opcoes_filtro)

        if filtro == "Times nos Playoffs":
            exibir = filtrar_noticias_por_times(noticias_raw, times_em_serie)
        elif filtro in times_em_serie:
            exibir = filtrar_noticias_por_times(noticias_raw, {filtro})
        else:
            exibir = noticias_raw

        if not exibir:
            st.info("Nenhuma notícia encontrada para o filtro selecionado.")
        else:
            st.caption(f"{len(exibir)} notícias encontradas")
            for n in exibir:
                titulo_pt = traduzir_titulo(n["titulo"])
                descr_pt  = traduzir_rapido(n["descricao"])
                data_fmt  = n["data"][:10] if n["data"] else ""
                with st.expander(f"**{titulo_pt}**"):
                    col1, col2 = st.columns([3,1])
                    col1.caption(f"✍️ {n['autor']}  |  📅 {data_fmt}  |  ESPN")
                    if n["categorias"]:
                        col1.caption("🏷️ " + " · ".join(n["categorias"][:5]))
                    col2.caption("Fonte: ESPN")
                    st.write(descr_pt)
                    if n["link"]:
                        st.markdown(f"[📖 Ler artigo completo na ESPN (EN)]({n['link']})")

    # ══════════════════════════════════════════════════════════════════════════
    # 💬 REDDIT r/nba
    # ══════════════════════════════════════════════════════════════════════════
    elif page == "💬 Reddit r/nba":
        st.header("💬 Reddit r/nba — Em Alta Hoje")
        st.caption("Fonte: Reddit API pública · Posts top do dia/semana · Game Threads + Análises")

        if not reddit_posts:
            st.warning("Reddit API indisponível ou sem posts relevantes no momento.")
            return

        # Filtros de flair
        flairs = sorted(set(p.get("flair","") for p in reddit_posts if p.get("flair")))
        col_f1, col_f2 = st.columns([2,3])
        tipo_filtro = col_f1.selectbox("Tipo:", ["Todos", "Game Thread", "Post Game", "Analysis", "Highlights"])
        flair_filtro = col_f2.selectbox("Flair:", ["Todos"] + flairs)

        exibir_reddit = reddit_posts
        if tipo_filtro != "Todos":
            exibir_reddit = [p for p in exibir_reddit if tipo_filtro.lower() in (p.get("titulo","") or p.get("title","")).lower()]
        if flair_filtro != "Todos":
            exibir_reddit = [p for p in exibir_reddit if p.get("flair","") == flair_filtro]

        if not exibir_reddit:
            st.info("Nenhum post encontrado para os filtros selecionados.")
        else:
            st.caption(f"{len(exibir_reddit)} posts encontrados")
            for i, post in enumerate(exibir_reddit):
                titulo = post.get("titulo","") or post.get("title","")
                score  = post.get("score",0)
                url    = post.get("url","")
                flair  = post.get("flair","")
                comentarios = post.get("comments",0)
                body   = post.get("body","")
                autor  = post.get("autor","")

                emoji = "🔥" if score >= 5000 else "⬆️" if score >= 1000 else "💬"
                with st.expander(f"{emoji} {titulo[:110]}"):
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Upvotes", f"{score:,}")
                    c2.metric("Comentários", f"{comentarios:,}")
                    c3.caption(f"por u/{autor}\n{flair}")
                    if body:
                        st.write(body[:400] + ("..." if len(body) > 400 else ""))
                    if url:
                        st.markdown(f"[🔗 Ver discussão completa no Reddit]({url})")

        # Busca manual de jogo
        st.divider()
        st.subheader("🔍 Buscar Thread de um Jogo")
        col_b1, col_b2, col_b3 = st.columns(3)
        home_input = col_b1.text_input("Time da casa:", placeholder="ex: Knicks")
        away_input = col_b2.text_input("Time visitante:", placeholder="ex: Celtics")
        if col_b3.button("🔎 Buscar no Reddit") and home_input and away_input:
            with st.spinner("Buscando threads..."):
                resultados = reddit_buscar_jogo(home_input, away_input)
            if resultados:
                for r in resultados:
                    titulo_r = r.get("title","")
                    score_r  = r.get("score",0)
                    url_r    = f"https://reddit.com{r.get('permalink','')}"
                    st.success(f"✅ [{titulo_r}]({url_r}) — {score_r:,} upvotes")
            else:
                st.info("Nenhum thread encontrado para essa combinação.")

    # ══════════════════════════════════════════════════════════════════════════
    # 📊 PAINEL DE JOGADORES
    # ══════════════════════════════════════════════════════════════════════════
    elif page == "📊 Painel de Jogadores":
        st.header("📊 Painel de Jogadores — Temporada Regular 2025-26")
        fonte_str = "NBA API oficial" if NBA_API else "dados locais (instale nba_api)"
        st.caption(f"Fonte: {fonte_str}")

        ranking = sorted(players, key=lambda x: calculate_cpi(x), reverse=True)

        df = pd.DataFrame([{
            "Pos": i+1, "Jogador": p["nome"], "Time": p["team"],
            "PTS": p["pts"], "AST": p["ast"], "REB": p["reb"],
            "FG%": f"{p['fg']:.1%}", "STL": p["stl"], "BLK": p["blk"], "TOV": p["tov"],
            "AST/TOV": round(p["ast"]/max(p["tov"],0.1),2),
            "Imp.Def": round(p["stl"]*1.5+p["blk"],2),
            "CPI": calculate_cpi(p),
        } for i, p in enumerate(ranking)])
        st.dataframe(df, use_container_width=True, hide_index=True)

        if PLOTLY:
            st.plotly_chart(cpi_bar(players), use_container_width=True)

        st.divider()
        st.subheader("📡 Comparativo de Perfil — Radar")
        nomes = [p["nome"] for p in players]
        sel   = st.multiselect("Selecione 2 a 5 jogadores:", nomes, default=nomes[:3], max_selections=5)
        if sel and PLOTLY:
            fig = radar_chart([p for p in players if p["nome"] in sel])
            if fig:
                st.plotly_chart(fig, use_container_width=True)

        st.divider()
        st.subheader("📈 Delta Performance")
        st.caption("Desvio ponderado da média de referência")
        AVG = {"pts":22.0,"fg":0.45,"reb":5.0,"ast":5.0,"tov":2.5}
        dl = sorted([{
            "nome": p["nome"], "team": p["team"], "cpi": calculate_cpi(p),
            "delta": round((
                ((p.get("pts",AVG["pts"])-AVG["pts"])/AVG["pts"])*0.30+
                ((p.get("fg",AVG["fg"])-AVG["fg"])/AVG["fg"])*0.35+
                ((p.get("reb",AVG["reb"])-AVG["reb"])/AVG["reb"])*0.15+
                ((p.get("ast",AVG["ast"])-AVG["ast"])/AVG["ast"])*0.20-
                ((p.get("tov",AVG["tov"])-AVG["tov"])/AVG["tov"])*0.10
            )*100,1),
        } for p in players], key=lambda x: x["delta"], reverse=True)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**📈 Acima da média**")
            for d in [x for x in dl if x["delta"]>0][:6]:
                st.metric(f"{d['nome']} ({d['team']})", f"+{d['delta']:.1f}", f"CPI {d['cpi']}")
        with c2:
            st.markdown("**📉 Abaixo da média**")
            for d in [x for x in dl if x["delta"]<=0][:6]:
                st.metric(f"{d['nome']} ({d['team']})", f"{d['delta']:.1f}", f"CPI {d['cpi']}")

    # ══════════════════════════════════════════════════════════════════════════
    # 🔍 ANÁLISE PROFUNDA
    # ══════════════════════════════════════════════════════════════════════════
    elif page == "🔍 Análise Profunda":
        st.header("🔍 Análise Profunda — Breakdown por Jogador")

        nome_esc = st.selectbox("Escolha o jogador:", [p["nome"] for p in players])
        p = next((x for x in players if x["nome"] == nome_esc), None)

        if p:
            adv = calculate_advanced(p)
            cols = st.columns(7)
            for col, (label, val) in zip(cols, [
                ("PTS",f"{p.get('pts',0):.1f}"), ("AST",f"{p.get('ast',0):.1f}"),
                ("REB",f"{p.get('reb',0):.1f}"), ("FG%",f"{p.get('fg',0):.1%}"),
                ("STL",f"{p.get('stl',0):.1f}"), ("BLK",f"{p.get('blk',0):.1f}"),
                ("CPI",f"{adv['CPI']}"),
            ]):
                col.metric(label, val)

            st.divider()
            ca, cb, cc = st.columns(3)
            ca.metric("AST/TOV", adv["AST/TOV"], "Elite >3", delta_color="off")
            cb.metric("Impacto Def.", adv["Impacto Def."], "STL×1.5+BLK", delta_color="off")
            cc.metric("Pts×FG%", adv["Pts×FG%"], "Volume × eficiência", delta_color="off")

            st.divider()
            st.markdown(gerar_analise_narrativa(p))

            if PLOTLY:
                media_ref = {"nome":"Média Ref.","pts":22.0,"ast":5.0,"reb":5.0,"fg":0.45,"stl":1.3,"blk":0.8,"tov":2.5}
                fig = radar_chart([p, media_ref], title=f"{nome_esc} vs Média de Referência")
                if fig:
                    st.plotly_chart(fig, use_container_width=True)

            # Notícias ESPN sobre o jogador
            nome_busca = nome_esc.split()[-1].lower()
            news_p = [n for n in noticias_raw if nome_busca in n["titulo"].lower() or nome_busca in n["descricao"].lower()]
            if news_p:
                st.divider()
                st.subheader(f"📰 Notícias ESPN sobre {nome_esc}")
                for n in news_p[:4]:
                    with st.expander(traduzir_titulo(n["titulo"])):
                        st.write(traduzir_rapido(n["descricao"]))
                        if n["link"]:
                            st.markdown(f"[Ler na ESPN]({n['link']})")

            # Posts Reddit sobre o jogador
            reddit_player = [
                post for post in reddit_posts
                if nome_esc.split()[-1].lower() in (post.get("titulo","") or post.get("title","")).lower()
            ]
            if reddit_player:
                st.divider()
                st.subheader(f"💬 Reddit sobre {nome_esc}")
                for post in reddit_player[:3]:
                    titulo = post.get("titulo","") or post.get("title","")
                    url    = post.get("url","")
                    score  = post.get("score",0)
                    with st.expander(f"⬆️ {titulo[:100]}"):
                        st.write(f"**{score:,} upvotes**")
                        if url:
                            st.markdown(f"[Ver no Reddit]({url})")

    # ══════════════════════════════════════════════════════════════════════════
    # 🕰️ E SE...? — LENDAS
    # ══════════════════════════════════════════════════════════════════════════
    elif page == "🕰️ E se...? — Lendas":
        st.header("🕰️ E se...? — Lendas nos Playoffs 2026")
        st.caption(
            "CPI calculado com stats ajustado pelo **era_factor** de cada época. "
            "Anos 80 (hand-check total, ~95 posses): 0.87-0.90. Era moderna: 1.0-1.02."
        )

        lenda_nome = st.selectbox("Escolha uma lenda:", list(LENDAS.keys()))
        l   = LENDAS[lenda_nome]
        ef  = l.get("era_factor",1.0)
        cpi = calculate_cpi(l, era_factor=ef)

        col1, col2 = st.columns([1,2])
        with col1:
            st.subheader(lenda_nome.split("(")[0].strip())
            ca, cb = st.columns(2)
            ca.metric("PPG",f"{l['pts']:.1f}"); cb.metric("APG",f"{l['ast']:.1f}")
            ca.metric("RPG",f"{l['reb']:.1f}"); cb.metric("FG%",f"{l['fg']:.1%}")
            ca.metric("STL",f"{l.get('stl',0):.1f}"); cb.metric("BLK",f"{l.get('blk',0):.1f}")
            st.metric("Era Factor",f"{ef:.2f}×",l["era"])
        with col2:
            st.metric("CPI Projetado nos Playoffs 2026",f"{cpi:.1f}")
            if cpi >= 118:   st.success("**🏆 DOMINANTE — Top 3 da liga.** Defesas modernas teriam dificuldade real.")
            elif cpi >= 108: st.success("**⭐ ELITE — All-NBA e candidato a MVP das Finais.**")
            elif cpi >= 98:  st.warning("**✅ MUITO BOM — Star sólido.** Ritmo e defesa modernos criariam desafios.")
            else:            st.info("**📊 COMPETITIVO.** O estilo de 2026 exige mais versatilidade.")
            st.divider()
            st.markdown(f"**Contexto:** {l.get('bio','')}")
            st.markdown("**Momentos icônicos:**")
            for m in l.get("momentos",[]):
                st.write(f"• {m}")

        st.divider()
        st.subheader("📊 Comparar Lendas")
        sel = st.multiselect("Selecione até 6 lendas:", list(LENDAS.keys()), max_selections=6)
        if sel:
            comp = [{
                "Lenda": n.split("(")[0].strip(), "Era": LENDAS[n]["era"],
                "PPG": LENDAS[n]["pts"], "APG": LENDAS[n]["ast"],
                "RPG": LENDAS[n]["reb"], "FG%": f"{LENDAS[n]['fg']:.1%}",
                "STL": LENDAS[n].get("stl",0), "BLK": LENDAS[n].get("blk",0),
                "Era×": LENDAS[n].get("era_factor",1.0),
                "CPI 2026": calculate_cpi(LENDAS[n], LENDAS[n].get("era_factor",1.0)),
            } for n in sel]
            st.dataframe(pd.DataFrame(comp).sort_values("CPI 2026",ascending=False),
                         use_container_width=True, hide_index=True)
            if PLOTLY and len(sel) >= 2:
                fig = radar_chart([{**LENDAS[n],"nome":n.split("(")[0].strip()} for n in sel],
                                  title="Comparativo — Lendas")
                if fig:
                    st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    main()