import yfinance as yf
import pandas as pd
import numpy as np
import requests
import re

class RiskAnalyzer:
    def __init__(self):
        self._cache = {}

    # ───────────────────────── Market Data with Google Finance Fallback ─────────
    def get_market_data(self, symbol):
        if not symbol.endswith('.NS') and not symbol.endswith('.BO'):
            if symbol.isdigit():
                symbol += '.BO'  # BSE scrip codes are numeric
            else:
                symbol += '.NS'  # NSE symbols are alphabetic

        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            hist = ticker.history(period="5y")

            if info and info.get('currentPrice') or info.get('regularMarketPrice'):
                self._cache[symbol] = (info, hist)
                return info, hist
        except Exception as e:
            print(f"Yahoo Finance failed for {symbol}: {e}")

        # ── Fallback: Google Finance scraping ──
        try:
            clean_sym = symbol.replace('.NS', '').replace('.BO', '')
            url = f"https://www.google.com/finance/quote/{clean_sym}:NSE"
            headers = {'User-Agent': 'Mozilla/5.0'}
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                price_match = re.search(r'data-last-price="([\d.]+)"', resp.text)
                if price_match:
                    price = float(price_match.group(1))
                    fallback_info = {'currentPrice': price, 'symbol': symbol}
                    return fallback_info, pd.DataFrame()
        except Exception as e:
            print(f"Google Finance fallback also failed: {e}")

        return None, None

    # ───────────────────────── VaR & Volatility ────────────────────────────────
    def calculate_var_and_volatility(self, hist):
        if hist is None or hist.empty or len(hist) < 30:
            return None, None

        returns = hist['Close'].pct_change().dropna()
        volatility = returns.std() * np.sqrt(252)
        var_95 = np.percentile(returns, 5)
        return volatility, var_95

    # ───────────────────────── Altman Z-Score ──────────────────────────────────
    def calculate_altman_z_score(self, info):
        try:
            total_assets = info.get('totalAssets', 1)
            total_liabilities = info.get('totalLiabilities', 1)
            working_capital = total_assets - total_liabilities
            retained_earnings = info.get('retainedEarnings', 0)
            ebitda = info.get('ebitda', 0)
            market_cap = info.get('marketCap', 0)
            revenue = info.get('totalRevenue', 0)

            x1 = working_capital / total_assets
            x2 = retained_earnings / total_assets
            x3 = ebitda / total_assets
            x4 = market_cap / total_liabilities
            x5 = revenue / total_assets

            z_score = (1.2 * x1) + (1.4 * x2) + (3.3 * x3) + (0.6 * x4) + (1.0 * x5)

            if z_score > 2.6:
                zone = "Safe Zone"
            elif z_score > 1.8:
                zone = "Grey Zone"
            else:
                zone = "Distress Zone"

            return z_score, zone
        except Exception:
            return None, "Unknown"

    # ───────────────────────── Moving Averages (5-year historical) ─────────────
    def calculate_moving_averages(self, hist):
        if hist is None or len(hist) < 200:
            return None, None

        sma_50 = hist['Close'].rolling(window=50).mean().iloc[-1]
        sma_200 = hist['Close'].rolling(window=200).mean().iloc[-1]
        return sma_50, sma_200

    # ───────────────────────── Piotroski F-Score (9-point) ─────────────────────
    def calculate_piotroski_f_score(self, info):
        try:
            score = 0
            details = []

            # 1. Positive net income
            net_income = info.get('netIncomeToCommon', 0)
            if net_income > 0:
                score += 1
                details.append("Net Income positive (+1)")

            # 2. Positive ROA
            roa = info.get('returnOnAssets', 0)
            if roa and roa > 0:
                score += 1
                details.append("ROA positive (+1)")

            # 3. Positive operating cash flow
            ocf = info.get('operatingCashflow', 0)
            if ocf and ocf > 0:
                score += 1
                details.append("Operating Cash Flow positive (+1)")

            # 4. Cash flow > net income (accruals quality)
            if ocf and net_income and ocf > net_income:
                score += 1
                details.append("Cash Flow > Net Income (+1)")

            # 5. Lower long-term debt ratio (assume positive if D/E < 1)
            debt_to_equity = info.get('debtToEquity', 0)
            if debt_to_equity and debt_to_equity < 100:
                score += 1
                details.append("Debt/Equity < 1.0 (+1)")

            # 6. Current ratio improvement (proxy: current ratio > 1)
            current_ratio = info.get('currentRatio', 0)
            if current_ratio and current_ratio > 1:
                score += 1
                details.append("Current Ratio > 1 (+1)")

            # 7. No share dilution (shares outstanding stable)
            if info.get('sharesOutstanding') and info.get('floatShares'):
                if info['sharesOutstanding'] <= info['floatShares'] * 1.1:
                    score += 1
                    details.append("No significant dilution (+1)")

            # 8. Gross margin improvement (proxy: gross margins > 30%)
            gross_margins = info.get('grossMargins', 0)
            if gross_margins and gross_margins > 0.30:
                score += 1
                details.append("Gross Margins > 30% (+1)")

            # 9. Asset turnover (revenue/total assets)
            total_assets = info.get('totalAssets', 1)
            revenue = info.get('totalRevenue', 0)
            if total_assets and revenue:
                turnover = revenue / total_assets
                if turnover > 0.5:
                    score += 1
                    details.append("Asset Turnover > 0.5 (+1)")

            return score, details
        except Exception:
            return None, []

    # ───────────────────────── Beneish M-Score (earnings manipulation) ─────────
    def calculate_beneish_m_score(self, info):
        try:
            # Simplified M-Score using available yfinance data
            # M = -4.84 + 0.92×DSRI + 0.528×GMI + 0.404×AQI + 0.892×SGI
            #     + 0.115×DEPI - 0.172×SGAI + 4.679×TATA - 0.327×LVGI

            total_assets = info.get('totalAssets', 1)
            revenue = info.get('totalRevenue', 1)
            gross_margins = info.get('grossMargins', 0.5)
            net_income = info.get('netIncomeToCommon', 0)
            receivables = info.get('totalReceivables', 0) or 0
            total_liabilities = info.get('totalLiabilities', 1)
            operating_cashflow = info.get('operatingCashflow', 0) or 0

            # DSRI (Days Sales in Receivables Index) — proxy
            dsri = (receivables / revenue * 365) / 45 if revenue else 1.0

            # GMI (Gross Margin Index) — proxy: inverse of current margins
            gmi = 1.0 / gross_margins if gross_margins and gross_margins > 0 else 2.0

            # AQI (Asset Quality Index) — proxy
            current_assets = total_assets * 0.4
            ppe = total_assets * 0.3
            aqi = 1.0 - ((current_assets + ppe) / total_assets)

            # SGI (Sales Growth Index) — proxy: use revenue growth
            revenue_growth = info.get('revenueGrowth', 0.1) or 0.1
            sgi = 1.0 + revenue_growth

            # DEPI (Depreciation Index) — proxy
            depi = 1.0

            # SGAI (SGA Index) — proxy
            sgai = 1.0

            # TATA (Total Accruals to Total Assets)
            tata = (net_income - operating_cashflow) / total_assets if total_assets else 0

            # LVGI (Leverage Index)
            lvgi = total_liabilities / total_assets if total_assets else 1.0

            m_score = (-4.84 + 0.92 * dsri + 0.528 * gmi + 0.404 * aqi
                       + 0.892 * sgi + 0.115 * depi - 0.172 * sgai
                       + 4.679 * tata - 0.327 * lvgi)

            if m_score > -1.78:
                flag = "Likely Manipulator"
            elif m_score > -2.22:
                flag = "Grey Zone"
            else:
                flag = "Unlikely Manipulator"

            return round(m_score, 4), flag
        except Exception:
            return None, "Unknown"

    # ───────────────────────── Implied Credit Rating ──────────────────────────
    def calculate_credit_rating(self, z_score, f_score, debt_to_equity, roe):
        try:
            composite = 0

            if z_score:
                if z_score > 3.0: composite += 30
                elif z_score > 2.6: composite += 25
                elif z_score > 1.8: composite += 15
                else: composite += 5

            if f_score is not None:
                composite += f_score * 3  # Max 27

            if debt_to_equity is not None:
                if debt_to_equity < 30: composite += 15
                elif debt_to_equity < 60: composite += 10
                elif debt_to_equity < 100: composite += 5
                else: composite += 0

            if roe is not None:
                if roe > 20: composite += 15
                elif roe > 15: composite += 12
                elif roe > 10: composite += 8
                elif roe > 5: composite += 4
                else: composite += 0

            # Max possible ~87, map to rating
            if composite >= 75: return "AAA", composite
            elif composite >= 65: return "AA", composite
            elif composite >= 55: return "A", composite
            elif composite >= 45: return "BBB", composite
            elif composite >= 35: return "BB", composite
            elif composite >= 25: return "B", composite
            elif composite >= 15: return "CCC", composite
            elif composite >= 5: return "CC", composite
            else: return "D", composite
        except Exception:
            return "N/A", 0

    # ───────────────────────── Insider & Promoter Data (NSE) ──────────────────
    def fetch_insider_data(self, symbol):
        clean_sym = symbol.replace('.NS', '').replace('.BO', '')
        result = {
            "insider_trades": [],
            "promoter_holding": None,
            "promoter_pledging": None
        }

        try:
            ticker = yf.Ticker(symbol if '.NS' in symbol or '.BO' in symbol else f"{symbol}.NS")
            holders = ticker.major_holders

            if holders is not None and not holders.empty:
                for _, row in holders.iterrows():
                    label = str(row.iloc[1]).lower() if len(row) > 1 else ""
                    value = str(row.iloc[0])
                    if 'insider' in label or 'promoter' in label:
                        try:
                            result["promoter_holding"] = float(value.replace('%', ''))
                        except ValueError:
                            result["promoter_holding"] = value

            insider_txns = ticker.insider_transactions
            if insider_txns is not None and not insider_txns.empty:
                for _, row in insider_txns.head(5).iterrows():
                    result["insider_trades"].append({
                        "name": str(row.get('Insider', 'N/A')),
                        "shares": str(row.get('Shares', 'N/A')),
                        "type": str(row.get('Transaction', 'N/A')),
                        "date": str(row.get('Start Date', 'N/A'))
                    })
        except Exception as e:
            print(f"Insider data fetch error: {e}")

        # Promoter pledging - attempt NSE scrape
        try:
            url = f"https://www.nseindia.com/api/corporate-pledgedata?index={clean_sym}"
            headers = {
                'User-Agent': 'Mozilla/5.0',
                'Accept': 'application/json'
            }
            resp = requests.get(url, headers=headers, timeout=5)
            if resp.status_code == 200:
                pledge_data = resp.json()
                if pledge_data and isinstance(pledge_data, list) and len(pledge_data) > 0:
                    latest = pledge_data[0]
                    result["promoter_pledging"] = latest.get('percPromoterPledged', 'N/A')
        except Exception:
            pass

        return result

    # ───────────────────────── Enhanced Recommendation (0-5 scale) ─────────────
    def generate_recommendation(self, z_score, debt_to_equity, roe, f_score=None, m_score=None):
        score = 0

        # Altman Z-Score contribution (max 2)
        if z_score:
            if z_score > 2.6: score += 2
            elif z_score > 1.8: score += 1
            else: score -= 2

        # Debt/Equity contribution (max 1)
        if debt_to_equity is not None:
            if debt_to_equity < 50: score += 1
            elif debt_to_equity > 100: score -= 1

        # ROE contribution (max 2)
        if roe is not None:
            if roe > 15: score += 2
            elif roe > 10: score += 1
            else: score -= 1

        # Piotroski F-Score bonus (max 1)
        if f_score is not None:
            if f_score >= 7: score += 1
            elif f_score <= 3: score -= 1

        # Beneish M-Score penalty
        if m_score is not None:
            if m_score > -1.78: score -= 2  # Likely manipulator

        # Map to 0-5 scale recommendation
        if score >= 5: return "Strong Buy"
        elif score >= 3: return "Buy"
        elif score >= 1: return "Accumulate on Dips"
        elif score >= 0: return "Hold"
        elif score >= -2: return "Reduce"
        else: return "Sell"

    # ───────────────────────── Main Analysis ──────────────────────────────────
    def analyze(self, symbol):
        if not symbol:
            return {"error": "No trading symbol provided"}

        info, hist = self.get_market_data(symbol)

        if not info:
            return {"error": f"Could not fetch data for {symbol}"}

        # Core metrics
        volatility, var_95 = self.calculate_var_and_volatility(hist)
        z_score, zone = self.calculate_altman_z_score(info)
        sma_50, sma_200 = self.calculate_moving_averages(hist)

        debt_to_equity = info.get('debtToEquity')
        roe = info.get('returnOnEquity', 0) * 100 if info.get('returnOnEquity') else None

        # Advanced scoring
        f_score, f_details = self.calculate_piotroski_f_score(info)
        m_score, m_flag = self.calculate_beneish_m_score(info)
        credit_rating, credit_composite = self.calculate_credit_rating(z_score, f_score, debt_to_equity, roe)

        # Insider & promoter data
        insider_data = self.fetch_insider_data(symbol)

        # Enhanced recommendation using all scores
        recommendation = self.generate_recommendation(z_score, debt_to_equity, roe, f_score, m_score)

        return {
            "symbol": symbol,
            "market_price": info.get('currentPrice', info.get('regularMarketPrice')),
            "market_cap": info.get('marketCap'),
            "pe_ratio": info.get('trailingPE'),
            "pb_ratio": info.get('priceToBook'),
            "roe": roe,
            "debt_to_equity": debt_to_equity,
            "volatility_annualized": float(volatility) if volatility else None,
            "var_95": float(var_95) if var_95 else None,
            "altman_z_score": float(z_score) if z_score else None,
            "altman_zone": zone,
            "sma_50": float(sma_50) if sma_50 else None,
            "sma_200": float(sma_200) if sma_200 else None,
            "piotroski_f_score": f_score,
            "piotroski_details": f_details,
            "beneish_m_score": float(m_score) if m_score else None,
            "beneish_flag": m_flag,
            "credit_rating": credit_rating,
            "credit_composite": credit_composite,
            "insider_data": insider_data,
            "recommendation": recommendation
        }
