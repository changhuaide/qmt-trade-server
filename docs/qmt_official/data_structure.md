# 数据结构

> 来源: https://dict.thinktrader.net/innerApi/

## 数据类## Tick - Tick 对象行情快照数据

### get_market_data_ex/get_full_tick返回对象：
### subscribe_quote/subscribe_whole_quote回调对象：同 `get_full_tick` 返回结构

## Bar - Bar对象bar数据是指各种频率的行情数据

| 字段 | 数据类型 | 含义 
| `time` | `int` | `时间` 
| `open` | `float` | `开盘价` 
| `high` | `float` | `最高价` 
| `low` | `float` | `最低价` 
| `close` | `float` | `收盘价` 
| `volume` | `float` | `成交量` 
| `amount` | `float` | `成交额` 
| `settelementPrice` | `float` | `今结算` 
| `openInterest` | `float` | `持仓量` 
| `preClose` | `float` | `前收盘价` 
| `suspendFlag` | `int` | `停牌` 1停牌，0 不停牌 

## l2quote - Level2行情快照
| 字段名 | 数据类型 | 解释 
| time | int | 时间戳 
| stime | string | 时间戳字符串形式 
| lastPrice | float | 最新价 
| open | float | 开盘价 
| high | float | 最高价 
| low | float | 最低价 
| amount | float | 成交额 
| volume | int | 成交总量 
| pvolume | int | 原始成交总量(未经过股手转换的成交总量) 
| stockStatus | int | 证券状态 
| openInt | int | 持仓量 
| transactionNum | int | 成交笔数(期货没有，单独计算) 
| lastClose | float | 前收盘价 
| lastSettlementPrice | float | 前结算(股票为0) 
| settlementPrice | float | 今结算(股票为0) 
| askPrice | list[float] | 多档委卖价 
| askVol | list[int] | 多档委卖量 
| bidPrice | list[float] | 多档委买价 
| bidVol | list[int] | 多档委买量 

## l2quoteaux - Level2行情快照补充
| 字段名 | 数据类型 | 解释 
| time | int | 时间戳 
| stime | string | 时间戳字符串形式 
| avgBidPrice | float | 委买均价 
| totalBidQuantity | int | 委买总量 
| avgOffPrice | float | 委卖均价 
| totalOffQuantity | int | 委卖总量 
| withdrawBidQuantity | int | 买入撤单总量 
| withdrawBidAmount | float | 买入撤单总额 
| withdrawOffQuantity | int | 卖出撤单总量 
| withdrawOffAmount | float | 卖出撤单总额 

## l2order - Level2逐笔委托
提示

注：上交所的撤单信息在逐笔委托的委托方向，区分撤买撤卖

- 0 - 未知
- 1 - 买入
- 2 - 卖出
- 3 - 撤买（上交所）
- 4 - 撤卖（上交所）

## l2transaction - Level2逐笔成交
| 字段名 | 数据类型 | 解释 
| time | int | 时间戳 
| stime | string | 时间戳字符串形式 
| price | float | 成交价 
| volume | int | 成交量 
| amount | float | 成交额 
| tradeIndex | int | 成交记录号 
| buyNo | int | 买方委托号 
| sellNo | int | 卖方委托号 
| tradeType | int | 成交类型 
| tradeFlag | int | 成交标志 

提示

深交所逐笔成交的撤单标志，没有方向

- 0 - 未知
- 1 - 外盘，主买
- 2 - 内盘，主卖
- 3 - 撤单

## l2transactioncount - Level2逐笔成交统计
| 字段名 | 数据类型 | 解释 
| time | int | 时间戳 
| bidNumber | int | 主买单总单数 
| offNumber | int | 主卖单总单数 
| ddx | float | 大单动向 
| ddy | float | 涨跌动因 
| ddz | float | 大单差分 
| netOrder | int | 净挂单量 
| netWithdraw | int | 净撤单量 
| withdrawBid | int | 总撤买量 
| withdrawOff | int | 总撤卖量 
| bidNumberDx | int | 主买单总单数增量 
| offNumberDx | int | 主卖单总单数增量 
| transactionNumber | int | 成交笔数增量 
| bidMostAmount | float | 主买特大单成交额 
| bidBigAmount | float | 主买大单成交额 
| bidMediumAmount | float | 主买中单成交额 
| bidSmallAmount | float | 主买小单成交额 
| bidTotalAmount | float | 主买累计成交额 
| offMostAmount | float | 主卖特大单成交额 
| offBigAmount | float | 主卖大单成交额 
| offMediumAmount | float | 主卖中单成交额 
| offSmallAmount | float | 主卖小单成交额 
| offTotalAmount | float | 主卖累计成交额 
| unactiveBidMostAmount | float | 被动买特大单成交额 
| unactiveBidBigAmount | float | 被动买大单成交额 
| unactiveBidMediumAmount | float | 被动买中单成交额 
| unactiveBidSmallAmount | float | 被动买小单成交额 
| unactiveBidTotalAmount | float | 被动买累计成交额 
| unactiveOffMostAmount | float | 被动卖特大单成交额 
| unactiveOffBigAmount | float | 被动卖大单成交额 
| unactiveOffMediumAmount | float | 被动卖中单成交额 
| unactiveOffSmallAmount | float | 被动卖小单成交额 
| unactiveOffTotalAmount | float | 被动卖累计成交额 
| netInflowMostAmount | float | 净流入超大单成交额（lv1数据不支持计算，返回为 0，如有需求可咨询高频资金流数据） 
| netInflowBigAmount | float | 净流入大单成交额（lv1数据不支持计算，返回为 0，如有需求可咨询高频资金流数据） 
| netInflowMediumAmount | float | 净流入中单成交额（lv1数据不支持计算，返回为 0，如有需求可咨询高频资金流数据） 
| netInflowSmallAmount | float | 净流入小单成交额（lv1数据不支持计算，返回为 0，如有需求可咨询高频资金流数据） 
| bidMostVolume | int | 主买特大单成交量 
| bidBigVolume | int | 主买大单成交量 
| bidMediumVolume | int | 主买中单成交量 
| bidSmallVolume | int | 主买小单成交量 
| bidTotalVolume | int | 主买累计成交量 
| offMostVolume | int | 主卖特大单成交量 
| offBigVolume | int | 主卖大单成交量 
| offMediumVolume | int | 主卖中单成交量 
| offSmallVolume | int | 主卖小单成交量 
| offTotalVolume | int | 主卖累计成交量 
| unactiveBidMostVolume | int | 被动买特大单成交量 
| unactiveBidBigVolume | int | 被动买大单成交量 
| unactiveBidMediumVolume | int | 被动买中单成交量 
| unactiveBidSmallVolume | int | 被动买小单成交量 
| unactiveBidTotalVolume | int | 被动买累计成交量 
| unactiveOffMostVolume | int | 被动卖特大单成交量 
| unactiveOffBigVolume | int | 被动卖大单成交量 
| unactiveOffMediumVolume | int | 被动卖中单成交量 
| unactiveOffSmallVolume | int | 被动卖小单成交量 
| unactiveOffTotalVolume | int | 被动卖累计成交量 
| netInflowMostVolume | int | 净流入超大单成交量 
| netInflowBigVolume | int | 净流入大单成交量 
| netInflowMediumVolume | int | 净流入中单成交量 
| netInflowSmallVolume | int | 净流入小单成交量 
| bidMostAmountDx | float | 主买特大单成交额增量 
| bidBigAmountDx | float | 主买大单成交额增量 
| bidMediumAmountDx | float | 主买中单成交额增量 
| bidSmallAmountDx | float | 主买小单成交额增量 
| bidTotalAmountDx | float | 主买累计成交额增量 
| offMostAmountDx | float | 主卖特大单成交额增量 
| offBigAmountDx | float | 主卖大单成交额增量 
| offMediumAmountDx | float | 主卖中单成交额增量 
| offSmallAmountDx | float | 主卖小单成交额增量 
| offTotalAmountDx | float | 主卖累计成交额增量 
| unactiveBidMostAmountDx | float | 被动买特大单成交额增量 
| unactiveBidBigAmountDx | float | 被动买大单成交额增量 
| unactiveBidMediumAmountDx | float | 被动买中单成交额增量 
| unactiveBidSmallAmountDx | float | 被动买小单成交额增量 
| unactiveBidTotalAmountDx | float | 被动买累计成交额增量 
| unactiveOffMostAmountDx | float | 被动卖特大单成交额增量 
| unactiveOffBigAmountDx | float | 被动卖大单成交额增量 
| unactiveOffMediumAmountDx | float | 被动卖中单成交额增量 
| unactiveOffSmallAmountDx | float | 被动卖小单成交额增量 
| unactiveOffTotalAmountDx | float | 被动卖累计成交额增量 
| netInflowMostAmountDx | float | 净流入超大单成交额增量 
| netInflowBigAmountDx | float | 净流入大单成交额增量 
| netInflowMediumAmountDx | float | 净流入中单成交额增量 
| netInflowSmallAmountDx | float | 净流入小单成交额增量 
| bidMostVolumeDx | int | 主买特大单成交量增量 
| bidBigVolumeDx | int | 主买大单成交量增量 
| bidMediumVolumeDx | int | 主买中单成交量增量 
| bidSmallVolumeDx | int | 主买小单成交量增量 
| bidTotalVolumeDx | int | 主买累计成交量增量 
| offMostVolumeDx | int | 主卖特大单成交量增量 
| offBigVolumeDx | int | 主卖大单成交量增量 
| offMediumVolumeDx | int | 主卖中单成交量增量 
| offSmallVolumeDx | int | 主卖小单成交量增量 
| offTotalVolumeDx | int | 主卖累计成交量增量 
| unactiveBidMostVolumeDx | int | 被动买特大单成交量增量 
| unactiveBidBigVolumeDx | int | 被动买大单成交量增量 
| unactiveBidMediumVolumeDx | int | 被动买中单成交量增量 
| unactiveBidSmallVolumeDx | int | 被动买小单成交量增量 
| unactiveBidTotalVolumeDx | int | 被动买累计成交量增量 
| unactiveOffMostVolumeDx | int | 被动卖特大单成交量增量 
| unactiveOffBigVolumeDx | int | 被动卖大单成交量增量 
| unactiveOffMediumVolumeDx | int | 被动卖中单成交量增量 
| unactiveOffSmallVolumeDx | int | 被动卖小单成交量增量 
| unactiveOffTotalVolumeDx | int | 被动卖累计成交量增量 
| netInflowMostVolumeDx | int | 净流入超大单成交量增量 
| netInflowBigVolumeDx | int | 净流入大单成交量增量 
| netInflowMediumVolumeDx | int | 净流入中单成交量增量 
| netInflowSmallVolumeDx | int | 净流入小单成交量增量 

## l2orderqueue - Level2委买委卖队列## 交易类## Account - 账户对象
| 字段名 | 数据类型 | 解释 
| m_strAccountID | str | 资金账号，用于识别不同的资金账户 
| m_nBrokerType | int | 账号类型，表示账号的具体种类 
| m_dMaxMarginRate | float | 保证金比率，通常用于期货账号 
| m_dFrozenMargin | float | 冻结保证金，指投资者在交易中被冻结的保证金金额 
| m_dFrozenCash | float | 冻结金额，指投资者在交易中被冻结的资金金额 
| m_dFrozenCommission | float | 冻结手续费，指投资者在交易中被冻结的手续费金额 
| m_dRisk | float | 风险度，指投资者账户的风险程度 
| m_dNav | float | 单位净值，用于表示基金的净值 
| m_dPreBalance | float | 期初权益，指期初时账户的资金金额 
| m_dBalance | float | 总资产，表示账户的总资金金额 
| m_dAvailable | float | 可用金额，指账户中可用于交易和提取的资金金额 
| m_dCommission | float | 手续费 (旧版本为 m_dComission) 
| m_dPositionProfit | float | 持仓盈亏，指当前持有的证券或期货合约的盈亏金额 
| m_dCloseProfit | float | 平仓盈亏，在期货交易中表示已经平仓的交易的盈亏金额 
| m_dCashIn | float | 出入金净值，表示账户中出入金的净额 
| m_dCurrMargin | float | 当前使用的保证金金额 
| m_dInitBalance | float | 初始权益，指账户初始时的权益金额 
| m_strStatus | str | 状态，表示账户的当前状态 
| m_dInitCloseMoney | float | 期初平仓盈亏，指账户初始时的平仓盈亏金额 
| m_dInstrumentValue | float | 总市值，表示持有的证券或期货合约的总市值 
| m_dDeposit | float | 入金，指账户中的入金金额 
| m_dWithdraw | float | 出金，指账户中的出金金额 
| m_dPreCredit | float | 上次信用额度，用于表示上次的信用额度 
| m_dPreMortgage | float | 上次质押，指上次的质押金额 
| m_dMortgage | float | 质押，指当前的质押金额 
| m_dCredit | float | 信用额度，表示账户的信用额度 
| m_dAssetBalance | float | 证券初始资金，表示股票账户的初始资金 
| m_strOpenDate | str | 起始日期，表示账户的起始日期 
| m_dFetchBalance | float | 可取金额，指账户中可取出的金额 
| m_strTradingDate | str | 交易日，表示当前的交易日期 
| m_dStockValue | float | 股票总市值，表示股票账户中持有的股票的总市值 
| m_dLoanValue | float | 债券总市值，表示账户中持有的债券的总市值 
| m_dFundValue | float | 基金总市值，包括ETF和封闭式基金在内的基金的总市值 
| m_dRepurchaseValue | float | 回购总市值，表示账户中持有的所有回购交易的总市值 
| m_dLongValue | float | 多单总市值，指现货账户中多单持仓的总市值 
| m_dShortValue | float | 空单总市值，指现货账户中空单持仓的总市值 
| m_dNetValue | float | 净持仓总市值，指现货账户中多单总市值减去空单总市值的差额 
| m_dAssureAsset | float | 净资产，表示账户的净资产金额 
| m_dTotalDebit | float | 总负债，表示账户的总负债金额 
| m_dEntrustAsset | float | 可信资产，用于校对账户资金的准确性 
| m_dInstrumentValueRMB | float | 总市值（人民币），指沪港通账户中的持仓证券的总市值 
| m_dSubscribeFee | float | 申购费，指申购基金时支付的费用 
| m_dGoldValue | float | 库存市值，表示黄金现货账户中黄金库存的市值 
| m_dGoldFrozen | float | 现货冻结，表示黄金现货账户中被冻结的黄金金额 
| m_dMargin | float | 占用保证金，用于维持保证金 
| m_strMoneyType | str | 币种，表示账户的资金所使用的货币种类 
| m_dPurchasingPower | float | 购买力，指账户可用于购买投资品的金额 
| m_dRawMargin | float | 原始保证金，指期货账户中的原始保证金金额 
| m_dBuyWaitMoney | float | 买入待交收金额（元），指账户中买入股票但尚未交收的金额 
| m_dSellWaitMoney | float | 卖出待交收金额（元），指账户中卖出股票但尚未交收的金额 
| m_dReceiveInterestTotal | float | 本期间应计利息，指账户本期间内应计的利息金额 
| m_dRoyalty | float | 权利金收支，指期货期权交易中的权利金收支金额 
| m_dFrozenRoyalty | float | 冻结权利金，指期货期权交易中被冻结的权利金金额 
| m_dRealUsedMargin | float | 实时占用保证金，用于股票期权交易中表示实时占用的保证金金额 
| m_dRealRiskDegree | float | 实时风险度，用于股票期权交易中表示实时的风险度 

## Order - 委托对象
m_strAccountID

资金账号，账号，账号，资金账号

m_strExchangeID

m_strExchangeName

m_strProductID

m_strProductName

m_strInstrumentID

m_strInstrumentName

证券名称，合约名称

m_nRef

m_strOrderRef

内部委托号，下单引用等于股票的内部委托号

m_nOrderPriceType

m_nDirection

m_nOffsetFlag

m_nHedgeFlag

m_dLimitPrice

float

委托价格，限价单的限价，即报价

m_nVolumeTotalOriginal

委托数量，最初的委托数量

m_nOrderSubmitStatus

m_strOrderSysID

合同编号，委托号

m_nOrderStatus

m_nVolumeTraded

成交数量，已成交量

m_nVolumeTotal

委托剩余量，当前总委托量，股票中表示总委托量减去成交量

m_nErrorID

m_strErrorMsg

m_nTaskId

m_dFrozenMargin

float

冻结金额，冻结保证金

m_dFrozenCommission

float

冻结手续费

m_strInsertDate

委托日期，报单日期

m_strInsertTime

m_dTradedPrice

float

成交均价（股票）

m_dCancelAmount

float

m_strOptName

买卖标记，展示委托属性的中文

m_dTradeAmount

float

成交金额，期货的计算方式为均价乘以数量乘以合约乘数

m_eEntrustType

m_strCancelInfo

m_strUnderCode

标的证券代码

m_eCoveredFlag

备兑标记，'0’表示非备兑，'1’表示备兑

m_dOrderPriceRMB

float

委托价格（人民币），目前用于港股通

m_dTradeAmountRMB

float

成交金额（人民币），目前用于港股通

m_dReferenceRate

float

汇率，目前用于港股通

m_strCompactNo

m_eCashgroupProp

m_dShortOccupedMargin

float

预估在途占用保证金，用于期权

m_strXTTrade

是否是迅投交易

m_strAccountKey

账号key，唯一区别不同账号的key

m_strRemark

m_strAccountID

m_strExchangeID

m_strExchangeName

m_strProductID

m_strProductName

m_strInstrumentID

m_strInstrumentName

m_strTradeID

m_strOrderRef

下单引用，等于股票的内部委托号

m_strOrderSysID

合同编号，报单编号，委托号

m_nDirection

m_nOffsetFlag

m_nHedgeFlag

m_dPrice

float

m_nVolume

成交量，期货单位手，股票做到股

m_strTradeDate

m_strTradeTime

m_dCommission

float

m_dTradeAmount

float

成交额，期货 = 均价 * 量 * 合约乘数

m_nTaskId

m_nOrderPriceType

m_strOptName

买卖标记，展示委托属性的中文

m_eEntrustType

m_eFutureTradeType

m_nRealOffsetFlag

m_eCoveredFlag

ECoveredFlag类型，备兑标记 '0' - 非备兑，'1' - 备兑

m_nCloseTodayVolume

平今量，不显示

m_dOrderPriceRMB

float

委托价格（人民币），目前用于港股通

m_dPriceRMB

float

成交价格（人民币），目前用于港股通

m_dTradeAmountRMB

float

成交金额（人民币），目前用于港股通

m_dReferenceRate

float

汇率，目前用于港股通

m_strXTTrade

是否是迅投交易

m_strCompactNo

m_dCloseProfit

float

平仓盈亏，目前用于外盘

m_strRemark

m_strAccountKey

账号key，唯一区别不同账号的key

m_nRef

m_strAccountID

string

m_strExchangeID

string

m_strExchangeName

string

m_strProductID

string

m_strProductName

string

m_strInstrumentID

string

m_strInstrumentName

string

m_nHedgeFlag

m_nDirection

m_strOpenDate

string

开仓日期 股票此字段无效

m_strTradeID

string

成交号，最初开仓位的成交

m_nVolume

当前拥股/持仓量

m_dOpenPrice

float

持仓成本 ；持仓成本 = (总买入金额 - 总卖出金额) / 剩余数量

m_strTradingDay

string

在实盘运行中是当前交易日，在回测中是股票最后交易过的日期

m_dMargin

float

m_dOpenCost

float

开仓成本，等于成本价*第一次建仓的量，后续减持会影响，不算手续费，股票不适用

m_dSettlementPrice

float

最新结算价/当前价

m_nCloseVolume

平仓量（对于股票不适用）

m_dCloseAmount

float

平仓额（对于股票不适用）

m_dFloatProfit

float

m_dCloseProfit

float

平仓盈亏（对于股票不适用）

m_dMarketValue

float

市值/合约价值

m_dPositionCost

float

持仓成本（对于股票不适用）

m_dPositionProfit

float

持仓盈亏（对于股票不适用）

m_dLastSettlementPrice

float

最新结算价（对于股票不适用）

m_dInstrumentValue

float

合约价值（对于股票不适用）

m_bIsToday

m_strStockHolder

string

m_nFrozenVolume

m_nCanUseVolume

m_nOnRoadVolume

m_nYesterdayVolume

m_dLastPrice

float

最新价/当前价

m_dAvgOpenPrice

float

开仓均价（对于股票不适用）

m_dProfitRate

float

m_eFutureTradeType

m_strExpireDate

string

到期日（针对逆回购）

m_strComTradeID

string

组合成交号

m_nLegId

m_dTotalCost

float

累计成本（自定义，股票信用用到）

m_dSingleCost

float

单股成本（自定义，股票信用用

m_nCoveredVolume

备兑数量，用于个股期权

m_eSideFlag

持仓类型 ，用于个股期权，标记 '0' - 权利，'1' - 义务，'2' - '备兑'

m_dReferenceRate

float

汇率，目前用于港股通

m_dStructFundVol

float

分级基金可用（可分拆或可合并）

m_dRedemptionVolume

float

分级基金可赎回量

m_nPREnableVolume

申赎可用量（记录当日申购赎回的股票或基金数量）

m_dRealUsedMargin

float

实时占用保证金，用于期权

m_dRoyalty

float

m_dStockLastPrice

float

标的证券最新价，用于期权

m_dStaticHoldMargin

float

静态持仓占用保证金，用于期权

m_nOptCombUsedVolume

期权组合占用数量

m_nEnableExerciseVolume

能够行使的数量，用于个股期权

m_strAccountKey

string

账号key，唯一区别不同账号的key