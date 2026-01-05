"""
Demo API Test Script
====================
测试所有 Demo 演示中会用到的 API 端点。

运行方式:
    python scripts/demo/test_demo_apis.py

确保后端服务运行在 http://localhost:8000
"""

import asyncio
import sys
import os

# Fix Windows encoding issues
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from dataclasses import dataclass
from typing import Optional
import httpx

# 配置
BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
API_PREFIX = "/api/v1"

# Demo 账号凭证
DEMO_EMAIL = "demo@doxmind.com"
DEMO_PASSWORD = "DemoRadar2024!"


@dataclass
class TestResult:
    """测试结果"""
    name: str
    endpoint: str
    method: str
    passed: bool
    status_code: Optional[int] = None
    error: Optional[str] = None
    data: Optional[dict] = None


class DemoAPITester:
    """Demo API 测试器"""

    def __init__(self):
        self.client = httpx.AsyncClient(base_url=BASE_URL, timeout=30.0)
        self.access_token: Optional[str] = None
        self.results: list[TestResult] = []

        # 存储测试过程中的数据
        self.user_id: Optional[str] = None
        self.match_id: Optional[str] = None
        self.opportunity_id: Optional[str] = None
        self.pipeline_id: Optional[str] = None
        self.material_id: Optional[str] = None

    async def close(self):
        await self.client.aclose()

    def _auth_headers(self) -> dict:
        """获取认证头"""
        if self.access_token:
            return {"Authorization": f"Bearer {self.access_token}"}
        return {}

    async def _request(
        self,
        method: str,
        endpoint: str,
        name: str,
        **kwargs
    ) -> TestResult:
        """发送请求并记录结果"""
        url = f"{API_PREFIX}{endpoint}"
        try:
            # 添加认证头
            headers = kwargs.pop("headers", {})
            headers.update(self._auth_headers())

            response = await self.client.request(
                method, url, headers=headers, **kwargs
            )

            # 尝试解析 JSON
            data = None
            try:
                data = response.json()
            except:
                pass

            passed = 200 <= response.status_code < 300
            result = TestResult(
                name=name,
                endpoint=url,
                method=method,
                passed=passed,
                status_code=response.status_code,
                data=data,
                error=None if passed else str(data)
            )
        except Exception as e:
            result = TestResult(
                name=name,
                endpoint=url,
                method=method,
                passed=False,
                error=str(e)
            )

        self.results.append(result)
        return result

    # ==================== 1. 认证测试 ====================

    async def test_login(self) -> bool:
        """测试登录"""
        print("\n📝 测试登录...")
        result = await self._request(
            "POST",
            "/auth/login",
            "用户登录",
            data={"username": DEMO_EMAIL, "password": DEMO_PASSWORD}
        )

        if result.passed and result.data:
            self.access_token = result.data.get("access_token")
            print(f"   ✅ 登录成功，获取到 Token")
            return True
        else:
            print(f"   ❌ 登录失败: {result.error}")
            return False

    async def test_get_me(self) -> bool:
        """测试获取当前用户"""
        print("\n👤 测试获取当前用户信息...")
        result = await self._request("GET", "/auth/me", "获取当前用户")

        if result.passed and result.data:
            self.user_id = result.data.get("id")
            print(f"   ✅ 用户: {result.data.get('email')}")
            print(f"   ✅ 已完成Profile: {result.data.get('has_profile', False)}")
            return True
        else:
            print(f"   ❌ 获取用户失败: {result.error}")
            return False

    # ==================== 2. Dashboard 测试 ====================

    async def test_matches_stats(self) -> bool:
        """测试匹配统计"""
        print("\n📊 测试匹配统计 (Dashboard)...")
        result = await self._request("GET", "/matches/stats", "匹配统计")

        if result.passed and result.data:
            print(f"   ✅ 总匹配数: {result.data.get('total', 0)}")
            print(f"   ✅ 已收藏: {result.data.get('bookmarked', 0)}")
            print(f"   ✅ 已驳回: {result.data.get('dismissed', 0)}")
            print(f"   ✅ 活跃匹配: {result.data.get('active', 0)}")
            return True
        else:
            print(f"   ❌ 获取统计失败: {result.error}")
            return False

    async def test_top_matches(self) -> bool:
        """测试 Top 匹配"""
        print("\n🏆 测试 Top 匹配 (Dashboard)...")
        result = await self._request("GET", "/matches/top?limit=5", "Top 匹配")

        if result.passed and result.data:
            matches = result.data if isinstance(result.data, list) else result.data.get("items", [])
            print(f"   ✅ 返回 {len(matches)} 个高分匹配")
            if matches:
                # 保存第一个 match_id 用于后续测试
                self.match_id = matches[0].get("id")
                self.opportunity_id = matches[0].get("opportunity_id")
                top = matches[0]
                print(f"   ✅ 最高匹配分数: {top.get('overall_score', 0):.2%}")
            return True
        else:
            print(f"   ❌ 获取 Top 匹配失败: {result.error}")
            return False

    async def test_pipeline_stats(self) -> bool:
        """测试 Pipeline 统计"""
        print("\n📈 测试 Pipeline 统计 (Dashboard)...")
        result = await self._request("GET", "/pipelines/stats", "Pipeline 统计")

        if result.passed and result.data:
            print(f"   ✅ Pipeline 统计:")
            for stage, count in result.data.items():
                if isinstance(count, int):
                    print(f"      - {stage}: {count}")
            return True
        else:
            print(f"   ❌ 获取 Pipeline 统计失败: {result.error}")
            return False

    # ==================== 3. Opportunities 测试 ====================

    async def test_list_opportunities(self) -> bool:
        """测试机会列表"""
        print("\n🔍 测试机会列表...")
        result = await self._request(
            "GET",
            "/opportunities?limit=10",
            "机会列表"
        )

        if result.passed and result.data:
            items = result.data.get("items", result.data) if isinstance(result.data, dict) else result.data
            if isinstance(items, list):
                print(f"   ✅ 返回 {len(items)} 个机会")
                if items and not self.opportunity_id:
                    self.opportunity_id = items[0].get("id")
            return True
        else:
            print(f"   ❌ 获取机会列表失败: {result.error}")
            return False

    async def test_filter_opportunities(self) -> bool:
        """测试机会过滤"""
        print("\n🎯 测试机会过滤 (按类型)...")
        result = await self._request(
            "GET",
            "/opportunities?category=hackathon&limit=5",
            "过滤机会 (Hackathon)"
        )

        if result.passed:
            items = result.data.get("items", result.data) if isinstance(result.data, dict) else result.data
            count = len(items) if isinstance(items, list) else 0
            print(f"   ✅ Hackathon 类型: {count} 个")
            return True
        else:
            print(f"   ❌ 过滤机会失败: {result.error}")
            return False

    async def test_opportunity_detail(self) -> bool:
        """测试机会详情"""
        if not self.opportunity_id:
            print("\n📄 跳过机会详情测试 (无可用 opportunity_id)")
            return True

        print(f"\n📄 测试机会详情 (ID: {self.opportunity_id[:8]}...)...")
        result = await self._request(
            "GET",
            f"/opportunities/{self.opportunity_id}",
            "机会详情"
        )

        if result.passed and result.data:
            print(f"   ✅ 标题: {result.data.get('title', 'N/A')[:50]}")
            print(f"   ✅ 类型: {result.data.get('opportunity_type', 'N/A')}")
            return True
        else:
            print(f"   ❌ 获取机会详情失败: {result.error}")
            return False

    # ==================== 4. Matches 测试 ====================

    async def test_list_matches(self) -> bool:
        """测试匹配列表"""
        print("\n🎲 测试匹配列表...")
        result = await self._request("GET", "/matches?limit=10", "匹配列表")

        if result.passed and result.data:
            items = result.data.get("items", result.data) if isinstance(result.data, dict) else result.data
            if isinstance(items, list):
                print(f"   ✅ 返回 {len(items)} 个匹配")
                if items:
                    # 总是更新 match_id，确保我们有有效的 ID
                    self.match_id = items[0].get("id")
                    if not self.opportunity_id:
                        self.opportunity_id = items[0].get("opportunity_id")
                    print(f"   ✅ 获取 match_id: {self.match_id[:8] if self.match_id else 'N/A'}...")
            return True
        else:
            print(f"   ❌ 获取匹配列表失败: {result.error}")
            return False

    async def test_bookmark_match(self) -> bool:
        """测试收藏匹配"""
        if not self.match_id:
            print("\n⭐ 跳过收藏测试 (无可用 match_id)")
            return True

        print(f"\n⭐ 测试收藏匹配...")
        result = await self._request(
            "POST",
            f"/matches/{self.match_id}/bookmark",
            "收藏匹配"
        )

        if result.passed:
            print(f"   ✅ 收藏成功")
            return True
        else:
            # 可能已经收藏了
            print(f"   ⚠️ 收藏状态: {result.error}")
            return True

    async def test_unbookmark_match(self) -> bool:
        """测试取消收藏"""
        if not self.match_id:
            return True

        print(f"\n⭐ 测试取消收藏匹配...")
        result = await self._request(
            "POST",
            f"/matches/{self.match_id}/unbookmark",
            "取消收藏"
        )

        if result.passed:
            print(f"   ✅ 取消收藏成功")
        else:
            print(f"   ⚠️ 取消收藏状态: {result.error}")
        return True

    # ==================== 5. Pipeline 测试 ====================

    async def test_list_pipelines(self) -> bool:
        """测试 Pipeline 列表"""
        print("\n📋 测试 Pipeline 列表...")
        result = await self._request("GET", "/pipelines", "Pipeline 列表")

        if result.passed and result.data:
            items = result.data.get("items", result.data) if isinstance(result.data, dict) else result.data
            if isinstance(items, list):
                print(f"   ✅ 返回 {len(items)} 个 Pipeline 项")
                if items:
                    self.pipeline_id = items[0].get("id")
            return True
        else:
            print(f"   ❌ 获取 Pipeline 失败: {result.error}")
            return False

    async def test_create_pipeline(self) -> bool:
        """测试创建 Pipeline"""
        if not self.opportunity_id:
            print("\n➕ 跳过创建 Pipeline 测试 (无可用 opportunity_id)")
            return True

        print(f"\n➕ 测试创建 Pipeline...")
        result = await self._request(
            "POST",
            "/pipelines",
            "创建 Pipeline",
            json={
                "opportunity_id": self.opportunity_id,
                "stage": "discovered",
                "notes": "Demo 测试创建"
            }
        )

        if result.passed and result.data:
            self.pipeline_id = result.data.get("id")
            print(f"   ✅ 创建成功, ID: {self.pipeline_id[:8] if self.pipeline_id else 'N/A'}...")
            return True
        else:
            # 可能已经存在 (400 或 409)
            error_str = str(result.error).lower()
            if "already" in error_str or "exists" in error_str or result.status_code in [400, 409]:
                print(f"   ⚠️ Pipeline 已存在 (这是正常的)")
                # 将测试结果标记为通过（因为已存在也是预期的情况）
                result.passed = True
                result.error = None
                return True
            print(f"   ❌ 创建 Pipeline 失败: {result.error}")
            return False

    async def test_update_pipeline_stage(self) -> bool:
        """测试更新 Pipeline 阶段"""
        if not self.pipeline_id:
            print("\n🔄 跳过更新 Pipeline 阶段测试 (无可用 pipeline_id)")
            return True

        print(f"\n🔄 测试更新 Pipeline 阶段 (拖拽模拟)...")
        result = await self._request(
            "POST",
            f"/pipelines/{self.pipeline_id}/stage/preparing",
            "更新 Pipeline 阶段"
        )

        if result.passed:
            print(f"   ✅ 阶段更新为: preparing")
            return True
        else:
            print(f"   ❌ 更新阶段失败: {result.error}")
            return False

    # ==================== 6. Materials 测试 ====================

    async def test_list_materials(self) -> bool:
        """测试材料列表"""
        print("\n📚 测试材料列表...")
        result = await self._request("GET", "/materials?limit=10", "材料列表")

        if result.passed:
            items = result.data.get("items", result.data) if isinstance(result.data, dict) else result.data
            if isinstance(items, list):
                print(f"   ✅ 返回 {len(items)} 个材料")
                if items:
                    self.material_id = items[0].get("id")
            return True
        else:
            print(f"   ❌ 获取材料列表失败: {result.error}")
            return False

    async def test_generate_material(self) -> bool:
        """测试生成材料 (核心功能)"""
        print("\n✨ 测试 AI 材料生成 (核心功能)...")

        # 正确的请求格式，使用 project_info 嵌套对象
        result = await self._request(
            "POST",
            "/materials/generate",
            "生成材料 (3分钟演讲稿)",
            json={
                "targets": ["pitch_3min"],
                "language": "en",
                "project_info": {
                    "name": "DoxMind",
                    "problem": "开发者和团队每天花费大量时间阅读、搜索和理解技术文档，效率低下且容易遗漏关键信息。",
                    "solution": "DoxMind是一个AI驱动的文档助手，通过RAG技术实现智能问答，帮助用户快速获取文档中的关键信息，提升10倍阅读效率。",
                    "tech_stack": ["Next.js", "TypeScript", "Python", "FastAPI", "LLM", "RAG", "Vector Database"]
                },
                "opportunity_id": self.opportunity_id,
                "constraints": {
                    "highlight_demo": False,
                    "include_user_evidence": False
                }
            }
        )

        if result.passed and result.data:
            # 响应可能包含 pitch_md, readme_md 等字段
            pitch_content = result.data.get("pitch_md", "")
            readme_content = result.data.get("readme_md", "")
            content = pitch_content or readme_content or str(result.data)

            print(f"   ✅ 材料生成成功!")
            print(f"   ✅ 返回字段: {list(result.data.keys())}")
            if pitch_content:
                print(f"   ✅ Pitch 内容长度: {len(pitch_content)} 字符")
                preview = pitch_content[:100].replace('\n', ' ')
                print(f"   ✅ 预览: {preview}...")

            # 检查是否有错误
            errors = result.data.get("errors", [])
            if errors:
                print(f"   ⚠️ 生成过程有 {len(errors)} 个警告")
                for err in errors:
                    print(f"      - {err.get('target')}: {err.get('error')}")
            return True
        else:
            print(f"   ❌ 生成材料失败: {result.error}")
            return False

    # ==================== 7. Profile 测试 ====================

    async def test_get_profile(self) -> bool:
        """测试获取 Profile"""
        print("\n👤 测试获取用户 Profile...")
        result = await self._request("GET", "/profiles/me", "获取 Profile")

        if result.passed and result.data:
            print(f"   ✅ 显示名: {result.data.get('display_name', 'N/A')}")
            print(f"   ✅ 技术栈: {result.data.get('tech_stack', [])[:3]}...")
            print(f"   ✅ 团队名: {result.data.get('team_name', 'N/A')}")
            return True
        else:
            print(f"   ❌ 获取 Profile 失败: {result.error}")
            return False

    # ==================== 8. 通知测试 ====================

    async def test_notifications(self) -> bool:
        """测试通知"""
        print("\n🔔 测试通知...")
        result = await self._request("GET", "/notifications?limit=5", "获取通知")

        if result.passed:
            items = result.data.get("items", result.data) if isinstance(result.data, dict) else result.data
            if isinstance(items, list):
                print(f"   ✅ 返回 {len(items)} 条通知")
            return True
        else:
            print(f"   ❌ 获取通知失败: {result.error}")
            return False

    async def test_unread_count(self) -> bool:
        """测试未读通知数"""
        print("\n🔔 测试未读通知数...")
        result = await self._request("GET", "/notifications/unread-count", "未读通知数")

        if result.passed and result.data:
            count = result.data.get("count", result.data.get("unread_count", 0))
            print(f"   ✅ 未读通知: {count} 条")
            return True
        else:
            print(f"   ❌ 获取未读数失败: {result.error}")
            return False

    # ==================== 运行所有测试 ====================

    async def run_all_tests(self):
        """运行所有 Demo API 测试"""
        print("=" * 60)
        print("🚀 OpportunityRadar Demo API 测试")
        print("=" * 60)
        print(f"API 地址: {BASE_URL}")
        print(f"Demo 账号: {DEMO_EMAIL}")
        print("=" * 60)

        # 1. 认证测试
        print("\n" + "=" * 40)
        print("【第一幕】认证测试")
        print("=" * 40)
        if not await self.test_login():
            print("\n❌ 登录失败，无法继续测试!")
            return False
        await self.test_get_me()

        # 2. Dashboard 测试
        print("\n" + "=" * 40)
        print("【第二幕】Dashboard 测试")
        print("=" * 40)
        await self.test_matches_stats()
        await self.test_top_matches()
        await self.test_pipeline_stats()

        # 3. Opportunities 测试
        print("\n" + "=" * 40)
        print("【第三幕】Opportunities 测试")
        print("=" * 40)
        await self.test_list_opportunities()
        await self.test_filter_opportunities()
        await self.test_opportunity_detail()

        # 4. Matches 测试
        print("\n" + "=" * 40)
        print("【第三幕续】Matches 测试")
        print("=" * 40)
        await self.test_list_matches()
        await self.test_bookmark_match()
        await self.test_unbookmark_match()

        # 5. Pipeline 测试
        print("\n" + "=" * 40)
        print("【第四幕】Pipeline 测试")
        print("=" * 40)
        await self.test_list_pipelines()
        await self.test_create_pipeline()
        await self.test_update_pipeline_stage()

        # 6. Materials 测试
        print("\n" + "=" * 40)
        print("【第五幕】Materials 测试 (AI 生成)")
        print("=" * 40)
        await self.test_list_materials()
        await self.test_generate_material()

        # 7. Profile 测试
        print("\n" + "=" * 40)
        print("【第六幕】Profile 测试")
        print("=" * 40)
        await self.test_get_profile()

        # 8. 通知测试
        print("\n" + "=" * 40)
        print("【附加】通知测试")
        print("=" * 40)
        await self.test_notifications()
        await self.test_unread_count()

        # 打印测试结果汇总
        self._print_summary()

        return all(r.passed for r in self.results)

    def _print_summary(self):
        """打印测试结果汇总"""
        print("\n" + "=" * 60)
        print("📊 测试结果汇总")
        print("=" * 60)

        passed = sum(1 for r in self.results if r.passed)
        failed = len(self.results) - passed

        print(f"\n总计: {len(self.results)} 个测试")
        print(f"✅ 通过: {passed}")
        print(f"❌ 失败: {failed}")

        if failed > 0:
            print("\n失败的测试:")
            for r in self.results:
                if not r.passed:
                    print(f"  ❌ {r.name} [{r.method} {r.endpoint}]")
                    print(f"     状态码: {r.status_code}")
                    print(f"     错误: {r.error[:100] if r.error else 'N/A'}...")

        print("\n" + "=" * 60)
        if failed == 0:
            print("🎉 所有 Demo API 测试通过! 可以开始录制了!")
        else:
            print(f"⚠️ 有 {failed} 个测试失败，请检查后再录制")
        print("=" * 60)


async def main():
    """主函数"""
    tester = DemoAPITester()
    try:
        success = await tester.run_all_tests()
        sys.exit(0 if success else 1)
    finally:
        await tester.close()


if __name__ == "__main__":
    asyncio.run(main())
