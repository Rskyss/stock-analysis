import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from .config import API_CONFIG, SENTIMENT_CONFIG

class SentimentAnalyzer:
    def __init__(self):
        self.config = API_CONFIG['stocktwits']
        self.sentiment_config = SENTIMENT_CONFIG
        
    def get_social_sentiment(self, symbol: str):
        """
        获取StockTwits上的社交媒体情绪数据
        params:
            symbol: str - 股票代码
        returns:
            dict - 情绪分析结果
        """
        try:
            # 构建API请求
            url = f"{self.config['base_url']}/streams/symbol/{symbol}.json"
            headers = {
                'Authorization': f"OAuth {self.config['api_key']}",
                'Content-Type': 'application/json'
            }
            
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                return None
                
            data = response.json()
            messages = data.get('messages', [])
            
            if len(messages) < self.sentiment_config['min_messages']:
                return {
                    'status': 'insufficient_data',
                    'message': f'消息数量不足，需要至少{self.sentiment_config["min_messages"]}条'
                }
            
            # 分析情绪
            sentiment_scores = []
            for msg in messages:
                if msg.get('entities', {}).get('sentiment'):
                    sentiment = msg['entities']['sentiment']['basic']
                    score = self.config['sentiment_weights'].get(sentiment, 0)
                    sentiment_scores.append(score)
            
            if not sentiment_scores:
                return {
                    'status': 'no_sentiment',
                    'message': '没有找到情绪数据'
                }
            
            # 计算情绪指标
            sentiment_df = pd.Series(sentiment_scores)
            results = {
                'status': 'success',
                'average_sentiment': sentiment_df.mean(),
                'sentiment_std': sentiment_df.std(),
                'bullish_ratio': (sentiment_df > 0).mean(),
                'bearish_ratio': (sentiment_df < 0).mean(),
                'message_count': len(messages),
                'analyzed_count': len(sentiment_scores)
            }
            
            # 添加情绪信号
            results['signal'] = self._generate_sentiment_signal(results)
            
            return results
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'获取情绪数据失败: {str(e)}'
            }
    
    def _generate_sentiment_signal(self, sentiment_results):
        """
        根据情绪指标生成交易信号
        """
        avg_sentiment = sentiment_results['average_sentiment']
        
        if avg_sentiment > self.sentiment_config['bullish_threshold']:
            return 'BULLISH'
        elif avg_sentiment < self.sentiment_config['bearish_threshold']:
            return 'BEARISH'
        else:
            return 'NEUTRAL'
    
    def analyze_volume_sentiment(self, price_data, sentiment_data):
        """
        结合成交量分析情绪
        """
        if sentiment_data['status'] != 'success':
            return sentiment_data
            
        try:
            # 计算成交量变化
            volume_change = price_data['Volume'].pct_change()
            recent_volume_change = volume_change.tail(5).mean()
            
            # 调整情绪得分
            volume_factor = self.sentiment_config['volume_factor']
            adjusted_sentiment = (
                sentiment_data['average_sentiment'] * (1 - volume_factor) +
                np.sign(sentiment_data['average_sentiment']) * recent_volume_change * volume_factor
            )
            
            sentiment_data['volume_adjusted_sentiment'] = adjusted_sentiment
            sentiment_data['volume_change_5d'] = recent_volume_change
            
            return sentiment_data
            
        except Exception as e:
            sentiment_data['volume_analysis_error'] = str(e)
            return sentiment_data 