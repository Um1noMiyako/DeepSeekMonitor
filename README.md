# DeepSeek Monitor

一个系统托盘常驻的 DeepSeek 余额监控工具。通过 DeepSeek 官方 API 定时拉取账户余额，在托盘图标和弹窗中展示。

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square)
![PySide6](https://img.shields.io/badge/PySide6-6.5%2B-green?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-lightgrey?style=flat-square)

---

## 功能

- 系统托盘常驻运行
- 定时自动刷新余额（间隔 5 / 10 / 15 / 30 / 60 分钟可选）
- 余额变动记录到本地 SQLite 数据库，支持历史导出
- **多 API Key 预设管理** — 存储多个命名 Key，设置页或托盘菜单一键切换
- **多来源 Key 解析** — 自动按优先级读取 Key：
  1. 激活的预设（SQLite）
  2. 单 Key 模式（`config.json`）
  3. 本地纯文本文件（`api_key.txt`）
  4. 环境变量文件（`.env` 中的 `DEEPSEEK_API_KEY`）
  5. 系统环境变量（`DEEPSEEK_API_KEY`）
- 皓白流光玻璃拟态 UI
- 启动自动载入上次使用的预设
- API Key 本地加密存储
- PyInstaller 打包为独立 exe

---

## 使用方式

1. 运行程序后，右键系统托盘图标 → **打开详情**
2. 切换到 **设置** 标签页
3. 在「API Key 预设管理」中新建预设（名称 + Key），点击「应用此预设」
4. 程序自动开始定时刷新余额，重启后自动载入上次预设

托盘图标左键弹出余额小窗，双击打开完整窗口。
右键菜单中可直接切换已保存的预设，无需打开设置页。

---

## 快速开始

```bash
git clone https://github.com/Um1noMiyako/DeepSeekMonitor.git
cd DeepSeekMonitor
pip install -r requirements.txt
python main.py
```

依赖：Python 3.10+，PySide6、requests、cryptography。

---

## 项目结构

```
DeepSeekMonitor/
├── main.py            # 入口 + 单例保护
├── app.py             # 应用生命周期管理
├── api.py             # DeepSeek API 封装
├── worker.py          # 后台定时刷新线程
├── storage.py         # SQLite / config / 文件 / 环境变量多来源读写
├── main_window.py     # 主窗口（概览 / 历史 / 设置 Tab）
├── popup.py           # 托盘弹出小窗
├── tray.py            # 系统托盘 + 预设切换子菜单
├── settings_page.py   # 设置页（单 Key + 预设管理 + 刷新间隔 + 导出）
├── theme.py           # 皓白流光 QSS 样式表
├── crypto.py          # API Key 加解密
├── build.bat          # PyInstaller 打包脚本
├── resources/         # 图标资源
└── requirements.txt   # Python 依赖
```

本地运行时会自动生成以下目录（已由 `.gitignore` 忽略，不会上传仓库）：

```
data/          # SQLite 数据库（余额快照 + 预设）
history/       # 30 天以上数据的 JSON 归档
config.json    # 单 Key 模式配置
dist/          # PyInstaller 打包产物
```

---

## 技术栈

| 模块 | 选型 |
|------|------|
| 桌面框架 | PySide6 (Qt for Python) |
| HTTP 请求 | requests |
| 本地存储 | SQLite + JSON |
| 加密 | cryptography |
| 打包 | PyInstaller (onefile) |

---

## v1.0.0 局限

- 无余额变动通知提醒
- 历史记录仅表格展示，无图表
- 无自动更新机制
- Key 明文存储于 SQLite / config.json（与运行环境同级别安全）

---

## License

MIT
