import math
import warnings
import numpy as np
import pypulseq as pp
# dependencies from mri4all console project
import common.logger as logger


log = logger.get_logger()

class seq2flocra:
    
    """
    Returns the flocra dictionary from a seq object or a seq file.

    Parameters
    ----------
    seq : object from a Pulseq sequence
    

    Returns
    -------
    flodict : dictionary for flocra ingestion
    
    """
    
    def __init__(self, seq: pp.Sequence = None, seq_file:str = None, system:pp.Opts = None, 
                 center_freq: float=15.58e6,  clk_freq: float = 122.88,
                 rf_amp_max: float = 5e3, tx_zero_end: bool = True,
                 debug_log: bool = True):
        """
        From Lincoln's object - trying to match structure for compatibility
        Args:
            rf_center (float): RF center (local oscillator frequency) in Hz.
            rf_amp_max (float): Default 5e+3 -- System RF amplitude max in Hz.
            grad_max (float): Default 1e+6 -- System gradient max in Hz/m. - from pp.Opts
            gx_max (float): Default None -- System X-gradient max in Hz/m. If None, defaults to grad_max. - from pp.Opts
            gy_max (float): Default None -- System Y-gradient max in Hz/m. If None, defaults to grad_max. - from pp.Opts
            gz_max (float): Default None -- System Z-gradient max in Hz/m. If None, defaults to grad_max. - from pp.Opts
            clf_freq (float): Default 122.88 -- System clock frequency in MHz.
            <DEPRECATED DUE TO DERIVED VARIABLE>clk_t (float): Default 1/122.88 -- System clock period in us.
            tx_t (float): Default 123/122.88 -- Transmit raster period in us. - from pp.Opts: rf_raster_time
            grad_t (float): Default 1229/122.88 -- Gradient raster period in us. - from pp.Opts: grad_raster_time
            tx_warmup (float): Default 500 -- Warmup time to turn on tx_gate before Tx events in us.
            tx_zero_end (bool): Default True -- Force zero at the end of RF shapes
            <DEPRECATED TO SUPPORT MORE SEQUENCES> grad_zero_end (bool): Default False, If True -- Force zero at the end of Gradient/Trap shapes
        """
        # seq world lives in seconds; marcos in us
        self._seq = seq                      # seq object 
        self._seq_file = seq_file
        self._center_freq = center_freq
        self._lo_freq = center_freq          # this will change based on frequency offset
        self._clk_freq = clk_freq  * 1e6     # More readily available in spec. - MHz :: Not available in system opts
        self._clk_t = 1 / self._clk_freq
        self._rf_amp_max = rf_amp_max        # Not available in system opts
        self._tx_zero_end = tx_zero_end
        self._debug_log = debug_log
        self._system = system

        if system is not None:
            log.info("**System defined**:", self._system)
        else:
            log.info("**System not defined, using defaults**")
            self._system = None

        # This seq system needs to be point of full control - simplifies config significantly; TODO:: simplify config using the pp.Opts()
        if self._system is None:
            self._system = pp.Opts(
                max_grad=1e7, # this should come from the config file
                grad_unit="Hz/m",
                # max_slew=130,
                # slew_unit="T/m/s",
                rf_ringdown_time=20e-6, # old one did not include this
                rf_dead_time=100e-6,
                adc_dead_time=20e-6,
                rf_raster_time = 1e-6, # (np.ceil(clk_freq) / self._clk_freq),
                grad_raster_time = 10e-6, # (np.ceil(clk_freq * 20) / self._clk_freq),       #clk_freq is in MHz, self._clk_freq is in Hz
                block_duration_raster=1e-6) #(np.ceil(clk_freq * 20) / self._clk_freq))
        
        
        self._tx_t = self._system.rf_raster_time #3.125
        self._grad_t = self._system.grad_raster_time
        self._tx_warmup = self._system.rf_dead_time
        self._rx_t = self._system.adc_raster_time

    def load_seqfile(self, seq_file): 
        self._seq = pp.Sequence(self._system)
        self._seq.read(seq_file, detect_rf_use=True)
        self._seq_duration = self._seq.get_definition("TotalDuration")
        
    def curate(self, times: np.ndarray = None, updates: np.ndarray=None):       #Lincoln's clean-up code
            # Make sure times are ordered, and overwrite duplicates to last inserted update
            time_sorted, unique_idx = np.unique(times, return_index=True)
            update_sorted = (updates)[unique_idx]
        
            # Compressed repeated values
            update_compressed_idx = np.concatenate([[0], np.nonzero(update_sorted[1:] - update_sorted[:-1])[0] + 1])
            update_arr = np.append(update_sorted[update_compressed_idx], 0.0) # end all arrays at 0.0 - Check with Vlad if necessary
            time_arr = np.append(time_sorted[update_compressed_idx], self._block_duration_us)

            return (time_arr, update_arr)
        
        
        
    def block_events_to_amps_times(self):
        # Future versions can exploit event libraries for more succint representation
        # adc  = self._seq.adc_library  # Library of ADC events
        # delay = self._seq.delay_library # Library of delay events
        # adc_times = self._seq.adc_times()

        # Initialize variables for flocra dictionary
        block_duration = 0.0
        self._num_samples_total = int(0)
        grad_vx_amp = np.array([0.0])
        grad_vx_time = np.array([0.0])
        grad_vy_amp = np.array([0.0])
        grad_vy_time = np.array([0.0])
        grad_vz_amp = np.array([0.0])
        grad_vz_time = np.array([0.0])
        
        tx0_amp = np.array([0.0])
        tx0_time = np.array([0.0])
        tx0_gate_amp = []
        tx0_gate_time = []
        
        rx0_gate_amp = [0.0]
        rx0_gate_time = [0.0]
        # TODO: Amplitude violation, slew violation, safety checks; can make this more concise using class' def for grad and RF props
        for block_counter in self._seq.block_events:
            block = self._seq.get_block(block_counter)
            if block.gx is not None:
                log.info('gx max:', self._system.max_grad)
                if block.gx.type == 'trap':
                    grad_vx_amp = np.concatenate((grad_vx_amp, [0, block.gx.amplitude / self._system.max_grad, block.gx.amplitude / self._system.max_grad, 0]))
                    grad_vx_time = np.concatenate((grad_vx_time, block_duration + [0, block.gx.rise_time, block.gx.rise_time + block.gx.flat_time, block.gx.rise_time + block.gx.flat_time + block.gx.fall_time ]))
                else:
                    grad_vx_amp.append(np.array(block.gx.waveform / self._system.max_grad))
                    grad_vx_time.append(np.array(block.gx.tt)+ block_duration) 
            
            
            if block.gy is not None:
                if block.gy.type == 'trap':
                    grad_vy_amp = np.concatenate((grad_vy_amp, [0, block.gy.amplitude / self._system.max_grad, block.gy.amplitude / self._system.max_grad, 0]))
                    grad_vy_time = np.concatenate((grad_vy_time, block_duration + [0, block.gy.rise_time, block.gy.rise_time + block.gy.flat_time, block.gy.rise_time + block.gy.flat_time + block.gy.fall_time ]))
                else:
                    grad_vy_amp.append(np.array(block.gy.waveform / self._system.max_grad))
                    grad_vy_time.append(np.array(block.gy.tt) + block_duration) 
            
            
            if block.gz is not None:
                if block.gz.type == 'trap':
                    grad_vz_amp = np.concatenate((grad_vz_amp, [0, block.gz.amplitude / self._system.max_grad, block.gz.amplitude / self._system.max_grad, 0]))
                    grad_vz_time = np.concatenate((grad_vz_time, block_duration + [0, block.gz.rise_time, block.gz.rise_time + block.gz.flat_time, block.gz.rise_time + block.gz.flat_time + block.gz.fall_time ]))
                else:
                    grad_vz_amp.append(np.array(block.gz.waveform / self._system.max_grad))
                    grad_vz_time.append(np.array(block.gz.tt) + block_duration) 
                    
            if block.rf is not None:
                if(block.rf.freq_offset > 0): # changes lo_freq, so need to playout current dict
                    self._lo_freq = self._center_freq + block.rf.freq_offset
                else:
                    signal_scaled = block.rf.signal / self._rf_amp_max
                    if (np.max(np.abs(signal_scaled)) > 1):
                        log.info('RF amplitude violation')
                        
                    mag = np.abs(signal_scaled)
                    phase = np.angle(signal_scaled)
                    tx0_pulse_amp = mag * np.exp((phase + block.rf.phase_offset) * 1j)
                    tx0_pulse_time = block_duration + np.max([block.rf.delay, self._tx_warmup]) + block.rf.t - block.rf.t[0]  #pp adds 0.5us start
                    

                    if self._tx_zero_end:
                        tx0_pulse_time = np.append(tx0_pulse_time, tx0_pulse_time[-1] + self._tx_t)
                        tx0_pulse_amp = np.append(tx0_pulse_amp, 0)
                    
                    tx0_amp = np.concatenate((tx0_amp, tx0_pulse_amp))
                    tx0_time = np.concatenate((tx0_time, tx0_pulse_time))
                    
                    tx0_gate_amp = np.concatenate((tx0_gate_amp, np.array([1.0, 0.0])))
                    if (tx0_pulse_time[0] - self._tx_warmup) < 0:
                        log.info('RF delay needs to be longer than RF deadtime (tx warmup)')
                    # tx0_gate_time = np.concatenate((tx0_gate_time,np.array([round(tx0_pulse_time[0] - self._tx_warmup, ndigits=6),tx0_pulse_time[-1]])))
                    tx0_gate_time = np.round(np.concatenate((tx0_gate_time, np.array([tx0_pulse_time[0] - self._tx_warmup, tx0_pulse_time[-1] + self._system.rf_ringdown_time]))), decimals = 6)  
          
            if block.adc is not None:
                # log.info('prescribed dwell time:', block.adc.dwell)
                self._rx_div = np.round(block.adc.dwell / self._clk_t).astype(int)
                self._rx_t = self._clk_t * self._rx_div
                rx_t_debug = self._rx_t
                # log.info('rx_t:', rx_t_debug)

                # log.info(self._rx_div * self._clk_t, '!= dwell')
                # log.info('Dwell time', block.adc.dwell, 'rounded to:', self._rx_t)
                
                rx0_start = block_duration + np.max([block.adc.dead_time, block.adc.delay])
                # rx0_start = block_duration + block.adc.dead_time + block.adc.delay # pp does this, why? TODO: Figure out adc in Sequence block_durations: could be a bug
                rx0_end = rx0_start + (block.adc.num_samples * self._rx_t) 
                # log.info('rx_time:', (rx0_end - rx0_start)* 1e6)

                rx0_gate_amp = np.concatenate((rx0_gate_amp, np.array([1.0, 0.0])))
                rx0_gate_time = np.concatenate((rx0_gate_time,np.array([rx0_start, rx0_end])))

                self._num_samples_total += block.adc.num_samples 
                if block.adc.freq_offset > 0:
                    self._lo_freq_center = self._center_freq + block.adc_freq_offset
                    
                
                
            block_duration += self._seq.block_durations[block_counter]
            
        block_duration_us = block_duration * 1e6
        self._block_duration_us = block_duration_us
        # Make all arrays shape compatible and test before putting it in a dict - roll it into a class' definition to clean up code
        if grad_vx_amp.shape[0] > 1:
            grad_vx_amp_cat = grad_vx_amp       
            grad_vx_time_cat = grad_vx_time * 1e6 # us
        else:   
            grad_vx_amp_cat = [0.0]
            grad_vx_time_cat = [0.0]
            
        if  grad_vy_amp.shape[0] > 1:    
            grad_vy_amp_cat = grad_vy_amp       
            grad_vy_time_cat = grad_vy_time * 1e6 # us
        else:
            grad_vy_amp_cat = [0.0]
            grad_vy_time_cat = [0.0]
             
        if grad_vz_amp.shape[0] > 1: 
            grad_vz_amp_cat = grad_vz_amp       
            grad_vz_time_cat = grad_vz_time  * 1e6 # us
        else:
            grad_vz_amp_cat = [0.0]
            grad_vz_time_cat = [0.0] 
            
        # Add this as dummy for now. not really sure whether we will depracate this
        grad_vz2_amp_cat = [0.0]
        grad_vz2_time_cat = [0.0] 
        
            
        # assert(grad_vx_amp_cat.shape == grad_vx_time_cat.shape), 'Issue with Gx waveform, cannot proceed' 
        # assert(grad_vy_amp_cat.shape == grad_vy_time_cat.shape), 'Issue with Gy waveform, cannot proceed' 
        # assert(grad_vz_amp_cat.shape == grad_vz_time_cat.shape), 'Issue with Gz waveform, cannot proceed' 
            
        if tx0_amp.shape[0] > 0: 
            tx0_amp_cat = tx0_amp       
            tx0_time_cat =tx0_time * 1e6 # us
            tx0_gate_amp_cat = tx0_gate_amp
            tx0_gate_time_cat = tx0_gate_time * 1e6 # us
            
        else:
            tx0_amp_cat =[0.0, 0.0]
            tx0_time_cat = [0.0, block_duration_us]
            tx0_gate_amp_cat = [0.0, 0.0]
            tx0_gate_time_cat = [0.0, block_duration_us]
            
        if rx0_gate_amp.shape[0] > 0: 
            rx0_gate_amp_cat = rx0_gate_amp      
            rx0_gate_time_cat = rx0_gate_time * 1e6 # us
            
        else:
            rx0_gate_amp_cat = [0.0]
            rx0_gate_time_cat =[0.0]
        
        # log.info('Obtained amplitudes and times for all blocks')
        # log.info('Making the flodict: six lines to the spectrometer')
       
        flo_dict = dict()
        # Tx - gate and first channel
        flo_dict['tx_gate'] = self.curate(tx0_gate_time_cat, tx0_gate_amp_cat)
        flo_dict['tx0'] = self.curate(tx0_time_cat, tx0_amp_cat)
        
        # Gradients
        flo_dict['grad_vx'] = self.curate(np.array(grad_vx_time_cat), np.array(grad_vx_amp_cat))
        flo_dict['grad_vy'] = self.curate(np.array(grad_vy_time_cat), np.array(grad_vy_amp_cat))
        flo_dict['grad_vz'] = self.curate(np.array(grad_vz_time_cat), np.array(grad_vz_amp_cat))
        flo_dict['grad_vz2'] = self.curate(np.array(grad_vz2_time_cat), np.array(grad_vz2_amp_cat))
        # Rx
        flo_dict['rx0_en'] = self.curate(rx0_gate_time_cat, rx0_gate_amp_cat)  # no control on sampling rate
        
        log.info('flodict', flo_dict)
        # Save the final dictionary as a property of the object
        self._grad_t = self._grad_t * 1e6 #us - seq world to marcos world
        self._rx_t = self._rx_t * 1e6 #us
        self._flo_dict = flo_dict

        
        
            