def make_numbers():
    print("准备产生 1")
    yield 1

    print("准备产生 2")
    yield 2

    print("准备产生 3")
    yield 3
numbers = make_numbers()

print("生成器已经创建")

print(next(numbers))
print(next(numbers))
print(next(numbers))

from contextlib import contextmanager


@contextmanager
def managed_resource():
    print("准备资源")

    try:
        yield "练习资源"
    finally:
        print("清理资源")


with managed_resource() as resource:
    print("正在使用：", resource)