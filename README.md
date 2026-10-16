# personal-memory

**给 Codex 一份你能查看、修改和带走的个人档案，让新聊天少一点重复介绍。**

保存你的背景、偏好和目标，在需要时调用相关内容。配套本地管理页面，方便审核、纠错和删除记录，也可以生成上下文卡片，复制给其他 AI。

[English](README.en.md) · 中文

Python 3.10+ · 零第三方运行依赖 · 无遥测 · [MIT](LICENSE) · v0.2

![本地管理页面，使用虚构演示资料](docs/preview.jpg)

[快速开始](#快速开始) · [使用示例](#使用示例) · [隐私与数据](#隐私与数据) · [反馈问题](https://github.com/13125846766/personal-memory/issues)

## 可以用它做什么

| 场景 | 用法 |
| --- | --- |
| 开新聊天时少介绍一遍自己 | 按需读取已保存的教育背景、表达偏好或近期目标 |
| 检查 AI 记住了什么 | 在本地页面搜索、筛选、编辑记录，查看来源和修正历史 |
| 分开管理工作和个人资料 | 用 personal、work 等档案分别保存和检索 |
| 换一个 AI 继续讨论 | 生成一段可复制的上下文卡片，选择要带走的主题 |
| 修正或撤回资料 | 修改过时内容，或删除记录及其在数据库中的修正历史 |

导入的资料会先进入待确认收件箱。临时目标可以设置有效期；生成上下文卡片时，默认排除敏感、待确认和过期记录。

档案保存在本机。**调用云端模型时，选入上下文的资料仍可能随请求发送。** 完整说明见[隐私与数据](#隐私与数据)。

## 快速开始

需要 Python 3.10+；使用 skill 需要支持本地 skill 和脚本执行的 Codex 环境。macOS/Linux 通常将下面命令中的 `python` 换成 `python3`。

### 1. 下载并安装

```sh
git clone https://github.com/13125846766/personal-memory.git
cd personal-memory
python install.py
```

没有 Git，也可以[下载 ZIP](https://github.com/13125846766/personal-memory/archive/refs/heads/main.zip)，解压后在项目目录运行 `python install.py`。

默认安装到 `~/.agents/skills/personal-memory/`。安装器只复制 skill 文件，不读取或复制私人档案。如果 skill 未显示，重新打开聊天或重启客户端后检查 skill 列表。[Codex 本地 skill 目录说明](https://learn.chatgpt.com/docs/build-skills)

### 2. 在 Codex 中保存第一条偏好

选择 Personal Memory skill，或输入：

```text
$personal-memory 初始化我的本地档案。
```

接着保存一条你希望后续聊天参考的偏好，例如：

```text
$personal-memory 记住我的表达偏好：先给结论，再解释细节。
```

新建聊天后，明确调用相关内容：

```text
$personal-memory 读取我的表达偏好，按这个偏好回答接下来的问题。
```

### 3. 打开本地管理页面

在下载的项目目录运行：

```sh
python skills/personal-memory/scripts/memory.py serve --open
```

Windows 也可双击 `Launch.cmd`。浏览器中可以查看和修改记录；终端显示本机地址，按 `Ctrl+C` 停止服务。管理页面无需项目账号，也可以在不安装 skill 的情况下单独体验。

想先看示例，可以在页面中导入 [examples/import.example.json](examples/import.example.json)。文件只包含虚构资料，导入后需要审核。

## 使用示例

在 Codex 中输入以下指令，按自己的情况修改内容：

```text
$personal-memory 记住：我的学校和专业是……
$personal-memory 结合我的教育背景制定学习计划。
$personal-memory 把我指定的旧聊天整理进记忆，区分自述和推测。
$personal-memory 列出保存了哪些个人资料及其来源。
$personal-memory 忘掉我上一段情感经历的记录。
$personal-memory 打开本地记忆管理页面。
$personal-memory 为另一个 AI 生成只包含教育背景的上下文卡片。
$personal-memory 检查我的临时目标是否已经过期。
```

默认不会静默积累新资料。你可以明确设置范围有限的持续保存偏好，之后在该范围内无需重复确认。自动选择 skill 依赖宿主，显式调用更可靠。普通网页聊天不能直接访问这台电脑的档案。

## 功能与当前限制

- 页面支持关键词搜索、主题与状态筛选、编辑、修正历史和删除；敏感记录默认隐藏。
- 归一化后相同的内容会跳过；同一主题下相同 `key` 的当前值冲突时，进入待确认。字段冲突检查需要填写相同的 `key`，尚未实现语义识别。
- 关键词搜索使用本地文字匹配，不依赖远程嵌入服务或 API。
- 没有后台采集、自动同步或扫描全部聊天的功能。
- 本版本不直接解析任意 ChatGPT 或其他平台的原始聊天导出。可先让 skill 整理你授权的聊天，再导入结构化候选记录。

### 导入、导出与上下文卡片

| 操作 | 行为 |
| --- | --- |
| 导入 JSON | 记录保留来源，全部新记录进入待确认 |
| 导出 JSON | 下载当前档案的全部当前记录，包含隐藏的敏感记录、过期及待确认记录，不包含修正历史 |
| 还原导入 | 分配新 ID，重新审核 |
| 生成上下文卡片 | 读取当前筛选条件，只包含已确认且未过期的记录；敏感内容需要明确启用 |

导出是明文备份，请保存在私人目录；下载位置由浏览器设置决定。上下文卡片默认最多 3000 字符，字符数不是 token 数。超过预算时会保留完整条目，并报告省略数量。

完整命令和数据格式见 [commands.md](skills/personal-memory/references/commands.md)。

## 隐私与数据

### 私人档案存在哪里

优先使用环境变量 `PERSONAL_MEMORY_DIR` 指定的目录，否则为：

| 系统 | 默认目录 |
| --- | --- |
| Windows | `%LOCALAPPDATA%/CodexPersonalMemory/` |
| Linux/macOS | `${XDG_DATA_HOME:-~/.local/share}/codex-personal-memory/` |

档案存于 `memory.sqlite3`。该目录必须位于 skill、开源包和 Git 仓库之外，数据库不会写入下载的项目目录。安装或升级不会覆盖私人资料。

不同档案共用本机数据库，用于区分检索范围，不提供不同用户之间的权限隔离。

### 使用前需要了解

**本地保存不等于本地推理。** 使用云端模型时，读入上下文的资料会随模型请求被处理，聊天及工具输出也可能包含它。本项目不能保证资料不离开电脑、零服务端留存或不被用于训练。要求资料始终不出设备时，需要本地模型和经过验证的离线执行环境。

档案是明文 SQLite，没有实现加密或独立访问控制。skill 规则不能阻止有文件权限的其他程序读取资料。请选择非云盘同步目录，按需使用操作系统权限、磁盘加密和备份。

管理页面仅监听 `127.0.0.1`，停止后不再运行；页面不请求外部资源。API 使用每次启动生成的令牌和来源检查，这些机制不防御拥有本机文件权限的程序。

删除记录时会一并删除它在数据库中的修正历史，但不会同时删除旧聊天、工具日志、系统备份或内置 Memories。性格记录需要保留来源和不确定性，不能将短期情绪或模型推测固化为事实。

### 和内置 Memories 的关系

Codex 有独立的本地 Memories，启用后可从符合条件的聊天在后台生成记忆。本 skill 提供可直接维护、按主题调用的个人档案，不修改内置记忆，也不承诺完整保留所有历史。[官方 Memories 说明](https://learn.chatgpt.com/docs/customization/memories)

## 升级与自定义安装

下载更新后的代码，在项目目录运行：

```sh
python install.py --upgrade
```

升级只更新 skill 文件，不读取或复制私人资料。使用自定义 skill 目录（如宿主配置的 `$CODEX_HOME/skills/`）时，用 `--target` 指定完整目标目录；请以宿主实际配置为准：

```sh
python install.py --target "/full/path/to/skills/personal-memory"
```

不要同时安装同名 skill 的重复副本。v0.1 的 Markdown 档案不会被静默导入或删除；`doctor` 会提示发现的旧文件，可在你授权后整理迁移，空索引无需迁移。

<details>
<summary>手工复制安装（Windows PowerShell）</summary>

在项目目录运行：

```powershell
$skillParent = Join-Path $env:USERPROFILE '.agents/skills'
$skillTarget = Join-Path $skillParent 'personal-memory'
if (Test-Path -LiteralPath $skillTarget) { throw '目标已存在，请先检查，避免覆盖。' }
New-Item -ItemType Directory -Path $skillParent -Force | Out-Null
Copy-Item -LiteralPath './skills/personal-memory' -Destination $skillTarget -Recurse
```

</details>

## 反馈与贡献

遇到安装、调用或页面问题，请[提交 Issue](https://github.com/13125846766/personal-memory/issues)，注明系统、Python 版本、复现步骤和报错。请用虚构数据复现，勿上传真实档案、聊天记录或含私人资料的截图。

本地验证：

```sh
python -m unittest discover -s tests -v
```

测试使用隔离的虚构数据，覆盖跨档案访问、去重、导入事务、过期与敏感过滤、字段冲突、并发纠错、删除历史、HTTP 来源与令牌检查、安装升级。

公开仓库只分发通用规则、代码、文档、测试和虚构示例。真实资料保存在外部私人目录，不作为示例、截图、测试或 Issue 附件。发布前检查要提交的文件和历史；`.gitignore` 无法清除已跟踪或提交的资料。

## 许可证

[MIT](LICENSE) 许可适用于本仓库规则和代码，不授予任何人的私人资料使用权。
