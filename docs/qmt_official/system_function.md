# 系统函数

> 来源: https://dict.thinktrader.net/innerApi/

## init - 初始化函数初始化函数，只在整个策略开始时调用运行到一次。用于初始订阅行情，订阅账号信息使用。init函数执行完成前部分接口无法使用，如交易日获取函数get_trading_dates。

**系统函数 不可被手动调用**

**参数：**

| 名称 | 类型 | 描述 
| `ContextInfo` | `object` | 策略运行环境对象，可以用于存储自定义的全局变量 

**返回：** 无

**示例：**

后初始化函数，在初始化函数执行完成后被调用一次。可以用于放置一次性触发的下单，取数据操作代码。

模型回测时无效

定时器没有结束方法，会随着策略的结束而结束。

period有nMilliSecond、nSecond和Day三个周期单元，部分周期下定时器函数在第一次运行之前会先等待一个period

parent_node：str，父节点，''为'我的'（默认目录）

sector_name：str，要创建的板块名

overwrite：bool，是否覆盖。如果目标节点已存在，为True时跳过，为False时在sector_name后增加数字编号，编号为从1开始自增的第一个不重复的值。