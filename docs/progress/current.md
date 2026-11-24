@wiki id=easycontrol-current-progress type=progress domain=projects state=draft
@summary EasyControl 已由用户授权启动第一阶段编程落地，新 session 先修复输入链路并建立网络与延迟基线，不直接进入产品外壳。
@terms EasyControl, progress, 新 session, 技术验证
@links easycontrol-overview, easycontrol-validation-plan

# Current Progress

## Now

需求、PRD、验证计划、路线图和网络调研已完成。用户已明确授权开始 EasyControl 编程落地，与暂停中的 Intranet 热点测试并行。当前只进入第一阶段技术验证，不批准直接跳到托盘、安装包或完整产品外壳。

## Next

新 session 从两个最小风险点开始：

1. 复现并修复隔离窗口中的键盘输入链路，要求 ControlClient → TCP → HostServer → Windows SendInput 端到端通过，而不是仅导入或本机直接调用成功。
2. 按 V0 记录当前 Tailscale direct/DERP、RTT、丢包和 RDP 对照，随后测量真实屏幕采集编码的端到端延迟。

每个增量先写验收指标、运行真实调用、保存证据，再决定是否扩展。不要同时启动 Windows 服务、UAC、自启动和安装包。

## Risks

已有输入代码的直接 SendInput 测试失败，不能作为可靠实现复用。早期密码和画面回环测试不等于双机或安全验收。无人值守涉及 Windows 服务与安全桌面；Tailscale 可能经 DERP，性能必须实测。

## Evidence

[网络方案调研](../research/network-options.md) 已附官方来源。早期一次性材料完成过密码认证、真实屏幕 JPEG 传输、解码、统计和动态设置测试；随后鼠标/键盘端到端测试只输入部分字符，直接 SendInput 测试也未能输入文字，因此键盘输入明确未通过。没有双机、跨城市、登录界面、UAC、八小时或安全验收证据。
