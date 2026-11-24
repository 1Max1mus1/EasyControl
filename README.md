# EasyControl

EasyControl 是为用户自己的手提电脑远程控制一台固定 Windows 台式电脑设计的工具，主要面向编程和普通办公，优先低延迟、高稳定、无人值守和每次主动访问的人为解锁。

**当前状态：第一阶段技术验证已启动。** 仓库内已有代码只是一次性验证材料，不是可安全交付的远程控制产品。

## 项目文档

- [项目概览](PROJECT.md)
- [产品需求与验收标准](docs/prd.md)
- [技术验证计划](docs/validation.md)
- [开发路线](docs/roadmap.md)
- [低成本网络方案调研](docs/research/network-options.md)
- [当前进展](docs/progress/current.md)
- [统一领域语言](CONTEXT.md)

网络方案不预设品牌：先测现有 Tailscale 的直连/中继和物理线路，再决定是否比较 ZeroTier、NetBird 或 VPS。技术验证通过后，才进入双端界面、托盘、自启动和安装包的完整落地阶段。
