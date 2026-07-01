# 同济排课助手

同济大学 1 系统（选课平台）的第三方课程浏览与排课模拟工具。提供比官方系统更友好的课程检索、课表编排、冲突检测和导出功能。

## 动机

1 系统的官方选课界面体验不佳：课程搜索繁琐、无法提前模拟排课、不支持课表导出。本项目最初是 *just a hobby*，后来逐步演进为功能完整的选课辅助网站，每学期稳定服务数百名同济学生。

核心目标：

- **提前规划**：在正式选课前浏览所有学期的课程，模拟编排课表
- **冲突检测**：自动检测时间冲突，避免选课时的意外
- **数据同步**：每周自动爬取 1 系统最新课程数据，保持信息准确
- **开放生态**：支持导出到 WakeUp 课程表等第三方工具

## 技术栈

| 层 | 技术 |
|---|------|
| 前端 | Vue 3 + TypeScript + Vite + Ant Design Vue + Tailwind CSS |
| 后端 | Python 3.11 + Flask + Gunicorn (gevent) |
| 爬虫 | Python 3.11 + requests + BeautifulSoup + PyCryptodome |
| 数据库 | MariaDB |
| 缓存 / 流 | Redis |
| 监控 | Prometheus + Grafana + Loki + Alertmanager |
| CI/CD | GitHub Actions + Docker + GitHub Container Registry |
| 文档 | Vitepress |

## 使用方法

访问 **[xk.xialing.icu](https://xk.xialing.icu)**。

详细使用指南见 [用户文档](https://xk.xialing.icu/docs/user/)。

## 本地开发

### 环境要求

如果使用容器，则只需要准备

- Docker + Docker Compose

如果希望不使用容器，则需要为前后端准备依赖（不推荐）

- Node.js 24+（前端开发）
- Python 3.11（可选，用于不使用 Docker 调试后端/爬虫）

### 快速启动

```bash
# 1. 配置文件
cp .env.example .env   # 填写 DB_PASSWORD 等必要字段

# 2. 启动全部服务（mysql + redis + backend + frontend）
docker compose up -d --build

# 3. 访问前端
# http://localhost:1239
```

此时数据库为空，需要爬取课程数据：

```bash
# 爬取指定学期（可多个）
docker compose run --rm crawler -c 122
docker compose run --rm crawler -c 122 121 -m "手动同步"
```

### 运行测试

```bash
# 后端测试
docker compose -f docker-compose.test.yml up --build backend --exit-code-from backend

# 爬虫测试
docker compose -f docker-compose.test.yml up --build crawler --exit-code-from crawler
```

### Docker Compose 文件说明

项目提供了三个 compose 文件，用于不同场景：

| 文件 | 用途 | 启动方式 |
|------|------|----------|
| `docker-compose.yml` | **生产部署**。包含 mysql + redis + backend + frontend，crawler 通过 `--profile crawler` 按需运行 | `docker compose up -d` |
| `docker-compose.test.yml` | **CI 测试**。每个服务使用独立 DB 实例，通过 pytest 入口运行测试，退出后容器自动停止 | `docker compose -f docker-compose.test.yml up --build backend` |
| `docker-compose.monitoring.yml` | **监控套件**。Prometheus + Grafana + Loki + Alertmanager，并为 backend 开启 `/metrics` 端点。部署时始终与主文件共同使用 | `docker compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d` |

### 项目结构

```
tongji-course-scheduler/
├── backend/             # Flask 后端 API
│   ├── db/              #   数据库访问层（连接池、路由、查询）
│   ├── routes/          #   API 路由（basic、course、status）
│   ├── utils/           #   工具（Redis 缓存、响应格式）
│   ├── tests/           #   pytest 测试
│   ├── app.py           #   入口
│   └── Dockerfile
├── crawler/             # 课程数据爬虫
│   ├── auth/            #   登录认证与加密
│   ├── meru/            #   邮件收发（IMAP/SMTP）
│   ├── db/              #   蓝绿部署、数据写入、日志发布
│   ├── tests/           #   pytest 测试
│   ├── fetchCourseList.py  # 入口
│   └── Dockerfile
├── xkFrontendts/        # Vue 3 前端 SPA
│   └── Dockerfile       #   多阶段构建（node 构建 + nginx 运行）
├── monitoring/          # 可观测性配置
│   ├── prometheus/      #   Prometheus 采集规则 + 告警规则
│   ├── grafana/         #   Grafana 仪表板 + 数据源
│   ├── alertmanager/    #   Alertmanager 邮件告警模板
│   ├── loki/            #   Loki 日志聚合配置
│   └── promtail/        #   Promtail 日志采集配置
├── xkDocs/              # Vitepress 文档站
├── .github/workflows/   # CI/CD 流水线
├── docker-compose.yml
├── docker-compose.test.yml
└── docker-compose.monitoring.yml
```

## 部署

项目通过 GitHub Actions 自动部署到生产服务器：

1. **代码推送** → 路径过滤检测变更的组件
2. **运行测试**（backend / crawler / frontend）
3. **构建 Docker 镜像**并推送到 ghcr.io
4. **SSH 到服务器**，`git pull && docker compose pull && docker compose up -d`

生产部署命令（监控与业务服务同时启动）：

```bash
docker compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d
```

## 自动化

- **CI/CD**：GitHub Actions（`.github/workflows/ci.yml`），路径过滤 → 测试 → 构建镜像 → 部署。仅变更的组件触发对应流程，deploy 在有任一组件构建成功时执行。
- **定时爬取**：服务器 crontab 每周六 7:00 AM 执行 `docker compose run --rm crawler -c <最新学期>`，自动同步最新课程数据。

## 许可证

GLWTPL (Good Luck With That Public License)
