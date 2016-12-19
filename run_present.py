from common import metrics, s3
from present import app

import default_config
app.config.from_object(default_config)
try:
    import config
    app.config.from_object(config)
except ImportError:
    pass

from common import login
app.register_blueprint(login.blueprint)
app.register_blueprint(s3.blueprint)

metrics.create_reporter(app)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
