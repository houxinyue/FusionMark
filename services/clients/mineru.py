"""
MinerU Client - 文档解析工具类

用于调用 MinerU API 进行文档解析，支持 PDF、Word、PPT、图片、HTML 等格式。
功能包括：创建解析任务、轮询任务状态、下载结果、解压提取 Markdown 内容。

使用示例:
    >>> from mineru_client import MinerUClient
    >>> client = MinerUClient()
    >>> result = client.process_document("https://example.com/file.pdf")
    >>> print(result["content"])

环境变量:
    MINERU_API_KEY: MinerU API 密钥（必需）

作者: AI Assistant
日期: 2026-02-04
"""

import os
import time
import zipfile
import requests
from pathlib import Path
from typing import Optional, Dict, List
from dataclasses import dataclass
from dotenv import load_dotenv

# 加载环境变量 (从 services/ 目录)
_ENV_PATH = Path(__file__).parent.parent / ".env"
if _ENV_PATH.exists():
    load_dotenv(_ENV_PATH)
else:
    load_dotenv()


@dataclass
class MinerUConfig:
    """MinerU 配置类"""
    api_key: str
    base_url: str = "https://mineru.net/api/v4/extract"
    output_dir: str = "./mineru_output"
    poll_interval: int = 3          # 轮询间隔（秒）
    max_poll_retries: int = 60      # 最大轮询次数，<=0 表示无限轮询
    download_timeout: int = 300     # 下载超时（秒）
    provider_mode: str = "open_sdk"
    sdk_base_url: str = "https://mineru.net/api/v4"
    sdk_token: str = ""
    sdk_token_env: str = "MINERU_API_KEY"
    sdk_extra_formats: Optional[List[str]] = None


@dataclass
class ParseResult:
    """解析结果数据类"""
    task_id: str
    state: str                      # done, failed, pending, running
    zip_url: str
    zip_path: str                   # 本地ZIP文件路径
    extract_dir: str                # 解压目录
    content: Optional[str] = None   # Markdown 内容
    error_msg: Optional[str] = None # 错误信息


class MinerUClient:
    """
    MinerU API 客户端
    
    提供文档解析的完整流程支持，包括任务创建、状态轮询、结果下载和内容提取。
    """
    
    # 模型版本常量
    MODEL_PIPELINE = "pipeline"      # 快速解析，默认
    MODEL_VLM = "vlm"                # 视觉语言模型，高精度
    MODEL_HTML = "MinerU-HTML"       # HTML 专用
    
    # 任务状态常量
    STATE_PENDING = "pending"
    STATE_RUNNING = "running"
    STATE_CONVERTING = "converting"
    STATE_DONE = "done"
    STATE_FAILED = "failed"
    
    def __init__(self, config: Optional[MinerUConfig] = None):
        """
        初始化客户端
        
        Args:
            config: 配置对象，None 时从环境变量自动创建
        """
        if config is None:
            api_key = os.getenv("MINERU_API_KEY")
            if not api_key:
                raise ValueError("环境变量 MINERU_API_KEY 未设置")
            config = MinerUConfig(api_key=api_key)
        
        self.config = config
        self.session = requests.Session()
    
    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.api_key}"
        }
    
    def create_task(
        self,
        url: str,
        model_version: str = MODEL_PIPELINE,
        is_ocr: bool = False,
        enable_formula: bool = True,
        enable_table: bool = True,
        language: str = "ch",
        data_id: Optional[str] = None,
        callback: Optional[str] = None,
        seed: Optional[str] = None,
        extra_formats: Optional[List[str]] = None,
        page_ranges: Optional[str] = None
    ) -> Optional[Dict]:
        """
        创建文档解析任务
        
        Args:
            url: 文件URL，支持 pdf/doc/docx/ppt/pptx/png/jpg/jpeg/html
            model_version: 模型版本，可选 pipeline/vlm/MinerU-HTML
            is_ocr: 是否启用 OCR（仅非HTML有效）
            enable_formula: 是否启用公式识别（仅非HTML有效）
            enable_table: 是否启用表格识别（仅非HTML有效）
            language: 文档语言，默认中文(ch)
            data_id: 业务数据ID（可选）
            callback: 回调通知URL（可选）
            seed: 回调签名随机字符串（可选）
            extra_formats: 额外导出格式，如 ["docx", "html"]
            page_ranges: 指定页码范围，如 "1-10" 或 "2,4-6"
            
        Returns:
            API响应字典，失败返回 None
            成功示例: {"code": 0, "data": {"task_id": "xxx"}, "msg": "ok"}
        """
        api_url = f"{self.config.base_url}/task"
        
        data = {"url": url, "model_version": model_version}
        
        # 非HTML文件添加专用参数
        if model_version != self.MODEL_HTML:
            data.update({
                "is_ocr": is_ocr,
                "enable_formula": enable_formula,
                "enable_table": enable_table,
                "language": language
            })
        
        # 添加可选参数
        for key, value in [
            ("data_id", data_id), ("callback", callback), ("seed", seed),
            ("extra_formats", extra_formats), ("page_ranges", page_ranges)
        ]:
            if value is not None:
                data[key] = value
        
        try:
            response = self.session.post(
                api_url, 
                headers=self._get_headers(), 
                json=data, 
                timeout=30
            )
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            print(f"[错误] 创建任务失败: {e}")
            return None
    
    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """
        查询任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            API响应字典，包含 state、progress、err_msg 等
        """
        url = f"{self.config.base_url}/task/{task_id}"
        
        try:
            response = self.session.get(
                url, 
                headers=self._get_headers(), 
                timeout=30
            )
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            print(f"[错误] 查询状态失败: {e}")
            return None
    
    def wait_for_completion(
        self, 
        task_id: str,
        verbose: bool = True,
        max_retries: Optional[int] = None,
        interval: Optional[int] = None,
        callback: Optional[callable] = None
    ) -> Optional[Dict]:
        """
        轮询等待任务完成
        
        Args:
            task_id: 任务ID
            verbose: 是否打印进度信息
            max_retries: 最大轮询次数，None 使用配置值，<=0 表示无限轮询
            interval: 轮询间隔秒数，None 使用配置值
            callback: 每轮轮询后的回调函数，接收 (attempt, state, data) 参数
                     返回 False 可提前终止轮询
            
        Returns:
            最终任务状态字典，超时/中断返回 None
        """
        # 使用传入参数或配置默认值
        max_retries = max_retries if max_retries is not None else self.config.max_poll_retries
        interval = interval if interval is not None else self.config.poll_interval
        
        # 判断是否无限轮询
        is_infinite = max_retries <= 0
        
        if verbose:
            mode = "无限轮询" if is_infinite else f"最多 {max_retries} 次"
            print(f"[轮询] 等待任务完成，间隔 {interval}秒，{mode}...")
        
        attempt = 0
        while is_infinite or attempt < max_retries:
            attempt += 1
            result = self.get_task_status(task_id)
            
            if not result or result.get("code") != 0:
                time.sleep(interval)
                continue
            
            data = result.get("data", {})
            state = data.get("state", "unknown")
            
            # 构建进度信息
            progress = data.get("extract_progress", {})
            page_info = ""
            if progress.get("total_pages"):
                page_info = f" [{progress['extracted_pages']}/{progress['total_pages']}页]"
            
            if verbose:
                attempt_str = f"第 {attempt} 次" if is_infinite else f"第 {attempt:2d}/{max_retries} 次"
                print(f"  {attempt_str} | 状态: {state:12s}{page_info}")
            
            # 执行回调函数（如果提供）
            if callback:
                try:
                    should_continue = callback(attempt, state, data)
                    if should_continue is False:
                        print(f"[轮询] 回调函数要求终止轮询")
                        return None
                except Exception as e:
                    print(f"[警告] 回调函数执行出错: {e}")
            
            # 任务完成或失败
            if state in (self.STATE_DONE, self.STATE_FAILED):
                return result
            
            time.sleep(interval)
        
        print(f"[警告] 轮询超时，已重试 {max_retries} 次")
        return None
    
    def download_result(
        self, 
        url: str, 
        save_path: str
    ) -> bool:
        """
        下载解析结果 ZIP 文件
        
        Args:
            url: ZIP 文件下载地址
            save_path: 本地保存路径
            
        Returns:
            下载成功返回 True
        """
        try:
            print(f"[下载] 开始下载结果文件...")
            
            response = self.session.get(
                url, 
                stream=True, 
                timeout=self.config.download_timeout
            )
            response.raise_for_status()
            
            # 确保目录存在
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            
            # 流式写入
            total_size = 0
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        total_size += len(chunk)
            
            size_mb = total_size / 1024 / 1024
            print(f"[下载] ✓ 完成，大小: {size_mb:.2f} MB")
            return True
            
        except Exception as e:
            print(f"[错误] 下载失败: {e}")
            return False
    
    @staticmethod
    def extract_zip(zip_path: str, extract_to: str) -> bool:
        """
        解压 ZIP 文件
        
        Args:
            zip_path: ZIP 文件路径
            extract_to: 解压目标目录
            
        Returns:
            解压成功返回 True
        """
        try:
            print(f"[解压] 解压到: {extract_to}")
            
            Path(extract_to).mkdir(parents=True, exist_ok=True)
            
            with zipfile.ZipFile(zip_path, 'r') as zf:
                print(f"[解压] 包含 {len(zf.namelist())} 个文件")
                zf.extractall(extract_to)
            
            print(f"[解压] ✓ 完成")
            return True
            
        except Exception as e:
            print(f"[错误] 解压失败: {e}")
            return False
    
    @staticmethod
    def read_markdown(extract_dir: str) -> Optional[str]:
        """
        读取解压目录中的 Markdown 内容
        
        MinerU 默认生成 full.md 作为主内容文件
        
        Args:
            extract_dir: 解压目录路径
            
        Returns:
            Markdown 文本内容，失败返回 None
        """
        # 可能的 Markdown 文件名
        candidates = ['full.md', 'result.md', 'output.md', 'content.md']
        
        # 查找文件
        md_path = None
        for root, dirs, files in os.walk(extract_dir):
            for file in files:
                if file.lower() in candidates:
                    md_path = os.path.join(root, file)
                    break
            if md_path:
                break
        
        if not md_path:
            print(f"[警告] 未找到 Markdown 文件")
            return None
        
        try:
            with open(md_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"[读取] ✓ 已读取 {len(content)} 字符")
            return content
            
        except Exception as e:
            print(f"[错误] 读取失败: {e}")
            return None
    
    def process_document(
        self,
        url: str,
        model_version: str = MODEL_VLM,
        wait_callback: Optional[callable] = None,
        **kwargs
    ) -> Optional[ParseResult]:
        """
        执行完整的文档解析流程
        
        流程: 创建任务 → 等待完成 → 下载 → 解压 → 提取内容
        
        Args:
            url: 文档 URL
            model_version: 模型版本，默认 vlm（高精度）
            wait_callback: 轮询回调函数，每轮调用，接收 (attempt, state, data)
            **kwargs: 传递给 create_task 的其他参数
            
        Returns:
            ParseResult 对象，包含解析结果和内容
        """
        print("=" * 60)
        print("MinerU 文档解析开始")
        print("=" * 60)
        print(f"文档: {url}")
        print(f"模型: {model_version}")
        print()
        
        # 1. 创建任务
        create_result = self.create_task(url=url, model_version=model_version, **kwargs)
        if not create_result or create_result.get("code") != 0:
            print("[错误] 任务创建失败")
            return None
        
        task_id = create_result["data"]["task_id"]
        print(f"[任务] ID: {task_id}")
        print()
        
        # 2. 等待完成（使用配置中的轮询策略）
        status_result = self.wait_for_completion(
            task_id=task_id,
            callback=wait_callback
        )
        if not status_result:
            return None
        
        data = status_result.get("data", {})
        state = data.get("state")
        
        if state == self.STATE_FAILED:
            error_msg = data.get("err_msg", "未知错误")
            print(f"[错误] 任务失败: {error_msg}")
            return ParseResult(
                task_id=task_id,
                state=state,
                zip_url="",
                zip_path="",
                extract_dir="",
                error_msg=error_msg
            )
        
        # 3. 下载结果
        zip_url = data.get("full_zip_url")
        if not zip_url:
            print("[错误] 未获取到下载地址")
            return None
        
        # 使用 task_id 作为目录名称，避免冲突
        # 目录结构: mineru_output/{task_id}/  (解压内容)
        #          mineru_output/{task_id}.zip (压缩包)
        output_base = Path(self.config.output_dir)
        output_base.mkdir(parents=True, exist_ok=True)
        
        zip_path = str(output_base / f"{task_id}.zip")
        extract_dir = str(output_base / task_id)
        
        if not self.download_result(zip_url, zip_path):
            return None
        
        # 4. 解压
        if not self.extract_zip(zip_path, extract_dir):
            return None
        
        # 5. 提取内容
        content = self.read_markdown(extract_dir)
        
        print()
        print("=" * 60)
        print("解析完成")
        print("=" * 60)
        
        return ParseResult(
            task_id=task_id,
            state=state,
            zip_url=zip_url,
            zip_path=zip_path,
            extract_dir=extract_dir,
            content=content
        )


def main():
    """使用示例"""
    
    # ========== 示例1: 基础使用 ==========
    print("=" * 60)
    print("示例1: 基础使用")
    print("=" * 60)
    
    client = MinerUClient()
      # 归脾丸 https://www.dayi.org.cn/drug/1146805.html
    result = client.process_document(
        url="https://www.dayi.org.cn/drug/1146805.html",
        model_version=MinerUClient.MODEL_HTML,
        is_ocr=True,
        enable_formula=True,
        enable_table=True
    )
    
    if result and result.content:
        print("\n提取内容预览（前500字符）:")
        print("-" * 60)
        print(result.content[:500])
        print(f"\n... (共 {len(result.content)} 字符)")
    


if __name__ == "__main__":
    main()
