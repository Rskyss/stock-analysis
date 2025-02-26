import yfinance as yf
import pandas as pd
import requests
from datetime import datetime, timedelta
from .config import API_CONFIG

class DataFetcher:
    def __init__(self):
        self.cache = {}  # 简单的内存缓存
        
    def get_stock_data(self, symbol: str, start_date: str, end_date: str = None):
        """获取股票基础数据"""
        try:
            # 使用缓存键
            cache_key = f"{symbol}_{start_date}_{end_date}"
            if cache_key in self.cache:
                return self.cache[cache_key]
            
            # 获取数据
            stock = yf.Ticker(symbol)
            hist = stock.history(start=start_date, end=end_date)
            
            # 移除时区信息并格式化日期
            hist.index = hist.index.tz_localize(None)
            hist.index = hist.index.strftime('%Y-%m-%d')
            
            # 获取财务数据
            financial_data = {}
            try:
                print(f"\n获取 {symbol} 的财务数据...")
                
                # 获取基础信息
                info = stock.info
                
                # 获取资产负债表
                balance_sheet = stock.balance_sheet
                if not balance_sheet.empty:
                    latest = balance_sheet.iloc[:, 0]
                    # 尝试更多可能的字段名
                    total_liabilities = float(
                        latest.get('Total Liabilities') or 
                        latest.get('TotalLiab') or 
                        latest.get('Total Debt') or 
                        stock.info.get('totalDebt', 0)
                    )
                    total_assets = float(latest.get('Total Assets', 0) or latest.get('TotalAssets', 0))
                    total_equity = float(latest.get('Total Stockholder Equity', 0) or latest.get('StockholderEquity', 0))
                    
                    # 如果股东权益为0，从资产负债计算
                    if total_equity == 0 and total_assets > 0:
                        total_equity = total_assets - total_liabilities
                    
                    # 单位转换（转为百万）
                    if total_assets > 1e9:
                        total_assets /= 1e6
                        total_liabilities /= 1e6
                        total_equity /= 1e6
                    
                    financial_data.update({
                        'Total Assets': total_assets,
                        'Total Liabilities': total_liabilities,
                        'Total Equity': total_equity
                    })
                
                # 获取利润表数据
                income_stmt = stock.income_stmt
                if not income_stmt.empty:
                    latest = income_stmt.iloc[:, 0]
                    net_income = float(latest.get('Net Income', 0) or 0)
                    if net_income > 1e9:
                        net_income /= 1e6
                    financial_data['Net Income'] = net_income
                
                # 计算关键比率
                if financial_data.get('Total Equity', 0) > 0:
                    financial_data['ROE'] = financial_data['Net Income'] / financial_data['Total Equity']
                else:
                    financial_data['ROE'] = 0
                    
                if financial_data.get('Total Assets', 0) > 0:
                    financial_data['DebtRatio'] = financial_data['Total Liabilities'] / financial_data['Total Assets']
                else:
                    financial_data['DebtRatio'] = 0
                
                # 打印获取到的数据
                print("\n获取到的财务数据（百万）:")
                for key, value in financial_data.items():
                    print(f"{key}: {value:,.2f}")
                
                data = {
                    'price_data': hist,
                    'basic_info': info,
                    'financial_data': financial_data
                }
                
                # 存入缓存
                self.cache[cache_key] = data
                return data
                
            except Exception as e:
                print(f"财务数据获取错误: {str(e)}")
                return None
                
        except Exception as e:
            print(f"数据获取失败: {str(e)}")
            return None
    
    def clear_cache(self):
        """清除缓存"""
        self.cache.clear() 