.PHONY: install dev build test lint migrate seed clean

# 安装依赖
install:
	pip install -r requirements.txt

# 启动开发服务器
dev:
	python main.py

# 运行测试
test:
	pytest tests/ -v

# 代码检查
lint:
	ruff check app/

# 数据库迁移
migrate:
	alembic revision --autogenerate -m "auto migration"
	alembic upgrade head

# 填充种子数据
seed:
	python seed.py

# 清理缓存文件
clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
