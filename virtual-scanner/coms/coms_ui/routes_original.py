from pathlib import Path
import os, signal
from werkzeug.utils import secure_filename

from virtualscanner.utils import constants
from virtualscanner.utils.helpers import allowed_file

CURRENT_PATH = Path(__file__).parent
ROOT_PATH = constants.ROOT_PATH
UPLOAD_FOLDER = constants.COMS_UI_STATIC_USER_UPLOAD_PATH
SERVER_ANALYZE_PATH = constants.SERVER_ANALYZE_PATH
STATIC_ANALYZE_PATH = constants.COMS_UI_STATIC_ANALYZE_PATH
STATIC_ADJUSTMENTS_PATH = constants.COMS_UI_STATIC_ADJUSTMENTS_PATH

import numpy as np

from virtualscanner.server.ana import T2_mapping as T2_mapping, T1_mapping as T1_mapping, ROI_analysis as ROI_analysis
from virtualscanner.server.registration import register as reg
from virtualscanner.server.rf.rx import caller_script_Rx as Rxfunc
from virtualscanner.server.rf.tx.SAR_calc import SAR_calc_main as SAR_calc_main
from virtualscanner.server.simulation.bloch import caller_script_blochsim as bsim
from virtualscanner.server.registration import register as reg
from flask import Flask, flash, render_template, session, redirect, url_for, request
from virtualscanner.server.scanner_control.seq.adjustments_acq.calibration import larmor_step_search, rf_max_cal, \
    grad_max_cal, shim_cal
from virtualscanner.coms.coms_ui.coms_server_flask import app, db, socketio  # , login_manager


@app.route('/', methods=['POST',
                         'GET'])  # This needs to point to the login screen and then we can use the register link seprately
def log_in():
    """
    Renders the log-in html page on the web and requests user log-in information (e-mail) and choice of user mode
    (Standard/Advanced).

    Returns
    -------
    AppContext
        | Redirects to register page if user-name exists and Standard mode is selected
        |    OR
        | Redirects to recon page if user-name exists and Advanced mode is selected
        |    OR
        | Renders log-in template
    """
    session.clear()
    session['acq_out_axial'] = []
    session['acq_out_sagittal'] = []
    session['acq_out_coronal'] = []

    ## Initialize session variables ########
    session['b0'] = {'best_vector': [], 'opt-3d': 'z', 'masked_field': np.zeros((10, 10, 10)),
                     'coordinates': [np.arange(10) for q in range(3)],
                     'ring_position_symmetry': [],
                     'inner_num_magnets': [],
                     'inner_ring_radii': [],
                     'outer_num_magnets': [],
                     'outer_ring_radii': [],
                     'resolution': 5,
                     'sim_dimensions': [],
                     'dsv': 0,
                     'dsv_display': 50,
                     'res_display': 5,
                     'x': 5,
                     'y': 5,
                     'z': 5,
                     'temperature': 20
                     }

    # TODO add x,y,z slices into session of b0 (have javascript update session on those ... )
    session['rf'] = {
        'spin_bw': 1000,
        'spin_num': 10,
        'pulse_type': 'sinc90',
        'rf_shape': 'sinc',
        'rf_thk': 5,
        'rf_fa': 90,
        'rf_dur': 2,
        'rf_df': 0,
        'rf_dphi': 0,
        'rf_tbw': 2,
        'spin_t1': 0,
        'spin_t2': 0

    }

    if request.method == 'POST':
        # users.append(request.form['user-name'])
        # session['username'] = users[-1]
        session['username'] = request.form['user-name']
        if session['username'] == "":
            return render_template("log_in.html")
        if request.form['mode'] == "Standard":
            return redirect("register")
        elif request.form['mode'] == "Advanced":
            return redirect("recon")
        elif request.form['mode'] == "Research":
            return redirect("research")  # Go to sequence plotter page.
        else:
            return redirect("log_in")

    else:
        return render_template("log_in.html")


# This needs to point to the login screen and then we can use the register link separately
@app.route('/register', methods=['POST', 'GET'])
def on_register():
    """
    Renders the registration html page on the web.

    Returns
    -------
    AppContext
        | Renders register page
        |    OR
        | Redirects to register success page if registration occurs

    """
    if 'acq' in session and 'reg_success' not in session:
        session.pop('acq')
        message = 1
        return render_template('register.html', msg=message)

    if 'ana_load' in session and 'reg_success' not in session:
        session.pop('ana_load')
        message = 1
        return render_template('register.html', msg=message)

    if 'reg_success' in session:
        return redirect('register_success')
    else:
        return render_template('register.html')


@app.route('/register_success', methods=['POST', 'GET'])
def on_register_success():
    """
    Renders the registration html page on the web with a success message when registration occurs.

    Returns
    -------
    AppContext
        | Renders register page with registration success message
        | May also pass variables:
        | success : int
        |    Either 1 or 0 depending on registration success
        | payload : dict
        |    Form inputted values sent back to display together with template

    """
    return render_template('register.html', success=session['reg_success'], payload=session['reg_payload'])


@app.route('/acquire', methods=['POST', 'GET'])
def on_acq():
    """
    Renders the acquire html page on the web.

    Returns
    -------
    AppContext
        | Renders acquire template
        | May also pass variables:
        | success : int
        |    Either 1 or 0 depending on acquisition success
        | axial : list
        |    File names for generated axial images
        | sagittal : list
        |    File names for generated sagittal images
        | coronal : list
        |    File names for generated coronal images
        | payload : dict
        |    Form inputted values sent back to display together with template
    """
    if 'acq' in session:

        return render_template('acquire.html', success=session['acq'], axial=session['acq_out_axial'],
                               sagittal=session['acq_out_sagittal'], coronal=session['acq_out_coronal'],
                               payload=session['acq_payload'])
    else:
        return render_template('acquire.html')


@app.route('/analyze', methods=['POST', 'GET'])
def on_analyze():
    """
    Renders the analyze html page on the web.

    Returns
    -------
    AppContext
        | Renders analyze template
        | May also pass variables:
        | roi_success/map_success/load_success : int
        |   Either 1 or 0 depending on analyze steps success
        | payload1/payload2/payload3 : dict
        |   Form inputted values and output results sent back to display together with template
    """
    if 'ana_load' in session:
        if 'ana_map' in session:
            if 'ana_roi' in session:
                return render_template('analyze.html', roi_success=session['ana_roi'], payload3=session['ana_payload3'],
                                       map_success=session['ana_map'], load_success=session['ana_load'],
                                       payload1=session['ana_payload1'], payload2=session['ana_payload2'])
            else:
                return render_template('analyze.html', map_success=session['ana_map'], load_success=session['ana_load'],
                                       payload1=session['ana_payload1'], payload2=session['ana_payload2'])
        else:
            return render_template('analyze.html', load_success=session['ana_load'], payload1=session['ana_payload1'])

    else:
        return render_template('analyze.html')


@app.route('/adjustments', methods=['POST', 'GET'])
def on_adjustments():
    """
    Renders the adjustments html page on the web.

    Returns
    -------
    AppContext
        | Renders analyze template
        | May also pass variables:
        | roi_success/map_success/load_success : int
        |   Either 1 or 0 depending on analyze steps success
        | payload1/payload2/payload3 : dict
        |   Form inputted values and output results sent back to display together with template
    """
    if 'adj' in session:
        return render_template('adjustments.html', success=session['adj'],
                               payload=session['adj_payload'])
    else:
        return render_template('adjustments.html')


@app.route('/tx', methods=['POST', 'GET'])
def on_tx():
    """
    Renders the tx html page on the web.

    Returns
    -------
    AppContext
        | Renders tx template
        | May also pass variables:
        | success : int
        |   Either 1 or 0 depending on tx success
        | payload : dict
        |   Form inputted values and output results sent back to display together with template
    """
    if 'tx' in session:
        return render_template('tx.html', success=session['tx'], payload=session['tx_payload'])
    else:
        return render_template('tx.html')


@app.route('/rx', methods=['POST', 'GET'])
def on_rx():
    """
    Renders the rx html page on the web.

    Returns
    -------
    AppContext
        | Renders rx template
        | May also pass variables:
        | success : int
        |   Either 1 or 0 depending on rx success
        | payload : dict
        |   Form inputted values and output results sent back to display together with template
    """
    if 'rx' in session:
        return render_template('rx.html', success=session['rx'], payload=session['rx_payload'])
    else:
        return render_template('rx.html')


@app.route('/recon', methods=['POST', 'GET'])
def on_recon():
    """
    Renders the recon html page on the web.

    Returns
    -------
    AppContext
        | Renders recon template
        | May also pass variables:
        | success : int
        |   Either 1 or 0 depending on recon success
        | payload : dict
        |   Form inputted values and output results sent back to display together with template
    """
    if 'recon' in session:
        return render_template('recon.html', success=session['recon'], payload=session['recon_payload'])
    else:
        return render_template('recon.html')


@app.route('/receiver', methods=['POST', 'GET'])
def worker():
    """
    Receives form inputs from the templates and applies the server methods.

    Returns
    -------
    AppContext
        Either renders templates or redirects to other templates
    """
    # read payload and convert it to dictionary

    if request.method == 'POST':
        payload = request.form.to_dict()
        print(request.form['formName'])
        # Registration
        if request.form['formName'] == 'reg':

            if payload['subjecttype'] == "Subject":
                return redirect('register')

            print(payload)
            session['reg_success'] = 1
            session['reg_payload'] = payload

            del payload['formName']

            # Currently only metric system since only phantom registration is possible. Fix this for future releases.
            del payload['height-unit']
            del payload['weight-unit']
            del payload['inches']

            pat_id = payload.get('patid')
            session['patid'] = pat_id
            query_dict = {
                "patid": pat_id,
            }
            rows = reg.reuse(query_dict)
            # print((rows))d

            if (rows):
                print('Subject is already registered with PATID: ' + pat_id)
            else:
                status = reg.consume(payload)

            return redirect('register_success')

        elif request.form['formName'] == 'new-reg':
            session.pop('reg_success')

            return redirect('register')
        # ACQUIRE
        elif request.form['formName'] == 'acq':

            session['acq'] = 0

            if "patid" not in session:  # Please register first
                return redirect('register')

            pat_id = session['patid']
            query_dict = {
                "patid": pat_id,
            }

            rows = reg.reuse(query_dict)  #
            print(rows)

            # session['acq'] = 0
            session['acq_payload'] = payload
            print(payload)

            progress = bsim.run_blochsim(seqinfo=payload, phtinfo=rows[0][0],
                                         pat_id=pat_id)  # phtinfo just needs to be 1 string
            sim_result_path = constants.COMS_PATH / 'coms_ui' / 'static' / 'acq' / 'outputs' / session['patid']

            while (os.path.isdir(sim_result_path) is False):
                pass

            if progress == 1:
                session['acq'] = 1

                STATIC_ACQUIRE_PATH_REL = constants.COMS_UI_STATIC_ACQUIRE_PATH.relative_to(CURRENT_PATH)
                im_path_from_template = STATIC_ACQUIRE_PATH_REL / 'outputs' / session['patid']

                imgpaths = os.listdir(sim_result_path)
                complete_path = [str(im_path_from_template / iname) for iname in imgpaths]
                Z_acq = []
                X_acq = []
                Y_acq = []

                for indx in range(len(complete_path)):
                    if 'GRE' in complete_path[indx]:
                        pos = complete_path[indx].find('_', 30, ) + 1  #
                    else:
                        pos = complete_path[indx].find('_', 29, ) + 1  #

                    sl_orientation = complete_path[indx][pos]
                    if sl_orientation == 'Z':
                        Z_acq.append(complete_path[indx])
                    elif sl_orientation == 'X':
                        X_acq.append(complete_path[indx])
                    elif sl_orientation == 'Y':
                        Y_acq.append(complete_path[indx])

                session['acq_out_axial'] = Z_acq
                session['acq_out_sagittal'] = X_acq
                session['acq_out_coronal'] = Y_acq
                print('hello')

                return redirect('acquire')

        elif request.form['formName'] == 'adj':
            print("Adjustments tab selected")

            if payload["selectedSeq"] == 'Findf0':
                larmor_step_search(step_search_center=float(payload["Frequency"]), steps=30, step_bw_MHz=5e-3,
                                   plot=False,
                                   shim_x=float(payload["Xshim"]) / 100, shim_y=float(payload["Yshim"]) / 100,
                                   shim_z=float(payload["Zshim"]) / 100,
                                   gui_test=False)  # TODO: add iteerations label/input in adjustments.html

            # rf_max_cal
            elif payload["selectedSeq"] == 'RFCal':
                rf_max_cal(larmor_freq=float(payload["Frequency"]), points=20, iterations=2, zoom_factor=2,
                           shim_x=float(payload["Xshim"]) / 100, shim_y=float(payload["Yshim"]) / 100,
                           shim_z=float(payload["Zshim"]) / 100,
                           tr_spacing=2, force_tr=False, first_max=False, smooth=True, plot=True, gui_test=False)

            # grad_max_cal
            elif payload["selectedSeq"] == 'GradCal':
                grad_max_cal(channel='x', phantom_width=10, larmor_freq=float(payload["Frequency"]),
                             calibration_power=0.8,
                             trs=3, tr_spacing=2e6, echo_duration=5000,
                             readout_duration=500, rx_period=25 / 3,
                             RF_PI2_DURATION=50, rf_max=2,  # cfg.RF_MAX
                             trap_ramp_duration=50, trap_ramp_pts=5,
                             plot=True)

            # shim_cal
            elif payload["selectedSeq"] == 'ShimCal':
                shim_cal(larmor_freq=float(payload["Frequency"]), channel='x', range=0.01, shim_points=3, points=2, iterations=1,
                         zoom_factor=2,
                         shim_x=float(payload["Xshim"]) / 100, shim_y=float(payload["Yshim"]) / 100, shim_z=float(payload["Zshim"]) / 100,
                         tr_spacing=2, force_tr=False, first_max=False, smooth=True, plot=True, gui_test=False)

            return redirect('adjustments')

        # Analyze
        elif request.form['formName'] == 'ana':

            if 'original-data-opt' in payload:

                if 'ana_load' in session:
                    session.pop('ana_load')
                    if 'ana_map' in session:
                        session.pop('ana_map')
                        if 'ana_roi' in session:
                            session.pop('ana_roi')

                session['ana_load'] = 1

                if "patid" not in session:  # Please register first
                    return redirect('register')

                if payload['original-data-opt'] == 'T1':
                    folder_path = STATIC_ANALYZE_PATH / 'inputs' / 'T1_original_data'
                elif payload['original-data-opt'] == 'T2':
                    folder_path = STATIC_ANALYZE_PATH / 'inputs' / 'T2_original_data'

                filenames_in_path = os.listdir(folder_path)
                STATIC_ANALYZE_PATH_REL = constants.COMS_UI_STATIC_ANALYZE_PATH.relative_to(CURRENT_PATH)
                original_data_path = [
                    str(STATIC_ANALYZE_PATH_REL / 'inputs' / (payload['original-data-opt'] + '_original_data') / iname)
                    for
                    iname in filenames_in_path]
                payload['data-path'] = original_data_path

                session['ana_payload1'] = payload


            elif 'map-form' in payload:
                STATIC_ANALYZE_PATH_REL = constants.COMS_UI_STATIC_ANALYZE_PATH.relative_to(CURRENT_PATH)
                session['ana_map'] = 1

                if payload['TI'] == "":
                    server_od_path = SERVER_ANALYZE_PATH / 'inputs' / 'T2_orig_data'
                    map_name, dicom_path, np_map_name = T2_mapping.main(server_od_path, payload['TR'], payload['TE'],
                                                                        session['patid'])
                else:
                    server_od_path = SERVER_ANALYZE_PATH / 'inputs' / 'T1_orig_data'
                    map_name, dicom_path, np_map_name = T1_mapping.main(server_od_path, payload['TR'], payload['TE'],
                                                                        payload['TI'],
                                                                        session['patid'])

                payload['dicom_path'] = str(dicom_path)
                payload['map_path'] = str(STATIC_ANALYZE_PATH_REL / 'outputs' / session['patid'] / map_name)
                session['ana_payload2'] = payload


            elif 'roi-form' in payload:

                # payload['map-type'] = 'T1'
                STATIC_ANALYZE_PATH_REL = constants.COMS_UI_STATIC_ANALYZE_PATH.relative_to(CURRENT_PATH)
                session['ana_roi'] = 1
                dicom_map_path = session['ana_payload2']['dicom_path']
                if 'T1' in dicom_map_path:
                    payload['map-type'] = 'T1'
                elif 'T2' in dicom_map_path:
                    payload['map-type'] = 'T2'

                roi_result_filename = ROI_analysis.main(dicom_map_path, payload['map-type'], payload['map-size'],
                                                        payload['map-FOV'], session['patid'])

                roi_result_path = STATIC_ANALYZE_PATH_REL / 'outputs' / session['patid'] / roi_result_filename

                payload['roi_path'] = str(roi_result_path)
                session['ana_payload3'] = payload

            return redirect('analyze')

        # Advance Mode
        # tx
        elif request.form['formName'] == 'tx':
            print(payload)
            file = request.files['file']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)

                upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(upload_path)

                filename = filename[:-4] + '.seq'

                if (filename != 'rad2d.seq'):
                    if (os.path.isfile(constants.SERVER_PATH / 'rf' / 'tx' / 'SAR_calc' / 'assets' / filename)):
                        os.remove(constants.SERVER_PATH / 'rf' / 'tx' / 'SAR_calc' / 'assets' / filename)
                    dest = str(constants.SERVER_PATH / 'rf' / 'tx' / 'SAR_calc' / 'assets' / filename)
                    os.rename(upload_path, dest)

                # os.rename(upload_path, constants.SERVER_PATH / 'rf' / 'tx' / 'SAR_calc' / 'assets' / filename)

                output = SAR_calc_main.payload_process(filename)

                session['tx'] = 1
                STATIC_RFTX_PATH_REL = constants.COMS_UI_STATIC_RFTX_PATH.relative_to(CURRENT_PATH)
                output['plot_path'] = str(STATIC_RFTX_PATH_REL / 'SAR' / output['filename'])
                session['tx_payload'] = output
                return redirect('tx')
        # rx
        elif request.form['formName'] == 'rx':

            signals_filename, recon_filename, orig_im_path = Rxfunc.run_Rx_sim(payload)

            COMS_UI_STATIC_RFRX_PATH_REL = constants.COMS_UI_STATIC_RX_OUTPUT_PATH.relative_to(CURRENT_PATH)

            payload['signals_path'] = str(COMS_UI_STATIC_RFRX_PATH_REL / signals_filename)
            payload['recon_path'] = str(COMS_UI_STATIC_RFRX_PATH_REL / recon_filename)

            session['rx'] = 1
            session['rx_payload'] = payload
            return redirect('rx')

        # recon
        elif request.form['formName'] == 'recon':
            file = request.files['file']
            filename = secure_filename(file.filename)

            input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(input_path)

            STATIC_RECON_PATH_REL = constants.COMS_UI_STATIC_RECON_PATH.relative_to(CURRENT_PATH)
            out_path_form_template = STATIC_RECON_PATH_REL / 'outputs'

            if payload['DL-type'] == "GT":
                out1, out2, out3 = main(input_path, payload['DL-type'])
                payload['output'] = [str(out_path_form_template / out1), str(out_path_form_template / out2),
                                     str(out_path_form_template / out3)]
            else:
                out1, out2 = main(input_path, payload['DL-type'])
                payload['output'] = [out_path_form_template / out1, out_path_form_template / out2]

            session['recon'] = 1
            session['recon_payload'] = payload

            return redirect('recon')
