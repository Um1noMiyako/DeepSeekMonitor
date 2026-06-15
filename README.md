# DeepSeek Monitor

一个系统托盘常驻的 DeepSeek 余额监控工具。通过 DeepSeek 官方 API 定时拉取账户余额，在托盘图标和弹窗中展示。

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square)
![PySide6](https://img.shields.io/badge/PySide6-6.5%2B-green?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-lightgrey?style=flat-square)

---

## 功能

- 系统托盘常驻运行
- 定时自动刷新余额（默认间隔 10 分钟）
- 余额变动记录到本地 SQLite 数据库
- 支持手动刷新
- 玻璃拟态 UI
- API Key 本地加密存储

### v1.0.0 局限

- 无余额变动通知提醒
- 历史记录仅表格展示，无图表
- 仅支持单 API Key
- 无自动更新机制
- 无打包分发版本（仅源码运行）

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

## 使用方式

1. 运行程序后，右键系统托盘图标 → **打开详情**
2. 切换到 **设置** 标签页
3. 填入 DeepSeek API Key 并保存
4. 程序自动开始定时刷新余额

托盘图标左键弹出余额小窗，双击打开完整窗口。

---

## 项目结构

```
DeepSeekMonitor/
├── main.py            # 入口 + 单例保护
├── app.py             # 应用生命周期管理
├── api.py             # DeepSeek API 封装
├── worker.py          # 后台定时刷新线程
├── storage.py         # SQLite 数据存取 + config.json 读写
├── main_window.py     # 主窗口（概览/历史/设置 Tab）
├── popup.py           # 托盘弹出小窗
├── tray.py            # 系统托盘管理
├── settings_page.py   # 设置页面 UI
├── theme.py           # QSS 样式表
├── crypto.py          # API Key 加解密
├── config.json        # 本地配置
└── requirements.txt   # Python 依赖
```

---

## 技术栈

| 模块 | 选型 |
|------|------|
| 桌面框架 | PySide6 (Qt for Python) |
| HTTP 请求 | requests |
| 本地存储 | SQLite + JSON |
| 加密 | cryptography |

---

## License

MIT
