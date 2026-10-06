import os

from flask import Flask, jsonify, request

from app.calculator import OPERATIONS

app = Flask(__name__)

APP_VERSION = os.environ.get("APP_VERSION", "dev")
APP_ENV = os.environ.get("APP_ENV", "local")


@app.get("/")
def index():
    return jsonify(
        app="Session 16 Calculator API",
        version=APP_VERSION,
        environment=APP_ENV,
        operations=sorted(OPERATIONS),
    )


@app.get("/health")
def health():
    return jsonify(status="ok", version=APP_VERSION)


@app.get("/calc/<op>")
def calc(op):
    if op not in OPERATIONS:
        return jsonify(error=f"Unknown operation: {op}"), 404
    try:
        a = float(request.args["a"])
        b = float(request.args["b"])
    except (KeyError, ValueError):
        return jsonify(error="Query params a and b must be numbers"), 400
    try:
        result = OPERATIONS[op](a, b)
    except ValueError as e:
        return jsonify(error=str(e)), 400
    return jsonify(operation=op, a=a, b=b, result=result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
