@wiki id=easycontrol-new-session-phase-1 type=runbook domain=projects state=draft
@summary EasyControl 新 session 的第一阶段编程落地指令，包含仓库、边界、既有证据、首批任务和验收要求。
@terms EasyControl, 新 session, 技术验证, SendInput, Tailscale
@links easycontrol-overview, easycontrol-validation-plan, easycontrol-current-progress

# EasyControl 新 Session 启动 Prompt

将以下代码块作为新 session 的任务说明：

```text
你正在开始 EasyControl 的第一阶段编程落地。请先阅读项目文档再修改代码，不要把已有原型当作已验收产品。

一、项目与环境

项目：EasyControl
GitHub：https://github.com/1Max1mus1/EasyControl.git
主分支：main
当前本机路径：C:\Users\Victo\Desktop\Project\EasyControl
Wiki：https://github.com/1Max1mus1/Victor-llm-wiki.git
Wiki 本机路径：C:\Users\Victo\Desktop\Project\Victor-llm-wiki

目标环境：两台个人 Windows 电脑。被控端通常在香港，控制端在香港/深圳/广州。
首版用于编程和普通桌面办公，不以游戏、高帧率视频或 4K 60 FPS 为目标。
本机已有 Python 3.13、Tkinter、Pillow；requirements.txt 当前为 Pillow>=10,<12。

先执行：
git status --short --branch
git log -1 --format="%H%n%ci%n%s"

并阅读：
- AGENTS.md
- PROJECT.md
- CONTEXT.md
- docs/INDEX.md
- docs/prd.md
- docs/validation.md
- docs/roadmap.md
- docs/progress/current.md
- docs/research/network-options.md
- docs/architecture/overview.md

二、当前阶段与边界

当前只做第一阶段技术验证：
- 修复可靠的鼠标键盘输入链路。
- 建立 Tailscale/物理线路/RDP 的故障分层与延迟基线。
- 验证真实屏幕采集、编码、传输和输入到画面反馈的延迟。
- 使用隔离测试窗口和合成数据，不接触真实密码或私人文件。

暂时不要做：
- 不直接开发完整托盘、安装包、自启动或产品主界面。
- 不开放公网端口，不配置端口映射。
- 不启用无人值守 Windows 服务，不处理真实 UAC，除非用户另行明确授权。
- 不把本机回环结果称为双机、跨城市或八小时验收。
- 不为了保留旧代码而迁就架构；可复用必须通过实测的部分。
- 不自行 commit 或 push，除非用户明确要求。

三、已知证据与问题

早期原型曾通过：
- 密码挑战认证。
- 本机真实屏幕 JPEG 采集、传输、解码。
- 帧率、码率、RTT 统计和动态画质设置。

早期输入验证失败：
- 端到端测试只输入了部分字符。
- 直接 SendInput 测试也未能向隔离 Tk 输入框写入文字。
因此键盘输入明确未通过，不能声称已有可靠远程控制。

已有网络调研在 docs/research/network-options.md：
- 先用 tailscale status、tailscale ping、tailscale netcheck 区分 direct、relay 和物理线路。
- 不预设 Tailscale、ZeroTier、NetBird 或 VPS 谁更快。
- 之前 CUHK1x 下 Tailscale 仅见 DERP(sin)，约 89–94 ms；该结果有时效性，必须重新测量。

四、第一批落地任务

任务 A：建立可重复的输入诊断闭环

1. 阅读 diagnosing-bugs 技能并按其诊断循环执行。
2. 创建隔离 Tk 测试窗口和输入框，只使用合成文本。
3. 分别验证：
   a. WindowsInput 直接注入。
   b. ControlClient → TCP → HostServer → SendInput 的完整链路。
4. 记录窗口焦点、SendInput 返回值、实际虚拟键、按下/释放顺序和断线状态。
5. 找出根因后做最小修复，再验证连续字符、退格、回车、方向键、鼠标移动和点击。
6. 测试结束释放全部按键并恢复鼠标位置，不影响用户其他窗口。

通过条件：
- 连续输入 abc、两次退格、一次回车和方向键均正确。
- 完整 TCP 链路通过，不只是直接调用。
- 不出现卡键、断线后仍按下或误操作用户窗口。
- 保存可重复运行的验证命令和原始输出。

任务 B：建立网络与延迟基线

1. 在不修改网络设置的情况下记录：
   tailscale status
   tailscale netcheck
   tailscale ping <被控端TailscaleIP>
2. 区分 direct、DERP/peer-relay、RTT、丢包和抖动。
3. 不把 RDP 卡顿直接归因于 Tailscale；需要 TCP 和画面对照。
4. 只有在本机网络允许时才启动回环测量；跨机测试由用户协调。

任务 C：在输入修复后测量真实画面闭环

1. 使用真实屏幕和办公场景，记录采集、编码、网络、解码各段耗时。
2. 测量输入到画面反馈的端到端 P50/P95，而不只测 FPS。
3. 网络 RTT ≤30 ms 且稳定时，目标 P95 ≤100 ms。
4. 画质以文字清楚为准，网络不足时降低质量，不积压旧帧。
5. 如果未达门槛，先报告数据和瓶颈，不直接扩大功能。

五、工程要求

- 遵守 AGENTS.md：架构变化同步更新 PROJECT.md、CONTEXT.md、docs/INDEX.md 和相关架构/进度文档。
- 新验证代码放在明确的技术验证位置，不伪装成完整产品入口。
- 不创建无关文档或测试脚手架；已有验证需求允许的测试应可重复运行。
- 不做静默依赖升级；需要新依赖时说明理由并确认项目惯例。
- 每次修改后运行覆盖该修改的真实验证，不只 compile/import。
- 保留失败证据，不删除或美化未通过结果。
- 不收集 Windows 密码、配对秘密或真实个人内容。
- 完成后报告：修改文件、根因、真实验证结果、未通过项、下一最小风险。

先完成任务 A 的最小复现与修复，再决定是否进入任务 B/C。不要一次实现全部 V0–V4。
```
