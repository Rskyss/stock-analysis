import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from .config import FACTOR_CONFIG

class WeightAdjuster:
    def __init__(self):
        self.config = FACTOR_CONFIG
        self.base_weights = self.config['weights']
        
    def analyze_market_state(self, price_data, window=20):
        """
        分析市场状态
        params:
            price_data: pd.DataFrame - 价格数据
            window: int - 分析窗口（默认20天）
        returns:
            dict - 市场状态分析结果
        """
        try:
            # 计算收益率
            returns = price_data['Close'].pct_change()
            
            # 计算趋势强度
            ma_short = price_data['Close'].rolling(window=5).mean()
            ma_long = price_data['Close'].rolling(window=20).mean()
            trend_strength = (ma_short.iloc[-1] / ma_long.iloc[-1] - 1)
            
            # 计算波动率
            volatility = returns.rolling(window=window).std() * np.sqrt(252)
            current_volatility = volatility.iloc[-1]
            
            # 计算成交量趋势
            volume_ma = price_data['Volume'].rolling(window=window).mean()
            volume_trend = (price_data['Volume'].iloc[-1] / volume_ma.iloc[-1] - 1)
            
            return {
                'trend_strength': trend_strength,
                'volatility': current_volatility,
                'volume_trend': volume_trend,
                'market_type': self._classify_market(trend_strength, current_volatility)
            }
            
        except Exception as e:
            print(f"市场状态分析错误: {str(e)}")
            return None
    
    def _classify_market(self, trend_strength, volatility):
        """
        根据趋势强度和波动率分类市场状态
        """
        if trend_strength > self.config['market_state']['bull_threshold']:
            if volatility > 0.3:
                return 'VOLATILE_BULL'
            return 'STEADY_BULL'
        elif trend_strength < self.config['market_state']['bear_threshold']:
            if volatility > 0.3:
                return 'VOLATILE_BEAR'
            return 'STEADY_BEAR'
        else:
            if volatility > 0.3:
                return 'VOLATILE_SIDEWAYS'
            return 'STEADY_SIDEWAYS'
    
    def adjust_weights_by_market(self, market_state):
        """
        根据市场状态调整权重
        """
        adjusted_weights = self.base_weights.copy()
        
        market_type = market_state['market_type']
        if market_type == 'STEADY_BULL':
            # 稳定牛市：增加技术面和情绪面权重
            self._adjust_category_weight(adjusted_weights, 'technical', 1.2)
            self._adjust_category_weight(adjusted_weights, 'sentiment', 1.2)
            self._adjust_category_weight(adjusted_weights, 'fundamental', 0.8)
            
        elif market_type == 'VOLATILE_BULL':
            # 波动牛市：增加风险控制权重
            self._adjust_category_weight(adjusted_weights, 'risk', 1.3)
            self._adjust_category_weight(adjusted_weights, 'technical', 1.1)
            
        elif market_type == 'STEADY_BEAR':
            # 稳定熊市：增加基本面权重
            self._adjust_category_weight(adjusted_weights, 'fundamental', 1.3)
            self._adjust_category_weight(adjusted_weights, 'risk', 1.2)
            self._adjust_category_weight(adjusted_weights, 'technical', 0.7)
            
        elif market_type == 'VOLATILE_BEAR':
            # 波动熊市：大幅增加风险控制权重
            self._adjust_category_weight(adjusted_weights, 'risk', 1.5)
            self._adjust_category_weight(adjusted_weights, 'fundamental', 1.2)
            self._adjust_category_weight(adjusted_weights, 'technical', 0.6)
            
        # 重新归一化权重
        self._normalize_weights(adjusted_weights)
        return adjusted_weights
    
    def _adjust_category_weight(self, weights, category, factor):
        """调整某个类别的权重"""
        weights[category]['weight'] *= factor
    
    def _normalize_weights(self, weights):
        """归一化权重"""
        total_weight = sum(w['weight'] for w in weights.values())
        for category in weights:
            weights[category]['weight'] /= total_weight
    
    def adjust_weights_by_volatility(self, weights, volatility):
        """根据波动率调整权重"""
        if volatility > 0.4:  # 高波动率
            self._adjust_category_weight(weights, 'risk', 1.3)
            self._adjust_category_weight(weights, 'technical', 0.8)
        elif volatility < 0.1:  # 低波动率
            self._adjust_category_weight(weights, 'technical', 1.2)
            self._adjust_category_weight(weights, 'risk', 0.8)
        
        self._normalize_weights(weights)
        return weights
    
    def adjust_weights_by_volume(self, weights, volume_trend):
        """根据成交量趋势调整权重"""
        if volume_trend > 0.5:  # 放量
            self._adjust_category_weight(weights, 'technical', 1.2)
            self._adjust_category_weight(weights, 'sentiment', 1.1)
        elif volume_trend < -0.5:  # 缩量
            self._adjust_category_weight(weights, 'fundamental', 1.2)
            self._adjust_category_weight(weights, 'technical', 0.9)
        
        self._normalize_weights(weights)
        return weights
    
    def get_adjusted_weights(self, price_data):
        """
        获取综合调整后的权重
        """
        try:
            # 分析市场状态
            market_state = self.analyze_market_state(price_data)
            if not market_state:
                return self.base_weights
            
            # 根据市场状态调整权重
            weights = self.adjust_weights_by_market(market_state)
            
            # 根据波动率调整权重
            weights = self.adjust_weights_by_volatility(
                weights, 
                market_state['volatility']
            )
            
            # 根据成交量调整权重
            weights = self.adjust_weights_by_volume(
                weights,
                market_state['volume_trend']
            )
            
            return weights
            
        except Exception as e:
            print(f"权重调整错误: {str(e)}")
            return self.base_weights 