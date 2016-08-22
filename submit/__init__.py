from flask import Flask

app = Flask(__name__)

import submit.views
import submit.utils
