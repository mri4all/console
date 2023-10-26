import numpy as np

def post_acq_do(seq_info):
    raw_file_path = seq_info["raw_file_path"]
    traj_file_path = seq_info["traj_file_path"]
    # TODO: Add info for the recon team into a JSON file later
    raw_data = seq_info["raw_data"]
    traj_data = seq_info["traj_data"]  
    
    # Saving files go here
    np.save(raw_file_path, raw_data)
    np.save(raw_file_path, raw_data)
      

