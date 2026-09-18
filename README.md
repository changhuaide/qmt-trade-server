# qmt-trade-server

**从外部 Python 通过 HTTP 调用 QMT 交易和行情接口的轻量级桥接工具。**

## 背景

近期部分券商开始关闭 miniQMT 通道，许多用户需要迁移到完整版 QMT。但完整版 QMT 的内置 Python 环境受限：

- **无法安装第三方库** — 内置 Python 环境无法使用 pip，依赖管理困难
- **难以与外部系统集成** — 无法直接连接 Web 服务、数据库、消息队列
- **策略迁移成本高** — 原有基于 xtquant 的策略需要重写

本项目提供 **HTTP 桥接方案**，让你在外部 Python 中通过标准 HTTP 协议调用 QMT 的交易和行情功能：

- ✅ **低代码迁移** — 策略代码几乎不用改动，只需将 `xtquant.xxx()` 调用替换为 `client.xxx()` HTTP 调用
- ✅ **完整功能** — 交易下单、行情查询、持仓/资产/委托/成交查询、事件回调
- ✅ **零外部依赖** — 服务端和客户端均仅使用 Python 标准库

**从 xtquant 迁移只需改 3 行代码：**

```python
# 原 xtquant 代码
from xtquant import xttrader
xttrader.order_stock(account, '000001.SZ', 23, 100, 11, 10.5)

# 迁移后
from client import QMTHttpClient
client = QMTHttpClient()
client.buy('000001.SZ', volume=100, price=10.5)
```

QMT（迅投极速策略交易系统）的内置 Python 环境无法直接安装第三方库，也难以与外部系统集成。本项目通过在 QMT 内置 Python 中运行一个 HTTP 服务端，让外部 Python 可以通过标准 HTTP 协议调用 QMT 的交易、行情、持仓等全部功能。

## 特性

- **零外部依赖** — 服务端和客户端均仅使用 Python 标准库
- **14 个 HTTP 接口** — 覆盖交易下单、行情查询、持仓/资产/委托/成交查询、事件回调
- **回调替代方案** — 事件轮询替代 QMT 的 callback 推送机制
- **tick 轮询替代全推** — 通过 HTTP 轮询获取实时 tick，替代 `subscribe_whole_quote`
- **xtquant 兼容接口** — 客户端提供与 xtquant 相似的 API，便于迁移
- **纯 Python 实现** — 服务端 ~800 行，客户端 ~400 行，代码透明可审计

## 架构

```
┌─────────────────────────────┐       HTTP        ┌──────────────────────────────┐
│     External Python          │  ◄──────────────►  │    QMT Built-in Python        │
│                              │   127.0.0.1:8964   │                              │
│  from client import          │                    │  trade_server.py              │
│    QMTHttpClient             │                    │  (QMT Strategy)               │
│                              │                    │                              │
│  client.buy('000001.SZ',     │   POST /buy       │    ↓ passorder()              │
│    volume=100, price=10.5)   │ ─────────────────► │    ↓ Exchange                 │
│                              │                    │                              │
│  client.get_full_tick(       │   GET /tick        │    ↓ get_full_tick()         │
│    ['000001.SZ'])            │ ─────────────────► │    ↓ QMT Market Data          │
│                              │                    │                              │
└─────────────────────────────┘                    └──────────────────────────────┘
```

## 快速开始

### 1. 启动服务端

将 `server/trade_server.py` 复制到 QMT 的策略目录，在 QMT 中新建策略并加载此文件，然后运行策略。

服务端会自动在 `127.0.0.1:8964` 启动 HTTP 服务。

### 2. 安装客户端

```bash
# 直接复制 client/ 目录到你的项目中
# 或者：
pip install qmt-trade-server  # (TODO: 发布到 PyPI)
```

### 3. 使用

```python
from client import QMTHttpClient

client = QMTHttpClient()

# 检查连接
assert client.check_connection()

# 查行情
tick = client.get_full_tick(['000001.SZ'])
print(tick['000001.SZ']['lastPrice'])

# 查持仓
positions = client.get_positions()

# 下单
success, order_id = client.buy('000001.SZ', volume=100, price=10.5)

# 撤单
client.cancel(order_id)

# 轮询回调事件
events = client.poll_events(since=0)
```

## 接口列表

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/buy` | 买入下单 |
| POST | `/sell` | 卖出下单 |
| POST | `/cancel` | 撤单 |
| GET | `/positions` | 查询持仓 |
| GET | `/asset` | 查询账户资产 |
| GET | `/orders` | 查询委托（`?cancelable_only=1`） |
| GET | `/trades` | 查询成交 |
| GET | `/events` | 轮询回调事件（`?since=<timestamp>`） |
| GET | `/health` | 健康检查 |
| GET | `/tick` | 实时 tick（`?codes=000001.SZ,600830.SH`） |
| GET | `/instrument` | 合约详情（`?code=000001.SZ`） |
| GET | `/kline` | K 线数据（`?stock=000001.SZ&count=10&period=1d`） |
| GET | `/sector_list` | 板块列表（`?node=`） |
| GET | `/sector_stocks` | 板块内股票（`?sector=name`） |

详细文档见 [docs/api_reference.md](docs/api_reference.md)。

### 接口覆盖范围

本项目目前封装了 **14 个 HTTP 接口**，覆盖了实际项目中常用的功能：

- **交易类**：买入、卖出、撤单
- **查询类**：持仓、资产、委托、成交
- **行情类**：tick、K 线、合约详情、板块列表、板块股票
- **系统类**：健康检查、事件回调

**QMT 的 xtquant 库提供了更丰富的 API**（如期权、融资融券、分钟级 K 线等），但本项目未封装所有接口。如需使用未封装的接口，可以：

1. 参考 [docs/qmt_innerapi_docs/](docs/qmt_innerapi_docs/) 中的 QMT 官方中文文档（包含完整的 API 列表和参数说明）
2. 在 `server/trade_server.py` 中添加新的 HTTP endpoint，参考现有接口的实现模式（每个接口 20-30 行代码）
3. 在 `client/qmt_http_client.py` 中添加对应的客户端方法

**扩展示例**：假设需要添加"查询历史委托"接口

```python
# server/trade_server.py - 添加 endpoint
def handle_query_history_orders(params):
    from xtquant import xttrader
    orders = xttrader.query_stock_orders(_account_id)  # QMT API
    return {'success': True, 'orders': orders}

# client/qmt_http_client.py - 添加客户端方法
def get_history_orders(self):
    resp = self._request('GET', '/history_orders')
    return resp.get('orders', [])
```

## 示例

- [basic_usage.py](examples/basic_usage.py) — 完整使用流程
- [test_all_endpoints.py](examples/test_all_endpoints.py) — 全接口测试
- [tick_polling.py](examples/tick_polling.py) — tick 轮询示例

## 配置

### 服务端配置（trade_server.py 顶部）

```python
HTTP_HOST = '127.0.0.1'   # 监听地址
HTTP_PORT = 8964           # 监听端口
ACCOUNT_TYPE = 'stock'     # 账户类型
```

### 客户端配置

```python
client = QMTHttpClient(
    host='127.0.0.1',   # trade_server 地址
    port=8964,           # trade_server 端口
    timeout=5.0,         # HTTP 超时（秒）
    max_retries=2,       # 最大重试次数
)
```

## 与 xtquant 的对应关系

| xtquant API | HTTP 替代 | 说明 |
|-------------|----------|------|
| `XtQuantTrader.order_stock()` | `client.buy()` / `client.sell()` | 买入/卖出 |
| `XtQuantTrader.cancel_order_stock()` | `client.cancel()` | 撤单 |
| `XtQuantTrader.query_stock_positions()` | `client.get_positions()` | 持仓 |
| `XtQuantTrader.query_stock_asset()` | `client.get_asset()` | 资产 |
| `xtdata.get_full_tick()` | `client.get_full_tick()` | 实时 tick |
| `xtdata.get_instrument_detail()` | `client.get_instrument_detail()` | 合约详情 |
| `xtdata.get_market_data()` | `client.get_kline()` | K 线 |
| `XtQuantTraderCallback` | `client.poll_events()` | 事件回调 |
| `subscribe_whole_quote()` | 轮询 `get_full_tick()` | 实时行情 |

## 常见问题

**Q: 为什么需要这个项目？**

A: QMT 内置 Python 环境受限，无法安装 pip 包，也难以与外部系统（如 Web 服务、数据库、消息队列）集成。通过 HTTP 桥接，外部 Python 可以使用任意第三方库，同时利用 QMT 的交易通道。

**Q: 安全性如何？**

A: 服务端仅监听 `127.0.0.1`，不接受外部网络连接。所有请求在本机完成。

**Q: 性能如何？**

A: HTTP 请求延迟约 1-5ms，对于秒级策略完全足够。tick 轮询建议间隔 ≥500ms。

**Q: 支持哪些 QMT 版本？**

A: 需要 QMT 支持 `schedule_run()` API 和内置 Python 策略。已在迅投 QMT 上测试。

**Q: 账户 ID 如何获取？**

A: 服务端自动从 QMT 框架获取当前绑定的交易账户 ID，无需手动配置。

## 免责声明

本项目仅供**个人学习、研究和技术交流**使用，**严禁用于任何商业用途**。

使用本项目前，请仔细阅读以下声明：

1. **非商业用途** — 本项目的代码、文档及相关资源不得用于任何形式的商业活动，包括但不限于：
   - 作为商业产品或服务的一部分
   - 用于营利性交易或投资活动
   - 出售、出租或许可给第三方
   - 用于商业培训或付费课程

2. **投资风险自负** — 本项目涉及金融交易接口，使用本项目进行任何真实交易产生的**一切风险和损失由用户自行承担**。作者不对因使用本项目导致的任何直接、间接、附带或衍生的损失负责。

3. **仅供学习参考** — 本项目代码仅作为技术学习和研究用途，不构成任何投资建议或交易指导。用户应自行评估交易风险，并遵守相关法律法规。

4. **合规使用** — 用户在使用本项目时，应确保其行为符合所在国家或地区的法律法规，以及所使用的交易平台（如 QMT）的相关规定。

**使用本项目即表示您已阅读、理解并同意本免责声明的全部内容。如果您不同意本声明的任何条款，请立即停止使用本项目。**

### 联系方式

如需商业授权或其他合作，请联系作者：
- 微信：**chang_huaide**
- GitHub Issues：[提交 Issue](https://github.com/wider/qmt-trade-server/issues)

## License

MIT License. See [LICENSE](LICENSE).

**注意**：尽管本项目采用 MIT 许可证，但上述免责声明中的限制条款（特别是禁止商业用途）优先于 MIT 许可证的授权范围。如需商业使用，请联系作者另行授权。
