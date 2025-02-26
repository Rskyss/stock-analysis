import numpy as np
import pandas as pd
from .config import INDICATOR_CONFIG

class TechnicalIndicators:
    @staticmethod
    def calculate_ma(close_prices, periods=None):
        """计算多个周期的移动平均线"""
        if periods is None:
            periods = INDICATOR_CONFIG['technical']['ma_periods']
        
        ma_dict = {}
        for period in periods:
            ma_dict[f'MA{period}'] = close_prices.rolling(window=period).mean()
        return pd.DataFrame(ma_dict)
    
    @staticmethod
    def calculate_rsi(close_prices, period=None):
        """计算RSI指标"""
        if period is None:
            period = INDICATOR_CONFIG['technical']['rsi_period']
            
        delta = close_prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def calculate_bollinger_bands(close_prices):
        """计算布林带"""
        period = INDICATOR_CONFIG['technical']['bollinger_period']
        std_dev = INDICATOR_CONFIG['technical']['bollinger_std']
        
        ma = close_prices.rolling(window=period).mean()
        std = close_prices.rolling(window=period).std()
        
        upper_band = ma + (std * std_dev)
        lower_band = ma - (std * std_dev)
        
        return pd.DataFrame({
            'middle': ma,
            'upper': upper_band,
            'lower': lower_band
        })

    @staticmethod
    def calculate_atr(high, low, close, period=14):
        """计算ATR"""
        tr = pd.DataFrame()
        tr['HL'] = high - low
        tr['HC'] = abs(high - close.shift(1))
        tr['LC'] = abs(low - close.shift(1))
        tr['TR'] = tr.max(axis=1)
        return tr['TR'].ewm(span=period).mean()

    @staticmethod
    def calculate_obv(close, volume):
        """计算OBV"""
        obv = pd.Series(index=close.index, dtype=float)
        obv.iloc[0] = volume.iloc[0]
        for i in range(1, len(close)):
            if close.iloc[i] > close.iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] + volume.iloc[i]
            elif close.iloc[i] < close.iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] - volume.iloc[i]
            else:
                obv.iloc[i] = obv.iloc[i-1]
        return obv

    @staticmethod
    def calculate_adx(high, low, close, period=14):
        """计算ADX"""
        # 计算+DM和-DM
        plus_dm = high.diff()
        minus_dm = low.diff()
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm > 0] = 0
        
        # 计算TR
        tr = pd.DataFrame()
        tr['HL'] = high - low
        tr['HC'] = abs(high - close.shift(1))
        tr['LC'] = abs(low - close.shift(1))
        tr['TR'] = tr.max(axis=1)
        
        # 计算+DI和-DI
        plus_di = 100 * plus_dm.ewm(span=period).mean() / tr['TR'].ewm(span=period).mean()
        minus_di = 100 * abs(minus_dm.ewm(span=period).mean()) / tr['TR'].ewm(span=period).mean()
        
        # 计算DX和ADX
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.ewm(span=period).mean()
        
        return adx

class FundamentalIndicators:
    @staticmethod
    def safe_convert_to_float(value):
        """安全地将值转换为浮点数"""
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            # 移除可能的百分号和其他字符
            value = value.replace('%', '').replace(',', '')
            try:
                return float(value)
            except ValueError:
                return 0.0
        return 0.0

    @staticmethod
    def calculate_financial_ratios(financial_data):
        """计算财务指标"""
        try:
            # 现有的ROE和负债率计算
            net_income = financial_data.get('Net Income', 0)
            total_equity = financial_data.get('Total Equity', 1)
            roe = net_income / total_equity
            
            # 添加FCF计算
            operating_cash_flow = financial_data.get('Operating Cash Flow', 0)
            capital_expenditure = financial_data.get('Capital Expenditure', 0)
            fcf = operating_cash_flow - capital_expenditure
            
            # 添加EV/EBITDA计算
            market_cap = financial_data.get('Market Cap', 0)
            total_debt = financial_data.get('Total Liabilities', 0)
            cash = financial_data.get('Cash', 0)
            ebitda = financial_data.get('EBITDA', 1)
            ev_ebitda = (market_cap + total_debt - cash) / ebitda
            
            # 添加股息保障倍数计算
            preferred_dividends = financial_data.get('Preferred Dividends', 0)
            common_dividends = financial_data.get('Common Dividends', 1)
            dividend_coverage = (net_income - preferred_dividends) / common_dividends
            
            return {
                'ROE': roe,
                'DebtRatio': total_debt / financial_data.get('Total Assets', 1),
                'FCF': fcf,
                'EV/EBITDA': ev_ebitda,
                'DividendCoverage': dividend_coverage
            }
        except Exception as e:
            print(f"财务指标计算错误: {str(e)}")
            return None 