---

## **股票量化分析方案（开发需求文档）**

---

### **一、分析框架设计**
#### **1. 核心方法论**
- **多因子模型**：结合基本面、技术面、市场情绪三维度，参考Fama-French五因子模型扩展。
- **动态权重调整**：根据市场周期（牛市/熊市）调整因子权重（如熊市加重财务健康权重）。
- **事件驱动校验**：财报发布、利率决议等事件后，重新校准模型参数。

#### **2. 关注优先级**
| **类别**       | **关键指标**                              | **权重** | **数据源**              |
|----------------|------------------------------------------|----------|-------------------------|
| **基本面**     | ROE、自由现金流、负债率、营收增长率       | 40%      | 财报、宏观数据          |
| **技术面**     | 均线系统、RSI、布林带、成交量背离         | 30%      | 历史价格数据            |
| **量化模型**   | 夏普比率、最大回撤、因子暴露度            | 20%      | 回测平台                |
| **市场情绪**   | VIX指数、资金流向、社交媒体情绪指数       | 10%      | 舆情API、期权数据       |

---

### **二、数据获取方案**
#### **1. 免费API选择标准**
- **稳定性**：日均请求量>1万次，宕机率<1%。  
- **数据完整性**：至少覆盖以下字段：  
  - 历史价格（OHLCV）  
  - 财务报表（资产负债表、利润表、现金流量表）  
  - 分析师预测（EPS、营收）  
  - 市场情绪（Reddit/Twitter提及量）  

#### **2. 推荐API组合**
| **数据类型**       | **API**                  | **频率限制**       | **获取方式**                     |
|--------------------|--------------------------|--------------------|----------------------------------|
| 历史价格           | Yahoo Finance API        | 无限制             | `yfinance`库（Python直接调用）    |
| 财务报表           | EOD Historical Data      | 1000次/天          | 注册免费API Key                  |
| 宏观经济指标       | FRED Economic Data       | 无限制             | 直接调用（无需Key）              |
| 社交媒体情绪       | StockTwits API           | 500次/小时         | OAuth 2.0认证                    |

---

### **三、指标与公式库**
#### **1. 基本面指标公式**
| **指标**           | **公式**                                                                 | **实现逻辑**                                                                 |
|--------------------|-------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **自由现金流(FCF)** | `FCF = 经营活动现金流 - 资本支出`                                        | 从现金流量表提取"Net Cash from Operating Activities"和"Capital Expenditure" |
| **EV/EBITDA**      | `EV/(EBITDA) = (市值 + 负债 - 现金) / 息税折旧摊销前利润`                | 需合并资产负债表与利润表数据                                                |
| **股息保障倍数**   | `股息保障倍数 = (净利润 - 优先股股息) / 普通股股息`                       | 优先股股息数据需从财报附注提取                                              |

#### **2. 技术面指标公式**
| **指标**           | **公式**                                                                 | **实现逻辑**                                                                 |
|--------------------|-------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **ATR（真实波幅）**| `TR = max(当日最高-当日最低, abs(当日最高-前收盘), abs(当日最低-前收盘))`<br>`ATR = EMA(TR, 14日)` | 需递归计算指数移动平均                                                      |
| **OBV能量潮**      | `若收盘价>前收盘价: OBV += 成交量`<br>`若收盘价<前收盘价: OBV -= 成交量` | 需按时间序列逐日累加                                                        |
| **ADX趋势强度**    | 计算+DM、-DM → 计算+DI、-DI → 计算DX → ADX = EMA(DX, 14日)               | 需严格遵循Wilder公式步骤                                                    |

#### **3. 风险模型公式**
| **指标**           | **公式**                                                                 | **实现逻辑**                                                                 |
|--------------------|-------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **VaR（风险价值）**| `历史模拟法：取5%分位数的日收益亏损`                                      | 需至少3年历史数据，按置信度95%计算                                           |
| **最大回撤**       | `回撤 = (峰值 - 谷值) / 峰值`                                            | 遍历历史数据，记录每个时间点的最大回撤                                        |

---

### **四、实现步骤**
#### **1. 数据获取模块**
- **步骤1：历史价格**  
  - 通过`yfinance`获取OHLCV数据：  
    ```python
    import yfinance as yf
    data = yf.download('AAPL', start='2020-01-01', end='2023-12-31', interval='1d')
    ```
- **步骤2：财务报表**  
  - 调用EOD Historical Data的`/fundamentals`接口：  
    ```
    GET https://eodhistoricaldata.com/api/fundamentals/AAPL?api_token=free_key
    ```
  - 解析JSON中的`Financials.Balance_Sheet`、`Financials.Income_Statement`字段。

#### **2. 指标计算模块**
- **步骤1：基本面指标计算**  
  - **ROE计算**：  
    ```python
    def calculate_roe(income_stmt, balance_sheet):
        net_income = income_stmt.loc['Net Income']
        equity = balance_sheet.loc['Total Shareholder Equity']
        return net_income / equity.mean()  # 使用平均股东权益
    ```
- **步骤2：技术指标计算**  
  - **布林带计算**：  
    ```python
    def bollinger_bands(close_prices, window=20, std_dev=2):
        ma = close_prices.rolling(window).mean()
        std = close_prices.rolling(window).std()
        upper = ma + std_dev * std
        lower = ma - std_dev * std
        return ma, upper, lower
    ```

#### **3. 模型集成模块**
- **多因子打分模型**  
  - **因子归一化**：将ROE、营收增长率等指标标准化为0-100分。  
  - **动态权重**：根据ADX值调整技术面权重（ADX>25时技术面权重+10%）。

#### **4. 风险控制模块**
- **止损策略**：  
  - **波动止损**：若当日跌幅超过2倍ATR，触发止损。  
  - **时间止损**：持仓超过5日未达目标价，自动平仓。

---

### **五、异常处理与校验**
#### **1. 数据校验规则**
| **异常类型**       | **检测逻辑**                          | **处理方式**                     |
|--------------------|---------------------------------------|----------------------------------|
| 财务数据矛盾       | 负债率>100%且ROE>20%                  | 标记为异常，人工复核财报原文      |
| 价格数据跳空       | 当日开盘价较前收盘涨跌幅>20%          | 暂停交易信号，等待数据确认        |
| 情绪数据噪声       | 社交媒体情绪指数单日波动>3σ           | 使用移动平均平滑                  |

#### **2. 容错机制**
- **API降级策略**：  
  - 若EOD Historical Data请求失败，自动切换至Yahoo Finance的`balanceSheetHistory`接口。  
- **缓存机制**：  
  - 本地存储最近30天数据，避免API不可用导致中断。

---

### **六、输出与交付**
#### **1. 分析报告模板**
| **模块**           | **内容**                              | **格式**          |
|--------------------|---------------------------------------|-------------------|
| 估值摘要           | PE分位数、DCF区间、行业对比           | 表格+雷达图       |
| 技术信号           | 均线排列、RSI超买超卖、成交量异动     | K线图+指标叠加    |
| 风险提示           | VaR值、最大回撤、负债预警             | 红色高亮文本      |

#### **2. 交付物清单**
- **代码仓库**：包含数据获取、指标计算、模型集成模块的Python脚本。  
- **API文档**：详细说明每个接口的调用参数与返回字段。  
- **测试案例**：苹果（AAPL）、特斯拉（TSLA）的完整分析流程示例。

---

### **七、实施路线图**
1. **第1周**：完成数据获取模块开发，实现Yahoo Finance与EOD Historical Data的对接。  
2. **第2周**：构建基本面与技术面指标计算库，通过单元测试验证公式准确性。  
3. **第3周**：集成多因子模型，实现动态权重调整逻辑。  
4. **第4周**：部署风险控制模块，完成历史回测（2015-2023年数据）。  
5. **第5周**：输出分析报告模板，编写用户操作手册。

---

### **八、备注**
- **合规性**：确保使用的API符合数据版权条款（如Yahoo Finance禁止商业用途）。  
- **扩展性**：预留接口支持未来添加期权数据、供应链数据等因子。