# YouziLoadLab 对齐 NashiYard 总项目压测验收执行计划

**日期:** 2026-05-06  
**状态:** Planning / 待执行  
**目标仓库:** `E:\cursor_project\nashiyard\youziloadlab`  
**源要求:** `E:\cursor_project\nashiyard\nashiyard\docs`，重点是 Fireworks 压测、安全脱敏、Polling 压力、Multi-Key/租约行为、Relay 稳定性观测。

---

## 1. 总目标

把 YouziLoadLab 从“可部署的压测平台骨架”升级为“能执行 NashiYard 总项目文档要求、能产出可复核压测报告的独立 WebUI 压测系统”。

第一版完成后，操作者应能在 WebUI 中完成：

1. 配置 NashiYard 目标站点、管理员凭据、测试 token、Fireworks keys。
2. 自动准备隔离压测环境：测试用户、token、额度、分组、Fireworks 渠道、批量 key。
3. 执行 Fireworks 五轮压力测试和冒烟测试。
4. 执行 Polling 系统压力测试，区分 admin/user polling 与前台 chat 流量。
5. 执行安全脱敏探针，验证错误响应体和响应头不暴露 provider/key/account/billing 信息。
6. 采集 Locust 统计、NashiYard API 探针结果、日志关键模式、资源观测数据和操作者备注。
7. 自动生成报告，明确通过、失败、风险、未验证项和清理状态。
8. 安全停止运行，并清理或保留测试资源。

---

## 2. 非目标

第一版不做以下事情：

- 不实现分布式 Locust 集群。
- 不绕过 NashiYard 权限模型；所有 admin/user 操作都走真实 API。
- 不在 YouziLoadLab 中复制 NashiYard 业务逻辑。
- 不读取或存储 Fireworks 明文 key 到报告、事件日志、前端状态。
- 不把机器保护上限放回环境变量；并发、阶段参数、是否执行完整压测由 WebUI run config 控制。
- 不承诺自动验证需要外部账单后台的数据，只提供手动录入和证据字段。

---

## 3. 当前缺口判断

| 模块 | 当前状态 | 缺口 |
| --- | --- | --- |
| 登录保护 | 已实现 | 需要保留，所有 API/WebUI 操作登录后可用。 |
| Run 创建 | 只创建 DB 记录和 placeholder Locust URL | 必须真正启动 Locust、跟踪进程、停止、采集产物。 |
| Fireworks 场景 | 有 Locust chat 用户和默认 phase helper | 缺 admin setup/cleanup、五轮编排、异常注入、阈值判定、报告。 |
| Polling 场景 | 有基础 GET 和前台 chat | 缺 session/cookie 鉴权、严格间隔调度、endpoint 探测、401/403 归因。 |
| NashiYard Admin Adapter | 只有 login/create_user 雏形 | 需要完整覆盖用户、quota、token、channel、keys、cleanup、查询状态。 |
| 安全脱敏测试 | 只有文档和基础错误分类 | 需要主动 probe、响应头/body 关键词扫描、stream/non-stream 双路径。 |
| WebUI | 当前是简单 Dashboard | 需要目标/密钥/场景/运行/报告 UI。 |
| 报告 | DB model 有基础结构 | 需要汇总 Locust CSV、阈值、证据、清理状态、导出。 |
| Zeabur | 可部署，需最小 env | 需要验证真实运行产生的数据都落 `/data`。 |

---

## 4. 验收标准总表

### 4.1 Fireworks 压测验收

必须覆盖 NashiYard `fireworks-stress-test-plan.md` 的核心项：

| 阶段 | 时长 | 并发 | RPS | 通过门槛 |
| --- | ---: | ---: | ---: | --- |
| Smoke | 60s | 5 | 2 | 成功率 >= 95%，平均响应 <= 5s，P99 <= 10s，无 5xx。 |
| W1 Baseline | 300s | 10 | 2 | 成功率 >= 95%，平均延迟 <= 5s。 |
| W2 Ramp | 600s | 50 | 5 | 成功率 >= 90%，错误分类清晰，key 分配可观测。 |
| W3 Peak | 300s | 100 | 10 | 无持续 5xx，P95/P99 记录完整。 |
| W4 Fault Injection | 600s | 30 | 3 | 混入无效 key 后，401/403 禁用、412 处理、静默重试行为被记录。 |
| W5 Recovery | 300s | 20 | 2 | 成功率恢复 >= 95%，错误率回落。 |

必须生成的证据：

- 每轮 Locust stats/failures/exceptions。
- 每轮成功率、平均延迟、P50/P95/P99、RPS、失败分类。
- 412、429、5xx、timeout、auth/quota、invalid request 分桶。
- 渠道状态检查结果。
- key 状态变化检查结果。
- 手动或 API 录入的计费核对字段。
- 错误响应泄露扫描结果。
- 清理状态。

### 4.2 Polling 系统验收

必须覆盖 NashiYard dashboard/background 轮询压力：

| 阶段 | 时长 | 用户 | Spawn Rate | 目标 |
| --- | ---: | ---: | ---: | --- |
| Smoke | 60s | 1 | 1 | 验证鉴权和 endpoint 可用性。 |
| Baseline | 5m | 5 | 1 | 建立 `/api/channel/`、`/api/token/`、`/api/log/self` 延迟基线。 |
| Mixed | 10m | 20 | 2 | polling + foreground chat 混合压力。 |
| Peak | 10m | 50 | 5 | 找 admin/user endpoint 饱和点和 gateway 竞争。 |

必须分开统计：

- `Polling GET /api/channel/`
- `Polling GET /api/token/`
- `Polling GET /api/log/self`
- `Polling foreground chat`
- 401/403 鉴权失败
- 429 rate limit
- 5xx/panic
- secret/key/provider 泄露扫描

### 4.3 安全脱敏验收

必须覆盖：

- 非流式错误响应体关键词扫描。
- 流式错误响应体关键词扫描。
- 响应头黑名单扫描：`Server`、`Via`、上游 request id、provider 特征头。
- provider/account/billing/payment/spending/suspended/fireworks/model path 等关键词扫描。
- 401/403、429、500、invalid model、invalid key、quota exhausted 场景。

扫描结果必须进入报告，报告不得包含明文 secret。

---

## 5. 架构改造方案

### 5.1 后端执行链路

新增真实 Run 生命周期：

```text
created -> preparing -> running -> stopping -> completed
                         |          |          |
                         v          v          v
                       failed     stopped    cleanup_failed
```

后端职责：

1. 校验 run config 和 scenario schema。
2. 解析 target/secrets，但只把敏感值传入 runner 环境或临时配置文件。
3. 为每次运行创建 `/data/runs/<run_id>/` 工作目录。
4. 写入 redacted run manifest。
5. 启动 Locust subprocess。
6. 记录 PID、命令、开始时间、工作目录、artifact 路径。
7. 定时采集进程状态、CSV 统计和事件。
8. 支持停止 run，优先优雅终止，超时后强制 kill。
9. 运行结束后生成 Report。
10. 所有事件日志走统一 redaction。

建议新增/修改文件：

- `apps/api/youziloadlab_api/services/locust_process.py`
- `apps/api/youziloadlab_api/services/run_orchestrator.py`
- `apps/api/youziloadlab_api/services/run_worker.py`
- `apps/api/youziloadlab_api/services/artifacts.py`
- `apps/api/youziloadlab_api/services/report_builder.py`
- `apps/api/youziloadlab_api/modules/runs/router.py`
- `apps/api/youziloadlab_api/modules/reports/router.py`
- `apps/api/youziloadlab_api/db/models.py`

### 5.2 Runner 配置方式

不要把复杂 JSON 全塞命令行。采用每次 run 一个配置文件：

```text
/data/runs/<run_id>/runner-config.json
/data/runs/<run_id>/locust-stats.csv
/data/runs/<run_id>/locust-failures.csv
/data/runs/<run_id>/locust-exceptions.csv
/data/runs/<run_id>/runner.log
/data/runs/<run_id>/report.json
/data/runs/<run_id>/report.md
```

敏感配置处理：

- DB 中 secret 加密保存。
- 启动前解密到内存。
- runner config 文件默认不写明文 secret；优先通过环境变量传递。
- 若 Locust 必须读取 token 文件，写入 `/data/runs/<run_id>/secrets.runtime.json`，权限收紧，运行结束默认删除或加密归档。
- report 和 event 永远只保存 fingerprint/masked preview。

### 5.3 Scenario Contract

新增 runner 统一入口：

```text
youziloadlab-runner run --scenario <id> --config <path> --artifacts-dir <path>
```

每个 scenario 实现同一契约：

- `validate_config(config) -> ValidationResult`
- `prepare(context) -> PrepareResult`
- `build_locust_command(context) -> list[str]`
- `post_run(context) -> ProbeResult`
- `cleanup(context) -> CleanupResult`
- `build_report_sections(context) -> list[ReportSection]`

FastAPI 不直接 import 场景细节，只通过 scenario ID 和 runner CLI 执行。

---

## 6. 任务分解

### Phase 0：计划和基线冻结

目标：明确总项目要求与当前差距，避免边写边漂移。

任务：

1. 把本计划作为总执行计划。
2. 建立 `docs/requirements/nashiyard-validation-matrix.md`，逐条映射 NashiYard docs 要求、实现位置、测试方式、状态。
3. 建立 `docs/runbook/fireworks-full-validation.md`，作为人工执行和自动执行一致的 runbook。
4. 建立 `docs/runbook/polling-system-validation.md`。
5. 建立 `docs/runbook/security-sanitization-validation.md`。

验收：

- 每个总项目要求都有 `covered / partial / missing / not applicable` 状态。
- 明确哪些项需要真实 staging 环境才能验证。

### Phase 1：真实 Run 执行和 Locust 生命周期

目标：WebUI/API 创建 run 后必须真的执行 Locust。

任务：

1. 替换 `launch_placeholder()` 为真实 subprocess 启动。
2. 生成 run 工作目录和 artifact 文件路径。
3. 支持 headless Locust 参数：`--headless`、`--users`、`--spawn-rate`、`--run-time`、`--csv`、`--html`。
4. 保存 `pid`、`command`、`started_at`、`finished_at`、`exit_code`。
5. 新增 `POST /api/runs/{id}/stop`。
6. 新增 run event：prepared、started、stats_snapshot、stopping、stopped、completed、failed。
7. 后台 worker 轮询 Locust 进程状态并更新 DB。
8. 解析 Locust CSV 写入 `RunMetricsSnapshot`。
9. 失败时保留 stderr/stdout，并 redaction。

测试：

- unit：命令构造、路径构造、redaction。
- integration：用 fake locust Python 脚本模拟启动/退出/失败。
- API：创建 run 后状态进入 running/completed。
- API：stop 能终止长运行 fake process。

验收：

- `POST /api/runs` 能产生真实 artifact。
- `/api/runs/{id}/events` 有生命周期事件。
- `/api/runs/{id}/metrics` 有快照。
- 重启服务后可读取历史 artifact。

### Phase 2：NashiYard Admin Adapter 完整化

目标：把 Fireworks 压测前置准备从手工脚本变成可控 adapter。

任务：

1. 登录：`POST /api/user/login`，保存 cookie session。
2. 创建测试用户：`POST /api/user/`，支持 `discord_gate_exempt=true`。
3. 查询测试用户 ID：支持分页和 keyword。
4. 用户充值 quota：`POST /api/user/quota/:id`，明确增量语义。
5. 用户登录并获取 access token：`GET /api/user/token`。
6. 创建测试 token：`POST /api/token/`，设置 group、quota、expired_time。
7. 查询 token key：`GET /api/token/`。
8. 创建 Fireworks channel：`POST /api/channel/`，type=41，group=`fireworks_stress`。
9. 查询 channel ID：`GET /api/channel/`。
10. 批量添加 Fireworks keys：`POST /api/channel/:id/keys`。
11. 注入 invalid keys，用于 W4。
12. 查询 key/channel 状态，用于报告证据。
13. 清理 token/user/channel。
14. 所有请求和日志必须 redaction。
15. adapter 支持 dry-run，输出将执行的动作但不调用目标。

测试：

- 使用 `httpx.MockTransport` 覆盖每个 endpoint。
- 测试分页返回、失败返回、cookie/session、401/403、字段缺失。
- 测试 redaction：不输出 password/key/token/cookie。

验收：

- 在 mock NashiYard 上能完整 prepare + cleanup。
- 在 staging 上可 dry-run 展示计划。
- 任何失败都能指出停在 prepare 哪一步。

### Phase 3：Fireworks 完整场景编排

目标：执行总项目 Fireworks 五轮压测。

任务：

1. 定义 `FireworksRunConfig`：
   - targetId
   - admin secret id
   - fireworks keys secret id
   - test group
   - model
   - quota limits
   - phase selection
   - stream ratio
   - max tokens
   - fault injection enabled
   - cleanup policy
2. 实现 prepare：创建用户、quota、token、channel、keys。
3. 实现 smoke 单轮执行。
4. 实现 W1-W5 phase plan。
5. 实现 phase runner：每轮一个 Locust run 或同一 run 内 phase 子任务，优先“每轮独立子进程”，便于报告隔离。
6. W4 前注入 invalid keys。
7. 每轮结束后查询 channel/key 状态。
8. 每轮结束后执行安全脱敏 probes。
9. 汇总 phase 结果。
10. 支持失败回退和紧急停止。

通过门槛：

- Smoke 不通过时默认不允许继续完整压测，除非操作者显式 override。
- 任意轮成功率 < 50%、5xx > 10%、发现敏感信息泄露时标记 critical，并建议停止。
- W4 必须区分 401/403/412/429/5xx/timeout。

测试：

- unit：phase 表与文档一致。
- unit：阈值判定。
- integration：mock target 返回不同错误码，报告分类正确。
- integration：W4 invalid key 注入步骤被调用。

验收：

- 一次 run 下能看到 phase 列表和每轮状态。
- report 中有总项目表格对应指标。

### Phase 4：Polling 系统场景升级

目标：从“随机 weighted GET”升级成真实 polling 压力测试。

任务：

1. 增加 polling endpoint 配置：method、path、auth type、interval、weight、expected statuses。
2. 支持 Cookie Session、Bearer token、无鉴权三类 auth。
3. prepare 阶段验证每个 endpoint 可用性。
4. 将当前 weighted task 改为可配置任务集，严格记录每个 endpoint 名称。
5. 支持 foreground chat ratio、model、token、max tokens。
6. 分阶段执行 Smoke/Baseline/Mixed/Peak。
7. 单独统计 polling 和 chat 结果。
8. 对 401/403 标记为 auth_config_error 或 expected_protected，避免误判为性能问题。
9. 增加 response leakage scan。

测试：

- unit：endpoint config schema。
- unit：auth header/cookie 构造。
- integration：mock endpoint 200/401/403/429/500 分类。
- Locust dry smoke：本地 mock server 产生可预期统计。

验收：

- report 能清楚说明 polling endpoint 是否压到了真实业务，而不是只打出 401。
- foreground chat 不污染 polling endpoint 延迟统计。

### Phase 5：安全脱敏 Probe Suite

目标：把 `error-response-sanitization.md` 变成自动化测试套件。

任务：

1. 新增 runner probe 模块：`runner/youziloadlab_runner/probes/security_sanitization.py`。
2. Probe 类型：
   - invalid bearer token
   - invalid model
   - malformed request
   - quota/auth failure fixture
   - stream request failure
   - non-stream request failure
3. 响应头扫描：黑名单 + provider 特征。
4. 响应体扫描：provider/account/billing/payment/spending/suspended/full model path/token/key/cookie。
5. OpenAI error object 结构检查。
6. 每个 probe 记录：request class、status、headers finding、body finding、raw sample redacted。
7. 报告输出 pass/fail/needs_manual_setup。

测试：

- unit：关键词扫描。
- unit：header blacklist。
- unit：redacted sample 不含 secret。
- integration：fake upstream 返回 Fireworks 风格错误，probe 必须判 fail。

验收：

- Fireworks 压测报告自动包含安全脱敏章节。
- 发现泄露时 run 标记 `failed_security_gate` 或 report 标记 critical。

### Phase 6：报告系统

目标：报告可被总项目开发者复核，而不是只有 Locust 原始 CSV。

任务：

1. 定义 report schema：summary、environment、target、scenario、phases、metrics、errors、security findings、operator notes、cleanup、attachments。
2. 生成 `report.json` 供 WebUI 渲染。
3. 生成 `report.md` 供归档。
4. 支持下载 Locust HTML/CSV/JSON artifact。
5. 阈值判定统一封装。
6. 支持手动证据字段：Fireworks 账单核对、Zeabur CPU/memory 截图备注、NashiYard 日志摘录。
7. 所有文本进入报告前 redaction。
8. WebUI 展示 pass/fail/warn/unknown。

测试：

- unit：统计聚合。
- unit：percentile 和 failure rate。
- unit：阈值 pass/fail。
- snapshot：report markdown 稳定输出。

验收：

- 报告能回答：测了什么、怎么测、结果如何、是否通过、证据在哪、清理了吗、有什么风险。

### Phase 7：WebUI 完整操作流

目标：操作者不用改 Python 脚本即可跑测试。

页面/能力：

1. Login：已完成，保留。
2. Targets：创建/编辑 NashiYard/OpenAI-compatible target。
3. Secrets：保存 admin password、bearer token、Fireworks keys、cookie，展示 masked preview。
4. Scenarios：展示 schema、说明、风险。
5. Run Wizard：
   - 选择 target。
   - 选择 scenario。
   - 选择 secret。
   - 填写 phase/concurrency/rps/duration/model/stream ratio。
   - 选择 dry-run、prepare、cleanup policy。
   - 显示安全确认。
6. Run Detail：状态、events、metrics、Locust artifact、stop 按钮。
7. Reports：报告列表、报告详情、下载。
8. Evidence Notes：手动补充账单/资源/日志证据。

测试：

- TypeScript typecheck。
- 关键组件单测或轻量 Vitest。
- 手动浏览器验证：login -> target -> secret -> run wizard -> run detail -> report。

验收：

- Zeabur 部署后 WebUI 能完成全流程。
- 未登录访问任何 API 被 401。

### Phase 8：Zeabur 部署验证

目标：部署环境可长期保留历史运行数据。

任务：

1. 保持最小环境变量：
   - `APP_ENV=production`
   - `APP_SECRET_KEY`
   - `ADMIN_PASSWORD`
   - `DATABASE_URL=sqlite:////data/youziloadlab.db`
   - `DATA_DIR=/data`
   - `RUNNER_WORKDIR=/data/runs`
2. 确认 `/data` volume 挂载。
3. 确认 Locust subprocess 在容器内可启动。
4. 确认 run artifacts 写入 `/data/runs`。
5. 确认重部署后 DB/report/artifacts 保留。
6. 确认 Docker image 包含 runner/scenario 文件。

验收：

- Zeabur health check 通过。
- 登录成功。
- 本地或 staging smoke run 成功。
- 重部署后历史 run/report 可见。

---

## 7. 数据模型建议

新增/扩展：

| Model | 字段重点 |
| --- | --- |
| `Run` | `status`, `pid`, `exit_code`, `workdir`, `scenario_id`, `started_at`, `finished_at`, `error_message` |
| `RunEvent` | `run_id`, `level`, `event_type`, `message`, `payload_json`, `created_at` |
| `RunMetricsSnapshot` | `run_id`, `phase_name`, `name`, `method`, `request_count`, `failure_count`, `avg_ms`, `p50_ms`, `p95_ms`, `p99_ms`, `rps` |
| `Report` | `run_id`, `status`, `summary_json`, `report_json_path`, `report_md_path` |
| `RunArtifact` | `run_id`, `kind`, `path`, `size_bytes`, `sha256`, `created_at` |
| `ScenarioRunPhase` | `run_id`, `phase_name`, `status`, `users`, `spawn_rate`, `duration_seconds`, `started_at`, `finished_at` |

SQLite 先行，后续可迁移 Postgres。不要把 secret 明文放入任何 JSON 字段。

---

## 8. API 建议

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `POST` | `/api/runs` | 创建并可选择立即启动 run。 |
| `POST` | `/api/runs/{id}/start` | 启动已创建 run。 |
| `POST` | `/api/runs/{id}/stop` | 停止 run。 |
| `GET` | `/api/runs/{id}` | 获取状态。 |
| `GET` | `/api/runs/{id}/events` | 获取事件。 |
| `GET` | `/api/runs/{id}/metrics` | 获取指标快照。 |
| `GET` | `/api/runs/{id}/artifacts` | 获取产物列表。 |
| `GET` | `/api/reports/{id}` | 获取报告 JSON。 |
| `GET` | `/api/reports/{id}/markdown` | 下载报告 Markdown。 |
| `POST` | `/api/reports/{id}/notes` | 添加操作者证据备注。 |
| `POST` | `/api/scenarios/{id}/validate-config` | 校验场景配置。 |
| `POST` | `/api/scenarios/{id}/dry-run` | 展示 prepare/run/cleanup 计划，不执行。 |

---

## 9. 测试策略

### 9.1 YouziLoadLab 自身测试

每个阶段必须跑：

```powershell
py -3.13 -m pytest apps/api/tests runner/tests -q
py -3.13 -m ruff check apps/api runner
py -3.13 -m mypy apps/api runner
pnpm --filter @youziloadlab/web typecheck
pnpm --filter @youziloadlab/web build
```

Docker 可用时跑：

```powershell
docker build -t youziloadlab .
```

### 9.2 Mock NashiYard 集成测试

新增本地 fake NashiYard server，用于自动化覆盖：

- admin login success/fail。
- create user/token/channel。
- channel keys add/list/delete。
- `/v1/chat/completions` 200/401/403/412/429/500/timeout。
- stream before first chunk failure。
- stream after chunks failure。
- provider leakage headers/body。

### 9.3 Staging 验证

真实执行分三层：

1. `dry-run`：只验证配置和将要执行的 API 操作。
2. `smoke`：1 分钟、低并发、低额度。
3. `full`：五轮完整 Fireworks 压测。

任何 full run 前必须 smoke 通过，并确认：

- 独立 group。
- token quota 已限制。
- cleanup 策略明确。
- Fireworks keys 数量足够。
- Zeabur `/data` volume 正常。

---

## 10. 风险控制

| 风险 | 处理 |
| --- | --- |
| 误打生产用户/渠道 | 默认创建独立 group，Run Wizard 强制确认。 |
| 账单超支 | token quota、channel 限额、phase 明确展示；full run 需确认。 |
| Secret 泄露 | redaction 单元测试 + 报告扫描 + artifact 过滤。 |
| Locust 进程残留 | stop endpoint + startup reconcile 清理 orphan pid。 |
| W4 异常注入导致渠道不可用 | invalid key 注入前记录 channel 状态，W4 后立即状态检查和 cleanup。 |
| Polling 打出大量 401 被误判为性能差 | auth_config_error 单独分类。 |
| Zeabur 容器重启丢运行状态 | DB 记录 + artifact 持久化；启动时 reconcile running 状态。 |
| 阈值过于死板 | 报告分 `pass/fail/warn/unknown`，真实账单/资源可标记 manual evidence。 |

---

## 11. 推荐执行顺序

必须按顺序推进，不能先做漂亮 UI：

1. **真实 Run/Locust 生命周期**：没有它，WebUI 都是假操作。
2. **Admin Adapter 完整化**：没有它，Fireworks 总项目要求无法闭环。
3. **Fireworks Smoke + Report**：先做到低风险端到端。
4. **Security Probe Suite**：尽早做，避免报告泄露明文。
5. **Fireworks Full W1-W5**：完整压测。
6. **Polling Auth + Phase Runner**：补齐轮询系统专项。
7. **WebUI Run Wizard/Report UI**：把已稳定的后端能力产品化。
8. **Zeabur Staging 验证**：验证部署和挂盘。

---

## 12. 第一批提交拆分建议

| PR/Commit | 内容 | 可验收结果 |
| --- | --- | --- |
| 1 | Run workdir、artifact、real Locust subprocess、stop API | fake locust integration 通过。 |
| 2 | NashiYard admin adapter 扩展 | mock admin setup/cleanup 通过。 |
| 3 | Fireworks smoke scenario orchestrator | mock/staging smoke 可生成报告。 |
| 4 | Report builder + threshold evaluator | report json/md 稳定输出。 |
| 5 | Security probes | fake leakage 能判 fail。 |
| 6 | Fireworks full phase orchestrator + W4 injection | W1-W5 mock flow 通过。 |
| 7 | Polling auth/configurable endpoints | polling report 分桶准确。 |
| 8 | WebUI run wizard/report detail | WebUI 能完整操作。 |
| 9 | Zeabur runbook + deployment verification | Zeabur smoke 通过。 |

---

## 13. 完成定义

本目标完成不是“测试命令通过”，而是满足以下条件：

- YouziLoadLab 能从 WebUI 发起真实 NashiYard Fireworks smoke run。
- YouziLoadLab 能发起完整 W1-W5 run，或明确标记因 staging 资源不足只完成 smoke。
- Report 能映射 NashiYard 总项目文档的每个核心验收项。
- Security probe 能发现并报告错误响应泄露。
- Polling scenario 能使用真实鉴权打到目标 endpoint，并与 chat 流量分开统计。
- 所有 secret 在 DB、log、event、artifact、report、WebUI 中不明文泄露。
- Zeabur 部署后 run artifacts 持久化到 `/data`。
- 自动化测试、类型检查和 Web build 通过。
