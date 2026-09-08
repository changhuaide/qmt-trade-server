# 回调函数

> 来源: https://dict.thinktrader.net/innerApi/

## 实时主推函数## account_callback - 资金账号状态变化主推提示

- 仅在实盘运行模式下生效。
- 需要先在init里调用ContextInfo.set_account后生效。

**用法：** account_callback(ContextInfo, accountInfo)

**释义：** 当资金账号状态有变化时，这个函数被客户端调用

**参数：**

ContextInfo：特定对象

ContextInfo：特定对象

ContextInfo：特定对象

ContextInfo：特定对象

ContextInfo：特定对象

ContextInfo：特定对象

errMsg：错误信息

ContextInfo：策略模型全局对象

seq:query_credit_account时输入查询seq