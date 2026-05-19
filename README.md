# SillyTavern Relay2 Discord

通过 Discord 斜杠命令远程操控 [SillyTavern](https://github.com/SillyTavern/SillyTavern) ，支持消息发送、截图回传、角色/聊天/用户设定管理等功能。

## 功能

| 命令 | 说明 |
|------|------|
| `/st <消息>` | 发送消息到酒馆，等待 AI 回复并返回截图 |
| `/stop` | 中止当前正在生成的 AI 回复 |
| `/lastmsg` | 截取酒馆最后一条消息 |
| `/ss` | 全页截取酒馆当前界面 |
| `/rf` | 刷新酒馆页面并截图 |
| `/del <N>` | 删除当前聊天最后 N 条消息（1 或 2） |
| `/left` | 切换到上一个备选回复（左翻页） |
| `/right` | 切换到下一个备选回复（右翻页，可能触发生成） |
| `/regenerate` | 重新生成 AI 回复 |
| `/chat [序号]` | 查看最近聊天列表，或切换到指定聊天 |
| `/char [序号]` | 查看角色卡列表，或选择角色查看其聊天记录 |
| `/user [序号]` | 查看用户设定列表，或选择指定用户设定 |
| `/admin` | 切换管理员模式（仅 L1 管理员） |
| `/admin_add <用户>` | 添加用户到白名单（仅 L1 管理员） |
| `/admin_del <用户>` | 从白名单移除用户（仅 L1 管理员） |

## 环境要求

- Python 3.10+
- SillyTavern 服务运行在可访问的地址
- Playwright 浏览器

## 安装与配置

```bash
# 克隆项目
git clone <repo-url>
cd Sillytavern-Relay2-Discord

# 安装依赖
pip install -r requirements.txt

# 安装 Playwright 浏览器
playwright install chromium

# 创建配置文件
cp config.ini.example config.ini
```

编辑 `config.ini`：

```ini
[discord]
bot_token = 你的Discord机器人Token
admins = 你的Discord用户ID
admin_mode = false

[headless]
st_url = http://127.0.0.1:8000
headless = true
viewport_width = 600

[timing]
refresh_delay = 3
chat_switch_delay = 2
```

## 启动

```bash
python main.py
```

## 项目结构

```
Sillytavern-Relay2-Discord/
├── main.py              # Discord Bot 入口
├── config.ini            # 配置文件（不提交）
├── config.ini.example    # 配置示例
├── admin.py              # 管理员/白名单系统
├── core/                 # SillyTavern 无头浏览器交互核心
│   ├── config.py         # 配置读取
│   ├── browser.py        # Playwright 浏览器管理
│   ├── api.py            # ST API 调用（角色/聊天/用户设定）
│   ├── interaction.py    # 消息注入/等待回复/翻页
│   └── screenshot.py     # 截图
├── cogs/
│   ├── st_commands.py    # 核心交互命令
│   └── admin_commands.py # 管理命令
└── screenshot/           # 截图输出目录
```

## 权限系统

- **L1 管理员**：在 `config.ini` 的 `admins` 字段配置，可切换管理员模式和增删白名单
- **L2 白名单**：管理员模式下，只有白名单用户可使用机器人命令；关闭后所有人可用
- 白名单数据存储在 `admin_whitelist.json`
