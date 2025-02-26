import numpy as np
import pandas as pd
from scipy import stats
from .config import FACTOR_CONFIG
from .weight_adjuster import WeightAdjuster
from .indicators import TechnicalIndicators

class MultiFactorModel:
    def __init__(self):
        self.config = FACTOR_CONFIG
        self.weights = self.config['weights']
        self.weight_adjuster = WeightAdjuster()
        self.current_weights = self.weights.copy()  # 用于动态调整
        
    def normalize_factor(self, factor_data, method='zscore'):
        """标准化因子数据"""
        try:
            # 确保数据是数组且不为空
            factor_data = np.array(factor_data, dtype=float)
            if len(factor_data) == 0:
                return np.array([0.0])
            
            # 处理单个值的情况
            if len(factor_data) == 1:
                # 如果是单个值，使用预设的参考范围进行归一化
                reference_ranges = {
                    'roe': (0, 0.4),        # ROE范围 0-40%
                    'debt_ratio': (0, 1),    # 负债率范围 0-100%
                    'cash_ratio': (0, 0.5),  # 现金比率范围 0-50%
                }
                
                # 默认使用 0-1 范围
                min_val, max_val = 0, 1
                
                # 根据数据特征选择合适的范围
                for key, (low, high) in reference_ranges.items():
                    if key in str(factor_data).lower():
                        min_val, max_val = low, high
                        break
                
                # 使用 min-max 归一化
                normalized = (factor_data - min_val) / (max_val - min_val)
                return np.clip(normalized, 0, 1)
            
            if method == 'zscore':
                # Winsorize处理（去极值）
                lower = np.percentile(factor_data, self.config['normalization']['winsorize'] * 100)
                upper = np.percentile(factor_data, (1 - self.config['normalization']['winsorize']) * 100)
                factor_data = np.clip(factor_data, lower, upper)
                
                # Z-score标准化
                mean = np.mean(factor_data)
                std = np.std(factor_data)
                if std == 0:
                    return np.zeros_like(factor_data)
                return (factor_data - mean) / std
                
            elif method == 'minmax':
                min_val = np.min(factor_data)
                max_val = np.max(factor_data)
                if min_val == max_val:
                    return np.zeros_like(factor_data)
                return (factor_data - min_val) / (max_val - min_val)
                
            elif method == 'rank':
                return stats.rankdata(factor_data) / len(factor_data)
                
            return factor_data
            
        except Exception as e:
            print(f"标准化过程出错: {str(e)}")
            return np.array([0.0])
    
    def calculate_fundamental_score(self, financial_data):
        """计算基本面因子得分"""
        try:
            factors = self.weights['fundamental']['factors']
            
            # 获取基础指标
            roe = financial_data.get('ROE', 0)
            debt_ratio = financial_data.get('DebtRatio', 0)
            
            print("\n原始指标值:")
            print(f"ROE: {roe:.2%}")
            print(f"负债率: {debt_ratio:.2%}")
            
            # 标准化处理
            scores = {
                'roe': float(self.normalize_factor(np.array([roe]), 'minmax')[0]),
                'debt_ratio': float(self.normalize_factor(np.array([1 - debt_ratio]), 'minmax')[0]),
                'fcf': 0.0,  # 暂时设为0
                'ev_ebitda': 0.0,  # 暂时设为0
                'dividend_coverage': 0.0  # 暂时设为0
            }
            
            print("\n标准化后得分:")
            for k, v in scores.items():
                print(f"{k}: {v:.2f}")
            
            # 加权计算
            fundamental_score = sum(
                scores[factor] * weight 
                for factor, weight in factors.items()
            )
            
            print(f"\n最终基本面得分: {fundamental_score:.2f}")
            return fundamental_score
            
        except Exception as e:
            print(f"基本面因子计算错误: {str(e)}")
            return 0.0
    
    def calculate_technical_score(self, price_data, technical_indicators):
        """计算技术面因子得分"""
        try:
            factors = self.weights['technical']['factors']
            
            # 计算技术指标
            atr = TechnicalIndicators.calculate_atr(
                price_data['High'],
                price_data['Low'],
                price_data['Close']
            )
            
            obv = TechnicalIndicators.calculate_obv(
                price_data['Close'],
                price_data['Volume']
            )
            
            adx = TechnicalIndicators.calculate_adx(
                price_data['High'],
                price_data['Low'],
                price_data['Close']
            )
            
            ma_short = technical_indicators['MA5'].iloc[-1]
            ma_long = technical_indicators['MA20'].iloc[-1]
            ma_trend = (ma_short / ma_long - 1) if ma_long != 0 else 0
            
            print("\n技术指标原始值:")
            print(f"MA趋势: {ma_trend:.2%}")
            print(f"ATR: {atr.iloc[-1]:.2f}")
            print(f"OBV: {obv.iloc[-1]:,.0f}")
            print(f"ADX: {adx.iloc[-1]:.2f}")
            
            # 修改标准化方法
            scores = {
                'ma_trend': float(self.normalize_factor(np.array([ma_trend]), 'minmax')[0]),
                'atr': float(self.normalize_factor(np.array([atr.iloc[-1]]), 'minmax')[0]),
                'obv': float(self.normalize_factor(np.array([obv.iloc[-1]]), 'minmax')[0]),
                'adx': float(self.normalize_factor(np.array([adx.iloc[-1]]), 'minmax')[0])
            }
            
            # 使用变化率来判断趋势，并限制范围
            trends = {
                'atr_trend': min(max(atr.iloc[-1] / atr.iloc[-20] - 1, -0.5), 0.5) if len(atr) >= 20 else 0,
                'obv_trend': min(max(obv.iloc[-1] / obv.iloc[-20] - 1, -0.5), 0.5) if len(obv) >= 20 else 0,
                'adx_trend': min(max(adx.iloc[-1] / adx.iloc[-20] - 1, -0.5), 0.5) if len(adx) >= 20 else 0
            }
            
            print("\n技术指标趋势:")
            for k, v in trends.items():
                print(f"{k}: {v:.2%}")
            
            technical_score = sum(
                scores[factor] * weight 
                for factor, weight in factors.items()
            )
            
            print(f"\n最终技术面得分: {technical_score:.2f}")
            return technical_score
            
        except Exception as e:
            print(f"技术面因子计算错误: {str(e)}")
            return 0.0
    
    def calculate_risk_score(self, risk_metrics):
        """计算风险因子得分"""
        try:
            factors = self.weights['risk']['factors']
            
            # 转换风险指标为评分（越低风险越高分）
            var_score = 1 - min(abs(risk_metrics.get('VaR(95%)', 0)), 0.1) * 10  # 限制VaR的影响
            sharpe_ratio = risk_metrics.get('Sharpe Ratio', 0)
            sharpe_score = min(max(sharpe_ratio, -2), 2) / 2 + 0.5  # 将夏普比率映射到[0,1]
            max_dd = abs(risk_metrics.get('Max Drawdown', 0))
            drawdown_score = 1 - min(max_dd, 0.5) * 2  # 限制最大回撤的影响
            
            scores = {
                'var': var_score,
                'sharpe': sharpe_score,
                'max_drawdown': drawdown_score
            }
            
            print("\n风险指标原始值:")
            print(f"VaR(95%): {risk_metrics.get('VaR(95%)', 0):.2%}")
            print(f"夏普比率: {sharpe_ratio:.2f}")
            print(f"最大回撤: {max_dd:.2%}")
            
            # 标准化处理
            normalized_scores = {
                k: float(self.normalize_factor(np.array([v]), 'minmax')[0])
                for k, v in scores.items()
            }
            
            print("\n风险指标标准化得分:")
            for k, v in normalized_scores.items():
                print(f"{k}: {v:.2f}")
            
            risk_score = sum(
                normalized_scores[factor] * weight 
                for factor, weight in factors.items()
            )
            
            print(f"\n最终风险得分: {risk_score:.2f}")
            return risk_score
            
        except Exception as e:
            print(f"风险因子计算错误: {str(e)}")
            return 0.0
    
    def calculate_sentiment_score(self, sentiment_data):
        """计算情绪因子得分"""
        try:
            if sentiment_data['status'] != 'success':
                return 0
                
            factors = self.weights['sentiment']['factors']
            
            scores = {
                'social_score': sentiment_data['average_sentiment'],
                'volume_sentiment': sentiment_data.get('volume_adjusted_sentiment', 0)
            }
            
            # 标准化处理
            normalized_scores = {
                k: self.normalize_factor(np.array([v]))[0] 
                for k, v in scores.items()
            }
            
            # 加权计算
            sentiment_score = sum(
                normalized_scores[factor] * weight 
                for factor, weight in factors.items()
            )
            
            return sentiment_score
            
        except Exception as e:
            print(f"情绪因子计算错误: {str(e)}")
            return 0
    
    def adjust_weights_by_market(self, price_data):
        """根据市场状态调整权重"""
        # 计算20日收益率
        returns_20d = (
            price_data['Close'].iloc[-1] / 
            price_data['Close'].iloc[-20] - 1
        )
        
        # 判断市场状态
        if returns_20d > self.config['market_state']['bull_threshold']:
            # 牛市：增加技术面和情绪面权重
            self.current_weights['technical']['weight'] *= 1.2
            self.current_weights['sentiment']['weight'] *= 1.2
            self.current_weights['fundamental']['weight'] *= 0.8
            
        elif returns_20d < self.config['market_state']['bear_threshold']:
            # 熊市：增加基本面和风险控制权重
            self.current_weights['fundamental']['weight'] *= 1.2
            self.current_weights['risk']['weight'] *= 1.2
            self.current_weights['technical']['weight'] *= 0.8
            
        # 重新归一化权重
        total_weight = sum(w['weight'] for w in self.current_weights.values())
        for category in self.current_weights:
            self.current_weights[category]['weight'] /= total_weight
    
    def calculate_final_score(self, all_data):
        """计算最终的多因子得分"""
        try:
            # 使用权重调整器获取动态权重
            self.current_weights = self.weight_adjuster.get_adjusted_weights(
                all_data['price_data']
            )
            
            # 计算各类因子得分
            scores = {}
            raw_values = {}
            normalized_scores = {}
            technical_trends = {}
            risk_scores = {}
            
            # 1. 基本面因子
            if all_data.get('financial_ratios'):
                # 获取基础指标
                roe = all_data['financial_ratios'].get('ROE', 0)
                debt_ratio = all_data['financial_ratios'].get('DebtRatio', 0)
                
                # 记录原始值
                raw_values['roe'] = roe * 100  # 转为百分比
                raw_values['debt_ratio'] = debt_ratio * 100  # 转为百分比
                
                # 标准化处理
                normalized_scores['roe'] = float(self.normalize_factor(np.array([roe]), 'minmax')[0])
                normalized_scores['debt_ratio'] = float(self.normalize_factor(np.array([1 - debt_ratio]), 'minmax')[0])
                normalized_scores['fcf'] = 0.0  # 暂时设为0
                normalized_scores['ev_ebitda'] = 0.0  # 暂时设为0
                normalized_scores['dividend_coverage'] = 0.0  # 暂时设为0
                
                # 计算得分
                scores['fundamental'] = self.calculate_fundamental_score(
                    all_data['financial_ratios']
                )
            else:
                scores['fundamental'] = 0.0
            
            # 2. 技术面因子
            if all_data.get('technical_indicators'):
                # 计算技术指标
                atr = TechnicalIndicators.calculate_atr(
                    all_data['price_data']['High'],
                    all_data['price_data']['Low'],
                    all_data['price_data']['Close']
                )
                
                obv = TechnicalIndicators.calculate_obv(
                    all_data['price_data']['Close'],
                    all_data['price_data']['Volume']
                )
                
                adx = TechnicalIndicators.calculate_adx(
                    all_data['price_data']['High'],
                    all_data['price_data']['Low'],
                    all_data['price_data']['Close']
                )
                
                ma_short = all_data['technical_indicators']['MA5'].iloc[-1]
                ma_long = all_data['technical_indicators']['MA20'].iloc[-1]
                ma_trend = (ma_short / ma_long - 1) if ma_long != 0 else 0
                
                # 记录原始值
                raw_values['ma_trend'] = ma_trend * 100  # 转为百分比
                raw_values['atr'] = atr.iloc[-1]
                raw_values['obv'] = obv.iloc[-1]
                raw_values['adx'] = adx.iloc[-1]
                
                # 记录技术指标趋势
                technical_trends['atr_trend'] = 0.5  # 默认值
                technical_trends['obv_trend'] = 0.5  # 默认值
                technical_trends['adx_trend'] = 0.5  # 默认值
                
                # 计算得分
                scores['technical'] = self.calculate_technical_score(
                    all_data['price_data'],
                    all_data['technical_indicators']
                )
            else:
                scores['technical'] = 0.0
            
            # 3. 风险因子
            if all_data.get('risk_metrics'):
                # 获取风险指标
                var_95 = all_data['risk_metrics'].get('VaR(95%)', 0)
                sharpe_ratio = all_data['risk_metrics'].get('Sharpe Ratio', 0)
                max_dd = abs(all_data['risk_metrics'].get('Max Drawdown', 0))
                
                # 记录原始值
                raw_values['var'] = var_95
                raw_values['sharpe'] = sharpe_ratio
                raw_values['max_drawdown'] = max_dd
                
                # 转换风险指标为评分（越低风险越高分）
                var_score = 1 - min(abs(var_95), 0.1) * 10  # 限制VaR的影响
                sharpe_score = min(max(sharpe_ratio, -2), 2) / 2 + 0.5  # 将夏普比率映射到[0,1]
                drawdown_score = 1 - min(max_dd, 0.5) * 2  # 限制最大回撤的影响
                
                # 标准化处理
                risk_scores['var'] = float(self.normalize_factor(np.array([var_score]), 'minmax')[0])
                risk_scores['sharpe'] = float(self.normalize_factor(np.array([sharpe_score]), 'minmax')[0])
                risk_scores['max_drawdown'] = float(self.normalize_factor(np.array([drawdown_score]), 'minmax')[0])
                
                # 计算得分
                scores['risk'] = self.calculate_risk_score(
                    all_data['risk_metrics']
                )
            else:
                scores['risk'] = 0.0
            
            # 4. 情绪因子
            if all_data.get('sentiment_data'):
                scores['sentiment'] = self.calculate_sentiment_score(
                    all_data['sentiment_data']
                )
            else:
                scores['sentiment'] = 0.0
            
            # 确保所有分数都是有效数字
            scores = {k: 0.0 if np.isnan(v) else float(v) for k, v in scores.items()}
            
            # 计算加权得分
            final_score = 0.0
            for category, score in scores.items():
                weight = self.current_weights[category]['weight']
                final_score += score * weight
            
            # 生成详细报告
            report = {
                'final_score': float(final_score),  # 确保是浮点数
                'category_scores': scores,
                'weights': self.current_weights,
                'interpretation': self._interpret_score(final_score),
                'raw_values': raw_values,
                'normalized_scores': normalized_scores,
                'technical_trends': technical_trends,
                'risk_scores': risk_scores
            }
            
            print("\n多因子分析结果:")
            print(f"基本面得分: {scores['fundamental']:.2f}")
            print(f"技术面得分: {scores['technical']:.2f}")
            print(f"风险得分: {scores['risk']:.2f}")
            print(f"情绪得分: {scores['sentiment']:.2f}")
            print(f"最终得分: {final_score:.2f}")
            
            return report
            
        except Exception as e:
            print(f"多因子最终得分计算错误: {str(e)}")
            return {
                'final_score': 0.0,
                'category_scores': {
                    'fundamental': 0.0,
                    'technical': 0.0,
                    'risk': 0.0,
                    'sentiment': 0.0
                },
                'weights': self.current_weights,
                'interpretation': "计算错误",
                'raw_values': {},
                'normalized_scores': {},
                'technical_trends': {},
                'risk_scores': {}
            }
    
    def _interpret_score(self, score):
        """解释多因子得分"""
        result = ""
        if score > 0.8:
            result = "强烈看多 (非常好的投资机会)"
        elif score > 0.6:
            result = "看多 (较好的投资机会)"
        elif score > 0.4:
            result = "中性偏多 (可以考虑)"
        elif score > 0.2:
            result = "中性 (建议观望)"
        elif score > 0:
            result = "中性偏空 (暂不建议)"
        else:
            result = "看空 (建议规避)"
        
        # 添加详细说明
        if self.current_weights['fundamental']['weight'] > 0.5:
            result += "\n基本面因素权重较高"
        if self.current_weights['technical']['weight'] > 0.4:
            result += "\n技术面因素权重较高"
        
        return result 