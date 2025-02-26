import numpy as np
import pandas as pd

class RiskMetrics:
    @staticmethod
    def calculate_var(returns, confidence=0.95):
        """
        计算历史VaR (Value at Risk)
        params:
            returns: pd.Series - 收益率序列
            confidence: float - 置信度，默认95%
        returns:
            float - VaR值
        """
        if not isinstance(returns, pd.Series):
            returns = pd.Series(returns)
        return abs(returns.quantile(1 - confidence))
    
    @staticmethod
    def calculate_max_drawdown(prices):
        """
        计算最大回撤
        params:
            prices: pd.Series - 价格序列
        returns:
            float - 最大回撤比例
            int - 最大回撤开始位置
            int - 最大回撤结束位置
        """
        # 转换为Series类型
        if not isinstance(prices, pd.Series):
            prices = pd.Series(prices)
            
        # 计算累计最大值
        rolling_max = prices.expanding().max()
        # 计算每个时点的回撤
        drawdowns = prices / rolling_max - 1
        # 获取最大回撤及其位置
        max_drawdown = drawdowns.min()
        end_idx = drawdowns.idxmin()
        # 找到最大回撤区间的开始位置
        start_idx = prices[:end_idx].idxmax()
        
        return abs(max_drawdown), start_idx, end_idx
    
    @staticmethod
    def calculate_volatility(returns, window=252):
        """
        计算波动率
        params:
            returns: pd.Series - 收益率序列
            window: int - 计算窗口，默认252个交易日（一年）
        returns:
            pd.Series - 滚动波动率
        """
        return returns.rolling(window=window).std() * np.sqrt(window)
    
    @staticmethod
    def calculate_sharpe_ratio(returns, risk_free_rate=0.03, periods=252):
        """
        计算夏普比率
        params:
            returns: pd.Series - 收益率序列
            risk_free_rate: float - 无风险利率，默认3%
            periods: int - 年化周期，默认252个交易日
        returns:
            float - 夏普比率
        """
        excess_returns = returns - risk_free_rate/periods
        return np.sqrt(periods) * (excess_returns.mean() / excess_returns.std()) 