# DeepSeek Monitor — 设计规格说明书

**版本：** v1.0.0  
**日期：** 2026-06-15  
**状态：** 设计完成，待用户审查

---

## 1. 项目概述

一个 Windows 桌面应用，常驻系统托盘，点击弹出余额预览浮窗，右键菜单打开完整窗口。调用 DeepSeek 官方 API (`GET /user/balance`) 获取账户余额数据，每 10 分钟自动刷新，支持手动刷新。

**核心理念：** 不爬虫、不依赖网页登陆态，只使用官方公开 API，简洁稳定。

---

## 2. 技术栈

| 项 | 选型 | 理由 |
|:--|:--|:--|
| 语言 | Python 3.11+ | — |
| GUI 框架 | PySide6 | Qt 官方维护，LGPL，比 PyQt5 更现代 |
| HTTP 客户端 | requests | 简单可靠 |
| 数据库 | SQLite (sqlite3) | 零配置，单文件，Python 内置 |
| 加密 | cryptography.fernet | 对称加密，密钥派生自机器指纹 |
| 打包 | PyInstaller | 和 OptiX 同模式 |
| 主题 | 深空玻璃 9 色主题（移植 CSS → QSS） | 和 OptiX/深空玻璃 设计语言一致 |

---

## 3. 项目结构

```
D:\Projects\DeepSeekMonitor\
├── main.py              入口，单例锁，启动 App
├── app.py               QApplication + 生命周期管理
├── tray.py              QSystemTrayIcon（图标、菜单、左键/右键行为）
├── popup.py             Frameless 预览浮窗（从托盘弹出）
├── main_window.py       QMainWindow 完整大窗口（概览/历史/设置三 Tab）
├── settings_page.py     设置页（API Key 修改）
├── api.py               DeepSeek API 调用（GET /user/balance）
├── storage.py           SQLite 读写 + 历史快照 + 过期数据导出
├── crypto.py            cryptography 加解密 API Key
├── worker.py            QThread 后台定时刷新（10 分钟）
├── theme.py             深空玻璃 9 色主题 → PySide6 QSS
├── resources/
│   ├── icon.ico         托盘图标
│   └── icon.png         应用图标
├── build.bat            PyInstaller 打包脚本
├── requirements.txt     依赖列表
├── custom.css           用户主题覆盖（exe 同级，和 OptiX 同模式）
├── data/                运行时自动创建 — SQLite 数据库
└── history/             30 天前历史数据自动导出为 JSON（按月命名）
```

**依赖（requirements.txt）：**
```
PySide6>=6.5.0
requests>=2.28.0
cryptography>=41.0.0
```

---

## 4. 架构图

```
┌─────────────────────────────────────────────────┐
│                    main.py                        │
│         单例锁 → QApplication 启动                │
└──────────┬──────────────────────────────────────┘
           │
    ┌──────▼──────┐     信号槽     ┌─────────────┐
    │   app.py    │◄──────────────►│  worker.py  │
    │  生命周期    │                │  QThread    │
    │  主题管理    │                │  10min 定时  │
    └──┬────┬──┬──┘                └──────┬──────┘
       │    │  │                          │
    ┌──▼┐ ┌▼─┐└─────────────┐     ┌─────▼─────┐
    │   │ │  │               │     │  api.py   │
    │   │ │  │               └────►│  GET      │
    │   │ │  │                     │  /user/   │
    │   │ │  │                     │  balance  │
    │   │ │  │                     └─────┬─────┘
    │   │ │  │                           │
    │   │ │  │                     ┌─────▼─────┐
    │   │ │  └────────────────────►│ storage   │
    │   │ │                        │ SQLite +  │
    │   │ │                        │ history/  │
    │   │ │                        └─────┬─────┘
    │   │ │                              │
    ▼   ▼ ▼                              │
  ┌──────────┐  ┌──────────┐             │
  │  tray.py │  │ popup.py │◄────────────┘
  │  托盘    │  │  浮窗    │
  └────┬─────┘  └──────────┘
       │
       │ 右键菜单
       ▼
  ┌──────────────┐
  │main_window.py│
  │ 完整窗口      │
  │ Tab: 概览    │
  │     历史    │
  │     设置    │
  └──────────────┘
```

---

## 5. 托盘（tray.py）

### 5.1 行为

| 操作 | 响应 |
|:--|:--|
| **左键点击** | 弹出预览浮窗（位置：托盘图标上方对齐） |
| **左键再次点击** | 收起浮窗 |
| **右键** | 弹出菜单：[打开详情] [刷新余额] [退出] |
| **点击浮窗外 | 自动收起 |

### 5.2 右键菜单

```
┌─────────────┐
│ 📊 打开详情  │  → 打开完整窗口
│ 🔄 刷新余额  │  → 手动拉 API 刷新
├─────────────┤
│ 🚪 退出     │  → 确认后退出应用
└─────────────┘
```

---

## 6. 预览浮窗（popup.py）

### 6.1 设计

- **窗口类型：** Frameless QWidget，`WindowStaysOnTopHint` + `ToolTip`
- **尺寸：** 宽 320px，高自适应
- **外观：** 圆角 12px，阴影，玻璃质感背景（QGraphicsBlurEffect 模拟 backdrop-filter）
- **交互：** 失去焦点自动隐藏；鼠标悬浮保持显示

### 6.2 布局

```
┌──────────────────────────────────┐
│  🐋 DeepSeek Monitor    ⟳ ⚙ ✕  │  → 伪标题栏
│                     ●●●●●●●●●    │  → 9 色主题色板
├──────────────────────────────────┤
│                                  │
│     💰 账户余额        ● 可用    │
│        ¥ 927.23                  │  → 大字余额（accent 色）
│                                  │
│  ┌──────────┐ ┌──────────┐      │
│  │ 💰 充值  │ │ 🎁 赠送  │      │  → glass-card
│  │ ¥827.23  │ │ ¥100.00  │      │
│  └──────────┘ └──────────┘      │
│                                  │
│  ┌──────────────────────────┐   │
│  │ 📊 总余额     ¥ 927.23   │   │  → 汇总条
│  └──────────────────────────┘   │
│                                  │
│     最后刷新：06/15 01:35:22      │  → 底部状态
└──────────────────────────────────┘
```

### 6.3 状态指示

| 状态 | 显示 |
|:--|:--|
| 余额 ≥ 0.01 且 is_available=true | 绿色圆点 + "可用" |
| is_available=false | 黄色圆点 + "余额不足" |
| API 请求失败 | 红色圆点 + "连接失败" |
| 无 API Key | 灰色 + "未配置 Key" |

---

## 7. 完整窗口（main_window.py）

### 7.1 布局

```
┌──────────────────────────────────────────┐
│  🐋 DeepSeek Monitor            _ □ ✕   │  → 原生标题栏
│  [概览]  [历史]  [设置]                   │  → QTabWidget
│                        ●●●●●●●●●         │  → 9 色主题色板
├──────────────────────────────────────────┤
│                                          │
│  「概览」 Tab                            │
│  └─ 同浮窗内容 + 更宽松排版              │
│     额外显示：货币类型、API 响应时间      │
│                                          │
│  「历史」 Tab                            │
│  └─ QTableWidget                        │
│     | 时间 | 总余额 | 充值 | 赠金 | 状态 |
│     支持滚动，按时间倒序                  │
│                                          │
│  「设置」 Tab                            │
│  └─ API Key 输入框（密码掩码）+ 保存按钮 │
│     自动刷新间隔选择（5/10/15/30/60分钟） │
│     当前主题名称 + 色板预览              │
│     关于信息 + 版本号                    │
│                                          │
└──────────────────────────────────────────┘
```

### 7.2 概览 Tab

比浮窗额外显示：
- 货币类型（CNY / USD）
- 上次 API 响应时间（ms）
- 手动刷新按钮

### 7.3 历史 Tab

- 最近 30 天快照数据（QTableWidget）
- 列：时间、总余额、充值余额、赠金余额、状态
- 按时间倒序排列
- 底部显示："30 天前数据已自动归档至 history/ 文件夹" + "打开文件夹"按钮

### 7.4 设置 Tab

- **API Key：** QLineEdit（EchoMode=Password）+ "显示/隐藏"切换 + "保存"按钮
- **刷新间隔：** QComboBox（5/10/15/30/60 分钟）
- **当前主题：** 标签显示当前主题名 + 9 色小点（选中高亮）
- **导出数据：** "导出历史数据"按钮 → 保存为 JSON
- **关于：** 版本号 v1.0.0 + "DeepSeek Monitor" + GitHub 链接（如有）

---

## 8. 主题系统（theme.py）

### 8.1 9 色主题

移植深空玻璃设计系统，和 OptiX `theme.py` 同模式（dataclass + CSS 变量映射）。

| # | 主题 | data-theme | 主色 | 风格 |
|:-:|:--|:--|:--|:--|
| 1 | 靛蓝流光 | `indigo` | `#6366F1` | 紫蓝（默认暗色）|
| 2 | 碧翠琉璃 | `emerald` | `#10B981` | 绿 |
| 3 | 赤焰熔金 | `amber` | `#F59E0B` | 金/橙 |
| 4 | 玫瑰星云 | `rose` | `#EC4899` | 粉 |
| 5 | 极光冰晶 | `cyan` | `#06B6D4` | 青 |
| 6 | 紫罗兰夜 | `violet` | `#8B5CF6` | 紫 |
| 7 | 霓虹都市 | `neon` | `#FF0080` | 品红/紫 |
| 8 | 暗灰墨 | `charcoal` | `#8888A0` | 灰 |
| 9 | 皓白流光 | `white` | `#4F46E5` | 亮色 |

### 8.2 实现方式

- `ThemeColors` dataclass 存储完整色值（24 字段，和 OptiX 一致）
- 动态生成 QSS：`THEME_QSS_TEMPLATE` 模板 + `format(**theme.__dict__)`
- 切换主题：`QApplication.instance().setStyleSheet(new_qss)`
- `custom.css` 覆盖机制（exe 同级，`load_css_overrides()` 解析后合并）
- 当前主题名存入 SQLite settings 表，下次启动恢复

### 8.3 玻璃效果

Qt 不原生支持 CSS `backdrop-filter`。用以下方式模拟：
- 半透明背景 `rgba(r,g,b,0.55)` (QSS 直接支持)
- `QGraphicsBlurEffect` 应用到父窗口背景（可选，性能权衡）
- 边框 `1px solid rgba(r,g,b,0.12)`

---

## 9. API 层（api.py）

### 9.1 端点

```
GET https://api.deepseek.com/user/balance
Headers:
  Authorization: Bearer <API_KEY>
  Accept: application/json
```

### 9.2 响应模型

```python
@dataclass
class BalanceInfo:
    currency: str          # "CNY" | "USD"
    total_balance: str     # "110.00"
    granted_balance: str   # "10.00"
    topped_up_balance: str # "100.00"

@dataclass
class Balance:
    is_available: bool
    balance_infos: list[BalanceInfo]
```

### 9.3 错误处理

| 状态码 | 含义 | 用户提示 |
|:--|:--|:--|
| 200 | 成功 | — |
| 401 | Key 无效 | "API Key 无效，请在设置中更新" |
| 429 | 限流 | "请求太频繁，请稍后重试" |
| 5xx | 服务端错误 | "DeepSeek 服务异常，稍后重试" |
| 网络错误 | 超时/DNS | "网络连接失败，检查网络" |

超时：connect 10s，read 15s。

---

## 10. 存储层（storage.py）

### 10.1 表结构

```sql
-- API Key（加密存储）
CREATE TABLE api_keys (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    encrypted_key TEXT NOT NULL,
    created_at  TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- 余额快照
CREATE TABLE balance_snapshots (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    total_balance   REAL NOT NULL,
    granted_balance REAL NOT NULL,
    topped_up_balance REAL NOT NULL,
    is_available    INTEGER NOT NULL DEFAULT 1,
    currency        TEXT NOT NULL DEFAULT 'CNY',
    fetched_at      TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- 应用设置
CREATE TABLE settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
```

### 10.2 数据生命周期

```
写入 → balance_snapshots（SQLite）
  │
  ├─ 30 天内 → 保留在 SQLite，历史 Tab 可查
  │
  └─ 超过 30 天 → 导出到 history/YYYY-MM.json
                  → 从 SQLite 删除
```

**导出格式（history/2026-05.json）：**
```json
[
  {
    "fetched_at": "2026-05-15T01:35:22",
    "total_balance": 927.23,
    "granted_balance": 100.00,
    "topped_up_balance": 827.23,
    "is_available": true,
    "currency": "CNY"
  },
  ...
]
```

### 10.3 清理策略

- 每次插入新快照时触发清理检查
- 执行 `DELETE FROM balance_snapshots WHERE fetched_at < datetime('now', '-30 days')`
- 如果 SQLite 文件超 10MB → 强制清理（VACUUM）

---

## 11. 加密层（crypto.py）

### 11.1 方案

```
API Key (明文)
     │
     ▼ encrypt()
Fernet(derived_key) → encrypted_key (base64)
     │
     ▼ 存入 SQLite api_keys 表
     │
     ▼ decrypt()
Fernet(derived_key) → API Key (明文)
```

### 11.2 密钥派生

```python
import uuid, socket, hashlib, base64
from cryptography.fernet import Fernet

def _derive_key() -> bytes:
    machine_id = uuid.getnode()          # MAC 地址
    hostname = socket.gethostname()
    seed = f"{machine_id}:{hostname}:deepseek-monitor-salt"
    digest = hashlib.sha256(seed.encode()).digest()
    return base64.urlsafe_b64encode(digest)
```

> **注意：** 这是本地模糊处理，不是防专业攻击的安全方案。密钥派生在同一台机器上可重现，换机器需要重新输入 Key。

---

## 12. 后台刷新（worker.py）

### 12.1 定时器

- QThread 封装，避免阻塞主 UI 线程
- 默认每 10 分钟触发一次（可在设置中修改）
- 首次启动立即拉一次
- `api.py` 调用成功后发射 `pyqtSignal(balance: Balance)` → UI 层更新
- 调用失败发射 `pyqtSignal(error_message: str)` → UI 显示错误

### 12.2 刷新策略

| 条件 | 行为 |
|:--|:--|
| 定时器到期（无 Key） | 跳过，不报错 |
| 定时器到期（有 Key） | 拉 API，更新 UI |
| 用户点刷新（无 Key） | 提示 "请先设置 API Key" |
| 用户点刷新（有 Key） | 拉 API，无论是否有定时器 |
| API 请求失败 | 保留上次数据，显示错误提示，3 次连续失败后调低频率至 30 分钟 |

---

## 13. 打包（build.bat）

### 13.1 PyInstaller 命令

```bash
pyinstaller \
  --name "DeepSeekMonitor" \
  --onefile \
  --windowed \
  --icon resources/icon.ico \
  --add-data "resources;resources" \
  --hidden-import PySide6.QtNetwork \
  --hidden-import cryptography.fernet \
  main.py
```

### 13.2 产物

- `dist/DeepSeekMonitor.exe` — 单文件，无控制台窗口
- exe 同级目录自动创建：
  - `data/` → SQLite
  - `history/` → 过期数据 JSON
  - `custom.css`（可选，用户自放）

---

## 14. 错误处理矩阵

| 场景 | 用户可见行为 |
|:--|:--|
| 首次启动，无 Key | 浮窗不显示数据，菜单"刷新"提示设置 Key |
| Key 无效（401） | 浮窗/窗口状态变红，提示 Key 无效 |
| 网络断开 | 显示上次成功数据 + "连接失败"标记 |
| API 限流（429） | 显示提示，自动推迟下次刷新至 15 分钟后 |
| SQLite 损坏 | 重建数据库 + 提示重新设置 Key |
| 单例冲突 | 第二个进程静默退出（不弹窗） |

---

## 15. 单例保护

```python
# main.py
from PySide6.QtNetwork import QLocalSocket, QLocalServer

def is_already_running() -> bool:
    socket = QLocalSocket()
    socket.connectToServer("DeepSeekMonitor")
    if socket.waitForConnected(500):
        socket.close()
        return True
    return False
```

若已运行，静默退出，不弹错误框。

---

## 16. 不做什么（YAGNI）

- ❌ 不爬 platform.deepseek.com 网页
- ❌ 不做分模型 Token 统计（官方 API 不支持）
- ❌ 不做趋势柱状图（无数据源）
- ❌ 不做开机自启（v2 再说）
- ❌ 不做通知推送
- ❌ 不做多语言（只中文）
- ❌ 不做深色/浅色跟随系统自动切换（手动 9 色够用）

---

## 17. 自检清单

- [x] 无 TBD / TODO 占位符
- [x] 架构图和代码结构一致
- [x] 浮窗和完整窗口的职责边界清晰
- [x] 数据流（API → SQLite → UI）完整闭环
- [x] 错误状态覆盖：无 Key / 401 / 429 / 5xx / 网络断 / 单例冲突 / 数据库损坏
- [x] 9 色主题移植方案明确（CSS 变量 → ThemeColors dataclass → QSS 动态生成）
- [x] 历史数据过期导出逻辑定义清晰
- [x] 打包方案完整
