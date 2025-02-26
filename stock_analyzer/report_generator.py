import pandas as pd
import os
from datetime import datetime
from .config import REPORT_CONFIG
import matplotlib.pyplot as plt
import numpy as np

class ReportGenerator:
    def __init__(self):
        self.report_data = {}
        # 确保输出目录存在
        os.makedirs(REPORT_CONFIG['output_path'], exist_ok=True)
    
    def add_section(self, section_name: str, data):
        """添加报告部分"""
        self.report_data[section_name] = data
    
    def generate_report(self, symbol: str):
        """生成分析报告"""
        try:
            # 创建报告文件名
            timestamp = datetime.now().strftime(REPORT_CONFIG['date_format'])
            filename = f"{REPORT_CONFIG['output_path']}/{symbol}_analysis_{timestamp}.xlsx"
            
            # 创建Excel写入器
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                # 写入每个部分的数据
                for section_name, data in self.report_data.items():
                    if isinstance(data, pd.DataFrame):
                        data.to_excel(writer, sheet_name=section_name[:31])  # Excel工作表名最大31字符
                    elif isinstance(data, dict):
                        pd.DataFrame.from_dict(data, orient='index').to_excel(
                            writer, 
                            sheet_name=section_name[:31]
                        )
            
            return filename
            
        except Exception as e:
            print(f"生成报告失败: {str(e)}")
            return None 

    def generate_markdown_report(self, symbol: str):
        """生成Markdown格式的分析报告，使用与日志文件完全一致的格式"""
        try:
            # 创建报告文件名
            timestamp = datetime.now().strftime(REPORT_CONFIG['date_format'])
            filename = f"{REPORT_CONFIG['output_path']}/{symbol}_analysis_{timestamp}.md"
            
            # 准备报告内容
            report_content = []
            
            # 添加财务指标
            if '财务指标' in self.report_data:
                financial_ratios = self.report_data['财务指标']
                report_content.append(f"获取 {symbol} 的财务数据...")
                report_content.append("")
                report_content.append("获取到的财务数据（百万）:")
                
                # 添加可用的财务数据
                if 'ROE' in financial_ratios:
                    report_content.append(f"ROE: {financial_ratios['ROE']:.2f}")
                if 'DebtRatio' in financial_ratios:
                    report_content.append(f"DebtRatio: {financial_ratios['DebtRatio']:.2f}")
                report_content.append("")
            
            # 添加多因子分析
            if '多因子分析' in self.report_data:
                factor_analysis = self.report_data['多因子分析']
                
                # 确保raw_values存在
                if 'raw_values' in factor_analysis:
                    report_content.append("原始指标值:")
                    if 'roe' in factor_analysis['raw_values']:
                        report_content.append(f"ROE: {factor_analysis['raw_values']['roe']:.2f}%")
                    if 'debt_ratio' in factor_analysis['raw_values']:
                        report_content.append(f"负债率: {factor_analysis['raw_values']['debt_ratio']:.2f}%")
                    report_content.append("")
                
                # 确保normalized_scores存在
                if 'normalized_scores' in factor_analysis:
                    report_content.append("标准化后得分:")
                    if 'roe' in factor_analysis['normalized_scores']:
                        report_content.append(f"roe: {factor_analysis['normalized_scores']['roe']:.2f}")
                    if 'debt_ratio' in factor_analysis['normalized_scores']:
                        report_content.append(f"debt_ratio: {factor_analysis['normalized_scores']['debt_ratio']:.2f}")
                    if 'fcf' in factor_analysis['normalized_scores']:
                        report_content.append(f"fcf: {factor_analysis['normalized_scores']['fcf']:.2f}")
                    if 'ev_ebitda' in factor_analysis['normalized_scores']:
                        report_content.append(f"ev_ebitda: {factor_analysis['normalized_scores']['ev_ebitda']:.2f}")
                    if 'dividend_coverage' in factor_analysis['normalized_scores']:
                        report_content.append(f"dividend_coverage: {factor_analysis['normalized_scores']['dividend_coverage']:.2f}")
                    report_content.append("")
                
                # 确保category_scores存在
                if 'category_scores' in factor_analysis and 'fundamental' in factor_analysis['category_scores']:
                    report_content.append(f"最终基本面得分: {factor_analysis['category_scores']['fundamental']:.2f}")
                    report_content.append("")
                
                # 确保raw_values存在
                if 'raw_values' in factor_analysis:
                    report_content.append("技术指标原始值:")
                    if 'ma_trend' in factor_analysis['raw_values']:
                        report_content.append(f"MA趋势: {factor_analysis['raw_values']['ma_trend']:.2f}%")
                    if 'atr' in factor_analysis['raw_values']:
                        report_content.append(f"ATR: {factor_analysis['raw_values']['atr']:.2f}")
                    if 'obv' in factor_analysis['raw_values']:
                        report_content.append(f"OBV: {factor_analysis['raw_values']['obv']:,.0f}")
                    if 'adx' in factor_analysis['raw_values']:
                        report_content.append(f"ADX: {factor_analysis['raw_values']['adx']:.2f}")
                    report_content.append("")
                
                # 确保technical_trends存在
                if 'technical_trends' in factor_analysis:
                    report_content.append("技术指标趋势:")
                    if 'atr_trend' in factor_analysis['technical_trends']:
                        report_content.append(f"atr_trend: {factor_analysis['technical_trends']['atr_trend']*100:.2f}%")
                    if 'obv_trend' in factor_analysis['technical_trends']:
                        report_content.append(f"obv_trend: {factor_analysis['technical_trends']['obv_trend']*100:.2f}%")
                    if 'adx_trend' in factor_analysis['technical_trends']:
                        report_content.append(f"adx_trend: {factor_analysis['technical_trends']['adx_trend']*100:.2f}%")
                    report_content.append("")
                
                # 确保category_scores存在
                if 'category_scores' in factor_analysis and 'technical' in factor_analysis['category_scores']:
                    report_content.append(f"最终技术面得分: {factor_analysis['category_scores']['technical']:.2f}")
                    report_content.append("")
                
                # 确保raw_values存在
                if 'raw_values' in factor_analysis:
                    report_content.append("风险指标原始值:")
                    if 'var' in factor_analysis['raw_values']:
                        report_content.append(f"VaR(95%): {factor_analysis['raw_values']['var']*100:.2f}%")
                    if 'sharpe' in factor_analysis['raw_values']:
                        report_content.append(f"夏普比率: {factor_analysis['raw_values']['sharpe']:.2f}")
                    if 'max_drawdown' in factor_analysis['raw_values']:
                        report_content.append(f"最大回撤: {factor_analysis['raw_values']['max_drawdown']*100:.2f}%")
                    report_content.append("")
                
                # 确保risk_scores存在
                if 'risk_scores' in factor_analysis:
                    report_content.append("风险指标标准化得分:")
                    if 'var' in factor_analysis['risk_scores']:
                        report_content.append(f"var: {factor_analysis['risk_scores']['var']:.2f}")
                    if 'sharpe' in factor_analysis['risk_scores']:
                        report_content.append(f"sharpe: {factor_analysis['risk_scores']['sharpe']:.2f}")
                    if 'max_drawdown' in factor_analysis['risk_scores']:
                        report_content.append(f"max_drawdown: {factor_analysis['risk_scores']['max_drawdown']:.2f}")
                    report_content.append("")
                
                # 确保category_scores存在
                if 'category_scores' in factor_analysis and 'risk' in factor_analysis['category_scores']:
                    report_content.append(f"最终风险得分: {factor_analysis['category_scores']['risk']:.2f}")
                    report_content.append("")
                
                # 确保category_scores存在
                if 'category_scores' in factor_analysis:
                    report_content.append("多因子分析结果:")
                    if 'fundamental' in factor_analysis['category_scores']:
                        report_content.append(f"基本面得分: {factor_analysis['category_scores']['fundamental']:.2f}")
                    if 'technical' in factor_analysis['category_scores']:
                        report_content.append(f"技术面得分: {factor_analysis['category_scores']['technical']:.2f}")
                    if 'risk' in factor_analysis['category_scores']:
                        report_content.append(f"风险得分: {factor_analysis['category_scores']['risk']:.2f}")
                    if 'sentiment' in factor_analysis['category_scores']:
                        report_content.append(f"情绪得分: {factor_analysis['category_scores']['sentiment']:.2f}")
                    report_content.append("")
                
                # 确保final_score存在
                if 'final_score' in factor_analysis:
                    report_content.append(f"最终得分: {factor_analysis['final_score']:.2f}")
                    report_content.append("")
                
                # 确保interpretation存在
                if 'interpretation' in factor_analysis:
                    report_content.append("投资建议:")
                    report_content.append(f"综合评级: {factor_analysis['interpretation']}")
                    report_content.append("")
                    
                    report_content.append("主要优势:")
                    if 'category_scores' in factor_analysis:
                        if 'fundamental' in factor_analysis['category_scores'] and factor_analysis['category_scores']['fundamental'] > 0.3:
                            report_content.append("- 基本面稳健")
                        if 'risk' in factor_analysis['category_scores'] and factor_analysis['category_scores']['risk'] > 0.6:
                            report_content.append("- 风险可控")
                    report_content.append("")
                    
                    report_content.append("需要关注:")
                    if 'category_scores' in factor_analysis:
                        if 'technical' in factor_analysis['category_scores'] and factor_analysis['category_scores']['technical'] < 0.3:
                            report_content.append("- 技术面偏弱")
                        if 'sentiment' in factor_analysis['category_scores'] and factor_analysis['category_scores']['sentiment'] == 0:
                            report_content.append("- 缺乏市场情绪数据")
                    report_content.append("")
            
            # 写入文件 - 使用与日志文件完全相同的格式
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"# {symbol} 股票分析报告 ({timestamp})\n\n")
                f.write("```\n")
                f.write("\n".join(report_content))
                f.write("\n```\n")
            
            return filename
            
        except Exception as e:
            print(f"生成Markdown报告失败: {str(e)}")
            return None

    def generate_score_chart(self, scores):
        """生成得分雷达图"""
        categories = list(scores.keys())
        values = list(scores.values())
        
        # 创建雷达图
        angles = np.linspace(0, 2*np.pi, len(categories), endpoint=False)
        values = np.concatenate((values, [values[0]]))  # 闭合图形
        angles = np.concatenate((angles, [angles[0]]))  # 闭合图形
        
        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'))
        ax.plot(angles, values)
        ax.fill(angles, values, alpha=0.25)
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories)
        
        return fig 