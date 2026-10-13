def change(customer):
    customer["name"] = "乙公司"
    customer = {"name": "丙公司"}


data = {"name": "甲公司"}
change(data)

print(data)