"""
服务启动脚本

提供简单的命令行界面启动各种服务

使用方法:
    python start.py api          # 启动 API 服务
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()


def check_env():
    """检查环境变量"""
    required = ["MINERU_API_KEY", "DS_API_KEY"]
    missing = [var for var in required if not os.getenv(var)]
    
    if missing:
        print("❌ 缺少必需的环境变量:")
        for var in missing:
            print(f"   - {var}")
        print("\n请在 .env 文件中设置这些变量，或导出到环境变量")
        return False
    
    print("✅ 环境变量检查通过")
    return True


def start_api(host="0.0.0.0", port=8000, reload=True):
    """启动 API 服务"""
    print(f"🚀 启动 API 服务...")
    print(f"   地址: http://{host}:{port}")
    print(f"   文档: http://{host}:{port}/docs")
    
    # 判断当前是否在 services 目录内
    current_dir = Path.cwd().name
    if current_dir == "services":
        # 在 services 目录内，使用相对导入
        app_module = "api.server:app"
    else:
        # 在项目根目录，使用完整路径
        app_module = "services.api.server:app"
    
    cmd = [
        sys.executable, "-m", "uvicorn",
        app_module,
        "--host", host,
        "--port", str(port),
    ]
    
    if reload:
        cmd.append("--reload")
    
    subprocess.run(cmd)


def start_worker(queues="pdf_processing,default", concurrency=4):
    """启动 Celery Worker"""
    print(f"🚀 启动 Celery Worker...")
    print(f"   队列: {queues}")
    print(f"   并发数: {concurrency}")
    
    # 判断当前是否在 services 目录内
    current_dir = Path.cwd().name
    if current_dir == "services":
        celery_app = "legacy.celery_config"
    else:
        celery_app = "services.legacy.celery_config"
    
    cmd = [
        sys.executable, "-m", "celery",
        "-A", celery_app,
        "worker",
        "--loglevel=info",
        "-Q", queues,
        "--concurrency", str(concurrency),
        "-n", "worker@%h"
    ]
    
    subprocess.run(cmd)


def start_beat():
    """启动 Celery Beat"""
    print(f"🚀 启动 Celery Beat (定时任务)...")
    
    # 判断当前是否在 services 目录内
    current_dir = Path.cwd().name
    if current_dir == "services":
        celery_app = "legacy.celery_config"
    else:
        celery_app = "services.legacy.celery_config"
    
    cmd = [
        sys.executable, "-m", "celery",
        "-A", celery_app,
        "beat",
        "--loglevel=info",
        "--scheduler", "celery.beat.PersistentScheduler",
        "--schedule", "celerybeat-schedule.db"
    ]
    
    subprocess.run(cmd)


def start_flower(port=5555):
    """启动 Flower 监控"""
    print(f"🚀 启动 Flower 监控...")
    print(f"   地址: http://localhost:{port}")
    
    # 判断当前是否在 services 目录内
    current_dir = Path.cwd().name
    if current_dir == "services":
        celery_app = "legacy.celery_config"
    else:
        celery_app = "services.legacy.celery_config"
    
    cmd = [
        sys.executable, "-m", "celery",
        "-A", celery_app,
        "flower",
        f"--port={port}",
        "--loglevel=info"
    ]
    
    subprocess.run(cmd)


def start_all():
    """启动所有服务（使用多进程）"""
    import multiprocessing
    
    print("🚀 启动所有服务...")
    
    processes = []
    
    # 启动 API
    p_api = multiprocessing.Process(target=start_api, kwargs={"reload": False})
    p_api.start()
    processes.append(("API", p_api))
    
    # 启动 Worker
    p_worker = multiprocessing.Process(target=start_worker)
    p_worker.start()
    processes.append(("Worker", p_worker))
    
    # 启动 Beat
    p_beat = multiprocessing.Process(target=start_beat)
    p_beat.start()
    processes.append(("Beat", p_beat))
    
    # 启动 Flower
    p_flower = multiprocessing.Process(target=start_flower)
    p_flower.start()
    processes.append(("Flower", p_flower))
    
    print("\n✅ 所有服务已启动:")
    print("   - API: http://localhost:8000")
    print("   - Flower: http://localhost:5555")
    print("\n按 Ctrl+C 停止所有服务")
    
    try:
        for name, p in processes:
            p.join()
    except KeyboardInterrupt:
        print("\n🛑 停止所有服务...")
        for name, p in processes:
            p.terminate()
            p.join()
        print("✅ 所有服务已停止")


def main():
    parser = argparse.ArgumentParser(
        description="PDF 智能解析服务启动脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python start_server.py api              # 启动 API 服务
    python start_server.py api --port 8080  # 指定端口
    python start_server.py worker           # 启动 Worker
    python start_server.py worker -c 8      # 8 个并发 Worker
    python start_server.py all              # 启动所有服务
        """
    )
    
    parser.add_argument(
        "service",
        choices=["api", "worker", "beat", "flower", "all"],
        help="要启动的服务"
    )
    
    # API 参数
    parser.add_argument("--host", default="0.0.0.0", help="API 监听地址")
    parser.add_argument("--port", type=int, default=8000, help="API 端口")
    parser.add_argument("--no-reload", action="store_true", help="禁用热重载")
    
    # Worker 参数
    parser.add_argument("-c", "--concurrency", type=int, default=4, help="Worker 并发数")
    parser.add_argument("-Q", "--queues", default="pdf_processing,default", help="监听的队列")
    
    # Flower 参数
    parser.add_argument("--flower-port", type=int, default=5555, help="Flower 端口")
    
    args = parser.parse_args()
    
    # 检查环境变量
    if not check_env():
        sys.exit(1)
    
    # 启动对应服务
    if args.service == "api":
        start_api(args.host, args.port, not args.no_reload)
    
    elif args.service == "worker":
        start_worker(args.queues, args.concurrency)
    
    elif args.service == "beat":
        start_beat()
    
    elif args.service == "flower":
        start_flower(args.flower_port)
    
    elif args.service == "all":
        start_all()


if __name__ == "__main__":
    main()

