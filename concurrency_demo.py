import time
from concurrent.futures import ThreadPoolExecutor
import asyncio

def fetch_customer(customer_id):
    print(f"开始获取客户 {customer_id}")

    # 模拟等待外部服务，实际没有查询数据库。
    time.sleep(1)

    print(f"获取客户 {customer_id} 完成")
    return {"id": customer_id}

async def async_fetch_customer(customer_id):
    print(f"协程开始获取客户 {customer_id}")

    await asyncio.sleep(1)

    print(f"协程获取客户 {customer_id} 完成")
    return {"id": customer_id}


async def main():
    start = time.perf_counter()

    results = await asyncio.gather(
        async_fetch_customer(1),
        async_fetch_customer(2),
        async_fetch_customer(3),
    )

    print(results)
    print(f"协程耗时：{time.perf_counter() - start:.2f} 秒")


if __name__ == "__main__":
    print("顺序执行：")

    start = time.perf_counter()

    results = []
    for customer_id in (1, 2, 3):
        results.append(fetch_customer(customer_id))

    print(results)
    print(f"耗时：{time.perf_counter() - start:.2f} 秒")

    print("\n线程池执行：")

    start = time.perf_counter()

    with ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(fetch_customer, (1, 2, 3)))

    print(results)
    print(f"耗时：{time.perf_counter() - start:.2f} 秒")

    asyncio.run(main())