---
name: solar-energy-potential
description: 'Calculate solar PV energy potential from NASA POWER solar radiation data. Computes annual GHI, optimal tilt angle, estimated PV output, and economic analysis.'
---

# Solar Energy Potential

Assess solar photovoltaic (PV) energy potential using NASA POWER solar radiation data. Computes annual GHI, optimal tilt, estimated PV output, and economic metrics.

## Features

- **Annual GHI**: Global Horizontal Irradiance from NASA POWER
- **Optimal tilt angle**: Based on latitude
- **PV output estimation**: kWh/kWp/year
- **Economic analysis**: Simple payback, LCOE estimate
- **Single point + batch**: CSV input for multiple locations
- **No API key required**: NASA POWER is free and open

## Key Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| System efficiency | PV panel efficiency (%) | 18% |
| Performance ratio | System losses factor | 0.80 |
| Installed capacity | kWp per assessment | 1.0 |
| Electricity price | $/kWh for economic analysis | 0.10 |
| System cost | $/kWp installed | 1000 |

## Usage

### Assess a single location
```bash
python scripts\solar-energy-potential.py assess \
  --lat 39.9 --lon 116.4 \
  --output solar_assessment.json
```

### Batch process from CSV
```bash
python scripts\solar-energy-potential.py batch \
  --input locations.csv --lat-col lat --lon-col lon \
  --output solar_batch.json
```

### Economic analysis
```bash
python scripts\solar-energy-potential.py economic \
  --lat 39.9 --lon 116.4 \
  --capacity 5.0 --cost-per-kwp 800 --electricity-price 0.12 \
  --output economic.json
```

## Installation

```bash
pip install requests>=2.28.0 numpy>=1.21.0
# Or: pip install -r scripts/requirements.txt
```

## Parameters

- `--lat`: Latitude (-90 to 90)
- `--lon`: Longitude (-180 to 180)
- `--input`: Input CSV file for batch mode
- `--lat-col`: Latitude column name in CSV
- `--lon-col`: Longitude column name in CSV
- `--output`: Output JSON file
- `--efficiency`: PV panel efficiency (0.15-0.25, default: 0.18)
- `--performance-ratio`: Performance ratio (0.70-0.90, default: 0.80)
- `--capacity`: Installed capacity in kWp (default: 1.0)
- `--cost-per-kwp`: System cost per kWp in USD (default: 1000)
- `--electricity-price`: Electricity price in USD/kWh (default: 0.10)
- `--year`: Year for NASA POWER data (default: 2023)
- `--json`: Output as JSON

## Output

- **Annual GHI**: kWh/m²/year
- **Optimal tilt**: degrees
- **Annual PV output**: kWh/kWp/year
- **Capacity factor**: %
- **Economic metrics**: Payback period, LCOE, annual savings

## Optimal Tilt Angle Formula

The optimal tilt angle for fixed-mount PV systems is estimated as:

```
tilt ≈ latitude × 0.87
```

For more precise estimation, the tool uses the PVWatts method:

| Mount Type | Tilt Formula |
|------------|-------------|
| Fixed | `latitude × 0.87` |
| Seasonal adjust | `latitude − 15°` (summer), `latitude + 15°` (winter) |
| Tracking | 0° (horizontal axis), latitude (tilted axis) |

**Note**: This is a simplified estimate. Actual optimal tilt depends on local climate, albedo, and shading.

## LCOE Formula Documentation

Levelized Cost of Energy is calculated as:

```
LCOE = (CAPEX × CRF + O&M) / Annual_energy
```

Where:

| Variable | Description | Default |
|----------|-------------|---------|
| CAPEX | Initial investment ($/kWp) | 1000 |
| CRF | Capital recovery factor = r(1+r)ⁿ / ((1+r)ⁿ − 1) | r=0.06, n=25 |
| O&M | Annual O&M cost ($/kWp/year) | 20 |
| Annual_energy | kWh/kWp/year from PV output | computed |

Use `--discount-rate` and `--system-lifetime` to adjust CRF parameters.

## Temporal Resolution

NASA POWER data supports three temporal resolutions:

| Resolution | Parameter | Use Case |
|------------|-----------|----------|
| Daily | `daily` | Detailed analysis, day-to-day variation |
| Monthly | `monthly` | Seasonal patterns, resource mapping |
| Climatology | `climatology` | Long-term average, feasibility studies |

Specify with `--temporal-resolution monthly`. Default is `daily`.

## CSV Output Format

In addition to JSON, output results as CSV:

```bash
python scripts\solar-energy-potential.py assess \
  --lat 39.9 --lon 116.4 \
  --output solar_assessment.csv --format csv
```

Batch mode outputs CSV by default (one row per location).

## API Error Handling and Retry Logic

The tool handles NASA POWER API errors:

| Error | Cause | Tool Behavior |
|-------|-------|---------------|
| HTTP 500 | Server error | Waits 30s, retries up to 3 times |
| HTTP 503 | Service unavailable | Waits 60s, retries |
| Timeout | Slow response | Increases timeout, retries |
| No data | Invalid coordinates | Reports error, suggests valid range |

Use `--max-retries 5` and `--retry-delay 120` to customize.

## Known Limitations

This tool provides estimates only. Known limitations include:

- **No shading analysis**: Does not account for terrain or building shadows
- **No soiling losses**: Does not model dust/pollution on panels
- **No terrain effects**: Assumes flat surface; no slope/aspect correction
- **Simplified PV model**: Uses performance ratio; does not model inverter efficiency curves
- **NASA POWER resolution**: ~0.5°×0.5° grid; local microclimate not captured
- **Economic assumptions**: Simple LCOE; does not model degradation, financing, incentives

For detailed system design, use PVsyst, SAM, or HOMER.

## Batch Output Format

Batch mode produces structured output:

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

CSV output has one row per location with all metrics as columns.

## Visualization

- **GHI map**: Interpolate point results to create spatial raster (use QGIS or Python `scipy.interpolate`)
- **Bar chart**: Compare PV output across locations
- **Monthly profile**: Plot monthly GHI to show seasonal variation
- **Economic scatter**: LCOE vs GHI for site comparison

```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('solar_batch.csv')
plt.scatter(df['ghi'], df['pv_output'], c=df['latitude'], cmap='coolwarm')
plt.colorbar(label='Latitude')
plt.xlabel('Annual GHI (kWh/m²/year)')
plt.ylabel('PV Output (kWh/kWp/year)')
plt.show()
```

## Citation

Please cite NASA POWER data:

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

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| `ConnectionError` | Network issue | Check internet, retry |
| `HTTP 429` | Rate limit | Wait 60s, retry |
| `ValueError` | Invalid coordinates | Check lat (-90 to 90), lon (-180 to 180) |
| Empty output | No data for location | Try nearby coordinates |
| `ModuleNotFoundError` | Missing dep | Run pip install |
| `HTTP 500/503` | NASA server issue | Wait and retry later |
| Unrealistic GHI | Ocean/coastland grid cell | Move point inland or check grid resolution |

## API Information

- **Endpoint**: `https://power.larc.nasa.gov/api/temporal/daily/point`
- **No API key required**
- **Data**: NASA POWER Project (SSE-R6)
- **License**: Public Domain

## Dependencies

```
requests>=2.28.0
numpy>=1.21.0
```

## Data Source

NASA POWER (Prediction Of Worldwide Energy Resources) API.

---

## Advanced Usage

### Batch Assessment from CSV
```bash
python scripts\solar-energy-potential.py assess   --input locations.csv --output solar_assessment.json
```

### CI/CD Integration (GitHub Actions)
```yaml
# .github/workflows/solar-assessment.yml
name: Solar Potential Update
on:
  schedule:
    - cron: '0 0 1 1 *'  # Yearly
jobs:
  assess:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install requests
      - run: |
          python scripts\solar-energy-potential.py assess \
            --input data/solar_sites.csv \
            --output data/solar_latest.json
```

### PostgreSQL Import
```bash
python scripts\solar-energy-potential.py assess   --input sites.csv --output solar.json

# Parse JSON and import
python -c "
import json, csv
data = json.load(open('solar.json'))
with open('solar.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=data[0].keys())
    w.writeheader(); w.writerows(data)
"
psql -d gis_db -c "\COPY solar_assessment FROM 'solar.csv' CSV HEADER"
```

### Performance Tips
- Use `--temporal climatology` for feasibility studies (fastest, pre-computed)
- Add `sleep 1` between batch locations to avoid rate limits
- `--json` output is machine-readable; use `--csv` for direct spreadsheet import

---

## 中文说明

使用 NASA POWER 太阳辐射数据评估太阳能光伏潜力。计算年 GHI、最佳倾角、预估发电量及经济分析。

## 功能特性

- **年 GHI**：全球水平辐照度
- **最佳倾角**：基于纬度计算
- **发电量估算**：kWh/kWp/年
- **经济分析**：简单回收期、LCOE 估算
- **单点 + 批量**：CSV 输入多地点
- **无需 API 密钥**：NASA POWER 免费开放

## 关键参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| 系统效率 | 光伏板效率 (%) | 18% |
| 性能比 | 系统损耗因子 | 0.80 |
| 装机容量 | kWp | 1.0 |
| 电价 | $/kWh | 0.10 |
| 系统成本 | $/kWp | 1000 |

## 使用示例

### 单点评估
```bash
python scripts\solar-energy-potential.py assess \
  --lat 39.9 --lon 116.4 \
  --output solar_assessment.json
```
