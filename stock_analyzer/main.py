from stock_analyzer.data_fetcher import DataFetcher
from stock_analyzer.indicators import TechnicalIndicators, FundamentalIndicators
from stock_analyzer.report_generator import ReportGenerator
from stock_analyzer.risk_metrics import RiskMetrics
from stock_analyzer.validators import DataValidator
from stock_analyzer.sentiment_analyzer import SentimentAnalyzer
from stock_analyzer.models import MultiFactorModel
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from .logger import Logger

class StockAnalyzer:
    def __init__(self):
        self.logger = Logger()
        self.data_fetcher = DataFetcher()
        self.report_generator = ReportGenerator()
        self.validator = DataValidator()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.factor_model = MultiFactorModel()
    
    def analyze_stock(self, symbol: str, days: int = 365, export_md: bool = False):
        """分析指定股票"""
        self.logger.info(f"开始分析股票: {symbol}")
        # 计算日期范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # 获取数据
        stock_data = self.data_fetcher.get_stock_data(
            symbol,
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        )
        
        if stock_data is None:
            return None
            
        # 计算收益率
        price_data = stock_data['price_data']
        returns = price_data['Close'].pct_change().dropna()
        
        # 计算风险指标
        risk_metrics = {
            'VaR(95%)': RiskMetrics.calculate_var(returns),
            'VaR(99%)': RiskMetrics.calculate_var(returns, 0.99),
        }
        
        # 计算最大回撤
        max_dd, start_idx, end_idx = RiskMetrics.calculate_max_drawdown(price_data['Close'])
        risk_metrics.update({
            'Max Drawdown': max_dd,
            'Max Drawdown Start': start_idx,
            'Max Drawdown End': end_idx
        })
        
        # 计算波动率
        volatility = RiskMetrics.calculate_volatility(returns)
        risk_metrics['Annual Volatility'] = volatility.iloc[-1]
        
        # 计算夏普比率
        sharpe = RiskMetrics.calculate_sharpe_ratio(returns)
        risk_metrics['Sharpe Ratio'] = sharpe
        
        # 生成报告
        self.report_generator.add_section('价格数据', price_data)
        self.report_generator.add_section('风险指标', risk_metrics)
        
        # 添加技术指标
        ma_data = TechnicalIndicators.calculate_ma(price_data['Close'])
        rsi_data = pd.DataFrame({
            'RSI': TechnicalIndicators.calculate_rsi(price_data['Close'])
        })
        bollinger_data = TechnicalIndicators.calculate_bollinger_bands(price_data['Close'])
        
        self.report_generator.add_section('移动平均线', ma_data)
        self.report_generator.add_section('RSI指标', rsi_data)
        self.report_generator.add_section('布林带', bollinger_data)
        
        # 添加财务指标
        financial_ratios = FundamentalIndicators.calculate_financial_ratios(
            stock_data['financial_data']
        )
        if financial_ratios:
            self.report_generator.add_section('财务指标', financial_ratios)
        
        # 添加情绪分析
        sentiment_data = self.sentiment_analyzer.get_social_sentiment(symbol)
        if sentiment_data and sentiment_data['status'] == 'success':
            # 结合成交量分析情绪
            sentiment_data = self.sentiment_analyzer.analyze_volume_sentiment(
                price_data, 
                sentiment_data
            )
            self.report_generator.add_section('市场情绪', sentiment_data)
            
            # 如果情绪显著，添加到风险指标中
            if sentiment_data['signal'] != 'NEUTRAL':
                risk_metrics['Sentiment_Signal'] = sentiment_data['signal']
                risk_metrics['Sentiment_Score'] = sentiment_data['average_sentiment']
        
        # 数据验证
        price_validation = self.validator.validate_price_data(price_data)
        if not price_validation['valid']:
            print(f"价格数据验证失败: {price_validation['errors']}")
            return None
            
        if price_validation.get('warnings'):
            print(f"价格数据警告: {price_validation['warnings']}")
            
        financial_validation = self.validator.validate_financial_data(stock_data['financial_data'])
        if not financial_validation['valid']:
            print(f"财务数据验证失败: {financial_validation['errors']}")
            return None
            
        if financial_validation.get('warnings'):
            print(f"财务数据警告: {financial_validation['warnings']}")
        
        # 添加更多技术指标
        technical_indicators = {
            'MA5': ma_data['MA5'],
            'MA20': ma_data['MA20'],
            'RSI': rsi_data['RSI'],
            'ATR': TechnicalIndicators.calculate_atr(
                price_data['High'],
                price_data['Low'],
                price_data['Close']
            ),
            'OBV': TechnicalIndicators.calculate_obv(
                price_data['Close'],
                price_data['Volume']
            ),
            'ADX': TechnicalIndicators.calculate_adx(
                price_data['High'],
                price_data['Low'],
                price_data['Close']
            )
        }
        
        # 整合所有数据用于多因子分析
        all_data = {
            'price_data': price_data,
            'technical_indicators': technical_indicators,
            'financial_ratios': financial_ratios,
            'risk_metrics': risk_metrics,
            'sentiment_data': sentiment_data if sentiment_data else {'status': 'error'}
        }
        
        # 计算多因子得分
        factor_analysis = self.factor_model.calculate_final_score(all_data)
        if factor_analysis:
            self.report_generator.add_section('多因子分析', factor_analysis)
            
            # 打印财务数据
            print("\n获取到的财务数据（百万）:")
            if 'Total Assets' in financial_ratios:
                print(f"Total Assets: {financial_ratios['Total Assets']:,.2f}")
            if 'Total Liabilities' in financial_ratios:
                print(f"Total Liabilities: {financial_ratios['Total Liabilities']:,.2f}")
            if 'Total Equity' in financial_ratios:
                print(f"Total Equity: {financial_ratios['Total Equity']:,.2f}")
            if 'Net Income' in financial_ratios:
                print(f"Net Income: {financial_ratios['Net Income']:,.2f}")
            if 'ROE' in financial_ratios:
                print(f"ROE: {financial_ratios['ROE']:.2f}")
            if 'DebtRatio' in financial_ratios:
                print(f"DebtRatio: {financial_ratios['DebtRatio']:.2f}")
            
            # 打印基本面指标
            if 'raw_values' in factor_analysis and 'roe' in factor_analysis['raw_values'] and 'debt_ratio' in factor_analysis['raw_values']:
                print("\n原始指标值:")
                print(f"ROE: {factor_analysis['raw_values']['roe']:.2f}%")
                print(f"负债率: {factor_analysis['raw_values']['debt_ratio']:.2f}%")
            
            # 打印标准化后的基本面得分
            if 'normalized_scores' in factor_analysis and 'fundamental' in factor_analysis['normalized_scores']:
                print("\n标准化后得分:")
                for key, value in factor_analysis['normalized_scores']['fundamental'].items():
                    print(f"{key}: {value:.2f}")
            
            if 'category_scores' in factor_analysis and 'fundamental' in factor_analysis['category_scores']:
                print(f"\n最终基本面得分: {factor_analysis['category_scores']['fundamental']:.2f}")
            
            # 打印技术指标
            if 'raw_values' in factor_analysis:
                print("\n技术指标原始值:")
                if 'ma_trend' in factor_analysis['raw_values']:
                    print(f"MA趋势: {factor_analysis['raw_values']['ma_trend']:.2f}%")
                if 'atr' in factor_analysis['raw_values']:
                    print(f"ATR: {factor_analysis['raw_values']['atr']:.2f}")
                if 'obv' in factor_analysis['raw_values']:
                    print(f"OBV: {factor_analysis['raw_values']['obv']:,.0f}")
                if 'adx' in factor_analysis['raw_values']:
                    print(f"ADX: {factor_analysis['raw_values']['adx']:.2f}")
            
            # 打印技术指标趋势
            if 'normalized_scores' in factor_analysis and 'technical' in factor_analysis['normalized_scores']:
                print("\n技术指标趋势:")
                for key, value in factor_analysis['normalized_scores']['technical'].items():
                    if key.endswith('_trend'):
                        print(f"{key}: {value*100:.2f}%")
            
            if 'category_scores' in factor_analysis and 'technical' in factor_analysis['category_scores']:
                print(f"\n最终技术面得分: {factor_analysis['category_scores']['technical']:.2f}")
            
            # 打印风险指标
            if 'raw_values' in factor_analysis:
                print("\n风险指标原始值:")
                if 'var' in factor_analysis['raw_values']:
                    print(f"VaR(95%): {factor_analysis['raw_values']['var']*100:.2f}%")
                if 'sharpe' in factor_analysis['raw_values']:
                    print(f"夏普比率: {factor_analysis['raw_values']['sharpe']:.2f}")
                if 'max_drawdown' in factor_analysis['raw_values']:
                    print(f"最大回撤: {factor_analysis['raw_values']['max_drawdown']*100:.2f}%")
            
            # 打印风险指标标准化得分
            if 'normalized_scores' in factor_analysis and 'risk' in factor_analysis['normalized_scores']:
                print("\n风险指标标准化得分:")
                for key, value in factor_analysis['normalized_scores']['risk'].items():
                    print(f"{key}: {value:.2f}")
            
            if 'category_scores' in factor_analysis and 'risk' in factor_analysis['category_scores']:
                print(f"\n最终风险得分: {factor_analysis['category_scores']['risk']:.2f}")
            
            # 打印多因子分析结果
            if 'category_scores' in factor_analysis:
                print("\n多因子分析结果:")
                if 'fundamental' in factor_analysis['category_scores']:
                    print(f"基本面得分: {factor_analysis['category_scores']['fundamental']:.2f}")
                if 'technical' in factor_analysis['category_scores']:
                    print(f"技术面得分: {factor_analysis['category_scores']['technical']:.2f}")
                if 'risk' in factor_analysis['category_scores']:
                    print(f"风险得分: {factor_analysis['category_scores']['risk']:.2f}")
                if 'sentiment' in factor_analysis['category_scores']:
                    print(f"情绪得分: {factor_analysis['category_scores']['sentiment']:.2f}")
            
            if 'final_score' in factor_analysis:
                print(f"最终得分: {factor_analysis['final_score']:.2f}")
            
            # 添加投资建议输出
            if 'interpretation' in factor_analysis:
                print("\n投资建议:")
                print(f"综合评级: {factor_analysis['interpretation']}")
            
                print("\n主要优势:")
                if 'category_scores' in factor_analysis:
                    if 'fundamental' in factor_analysis['category_scores'] and factor_analysis['category_scores']['fundamental'] > 0.3:
                        print("- 基本面稳健")
                    if 'risk' in factor_analysis['category_scores'] and factor_analysis['category_scores']['risk'] > 0.6:
                        print("- 风险可控")
                
                print("\n需要关注:")
                if 'category_scores' in factor_analysis:
                    if 'technical' in factor_analysis['category_scores'] and factor_analysis['category_scores']['technical'] < 0.3:
                        print("- 技术面偏弱")
                    if 'sentiment' in factor_analysis['category_scores'] and factor_analysis['category_scores']['sentiment'] == 0:
                        print("- 缺乏市场情绪数据")
        
        # 生成报告
        report_path = self.report_generator.generate_report(symbol)
        
        # 如果需要导出Markdown报告
        if export_md:
            md_report_path = self.report_generator.generate_markdown_report(symbol)
            if md_report_path:
                print(f"成功生成 {symbol} 的Markdown分析报告: {md_report_path}")
        
        return report_path

def main():
    analyzer = StockAnalyzer()
    report_path = analyzer.analyze_stock('AAPL')  # 示例：分析苹果股票
    if report_path:
        print(f"分析报告已生成: {report_path}")
    else:
        print("分析失败")

if __name__ == "__main__":
    main() 