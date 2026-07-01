# 怎样基于现有代码进行学习开发

## 项目结构

| 文件夹 | 功能 |
| ----- | ---- |
| backend | 后端代码 |
| crawler | 爬虫程序 |
| xkFrontendts | 前端代码 |
| monitoring | 可观测性配置（Prometheus + Grafana + Loki + Promtail） |
| xkDocs | 本文档 |
| .github/workflows | CI/CD 流水线 |

## 容器化

项目通过 Docker 容器化，提供三种 compose 文件应对不同场景：

| 文件 | 用途 |
|------|------|
| `docker-compose.yml` | 生产部署。包含 mysql + redis + backend + frontend，crawler 通过 `--profile crawler` 按需运行 |
| `docker-compose.test.yml` | CI 测试。每个服务使用独立 DB 实例，通过 pytest 入口运行测试 |
| `docker-compose.monitoring.yml` | 监控套件。Prometheus + Grafana + Loki + Alertmanager，部署时始终与主文件共同使用 |

典型使用方式：

```bash
# 生产部署（监控与业务服务同时启动）
docker compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d --build

# 本地开发（可省略监控，仅启动业务服务）
docker compose up -d --build

# 运行测试
docker compose -f docker-compose.test.yml up --build backend --exit-code-from backend
docker compose -f docker-compose.test.yml up --build crawler --exit-code-from crawler
```

crawler 作为一次性任务，使用 profile 按需执行：

```bash
docker compose run --rm crawler -c 122              # 单个学期
docker compose run --rm crawler -c 122 121          # 多个学期
docker compose run --rm crawler -c 122 -m "手动同步"  # 带备注
```

三个组件的 Dockerfile 各有特点：

- **backend**：`python:3.11-slim` 基础镜像，通过 Gunicorn (gevent) 启动 Flask 应用，单 worker（gevent 协程已提供足够并发）
- **crawler**：`python:3.11-slim` 基础镜像，入口为 `fetchCourseList.py`，作为一次性任务运行
- **frontend**：多阶段构建 — `node:24-alpine` 构建 Vue SPA，产物复制到 `nginx:stable-alpine` 提供静态文件服务

项目经过了漫长的演进过程，从没有容器化和流水线，到部分容器化和一点点流水线，再到现在全部容器化。感谢逐渐强大的 AI 工具，让重构一个现有项目变的非常容易。如果哪天我有精力，希望把后端用 Go 重写，这样运行时容器的体积会更小。

## 后端

后端基于 `Flask`。入口文件 `app.py` 负责创建应用、初始化 Redis、注册蓝图和 Prometheus 指标导出（由 `ENABLE_METRICS` 环境变量控制）。

代码按职责分入三层：

- **`routes/`** — API 路由层。`basic.py`（学期、年级、专业）、`course.py`（课程查询、高级检索、同步）、`status.py`（健康检查、更新时间和同步状态）
- **`db/`** — 数据库访问层。`connection.py`（连接池与上下文管理器）、`router.py`（蓝绿部署路由 — 根据 calendarId 定位活跃数据库）、`course.py`（课程查询 SQL）、`meta.py`（维度表查询 SQL）
- **`utils/`** — 工具层。`response.py`（统一 API 响应格式）、`redis_client.py`（Redis 连接管理）、`redis_cache.py`（三级缓存策略：静态/热/普通，按 calendarId 隔离）、`bckndTools.py`（原始数据切分等工具）

此外还有 `tests/` 目录，包含基于 pytest 的 API 和工具函数测试。

数据库访问使用连接池模式，`DbRouter` 通过 `course_scheduler_meta.active_calendars` 视图自动定位每个学期当前的活跃数据库，支持蓝绿部署的零停机数据更新。

运行后端的方式：

```bash
# Docker（推荐）— 根目录
docker compose up -d --build backend

# 本地 — 切换到 backend 文件夹
flask run --port=1239
```

## Redis

Redis 在项目中承担两个职责：热数据缓存和同步日志流。

### 热数据缓存

后端在查询 MariaDB 前先查 Redis，命中则直接返回。缓存按三级策略管理：

| 等级 | TTL | 晋升机制 | 适用场景 |
|------|-----|----------|----------|
| `static` | 永不过期 | 无（同步时主动清除） | 维度表（校区、学院、学期列表） |
| `hot` | 初始 2 min | 5 min 内命中 ≥3 次自动晋升为 1 hr | 热门课程、高频搜索 |
| `normal` | 固定 10 min | 无（自然过期） | 课程详情、低频检索 |

所有缓存的 key 都按 `calendarId` 隔离（如 `cache:cal:119:campuses`），不同学期的缓存互不影响。同步完成后，爬虫通过 `redis_pub.py` 的 `cache_invalidate()` 扫描并清除对应学期的全部缓存 key，确保用户下次访问拿到最新数据。所有缓存操作静默容错——Redis 不可用时后端退化为直查数据库。

### SSE 日志流

同步过程中，爬虫将实时日志通过 Redis Stream 推送给前端：

```
crawler (redis_pub.py)
  │  xadd → Redis Stream "crawler:log"     ← 实时推送
  │  rpush → Redis List "crawler:log:{id}"  ← 累积聚合（fullLog）
  ▼
backend (routes/status.py)
  │  xread → SSE endpoint /api/sync/history/{id}/stream
  ▼
前端 (EventSource)
  │  实时渲染同步进度
```

- **Stream**：爬虫每写一条日志就 `xadd` 到 Stream，后端 SSE 端点通过阻塞 `xread` 读取，推给前端。Stream 有 `maxlen` 上限防止内存膨胀
- **List**：同时 `rpush` 到 List 做全量累积，同步完成后通过 `aggregate()` 一次性取出存入 MariaDB 作为 `fullLog`，之后删除 List。List 设 24h 过期兜底
- **容错**：所有 Redis 操作在 `try/except redis.RedisError` 内，Redis 挂了不影响爬虫主流程和数据库写入

## 数据库设计

### 分库架构

数据库采用两层结构：

```
course_scheduler_meta          ← 元数据库（1 个）
├── calendar_registry          ← 学期注册表（active_suffix 控制路由）
├── active_calendars (VIEW)    ← 自动计算当前活跃数据库名
└── fetchlog                   ← 同步日志

calendar_{id}_a                ← 学期课程库（每学期 2 个，蓝绿）
calendar_{id}_b
├── coursedetail               ← 课程明细（主表）
├── teacher                    ← 教师与排课
├── major / majorandcourse     ← 专业与课程关联
├── campus / faculty           ← 维度表
├── coursenature / assessment  ← 维度表
└── language                   ← 维度表
```

核心思路：

- **每学期独立数据库**：杜绝跨学期影响。旧设计将所有学期挤在一个库中，[删除某学期数据时可能通过外键级联误伤其他学期](https://github.com/XiaLing233/tongji-course-scheduler/issues/41)。分库后各学期物理隔离，互不干扰
- **每学期双库（蓝绿）**：a 和 b 互为镜像，爬虫写入非活跃库后原子切换 `active_suffix`，后端无感知。切换前用户仍读旧数据，切换瞬间指向新数据，实现零停机更新
- **维度表去 calendarId**：校区、学院、课程性质等表每个学期都维护一份，自包含

### 路由

后端 `DbRouter` 通过 `active_calendars` 视图获取目标数据库名：

```sql
SELECT db_name FROM active_calendars WHERE calendarId = 121
-- → calendar_121_a
```

每次请求根据 URL 中的 `calendarId` 动态路由到对应数据库，维护按学期的连接池。元数据库固定名为 `course_scheduler_meta`。

## 爬虫

爬虫负责从 1 系统登录并爬取课程数据，写入数据库。

### 目录结构

| 目录/文件 | 功能 |
|-----------|------|
| `fetchCourseList.py` | 入口，编排爬取全流程 |
| `auth/` | 登录认证。`loginout.py`（OAuth2 状态机）、`encrypt.py`（密码加密） |
| `meru/` | 邮件收发。`imap.py`（IMAP 接收加强认证验证码）、`smtp.py`（SMTP 发送完成通知） |
| `db/` | 数据库操作。`bluegreen.py`（蓝绿部署 — 写入非活跃库后切换）、`inserter.py`（数据写入）、`connection.py`（连接管理）、`log.py`（同步日志持久化）、`redis_pub.py`（同步完成后清除缓存 + 发布日志到 Redis Stream） |
| `tjSql.py` | 与数据库交互的 SQL 语句 |

### 配置文件

所有配置通过项目根目录的 `.env` 文件统一管理（复制 `.env.example` 并填入真实值），不再使用 `config.ini`。以下为爬虫相关的环境变量：

- **数据库**：`DB_HOST`、`DB_PORT`、`DB_USER`、`DB_PASSWORD`、`DB_R_USER`、`DB_R_PASSWORD`、`DB_META`
- **Redis**：`REDIS_HOST`、`REDIS_PORT`、`REDIS_DB`、`REDIS_STREAM_KEY`、`REDIS_MAXLEN`
- **1 系统认证**：`TJ_SNO`（学号）、`TJ_PASSWD`（密码）
- **邮件（IMAP）**：`IMAP_EMAIL`、`IMAP_GRANTCODE`、`IMAP_SERVER`、`IMAP_PORT`（加强认证时接收验证码）
- **邮件（SMTP）**：`SMTP_SERVER`、`SMTP_PORT`、`SMTP_USERNAME`、`SMTP_PASSWORD`、`SMTP_SENDER`、`CRAWLER_SEND_EMAIL`（爬取结束后发送邮件提醒，非必须）
- **学期参数**：通过 CLI 传入，`-c` 指定学期 ID（必填，支持多个），`-m` 添加同步备注，`--dry-run` 预览不执行

IMAP 配置需要根据实际绑定的邮箱替换。示例基于 QQ 邮箱，使用其他邮箱需要修改对应参数。

这里必须要准备的参数有自己的学号和密码。其余如果出于本地开发的目的，不必准备。关于 IMAP，在加强认证时，会给邮箱发送验证码，我的示例基于 QQ 邮箱，且代码中设置的读取路径也是个性化的，因此如果需要迁移到自己的邮件服务，不只要修改配置邮件，还要修改源代码 `imap.py` 的 `get_latest_verification_code` 函数。

### 数据库初始化

与旧版不同，不再需要手动运行 `initNewDB.py`。MariaDB 容器首次启动时会自动从 `crawler/meta_template.sql` 初始化元数据库结构（`course_scheduler_meta`），课程数据库（`calendar_{id}_a` / `calendar_{id}_b`）则按 `course_template.sql` 的结构由爬虫首次执行时自动创建。

之所以使用 MariaDB，而不是 MySQL，因为前者的镜像体积小一些。

### 蓝绿部署

爬虫采用蓝绿部署策略写入数据，避免更新过程中影响用户查询：

1. `ensureCalendarDb()` — 确保目标学期有 a 和 b 两个数据库，若不存在则按模板创建
2. **写入非活跃库** — 将爬取的数据全部写入当前**非活跃**侧的数据库（先 TRUNCATE 清空旧数据）
3. `switchActiveDb()` — 原子切换活跃标识，后端下次查询自动指向新库
4. `cacheInvalidate()` — 清除 Redis 中该学期的缓存

爬取过程中使用 `tjSql.py` 完成数据库的写入操作。

## 前端

前端基于 `Vue3` + `TypeScript`，负责课程浏览、排课模拟、冲突检测等交互逻辑。

### 本地开发

```bash
cd xkFrontendts
npm install
npm run dev          # Vite 开发服务器，API 请求代理到 localhost:1239 后端
npm run type-check   # TypeScript 类型检查
npm run test         # Vitest 单元测试
npm run build-only   # 生产构建 → dist/
```

### 构建与部署

前端采用**多阶段 Docker 构建**：

1. **构建阶段**（`node:24-alpine`）：`npm ci` 安装依赖 → `npm run build-only` 生成 `dist/` 静态文件
2. **运行阶段**（`nginx:stable-alpine`）：将 `dist/` 复制到 nginx 静态目录，通过自定义 `nginx.conf` 处理 SPA 路由（所有路径 fallback 到 `index.html`）并反向代理 `/api/` 请求到后端

生产环境中前端容器对外暴露 80 端口，由 `docker-compose.yml` 映射到宿主机的 1239 端口。用户访问 `xk.xialing.icu` 时，由云服务器的 nginx 反代到容器的 1239 端口。

这种方式的好处是前端构建产物只是一个静态 nginx 容器，运行时没有 Node.js 依赖，镜像体积小、性能高。

## Nginx 路由

项目采用**双层 nginx**架构：

```
用户浏览器 (HTTPS)
  │  xk.xialing.icu
  ▼
宿主机 nginx (SSL 终止 + 域名路由)
  │  /           → http://127.0.0.1:1239        (前端容器)
  │  /docs/      → /var/www/xkDocs/              (文档站静态文件)
  │  /.well-known/ → certbot 验证
  ▼
前端容器内 nginx (服务间路由)
  │  /           → SPA 静态文件 (try_files fallback)
  │  /api/       → http://xk-backend:1239         (后端)
  │  /grafana/   → http://xk-grafana:3000         (Grafana)
```

**宿主机 nginx** 运行在云服务器上，负责：

- SSL 终止（通过 certbot 自动管理 HTTPS 证书）
- 域名路由：将 `xk.xialing.icu` 的请求转发到 Docker 容器的 1239 端口（前端容器）
- 文档站：`xk.xialing.icu/docs/` 直接 serve Vitepress 构建产物（`xkDocs/.vitepress/dist/`），与业务容器解耦，由独立的 `docs-deploy.yml` 流水线部署

**容器内 nginx**（`xkFrontendts/nginx.conf`）运行在前端容器中，负责：

- SPA 路由：`try_files $uri /index.html`，所有非 API 路径 fallback 到 `index.html`，支持 Vue Router 的 history 模式
- API 代理：`/api/` 转发到 `xk-backend:1239`（Docker 内部网络），关闭缓冲（`proxy_buffering off`）支持 SSE 长连接，超时设为 1 小时
- Grafana 代理：`/grafana/` 转发到 `xk-grafana:3000`，用户无需暴露额外端口即可访问监控面板

所有服务共享 Docker 内部网络 `xk_network`，容器间通过服务名互相访问，不暴露到公网。对外只需前端容器的 80 端口映射到宿主机 1239。这种设计让 nginx 配置职责分明：宿主机只管「从哪来」（域名/HTTPS），容器内只管「到哪去」（服务路由）。

## 可观测性

项目提供了一套完整的监控栈，通过 `docker-compose.monitoring.yml` 与主文件共同部署：

- **Prometheus** — 每 15s 从后端 `/metrics` 采集指标（请求数、QPS、延迟分布、状态码）
- **Grafana** — 预置仪表板：系统状态（QPS/延迟/热力图）、API 总览（速率/错误率/状态码/Top API）、告警面板、日志面板。匿名只读，通过 `/grafana/` 子路径访问
- **Loki + Promtail** — 收集所有容器的日志，支持在 Grafana 中按标签检索
- **Alertmanager** — 基于 Prometheus 告警规则，通过 SMTP 发送邮件通知

后端通过环境变量 `ENABLE_METRICS=true` 开启 Prometheus 指标导出，默认关闭以免影响本地开发。

> 监控系统刚上线，不稳定，会有一些明显失真的指标，逐渐观察中。

## 文档

文档基于 `Vitepress`。需要切换到 `xkDocs` 文件夹，运行 `npm install` 安装依赖；`npm run docs:dev` 进行页面预览；`npm run docs:build` 生成可部署的文件。

## 流水线

流水线在 `.github/workflows/ci.yml` 下：

1. **路径过滤**（`dorny/paths-filter`）— 检测哪些组件发生了变更（backend / crawler / frontend / monitoring）
2. **测试** — 仅运行变更组件的测试（pytest / vitest / type-check）
3. **构建镜像** — 将变更组件的 Docker 镜像推送到 GitHub Container Registry (ghcr.io)
4. **部署** — SSH 到服务器，`git pull && docker compose pull && docker compose up -d`。只要有任一组件构建成功（未被跳过）即执行部署，无需所有组件都变更

另有一个 `docs-deploy.yml` 用于部署文档站到独立服务器。

## 其他

有关云服务器、`Linux`、`crontab`、`gunicorn`、`systemctl`、`nginx`、域名、`DNS`、`Cloudflare`、`GitHub` 相关的技术，不再赘述了。
