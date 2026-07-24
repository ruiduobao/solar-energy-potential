# solar-energy-potential

Calculate solar PV energy potential from NASA POWER solar radiation data.

## Features

- Annual GHI from NASA POWER
- Optimal tilt angle estimation
- PV output estimation (kWh/kWp/year)
- Economic analysis (payback, LCOE)
- Single point + batch processing

## Installation

### Option 1: ClawHub
```bash
clawhub install solar-energy-potential
```

### Option 2: Manual
```bash
git clone https://github.com/ruiduobao/solar-energy-potential.git
cd solar-energy-potential
pip install -r requirements.txt
```

### Option 3: Claude Code / skills.sh
```bash
claude skills install solar-energy-potential
```

## Quick Start

```bash
python scripts/solar-energy-potential.py assess \
  --lat 39.9 --lon 116.4 -o solar.json

python scripts/solar-energy-potential.py batch \
  -i locations.csv --lat-col lat --lon-col lon -o batch.json

python scripts/solar-energy-potential.py economic \
  --lat 39.9 --lon 116.4 --capacity 5.0 --cost-per-kwp 800
```

## Dependencies

```
requests>=2.28.0
numpy>=1.21.0
```

## Data Source

NASA POWER API. Data © NASA (Public Domain).

## License

MIT-0 (Public Domain)

---

# 中文说明

使用 NASA POWER 太阳辐射数据评估太阳能光伏潜力。

## 功能

- 年 GHI 获取
- 最佳倾角估算
- 发电量估算
- 经济分析（回收期、LCOE）
- 单点 + 批量处理

## 安装

### 方式一：ClawHub
```bash
clawhub install solar-energy-potential
```

### 方式二：手动安装
```bash
git clone https://github.com/ruiduobao/solar-energy-potential.git
cd solar-energy-potential
pip install -r requirements.txt
```

### 方式三：Claude Code / skills.sh
```bash
claude skills install solar-energy-potential
```

## 快速开始

```bash
python scripts/solar-energy-potential.py assess \
  --lat 39.9 --lon 116.4 -o solar.json

python scripts/solar-energy-potential.py batch \
  -i locations.csv --lat-col lat --lon-col lon -o batch.json

python scripts/solar-energy-potential.py economic \
  --lat 39.9 --lon 116.4 --capacity 5.0 --cost-per-kwp 800
```

## 数据来源

NASA POWER API. 数据 © NASA (Public Domain)。

## 许可证

MIT-0 (Public Domain)
