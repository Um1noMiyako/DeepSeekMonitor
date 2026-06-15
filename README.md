# DeepSeek Monitor 🔍

一个用 Python 写的小工具，能在系统托盘里看 DeepSeek 账户余额还剩多少钱。

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square)
![PySide6](https://img.shields.io/badge/PySide6-6.5%2B-green?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-lightgrey?style=flat-square)

---

## 这是干啥的？

就是**看看余额**。

把 DeepSeek 的 API Key 填进去，它就会定时去调 DeepSeek 官方的 `/user/balance` 接口，把余额数字显示出来。

> v1.0.0 就这点功能，没别的了。

---

## 截图

（TODO：还没放截图，因为我不会搞）

反正就是一个**托盘图标**，左键弹出小窗显示余额，右键有菜单可以刷新和退出。还有一个主窗口，分了三个标签页：

- **概览** — 显示余额数字和大头状态
- **历史** — 显示之前抓到的余额记录
- **设置** — 填 API Key 的地方

---

## 功能列表

- [x] 系统托盘常驻，开机不弹大窗口烦人
- [x] 定时自动刷新余额（默认 10 分钟一次）
- [x] 余额变动记录到 SQLite 数据库
- [x] 可以手动点刷新按钮
- [x] 玻璃拟态 UI（抄的网上的样式，自己调了调）
- [x] API Key 加密存本地

### 已知不足（就是还没做）

- [ ] **没有通知提醒** — 余额低了也不会弹窗告诉你
- [ ] **没有图表** — 历史记录就是列表，没有折线图
- [ ] **没有导出 Excel** — 只能导出 JSON
- [ ] **没有多账户支持** — 只能看一个 API Key
- [ ] **没有自动更新** — 有新版本不会自己提醒你
- [ ] **没有打包成真正意义的安装包** — 用 PyInstaller 打的 exe 有点粗糙

---

## 安装使用

### 方法一：直接跑源码

```bash
# 1. 克隆（或者下载 ZIP）
git clone https://github.com/Um1noMiyako/DeepSeekMonitor.git
cd DeepSeekMonitor

# 2. 装依赖
pip install -r requirements.txt

# 3. 运行
python main.py
```

### 方法二：用打包好的 exe

去 Releases 里下载 `DeepSeekMonitor.exe`，双击就能跑。

> 杀软可能会报毒，因为 PyInstaller 打包的 exe 都这样，不信你可以自己打包试试。

---

## 怎么配置

1. 打开程序，右键托盘图标 → **打开详情**
2. 切到 **设置** 标签页
3. 把你的 DeepSeek API Key 填进去
4. 点保存

然后就自动开始刷新了。

---

## 技术栈

| 东西 | 用的啥 |
|------|--------|
| 界面 | PySide6（Qt for Python） |
| 网络请求 | requests |
| 数据库 | SQLite（Python 自带的 sqlite3） |
| 加密 | cryptography |
| 打包 | PyInstaller |

---

## 项目结构

```
DeepSeekMonitor/
├── main.py              # 入口 + 单例保护（防止开两个）
├── app.py               # 应用生命周期管理
├── api.py               # 调 DeepSeek API 的封装
├── worker.py            # 后台定时刷新线程
├── storage.py           # 数据存取（SQLite + config.json）
├── main_window.py       # 主窗口 UI
├── popup.py             # 托盘弹出小窗
├── tray.py              # 系统托盘管理
├── settings_page.py     # 设置页面
├── theme.py             # 样式表（玻璃拟态）
├── crypto.py            # API Key 加密/解密
├── config.json          # 本地配置文件
├── requirements.txt     # Python 依赖
└── DeepSeekMonitor.spec # PyInstaller 打包配置
```

---

## 碎碎念

这是我第一次正经用 PySide6 写桌面程序，边查文档边写的，代码写得可能不太优雅，凑合着看吧。

如果有啥问题或者建议……嗯，可以提 Issue，但我也不一定会改（开玩笑的，我看到会回的）。

---

## License

MIT

---

*写于 2026 年 6 月 · 一个想监控自己 DeepSeek 余额花没花完的下午*
