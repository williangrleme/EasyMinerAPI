import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "api")))

from api.app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
