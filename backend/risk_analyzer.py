import yfinance as yf
import pandas as pd
import numpy as np

class RiskAnalyzer:
    def __init__(self):
        pass

    def get_market_data(self, symbol):
        # Fallback handling for Indian stocks
        if not symbol.endswith('.NS') and not symbol.endswith('.BO'):
            symbol += '.NS'
            
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            hist = ticker.history(period="6mo")
            
            return info, hist
        except Exception:
            return None, None

    def calculate_var_and_volatility(self, hist):
        if hist is None or hist.empty:
            return None, None
            
        returns = hist['Close'].pct_change().dropna()
        
        # Annualized Volatility
        volatility = returns.std() * np.sqrt(252)
        
        # 95% Historical VaR
        var_95 = np.percentile(returns, 5)
        
        return volatility, var_95

    def calculate_altman_z_score(self, info):
        # Altman Z-Score = 1.2×X1 + 1.4×X2 + 3.3×X3 + 0.6×X4 + 1.0×X5
        try:
            working_capital = info.get('totalAssets', 1) - info.get('totalLiabilities', 0)
            retained_earnings = info.get('retainedEarnings', 0)
            ebitda = info.get('ebitda', 0)
            market_cap = info.get('marketCap', 0)
            total_assets = info.get('totalAssets', 1) # Prevent division by zero
            total_liabilities = info.get('totalLiabilities', 1)
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

    def calculate_moving_averages(self, hist):
        if hist is None or len(hist) < 200:
            return None, None
        
        sma_50 = hist['Close'].rolling(window=50).mean().iloc[-1]
        sma_200 = hist['Close'].rolling(window=200).mean().iloc[-1]
        return sma_50, sma_200

    def generate_recommendation(self, z_score, debt_to_equity, roe):
        score = 0
        
        if z_score:
            if z_score > 2.6: score += 2
            elif z_score > 1.8: score += 1
            else: score -= 2
            
        if debt_to_equity:
            if debt_to_equity < 50: score += 1
            elif debt_to_equity > 100: score -= 1
            
        if roe:
            if roe > 15: score += 2
            elif roe > 10: score += 1
            else: score -= 1
            
        if score >= 4: return "Strong Buy"
        elif score >= 2: return "Buy"
        elif score == 1: return "Accumulate on Dips"
        elif score == 0: return "Hold"
        elif score >= -2: return "Reduce"
        else: return "Sell"

    def analyze(self, symbol):
        if not symbol:
            return {"error": "No trading symbol provided"}
            
        info, hist = self.get_market_data(symbol)
        
        if not info:
            return {"error": f"Could not fetch data for {symbol}"}
            
        volatility, var_95 = self.calculate_var_and_volatility(hist)
        z_score, zone = self.calculate_altman_z_score(info)
        sma_50, sma_200 = self.calculate_moving_averages(hist)
        
        debt_to_equity = info.get('debtToEquity')
        roe = info.get('returnOnEquity', 0) * 100 if info.get('returnOnEquity') else None
        
        recommendation = self.generate_recommendation(z_score, debt_to_equity, roe)
        
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
            "recommendation": recommendation
        }
