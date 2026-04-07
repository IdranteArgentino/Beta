import os

from gestionale.webapp import create_app


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    db_path = os.path.join(data_dir, "gestionale.db")

    app = create_app(db_path)
    app.run(host="127.0.0.1", port=5000, debug=True)


if __name__ == "__main__":
    main()
