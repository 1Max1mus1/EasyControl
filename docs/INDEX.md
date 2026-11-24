@index scope=projects generated=true

## Knowledge

@ref id=easycontrol-architecture type=module state=draft path=architecture/overview.md
  EasyControl 当前只定义采集编码、输入、会话安全、系统权限和网络诊断边界，编码与网络实现由技术验证选择。

@ref id=easycontrol-current-progress type=progress state=draft path=progress/current.md
  EasyControl 已由用户授权启动第一阶段编程落地，新 session 先修复输入链路并建立网络与延迟基线，不直接进入产品外壳。

@ref id=easycontrol-data-flow type=module state=draft path=architecture/data-flow.md
  EasyControl 在已配对且人为解锁的会话中传输最新画面、远程输入和文本剪贴板，并持续输出网络与会话诊断。

@ref id=easycontrol-network-options type=module state=draft path=research/network-options.md
  基于官方资料比较 Tailscale、ZeroTier、NetBird 与 VPS 中继，要求先测真实路径再选择低成本网络方案。

@ref id=easycontrol-new-session-phase-1 type=runbook state=draft path=prompts/new-session-phase-1.md
  EasyControl 新 session 的第一阶段编程落地指令，包含仓库、边界、既有证据、首批任务和验收要求。

@ref id=easycontrol-overview type=project-overview state=draft path=../PROJECT.md
  EasyControl 是为自有手提电脑远程控制香港台式电脑设计的低延迟 Windows 工具，目前已进入第一阶段技术验证。

@ref id=easycontrol-prd type=module state=draft path=prd.md
  EasyControl 首版服务一组个人 Windows 设备，强调办公低延迟、八小时稳定、完整无人值守和每次主动访问的人为解锁。

@ref id=easycontrol-roadmap type=runbook state=draft path=roadmap.md
  EasyControl 在 Intranet 后推进，先验证网络、编码与无人值守，再落地双端产品并完成跨地点七日试用。

@ref id=easycontrol-validation-plan type=runbook state=draft path=validation.md
  EasyControl 第一阶段先定位网络路径，再验证采集编码、无人值守权限和稳定性，未达到预设门槛不进入产品开发。
