# bond-calendar-notify 📱

每天北京时间 09:17 查询东方财富可转债日历，并通过 Server 酱推送当天可申购的新债。

## 工作方式

- `.github/workflows/push_daily_bonds.yml`：每日抓取、测试并推送，也支持手动运行。
- `.github/workflows/keepalive.yml`：每月记录一次仓库活动，降低公开仓库的定时工作流因长期无活动而被 GitHub 自动停用的风险。
- `bonds.py`：负责接口请求、日期筛选和 Server 酱推送。

默认在没有新债时不推送。将工作流中的 `NOTIFY_WHEN_EMPTY` 改为 `"true"` 后，可每天收到“今日无可申购新债”的确认消息。

## 配置

1. Fork 或复制本仓库。
2. 在仓库的 `Settings → Secrets and variables → Actions` 中新增 Repository secret：
   - 名称：`SERVERCHAN_API_KEY`
   - 值：Server 酱 SendKey
3. 打开 `Actions → push_bonds_daily`，点击 `Enable workflow`。
4. 点击 `Run workflow` 手动运行一次，确认微信能收到通知。

> GitHub 使用 UTC 执行 cron。`17 1 * * *` 对应北京时间每天 09:17，并避开 Actions 的整点拥堵时段。

## 本地验证

需要 Python 3.9 或更高版本（GitHub Actions 使用 Python 3.13）：

```bash
python -m pip install --requirement requirements.txt
python -m unittest discover --start-directory tests --verbose
python bonds.py --dry-run
```

`--dry-run` 会调用真实数据源并显示筛选结果，但不会发送微信通知，也不需要配置 SendKey。

## 可靠性设计

- 东方财富 GET 请求最多重试 3 次，并设置连接与读取超时。
- HTTP 错误、异常响应结构、Server 酱业务错误都会让任务失败，不再出现“没有实际推送但 Actions 显示成功”。
- 使用 `Asia/Shanghai` 时区判断申购日期。
- 每次运行先执行单元测试；任务最长运行 10 分钟。
- 日常推送只有仓库只读权限；只有独立的 keepalive 工作流具有内容写权限。
- 相同工作流不会并发执行，避免手动运行与定时运行重叠造成重复推送。

## 故障排查

- **没有产生新的运行记录**：先确认工作流是否显示 `disabled_inactivity`，如是则点击 `Enable workflow`。
- **Validate configuration 失败**：检查 `SERVERCHAN_API_KEY` 是否存在且名称完全一致。
- **Push today's bonds 失败**：展开对应步骤查看东方财富或 Server 酱的错误信息。
- **希望每天都收到确认**：把 `NOTIFY_WHEN_EMPTY` 设置为 `"true"`。

如果任务必须具备严格的准点和可用性保障，建议将定时调度迁移到云函数或其他专用定时服务；GitHub Actions 的计划任务仍可能因平台负载而延迟。
