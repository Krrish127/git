import sqlite3
from pathlib import Path

from flask import Flask, jsonify, request

app = Flask(__name__)
app.json.ensure_ascii = False

db_path = Path(__file__).resolve().parent / "customers.db"


def get_connection():
    connection = sqlite3.connect(str(db_path))
    connection.row_factory = sqlite3.Row
    return connection


@app.route("/customers", methods=["GET"])
def list_customers():
    connection = get_connection()

    try:
        cursor = connection.execute(
            "SELECT id, name, industry FROM customers ORDER BY id"
        )
        rows = cursor.fetchall()

        customers = [dict(row) for row in rows]

        return jsonify({"data": customers}), 200
    finally:
        connection.close()


@app.route("/customers/<int:customer_id>", methods=["GET"])
def get_customer(customer_id):
    connection = get_connection()

    try:
        cursor = connection.execute(
            "SELECT id, name, industry FROM customers WHERE id = ?",
            (customer_id,),
        )
        row = cursor.fetchone()

        if row is None:
            return jsonify({"error": "客户不存在"}), 404

        return jsonify({"data": dict(row)}), 200
    finally:
        connection.close()

@app.route("/customers", methods=["POST"])
def create_customer():
    # 第一步：读取并检查输入。
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "请求体必须是 JSON 对象"}), 400

    name = data.get("name")
    industry = data.get("industry")

    if not isinstance(name, str) or not name.strip():
        return jsonify({"error": "name 必须是非空字符串"}), 400

    if not isinstance(industry, str) or not industry.strip():
        return jsonify({"error": "industry 必须是非空字符串"}), 400

    name = name.strip()
    industry = industry.strip()

    # 第二步：写入数据库。
    connection = get_connection()

    try:
        cursor = connection.execute(
            "INSERT INTO customers (name, industry) VALUES (?, ?)",
            (name, industry),
        )

        customer_id = cursor.lastrowid
        connection.commit()

        # 第三步：返回创建结果。
        return jsonify({
            "data": {
                "id": customer_id,
                "name": name,
                "industry": industry,
            }
        }), 201

    except sqlite3.Error:
        connection.rollback()
        app.logger.exception("新增客户时发生数据库错误")
        return jsonify({"error": "新增失败，请稍后重试"}), 500

    finally:
        connection.close()

@app.route("/customers/<int:customer_id>", methods=["PATCH"])
def update_customer(customer_id):
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "请求体必须是 JSON 对象"}), 400

    industry = data.get("industry")

    if not isinstance(industry, str) or not industry.strip():
        return jsonify({"error": "industry 必须是非空字符串"}), 400

    industry = industry.strip()
    connection = get_connection()

    try:
        cursor = connection.execute(
            "UPDATE customers SET industry = ? WHERE id = ?",
            (industry, customer_id),
        )

        if cursor.rowcount == 0:
            connection.rollback()
            return jsonify({"error": "客户不存在"}), 404

        row = connection.execute(
            "SELECT id, name, industry FROM customers WHERE id = ?",
            (customer_id,),
        ).fetchone()

        connection.commit()

        return jsonify({"data": dict(row)}), 200

    except sqlite3.Error:
        connection.rollback()
        app.logger.exception("修改客户时发生数据库错误")
        return jsonify({"error": "修改失败，请稍后重试"}), 500

    finally:
        connection.close()

@app.route("/customers/<int:customer_id>", methods=["DELETE"])
def delete_customer(customer_id):
    connection = get_connection()

    try:
        cursor = connection.execute(
            "DELETE FROM customers WHERE id = ?",
            (customer_id,),
        )

        if cursor.rowcount == 0:
            connection.rollback()
            return jsonify({"error": "客户不存在"}), 404

        connection.commit()

        return jsonify({
            "message": "删除成功",
            "id": customer_id,
        }), 200

    except sqlite3.Error:
        connection.rollback()
        app.logger.exception("删除客户时发生数据库错误")
        return jsonify({"error": "删除失败，请稍后重试"}), 500

    finally:
        connection.close()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)