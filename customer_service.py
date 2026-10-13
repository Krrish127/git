class CustomerInputError(ValueError):
    pass


def validate_customer_input(data):
    if not isinstance(data, dict):
        raise CustomerInputError("请求体必须是 JSON 对象")

    name = data.get("name")
    industry = data.get("industry")

    if not isinstance(name, str) or not name.strip():
        raise CustomerInputError("name 必须是非空字符串")

    if not isinstance(industry, str) or not industry.strip():
        raise CustomerInputError("industry 必须是非空字符串")

    name = name.strip()
    industry = industry.strip()

    if len(name) > 100:
        raise CustomerInputError("name 不能超过 100 个字符")

    if len(industry) > 50:
        raise CustomerInputError("industry 不能超过 50 个字符")

    return {
        "name": name,
        "industry": industry,
    }