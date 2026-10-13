from decimal import Decimal


def normal_price(amount):
    return amount


def vip_price(amount):
    return amount * Decimal("0.9")


price_strategies = {
    "normal": normal_price,
    "vip": vip_price,
}


def calculate_price(amount, customer_type):
    strategy = price_strategies.get(customer_type)

    if strategy is None:
        raise ValueError("不支持的客户类型")

    return strategy(amount)


print(calculate_price(Decimal("100.00"), "normal"))
print(calculate_price(Decimal("100.00"), "vip"))