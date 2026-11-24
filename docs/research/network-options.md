@wiki id=easycontrol-network-options type=module domain=projects state=draft
@summary 基于官方资料比较 Tailscale、ZeroTier、NetBird 与 VPS 中继，要求先测真实路径再选择低成本网络方案。
@terms EasyControl, Tailscale, ZeroTier, NetBird, WireGuard, 网络调研
@links easycontrol-validation-plan

# EasyControl 低成本远程网络方案调研

## 核心结论

1. **先测现有 Tailscale，不应先换软件。**
   `tailscale status` 能区分 `direct`、`relay`、`peer-relay`；`tailscale ping` 能显示直连升级、DERP 城市和逐次 RTT；`tailscale netcheck` 能检查 UDP、困难 NAT、端口映射和各 DERP 延迟。当前问题可以先拆成“Tailscale 路径、物理线路、RDP/Windows”三层。[连接类型](https://tailscale.com/kb/1257/connection-types) · [CLI](https://tailscale.com/kb/1080/cli)

2. **若持续 DERP，先修香港被控端 NAT/防火墙，再对比 ZeroTier、NetBird。**
   检查 UDP 是否可用、是否双 NAT/CGNAT、路由器 NAT-PMP/UPnP 或静态 UDP 映射、IPv6 是否可用。Tailscale 明确说明：UDP 被阻止或两端都是 hard NAT 时可能无法直连。[防火墙端口](https://tailscale.com/kb/1082/firewall-ports)

3. **ZeroTier、NetBird 都只能作为同条件 A/B 候选，不能预设谁穿透更好。**
   - ZeroTier 会持续尝试 UDP 打洞，失败时经 root 中继；UDP 不可用还有较慢的 TCP fallback。[协议](https://docs.zerotier.com/protocol/) · [路由器建议](https://docs.zerotier.com/routertips/)
   - NetBird 使用 ICE/STUN 建立 WireGuard P2P，失败后走 UDP/443 QUIC 或 TCP/443 WebSocket 中继。[架构](https://docs.netbird.io/about-netbird/how-netbird-works) · [端口与中继](https://docs.netbird.io/about-netbird/ports-and-firewalls)

4. **若各方案都只能中继，已有 VPS 比继续盲目换 mesh 更有价值。**
   - 保留 Tailscale 时，优先试官方 **Peer Relay**：顺序为 direct → 自有 UDP peer relay → DERP，且 `tailscale status` 可看到实际 relay endpoint。[Peer Relay](https://tailscale.com/kb/1591/peer-relays)
   - 想要最少组件、固定可控路径时，试**纯 WireGuard + VPS**。但裸 WireGuard 没有自动打洞和自动中继选择，VPS 模式下两端流量固定经过 VPS。[Quick Start](https://www.wireguard.com/quickstart/) · [`wg(8)` 源码手册](https://git.zx2c4.com/wireguard-tools/tree/src/man/wg.8)

5. **不建议第一阶段自建 DERP、ZeroTier TCP relay、Headscale 或完整 NetBird。**
   - Tailscale 自定义 DERP 仍标为 alpha，需要公网直连、80/443/3478，官方通常更建议 Peer Relay。[自定义 DERP](https://tailscale.com/kb/1118/custom-derp-servers)
   - ZeroTier 官方把 TCP relay 定位为 UDP 不可用时的最后 fallback。[TCP Relay](https://docs.zerotier.com/relay/)
   - Headscale 是自托管控制面，不等于更优数据路径；其内嵌 DERP 文档还明确说没有速度或吞吐优化。[Headscale 功能](https://headscale.net/stable/about/features/) · [Headscale DERP](https://headscale.net/stable/ref/derp/)

## 费用与可观测性对比

| 方案 | 个人免费/自建成本 | 直连、中继与地域可观测性 | 立项建议 |
|---|---|---|---|
| Tailscale | Personal 非商业免费，最多 6 用户，用户设备不限；Peer Relay 包含在免费功能中。[价格](https://tailscale.com/pricing) | 最强：`status` 显示 direct/relay/peer-relay；`netcheck` 显示 DERP 延迟；实时区域见 [DERP map](https://controlplane.tailscale.com/derpmap/default) | 保留为基线 |
| ZeroTier | Personal 免费，10 用户、10 设备、1 网络。[价格](https://www.zerotier.com/pricing.md) | `zerotier-cli peers` 显示 DIRECT、对端物理 IP；无 path IP 表示中继；`info -j` 查 `tcpFallbackActive`。公共中继没有像 DERP 那样明确的城市代码。[CLI](https://docs.zerotier.com/cli/) | 第二组实测 |
| NetBird Cloud | Free 最多 5 用户、100 机器。[价格](https://netbird.io/pricing) | `netbird status -d` 显示 P2P/Relayed、ICE candidate/endpoints、握手、延迟及动态 relay 域名；官方未提供固定地域承诺。[CLI](https://docs.netbird.io/get-started/cli) | 第二组实测 |
| 纯 WireGuard + VPS | 软件无订阅费；成本为 VPS、公网 IP、流量/出网及维护。已有 VPS 的边际软件成本为零，但要核对流量额度 | 没有自动直连/中继切换；`wg show` 看 endpoint、最近握手和收发量。中继地域就是自己选择的 VPS | 固定中继优先候选 |
| Tailscale Peer Relay | Tailscale 免费功能，另加 VPS 成本 | `peer-relay <ip:port:vni>` 明确可见；失败仍可回退 DERP | 保留 Tailscale 时的自建首选 |
| 完整 NetBird 自托管 | 至少 1 CPU、2 GB Linux VM、公网域名和 443/3478 等要求。[部署要求](https://docs.netbird.io/selfhosted/selfhosted-quickstart) | 自控 relay，但组件和维护明显多于纯 WireGuard/Peer Relay | 两台个人电脑不宜先上 |

## 建议先做的测量

在香港、深圳、广州分别使用**真实会使用的运营商和 Wi-Fi/移动网络**，覆盖晚高峰与非高峰，重复数天。每轮保持相同 RDP 分辨率和工作负载，至少记录 15–30 分钟。

两端先执行：

```powershell
tailscale netcheck
tailscale status
```

RDP 有流量时，在控制端执行：

```powershell
tailscale ping --c 300 --until-direct=false <被控端TailscaleIP>
ping -n 300 <被控端TailscaleIP>
Test-NetConnection <被控端TailscaleIP> -CommonTCPPort RDP
```

`Test-NetConnection` 官方支持 ICMP、TCP 和路由诊断。[Microsoft 文档](https://learn.microsoft.com/en-us/powershell/module/nettcpip/test-netconnection?view=windowsserver2025-ps)

每轮记录：

- `direct / relay / peer-relay` 比例及切换时间；
- DERP 城市代码、两端 `Nearest DERP`；
- RTT 的 p50/p95/p99、丢包、抖动；
- 首次直连耗时、断流和重连次数；
- RDP 卡顿发生的精确时间，与网络样本对齐；
- 实际上下行吞吐，而不只是 ICMP。

需要 TCP/UDP 延迟和带宽测试时，可用微软官方 PsPing；服务端只绑定虚拟网络 IP，测试完关闭。[PsPing](https://learn.microsoft.com/en-us/sysinternals/downloads/psping)

### 如何判定故障层

- **长期 `relay`，且 RTT/卡顿随中继恶化**：优先处理 NAT 或测试自有 relay。
- **已经 `direct`，但 RTT 仍高或丢包**：问题更可能是物理线路、Wi-Fi、运营商绕路；换上层远控软件不能消除这段延迟。
- **Tailscale ping 和普通 ping 稳定，但 3389 TCP 失败**：查 Windows 防火墙、RDP listener、睡眠、认证和系统服务。
- **网络指标稳定但 RDP 画面卡顿**：查 RDP 编码、主机 CPU/GPU 和应用输入排队。微软的 `User Input Delay` 可区分应用处理延迟，但它不是网络 RTT。[RDS 性能计数器](https://learn.microsoft.com/en-us/windows-server/remote/remote-desktop-services/rds-rdsh-performance-counters)
- 微软带宽建议以**丢包低于 0.1%**为前提，1080p、30 fps 的典型建议带宽为 5 Mbps；只能作为测试参考，不能代替真实工作负载。[RDP 网络指导](https://learn.microsoft.com/en-us/windows-server/remote/remote-desktop-services/network-guidance)

## 再如何选方案

1. **Tailscale 已稳定直连**：保留，转查 RDP/Windows，不换网络。
2. **仅部分地点长期 DERP**：先修香港端静态 UDP 映射、双 NAT/CGNAT、IPv6 或防火墙，再复测。
3. **修复后仍中继**：在相同地点、时段分别测 ZeroTier 和 NetBird，按直连比例、p95/p99、丢包和重连选择，而不是按品牌选择。
4. **三者都中继，或直连物理路径仍差**：用已有 VPS 对 **Peer Relay 与纯 WireGuard** 做 A/B。VPS 地域必须根据“两端到 VPS 的实测 RTT、丢包和晚高峰稳定性”选择；不能仅凭香港、深圳地理距离判断。
5. **只有 UDP 被封、TCP/443 才通**：才考虑 DERP、NetBird WebSocket 或 ZeroTier TCP relay；它们主要解决可达性，不能承诺低延迟。

**只能实测、不能由文档承诺的事项**：各内地运营商及移动网络的 CGNAT/NAT 类型、UDP 过滤、IPv6 入站、跨城/跨境路由与晚高峰拥塞、实际中继选择及中继吞吐。Tailscale 有香港 DERP 不等于内地控制端一定选香港，也不等于深港、广港能直连；任何“支持 NAT 穿透”的文档都不是这些具体线路的延迟或稳定性 SLA。
