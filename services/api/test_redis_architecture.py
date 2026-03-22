"""
轻量化 Redis 进度架构测试脚本

测试内容:
1. Redis 连接测试
2. 任务创建和进度更新测试
3. 任务列表查询测试
4. WebSocket 处理器初始化测试

运行方式:
    python services/api/test_redis_architecture.py

需要先启动 Redis:
    redis-server
"""

import sys
import time
import asyncio
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from services.api.progress_store import RedisProgressStore, get_progress_store
from services.api.websocket_handler import WebSocketProgressHandler


def test_redis_connection():
    """测试 Redis 连接"""
    print("\n" + "=" * 60)
    print("测试 1: Redis 连接")
    print("=" * 60)
    
    try:
        store = RedisProgressStore()
        if store.ping():
            print("[OK] Redis 连接成功")
            return True
        else:
            print("[FAIL] Redis 连接失败")
            return False
    except Exception as e:
        print(f"[FAIL] Redis 连接错误: {e}")
        print("  请确保 Redis 已启动: redis-server")
        return False


def test_task_lifecycle():
    """测试任务生命周期"""
    print("\n" + "=" * 60)
    print("测试 2: 任务生命周期")
    print("=" * 60)
    
    store = RedisProgressStore()
    task_id = f"test_task_{int(time.time())}"
    
    # 1. 创建任务
    print("\n1. 创建任务...")
    task = store.create_task(task_id, "https://example.com/test.pdf")
    print(f"  任务 ID: {task_id}")
    print(f"  初始状态: {task['status']}")
    print(f"  初始进度: {task['overall_progress']}%")
    assert task["status"] == "pending"
    assert task["overall_progress"] == 5
    
    # 2. 更新进度
    print("\n2. 更新进度...")
    store.update_progress(
        task_id=task_id,
        stage="mineru",
        stage_progress=50,
        overall_progress=25,
        message="MinerU 解析中...",
        status="processing",
        mineru_data={"state": "running", "progress": 50, "current_page": 5, "total_pages": 10}
    )
    
    task = store.get_task(task_id)
    print(f"  阶段: {task['stage']}")
    print(f"  阶段进度: {task['stage_progress']}%")
    print(f"  总体进度: {task['overall_progress']}%")
    print(f"  MinerU 状态: {task['mineru']['state']}")
    assert task["stage"] == "mineru"
    assert task["overall_progress"] == 25
    
    # 3. 完成任务
    print("\n3. 完成任务...")
    store.update_progress(
        task_id=task_id,
        stage="completed",
        stage_progress=100,
        overall_progress=100,
        message="处理完成",
        status="completed",
        result={"output_path": "/path/to/output.pdf", "extraction_count": 42}
    )
    
    task = store.get_task(task_id)
    print(f"  最终状态: {task['status']}")
    print(f"  结果: {task['result']}")
    assert task["status"] == "completed"
    assert task["result"]["extraction_count"] == 42
    
    # 4. 清理测试数据
    print("\n4. 清理测试数据...")
    store.delete_task(task_id)
    task = store.get_task(task_id)
    assert task is None
    print("  测试任务已删除")
    
    print("\n[OK] 任务生命周期测试通过")
    return True


def test_task_list():
    """测试任务列表"""
    print("\n" + "=" * 60)
    print("测试 3: 任务列表")
    print("=" * 60)
    
    store = RedisProgressStore()
    
    # 创建几个测试任务
    print("\n创建测试任务...")
    task_ids = []
    for i in range(3):
        task_id = f"test_list_{int(time.time())}_{i}"
        store.create_task(task_id, f"https://example.com/doc{i}.pdf")
        task_ids.append(task_id)
        time.sleep(0.1)  # 确保时间戳不同
    
    # 查询列表
    print("\n查询任务列表...")
    tasks = store.list_tasks(limit=10)
    print(f"  返回任务数: {len(tasks)}")
    
    # 验证排序（按时间倒序）
    if len(tasks) >= 2:
        assert tasks[0]["created_at"] >= tasks[1]["created_at"]
        print("  排序正确（按创建时间倒序）")
    
    # 清理
    print("\n清理测试任务...")
    for task_id in task_ids:
        store.delete_task(task_id)
    
    print("\n[OK] 任务列表测试通过")
    return True


def test_pubsub():
    """测试 PubSub 功能"""
    print("\n" + "=" * 60)
    print("测试 4: PubSub 发布订阅")
    print("=" * 60)
    
    store = RedisProgressStore()
    task_id = f"test_pubsub_{int(time.time())}"
    
    # 创建订阅
    print("\n1. 创建 PubSub 订阅...")
    pubsub = store.redis.pubsub()
    channel = store.get_pubsub_channel(task_id)
    pubsub.subscribe(channel)
    print(f"  订阅频道: {channel}")
    
    # 创建任务（会触发发布）
    print("\n2. 创建任务，触发发布...")
    store.create_task(task_id, "https://example.com/test.pdf")
    
    # 获取消息
    print("\n3. 接收消息...")
    message = pubsub.get_message(timeout=1)
    if message:
        print(f"  收到订阅确认: {message['type']}")
    
    # 等待并获取实际数据消息
    time.sleep(0.5)
    message = pubsub.get_message(timeout=1)
    if message and message["type"] == "message":
        import json
        data = json.loads(message["data"])
        print(f"  收到数据消息: {data.get('type')}")
        print(f"  任务状态: {data.get('status')}")
    
    # 清理
    pubsub.unsubscribe(channel)
    pubsub.close()
    store.delete_task(task_id)
    
    print("\n[OK] PubSub 测试通过")
    return True


def test_websocket_handler():
    """测试 WebSocket 处理器初始化"""
    print("\n" + "=" * 60)
    print("测试 5: WebSocket 处理器")
    print("=" * 60)
    
    try:
        handler = WebSocketProgressHandler()
        print("[OK] WebSocket 处理器初始化成功")
        return True
    except Exception as e:
        print(f"[FAIL] WebSocket 处理器初始化失败: {e}")
        return False


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("轻量化 Redis 进度架构测试")
    print("=" * 60)
    
    tests = [
        ("Redis 连接", test_redis_connection),
        ("任务生命周期", test_task_lifecycle),
        ("任务列表", test_task_list),
        ("PubSub 发布订阅", test_pubsub),
        ("WebSocket 处理器", test_websocket_handler),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n[FAIL] {name} 测试失败: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # 打印总结
    print("\n" + "=" * 60)
    print("测试结果总结")
    print("=" * 60)
    
    passed = sum(1 for _, r in results if r)
    failed = sum(1 for _, r in results if not r)
    
    for name, result in results:
        status = "[OK] 通过" if result else "[FAIL] 失败"
        print(f"  {status}: {name}")
    
    print(f"\n总计: {passed} 通过, {failed} 失败")
    
    if failed == 0:
        print("\n[SUCCESS] 所有测试通过！Redis 架构已就绪。")
        return 0
    else:
        print("\n[WARNING] 部分测试失败，请检查 Redis 连接和配置。")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
