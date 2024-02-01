import os
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime

TIMESTAMPS_FILE_NAME = "heart_beat_timestamps"
FEATURES_DIRECTORY = "driver_status"
SESSION_DURATION = 10 # This is the duration of the session that will be classified
MAX_INTERVAL_BETWEEN_BEATS = 1200 # This is the maximum interval (mS) between two consecutive beats. Above that, there was a missing sample
PROF_TEST = True

class HeartBeatAnalysis:
    """ Class for the Study of the Heart-beat and the computation of the HRV Scores """

    def __init__(self):
        self.timeseries = []
        self.rr_intervals = []
        self.missing_samples = 0
        self.temp_rr_intervals = []
        self.features : dict = {}

    # https://github.com/sam-luby/ECG-Pi/blob/master/ecg/pan_tomp.py#L112
    def compute_rr_intervals(self):
        """ This function return the differences of every two-consecutive heart-beat-timestamps """
        self.rr_intervals[:] = []   #Empty the older rr_intervals
        for i in range(len(self.timeseries) - 1):
            diff = self.timeseries[i + 1] - self.timeseries[i]
            self.rr_intervals.append(diff)

    def get_session_duration(self):
        """ calcola la durata della sessione di campionamento attuale """
        return sum(self.rr_intervals)
    
    def session_duration_reached(self) -> bool :
        """ if the in the session has been sampled "#SESSION_DURATION second-samples", then returns True, else False """
        return ( self.get_session_duration() >= SESSION_DURATION )

    def empty_arrays(self):
        """ reset(WITHOUT CHANGING THE REFEENCED OBJECTS) the two arrays. You must NOT do -> self.timeseries[] = [] """
        self.timeseries[:] = []
        self.rr_intervals[:] = []

    def copy__rr_intervals__in__temp_rr_intervals(self):
        """ copy the rr_interval in temp_rr_intervals """
        self.temp_rr_intervals = self.rr_intervals.copy()
        self.features["rr_intervals"] = (',').join(map(str,self.temp_rr_intervals))

    def get_average_temp_rrintervals(self):
        """ ritorna la media degli rr_intervals """
        return np.average(self.temp_rr_intervals)
    
    def get_duration_temp_rrintervals(self):
        """ ritorna la media degli rr_intervals """
        return np.average(self.temp_rr_intervals)

    def compute_bpm(self):
        """ return the bmp """
        _session_duration = self.get_duration_temp_rrintervals()
        bpm = ( ( _session_duration / self.get_average_temp_rrintervals() )
               *
               ( 60 / _session_duration ) )
        print("bpm(): " + str(bpm))
        if(PROF_TEST):
            with open('statistics.csv', 'a') as file:
                file.write("bpm(): " + str(bpm) + "\n")
        self.features["bpm"] = bpm

    def compute_rmssd(self):
        """ calculate the RootMeanSquareSuccessiveDifferences RMSSD"""
        differences = np.diff(self.temp_rr_intervals)
        squared_differences = differences ** 2
        _sum = sum(squared_differences)
        intermediate_value = _sum / (len(differences) - 1 )
        rmssd = np.sqrt(intermediate_value)
        print("compute_rmssd(): " + str(rmssd))
        if(PROF_TEST):
            with open('statistics.csv', 'a') as file:
                file.write("compute_rmssd(): " + str(rmssd) + "\n")
        self.features["rmssd"] = (rmssd * 1000)
    
    def compute_standard_deviation(self):
        """ return the Standard Deviation of RR_intervals"""
        sd = np.std(self.temp_rr_intervals)
        print("compute_sdrr(): " + str(sd))
        if(PROF_TEST):
            with open('statistics.csv', 'a') as file:
                file.write("compute_standard_deviation(): " + str(sd) + "\n")
        self.features["sd"] = (sd * 1000)
    
    def compute_pnn(self, _x_milliseconds = 50):
        """ return the number of successive intervals that distance more than _x millisecond"""
        _len = len(self.temp_rr_intervals)
        NNx = 0
        for i in range(_len - 1):
            if (self.temp_rr_intervals[i + 1] - self.temp_rr_intervals[i]) > (_x_milliseconds/1000):
                NNx += 1
        pNNx = NNx / ( _len if _len != 0 else 1)
        print("compute_nn(): " + str(NNx) + " Percentage: " + str(pNNx))
        if(PROF_TEST):
            with open('statistics.csv', 'a') as file:
                file.write("compute_nn(): " + str(NNx) + "\n")
                file.write("Percentage(): " + str(pNNx) + "\n")
        self.features["pNN"] = pNNx
    
    def write_timeseries(self):
        """ write in .csvFile the timeseries """
        with open(TIMESTAMPS_FILE_NAME + '_' + str(SESSION_DURATION) + '.csv', 'a') as file:
            _len = len(self.timeseries) - 1
            for i, timestamp in enumerate(self.timeseries):
                file.write(str(timestamp) + (',' if i != _len else ''))

    def write_rrintervals(self):
        """ write in .csvFile the rr_intervals """
        with open(RR_FILE_NAME + '_' + str(SESSION_DURATION) + '.csv', 'a') as file:
            _len = len(self.temp_rr_intervals) - 1
            for i, temp_rr_interval in enumerate(self.temp_rr_intervals):
                file.write(str(temp_rr_interval) + (',' if i != _len else '\n'))

    def write_features(self, prediction):
        """ This function handle the log-features creation for the driver status condition.
            Creates a new CSV file for each hour in which stores the predictioned status for that sampling hour """
        folder_features_path = Path(FEATURES_DIRECTORY)
        if not folder_features_path.is_dir():
            os.makedirs(folder_features_path)

        current_time = datetime.now()
        formatted_time = current_time.strftime("%m-%d-%Y,%H") #driver_status/01-02-2024,10.csv
        time_features_name = FEATURES_DIRECTORY + "/" + formatted_time +'.csv' # EXAMPLE -> driver_status/01-02-2024,10:54.csv
        time_features_path = Path(time_features_name)
        if not time_features_path.is_file():
            print("Non esiste la cartella -> " + time_features_name)
            with open(time_features_name, 'a') as file:
                 file.write("HOUR:MINUTE, FEATURES[bpm, mean_rr, rmssd, sdnn, pnn50], PREDICTION\n")
        hour_minute = current_time.strftime("%H:%M") #10:02
        line = str(hour_minute) + ', ' +\
            str(self.features["bpm"]) + ',' +\
            str(self.get_average_temp_rrintervals()) + ',' +\
            str(self.features["rmssd"]) + ',' +\
            str(self.features["sd"]) + ',' +\
            str(self.features["pNN"]) + ', ' +\
            str(prediction)
        with open(time_features_name, 'a') as file:
            file.write(line + '\n')
        