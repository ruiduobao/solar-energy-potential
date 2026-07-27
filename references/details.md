
### 批量处理
```bash
python scripts\solar-energy-potential.py batch \
  --input locations.csv --lat-col lat --lon-col lon \
  --output solar_batch.json
```

### 经济分析
```bash
python scripts\solar-energy-potential.py economic \
  --lat 39.9 --lon 116.4 \
  --capacity 5.0 --cost-per-kwp 800 --electricity-price 0.12 \
  --output economic.json
```

## 安装

```bash
pip install requests>=2.28.0 numpy>=1.21.0
# 或: pip install -r scripts/requirements.txt
```

## 参数说明

- `--lat`: 纬度 (-90 到 90)
- `--lon`: 经度 (-180 到 180)
- `--input`: 批量模式输入 CSV
- `--lat-col`: CSV 中纬度列名
- `--lon-col`: CSV 中经度列名
- `--output`: 输出 JSON 文件
- `--efficiency`: 光伏板效率 (0.15-0.25)
- `--performance-ratio`: 性能比 (0.70-0.90)
- `--capacity`: 装机容量 kWp
- `--cost-per-kwp`: 每 kWp 系统成本 USD
- `--electricity-price`: 电价 USD/kWh
- `--year`: NASA POWER 数据年份
- `--json`: 以 JSON 输出

## 输出结果

- **年 GHI**：kWh/m²/年
- **最佳倾角**：度
- **年发电量**：kWh/kWp/年
- **容量因子**：%
- **经济指标**：回收期、LCOE、年节省

## API 信息

- **端点**: `https://power.larc.nasa.gov/api/temporal/daily/point`
- **无需 API 密钥**
- **数据**: NASA POWER Project
- **许可**: Public Domain

## 依赖库

```
requests>=2.28.0
numpy>=1.21.0
```

## 最佳倾角公式

固定支架光伏系统的最佳倾角估算：

```
倾角 ≈ 纬度 × 0.87
```

更精确的估算使用 PVWatts 方法：

| 支架类型 | 倾角公式 |
|---------|---------|
| 固定支架 | `纬度 × 0.87` |
| 季节可调 | `纬度 − 15°`（夏季），`纬度 + 15°`（冬季） |
| 跟踪支架 | 0°（水平轴），纬度（倾斜轴） |

**注意**：此为简化估算。实际最佳倾角取决于当地气候、反照率和遮挡情况。

## LCOE 公式文档

平准化度电成本（LCOE）计算公式：

```
LCOE = (CAPEX × CRF + O&M) / 年发电量
```

其中：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| CAPEX | 初始投资 ($/kWp) | 1000 |
| CRF | 资本回收因子 = r(1+r)ⁿ / ((1+r)ⁿ − 1) | r=0.06, n=25 |
| O&M | 年运维成本 ($/kWp/年) | 20 |
| 年发电量 | kWh/kWp/年（来自光伏输出） | 计算得出 |

使用 `--discount-rate` 和 `--system-lifetime` 调整 CRF 参数。

## 时间分辨率

NASA POWER 数据支持三种时间分辨率：

| 分辨率 | 参数 | 用途 |
|--------|------|------|
| 日 | `daily` | 详细分析、逐日变化 |
| 月 | `monthly` | 季节模式、资源制图 |
| 气候态 | `climatology` | 长期平均、可行性研究 |

使用 `--temporal-resolution monthly` 指定。默认 `daily`。

## CSV 输出格式

除 JSON 外，还支持 CSV 输出：

```bash
python scripts\solar-energy-potential.py assess \
  --lat 39.9 --lon 116.4 \
  --output solar_assessment.csv --format csv
```

批量模式默认输出 CSV（每个地点一行）。

## API 错误处理与重试逻辑

工具处理 NASA POWER API 错误：

| 错误 | 原因 | 工具行为 |
|------|------|---------|
| HTTP 500 | 服务器错误 | 等待 30 秒，最多重试 3 次 |
| HTTP 503 | 服务不可用 | 等待 60 秒，重试 |
| 超时 | 响应慢 | 增加超时，重试 |
| 无数据 | 坐标无效 | 报告错误，建议有效范围 |

使用 `--max-retries 5` 和 `--retry-delay 120` 自定义。

## 已知限制

本工具仅提供估算。已知限制包括：

- **无遮挡分析**：不考虑地形或建筑阴影
- **无污染损失**：不建模灰尘/污染对面板的影响
- **无地形效应**：假设平面；无坡度/坡向校正
- **简化光伏模型**：使用性能比；不建模逆变器效率曲线
- **NASA POWER 分辨率**：~0.5°×0.5° 网格；无法捕捉局地小气候
- **经济假设**：简单 LCOE；不建模衰减、融资、补贴

详细系统设计请使用 PVsyst、SAM 或 HOMER。

## 批量输出格式

批量模式产生结构化输出：

```json
{
  "locations": [
    {"lat": 39.9, "lon": 116.4, "ghi": 1450, "tilt": 34.7, "pv_output": 1320},
    {"lat": 31.2, "lon": 121.5, "ghi": 1380, "tilt": 27.2, "pv_output": 1250}
  ],
  "summary": {
    "mean_ghi": 1415,
    "total_potential_kwp": 2570
  }
}
```

CSV 输出每个地点一行，所有指标为列。

## 可视化

- **GHI 制图**：插点结果生成空间栅格（使用 QGIS 或 Python `scipy.interpolate`）
- **柱状图**：比较不同地点的光伏输出
- **月际分布**：绘制月 GHI 展示季节变化
- **经济散点图**：LCOE vs GHI 用于选址对比

## 引用格式

使用 NASA POWER 数据时请引用：

```bibtex
@misc{nasa_power,
  author       = {{NASA Langley Research Center}},
  title        = {NASA POWER Project},
  howpublished = {\url{https://power.larc.nasa.gov}},
  year         = {2024},
  note         = {SSE-R6}
}

@software{solar_energy_potential,
  author  = {ruiduobao},
  title   = {Solar Energy Potential Assessment Tool},
  url     = {https://github.com/ruiduobao/solar-energy-potential},
  version = {0.1.0},
  year    = {2024},
}
```

## 故障排除

| 错误 | 原因 | 解决方案 |
|------|------|---------|
| `ConnectionError` | 网络问题 | 检查网络，重试 |
| `HTTP 429` | 速率限制 | 等待 60 秒后重试 |
| `ValueError` | 坐标无效 | 检查纬度 (-90 到 90)，经度 (-180 到 180) |
| 无输出 | 该位置无数据 | 尝试附近坐标 |
| `ModuleNotFoundError` | 缺少依赖 | 运行 pip install |
| `HTTP 500/503` | NASA 服务器问题 | 稍后重试 |
| GHI 不现实 | 海洋/海岸网格单元 | 移入内陆或检查网格分辨率 |

## 数据来源

NASA POWER (Prediction Of Worldwide Energy Resources) API。
