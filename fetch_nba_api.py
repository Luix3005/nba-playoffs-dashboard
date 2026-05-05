#!/usr/bin/env python3
"""
Busca dados REAIS da NBA API (gratuita, sem API key)
Puxa: jogos de hoje, playoffs 2026, estatísticas de jogadores
"""

import json
import requests
from datetime import datetime

def fetch_real_data():
    print("Iniciando busca de dados NBA 2026...\n")

    # 1. Jogos de hoje (Scoreboard V3 - funciona melhor)
    try:
        print("Buscando jogos de hoje...")
        today = datetime.now().strftime("%Y%m%d")
        url = f"https://cdn.nba.com/static/json/liveData/scoreboard/today.json"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            games = data.get('scoreboard', {}).get('games', [])
            print(f"Encontrados {len(games)} jogos hoje!")
            for game in games[:10]:
                home = game.get('homeTeam', {}).get('teamTricode', 'N/A')
                away = game.get('awayTeam', {}).get('teamTricode', 'N/A')
                print(f"  {away} vs {home}")
        else:
            print(f"Erro {resp.status_code} na NBA CDN")
    except Exception as e:
        print(f"Erro nos jogos: {e}")

    # 2. Playoffs 2026 (via NBA API direta)
    try:
        print("\nBuscando playoffs 2026...")
        # Use the correct parameter name
        from nba_api.stats.endpoints import playoffpicture
        playoffs = playoffpicture.PlayoffPicture(season_id='2025-26')
        data = playoffs.get_data_frames()
        print(f"Playoffs 2026 data encontrado!")
        if len(data) > 0:
            print(f"  Times no Leste: {len(data[0])}")
        if len(data) > 1:
            print(f"  Times no Oeste: {len(data[1])}")
    except Exception as e:
        print(f"Erro nos playoffs: {e}")

    # 3. Estatísticas de jogadores (Top 50 Playoffs 2026)
    try:
        print("\nBuscando estatísticas de jogadores 2025-26 (Playoffs)...")
        from nba_api.stats.endpoints import leaguedashptstats
        player_stats = leaguedashptstats.LeagueDashPtStats(
            season='2025-26',
            season_type_all_star='Playoffs'
        )
        df = player_stats.get_data_frames()[0]
        print(f"Encontrados {len(df)} jogadores nos playoffs 2026!\n")
        print("Top 10 jogadores (PPG):")
        if 'PTS' in df.columns and 'GP' in df.columns:
            df['PPG'] = df['PTS'] / df['GP']
            top_10 = df.nlargest(10, 'PPG')
            for idx, row in top_10.iterrows():
                player_name = row.get('PLAYER_NAME', 'N/A')
                ppg = row.get('PPG', 0)
                rpg = row.get('REB', 0) / max(row.get('GP', 1), 1)
                apg = row.get('AST', 0) / max(row.get('GP', 1), 1)
                fg_pct = row.get('FG_PCT', 0)
                print(f"  {idx+1}. {player_name}: {ppg:.1f} PPG, {rpg:.1f} RPG, {apg:.1f} APG, {fg_pct:.3f} FG%")
    except Exception as e:
        print(f"Erro nas estatísticas: {e}")

    # 4. Lesões (Injury Report - via ESPN)
    try:
        print("\nBuscando relatório de lesões...")
        url = "https://www.espn.com/nba/injuries"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            print("ESPN Injury page acessada! (Conteúdo JS dinâmico - use Playwright)")
        else:
            print(f"Erro {resp.status_code} no injury report")
    except Exception as e:
        print(f"Erro nas lesões: {e}")

    print("\nBusca concluída!")
    print("\nDica: Como o WebFetch não lê JavaScript, você pode:")
    print("   1. Me dizer os dados e eu atualizo o dashboard")
    print("   2. Rodar o Playwright localmente: python fetch_espn_data.py")
    print("   3. Usar o navegador para ver a ESPN e me passar os dados")

if __name__ == "__main__":
    fetch_real_data()
