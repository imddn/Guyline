# Guyline 架构

[English](ARCHITECTURE.en.md) · [返回首页](../README.md)

本文按「解决的问题 → 实现方式 → 设计取舍 → 源码与测试入口」说明 Guyline 的主要
组成部分。描述以当前 `main` 分支代码为准：命令、路径和行为都可以在对应源码中核对。

- [1. 执行循环](#1-执行循环)
- [2. 多 Agent 与后台任务](#2-多-agent-与后台任务)
- [3. 上下文、压缩与记忆](#3-上下文压缩与记忆)
- [4. 权限与沙箱](#4-权限与沙箱)
- [5. 扩展机制与模型适配](#5-扩展机制与模型适配)
- [6. 入口与渠道](#6-入口与渠道)
- [附录 A：路径、环境变量与优先级](#附录-a路径环境变量与优先级)
- [附录 B：其他安装方式](#附录-b其他安装方式)
- [附录 C：数据与迁移规则](#附录-c数据与迁移规则)
- [附录 D：第三方来源](#附录-d第三方来源)

## 1. 执行循环

**解决的问题。** 模型本身只会返回文本或工具调用请求；要完成真实任务，必须有东西
负责把工具结果送回模型、控制轮数与成本，并在出错时给出明确边界。

**实现方式。** `QueryEngine`（`src/guyline/engine/query_engine.py`）持有会话历史、
当前模型、system prompt、工具注册表、权限检查器、hook 执行器和用量统计。真正的循环
在 `src/guyline/engine/query.py`：

1. 把会话消息与工具 schema 发给模型适配层，流式接收文本增量；
2. 若模型返回工具调用，先经过权限检查与 hook 检查，再执行工具；
3. 工具结果被规范化为 `ToolResultBlock` 追加回会话（工具自身的返回值仍是 `ToolResult`）；
4. 再次请求模型，重复上述过程。

停止条件写在同一层：模型不再请求工具、达到 `max_turns`（超出时抛
`MaxTurnsExceeded`）、出现未处理错误，或命中上下文/输出长度边界。长度边界不是直接
失败：命中 prompt-too-long 时（`_is_prompt_too_long_error`）先尝试一次反应式压缩
（reactive compaction），只有压缩成功后该回合才重试；命中 completion-token 上限
（`_is_completion_token_limit_error`）且模型报出更低上限时，才下调
`effective_max_tokens` 后重试。

界面通过事件流消费过程，而不是直接调用工具：`src/guyline/engine/stream_events.py`
定义 `AssistantTextDelta`、`ToolExecutionStarted`、`ToolExecutionCompleted`、
`ErrorEvent`、`StatusEvent`、`CompactProgressEvent`。`QueryEngine` 另外保留
`has_pending_continuation()` 与 `continue_pending()`，用于在中断或压缩后继续未完成的
回合。

**设计取舍。**

- 循环与 UI 解耦，多入口（CLI、`-p`、React 终端、Gateway）复用同一套循环，
  避免每个界面各写一份行为不一致的 agent loop。
- 每轮都把工具结果写回上下文，会持续增加上下文负担，因此必须与第 3 节的压缩配合。
- 工具执行结果统一成结构化对象，便于被压缩、被记忆提取和被测。

**源码与测试入口。** [`src/guyline/engine/query.py`](../src/guyline/engine/query.py)、
[`query_engine.py`](../src/guyline/engine/query_engine.py)、
[`stream_events.py`](../src/guyline/engine/stream_events.py)、
[`cost_tracker.py`](../src/guyline/engine/cost_tracker.py)；
回归测试见 [`tests/test_engine/`](../tests/test_engine/)。

## 2. 多 Agent 与后台任务

**解决的问题。** 复杂任务可以被拆成并行的探索或实现分支；同时长任务不能阻塞主会话，
需要创建、查看、写入输出和停止的办法。

**实现方式。** 多 Agent 位于 `src/guyline/swarm/`：

- `registry.py` 的 `BackendRegistry` 可用于注册/检测多种后端：in-process、子进程，
  以及需要 tmux / iTerm2 的 pane 后端，检测不到时提供
  `mark_in_process_fallback()`。**注册了某种后端不等于默认都使用**：内置 `agent`
  工具（`src/guyline/tools/agent_tool.py`）对所有接受的 mode 都显式调用
  `registry.get_executor("subprocess")`，以便派生的 teammate 能被
  `BackgroundTaskManager` 轮询；in-process、pane 与 fallback 后端由各自的调用路径
  单独使用，而不是由 `agent` 工具按环境自动选择。
- `in_process.py` 把 teammate 作为当前进程内的 asyncio Task 运行，用 `contextvars`
  隔离每个 teammate 的身份与统计（`TeammateContext`、`TeammateAbortController`）。
- `subprocess_backend.py` 通过 CLI 派生 teammate 进程，并继承必要的参数与环境变量。
- `team_lifecycle.py` 把团队持久化为 `~/.guyline/teams/<name>/team.json`，管理成员、
  允许路径、成员模式与退出清理。
- `mailbox.py` 为每个 agent 维护一个 inbox 目录，消息是独立 JSON 文件，写入使用临时
  文件加 `os.replace` 的原子替换；权限请求/响应也走同一通道
  （`create_permission_request_message`、`create_sandbox_permission_request_message`）。

后台任务由 `src/guyline/tasks/manager.py` 的 `BackgroundTaskManager` 提供：
`create_shell_task`、`create_agent_task`、`read_task_output`、`write_to_task`、
`stop_task`，并带完成监听回调，让主会话可以继续交互。

**设计取舍。**

- 用本地文件系统做协调与持久化：团队与 mailbox 的持久化元数据可观测、重启后可恢复，
  但不保证恢复正在执行的 teammate 进程，也不提供分布式语义，跨机器协作不在当前范围内。
- in-process 后端成本最低、调试方便，但共享进程资源；需要更强隔离或独立生命周期时
  才值得付出子进程或 pane 的开销。

**源码与测试入口。** [`src/guyline/swarm/`](../src/guyline/swarm/)、
[`src/guyline/tasks/`](../src/guyline/tasks/)；
回归测试见 [`tests/test_swarm/`](../tests/test_swarm/)、
[`tests/test_tasks/`](../tests/test_tasks/)。

## 3. 上下文、压缩与记忆

**解决的问题。** 长任务会耗尽上下文窗口，而会话结束后的信息也需要在后续会话中可用。

**实现方式。** 压缩集中在 `src/guyline/services/compact/`：

- **microcompact**：清理较早的工具结果内容，成本低，不调用模型；
- **full compact**：调用模型生成结构化摘要；
- **auto-compact**：token 估算超过阈值时自动触发；
- 压缩边界会保持 `tool_use` / `tool_result` 配对
  （`_split_preserving_tool_pairs`），避免生成非法消息序列；附件形式的历史信息通过
  `render_compact_attachment` 回填。

Token 数量来自 `src/guyline/services/token_estimation.py` 的粗略字符启发式估算，
不是精确分词器结果。

记忆分成两类：

- **会话记忆**（`src/guyline/services/session_memory/`）按会话写入数据目录，为压缩后的
  连续性服务；
- **持久记忆**（`src/guyline/memory/`）落在数据根的 `memory/<项目名>-<hash>/`，
  以 `MEMORY.md` 为入口，条目带 frontmatter。`services/memory_extract/` 从完成的回合
  中抽取可长期保留的记忆条目，`services/autodream/` 在后台做整理，并提供备份、diff
  与回滚。

**设计取舍。**

- 估算与 LLM 摘要都是有损的：压缩后不保证保留每个细节，因此关键约束需要写进持久
  记忆或由用户重申。
- microcompact 便宜但只能减少工具输出；真正的语义压缩必须调用模型，存在额外成本与
  延迟，因此自动压缩路径按 token 阈值触发，此外还有手动压缩，以及命中长度边界时
  的反应式压缩路径。

**源码与测试入口。** [`src/guyline/services/compact/`](../src/guyline/services/compact/)、
[`services/session_memory/`](../src/guyline/services/session_memory/)、
[`services/memory_extract/`](../src/guyline/services/memory_extract/)、
[`services/autodream/`](../src/guyline/services/autodream/)、
[`src/guyline/memory/`](../src/guyline/memory/)；
回归测试见 [`tests/test_services/`](../tests/test_services/)、
[`tests/test_memory/`](../tests/test_memory/)。

## 4. 权限与沙箱

**解决的问题。** 让模型在真实文件系统上工作时，需要可解释的判定层；而更高强度的
隔离属于另一类能力，不能混为一谈。

**实现方式。** 权限层在 `src/guyline/permissions/`：

- `modes.py` 定义 `default`、`plan`、`full_auto` 三种模式；
- `checker.py` 的 `PermissionChecker.evaluate` 按路径规则（`PathRule`）、命令提示和
  当前模式给出决定；应用凭据路径一律拒绝读取（`_is_application_credential_path`）；
- 预工具 hook 也可以阻断执行，并在拦截后让模型改换工具。

沙箱与权限分开：`src/guyline/sandbox/adapter.py` 包装外部 `srt`
（sandbox-runtime）命令行，用 `SandboxAvailability` 报告是否启用、是否可用以及原因；
`sandbox/docker_backend.py` 提供 Docker 后端，`path_validator.py` 负责路径校验。
两个后端在已启用、运行时不可用且未要求失败时都允许无沙箱执行，但表现不同：`srt`
路径由 `wrap_command_for_sandbox` 直接返回原命令（不告警）；Docker 路径由
`start_docker_sandbox` 记录 warning 后不建立会话。只有
`sandbox.fail_if_unavailable` 为真时才抛 `SandboxUnavailableError`。

**启用与边界。** 沙箱默认关闭（`sandbox.enabled=False`）；是否启用、以及不可用时是否
硬失败，分别由 `sandbox.enabled` 与 `sandbox.fail_if_unavailable` 控制，也可用
`GUYLINE_SANDBOX_ENABLED`、`GUYLINE_SANDBOX_FAIL_IF_UNAVAILABLE` 覆盖。沙箱需要额外
的外部运行时，平台可用性取决于实际运行环境（本仓库 CI 仅在已配置的平台上执行沙箱
相关测试）。

**设计取舍。**

- 权限规则是应用层判定，**不等于系统隔离**：它约束 Guyline 自身发起的行为，真正的
  进程/文件隔离由外部沙箱运行时提供。
- 默认模式偏向可解释与可审查；完全放开需要显式选择 `full_auto` 或
  `--dangerously-skip-permissions`，并且只应在受控环境下使用。

**源码与测试入口。** [`src/guyline/permissions/`](../src/guyline/permissions/)、
[`src/guyline/sandbox/`](../src/guyline/sandbox/)；
回归测试见 [`tests/test_permissions/`](../tests/test_permissions/)、
[`tests/test_sandbox/`](../tests/test_sandbox/)。

## 5. 扩展机制与模型适配

**解决的问题。** 运行时能力需要在不改核心循环的前提下扩展；模型供应商的差异需要被
收敛到一层适配。

**实现方式。**

- **Skills**（`src/guyline/skills/loader.py`）：从内置、用户、兼容与项目目录发现
  skill，包括项目内 `.guyline/skills`、`.agents/skills` 与 `.claude/skills`。
- **Hooks**（[`src/guyline/hooks/`](../src/guyline/hooks/)）：从 settings 加载定义，
  按事件触发；运行时在 `src/guyline/ui/runtime.py` 中通过 `HookReloader` 接入热
  重载，并非所有入口都会自动监听配置变化。
- **Plugins**（`src/guyline/plugins/`）：发现与导入插件，含安装器与内置插件。
- **MCP**（`src/guyline/mcp/`）：连接 stdio 或 HTTP 的 MCP server，并暴露其工具。
- **模型适配**（`src/guyline/api/`）：`registry.py` 中的 `PROVIDERS` 是 provider 元数据
  的单一来源，`backend_type` 区分 `anthropic`、`openai_compat`、`copilot`；
  `client.py`、`openai_client.py`、`copilot_client.py`、`codex_client.py` 提供具体实现。
- **Provider 档案**（`src/guyline/config/settings.py`）：`ProviderProfile` 描述
  provider、模型与 `api_format`；`api/provider.py` 负责探测与认证状态展示。CLI 另有
  `--api-format`、`--base-url`、`--api-key` 与 `guyline provider` / `guyline auth`
  命令族。

**设计取舍。**

- 单一 registry 让「新增一个 provider」只改一处，代价是配置组合变多，运行前需要
  校验；`--dry-run` 正是为此提供的预览手段。
- **注册了 provider 规格不等于每家都做过端到端验证**：本仓库的自动化测试不会对每个
  供应商发起真实调用，真实调用属于 opt-in（见
  [CONTRIBUTING 的真实 API 与平台限制](../CONTRIBUTING.md#real-api-and-platform-limits)）。

**源码与测试入口。** [`src/guyline/skills/`](../src/guyline/skills/)、
[`hooks/`](../src/guyline/hooks/)、[`plugins/`](../src/guyline/plugins/)、
[`mcp/`](../src/guyline/mcp/)、[`api/`](../src/guyline/api/)；
回归测试见 [`tests/test_skills/`](../tests/test_skills/)、
[`tests/test_hooks/`](../tests/test_hooks/)、
[`tests/test_plugins/`](../tests/test_plugins/)、
[`tests/test_mcp/`](../tests/test_mcp/)、
[`tests/test_api/`](../tests/test_api/)。

## 6. 入口与渠道

**实现方式。** 所有入口最终都汇聚到第 1 节的循环：

- **编码 CLI**（`src/guyline/cli.py`）：根命令启动交互式编码会话，`-p/--print` 提供
  非交互输出，`--output-format` 支持 `text`、`json`、`stream-json`。
- **React 终端**（`src/guyline/ui/`、`frontend/terminal/`）：可选前端，通过结构化
  协议与 Python 后端通信（`ui/protocol.py`、`ui/backend_host.py`）。
- **个人 Agent 与 Gateway**（`src/guyline/agent/`）：`guyline agent` 运行长期存在的
  个人 Agent；`gateway` 管理其生命周期，`agent/gateway/bridge.py` 把渠道消息接到
  Guyline 运行时。
- **渠道**（`src/guyline/channels/`）：IM 渠道实现与消息总线，派生自 nanobot（见
  附录 D）。
- **用户定时任务**：`guyline cron` 管理用户自己的调度器与作业
  （`src/guyline/services/cron_scheduler.py`），属于产品能力，与仓库维护自动化无关。
- **维护者工具**：`guyline autopilot` 面向仓库维护自动化，默认不参与产品运行；
  autopilot workflow 只在自托管 runner 上手动触发。

**源码与测试入口。** [`src/guyline/cli.py`](../src/guyline/cli.py)、
[`src/guyline/ui/`](../src/guyline/ui/)、[`src/guyline/agent/`](../src/guyline/agent/)、
[`src/guyline/channels/`](../src/guyline/channels/)；
回归测试见 [`tests/test_entrypoints/`](../tests/test_entrypoints/)、
[`tests/test_ui/`](../tests/test_ui/)、[`tests/test_agent/`](../tests/test_agent/)、
[`tests/test_channels/`](../tests/test_channels/)、
[`tests/test_bridge/`](../tests/test_bridge/)。

## 附录 A：路径、环境变量与优先级

| 用途 | 默认位置 | 环境变量 |
| --- | --- | --- |
| 全局配置、skills、plugins | `~/.guyline/` | `GUYLINE_CONFIG_DIR` |
| 数据、会话、编码记忆 | `~/.guyline/data/` | `GUYLINE_DATA_DIR` |
| 日志 | `~/.guyline/logs/` | `GUYLINE_LOGS_DIR` |
| 个人工作区 | `~/.guyline/agent/` | `GUYLINE_AGENT_WORKSPACE` |
| 渠道附件 | `<个人工作区>/attachments/<渠道>/` | `GUYLINE_CHANNEL_MEDIA_DIR/<渠道>/` |

- 数据和日志默认跟随有效配置根目录变化，除非单独覆盖。
- 项目配置与 skills 使用项目内 `.guyline/`；项目 skill 发现还支持 `.agents/skills`
  与 `.claude/skills`；项目 plugins 默认关闭，需要显式启用。
- 编码记忆存放在数据根下 `memory/<项目名>-<hash>/`，个人记忆存放在个人工作区的
  `memory/`。
- 工作区优先级：显式 `--workspace` > `GUYLINE_AGENT_WORKSPACE` > 默认值。Gateway 对
  相对的显式/环境 workspace 路径按请求的 cwd 解析，并在生命周期内固定有效工作区。

## 附录 B：其他安装方式

```bash
# 本地源码或显式 wheel，默认创建 .guyline-venv，只注册 guyline 启动器
bash scripts/install.sh --source "/本地/源码目录"
bash scripts/install.sh --wheel "/本地/guyline-0.2.0-py3-none-any.whl"
bash scripts/install_dev.sh                 # checkout 本地的 editable venv
bash scripts/install_dev.sh --global-venv   # 使用 ~/.guyline-venv

# 直接安装 wheel
uv build --wheel
python -m pip install /path/to/guyline-0.2.0-py3-none-any.whl
```

PowerShell 使用 `-Source` / `-Wheel`。wheel 内含终端源码与 npm lockfile，安装器用
自身解释器发现它们并执行 `npm ci`；缺少 lock 的自定义开发布局回退到 `npm install`。
安装脚本在失败时会以非零状态退出；源码安装不保证回滚已经创建的环境或部分写入。

## 附录 C：数据与迁移规则

- Guyline 自身的路径与配置只使用 `.guyline`、`~/.guyline/` 与 `GUYLINE_*`；不会自动
  复制或读取旧应用目录、旧环境变量名，也不会自动迁移旧命名。
- 除自身配置外，Guyline 会读取 provider 相关的既有环境变量（如 `ANTHROPIC_*`、
  `OPENAI_*`），并按第 5 节从项目内 `.agents/skills`、`.claude/skills` 等目录发现
  skills。
- 记忆文件本身有 schema 迁移入口：`src/guyline/memory/migrate.py` 把 schema-v1 的
  frontmatter 迁移到当前格式，支持 dry-run 并在写入前备份。

## 附录 D：第三方来源

- 渠道组件派生自 [nanobot-ai/nanobot](https://github.com/nanobot-ai/nanobot)（MIT）。
  来源记录见 `src/guyline/channels/UPSTREAM`，许可证文本见
  `src/guyline/channels/LICENSE.nanobot`。
- 项目本体以 MIT 许可证发布（`LICENSE`，版权归 imddn）。
