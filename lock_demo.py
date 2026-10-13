import threading
from concurrent.futures import ThreadPoolExecutor


balance = 1000
balance_lock = threading.Lock()


def safe_withdraw(amount):
    global balance

    with balance_lock:
        if balance < amount:
            return False

        old_balance = balance
        balance = old_balance - amount

        return True


if __name__ == "__main__":
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(safe_withdraw, (100, 200)))

    print("两次扣款结果：", results)
    print("最终余额：", balance)