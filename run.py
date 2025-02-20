from server import create_app
from server.models import Role

app = create_app()



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=True)

