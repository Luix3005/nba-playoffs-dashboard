#!/usr/bin/env python3
"""
Automacao para pegar dados REAIS da ESPN Brasil NBA 2026
Usa Playwright para sites dinamicos (JavaScript)
"""

import asyncio
import json
from playwright.async_api import async_playwright

async def fetch_espn_data():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # 1. Playoffs Bracket
        print("Acessando ESPN Brasil NBA Playoffs 2026...")
        try:
            await page.goto("https://www.espn.com.br/nba/playoffs/2026", wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(3000)

            # Screenshot
            await page.screenshot(path="espn_playoffs_2026.png")
            print("Screenshot salvo: espn_playoffs_2026.png")

            # Try to extract bracket
            bracket = await page.evaluate("""
                () => {
                    const data = [];
                    const selectors = [
                        '.bracket__series',
                        '.bracket-series',
                        '[data-testid="bracket-series"]',
                        '.coralSeries'
                    ];

                    for (let sel of selectors) {
                        const items = document.querySelectorAll(sel);
                        if (items.length > 0) {
                            items.forEach((item, i) => {
                                const teamA = item.querySelector('.bracket__team--top') || item.querySelector('.team-top');
                                const teamB = item.querySelector('.bracket__team--bottom') || item.querySelector('.team-bottom');
                                data.push({
                                    series: i + 1,
                                    teamA: teamA ? teamA.innerText.trim() : 'N/A',
                                    teamB: teamB ? teamB.innerText.trim() : 'N/A'
                                });
                            });
                            break;
                        }
                    }
                    return data;
                }
            """)
            print(f"Bracket encontrado: {len(bracket)} series")
            for s in bracket:
                print(f"  Serie {s['series']}: {s['teamA']} vs {s['teamB']}")

        except Exception as e:
            print(f"Erro no bracket: {e}")

        # 2. Player Stats
        print("\nAcessando estatisticas de jogadores...")
        try:
            await page.goto("https://www.espn.com.br/nba/estatisticas/jogadores/_/temporada/2026/tipodetemporada/2", wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(3000)

            # Extract player data
            players = await page.evaluate("""
                () => {
                    const data = [];
                    const rows = document.querySelectorAll('table tbody tr');
                    rows.forEach((row, i) => {
                        if (i < 100) {
                            const cols = row.querySelectorAll('td');
                            if (cols.length >= 6) {
                                data.push({
                                    rank: cols[0]?.innerText || '',
                                    name: cols[1]?.innerText || '',
                                    team: cols[2]?.innerText || '',
                                    ppg: cols[3]?.innerText || '',
                                    rpg: cols[4]?.innerText || '',
                                    apg: cols[5]?.innerText || ''
                                });
                            }
                        }
                    });
                    return data;
                }
            """)

            print(f"Encontrados {len(players)} jogadores")
            for p in players[:15]:
                print(f"  {p['rank']}. {p['name']} ({p['team']}): {p['ppg']} PPG, {p['rpg']} RPG, {p['apg']} APG")

            # Save to JSON
            output = {"players": players, "bracket": bracket if 'bracket' in locals() else []}
            with open("espn_data_2026.json", "w", encoding="utf-8") as f:
                json.dump(output, f, ensure_ascii=False, indent=2)

            print("\nDados salvos em: espn_data_2026.json")

        except Exception as e:
            print(f"Erro nas estatisticas: {e}")

        # 3. Injury Report
        print("\nAcessando relatorio de lesoes...")
        try:
            await page.goto("https://www.espn.com.br/nba/lesoes", wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(2000)

            injuries = await page.evaluate("""
                () => {
                    const data = [];
                    const rows = document.querySelectorAll('table tbody tr');
                    rows.forEach((row, i) => {
                        if (i < 50) {
                            const cols = row.querySelectorAll('td');
                            if (cols.length >= 3) {
                                data.push({
                                    player: cols[0]?.innerText || '',
                                    team: cols[1]?.innerText || '',
                                    status: cols[2]?.innerText || ''
                                });
                            }
                        }
                    });
                    return data;
                }
            """)

            print(f"Encontrados {len(injuries)} lesoes")
            for inj in injuries[:10]:
                print(f"  {inj['player']} ({inj['team']}): {inj['status']}")

        except Exception as e:
            print(f"Erro no injury report: {e}")

        await browser.close()
        print("\nAutomacao concluida!")

if __name__ == "__main__":
    print("Iniciando Playwright para ESPN Brasil...\n")
    asyncio.run(fetch_espn_data())
