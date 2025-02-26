import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class DataValidator:
    def __init__(self):
        # 定义异常检测阈值
        self.thresholds = {
            'price': {
                'max_daily_change': 0.2,  # 最大日涨跌幅
                'min_price': 0.01,        # 最小价格
                'max_price_gap': 0.1      # 最大价格跳空比例
            },
            'financial': {
                'max_debt_ratio': 0.95,   # 最大负债率
                'min_cash_ratio': 0.05,   # 最小现金比率
                'max_roe': 1.0,           # 最大ROE
                'min_total_assets': 0     # 最小总资产
            },
            'volume': {
                'min_volume': 1000,       # 最小成交量
                'max_volume_change': 10   # 最大成交量变化倍数
            }
        }
        
    def validate_price_data(self, price_data):
        """
        验证价格数据的合理性
        params:
            price_data: pd.DataFrame - 包含OHLCV的DataFrame
        returns:
            dict - 验证结果和异常信息
        """
        if not isinstance(price_data, pd.DataFrame):
            return {'valid': False, 'errors': ['价格数据格式错误']}
            
        errors = []
        warnings = []
        
        # 检查必要的列
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        missing_columns = [col for col in required_columns if col not in price_data.columns]
        if missing_columns:
            errors.append(f'缺少必要的列: {missing_columns}')
            return {'valid': False, 'errors': errors}
            
        # 检查数据连续性
        date_index = pd.DatetimeIndex(price_data.index)
        date_gaps = date_index[1:] - date_index[:-1]
        large_gaps = date_gaps[date_gaps > timedelta(days=5)]
        if not large_gaps.empty:
            warnings.append(f'发现数据缺失: {large_gaps}')
            
        # 检查价格异常
        daily_returns = price_data['Close'].pct_change()
        abnormal_returns = daily_returns[abs(daily_returns) > self.thresholds['price']['max_daily_change']]
        if not abnormal_returns.empty:
            warnings.append(f'发现异常价格变动: {abnormal_returns}')
            
        # 检查成交量异常
        volume_change = price_data['Volume'].pct_change()
        abnormal_volumes = volume_change[abs(volume_change) > self.thresholds['volume']['max_volume_change']]
        if not abnormal_volumes.empty:
            warnings.append(f'发现异常成交量: {abnormal_volumes}')
            
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
        
    def validate_financial_data(self, financial_data):
        """
        验证财务数据的合理性
        params:
            financial_data: dict - 财务数据字典
        returns:
            dict - 验证结果和异常信息
        """
        if not isinstance(financial_data, dict):
            return {'valid': False, 'errors': ['财务数据格式错误']}
            
        errors = []
        warnings = []
        
        # 检查关键财务指标
        if financial_data.get('Total Assets', 0) < self.thresholds['financial']['min_total_assets']:
            errors.append('总资产异常')
            
        # 计算并检查负债率
        total_assets = financial_data.get('Total Assets', 0)
        total_liabilities = financial_data.get('Total Liabilities', 0)
        if total_assets > 0:
            debt_ratio = total_liabilities / total_assets
            if debt_ratio > self.thresholds['financial']['max_debt_ratio']:
                warnings.append(f'负债率过高: {debt_ratio:.2%}')
                
        # 检查ROE合理性
        net_income = financial_data.get('Net Income', 0)
        total_equity = financial_data.get('Total Equity', 1)
        roe = net_income / total_equity
        if abs(roe) > self.thresholds['financial']['max_roe']:
            warnings.append(f'ROE异常: {roe:.2%}')
            
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        } 