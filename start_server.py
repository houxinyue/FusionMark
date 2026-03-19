#!/usr/bin/env python
"""
服务启动快捷入口

在项目根目录运行:
    python start_server.py api        # 启动 API 服务
    python start_server.py --help     # 查看帮助
"""

import sys
import subprocess

if __name__ == "__main__":
    # 使用 python -m 方式运行，确保 services 包能被正确识别
    result = subprocess.run([sys.executable, "-m", "services.start"] + sys.argv[1:])
    sys.exit(result.returncode)
