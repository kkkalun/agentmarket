"""
AgentMarket 数据库种子脚本
用于初始化开发环境所需的示例数据
运行方式: python seed.py

管理员初始密码可通过环境变量 ADMIN_INITIAL_PASSWORD 设置，
若未设置则自动生成随机密码并打印在控制台。
"""
import asyncio
import os
import secrets
import sys
from datetime import datetime, timezone
from pathlib import Path

# 确保可以导入 app 模块
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import engine, Base, async_session_factory
from app.models.user import User
from app.models.agent import AgentTemplate, Category, Tag, License
from app.models.misc import Promotion
from app.services.auth_service import hash_password


async def seed_database():
    """填充数据库种子数据"""
    print("=" * 50)
    print("  AgentMarket 数据库种子脚本")
    print("=" * 50)

    # 确保表已创建
    print("\n[1/7] 正在创建数据库表...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("  -> 数据库表创建完成")

    async with async_session_factory() as session:
        # ==================== 创建管理员用户 ====================
        print("\n[2/7] 正在创建默认管理员用户...")
        result = await session.execute(
            select(User).where(User.email == "admin@example.com")
        )
        admin_user = result.scalar_one_or_none()

        # 从环境变量读取初始密码，未设置则自动生成
        admin_password = os.environ.get("ADMIN_INITIAL_PASSWORD") or secrets.token_urlsafe(12)

        if admin_user is None:
            admin_user = User(
                username="admin",
                email="admin@example.com",
                password_hash=hash_password(admin_password),
                display_name="系统管理员",
                role="ADMIN",
                status="ACTIVE",
                subscription_plan="FREE",
            )
            session.add(admin_user)
            await session.flush()
            print(f"  -> 管理员用户创建成功")
            print(f"     邮箱: admin@example.com")
            print(f"     密码: {admin_password}")
            print("  ⚠️  请妥善保存此密码，首次登录后建议立即修改！")
        else:
            print("  -> 管理员用户已存在，跳过")

        # ==================== 创建分类 ====================
        print("\n[3/7] 正在创建 Agent 分类...")
        categories_data = [
            {"name": "对话助手", "slug": "chatbot", "icon": "chat-bubble", "sort_order": 1},
            {"name": "代码生成", "slug": "code-gen", "icon": "code", "sort_order": 2},
            {"name": "数据分析", "slug": "data-analysis", "icon": "chart", "sort_order": 3},
            {"name": "图像生成", "slug": "image-gen", "icon": "image", "sort_order": 4},
            {"name": "文本处理", "slug": "text-processing", "icon": "document-text", "sort_order": 5},
            {"name": "自动化工作流", "slug": "automation", "icon": "cog", "sort_order": 6},
            {"name": "知识问答", "slug": "qa", "icon": "help-circle", "sort_order": 7},
            {"name": "多模态", "slug": "multimodal", "icon": "layers", "sort_order": 8},
        ]

        categories = {}
        for cat_data in categories_data:
            result = await session.execute(
                select(Category).where(Category.slug == cat_data["slug"])
            )
            existing = result.scalar_one_or_none()
            if existing is None:
                category = Category(**cat_data)
                session.add(category)
                categories[cat_data["slug"]] = category
                print(f"  -> 分类 [{cat_data['name']}] 创建成功")
            else:
                categories[cat_data["slug"]] = existing
                print(f"  -> 分类 [{cat_data['name']}] 已存在，跳过")

        # ==================== 创建标签 ====================
        print("\n[4/7] 正在创建标签...")
        tags_data = [
            {"name": "LangChain", "slug": "langchain", "group_name": "framework"},
            {"name": "AutoGen", "slug": "autogen", "group_name": "framework"},
            {"name": "CrewAI", "slug": "crewai", "group_name": "framework"},
            {"name": "LlamaIndex", "slug": "llama-index", "group_name": "framework"},
            {"name": "OpenAI", "slug": "openai", "group_name": "provider"},
            {"name": "Anthropic", "slug": "anthropic", "group_name": "provider"},
            {"name": "Python", "slug": "python", "group_name": "language"},
            {"name": "TypeScript", "slug": "typescript", "group_name": "language"},
            {"name": "RAG", "slug": "rag", "group_name": "technique"},
            {"name": "Function Calling", "slug": "function-calling", "group_name": "technique"},
            {"name": "Multi-Agent", "slug": "multi-agent", "group_name": "technique"},
            {"name": "Prompt Engineering", "slug": "prompt-engineering", "group_name": "technique"},
        ]

        tags = {}
        for tag_data in tags_data:
            result = await session.execute(
                select(Tag).where(Tag.slug == tag_data["slug"])
            )
            existing = result.scalar_one_or_none()
            if existing is None:
                tag = Tag(**tag_data)
                session.add(tag)
                tags[tag_data["slug"]] = tag
                print(f"  -> 标签 [{tag_data['name']}] 创建成功")
            else:
                tags[tag_data["slug"]] = existing
                print(f"  -> 标签 [{tag_data['name']}] 已存在，跳过")

        # ==================== 创建许可证 ====================
        print("\n[5/7] 正在创建开源许可证...")
        licenses_data = [
            {"name": "MIT License", "spdx_id": "MIT", "allows_commercial_use": True, "requires_disclosure": False, "description": "宽松开源许可证，允许商业使用、修改和分发"},
            {"name": "Apache License 2.0", "spdx_id": "Apache-2.0", "allows_commercial_use": True, "requires_disclosure": False, "description": "允许商业使用，要求保留版权声明和许可证副本"},
            {"name": "GNU GPL v3.0", "spdx_id": "GPL-3.0", "allows_commercial_use": True, "requires_disclosure": True, "description": "强 Copyleft 许可证，衍生作品必须以相同许可证发布"},
            {"name": "BSD 3-Clause", "spdx_id": "BSD-3-Clause", "allows_commercial_use": True, "requires_disclosure": False, "description": "宽松许可证，禁止使用贡献者名称进行推广"},
        ]

        licenses = {}
        for lic_data in licenses_data:
            result = await session.execute(
                select(License).where(License.spdx_id == lic_data["spdx_id"])
            )
            existing = result.scalar_one_or_none()
            if existing is None:
                license_obj = License(**lic_data)
                session.add(license_obj)
                licenses[lic_data["spdx_id"]] = license_obj
                print(f"  -> 许可证 [{lic_data['name']}] 创建成功")
            else:
                licenses[lic_data["spdx_id"]] = existing
                print(f"  -> 许可证 [{lic_data['name']}] 已存在，跳过")

        # ==================== 创建示例 Agent 模板 ====================
        print("\n[6/7] 正在创建示例 Agent 模板...")
        agents_data = [
            {
                "name": "智能客服助手",
                "slug": "smart-customer-service",
                "short_description": "基于 LangChain 的智能客服系统，支持多轮对话和知识库检索",
                "description": "基于 LangChain 和 RAG 的智能客服系统，支持多轮对话、知识库检索和意图识别。可快速集成到企业客服场景中，提供 7x24 小时自动问答服务。",
                "category_slug": "chatbot",
                "license_spdx": "MIT",
                "tag_slugs": ["langchain", "rag", "openai", "python"],
                "github_repo_url": "https://github.com/example/smart-cs-agent",
                "deploy_type": "DOCKER",
                "pricing_model": "FREE",
                "base_price": 0.0,
                "is_featured": True,
                "status": "PUBLISHED",
                "github_stars": 892,
                "total_deployments": 3580,
                "avg_rating": 4.6,
            },
            {
                "name": "代码审查大师",
                "slug": "code-review-master",
                "short_description": "自动化代码审查工具，支持多语言，检测安全和性能问题",
                "description": "自动化代码审查 Agent，支持 Python、TypeScript、Go 等主流语言。能够分析代码质量、安全漏洞、性能问题，并给出详细的改进建议和修复方案。",
                "category_slug": "code-gen",
                "license_spdx": "Apache-2.0",
                "tag_slugs": ["openai", "function-calling", "python", "typescript"],
                "github_repo_url": "https://github.com/example/code-review-agent",
                "deploy_type": "DOCKER",
                "pricing_model": "FREE",
                "base_price": 0.0,
                "is_featured": True,
                "status": "PUBLISHED",
                "github_stars": 1456,
                "total_deployments": 5200,
                "avg_rating": 4.8,
            },
            {
                "name": "数据分析工作台",
                "slug": "data-analysis-workbench",
                "short_description": "自然语言驱动的数据分析工具，自动生成图表和报告",
                "description": "一站式数据分析 Agent，支持 CSV/Excel 数据导入、自动统计分析、生成可视化图表和洞察报告。",
                "category_slug": "data-analysis",
                "license_spdx": "MIT",
                "tag_slugs": ["langchain", "openai", "python", "rag"],
                "github_repo_url": "https://github.com/example/data-workbench",
                "deploy_type": "CLOUD",
                "pricing_model": "PAID",
                "base_price": 29.9,
                "is_featured": False,
                "status": "PUBLISHED",
                "github_stars": 678,
                "total_deployments": 2890,
                "avg_rating": 4.3,
            },
            {
                "name": "多 Agent 协作框架",
                "slug": "multi-agent-collab",
                "short_description": "CrewAI 多角色协作框架，支持复杂工作流编排",
                "description": "基于 CrewAI 的多 Agent 协作框架，支持定义多个角色，通过任务编排实现复杂工作流的自动化执行。",
                "category_slug": "automation",
                "license_spdx": "MIT",
                "tag_slugs": ["crewai", "multi-agent", "openai", "python"],
                "github_repo_url": "https://github.com/example/multi-agent-collab",
                "deploy_type": "DOCKER",
                "pricing_model": "FREE",
                "base_price": 0.0,
                "is_featured": True,
                "status": "PUBLISHED",
                "github_stars": 445,
                "total_deployments": 1250,
                "avg_rating": 4.1,
            },
            {
                "name": "文档智能问答",
                "slug": "doc-smart-qa",
                "short_description": "LlamaIndex 文档问答系统，支持多种格式文档解析",
                "description": "基于 LlamaIndex 的文档智能问答系统，支持 PDF、Word、网页等多种文档格式的解析和索引。",
                "category_slug": "qa",
                "license_spdx": "Apache-2.0",
                "tag_slugs": ["llama-index", "rag", "anthropic", "python"],
                "github_repo_url": "https://github.com/example/doc-smart-qa",
                "deploy_type": "DOCKER",
                "pricing_model": "FREEMIUM",
                "base_price": 9.9,
                "is_featured": False,
                "status": "PUBLISHED",
                "github_stars": 1023,
                "total_deployments": 4100,
                "avg_rating": 4.5,
            },
        ]

        for agent_data in agents_data:
            result = await session.execute(
                select(AgentTemplate).where(AgentTemplate.slug == agent_data["slug"])
            )
            existing = result.scalar_one_or_none()

            if existing is None:
                # 解析关联关系
                category_slug = agent_data.pop("category_slug")
                license_spdx = agent_data.pop("license_spdx")
                tag_slugs = agent_data.pop("tag_slugs")

                # 设置作者为管理员
                agent_data["author_id"] = admin_user.id
                agent_data["category_id"] = categories[category_slug].id
                agent_data["license_id"] = licenses[license_spdx].id

                agent = AgentTemplate(**agent_data)
                session.add(agent)
                print(f"  -> Agent [{agent_data['name']}] 创建成功")
            else:
                print(f"  -> Agent [{agent_data['name']}] 已存在，跳过")

        # ==================== 提交事务 ====================
        print("\n[7/7] 正在提交数据...")
        await session.commit()
        print("  -> 所有数据提交成功！")

    print("\n" + "=" * 50)
    print("  种子数据填充完成！")
    print("  管理员账号: admin@example.com")
    print(f"  管理员密码: {admin_password}")
    print("  ⚠️  请妥善保存此密码，首次登录后建议立即修改！")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(seed_database())
