@wiki id=easycontrol-overview type=project-overview domain=projects state=draft
@summary EasyControl 是为自有手提电脑远程控制香港台式电脑设计的低延迟 Windows 工具，目前已进入第一阶段技术验证。
@terms EasyControl, 远程控制, 低延迟, 无人值守
@links easycontrol-prd, easycontrol-validation-plan, easycontrol-roadmap, easycontrol-current-progress

# EasyControl

## Purpose

让用户用自己的手提电脑在香港、深圳或广州稳定控制香港住处的一台台式电脑，主要满足编程和普通桌面办公，而不是游戏或高帧率视频。

## Scope

首版只服务这一组固定 Windows 设备，包含远程画面、输入、无人值守、设备配对、每次主动访问解锁和纯文本剪贴板。网络方案根据实测选择，不预设 Tailscale 或其他品牌。完整范围见 [PRD](docs/prd.md)。

## Run

当前没有经完整验收的产品运行路径。仓库内已有代码仅为一次性技术验证材料，不得视为可安全使用的远程控制服务。后续技术验证必须记录网络环境、测量方法和原始结果。

## Key entry points

- [产品需求与验收标准](docs/prd.md)
- [技术验证计划与阶段门槛](docs/validation.md)
- [后续开发路线](docs/roadmap.md)
- [低成本网络方案调研](docs/research/network-options.md)
- [架构约束与候选边界](docs/architecture/overview.md)
- [当前进展与证据](docs/progress/current.md)

## Current state

立项需求和网络资料调研已完成。用户已授权启动第一阶段编程落地，与暂停的 Intranet 热点测试并行；先验证输入链路、网络路径和采集编码，不直接跳到完整产品外壳。
