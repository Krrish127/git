import pymysql
import time
import secrets

from flask import Flask, jsonify, request, session
from werkzeug.security import generate_password_hash, check_password_hash
from customer_service import (
    CustomerInputError,
    validate_customer_input,
)

app = Flask(__name__)
app.json.ensure_ascii = False

# 本机单进程练习：每次启动生成一个随机签名密钥。
app.config["SECRET_KEY"] = secrets.token_hex(32)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# 固定的演示账号，不是真实用户数据库。
demo_user = {
    "id": 1,
    "username": "demo",
    "role": "admin",
    "password_hash": generate_password_hash(
        "Demo123456!",
        method="pbkdf2:sha256:600000",
    ),
}

def get_connection():
    return pymysql.connect(
        host="127.0.0.1",
        port=3306,
        user="root",
        password="",
        database="interview_crm_practice",
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
        connect_timeout=5,
    )


@app.route("/customers", methods=["GET"])
def list_customers():
    # 1. 读取并检查分页参数。
    try:
        page = int(request.args.get("page", "1"))
        page_size = int(request.args.get("page_size", "10"))
    except ValueError:
        return jsonify({
            "error": "page 和 page_size 必须是整数"
        }), 400

    if page < 1:
        return jsonify({"error": "page 必须大于等于 1"}), 400

    if page_size < 1 or page_size > 100:
        return jsonify({
            "error": "page_size 必须在 1 到 100 之间"
        }), 400

    offset = (page - 1) * page_size

    # 2. 读取可选的行业筛选条件。
    industry = request.args.get("industry")

    where_sql = ""
    filter_params = ()

    if industry is not None:
        industry = industry.strip()

        if not industry or len(industry) > 50:
            return jsonify({
                "error": "industry 必须是 1 到 50 个字符"
            }), 400

        where_sql = " WHERE industry = %s"
        filter_params = (industry,)

    connection = None

    try:
        connection = get_connection()

        with connection.cursor() as cursor:
            # 3. 统计符合筛选条件的客户总数。
            cursor.execute(
                "SELECT COUNT(*) AS total FROM customers"
                + where_sql,
                filter_params,
            )

            total = cursor.fetchone()["total"]

            # 4. 只查询当前页。
            cursor.execute(
                "SELECT id, name, industry FROM customers"
                + where_sql
                + " ORDER BY id LIMIT %s OFFSET %s",
                filter_params + (page_size, offset),
            )

            customers = cursor.fetchall()

        return jsonify({
            "data": customers,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (
                    total + page_size - 1
                ) // page_size,
            },
        }), 200

    except pymysql.MySQLError:
        app.logger.exception("分页查询客户失败")
        return jsonify({"error": "数据库查询失败"}), 500

    finally:
        if connection is not None:
            connection.close()


@app.route("/customers/<int:customer_id>", methods=["GET"])
def get_customer(customer_id):
    connection = None

    try:
        connection = get_connection()

        with connection.cursor() as cursor:
            start = time.perf_counter()

            cursor.execute(
                "SELECT id, name, industry "
                "FROM customers WHERE id = %s",
                (customer_id,),
            )
            customer = cursor.fetchone()

            elapsed_ms = (time.perf_counter() - start) * 1000
            print(f"客户查询耗时：{elapsed_ms:.2f} 毫秒")

        if customer is None:
            return jsonify({"error": "客户不存在"}), 404

        return jsonify({"data": customer}), 200

    except pymysql.MySQLError:
        app.logger.exception("查询单个客户失败")
        return jsonify({"error": "数据库查询失败"}), 500

    finally:
        if connection is not None:
            connection.close()

@app.route("/customers", methods=["POST"])
def create_customer():
    data = request.get_json(silent=True)

    try:
        customer_input = validate_customer_input(data)
    except CustomerInputError as error:
        return jsonify({"error": str(error)}), 400

    name = customer_input["name"]
    industry = customer_input["industry"]

    # 从这里开始，保留原来的数据库写入代码。
    connection = None

    # 原来的 try、INSERT、commit、except、finally 继续保留。

    try:
        connection = get_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO customers (name, industry) "
                "VALUES (%s, %s)",
                (name, industry),
            )

            customer_id = cursor.lastrowid

        # 4. 提交事务。
        connection.commit()

        # 5. 返回创建结果。
        return jsonify({
            "data": {
                "id": customer_id,
                "name": name,
                "industry": industry,
            }
        }), 201

    except pymysql.MySQLError:
        if connection is not None:
            connection.rollback()

        app.logger.exception("新增客户失败")
        return jsonify({"error": "新增客户失败"}), 500

    finally:
        if connection is not None:
            connection.close()

@app.route("/customers/<int:customer_id>", methods=["PATCH"])
def update_customer(customer_id):
    # 1. 读取并检查请求数据。
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "请求体必须是 JSON 对象"}), 400

    industry = data.get("industry")

    if not isinstance(industry, str) or not industry.strip():
        return jsonify({"error": "industry 必须是非空字符串"}), 400

    industry = industry.strip()

    if len(industry) > 50:
        return jsonify({"error": "industry 不能超过 50 个字符"}), 400

    connection = None

    try:
        connection = get_connection()

        with connection.cursor() as cursor:
            # 2. 查找客户，并锁住这条记录。
            cursor.execute(
                "SELECT id, name, industry "
                "FROM customers WHERE id = %s FOR UPDATE",
                (customer_id,),
            )

            customer = cursor.fetchone()

            if customer is None:
                connection.rollback()
                return jsonify({"error": "客户不存在"}), 404

            # 3. 客户存在，执行修改。
            cursor.execute(
                "UPDATE customers SET industry = %s WHERE id = %s",
                (industry, customer_id),
            )

            # 更新用于返回的 Python 字典。
            customer["industry"] = industry

        # 4. 提交修改。
        connection.commit()

        return jsonify({"data": customer}), 200

    except pymysql.MySQLError:
        if connection is not None:
            connection.rollback()

        app.logger.exception("修改客户失败")
        return jsonify({"error": "修改客户失败"}), 500

    finally:
        if connection is not None:
            connection.close()

@app.route("/customers/<int:customer_id>", methods=["DELETE"])
def delete_customer(customer_id):
    connection = None

    try:
        connection = get_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM customers WHERE id = %s",
                (customer_id,),
            )

            deleted_count = cursor.rowcount

        if deleted_count == 0:
            connection.rollback()
            return jsonify({"error": "客户不存在"}), 404

        connection.commit()

        return jsonify({
            "message": "删除成功",
            "id": customer_id,
        }), 200

    except pymysql.IntegrityError as error:
        if connection is not None:
            connection.rollback()

        # MySQL 1451：记录被外键引用，不能删除。
        if error.args[0] == 1451:
            return jsonify({
                "error": "客户存在关联数据，不能直接删除"
            }), 409

        app.logger.exception("删除客户时发生数据约束错误")
        return jsonify({"error": "删除客户失败"}), 500

    except pymysql.MySQLError:
        if connection is not None:
            connection.rollback()

        app.logger.exception("删除客户时发生数据库错误")
        return jsonify({"error": "删除客户失败"}), 500

    finally:
        if connection is not None:
            connection.close()

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "请求体必须是 JSON 对象"}), 400

    username = data.get("username")
    password = data.get("password")

    if not isinstance(username, str) or not username:
        return jsonify({"error": "username 必须是非空字符串"}), 400

    if not isinstance(password, str) or not password:
        return jsonify({"error": "password 必须是非空字符串"}), 400

    password_matches = check_password_hash(
        demo_user["password_hash"],
        password,
    )

    if username != demo_user["username"] or not password_matches:
        return jsonify({"error": "账号或密码错误"}), 401

    # 清除之前的登录信息，再记录当前用户身份。
    session.clear()
    session["user_id"] = demo_user["id"]

    return jsonify({"message": "登录成功"}), 200


@app.route("/me", methods=["GET"])
def current_user():
    if session.get("user_id") != demo_user["id"]:
        return jsonify({"error": "请先登录"}), 401

    return jsonify({
        "data": {
            "id": demo_user["id"],
            "username": demo_user["username"],
        }
    }), 200


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "已退出登录"}), 200

@app.before_request
def check_customer_access():
    is_customer_request = (
        request.path == "/customers"
        or request.path.startswith("/customers/")
    )

    # 不是客户接口，本轮不在这里检查。
    if not is_customer_request:
        return None

    # 第一步：确认身份。
    if session.get("user_id") != demo_user["id"]:
        return jsonify({"error": "请先登录"}), 401

    # 第二步：确认是否允许这个操作。
    if request.method in ("POST", "PATCH", "PUT", "DELETE"):
        if demo_user["role"] != "admin":
            return jsonify({"error": "没有操作权限"}), 403

    return None



if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001)