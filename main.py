from openai import OpenAI

client = OpenAI(timeout=30.0, max_retries=0)

instructions = """
从用户输入中提取采购需求，只返回 JSON：
product：产品名称
quantity：采购数量
max_unit_price：单价上限，单位元
max_delivery_days：交货天数上限

缺失的信息返回 null，不要猜测。
不要输出额外解释或 Markdown 标记。
"""

print("正在请求模型……")

response = client.responses.create(
    model="gpt-4.1-mini",
    instructions=instructions,
    input="采购100个轴承，每个不超过50元，7天内交货。",
    max_output_tokens=300,
    store=False,
)

print("模型返回：")
print(response.output_text)