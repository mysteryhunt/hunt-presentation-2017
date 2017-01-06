from flask import Flask

app = Flask(__name__)

import present.views
import present.utils
