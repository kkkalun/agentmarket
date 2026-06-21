"""
GitHub API 服务模块

使用 httpx 异步调用 GitHub REST API，获取仓库信息、README 内容，
并同步 Agent 模板的 GitHub 元数据（Stars、Forks 等）。
"""

import re
from typing import Optional

import httpx

from app.config import settings

# GitHub API 基础地址
_GITHUB_API_BASE = "https://api.github.com"


def _parse_owner_repo(repo_url: str) -> Optional[tuple[str, str]]:
    """
    从 GitHub 仓库 URL 中解析出 owner 和 repo 名称。

    支持的格式：
    - https://github.com/owner/repo
    - https://github.com/owner/repo.git
    - git@github.com:owner/repo.git

    返回：
        (owner, repo) 元组，解析失败返回 None
    """
    # HTTPS 格式
    match = re.match(
        r"https?://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$", repo_url
    )
    if match:
        return match.group(1), match.group(2)

    # SSH 格式
    match = re.match(r"git@github\.com:([^/]+)/([^/]+?)(?:\.git)?$", repo_url)
    if match:
        return match.group(1), match.group(2)

    return None


async def _get_headers() -> dict[str, str]:
    """
    构建 GitHub API 请求头部。

    如果配置了 GitHub OAuth 凭据，则附带 Authorization 头以提高速率限制。
    """
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "AgentMarket/1.0",
    }
    # 使用 Personal Access Token 提高速率限制（如果配置了）
    # 注意：GITHUB_CLIENT_SECRET 用于 OAuth 流程，不应作为 PAT 使用
    # 如需 API 认证，请在 .env 中配置 GITHUB_TOKEN
    github_token = getattr(settings, 'GITHUB_TOKEN', '')
    if github_token:
        headers["Authorization"] = f"token {github_token}"
    return headers


async def get_repo_info(repo_url: str) -> Optional[dict]:
    """
    获取 GitHub 仓库的基本信息。

    参数：
        repo_url: GitHub 仓库 URL

    返回：
        包含 stars、forks、description、language 等信息的字典，
        请求失败或解析失败时返回 None。
    """
    parsed = _parse_owner_repo(repo_url)
    if not parsed:
        return None

    owner, repo = parsed
    url = f"{_GITHUB_API_BASE}/repos/{owner}/{repo}"

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            headers = await _get_headers()
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()

            return {
                "stars": data.get("stargazers_count", 0),
                "forks": data.get("forks_count", 0),
                "description": data.get("description", ""),
                "language": data.get("language", ""),
                "topics": data.get("topics", []),
                "license": data.get("license", {}).get("spdx_id", "") if data.get("license") else None,
                "homepage": data.get("homepage", ""),
                "updated_at": data.get("updated_at", ""),
            }
        except (httpx.HTTPError, Exception):
            return None


async def get_readme(repo_url: str) -> Optional[str]:
    """
    获取 GitHub 仓库的 README 内容（Markdown 格式）。

    参数：
        repo_url: GitHub 仓库 URL

    返回：
        README 的原始 Markdown 文本，请求失败时返回 None。
    """
    parsed = _parse_owner_repo(repo_url)
    if not parsed:
        return None

    owner, repo = parsed
    url = f"{_GITHUB_API_BASE}/repos/{owner}/{repo}/readme"

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            headers = await _get_headers()
            # 请求原始内容（非 base64 编码）
            headers["Accept"] = "application/vnd.github.v3.raw"
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.text
        except (httpx.HTTPError, Exception):
            return None


async def sync_metadata(agent_template_id: str) -> bool:
    """
    同步指定 Agent 模板的 GitHub 仓库元数据。

    从 GitHub API 拉取最新的 stars、forks 等数据并更新数据库。

    参数：
        agent_template_id: Agent 模板 ID

    返回：
        同步成功返回 True，失败返回 False

    注意：
        此方法需要在有数据库会话上下文中调用。
        当前为骨架实现，实际使用时需注入 db 会话。
    """
    # TODO: 注入数据库会话，查询 AgentTemplate，调用 get_repo_info 并更新
    # 示例流程：
    # 1. agent = await db.get(AgentTemplate, agent_template_id)
    # 2. if not agent.github_repo_url: return False
    # 3. info = await get_repo_info(agent.github_repo_url)
    # 4. if not info: return False
    # 5. agent.github_stars = info["stars"]
    # 6. agent.github_forks = info["forks"]
    # 7. await db.flush()
    # 8. return True
    return False
