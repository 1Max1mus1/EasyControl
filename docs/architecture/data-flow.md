@wiki id=easycontrol-data-flow type=module domain=projects state=draft
@summary EasyControl 在已配对且人为解锁的会话中传输最新画面、远程输入和文本剪贴板，并持续输出网络与会话诊断。
@terms EasyControl, data flow, 远程会话, 输入延迟
@links easycontrol-architecture, easycontrol-prd

# Data Flow

## Inputs

被控端屏幕与系统会话、控制端鼠标键盘与纯文本、设备配对状态、本地解锁结果和网络路径状态。

## Transformations

1. 验证配对设备，并在主动访问时验证 EasyControl 本地解锁密码。
2. 被控端采集并编码当前画面，根据带宽与处理能力调整质量，只优先发送最新画面。
3. 加密传输画面、输入和纯文本剪贴板。
4. 被控端在正确 Windows 会话和安全桌面中执行输入，断线释放状态。
5. 同会话短暂断网自动恢复；主动访问、程序重启或锁定后重新验证本人。
6. 持续记录 RTT、路径、帧率、端到端延迟和重连原因。

## Outputs

控制端可见且可操作的远程画面、纯文本剪贴板、会话锁定状态和诊断信息。秘密、Windows 凭据和不必要的隐私内容不得进入日志。
