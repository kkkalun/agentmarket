# AgentMarket - AI Agent 模板聚合平台

> 一站式 AI Agent 模板发现、部署和管理平台

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-green)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0%2B-orange)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 项目简介

AgentMarket 是一个 AI Agent 模板聚合平台，帮助开发者和企业用户快速发现、部署和管理各类 AI Agent。平台提供丰富的 Agent 模板，涵盖对话助手、代码生成、数据分析、图像生成等多个领域，支持一键部署和自定义配置。

## 功能特性

- **Agent 模板市场** - 浏览、搜索、筛选各类 AI Agent 模板
- **分类与标签** - 按功能分类和技术标签快速定位所需 Agent
- **用户认证** - 完整的注册、登录、OAuth（GitHub）认证体系
- **开发者控制台** - 上传、管理和统计自己发布的 Agent 模板
- **订单系统** - 支持免费和付费 Agent 模板的交易管理
- **管理后台** - 用户管理、内容审核、平台数据统计
- **API 接口** - RESTful API，完整的 Swagger 文档
- **服务端渲染** - Jinja2 模板引擎，SEO 友好的页面渲染

## 技术栈

| 类别 | 技术 |
|------|------|
| 后端框架 | FastAPI |
| 数据库 ORM | SQLAlchemy 2.0 (异步) |
| 数据库 | SQLite (开发) / PostgreSQL (生产) |
| 数据库迁移 | Alembic |
| 数据验证 | Pydantic v2 |
| 模板引擎 | Jinja2 |
| 认证方案 | JWT + OAuth 2.0 |
| HTTP 客户端 | HTTPX |
| 容器化 | Docker |

## 快速开始

### 环境要求

- Python 3.10+
- pip 或 uv

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/kkkalun/agentmarket.git
cd agentmarket
```

2. **创建虚拟环境**
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. **安装依赖**
```bash
pip install -r requirements.txt
# 或使用 pyproject.toml
pip install -e .
```

4. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件，设置 SECRET_KEY 等必要参数
# 生成 SECRET_KEY：python -c "import secrets; print(secrets.token_urlsafe(32))"
```

5. **初始化数据库**
```bash
# 运行数据库迁移
alembic upgrade head

# 填充种子数据（可选）
python seed.py
```

6. **启动开发服务器**
```bash
python main.py
# 或使用 uvicorn
uvicorn main:app --reload --port 8000
```

访问 http://localhost:8000 查看应用，http://localhost:8000/docs 查看 API 文档。

## 项目结构

```
agentmarket/
├── main.py                 # 应用入口
├── seed.py                 # 数据库种子脚本
├── alembic.ini             # Alembic 配置
├── alembic/                # 数据库迁移目录
│   ├── env.py              # 迁移环境配置
│   ├── script.py.mako      # 迁移脚本模板
│   └── versions/           # 迁移版本文件
├── app/                    # 应用核心代码
│   ├── api/                # API 路由
│   │   ├── auth.py         # 认证接口
│   │   ├── agents.py       # Agent 接口
│   │   ├── orders.py       # 订单接口
│   │   └── admin.py        # 管理接口
│   ├── models/             # 数据模型
│   ├── schemas/            # Pydantic 数据模式
│   ├── services/           # 业务逻辑层
│   ├── middleware/         # 中间件
│   ├── utils/              # 工具函数
│   ├── config.py           # 应用配置
│   ├── database.py         # 数据库连接
│   └── exceptions.py       # 异常处理
├── templates/              # Jinja2 HTML 模板
├── static/                 # 静态资源文件
├── tests/                  # 测试文件
├── data/                   # 数据存储目录
├── pyproject.toml          # 项目元数据
├── requirements.txt        # 依赖列表
├── Dockerfile              # Docker 构建文件
├── docker-compose.yml      # Docker Compose 配置
└── .env.example            # 环境变量示例
```

## API 文档

启动应用后，访问以下地址查看自动生成的 API 文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 主要 API 端点

| 模块 | 前缀 | 说明 |
|------|------|------|
| 认证 | `/api/v1/auth` | 注册、登录、刷新令牌 |
| Agent | `/api/v1/agents` | Agent 模板 CRUD、搜索、下载 |
| 订单 | `/api/v1/orders` | 订单创建、查询、支付 |
| 管理 | `/api/v1/admin` | 用户管理、内容审核、统计 |

## 开发指南

### 代码规范

项目使用 Ruff 进行代码检查和格式化：
```bash
ruff check app/
ruff format app/
```

### 运行测试

```bash
pytest tests/ -v
```

### 数据库迁移

```bash
# 自动生成迁移脚本
alembic revision --autogenerate -m "描述信息"

# 应用迁移
alembic upgrade head

# 回滚到上一版本
alembic downgrade -1
```

### 使用 Makefile（Linux/Mac）

```bash
make install    # 安装依赖
make dev        # 启动开发服务器
make test       # 运行测试
make lint       # 代码检查
make migrate    # 数据库迁移
make seed       # 填充种子数据
make clean      # 清理缓存
```

## 部署指南

### Docker 部署

```bash
# 构建镜像
docker build -t agentmarket .

# 运行容器
docker run -d -p 8000:8000 \
  -v ./data:/app/data \
  --env-file .env \
  agentmarket
```

### Docker Compose 部署

```bash
# 先确保已复制并配置 .env 文件
cp .env.example .env
# 编辑 .env 设置 SECRET_KEY 等参数

docker-compose up -d
```

### 生产环境配置

生产环境部署时，请确保：

1. 在 `.env` 中设置强随机 `SECRET_KEY`（生成方式：`python -c "import secrets; print(secrets.token_urlsafe(32))"`)
2. 设置 `DEBUG=false`
3. 使用 PostgreSQL 替代 SQLite：`DATABASE_URL=postgresql+asyncpg://user:pass@host/db`
4. 配置反向代理（Nginx）处理 HTTPS
5. 使用 Gunicorn + Uvicorn workers 运行：
   ```bash
   gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
   ```

## 环境变量说明

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `APP_NAME` | 应用名称 | AgentMarket |
| `DEBUG` | 调试模式 | true |
| `SECRET_KEY` | JWT 签名密钥 | (必填，无默认值) |
| `DATABASE_URL` | 数据库连接 URL | sqlite+aiosqlite:///./dev.db |
| `JWT_ALGORITHM` | JWT 算法 | HS256 |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | 访问令牌过期时间（分钟） | 1440 |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | 刷新令牌过期时间（天） | 7 |
| `CORS_ORIGINS` | 允许的跨域来源 | ["http://localhost:3000", "http://localhost:8080"] |
| `API_PREFIX` | API 路径前缀 | /api/v1 |
| `RATE_LIMIT_PER_MINUTE` | 每分钟请求限制 | 100 |

## 默认账号

运行种子脚本 (`python seed.py`) 后，系统会自动生成管理员账号。初始密码可通过环境变量 `ADMIN_INITIAL_PASSWORD` 设置，若未设置则自动生成随机密码并打印在控制台。请在首次登录后立即修改密码。

## 许可证

本项目采用 [MIT 许可证](LICENSE) 开源。

## 联系我们

- **项目地址**: https://github.com/kkkalun/agentmarket
- **问题反馈**: https://github.com/kkkalun/agentmarket/issues

---

Made with ❤️ by AgentMarket Team
