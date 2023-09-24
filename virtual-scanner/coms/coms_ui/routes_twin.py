# Digital twin dashboard and components

from flask import Flask, flash, render_template, session, redirect, url_for, request
from virtualscanner.coms.coms_ui.coms_server_flask import app, db, socketio  #, login_manager


@app.route('/twin',methods=['POST','GET'])
def view_twin():

    return 'Digital Twin dashboard'


@app.route('/twin/b0',methods=['POST','GET'])
def view_twin_b0():

    return render_template('b0.html')