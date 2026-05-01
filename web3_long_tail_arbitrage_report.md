# Web3 长尾套利机会调研报告

日期：2026-04-30

> 说明：以下内容不是投资建议。Web3 套利、衍生品、RWA、预测市场和跨境资金流动都可能涉及市场、技术、合规和对手方风险，实盘前应自行确认所在地法规和平台条款。

## 核心判断

Web3 里“无风险套利”基本已经被机器人和专业做市吃掉了，但带一点操作复杂度、合规摩擦、资金碎片化、期限错配、结算规则差异的长尾套利/相对价值机会仍然有空间。

真正适合研究的是：低拥挤、可流程化、收益不靠预测单边方向的方向。

## 机会地图

| 方向 | 机会类型 | 拥挤度 | 资金门槛 | 适合度 |
|---|---:|---:|---:|---:|
| 链上借贷/清算 | 长尾资产清算、隔离池利差、健康因子机器人 | 中 | 中 | 高 |
| RWA | RWA 收益率差、链间/协议间 USDY/USYC/OUSG 等收益差 | 低-中 | 中 | 高 |
| Pendle/收益交易 | PT/YT 定价偏差、固定收益 vs 浮动收益利差 | 中 | 中 | 高 |
| Perp DEX | 长尾币 funding rate delta-neutral、DEX-CEX/DEX-DEX 资金费差 | 中 | 中-高 | 高 |
| Perp LP vault | HLP/JLP/GLP 类 LP 收益 + 对冲 | 中 | 中 | 中高 |
| Options | IV/RV 差、期限结构、Deribit vs 链上期权定价差 | 中低 | 高 | 中 |
| 预测市场 | 跨平台价差、同平台多结果价差、冷门市场流动性错价 | 中 | 低-中 | 中高 |
| 跨链稳定币 | 桥/链/池间稳定币折溢价、提现延迟带来的 basis | 中 | 中 | 中 |

## 最值得优先看的 8 类长尾机会

### 1. RWA 收益率轮动套利

RWA tokenized treasuries 已经不是小赛道。机会不是“买 RWA 等收益”这么简单，而是：

- 同一 RWA 资产在不同链的流动性、DeFi 激励、借贷抵押率不同。
- RWA 固定收益与 Aave/Morpho/Compound 稳定币借贷 APY 之间会阶段性倒挂。
- 有些 RWA 资产可作为抵押物，但市场对其折价、借贷上限、清算参数理解不足。

执行路径：

1. 建表跟踪 `USDC lending APY`、`USDY/USYC/OUSG native yield`、`DeFi incentive APY`、`退出滑点`。
2. 只做净收益差大于 1.5%-2% 年化的轮动，因为桥费、gas、退出折价会吃掉小利差。
3. 首选可自由转让、链上流动性较好的资产，例如 USDY；BUIDL/OUSG 等可能有 KYC/白名单限制。
4. 资金分 3 档：现金 USDC、RWA 资产、RWA 抵押借贷组合，避免全部锁死。

主要风险：KYC/赎回限制、RWA 发行人风险、流动性折价、监管变化、桥风险。

### 2. Pendle PT/YT 相对价值套利

Pendle 把收益资产拆成 PT 和 YT，核心关系是：

```text
PT + YT ~= SY
```

可做的不是盲目买高 APY，而是找：

- `PT 隐含固定收益` 高于你对未来实际收益的保守估计。
- `YT 价格` 低于你预计能收到的未来收益 + points/airdrop。
- PT/YT/SY 之间出现短暂偏离时做组合套利。

执行路径：

1. 每天抓 Pendle 市场：PT price、implied APY、underlying APY、YT price、到期日。
2. 建一个阈值：`implied APY - conservative realized APY > 3%-5%` 才买 PT。
3. 对 YT，只做你能估算收益来源的市场，比如 sUSDe、LRT、RWA 收益资产，不碰纯 points 叙事。
4. 临近到期前减少 YT 风险，因为 theta 衰减会非常快。

主要风险：收益率突降、协议积分不兑现、PT/YT 流动性不足、到期日前退出滑点。

### 3. 长尾 Perp DEX funding rate 套利

长尾机会在：

- 新上市 alt perp 的 funding 极端偏正或偏负。
- DEX 上某资产 OI 偏一边，CEX/spot 市场还没同步。
- Perp DEX 为吸引交易提供积分/返佣，抵消一部分费用。

执行路径：

1. 监控 Hyperliquid、Drift、dYdX、Aster、Vertex、GMX 与 Binance/Bybit/OKX 的 funding。
2. 只做可 delta-neutral 的组合：一边收 funding，另一边用 spot 或反向 perp 对冲。
3. 计算净收益：

```text
净 APR = 收到 funding - 支付 funding - 交易费 - 借币费 - 滑点 - 预估爆仓缓冲成本
```

4. 优先做长尾但有足够深度的币，不碰盘口太薄的微盘。
5. 杠杆控制在 1x-2x，核心是吃 carry，不是赌方向。

主要风险：funding 反转、交易所/链宕机、指数价格异常、对冲腿无法及时成交、长尾币插针。

### 4. Perp LP vault 收益 + 对冲

HLP、JLP、GLP 这类 LP vault 本质上吃交易费、做市收益、清算收益，但也承担交易员赢钱、库存暴露、极端行情亏损。

长尾做法不是裸存 LP，而是：

- 存入 LP vault。
- 估算 vault 的隐含 BTC/ETH/SOL/alt 风险暴露。
- 用 perp 做部分对冲，留下手续费/清算收益。

执行路径：

1. 选择透明度高、历史净值曲线可追踪的 vault。
2. 每周估算 vault beta：BTC beta、ETH beta、市场方向暴露。
3. 用低杠杆 perp 对冲 50%-80% 的方向风险。
4. 当 vault 收益低于 RWA 或稳定币 lending 时退出。

主要风险：vault 策略黑箱、极端行情交易员盈利导致 LP 亏损、对冲成本超过收益。

### 5. 链上清算机器人：避开 Aave 主池，盯隔离市场

Aave 主池清算竞争很激烈，但 Morpho、Euler、Silo、Gearbox、Radiant、Solend/Save 等隔离池或新链部署仍可能有机会。

空间主要来自：

- 小资产抵押池监控不足。
- Oracle 更新、LTV 参数变化、流动性迁移导致清算窗口。
- 新链 gas/MEV 竞争较弱。

执行路径：

1. 先选 2-3 条链，不要全链铺开，比如 Base、Arbitrum、Sonic、Sui/EVM 生态。
2. 监控借贷协议的 `health factor < 1.03` 地址。
3. 只做有足够 DEX 深度的抵押物清算，提前模拟还债、拿抵押、卖出全过程。
4. 用私有 RPC / builder relay，避免公开 mempool 被抢。
5. 清算利润阈值至少覆盖 gas 的 3-5 倍。

主要风险：被 MEV 抢跑、oracle 延迟、清算资产卖不掉、协议暂停、RPC 延迟。

### 6. 跨链稳定币 basis / 桥流动性套利

机会来自：

- 某条链 USDC/USDT/DAI/USDe 短缺，出现 10-80 bps 溢价。
- CCTP 原生 USDC 跨链慢于市场需求。
- 激励池导致某稳定币在特定链收益异常。

执行路径：

1. 监控 Curve、Uniswap、Aerodrome、Balancer、Maverick 的稳定币池价格。
2. 只使用原生桥或 CCTP/官方桥，少碰不透明 wrapped stablecoin。
3. 做“库存式套利”：多链预放 USDC，不每次临时桥。
4. 每笔交易要求净利差大于 20-30 bps，小于这个不值得。

主要风险：桥风险、假稳定币、提现延迟、池子被抽干、稳定币脱锚。

### 7. Options：波动率相对价值，而不是裸卖期权

Deribit 仍是 BTC/ETH options 核心流动性中心。长尾机会在：

- 短期限 IV 被事件炒高，但 realized vol 没跟上。
- ETH/BTC vol spread 异常。
- Deribit 与链上期权协议/结构化 vault 报价不同步。
- 同一标的不同期限 skew/term structure 变形。

执行路径：

1. 只从 BTC/ETH 开始，不建议先碰 alt options。
2. 跟踪 `DVOL`、7D/30D realized vol、ATM IV、25-delta skew。
3. 低风险做法：calendar spread、defined-risk iron condor、put spread/call spread。
4. 如果做 short vol，一定定义最大亏损，不裸卖远端尾部。

主要风险：gamma 爆炸、流动性突然消失、保证金模型变化、黑天鹅行情。

### 8. 预测市场：冷门市场规则差和多结果定价偏差

Polymarket/Kalshi 的主流跨平台套利已经非常卷，但长尾仍有空间：

- 同平台多结果市场，所有 outcome 价格和低于/高于 1。
- 冷门体育、天气、AI 产品、监管事件市场，参与者少。
- Polymarket 与 Kalshi 对“同一事件”的定义、结算源、时区、口径不同，产生价格差。
- 流动性提供者挂单赚 spread，而非抢纯套利。

执行路径：

1. 不做内幕信息、不做操纵天气/数据源等违法行为。
2. 抓取市场标题、resolution source、截止时间、YES/NO bid-ask。
3. 只有当规则完全等价时，才做跨平台 yes/no 套利。
4. 更推荐同平台多 outcome 检查：

```text
如果所有 YES 价格之和 < 1 - fees：买入所有结果
如果所有 YES 价格之和 > 1 + fees：卖出/买 NO 所有结果
```

5. 冷门市场要把资金占用时间计入收益率，不要只看名义价差。

主要风险：结算规则不同、KYC/地区限制、提现限制、市场取消、监管风险、流动性不足。

## 优先执行组合

如果目标是“有空间、能长期流程化”，建议按这个优先级：

1. **RWA + 稳定币收益轮动**  
   低频、容量中等、适合做资金底仓。目标是比纯 USDC 多 1%-3% 年化。

2. **Pendle PT 固定收益 + 少量 YT mispricing**  
   适合建立模型，收益来源清晰，能做期限管理。

3. **长尾 perp funding delta-neutral**  
   收益弹性高，但需要执行纪律和风控系统。

4. **预测市场冷门规则套利**  
   小资金先跑，验证数据抓取和结算理解能力。

5. **链上清算机器人**  
   技术门槛高，但如果能写 bot，这类机会比人工交易更可持续。

## 30 天落地路线

### 第 1 周：数据面板

搭建表或脚本，抓这些数据：

- DeFiLlama yields / RWA
- Pendle PT/YT implied APY
- Hyperliquid、dYdX、Drift、Binance、Bybit funding
- Curve/Uniswap/Aerodrome 稳定币池价格
- Polymarket/Kalshi 市场价格和规则文本

### 第 2 周：纸面回测

每类机会先不交易，记录：

- 价差出现频率
- 持续时间
- 可成交深度
- 手续费后收益
- 最大不利变化

### 第 3 周：小资金实盘

每类只放 5%-10% 测试资金。重点不是赚钱，而是测：

- 桥/提现耗时
- API 稳定性
- 实际成交滑点
- 风控报警是否及时

### 第 4 周：筛掉伪机会

留下满足这三个条件的策略：

```text
净收益 > 无风险/RWA 收益
最大单次损失可控
机会每周至少出现 2-3 次，或可作为低频资金配置
```

## 结论

现在 Web3 长尾套利的核心不在“更快”，而在“更细”。主流币 CEX 搬砖、BTC/ETH funding、热门预测市场跨平台价差，已经被充分竞争。

更有空间的是：

- RWA 与 DeFi 收益率之间的慢变量错配；
- Pendle 期限和收益预期错配；
- 长尾 perp DEX funding 与流动性激励；
- 隔离借贷市场清算；
- 预测市场冷门规则/多结果错价；
- 跨链稳定币库存式 basis。

如果只选一个方向开始，建议选 **RWA/Pendle 收益利差 + 小规模 perp funding 对冲**。它不要求毫秒级速度，模型可解释，能从小资金逐渐放大。
