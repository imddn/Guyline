# Guyline 0.2.0

Guyline 是本地编码和个人 Agent 工具，包含工具调用、skills、记忆、权限、
后台任务和聊天 Gateway。完整开发说明见 [README](README.md)，
安全策略见 [SECURITY.md](SECURITY.md)，示例见 [docs/SHOWCASE.md](docs/SHOWCASE.md)。

## 安装

需要 Python 3.10+。React 终端还需要 Node.js 18+ 和 npm。
从 [imddn/Guyline](https://github.com/imddn/Guyline) 克隆后安装，
不依赖产品已发布到 PyPI。私有仓库需要先完成 GitHub 认证。

```bash
git clone https://github.com/imddn/Guyline.git
cd Guyline
uv sync --extra dev
cd frontend/terminal
npm ci
cd ../..
uv run guyline
```

也可在虚拟环境内执行 `python -m pip install -e .`。
三个安装入口使用本地源码或显式 wheel，创建 `.guyline-venv`，
仅注册 `guyline` 启动器，并通过安装后的解释器验证模块和前端资源。

```bash
bash scripts/install.sh --source "/本地/源码目录"
bash scripts/install_dev.sh --global-venv
uv build --wheel
bash scripts/install.sh --wheel "/本地/guyline-0.2.0-py3-none-any.whl"
```

PowerShell 使用 `-Source "C:\本地源码"` 或
`-Wheel "C:\本地\guyline-0.2.0-py3-none-any.whl"`。
省略路径时安装脚本所在的仓库；找不到仓库时明确报错。
直接安装 wheel 也可使用 `python -m pip install /path/to/local.whl`。
wheel 带有 npm lock，安装器和首次启动使用 `npm ci`；
自定义开发布局缺少 lock 时回退到 `npm install`。

## 首次运行

先确认安装，并在没有任何 provider 凭据时预览解析后的运行配置：

```bash
uv run guyline --version
uv run guyline --dry-run -p "/help"   # 解析配置/skills/命令/工具；不调用模型
```

`--dry-run` 只打印 Guyline 将使用的配置，不会调用模型或执行工具，因此在配置
provider 之前即可运行。要真正获得回答，需先配置一个 provider，再发送提示：

```bash
uv run guyline setup          # 交互式：选择工作流、完成认证、选择模型
uv run guyline provider list  # 列出已配置的 provider 档案
uv run guyline auth status    # 查看当前认证来源
uv run guyline -p "Explain this repository"   # 需要已配置的 provider
```

`guyline -p` 会调用已配置的模型，可能产生 provider 费用；未配置 provider 时
无法回答。建议使用交互式 `guyline setup` 或 `guyline auth login`，让凭据在
提示符中输入，而不是写进 shell 历史或提交到仓库。不要把真实 token 写入脚本、
issue 或示例，示例一律使用占位符。

React 终端为可选能力：仅安装 Python 时可用 CLI、`-p`、`python -m guyline`
和 `gateway`；安装 `frontend/terminal` 才会加入 React TUI。

## 命令

```bash
guyline
guyline setup
guyline provider list
guyline auth status
guyline -p "Explain this repository"
guyline --dry-run -p "/help"
guyline -p "Summarize this repository" --output-format json
guyline agent init
guyline agent config
guyline agent
guyline gateway run
guyline gateway start
guyline gateway status
guyline gateway restart
guyline gateway stop
```

`python -m guyline` 使用相同命令树。根命令启动编码 CLI，
`agent` 启动个人 Agent，`gateway` 管理 Gateway 生命周期。
只有 `guyline` console script；原有命令别名不再安装。

## 路径和配置

| 用途 | 默认位置 | 环境变量 |
| --- | --- | --- |
| 全局配置、skills、plugins | `~/.guyline/` | `GUYLINE_CONFIG_DIR` |
| 数据、会话、编码记忆 | `~/.guyline/data/` | `GUYLINE_DATA_DIR` |
| 日志 | `~/.guyline/logs/` | `GUYLINE_LOGS_DIR` |
| 个人工作区 | `~/.guyline/agent/` | `GUYLINE_AGENT_WORKSPACE` |
| 渠道附件 | `<个人工作区>/attachments/<渠道>/` | `GUYLINE_CHANNEL_MEDIA_DIR` |

数据和日志默认随有效配置根目录变化。项目配置和 skills 使用项目内
`.guyline/`，还支持 `.agents/skills` 和 `.claude/skills`；
项目 plugins 默认关闭，需要显式启用。编码记忆存入数据根下
`memory/<项目>-<hash>`，个人记忆存入个人工作区的 `memory/`。

显式 `--workspace` 优先于 `GUYLINE_AGENT_WORKSPACE`，最后使用默认值。
Gateway 相对 workspace 根据请求的 cwd 解析，并固定有效工作区。

第三方接口变量 `CODEX_HOME`、`ANTHROPIC_API_KEY`、`OPENAI_API_KEY`
维持原义。Windows 原生路径与安装回归由 CI 的 Python 3.10/3.11 运行；
Linux 模拟不能代替 Windows 执行。

真实 API 测试默认跳过、需显式启用：设置 `GUYLINE_RUN_REAL_API=1`、非空
`ANTHROPIC_API_KEY`，以及 `GUYLINE_REAL_WORKSPACE`（本地代码目录）后才会运行。
默认 `pytest` 不会访问模型。

## 已知限制

- 不存在无需凭据的模型路径：真实提示必须有一个配置了有效凭据的 provider。
- 真实 API 与 Docker 沙箱测试需要额外的本地前提，不属于默认离线测试。
- Autopilot workflow 运行在自托管 runner 上且仅手动触发，应视为受信维护者的
  特权自动化，详见 [SECURITY.md](SECURITY.md)。
- 平台支持以实际运行的 CI 矩阵为准；Windows 原生文件存储行为仅由 Windows CI
  job 覆盖。
