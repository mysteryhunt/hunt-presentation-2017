from flask import Flask

app = Flask(__name__)

import admin.views
import admin.utils
