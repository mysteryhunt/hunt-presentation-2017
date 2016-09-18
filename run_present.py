from present import app

import default_config
app.config.from_object(default_config)
try:
    import config
    app.config.from_object(config)
except ImportError:
    pass
    
import puzzles
app.config.from_object(puzzles)

from common import login
app.register_blueprint(login.blueprint)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
