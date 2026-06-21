# 贡献指南

感谢你对 AgentMarket 项目的关注！我们欢迎各种形式的贡献。

## 如何贡献

### 报告 Bug

如果你发现了 Bug，请通过 [GitHub Issues](../../issues) 报告，并包含以下信息：

- Bug 的详细描述
- 复现步骤
- 预期行为与实际行为
- 运行环境信息（Python 版本、操作系统等）

### 提交功能建议

如果你有好的功能建议，同样欢迎通过 Issues 提出。请描述：

- 功能的用途和场景
- 期望的行为
- 可能的实现思路（可选）

### 提交代码（Pull Request）

1. Fork 本仓库
2. 创建你的功能分支 (`git checkout -b feature/amazing-feature`)
3. 确保代码通过测试和 lint 检查
4. 提交你的修改 (`git commit -m 'Add some amazing feature'`)
5. 推送到分支 (`git push origin feature/amazing-feature`)
6. 创建 Pull Request

## 开发环境搭建

```bash
# 克隆项目
git clone https://github.com/kkkalun/agentmarket.git
cd agentmarket

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装开发依赖
pip install -r requirements-dev.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件设置 SECRET_KEY
```

## 代码规范

- 使用 Ruff 进行代码检查和格式化
- 遵循 PEP 8 编码规范
- 所有新增功能需要附带测试
- 提交信息应清晰描述变更内容

```bash
# 代码检查
ruff check app/

# 格式化
ruff format app/

# 运行测试
pytest tests/ -v
```

## 许可证

通过贡献代码，你同意你的贡献将在 MIT 许可证下发布。
