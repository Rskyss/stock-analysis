# API配置
API_CONFIG = {
    'yahoo_finance': {
        'enabled': True,
    },
    'eod_historical': {
        'api_key': ' 67a195ce6824d7.43340520',
        'base_url': 'https://eodhistoricaldata.com/api',
        'requests_per_day': 1000
    },
    'stocktwits': {
        'api_key': 'your_api_key_here',
        'base_url': 'https://api.stocktwits.com/api/2',
        'requests_per_hour': 500,
        'sentiment_weights': {
            'Bullish': 1,
            'Bearish': -1,
            'Neutral': 0
        }
    }
}

# 指标计算配置
INDICATOR_CONFIG = {
    'technical': {
        'ma_periods': [5, 10, 20, 60],  # 均线周期
        'rsi_period': 14,
        'atr_period': 14,
        'bollinger_period': 20,
        'bollinger_std': 2
    },
    'fundamental': {
        'roe_threshold': 0.15,  # ROE警戒线
        'debt_ratio_warning': 0.7,  # 负债率警戒线
        'min_cash_ratio': 0.1  # 最小现金比率
    }
}

# 报告输出配置
REPORT_CONFIG = {
    'output_path': './reports',
    'template_path': './templates',
    'date_format': '%Y-%m-%d'
}

# 添加情绪分析配置
SENTIMENT_CONFIG = {
    'min_messages': 10,        # 最小消息数量
    'time_window': '7d',       # 情绪分析时间窗口
    'bullish_threshold': 0.6,  # 看多阈值
    'bearish_threshold': -0.3, # 看空阈值
    'volume_factor': 0.3       # 成交量因子权重
}

# 添加多因子模型配置
FACTOR_CONFIG = {
    'weights': {
        'fundamental': {
            'weight': 0.4,
            'factors': {
                'roe': 0.4,
                'debt_ratio': 0.3,
                'fcf': 0.1,
                'ev_ebitda': 0.1,
                'dividend_coverage': 0.1
            }
        },
        'technical': {
            'weight': 0.3,
            'factors': {
                'ma_trend': 0.4,
                'atr': 0.2,
                'obv': 0.2,
                'adx': 0.2
            }
        },
        'risk': {
            'weight': 0.2,
            'factors': {
                'var': 0.3,
                'sharpe': 0.3,
                'max_drawdown': 0.4
            }
        },
        'sentiment': {
            'weight': 0.1,
            'factors': {
                'social_score': 0.6,
                'volume_sentiment': 0.4
            }
        }
    },
    
    # 因子标准化参数
    'normalization': {
        'method': 'zscore',  # 可选: zscore, minmax, rank
        'winsorize': 0.05    # 去极值比例
    },
    
    # 市场状态阈值
    'market_state': {
        'bull_threshold': 0.2,   # 牛市判定阈值（20日涨幅）
        'bear_threshold': -0.2,  # 熊市判定阈值（20日跌幅）
    }
} 