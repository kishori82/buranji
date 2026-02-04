import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import routes

app = routes.app
app.debug = True

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
