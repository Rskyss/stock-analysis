# 股票量化分析系统

基于多因子模型的股票量化分析系统，集成基本面、技术面、市场情绪等多维度分析。

## 功能特点

- **多因子分析模型**：结合基本面、技术面、市场情绪三维度，参考Fama-French五因子模型扩展
- **动态权重调整**：根据市场周期（牛市/熊市）自动调整因子权重
- **风险控制**：计算VaR、最大回撤、波动率等风险指标
- **市场情绪分析**：结合社交媒体数据和成交量分析市场情绪
- **自动报告生成**：支持Excel、CSV、JSON、Markdown和PDF格式报告

## 技术架构

- **数据获取**：使用Yahoo Finance API获取价格数据和财务数据
- **技术指标**：MA、RSI、布林带、ATR、OBV、ADX等
- **基本面指标**：ROE、自由现金流、负债率、营收增长率等
- **风险指标**：VaR(95%/99%)、最大回撤、年化波动率、夏普比率
- **多因子模型**：整合技术面、基本面和情绪因子，动态调整权重

## 安装

```bash
pip install -r requirements.txt
```

## 使用方法

### 基本用法

1. 分析单个股票:
```bash
python run.py AAPL
```

2. 分析多个股票:
```bash
python run.py AAPL MSFT GOOG
```

3. 指定分析天数:
```bash
python run.py AAPL --days 180
```

4. 指定输出目录:
```bash
python run.py AAPL --output ./my_reports
```

5. 显示详细日志:
```bash
python run.py AAPL --verbose
```

### 高级用法

1. 指定输出格式:
```bash
python run.py AAPL --format excel  # 可选: excel, csv, json
```

2. 导出Markdown报告:
```bash
python run.py AAPL --export-md
```

3. 导出PDF报告:
```bash
python run.py AAPL --export-pdf
```

4. 组合使用:
```bash
python run.py AAPL MSFT --days 90 --output ./reports --format json --verbose
```

## 报告内容

生成的分析报告包含以下内容：

- **价格数据摘要**：开盘价、最高价、最低价、收盘价、成交量
- **技术指标分析**：移动平均线、RSI、布林带、ATR、OBV、ADX
- **基本面分析**：财务比率、盈利能力、估值指标
- **风险评估**：VaR、最大回撤、波动率、夏普比率
- **市场情绪**：社交媒体情绪分析、成交量异常检测
- **多因子评分**：综合技术面、基本面和情绪因子的最终评分和建议

## 配置说明

请在 `stock_analyzer/config.py` 中配置相关API密钥和参数。主要配置项包括：

- API密钥设置
- 技术指标参数
- 风险控制阈值
- 因子权重配置

## 开发文档

详细开发文档请参考 `PRD.md`。

## 注意事项

- 本系统仅供研究和学习使用，不构成投资建议
- 使用免费API可能存在请求限制，建议合理控制请求频率
- 历史数据不代表未来表现，投资决策需谨慎 