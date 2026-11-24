@wiki id=easycontrol-architecture type=module domain=projects state=draft
@summary EasyControl 当前只定义采集编码、输入、会话安全、系统权限和网络诊断边界，编码与网络实现由技术验证选择。
@terms EasyControl, architecture, 无人值守, 会话安全
@links easycontrol-prd, easycontrol-validation-plan

# Architecture Overview

本页记录逻辑边界，不代表已选定采集、编码、网络库或旧代码结构。

## Modules

- **画面采集与编码**：在真实硬件上比较候选，优先文字清晰和最新画面。
- **输入与剪贴板**：执行鼠标、键盘和纯文本同步，断线释放输入状态。
- **会话与解锁**：设备配对、人为解锁、同会话重连、主动与空闲锁定。
- **Windows 系统接入**：服务、用户会话、锁屏、登录界面和常规 UAC。
- **网络路径与诊断**：直连/中继选择、加密、RTT、丢包和重连状态。
- **产品外壳（第二阶段）**：双端界面、托盘、自启动、安装与卸载。

## Interfaces

第一阶段以可测行为定义边界：输入画面与操作，输出端到端延迟、带宽、系统权限结果和故障证据。内部协议和模块接口等 V0–V4 后确定。

## Invariants

- 设备配对不能替代主动访问的人为解锁。
- 自动重连只在同一已解锁会话内免密，不得扩大为永久免密。
- 不保存 Windows 账户密码，不开放无认证或仅简单密码的公网控制路径。
- 带宽不足时丢弃过期画面，不能无限积压。
- 断线不能留下持续按下的鼠标或键盘状态。

## Failure modes

物理线路高延迟、长期中继、UDP 被封、GPU 不可用、会话切换、安全桌面、Wi-Fi 切换、睡眠重启、八小时资源增长和输入队列积压必须显式验证。
