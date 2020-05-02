# -*- coding: utf-8 -*-
""" Derivation views. """
from flask import Blueprint

blueprint = Blueprint('derivation', __name__, url_prefix='/derivations', static_folder='../static')
