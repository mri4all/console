
from flask import Flask, flash, render_template, session, redirect, url_for, request
from virtualscanner.coms.coms_ui.coms_server_flask import app, db, socketio  #, login_manager
import numpy as np
# B0
from virtualscanner.coms.coms_ui.forms import HalbachForm
from virtualscanner.server.b0.b0_worker import b0_halbach_worker, b0_plot_worker, b0_3dplot_worker, b0_rings_worker,\
                                               b0_eval_field_any
from virtualscanner.utils import constants
from virtualscanner.utils.helpers import update_session_subdict
from scipy.io import savemat, loadmat

@app.route('/research',methods=['POST','GET'])
def research():
    return render_template('research.html')
