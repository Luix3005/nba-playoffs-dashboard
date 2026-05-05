#!/usr/bin/env python3
"""
Busca dados REAIS da NBA usando balldontlie (gratuito, sem API key)
Puxa: jogos de hoje, playoffs 2026, estatísticas, lesões
"""

import json
from balldontlie import BalldontlieAPI

def fetch_real_data():
    # balldontlie uses the free NBA API (no key needed for basic stuff)
    # But actualy it needs a key - let me try alternative approach

    print("🚀 Iniciando busca de dados NBA 2026...\n")

    # Alternative: Use nba-api package
    try:
        import requests

        # 1. Get today's games
        print("📅 Buscando jogos de hoje...")
        today = "2026-04-30"
        url = f"https://data.nba.com/data/10s/v2015/json/mobile_teams/nba/2026/scores/gamedate/LIVE.json"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            print(f"✅ Jogos de hoje encontrados!")
            print(json.dumps(data, indent=2)[:500])
        else:
            print(f"❌ Erro {resp.status_code} na NBA API")

    except Exception as e:
        print(f"❌ Erro: {e}")

    # 2. Try ESPN public API
    try:
        print("\n🌐 Tentando ESPN API...")
        url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates=20260430"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            events = data.get('events', [])
            print(f"✅ ESPN API funcionou! {len(events)} eventos encontrados")
            for ev in events[:5]:
                print(f"  - {ev['name']}: {ev['competitions'][0]['competitors'][0]['team']['displayName']} vs {ev['competitions'][0]['competitors'][1]['team']['displayName']}")
        else:
            print(f"❌ ESPN API erro: {resp.status_code}")

    except Exception as e:
        print(f"❌ Erro ESPN: {e}")

    # 3. Try TheRundown API (free tier)
    try:
        print("\n🏀 Tentando TheRundown...")
        url = "https://therundown.com/api/sports/nba"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            print("✅ TheRundown funcionou!")
            print(resp.text[:300])
    except Exception as e:
        print(f"❌ Erro: {e}")

    print("\n💡 Dica: Como o WebFetch não lê JavaScript, você pode:")
    print("   1. Me dizer os dados e eu atualizo o dashboard")
    print("   2. Rodar o Playwright localmente: python fetch_espn_data.py")
    print("   3. Usar o navegador para ver a ESPN e me passar os dados")

if __name__ == "__main__":
    fetch_real_data()
