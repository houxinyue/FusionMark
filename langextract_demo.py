import langextract as lx
from langextract.factory import ModelConfig  # 必须导入这个
from langextract.providers.openai import OpenAILanguageModel # 显式导入提供者
import textwrap
import os
from dotenv import load_dotenv
load_dotenv()

# 1. Define the prompt and extraction rules
def run_deepseek_extraction():
# 1. 定义提取规则
# 这里的指令要清晰地告诉 AI attributes 内部的结构
    prompt = textwrap.dedent("""\
        从文本中提取个人的基本信息和工作经历。
        每个提取对象应包含以下属性：
        - name: 姓名
        - date: 出生日期
        - work_list: 一个数组，包含工作经历。
        每个工作经历对象包含：
        - name: 公司或项目名称
        - desc: 详细的工作描述
        - date: 工作时间范围
        """)

    # 2. 提供参考示例
    examples = [
        lx.data.ExampleData(
            # text 建议保留一点原文的样式
            text="姓 名 小帅,出生年月 1999 年 11 月 25 日,2021 年 7 月~2022 年 5 月 在亚信科技公司实习...",
            extractions=[
                lx.data.Extraction(
                    extraction_class="resume_info", # 给这个类起个名字
                    extraction_text="姓 名 小帅,出生年月 1999 年 11 月 25 日,2021 年 7 月~2022 年 5 月 在亚信科技公司实习", # 对应被提取的文本范围
                    attributes={
                        "name": "小帅",
                        "date": "1999-11-25",
                        "work_list": [
                            {
                                "name": "亚信科技公司",
                                "desc": "担任后端开发，负责三大资源可视、渠道数字化、大屏打点热力图等模块。使用SpringBoot+SpringCloud+Redis+Es等技术。",
                                "date": "2021年7月~2022年5月"
                            }
                        ]
                    }
                )
            ]
        )
    ]


    print("正在调用 DeepSeek 进行提取，请稍候...")

    try:
        # 4. 执行提取
        # 注意：对于 DeepSeek，我们通常借用 openai 的 provider 逻辑
        result = lx.extract(
            examples = examples,
            text_or_documents=r"file:///D:/%E9%87%8D%E8%A6%81%E6%96%87%E6%A1%A3/%E7%AE%80%E5%8E%86-20260122.pdf",
            prompt_description=prompt,
            config=ModelConfig(
                model_id="deepseek-chat",
                provider="OpenAILanguageModel",
                provider_kwargs={
                    "api_key":os.getenv("DS_API_KEY"),
                    "base_url":os.getenv("DS_API_BASE_URL")
                }
            )
        )
        # 5. 保存结果到本地 JSONL 文件
        output_file = "extraction_results.jsonl"
        lx.io.save_annotated_documents([result], output_name=output_file, output_dir=".")
        print(f"提取完成！结果已保存至: {output_file}")

        # 6. 生成可视化 HTML 文件
        # 这样你就能在浏览器里看到漂亮的带颜色标注的文本了
        html_content = lx.visualize(output_file)
        
        with open("visualization.html", "w", encoding="utf-8") as f:
            if hasattr(html_content, 'data'):
                f.write(html_content.data)
            else:
                f.write(str(html_content))
        
        print("可视化页面已生成：visualization.html (请用浏览器打开查看)")

    except Exception as e:
        print(f"运行出错: {e}")

if __name__ == "__main__":
    run_deepseek_extraction()

