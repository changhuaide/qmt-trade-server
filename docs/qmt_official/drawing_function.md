# 绘图函数

> 来源: https://dict.thinktrader.net/innerApi/

## ContextInfo.paint - 在界面上画图在界面上画图

**调用方法：** ContextInfo.paint(name, value, index, line_style, color = 'white', limit = '')

**参数：**

| 参数名 | 类型 | 说明 | 提示 
| `name` | `string` | 需显示的指标名 | 
| `value` | `number` | 需显示的数值 | 
| `index` | `number` | 显示索引位置 | 填 -1 表示按主图索引显示 
| `line_style` | `number` | 线型 | 0：曲线42：柱状线 
| `color` | `string` | 颜色（不填默认为白色） | blue：蓝色brown：棕cyan：蓝绿green：绿magenta：品红red：红white：白yellow：黄 
| `limit` | `string` | 画线控制 | 'noaxis'：不影响坐标画线'nodraw'：不画线 

**返回：**无

**示例：**