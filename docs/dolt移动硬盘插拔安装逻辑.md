

---

# Dolt 纯绿色便携版完整指南  
**插上即用 · 拔了就走 · 多电脑无缝切换**

**特点**  
- 无需安装、无注册表、无污染系统  
- 数据 + 配置 + 程序全在移动硬盘  
- 支持 CLI + SQL Server 两种模式  
- 自动适配任意盘符（E:、F:、G:…）

## 推荐目录结构（移动硬盘根目录）

```
E:\
├── dolt\                  # Dolt 可执行文件（绿色版）
│   ├── dolt.exe
│   ├── git-dolt.exe
├── data\                  # 所有数据库数据（推荐）
│   ├── myproject\         # 数据库A（内含 .dolt/）
│   └── another_db\        # 数据库B
├── config\                # 全局配置（用户名、邮箱、凭证）
│   └── .dolt\             # 自动生成 config_global.json 等
└── start-dolt.bat         # 一键启动脚本（放根目录）
    start-server.bat
    init-db.bat
    setup-user.bat
```

## 步骤 1：准备文件夹

插入移动硬盘（假设盘符 E:），在**命令提示符**或 PowerShell 执行：

```cmd
E:
mkdir dolt data config
```

## 步骤 2：下载并解压 Dolt 绿色版

在**PowerShell**（管理员或普通均可）中执行：

```powershell
cd E:\dolt

# 下载最新版（自动跟随 latest）
Invoke-WebRequest -Uri "https://github.com/dolthub/dolt/releases/latest/download/dolt-windows-amd64.zip" -OutFile "dolt.zip"

# 解压
Expand-Archive -Path "dolt.zip" -DestinationPath "." -Force

# 清理压缩包（可选）
Remove-Item "dolt.zip"
```

**验证**：确保 `E:\dolt\dolt.exe` 和 `git-dolt.exe` 存在。若解压后文件在子文件夹（如 `bin\`），手动移动出来即可。

## 步骤 3：创建一键启动脚本

### 3.1 最简启动器（推荐）—— `E:\start-dolt.bat`

```batch
@echo off
chcp 65001 >nul
title Dolt Portable - CLI 模式

set "DOLT_DRIVE=%~d0"

echo ==========================================
echo    🗃️  Dolt 便携版启动器 (CLI)
echo    盘符: %DOLT_DRIVE%
echo ==========================================
echo.

:: 环境变量（完全隔离）
set "PATH=%DOLT_DRIVE%\dolt;%PATH%"
set "HOME=%DOLT_DRIVE%\config"

:: 进入数据目录
cd /d %DOLT_DRIVE%\data

echo ✅ 环境已配置完成！
echo 📂 数据目录: %CD%
echo 📁 配置目录: %HOME%\.dolt
echo.
echo 常用命令：
echo   dolt sql                  - 多数据库 SQL Shell（推荐）
echo   cd myproject ^&^& dolt sql  - 进入单个数据库并启动 SQL
echo   dolt version              - 查看版本
echo   dolt status               - 查看当前状态
echo.
echo 提示：输入 exit 退出当前命令窗口
echo.

cmd /k
```

### 3.2 带 SQL Server 的启动器 —— `E:\start-server.bat`

```batch
@echo off
chcp 65001 >nul
title Dolt SQL Server (Portable)

set "DOLT_DRIVE=%~d0"
set "PATH=%DOLT_DRIVE%\dolt;%PATH%"
set "HOME=%DOLT_DRIVE%\config"

cd /d %DOLT_DRIVE%\data

echo ==========================================
echo    Dolt SQL Server 便携版
echo    监听: 0.0.0.0:3306
echo    数据目录: %CD%
echo ==========================================
echo.

echo 正在启动服务器...（按 Ctrl+C 停止）
dolt sql-server --host 0.0.0.0 --port 3306 --data-dir "%CD%" --loglevel info
pause
```

### 3.3 初始化新数据库 —— `E:\init-db.bat`

```batch
@echo off
chcp 65001 >nul
set "DOLT_DRIVE=%~d0"
set "PATH=%DOLT_DRIVE%\dolt;%PATH%"
set "HOME=%DOLT_DRIVE%\config"

cd /d %DOLT_DRIVE%\data

set /p DBNAME=请输入数据库名称（英文）: 
if "%DBNAME%"=="" exit /b 1

mkdir "%DBNAME%" 2>nul
cd "%DBNAME%"

echo 正在初始化 %DBNAME% ...
dolt init

echo ✅ 数据库 %DBNAME% 创建完成！
pause
```

### 3.4 设置全局用户信息 —— `E:\setup-user.bat`

```batch
@echo off
chcp 65001 >nul
set "DOLT_DRIVE=%~d0"
set "PATH=%DOLT_DRIVE%\dolt;%PATH%"
set "HOME=%DOLT_DRIVE%\config"

cd /d %DOLT_DRIVE%\config

echo 设置 Dolt 用户信息（保存到移动硬盘）
set /p NAME=用户名: 
set /p EMAIL=邮箱: 

dolt config --global --add user.name "%NAME%"
dolt config --global --add user.email "%EMAIL%"

echo ✅ 配置已保存！
dolt config --global --list
pause
```

## 使用流程示例

**电脑 A（首次）**  
1. 插入硬盘 → 双击 `start-dolt.bat`  
2. 输入 `setup-user.bat` 设置用户名（只需一次）  
3. `dolt sql` 或运行 `init-db.bat` 创建数据库  
4. 创建表、提交：`dolt add . && dolt commit -m "init"`  
5. 关闭窗口 → 安全弹出硬盘

**电脑 B（后续）**  
1. 插入硬盘 → 双击 `start-dolt.bat`（自动识别新盘符）  
2. 直接 `dolt log`、`dolt sql` 继续工作

**连接其他工具**（Navicat、DBeaver、MySQL Workbench 等）  
- 主机：`127.0.0.1` 或本机IP  
- 端口：3306  
- 用户：`root`（默认空密码，建议在 SQL Shell 中 `CREATE USER` 设置密码）

## 性能与安全建议

- **接口**：优先 USB 3.0/3.1/Thunderbolt（蓝色接口）  
- **硬盘**：移动 SSD 体验最佳，机械硬盘也可  
- **安全弹出**：**必须**先关闭命令窗口，再右键“安全弹出”  
- **首次查询慢**：Dolt 会自动缓存，后续极快  
- **更新 Dolt**：重新下载 zip 覆盖 `dolt\` 文件夹即可

## 一句话总结

把 `dolt.exe` + 四个 `.bat` 脚本放移动硬盘，双击 `start-dolt.bat` 即可使用，所有数据和配置随身携带，完美实现“插上即用，拔了就走”。

---
