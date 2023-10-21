# coding: utf-8
import ismrmrd
import ismrmrd.xsd
import numpy as np
import argparse
import json
import os

#json_file = "/opt/mri4all/data/acq_queue/e05a03dc-6f73-11ee-b9cb-4be9ddc04f52#scan_1/scan.json"

def create_ismrmrd(folder, raw_data, task):
    # Opening JSON file
    #f = open(json_file)
    data = task
    ##?############# Following block of code will get replaced by whatever numpy is given to us ##?###############?###############?###############?###############?###############?#############
    repetitions = 1 #! check
    coils = 1 #! check
    acceleration = 1 #! check
    ##?###############?###############?###############?###############?###############?###############?############# ##?###############?###############?###########?###############?###############?#################
    # The number of points in x,y,kx,ky
    nx, ny, nz = raw_data.shape[0], raw_data.shape[1], raw_data.shape[2]
    nkx, nky, nkz = raw_data.shape[0], raw_data.shape[1], raw_data.shape[2]

    # Open the dataset (creation mode)
    filename_to_save = os.path.join(folder, "ismrmrd_file.h5")
    dset = ismrmrd.Dataset(filename_to_save, "dataset", create_if_needed=True)

    # Create the XML header and write it to the file (creation mode)
    header = ismrmrd.xsd.ismrmrdHeader()

    # Experimental Conditions
    exp = ismrmrd.xsd.experimentalConditionsType() 
    magneticFieldStrength = 0.048
    exp.H1resonanceFrequency_Hz = magneticFieldStrength*(42.57e+06) 

    header.experimentalConditions = exp

    # Acquisition System Information
    sys = ismrmrd.xsd.acquisitionSystemInformationType()
    sys.receiverChannels = 1 #! assuming single coil
    header.acquisitionSystemInformation = sys


    # Encoding
    encoding = ismrmrd.xsd.encodingType()  
    #encoding.trajectory = ismrmrd.xsd.trajectoryType.CARTESIAN
    encoding.trajectory =ismrmrd.xsd.trajectoryType[data.processing.trajectory.upper()]

    # encoded and recon spaces
    efov = ismrmrd.xsd.fieldOfViewMm() 
    #efov.x = oversampling*256 #! needed field
    #efov.y = 256 #! needed field
    #efov.z = 5   #! needed field
    efov.x = raw_data.shape[0]
    efov.y = raw_data.shape[1]
    efov.z = raw_data.shape[2]

    rfov = ismrmrd.xsd.fieldOfViewMm() 
    rfov.x = raw_data.shape[0]
    rfov.y = raw_data.shape[1]
    rfov.z = raw_data.shape[2]

    ematrix = ismrmrd.xsd.matrixSizeType()
    rmatrix = ismrmrd.xsd.matrixSizeType()

    ematrix.x = raw_data.shape[0]
    ematrix.y = raw_data.shape[1]
    ematrix.z = raw_data.shape[2]
    rmatrix.x = raw_data.shape[0]
    rmatrix.y = raw_data.shape[1]
    rmatrix.z = raw_data.shape[2]

    espace = ismrmrd.xsd.encodingSpaceType() 
    espace.matrixSize = ematrix
    espace.fieldOfView_mm = efov
    rspace = ismrmrd.xsd.encodingSpaceType()
    rspace.matrixSize = rmatrix
    rspace.fieldOfView_mm = rfov
    # Set encoded and recon spaces
    encoding.encodedSpace = espace
    encoding.reconSpace = rspace

    # Encoding limits
    limits = ismrmrd.xsd.encodingLimitsType()

    limits1 = ismrmrd.xsd.limitType()
    limits1.minimum = 0
    limits1.center = round(ny/2)
    limits1.maximum = ny - 1
    limits.kspace_encoding_step_1 = limits1

    limits_rep = ismrmrd.xsd.limitType()
    limits_rep.minimum = 0
    limits_rep.center = round(repetitions / 2)
    limits_rep.maximum = repetitions - 1
    limits.repetition = limits_rep

    limits_rest = ismrmrd.xsd.limitType()
    limits_rest.minimum = 0
    limits_rest.center = 0
    limits_rest.maximum = 0
    limits.kspace_encoding_step_0 = limits_rest
    limits.slice = limits_rest    
    limits.average = limits_rest
    limits.contrast = limits_rest
    limits.kspaceEncodingStep2 = limits_rest
    limits.phase = limits_rest
    limits.segment = limits_rest
    limits.set = limits_rest

    encoding.encodingLimits = limits
    header.encoding.append(encoding)

    dset.write_xml_header(header.toXML('utf-8'))           

    # Synthesize the k-space data
    #Ktrue = transform_image_to_kspace(coil_images,(1,2))
    Ktrue = raw_data[np.newaxis,np.newaxis,...]

    # Create an acquistion and reuse it
    acq = ismrmrd.Acquisition()
    acq.resize(nkx, coils)
    acq.version = 1
    acq.available_channels = coils
    acq.center_sample = round(nkx/2)
    acq.read_dir[0] = 1.0
    acq.phase_dir[1] = 1.0
    acq.slice_dir[2] = 1.0


    # Initialize an acquisition counter
    counter = 0

    # Loop over the repetitions, add noise and write to disk
    # simulating a T-SENSE type scan
    for rep in range(repetitions):
        K = Ktrue  
        acq.idx.repetition = rep
        for slice_num in range(nz):
            acq.idx.slice += 1
            for acc in range(acceleration):
                for line in np.arange(acc,nky,acceleration):
                    # set some fields in the header
                    acq.scan_counter = counter
                    acq.idx.kspace_encode_step_1 = line
                    acq.clearAllFlags()
                    if line == 0:
                            acq.setFlag(ismrmrd.ACQ_FIRST_IN_ENCODE_STEP1)
                            acq.setFlag(ismrmrd.ACQ_FIRST_IN_SLICE)
                            acq.setFlag(ismrmrd.ACQ_FIRST_IN_REPETITION)
                    elif line == nky - 1:
                            acq.setFlag(ismrmrd.ACQ_LAST_IN_ENCODE_STEP1)
                            acq.setFlag(ismrmrd.ACQ_LAST_IN_SLICE)
                            acq.setFlag(ismrmrd.ACQ_LAST_IN_REPETITION)
                    # set the data and append
                    acq.data[:] = K[rep,acc,:,line,slice_num]
                    dset.append_acquisition(acq)
                    counter += 1

    # Clean up
    dset.close()
    print("ISMRMRD file created")