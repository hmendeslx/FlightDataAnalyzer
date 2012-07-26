import csv
import mock
import numpy as np
import os
import unittest

from math import sqrt
from datetime import datetime

# A set of masked array test utilities from Pierre GF Gerard-Marchant
# http://www.java2s.com/Open-Source/Python/Math/Numerical-Python/numpy/numpy/ma/testutils.py.htm
import utilities.masked_array_testutils as ma_test

from analysis_engine.node import (A, KeyPointValue, KeyTimeInstance, KPV, KTI,
                                  P, S, Section)
from analysis_engine.library import *
from analysis_engine.plot_flight import plot_parameter

test_data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              'test_data')


class TestAlign(unittest.TestCase):
    
    def test_align_returns_same_array_if_aligned(self):
        slave = P('slave', np.ma.array(range(10)))
        master = P('master', np.ma.array(range(30)))
        aligned = align(slave, master)
        self.assertEqual(id(slave.array), id(aligned))
    
    def test_align_section_param(self):
        alt_aal = P('Altitude AAL', np.ma.arange(0, 5), frequency=1, offset=1)
        fast = S('Fast', frequency=4, offset=0.5)
        aligned = align(alt_aal, fast)
        self.assertEqual(len(aligned), 20)
        np.testing.assert_array_equal(aligned,
                                      [0, 0, 0, 0.25, 0.5, 0.75, 1, 1.25,
                                       1.5, 1.75, 2, 2.25, 2.5, 2.75, 3,
                                       3.25, 3.5, 3.75, 4, 4])
        
    def test_align_basic(self):
        class DumParam():
            def __init__(self):
                self.data_type = None
                self.offset = None
                self.frequency = None
                self.array = []
                
        first = DumParam()
        first.frequency = 4
        first.offset = 0.1
        first.array = np.ma.array(range(8))
        
        second = DumParam()
        second.frequency = 4
        second.offset = 0.2
        second.array = np.ma.array(range(8))
        
        result = align(second, first) #  sounds more natural so order reversed 20/11/11
        np.testing.assert_array_equal(result.data,
                                      [0.0, 0.6, 1.6, 2.6, 3.6,
                                       4.6, 5.6, 6.6000000000000005])
        np.testing.assert_array_equal(result.mask, False)
                
    def test_align_discrete(self):
        class DumParam():
            def __init__(self):
                self.data_type = None
                self.offset = None
                self.frequency = None
                self.array = []
                
        first = DumParam()
        first.frequency = 1
        first.offset = 0.0
        first.array = np.ma.array([0,0,1,1,0,1,0,1],dtype=float)
        
        second = DumParam()
        second.frequency = 1
        second.offset = 0.7
        second.array = np.ma.array([0,0,1,1,0,1,0,1],dtype=float)
        
        result = align(second, first, data_type='Discrete') #  sounds more natural so order reversed 20/11/11
        np.testing.assert_array_equal(result.data, [0,0,0,1,1,0,1,0])
        np.testing.assert_array_equal(result.mask, False)
                        
    def test_align_multi_state(self):
        class DumParam():
            def __init__(self):
                self.data_type = None
                self.offset = None
                self.frequency = None
                self.array = []
                
        first = DumParam()
        first.frequency = 1
        first.offset = 0.6
        first.array = np.ma.array([11,12,13,14,15],dtype=float)
        
        second = DumParam()
        second.frequency = 1
        second.offset = 0.0
        second.array = np.ma.array([0,1,2,3,4],dtype=float)
        
        result = align(second, first, data_type='Discrete') #  sounds more natural so order reversed 20/11/11
        np.testing.assert_array_equal(result.data, [1,2,3,4,4])
        np.testing.assert_array_equal(result.mask, False)
    
    def test_align_same_hz_delayed(self):
        # Both arrays at 1Hz, master behind slave in time
        class DumParam():
            def __init__(self):
                self.data_type = None
                self.offset = None
                self.frequency = 1
                self.array = []
        master = DumParam()
        master.array = np.ma.array([0,1,2,3],dtype=float)
        # It is necessary to force the data type, as otherwise the array is cast
        # as integer and the result comes out rounded down as well.
        master.frequency = 1
        master.offset = 0.5
        slave = DumParam()
        slave.array = np.ma.array([10,11,12,13],dtype=float)
        slave.frequency = 1
        slave.offset = 0.2
        result = align(slave, master)
        np.testing.assert_array_almost_equal(result.data, [10.3,11.3,12.3,13.0])
        np.testing.assert_array_equal(result.mask, False)
        
    def test_align_same_hz_advanced(self):
        # Both arrays at 1Hz, master ahead of slave in time
        class DumParam():
            def __init__(self):
                self.data_type = None
                self.offset = None
                self.frequency = 1
                self.array = []
        master = DumParam()
        master.array = np.ma.array([0,1,2,3],dtype=float)
        master.frequency = 1
        master.offset = 0.2
        slave = DumParam()
        slave.array = np.ma.array([10,11,12,13],dtype=float)
        slave.frequency = 1
        slave.offset = 0.5
        result = align(slave, master)
        np.testing.assert_array_almost_equal(result.data, [10.0,10.7,11.7,12.7])
        np.testing.assert_array_equal(result.mask, False)
        
    def test_align_increasing_hz_delayed(self):
        # Master at higher frequency than slave
        class DumParam():
            def __init__(self):
                self.data_type = None
                self.offset = None
                self.frequency = 1
                self.array = []
        master = DumParam()
        master.array = np.ma.array([0,1,2,3,4,6,6,7],dtype=float)
        # It is necessary to force the data type, as otherwise the array is cast
        # as integer and the result comes out rounded down as well.
        master.frequency = 4
        master.offset = 0.15
        slave = DumParam()
        slave.array = np.ma.array([10,11,12,13],dtype=float)
        slave.frequency = 2
        slave.offset = 0.1
        result = align(slave, master)
        np.testing.assert_array_almost_equal(result.data, [10.1,10.6,11.1,11.6,
                                                           12.1,12.6,13.0,13.0])
        np.testing.assert_array_equal(result.mask, False)
        
    def test_align_increasing_hz_advanced(self):
        # Master at higher frequency than slave
        class DumParam():
            def __init__(self):
                self.data_type = None
                self.offset = None
                self.frequency = 1
                self.array = []
        master = DumParam()
        master.array = np.ma.array([0,1,2,3,4,6,6,7,
                                   0,1,2,3,4,6,6,7],dtype=float)
        # It is necessary to force the data type, as otherwise the array is cast
        # as integer and the result comes out rounded down as well.
        master.frequency = 8
        master.offset = 0.1
        slave = DumParam()
        slave.array = np.ma.array([10,11,12,13],dtype=float)
        slave.frequency = 2
        slave.offset = 0.15
        result = align(slave, master)
        np.testing.assert_array_almost_equal(result.data, [10.0,10.15,10.4,10.65,
                                                           10.9,11.15,11.4,11.65,
                                                           11.9,12.15,12.4,12.65,
                                                           12.9,13.0 ,13.0,13.0 ])
        
    def test_align_mask_propogation(self):
        # Master at higher frequency than slave
        class DumParam():
            def __init__(self):
                self.data_type = None
                self.offset = None
                self.frequency = 1
                self.array = []
        master = DumParam()
        master.array = np.ma.array([0,1,2,3,4,6,6,7,
                                   0,1,2,3,4,6,6,7],dtype=float)
        # It is necessary to force the data type, as otherwise the array is cast
        # as integer and the result comes out rounded down as well.
        master.frequency = 8
        master.offset = 0.1
        slave = DumParam()
        slave.array = np.ma.array([10,11,12,13],dtype=float)
        slave.array[2] = np.ma.masked
        slave.frequency = 2
        slave.offset = 0.15
        result = align(slave, master)
        answer = np.ma.array(data = [10.0,10.15,10.4,10.65,
                                     10.9,0,0,0,
                                     0,0,0,0,
                                     0,13.0,13.0,13.0],
                             mask = [False,False,False,False,
                                     False, True, True, True,
                                     True , True, True, True,
                                     True ,False,False,False])
        ma_test.assert_masked_array_approx_equal(result, answer)

    def test_align_increasing_hz_extreme(self):
        # Master at higher frequency than slave
        class DumParam():
            def __init__(self):
                self.data_type = None
                self.offset = None
                self.frequency = 1
                self.array = []
        master = DumParam()
        master.array = np.ma.array([0,1,2,3,4,6,6,7,
                                   0,1,2,3,4,6,6,7],dtype=float)
        # It is necessary to force the data type, as otherwise the array is cast
        # as integer and the result comes out rounded down as well.
        master.frequency = 8
        master.offset = 0.1
        slave = DumParam()
        slave.array = np.ma.array([10,11],dtype=float)
        slave.frequency = 1
        slave.offset = 0.95
        result = align(slave, master)
        np.testing.assert_array_almost_equal(result.data,[10.0 ,10.0  ,10.0,10.0  ,
                                                          10.0 ,10.0  ,10.0,10.025,
                                                          10.15,10.275,10.4,10.525,
                                                          10.65,10.775,10.9,11.0  ])
        np.testing.assert_array_equal(result.mask, False)

    def test_align_across_frame_increasing(self):
        # Master at higher frequency than slave
        class DumParam():
            def __init__(self):
                self.data_type = None
                self.offset = None
                self.frequency = 1
                self.array = []
        master = DumParam()
        master.array = np.ma.zeros(64, dtype=float)
        # It is necessary to force the data type, as otherwise the array is cast
        # as integer and the result comes out rounded down as well.
        master.frequency = 8
        master.offset = 0.1
        slave = DumParam()
        slave.array = np.ma.array([10,11],dtype=float)
        slave.frequency = 0.25
        slave.offset = 3.95
        result = align(slave, master, interval='Frame')
        # Build the correct answer...
        answer=np.ma.ones(64)*10
        answer[31] = answer[31] + 0.00625
        for i in range(31):
            answer [31+i+1] = answer[31+i] + 1/32.0
        answer[-1] = 11.0
        # ...and check the resulting array in one hit.
        ma_test.assert_masked_array_approx_equal(result, answer)
        

    def test_align_across_frame_decreasing(self):
        # Master at higher frequency than slave
        class DumParam():
            def __init__(self):
                self.data_type = None
                self.offset = None
                self.frequency = 1
                self.array = []
        master = DumParam()
        master.array = np.ma.zeros(4, dtype=float)
        # It is necessary to force the data type, as otherwise the array is cast
        # as integer and the result comes out rounded down as well.
        master.frequency = 0.5
        master.offset = 1.5
        slave = DumParam()
        # Fill a two-frame sample with linear data
        slave.array = np.ma.arange(32,dtype=float)
        slave.frequency = 4
        slave.offset = 0.1
        result = align(slave, master, interval='Frame')
        # Build the correct answer...
        answer=np.ma.array([5.6,13.6,21.6,29.6])
        ma_test.assert_masked_array_approx_equal(result, answer)

    def test_align_superframe_master(self):
        class DumParam():
            def __init__(self):
                self.data_type = None
                self.offset = None
                self.frequency = 1
                self.offset = 0.0
                self.array = []
        master = DumParam()
        master.array = np.ma.array([1,2])
        master.frequency = 1/64.0
        slave = DumParam()
        slave.array = np.ma.arange(128)
        slave.frequency = 1
        result = align(slave, master)
        expected = [0,64]
        np.testing.assert_array_equal(result.data,expected)

    def test_align_superframe_slave(self):
        class DumParam():
            def __init__(self):
                self.data_type = None
                self.offset = None
                self.frequency = 1
                self.offset = 0.0
                self.array = []
        master = DumParam()
        master.array = np.ma.arange(64)
        master.frequency = 2
        slave = DumParam()
        slave.array = np.ma.array([1,3,6,9])
        slave.frequency = 1/8.0
        result = align(slave, master)
        expected = [1]*16+[3]*16+[6]*16+[9]*16
        np.testing.assert_array_equal(result.data,expected)

    def test_align_superframes_both(self):
        class DumParam():
            def __init__(self):
                self.data_type = None
                self.offset = None
                self.frequency = 1
                self.offset = 0.0
                self.array = []
        master = DumParam()
        master.array = np.ma.arange(16)
        master.frequency = 1/8.0
        slave = DumParam()
        slave.array = np.ma.arange(4)+100
        slave.frequency = 1/32.0
        result = align(slave, master)
        expected = [100]*4+[101]*4+[102]*4+[103]*4
        np.testing.assert_array_equal(result.data,expected)
        
    def test_align_8_hz_half_hz(self):
        class DumParam():
            def __init__(self):
                self.data_type = None
                self.offset = None
                self.frequency = 1
                self.offset = 0.0
                self.array = []
                
        master = DumParam()
        master.array = np.ma.arange(22576)
        master.frequency = 8.0
        slave = DumParam()
        slave.array = np.ma.arange(1411)
        slave.frequency = 0.5
        result = align(slave, master)
        self.assertTrue(False)
        #np.testing.assert_array_equal(result.data,expected) - test not implemented

    def test_align_superframe_to_onehz_multistate(self):
        # Slave once per superframe, master at 1Hz, Multi-State
        class DumParam():
            def __init__(self):
                self.data_type = None
                self.offset = None
                self.frequency = 1
                self.array = []
        onehz = P(frequency = 1)
        slave = DumParam()
        slave.array = np.ma.array([1, 2, 3, 4], dtype=float)
        slave.frequency = 1.0 / 64
        result = align(slave, onehz, data_type='Multi-state')
        expected = np.ma.array([1] * 64 + [2] * 64 + [3] * 64 + [4] * 64)
        np.testing.assert_array_equal(result.data, expected)
    
    
class TestBearingsAndDistances(unittest.TestCase):
    def test_known_distance(self):
        fareham = {'latitude':50.856146,'longitude':-1.183182}
        goodyear_lon = np.ma.array([-112.358214])
        goodyear_lat = np.ma.array([33.449806])
        brg,dist = bearings_and_distances(goodyear_lat, goodyear_lon, fareham)
        self.assertEqual(dist,[8481553.935041398])
        
    # With an atan(x/y) formula giving the bearings, it's easy to get this
    # wrong, as I did originally, hence the three tests for bearings ! The
    # important thing to remember is we are looking for the bearing from the
    # reference point to the array points, not the other way round.
    def test_quarter_bearings(self):
        origin = {'latitude':0.0,'longitude':0.0}
        latitudes = np.ma.array([.1,.1,-.1,-.1])
        longitudes = np.ma.array([-.1,.1,.1,-.1])
        # Bearings changed from +/-180 to 0:360 when this function was used
        # to populate runway magnetic headings in the airport database.
        compass = np.ma.array([360-45,45,135,360-135])
        brg, dist = bearings_and_distances(latitudes, longitudes, origin)
        ma_test.assert_masked_array_approx_equal(brg, compass)

    def test_ordinal_bearings(self):
        origin = {'latitude':0.0,'longitude':0.0}
        latitudes = np.ma.array([1,0,-1,0])
        longitudes = np.ma.array([0,1,0,-1])
        compass = np.ma.array([0,90,180,270])
        brg, dist = bearings_and_distances(latitudes, longitudes, origin)
        ma_test.assert_masked_array_approx_equal(brg, compass)

    def test_known_bearings(self):
        origin = {'latitude':60.280151,'longitude':5.222579}
        latitudes = np.ma.array([60.2789,60.30662494,60.289,60.28875])
        longitudes = np.ma.array([5.223,5.21370074,5.2272,5.2636])
        compass = np.ma.array([170,351,14,67])
        brg, dist = bearings_and_distances(latitudes, longitudes, origin)
        for i in range(4):
            self.assertLess(abs(compass[i]-brg[i]),1.0)

    def test_mask(self):
        origin = {'latitude':0.0,'longitude':0.0}
        latitudes = np.ma.array([.1,.1,-.1,-.1])
        latitudes[0]=np.ma.masked
        longitudes = np.ma.array([-.1,.1,.1,-.1])
        longitudes[2]=np.ma.masked
        # Bearings changed from +/-180 to 0:360 when this function was used
        # to populate runway magnetic headings in the airport database.
        compass = np.ma.array([135,45,360-45,360-135])
        compass.mask=[True,False,True,False]
        brg, dist = bearings_and_distances(latitudes, longitudes, origin)
        ma_test.assert_masked_array_approx_equal(brg, compass)
        self.assertEqual(dist[0].mask,True)
        self.assertEqual(dist[2].mask,True)


class TestLatitudesAndLongitudes(unittest.TestCase):
    def test_known_distance(self):
        fareham = {'latitude': 50.852731,'longitude': -1.185608}
        pompey_dist = np.ma.array([10662.0])
        pompey_brg = np.ma.array([126.45])
        lat,lon = latitudes_and_longitudes(pompey_brg, pompey_dist, fareham)
        self.assertAlmostEqual(lat,[50.79569963])
        self.assertAlmostEqual(lon,[-1.06358672])
        
        # TODO - Test with array and masks (for Brg/Dist also?)
        

class TestBlendEquispacedSensors(unittest.TestCase):
    def test_blend_alternate_sensors_basic(self):
        array_1 = np.ma.array([0, 0, 1, 1],dtype=float)
        array_2 = np.ma.array([5, 5, 6, 6],dtype=float)
        result = blend_equispaced_sensors (array_1, array_2)
        np.testing.assert_array_equal(result.data, [2.5,2.5,2.5,2.75,3.25,3.5,3.5,3.5])
        np.testing.assert_array_equal(result.mask, [False,False,False,False,
                                                   False,False,False,False])
    
    def test_blend_alternate_sensors_masked(self):
        array_1 = np.ma.array(data = [0, 0, 1, 1, 2, 2],dtype=float,
                              mask = [0, 1, 0, 0, 0, 1])
        array_2 = np.ma.array(data = [5, 5, 6, 6, 7, 7],dtype=float,
                              mask = [0, 0, 1, 0, 0, 1])
        result = blend_equispaced_sensors (array_1, array_2)
        np.testing.assert_array_equal(result.data,[2.5,5.0,5.0,5.0,1.0,1.0,
                                                   1.0,3.75,4.25,7.0,0.0,0.0])
        np.testing.assert_array_equal(result.mask, [False,False,False,False,False,False,
                                                   False,False,False,False,True,True])
    
class TestBlendNonequispacedSensors(unittest.TestCase):
    def test_blend_alternate_sensors_basic(self):
        array_1 = np.ma.array([0, 0, 1, 1],dtype=float)
        array_2 = np.ma.array([5, 5, 6, 6],dtype=float)
        result = blend_nonequispaced_sensors (array_1, array_2, 'Follow')
        np.testing.assert_array_equal(result.data, [2.5,2.5,2.5,3,3.5,3.5,3.5,3.5])
        np.testing.assert_array_equal(result.mask, [False,False,False,False,
                                                   False,False,False,True])

    def test_blend_alternate_sensors_mask(self):
        array_1 = np.ma.array([0, 0, 1, 1],dtype=float)
        array_2 = np.ma.array([5, 5, 6, 6],dtype=float)
        array_1[2] = np.ma.masked
        result = blend_nonequispaced_sensors (array_1, array_2, 'Follow')
        np.testing.assert_array_equal(result.data[0:3], [2.5,2.5,2.5])
        np.testing.assert_array_equal(result.data[6:8], [3.5,3.5])
        np.testing.assert_array_equal(result.mask, [False,False,False,
                                                    True,True,False,
                                                    False,True])

    def test_blend_alternate_sensors_reverse(self):
        array_1 = np.ma.array([0, 0, 1, 1],dtype=float)
        array_2 = np.ma.array([5, 5, 6, 6],dtype=float)
        result = blend_nonequispaced_sensors (array_1, array_2, 'Precede')
        np.testing.assert_array_equal(result.data, [2.5,2.5,2.5,2.5,3,3.5,3.5,3.5])
        np.testing.assert_array_equal(result.mask, [True,False,False,False,
                                                    False,False,False,False])


class TestCalculateTimebase(unittest.TestCase):
    def test_calculate_timebase(self):
        # 6th second is the first valid datetime(2020,12,25,23,59,0)
        years = [None] * 6 + [2020] * 19  # 6 sec offset
        months = [None] * 5 + [12] * 20
        days = [None] * 4 + [24] * 5 + [25] * 16
        hours = [None] * 3 + [23] * 7 + [00] * 15
        mins = [None] * 2 + [59] * 10 + [01] * 13
        secs = [None] * 1 + range(55, 60) + range(19)  # 6th second in next hr
        start_dt = calculate_timebase(years, months, days, hours, mins, secs)
        
        #>>> datetime(2020,12,25,00,01,19) - timedelta(seconds=25)
        #datetime.datetime(2020, 12, 25, 0, 0, 50)
        self.assertEqual(start_dt, datetime(2020, 12, 25, 0, 0, 54))
        
    def test_no_valid_datetimes_raises_valueerror(self):
        years = [None] * 20
        months = [None] * 20
        days = [None] * 4 + [24] * 5 + [25] * 16
        hours = [None] * 3 + [23] * 7 + [00] * 15
        mins = [None] * 2 + [59] * 10 + [01] * 13
        secs = [None] * 1 + range(55, 60) + range(19)  # 6th second in next hr
        self.assertRaises(InvalidDatetime, calculate_timebase, years, months, days, hours, mins, secs)
        
        
    def test_uneven_length_arrays(self):
        "Tests that the uneven drabs at the end are ignored"
        # You should always pass in complete arrays at the moment!
        years = [None] * 1 + [2020] * 10  # uneven
        months = [None] * 5 + [12] * 20
        days = [None] * 4 + [24] * 5 + [25] * 16
        hours = [None] * 3 + [23] * 7 + [00] * 1 # uneven
        mins = [None] * 2 + [59] * 10 + [01] * 13
        secs = [None] * 1 + range(55, 60) + range(19)
        start_dt = calculate_timebase(years, months, days, hours, mins, secs)
        self.assertEqual(start_dt, datetime(2020,12,24,23,58,54))
        
    def test_no_change_in_dt_picks_it_as_start(self):
        # also tests using numpy masked arrays
        years = np.ma.array([2020] * 20)  # 6 sec offset
        months = np.ma.array([12] * 20)
        days = np.ma.array([25] * 20)
        hours = np.ma.array([23] * 20)
        mins = np.ma.array([0] * 20)
        secs = np.ma.array([0] * 20) # 6th second in next hr
        start_dt = calculate_timebase(years, months, days, hours, mins, secs)
        self.assertEqual(start_dt, datetime(2020,12,25,23,0,0))
        
    def test_real_data_params_2_digit_year(self):
        years = np.load(os.path.join(test_data_path, 'year.npy'))
        months = np.load(os.path.join(test_data_path, 'month.npy'))
        days = np.load(os.path.join(test_data_path, 'day.npy'))
        hours = np.load(os.path.join(test_data_path, 'hour.npy'))
        mins = np.load(os.path.join(test_data_path, 'minute.npy'))
        secs = np.load(os.path.join(test_data_path, 'second.npy'))
        start_dt = calculate_timebase(years, months, days, hours, mins, secs)
        self.assertEqual(start_dt, datetime(2011,12,30,8,20,36))
        
    def test_real_data_params_no_year(self):
        months = np.load(os.path.join(test_data_path, 'month.npy'))
        days = np.load(os.path.join(test_data_path, 'day.npy'))
        hours = np.load(os.path.join(test_data_path, 'hour.npy'))
        mins = np.load(os.path.join(test_data_path, 'minute.npy'))
        secs = np.load(os.path.join(test_data_path, 'second.npy'))
        years = np.array([2012]*len(months)) # fixed year
        start_dt = calculate_timebase(years, months, days, hours, mins, secs)
        self.assertEqual(start_dt, datetime(2012,12,30,8,20,36))
        
    @unittest.skip("Implement if this is a requirement")
    def test_using_offset_for_seconds(self):
        # check offset milliseconds are applied to the timestamps
        self.assertFalse(True)
        
        
class TestConvertTwoDigitToFourDigitYear(unittest.TestCase):
    def test_convert_two_digit_to_four_digit_year(self):
        # WARNING - this test will fail next year(!)
        self.assertEquals(convert_two_digit_to_four_digit_year(99), 1999)
        self.assertEquals(convert_two_digit_to_four_digit_year(13), 1913)
        self.assertEquals(convert_two_digit_to_four_digit_year(12), 2012) # will break next year
        self.assertEquals(convert_two_digit_to_four_digit_year(11), 2011)
        self.assertEquals(convert_two_digit_to_four_digit_year(1), 2001)
        
        
class TestCoReg(unittest.TestCase):
    def test_correlation_basic(self):
        x=np.ma.array([0,1,2,4,5,7], dtype=float)
        y=np.ma.array([2,4,5,3,6,8], dtype=float)
        correlate, slope, offset = coreg(y, indep_var=x)
        self.assertAlmostEqual(correlate, 0.818447591071135)
        self.assertAlmostEqual(slope, 0.669856459330144)
        self.assertAlmostEqual(offset, 2.54545454545455)
        
    def test_correlation_masked(self):
        x=np.ma.array([0,1,2,4,5,7], mask=[0,0,1,0,0,0], dtype=float)
        y=np.ma.array([2,4,5,3,6,8], mask=[0,0,0,0,1,0], dtype=float)
        correlate, slope, offset = coreg(y, indep_var=x)
        self.assertAlmostEqual(correlate, 0.841685056859012)
        self.assertAlmostEqual(slope, 0.7)
        self.assertAlmostEqual(offset, 2.15)
        
    def test_correlation_raises_error_unequal(self):
        x=np.ma.array([0,1,2,4,5,7], dtype=float)
        y=np.ma.array([-2,-4,-5,-3,-6], dtype=float)
        self.assertRaises(ValueError, coreg, y, indep_var=x)
        
    def test_correlation_raises_error_too_short(self):
        y=np.ma.array([1], dtype=float)
        self.assertRaises(ValueError, coreg, y)
    
    def test_correlation_constant_arrays(self):
        x=np.ma.array([0,0,0,0,0,0], dtype=float)
        y=np.ma.arange(6)
        self.assertEqual(coreg(x), (0.0, 0.0, 0.0))
        self.assertEqual(coreg(x, indep_var=y), (0.0, 0.0, 0.0))
        self.assertEqual(coreg(y, indep_var=x), (0.0, 0.0, 0.0))
    
    def test_correlation_monotonic_independent_variable(self):
        y=np.ma.array([2,4,5,3,6,8], dtype=float)
        correlate, slope, offset = coreg(y)
        self.assertAlmostEqual(correlate, 0.841281820819169)
        self.assertAlmostEqual(slope, 0.971428571428571)
        self.assertAlmostEqual(offset, 2.23809523809524)
        
    def test_correlation_only_return(self):
        y=np.ma.array([2,4,5,3,6,8], dtype=float)
        correlate,d1,d2 = coreg(y)  # You need to cater for the three return arguments.
        self.assertAlmostEqual(correlate, 0.841281820819169)
        
    def test_correlation_forced_zero(self):
        y=np.ma.array([2,4,5,3,6,8], dtype=float)
        correlate, slope, offset = coreg(y, force_zero=True)
        self.assertAlmostEqual(slope, 1.58181818181818)
        self.assertAlmostEqual(offset, 0.0)
        
    def test_correlation_negative_slope(self):
        x=np.ma.array([0,1,2,4,5,7], dtype=float)
        y=np.ma.array([-2,-4,-5,-3,-6,-8], dtype=float)
        correlate, slope, offset = coreg(y,indep_var=x)
        self.assertAlmostEqual(correlate, 0.818447591071135)
        self.assertAlmostEqual(slope, -0.669856459330144)
        self.assertAlmostEqual(offset, -2.54545454545455)


class TestClip(unittest.TestCase):
    # Previously known as Duration
    def setUp(self):
        test_list = []
        result_list = []
        duration_test_data_path = os.path.join(test_data_path,
                                               'duration_test_data.csv')
        with open(duration_test_data_path, 'rb') as csvfile:
            self.reader = csv.DictReader(csvfile)
            for row in self.reader:
                test_list.append(float(row['input']))
                result_list.append(float(row['output']))
        self.test_array = np.array(test_list)
        self.result_array = np.array(result_list)

    def test_clip_example_of_use(self):
        # Engine temperature at startup limit = 900 C for 5 seconds, say.

        # Pseudo-POLARIS exceedance would be like this:
        # Exceedance = clip(Eng_1_Gas_Temp,5sec,1Hz) > 900
        
        # In this case it was over 910 for 5 seconds, hence is an exceedance.
        
        # You get 6 values in the output array for a 5-second duration event.
        # Remember, fenceposts and panels.

        engine_egt = np.array([600.0,700.0,800.0,910.0,950.0,970.0,940.0,\
                                960.0,920.0,890.0,840.0,730.0])
        output_array = np.array([600.0,600.0,600.0,700.0,800.0,910.0,920.0,\
                                890.0,840.0,730.0,730.0,730.0])
        result = clip(engine_egt,5)
        np.testing.assert_array_equal(result, output_array)
        
    def test_clip_correct_result(self):
        result = clip(self.test_array, 5)
        np.testing.assert_array_almost_equal(result, self.result_array)
    
    def test_clip_rejects_negative_period(self):
        an_array = np.array([0,1])
        self.assertRaises(ValueError, clip, an_array, -0.2)
        
    def test_clip_rejects_negative_hz(self):
        an_array = np.array([0,1])
        self.assertRaises(ValueError, clip, an_array, 0.2, hz=-2)
        
    def test_clip_rejects_zero_period(self):
        an_array = np.array([0,1])
        self.assertRaises(ValueError, clip, an_array, 0.0)
        
    def test_clip_rejects_zero_hz(self):
        an_array = np.array([0,1])
        self.assertRaises(ValueError, clip, an_array, 1.0, hz=0.0)
        
    def test_clip_rejects_meaningless_call(self):
        an_array = np.array([0,1])
        self.assertRaises(ValueError, clip, an_array, 1.0, remove='everything')
        
    def test_clip_minimum(self):
        an_array = np.array([9,8,7,6,5,4,3,2,1,2,3,4,5,6,7,8])
        result = clip(an_array, 5, remove='troughs')
        expected = np.array([9,9,9,8,7,6,5,4,3,4,5,6,7,8,8,8])
        np.testing.assert_array_almost_equal(result, expected)

    def test_clip_all_masked(self):
        array = np.ma.array(data=[1,2,3],mask=[1,1,1])
        result = clip(array, 3)
        np.testing.assert_array_equal(result.mask, array.mask)

class TestCycleCounter(unittest.TestCase):
    def test_cycle_counter(self):
        array = np.ma.sin(np.ma.arange(100)*0.7+3)+np.ma.sin(np.ma.arange(100)*0.82)
        end_index, n_cycles = cycle_counter(array, 3.0, 10, 1.0, 0)
        self.assertEqual(n_cycles, 3)
        self.assertEqual(end_index, 91)

    def test_cycle_counter_with_offset(self):
        array = np.ma.sin(np.ma.arange(100)*0.7+3)+np.ma.sin(np.ma.arange(100)*0.82)
        end_index, n_cycles = cycle_counter(array, 3.0, 10, 1.0, 1234)
        self.assertEqual(end_index, 1234+91)
        
    def test_cycle_counter_too_slow(self):
        array = np.ma.sin(np.ma.arange(100)*0.7+3)+np.ma.sin(np.ma.arange(100)*0.82)
        end_index, n_cycles = cycle_counter(array, 3.0, 1, 1.0, 0)
        self.assertEqual(n_cycles, None)
        self.assertEqual(end_index, None)
        
    def test_cycle_counter_empty(self):
        array=np.ma.array([])
        end_index, n_cycles = cycle_counter(array, 3.0, 10, 1.0, 0)
        self.assertEqual(n_cycles, None)
        self.assertEqual(end_index, None)
        

class TestCycleFinder(unittest.TestCase):
    def test_cycle_finder_basic(self):
        array = np.ma.array([0,1,3.8,1,0.3,1,2,3,2,1,2,3,4,3,2])
        idxs, vals = cycle_finder(array, min_step=2.1, include_ends=False)
        np.testing.assert_array_equal(idxs, [2, 4, 12])
        np.testing.assert_array_equal(vals, [3.8,0.3,4])
        
    def test_cycle_finder_default(self):
        array = np.ma.array([0,1,3.8,1,0.3,1,2,3,2,1,2,3,4,3,2])
        idxs, vals = cycle_finder(array)
        np.testing.assert_array_equal(idxs, [ 0, 2, 4, 7, 9,12,15])
        np.testing.assert_array_equal(vals, [ 0., 3.8, 0.3, 3., 1., 4., 2.])
        
    def test_cycle_finder_null(self):
        array = np.ma.array([0,1,3.8,1,0.3,1,2,3,2,1,2,3,4,3,2])
        idxs, vals = cycle_finder(array, min_step=15)
        np.testing.assert_array_equal(idxs, None)
        np.testing.assert_array_equal(vals, None)
        
    def test_cycle_finder_ramp(self):
        array = np.ma.array([0,1,2])
        idxs, vals = cycle_finder(array, include_ends=False)
        np.testing.assert_array_equal(idxs, None)
        np.testing.assert_array_equal(vals, None)
        
    def test_cycle_finder_removals(self):
        array = np.ma.array([0,1,2,1,2,3,2,1,2,3,4,5,4,5,6])
        idxs, vals = cycle_finder(array, min_step=1.5)
        np.testing.assert_array_equal(idxs, [0,5,7,15])
        np.testing.assert_array_equal(vals, [0,3,1,6])

class TestDatetimeOfIndex(unittest.TestCase):
    def test_index_of_datetime(self):
        start_datetime = datetime.now()
        index = 160
        frequency = 4
        dt = datetime_of_index(start_datetime, index, frequency=frequency)
        self.assertEqual(dt, start_datetime + timedelta(seconds=40))

class TestFindEdges(unittest.TestCase):
    # Reminder: find_edges(array, _slice, direction='rising_edges')                    
    
    def test_find_edges_basic(self):
        array=np.ma.array([0,0,0,1,1,1])
        result = find_edges(array, slice(0,6))
        expected = [2.5]
        self.assertEqual(expected, result)
                    
    def test_find_edges_slice(self):
        array=np.ma.array([0,0,0,1,1,1])
        result = find_edges(array, slice(0,2))
        expected = []
        self.assertEqual(expected, result)
                    
    def test_find_edges_default_direction(self):
        array=np.ma.array([0,0,0,-1,-1,-1])
        result = find_edges(array, slice(0,6))
        expected = []
        self.assertEqual(expected, result)

    def test_find_edges_falling(self):
        array=np.ma.array([2,2,2,2,0,0])
        result = find_edges(array, slice(0,6), direction='falling_edges')
        expected = [3.5]
        self.assertEqual(expected, result)
                         
    def test_find_edges_falling(self):
        array=np.ma.array([1,1,0,0,2,2,0,0,-1-1])
        result = find_edges(array, slice(0,10), direction='all_edges')
        expected = [1.5,3.5,5.5,7.5]
        self.assertEqual(expected, result)
        
    def test_find_edges_failure(self):
        array=np.ma.array([1])
        self.assertRaises(ValueError, find_edges, array, slice(0,1), direction='anything')
                    
                    
class TestFirstOrderLag(unittest.TestCase):

    # first_order_lag (in_param, time_constant, hz, gain = 1.0, initial_value = 0.0)
    
    def test_firstorderlag_time_constant(self):
        # Note: Also tests initialisation.
        array = np.ma.zeros(10)
        # The result of processing this data is...
        result = first_order_lag (array, 2.0, 1.0, initial_value = 1.0)
        # The correct answer is...
        answer = np.ma.array(data=[0.8,0.48,0.288,0.1728,0.10368,0.062208,
                                   0.0373248,0.02239488,0.01343693,0.00806216],
                             mask = False)
        ma_test.assert_masked_array_approx_equal(result, answer)

    def test_firstorderlag_sample_rate_chage(self):
        # Note: Also tests initialisation.
        array = np.ma.zeros(10)
        # The result of processing this data is...
        result = first_order_lag (array, 2.0, 2.0, initial_value = 1.0)
        # The correct answer is...
        answer = np.ma.array(data=[0.88888889,0.69135802,0.53772291,0.41822893,
                                 0.32528917,0.25300269,0.19677987,0.15305101,
                                 0.11903967,0.09258641], mask = False)
        ma_test.assert_masked_array_approx_equal(result, answer)

    def test_firstorderlag_gain(self):
        array = np.ma.ones(20)
        result = first_order_lag (array, 1.0, 1.0, gain = 10.0)
        # With a short time constant and more samples, the end result will
        # reach the input level (1.0) multiplied by the gain.
        self.assertAlmostEquals(result.data[-1], 10.0)

    def test_firstorderlag_stability_check(self):
        array = np.ma.ones(4)
        # With a time constant of 1 and a frequency of 4, the simple algorithm
        # becomes too inaccurate to be useful.
        self.assertRaises(ValueError, first_order_lag, array, 0.2, 1.0)

    def test_firstorderlag_mask_retained(self):
        array = np.ma.zeros(5)
        array[3] = np.ma.masked
        result = first_order_lag (array, 1.0, 1.0, initial_value = 1.0)
        ma_test.assert_mask_eqivalent(result.mask, [0,0,0,1,0], err_msg='Masks are not equal')

class TestFirstOrderWashout(unittest.TestCase):

    # first_order_washout (in_param, time_constant, hz, gain = 1.0, initial_value = 0.0)
    
    def test_firstorderwashout_time_constant(self):
        array = np.ma.ones(10)
        result = first_order_washout (array, 2.0, 1.0, initial_value = 0.0)
        # The correct answer is the same as for the first order lag test, but in
        # this case we are starting from zero and the input data is all 1.0.
        # The washout responds transiently then washes back out to zero, 
        # providing the high pass filter that matches the low pass lag filter.
        answer = np.ma.array(data=[0.8,0.48,0.288,0.1728,0.10368,0.062208,
                                   0.0373248,0.02239488,0.01343693,0.00806216],
                             mask = False)
        ma_test.assert_masked_array_approx_equal(result, answer)

    def test_firstorderwashout_sample_rate_chage(self):
        # Note: Also tests initialisation.
        array = np.ma.zeros(10)
        '''
        OK. Tricky test that needs some explanation.
        
        The initial value is the steady state input condition prior to the data 
        we supply. This filter is a washout (high pass) filter, so the steady 
        state output will always be zero.
        
        The initial condition is set to -1.0, then when the data arrives, 
        array[0]=0.0 gives a +1.0 step change to the input and we get a positive 
        kick on the output.
        '''
        result = first_order_washout (array, 2.0, 0.5, initial_value = -1.0)
        # The correct answer is...
        answer = np.ma.array(data=[6.66666667e-01,2.22222222e-01,7.40740741e-02,
                                   2.46913580e-02,8.23045267e-03,2.74348422e-03,
                                   9.14494742e-04,3.04831581e-04,1.01610527e-04,
                                   3.38701756e-05], mask = False)
        ma_test.assert_masked_array_approx_equal(result, answer)

    def test_firstorderwashout_gain(self):
        array = np.ma.ones(20)
        result = first_order_washout (array, 1.0, 1.0, gain = 10.0, initial_value = 0.0)
        # With a short time constant and more samples, the end result will
        # reach the input level (1.0) multiplied by the gain.
        self.assertAlmostEquals(result.data[0], 6.6666667)

    def test_firstorderwashout_stability_check(self):
        array = np.ma.ones(4)
        # With a time constant of 1 and a frequency of 4, the simple algorithm
        # becomes too inaccurate to be useful.
        self.assertRaises(ValueError, first_order_washout, array, 0.2, 1.0)

    def test_firstorderwashout_mask_retained(self):
        array = np.ma.zeros(5)
        array[3] = np.ma.masked
        result = first_order_washout (array, 1.0, 1.0, initial_value = 1.0)
        ma_test.assert_mask_eqivalent(result.mask, [0,0,0,1,0], err_msg='Masks are not equal')
    
    
    
class TestFirstValidSample(unittest.TestCase):
    def test_first_valid_sample(self):
        result = first_valid_sample(np.ma.array(data=[11,12,13,14],mask=[1,0,1,0]))
        self.assertEqual(result, (1, 12))
        
    def test_first_valid_sample_all_masked(self):
        result = first_valid_sample(np.ma.array(data=[11,12,13,14],mask=True))
        self.assertEqual(result, (None, None))

    def test_first_valid_sample_offset(self):
        result = first_valid_sample(np.ma.array(data=[11,12,13,14],mask=[1,0,1,0]),2)
        self.assertEqual(result, (3,14))

    def test_first_valid_sample_at_offset(self):
        result = first_valid_sample(np.ma.array(data=[11,12,13,14],mask=[1,0,1,0]),1)
        self.assertEqual(result, (1,12))

    def test_first_valid_sample_overrun(self):
        result = first_valid_sample(np.ma.array(data=[11,12,13,14],mask=[1,0,1,0]),9)
        self.assertEqual(result, (None, None))
        
    def test_first_valid_sample_underrun(self):
        result = first_valid_sample(np.ma.array(data=[11,12,13,14],mask=[1,0,1,0]),-2)
        self.assertEqual(result, (None, None))
        
class TestLastValidSample(unittest.TestCase):
    def test_last_valid_sample(self):
        result = last_valid_sample(np.ma.array(data=[11,12,13,14],mask=[1,0,1,0]))
        self.assertEqual(result, (3,14))
        
    def test_last_valid_sample_all_masked(self):
        result = last_valid_sample(np.ma.array(data=[11,12,13,14],mask=True))
        self.assertEqual(result, (None, None))

    def test_last_valid_sample_offset(self):
        result = last_valid_sample(np.ma.array(data=[11,12,13,14],mask=[1,0,1,0]),-2)
        self.assertEqual(result, (1,12))

    def test_last_valid_sample_at_offset(self):
        result = last_valid_sample(np.ma.array(data=[11,12,13,14],mask=[1,0,1,0]),-3)
        self.assertEqual(result, (1,12))

    def test_last_valid_sample_overrun(self):
        result = last_valid_sample(np.ma.array(data=[11,12,13,14],mask=[1,0,1,0]),9)
        self.assertEqual(result, (None, None))
        
class TestRunwayDistanceFromEnd(unittest.TestCase):
    def test_null(self):
        runway =  {'end': {'latitude': 60.280151, 
                      'longitude': 5.222579}, 
              'localizer': {'latitude': 60.2789, 
                            'longitude': 5.223}, 
              'glideslope': {'latitude': 60.300981,
                             'longitude': 5.214092, 
                             'threshold_distance': 1161}, 
              'start': {'latitude': 60.30662494, 
                        'longitude': 5.21370074}}
        result = runway_distance_from_end(runway, 60.280151, 5.222579)
        expected = 0.0
        self.assertEqual(result, expected)
    
    def test_runway_dist_by_coordinates(self):
        runway =  {'end': {'latitude': 60.280151, 
                      'longitude': 5.222579}, 
              'localizer': {'latitude': 60.2789, 
                            'longitude': 5.223}, 
              'glideslope': {'latitude': 60.300981,
                             'longitude': 5.214092, 
                             'threshold_distance': 1161}, 
              'start': {'latitude': 60.30662494, 
                        'longitude': 5.21370074}}
        result = runway_distance_from_end(runway, 60.30662494, 5.21370074)
        expected = 2984.0
        self.assertAlmostEqual(result, expected, places=0)
        
    def test_runway_dist_by_identifier(self):
        runway =  {'end': {'latitude': 60.280151, 
                      'longitude': 5.222579}, 
              'localizer': {'latitude': 60.2789, 
                            'longitude': 5.223}, 
              'glideslope': {'latitude': 60.300981,
                             'longitude': 5.214092, 
                             'threshold_distance': 1161}, 
              'start': {'latitude': 60.30662494, 
                        'longitude': 5.21370074}}
        result = runway_distance_from_end(runway, point='start')
        expected = 2984.0
        self.assertAlmostEqual(result, expected, places=0)
    
    def test_runway_dist_not_recognised(self):
        runway =  {'end': {'latitude': 60.280151, 
                      'longitude': 5.222579},
              'start': {'latitude': 60.30662494, 
                        'longitude': 5.21370074}}
        self.assertRaises(ValueError, runway_distance_from_end, runway, point='threshold')
         
class TestRunwayDistances(unittest.TestCase):
    # This single test case uses data for Bergen and has been checked against
    # Google Earth measurements for reasonable accuracy.
    def test_runway_distances(self):
        result = []
        runway =  {'end': {'latitude': 60.280151, 
                              'longitude': 5.222579}, 
                      'localizer': {'latitude': 60.2789, 
                                    'frequency': u'109900M', 
                                    'longitude': 5.223, 
                                    'heading': 173, 
                                    'beam_width': 4.5}, 
                      'glideslope': {'latitude': 60.300981, 
                                     'frequency': u'333800M', 
                                     'angle': 3.1, 
                                     'longitude': 5.214092, 
                                     'threshold_distance': 1161}, 
                      'start': {'latitude': 60.30662494, 
                                'longitude': 5.21370074}, 
                      'strip': {'width': 147, 'length': 9810, 
                                'id': 4097, 'surface': u'ASP'}, 
                      'identifier': u'17', 'id': 8193}
        result = runway_distances(runway)
        
        # Forced failure. the Bergen runway details need amending to remove undershoot areas.
        self.assertAlmostEqual(result[0],9999, places=0)
        # correct:self.assertAlmostEqual(result[0],3125, places=0)
        self.assertAlmostEqual(result[1],2503, places=0)
        self.assertAlmostEqual(result[2],141.0, places=1)
        # Optional glideslope antenna projected position...
        self.assertAlmostEqual(result[3],60.3, places=1)
        self.assertAlmostEqual(result[4],5.22, places=2)


class TestRunwayHeading(unittest.TestCase):
    # This single test case uses data for Bergen and has been checked against
    # Google Earth measurements for reasonable accuracy.
    def test_runway_heading(self):
        runway =  {'end': {'latitude': 60.280151, 
                              'longitude': 5.222579}, 
                      'localizer': {'latitude': 60.2789, 
                                    'longitude': 5.223, 
                                    'heading': 999}, 
                      'start': {'latitude': 60.30662494, 
                                'longitude': 5.21370074}, 
}
        rwy_hdg = runway_heading(runway)
        self.assertLess(abs(rwy_hdg - 170.6), 0.3)
        
class TestGroundTrack(unittest.TestCase):
    def test_ground_track_basic(self):
        gspd = np.ma.array([60,60,60,60,60,60,60])
        hdg = np.ma.array([0,0.0,0.0,90,90,90,270])
        lat, lon = ground_track(0.0, 0.0, gspd, hdg, 1.0, 'landing')
        expected_lat = [0.0,0.00027759,0.00055518,0.00069398,0.00069398,0.00069398,0.00069398]
        expected_lon = [0.0,0.0,0.0,0.00013880,0.00041639,0.00069398,0.00069398]
        np.testing.assert_array_almost_equal(expected_lat, lat)
        np.testing.assert_array_almost_equal(expected_lon, lon)
    def test_ground_track_data_errors(self):
        # Mismatched array lengths
        gspd = np.ma.array([60])
        hdg = np.ma.array([0,0])
        self.assertRaises(ValueError, ground_track, 0.0, 0.0, gspd, hdg, 1.0, 'landing')
        # Direction not understood
        gspd = np.ma.array([60,60,60,60,60,60,60])
        hdg = np.ma.array([0,0.0,0.0,90,90,90,270])
        self.assertRaises(ValueError, ground_track, 0.0, 0.0, gspd, hdg, 1.0, 'touchdown')
    def test_ground_track_arrays_too_short(self):
        gspd = np.ma.array([60,60])
        hdg = np.ma.array([0,0])
        lat, lon = ground_track(0.0, 0.0, gspd, hdg, 1.0, 'landing')
        self.assertEqual(lat, None)
        self.assertEqual(lon, None)
    def test_ground_track_heading_continuous(self):
        # Heading continuous means headings can be large.
        gspd = np.ma.array([60,60,60,60,60,60,60])
        hdg = np.ma.array([-720,-360.0,720,90,-270,450,-90])
        lat, lon = ground_track(0.0, 0.0, gspd, hdg, 1.0, 'landing')
        expected_lat = [0.0,0.00027759,0.00055518,0.00069398,0.00069398,0.00069398,0.00069398]
        expected_lon = [0.0,0.0,0.0,0.00013880,0.00041639,0.00069398,0.00069398]
        np.testing.assert_array_almost_equal(expected_lat, lat)
        np.testing.assert_array_almost_equal(expected_lon, lon)
    def test_ground_track_masking(self):
        # Heading continuous means headings can be large.
        gspd = np.ma.array(data=[60,60,60,60,60,60,60],
                           mask=[0,0,1,0,0,0,0])
        hdg = np.ma.array(data=[0,0.0,0.0,90,90,90,270],
                          mask=[0,0,0,0,1,0,0])
        lat, lon = ground_track(0.0, 0.0, gspd, hdg, 1.0, 'landing')
        expected_lat = np.ma.array(data=[0.0,0.00027759,0.00055518,0.00069398,0.00069398,0.00069398,0.00069398],
                                   mask=[0,0,1,0,1,0,0])
        expected_lon = np.ma.array(data=[0.0,0.0,0.0,0.00013880,0.00041639,0.00069398,0.00069398],
                                   mask=[0,0,1,0,1,0,0])
        np.testing.assert_almost_equal(expected_lat.data, lat.data)
        np.testing.assert_almost_equal(expected_lon.data, lon.data)
        np.testing.assert_equal(expected_lat.mask, lat.mask)
        np.testing.assert_equal(expected_lon.mask, lon.mask)
    def test_ground_track_takeoff(self):
        gspd = np.ma.array([60,60,60,60,60,60,60])
        hdg = np.ma.array([0,0.0,0.0,90,90,90,270])
        lat, lon = ground_track(0.0, 0.0, gspd, hdg, 1.0, 'takeoff')
        expected_lat = [-0.00069398,-0.00041639,-0.00013880,0.0,0.0,0.0,0.0]
        expected_lon = [-0.00069398,-0.00069398,-0.00069398,-0.00055518,-0.00027759,0.0,0.0]
        np.testing.assert_array_almost_equal(expected_lat, lat)
        np.testing.assert_array_almost_equal(expected_lon, lon)


class TestHashArray(unittest.TestCase):
    def test_hash_array(self):
        '''
        
        '''
        self.assertEqual(hash_array(np.ma.arange(10)),
                         hash_array(np.ma.arange(10)))
        self.assertNotEqual(hash_array(np.ma.arange(10)),
                            hash_array(np.ma.arange(1,11)))
        # Tests that mask contents affect the generated hash.
        ma1 = np.ma.array(np.ma.arange(100,200), mask=[False] * 100)
        ma2 = np.ma.array(np.ma.arange(100,200),
                          mask=[False] * 50 + [True] + 49 * [False])
        self.assertNotEqual(hash_array(ma1), hash_array(ma2))
        self.assertEqual(hash_array(ma2), hash_array(ma2))
        self.assertEqual(hash_array(np.ma.arange(10, dtype=np.float_)),
            'c29605eb4e50fbb653a19f1a28c4f0955721419f989f1ffd8cb2ed6f4914bbea')


class TestHysteresis(unittest.TestCase):
    def test_hysteresis(self):
        data = np.ma.array([0,1,2,1,0,-1,5,6,7,0],dtype=float)
        data[4] = np.ma.masked
        result = hysteresis(data,2)
        np.testing.assert_array_equal(result.filled(999),
                                      [0.5,1,1,1,999,0,5,6,6,0.5])

    def test_hysteresis_change_of_threshold(self):
        data = np.ma.array([0,1,2,1,0,-1,5,6,7,0],dtype=float)
        result = hysteresis(data,1)
        np.testing.assert_array_equal(result.data,[0.25,1.,1.5,1.,0.,
                                                   -0.5,5.,6.,6.5,0.25])

    def test_hysteresis_phase_stability(self):
        data = np.ma.array([0,1,2,3,4,5,5,4,3,2,1,0],dtype=float)
        result = hysteresis(data,2)
        # Hysteresis range of 2 = +/- 1.0, so top 1 gets "choppeed off".
        # Slopes remain unaltered, and endpoints are amended by half the
        # hysteresis, being affected only on one pass of this two-pass
        # process.
        np.testing.assert_array_equal(result.data,[0.5,1,2,3,4,4,4,4,3,2,1,0.5])
        
    def test_hysteresis_with_initial_data_masked(self):
        data = np.ma.array([0,1,2,1,-100000,-1,5,6,7,0],dtype=float)
        data[0] = np.ma.masked
        data[4] = np.ma.masked
        result = hysteresis(data,2)
        np.testing.assert_array_equal(result.filled(999),
                                      [999,1,1,1,999,0,5,6,6,0.5])
        
    """
    Hysteresis may need to be speeded up, in which case this test can be
    reinstated.
    
    def test_time_taken(self):
        from timeit import Timer
        timer = Timer(self.using_large_data)
        time = min(timer.repeat(1, 1))
        print "Time taken %s secs" % time
        self.assertLess(time, 0.1, msg="Took too long")
        
    def using_large_data(self):
        data = np.ma.arange(100000)
        data[0] = np.ma.masked
        data[-1000:] = np.ma.masked
        res = hysteresis(data, 10)
        pass
    """

class TestIndexAtValue(unittest.TestCase):
    
    # Reminder: index_at_value (array, section, threshold):

    def test_index_at_value_basic(self):
        array = np.ma.arange(4)
        self.assertEquals (index_at_value(array, 1.5, slice(0, 3)), 1.5)
        
    def test_index_at_value_no_slice(self):
        array = np.ma.arange(4)
        self.assertEquals (index_at_value(array, 1.5), 1.5)
        self.assertEquals (index_at_value(array, 1.5, slice(None, None, None)), 1.5)
        
    def test_index_at_value_backwards(self):
        array = np.ma.arange(8)
        self.assertEquals (index_at_value(array, 3.2, slice(6, 2, -1)), 3.2)

    def test_index_at_value_backwards_with_negative_values_a(self):
        array = np.ma.arange(8)*(-1.0)
        self.assertEquals (index_at_value(array, -3.2, slice(6, 2, -1)), 3.2)
        
    def test_index_at_value_backwards_with_negative_values_b(self):
        array = np.ma.arange(8)-10
        self.assertEquals (index_at_value(array, -5.2, slice(6, 2, -1)), 4.8)

    def test_index_at_value_right_at_start(self):
        array = np.ma.arange(4)
        self.assertEquals (index_at_value(array, 1.0, slice(1, 3)), 1.0)
                           
    def test_index_at_value_right_at_end(self):
        array = np.ma.arange(4)
        self.assertEquals (index_at_value(array, 3.0, slice(1, 4)), 3.0)
        
    def test_index_at_value_backwards_floating_point_end(self):
        array = np.ma.arange(4)
        self.assertEquals (index_at_value(array, 1.0, slice(3.4, 0.5, -1)), 1.0)
        
    def test_index_at_value_forwards_floating_point_end(self):
        array = np.ma.arange(4)
        self.assertEquals (index_at_value(array, 3.0, slice(0.6, 3.5)), 3.0)
        
    def test_index_at_value_threshold_not_crossed(self):
        array = np.ma.arange(4)
        self.assertEquals (index_at_value(array, 7.5, slice(0, 3)), None)
        
    def test_index_at_value_masked(self):
        array = np.ma.arange(4)
        array[1] = np.ma.masked
        self.assertEquals (index_at_value(array, 1.5, slice(0, 3)), None)
    
    def test_index_at_value_slice_too_small(self):
        '''
        Returns None when there is only one value in the array since it cannot
        cross a threshold.
        '''
        array = np.ma.arange(50)
        self.assertEqual(index_at_value(array, 25, slice(25,26)), None)

    def test_index_at_value_slice_beyond_top_end_of_data(self):
        '''
        Returns None when there is only one value in the array since it cannot
        cross a threshold.
        '''
        array = np.ma.arange(50)
        self.assertEqual(index_at_value(array, 55, slice(40,60)), None)

    def test_index_at_value_slice_beyond_bottom_end_of_data(self):
        '''
        Returns None when there is only one value in the array since it cannot
        cross a threshold.
        '''
        array = np.ma.arange(50)
        self.assertEqual(index_at_value(array, 55, slice(-20,20)), None)

    def test_index_at_value_divide_by_zero_trap(self):
        '''
        Returns None when there is only one value in the array since it cannot
        cross a threshold.
        '''
        array = np.ma.arange(50)
        array[25:] -= 1
        array[23]=np.ma.masked
        array[26]=np.ma.masked
        self.assertEqual(index_at_value(array, 24, slice(20,30)), 24.5)


class TestIndexClosestValue(unittest.TestCase):
    def test_index_closest_value(self):
        array = np.ma.array([1,2,3,4,5,4,3])
        self.assertEqual(index_closest_value(array, 6, slice(0,6)), 4)

    def test_index_closest_value_at_start(self):
        array = np.ma.array([6,2,3,4,5,4,3])
        self.assertEqual(index_closest_value(array, 7, slice(0,6)), 0)

    def test_index_closest_value_at_end(self):
        array = np.ma.array([1,2,3,4,5,6,7])
        self.assertEqual(index_closest_value(array, 99, slice(0,6)), 6)

    def test_index_closest_value_negative(self):
        array = np.ma.array([3,2,1,4,5,6,7])
        self.assertEqual(index_closest_value(array, -9, slice(0,6)), 2)

    def test_index_closest_value_sliced(self):
        array = np.ma.array([1,2,3,4,5,4,3])
        self.assertEqual(index_closest_value(array, 6, slice(2,5)), 4)

    def test_index_closest_value_backwards(self):
        array = np.ma.array([3,2,1,4,5,6,7])
        self.assertEqual(index_closest_value(array, -9, slice(5,1,-1)), 2)

class TestInterpolateAndExtend(unittest.TestCase):
    def test_interpolate_and_extend_basic(self):
        array = np.ma.array(data=[0,0,2,0,0,3.5,0],
                            mask=[1,1,0,1,1,0,1],
                            dtype=float)
        expected = np.ma.array([2,2,2,2.5,3,3.5,3.5])
        result = interpolate_and_extend(array)
        np.testing.assert_array_equal(result, expected)
        
    def test_interpolate_and_extend_four_parts(self):
        array = np.ma.array(data=[2,0,2,0,2,0,2],
                            mask=[1,0,1,0,1,0,1])
        expected = np.ma.array([0]*7)
        result = interpolate_and_extend(array)
        np.testing.assert_array_equal(result, expected)
        
    def test_interpolate_and_extend_nothing_to_do_none_masked(self):
        array = np.ma.array(data=[0,0,2,0,0,3.5,0],
                            mask=[0,0,0,0,0,0,0],
                            dtype=float)
        result = interpolate_and_extend(array)
        np.testing.assert_array_equal(result, array)
        
    def test_interpolate_and_extend_nothing_to_do_all_masked(self):
        array = np.ma.array(data=[0,0,2,0,0,3.5,0],
                            mask=[1,1,1,1,1,1,1],
                            dtype=float)
        expected = np.ma.array(data=[0,0,0,0,0,0,0],
                            mask=False, dtype=float)
        result = interpolate_and_extend(array)
        np.testing.assert_array_equal(result, expected)

    def test_interpolate_and_extend_no_ends(self):
        array = np.ma.array(data=[5,0,0,20],
                            mask=[0,1,1,0],
                            dtype=float)
        expected = np.ma.array([5, 10, 15, 20])
        result = interpolate_and_extend(array)
        np.testing.assert_array_equal(result, expected)
        
        

class TestIndexOfDatetime(unittest.TestCase):
    def test_index_of_datetime(self):
        start_datetime = datetime.now()
        difference = timedelta(seconds=40)
        index_datetime = start_datetime + difference
        frequency = 4
        index = index_of_datetime(start_datetime, index_datetime, frequency)
        self.assertEqual(index, 160)


class TestInterleave(unittest.TestCase):
    def test_interleave(self):
        param1 = P('A1',np.ma.array(range(4),dtype=float),1,0.2)
        param2 = P('A2',np.ma.array(range(4),dtype=float)+10,1,0.7)
        result = interleave(param1, param2)
        np.testing.assert_array_equal(result.data,[0,10,1,11,2,12,3,13])
        np.testing.assert_array_equal(result.mask, False)

    def test_merge_alternage_sensors_mask(self):
        param1 = P('A1',np.ma.array(range(4),dtype=float),1,0.2)
        param2 = P('A2',np.ma.array(range(4),dtype=float)+10,1,0.7)
        param1.array[1] = np.ma.masked
        param2.array[2] = np.ma.masked
        result = interleave(param1, param2)
        np.testing.assert_array_equal(result.data[0:2], [0,10])
        np.testing.assert_array_equal(result.data[3:5], [11,2])
        np.testing.assert_array_equal(result.data[6:], [3,13])
        np.testing.assert_array_equal(result.mask, [False,False,True,
                                                    False,False,True,
                                                    False,False])


"""
class TestInterpolateParams(unittest.TestCase):
    def test_interpolate_params(self):
        param1 = P('A1',np.ma.arange(10),
                   frequency=1,offset=0.2)
        param2 = P('A2',np.ma.arange(0.2, 10, 0.5),
                   frequency=2,offset=0.7)
        param1.array[1] = np.ma.masked
        param2.array[2] = np.ma.masked
        array, freq, off = interpolate_params(param1, param2)
        np.testing.assert_array_equal(array.data[:5], 
            [0.0, 0.27222222222222225, 0.49444444444444441, 0.71666666666666656,
             0.93888888888888866])
        np.testing.assert_array_equal(array[-5:], 
            [8.9047619047619033, 9.1481481481481435, 9.3833333333333311,
             9.6055555555555525, np.nan])
        array.mask[-1] = True
        self.assertEqual(freq, 3)
        self.assertEqual(off, 3 * param1.offset)
"""

class TestIsIndexWithinSlice(unittest.TestCase):
    def test_is_index_within_slice(self):
        self.assertTrue(is_index_within_slice(1, slice(0,2)))
        self.assertTrue(is_index_within_slice(5, slice(5,7)))
        # Slice is not inclusive of last index.
        self.assertFalse(is_index_within_slice(7, slice(5,7)))
        self.assertTrue(is_index_within_slice(10, slice(8,None)))
        self.assertTrue(is_index_within_slice(10, slice(None, 12)))

class TestILSLocalizerAlign(unittest.TestCase):
    def test_ils_localizer_align(self):
        runway =  {'end': {'latitude': 60.280151, 
                              'longitude': 5.222579}, 
                      'localizer': {'latitude': 60.2788, 
                                    'longitude': 5.22}, 
                      'start': {'latitude': 60.30662494, 
                                'longitude': 5.21370074}}
        result = ils_localizer_align(runway)
        self.assertEqual(result['longitude'],5.2229505710057404)
        self.assertEqual(result['latitude'],60.27904301842346)
        

class TestIntegrate (unittest.TestCase):
    # Reminder: integrate(array, frequency, initial_value=0.0, scale=1.0, direction="forwards"):
    def test_integration_basic(self):
        result = integrate([10,0], 1.0)
        np.testing.assert_array_equal(result, [0.0,5.0])

    def test_integration_initial_value(self):
        result = integrate([0,0], 1.0, initial_value=3.0)
        np.testing.assert_array_equal(result, [3.0,3.0])

    def test_integration_frequency(self):
        result = integrate([0,10.0], 2.0)
        np.testing.assert_array_equal(result, [0.0,2.5])

    def test_integration_reverse(self):
        result = integrate([0,10,6], 1.0, initial_value=7, direction='reverse')
        np.testing.assert_array_equal(result, [20.0,15.0,7.0])
        
    def test_integration_backwards(self):
        result = integrate([0,10,6], 1.0, initial_value=7, direction='BaCKWardS')
        np.testing.assert_array_equal(result, [-6.0,-1.0,7.0])

    def test_integration_scale(self):
        result = integrate([1,1,1], 1.0, scale=10)
        np.testing.assert_array_equal(result, [0.0,10.0,20.0])

    def test_integration_sinewave(self):
        # Double integration of a sine wave reverses phase, so result is just error terms.
        testwave = np.sin(np.arange(0,20.0,0.01))
        step_1 = integrate(testwave, 1.0, scale=0.01, initial_value=-1.0)
        step_2 = integrate(step_1, 1.0, scale=0.01)
        self.assertLess(np.max(np.abs(step_2+testwave)), 0.001)


class TestIsSliceWithinSlice(unittest.TestCase):
    def test_is_slice_within_slice(self):
        self.assertTrue(is_slice_within_slice(slice(5,6), slice(4,7)))
        self.assertTrue(is_slice_within_slice(slice(4,6), slice(4,7)))
        self.assertTrue(is_slice_within_slice(slice(4,7), slice(4,7)))
        self.assertFalse(is_slice_within_slice(slice(4,8), slice(4,7)))
        self.assertFalse(is_slice_within_slice(slice(3,7), slice(4,7)))
        self.assertTrue(is_slice_within_slice(slice(None, None),
                                              slice(None, None)))
        self.assertFalse(is_slice_within_slice(slice(None, None),
                                               slice(None, 20)))
        self.assertFalse(is_slice_within_slice(slice(None, 15), slice(4, None)))
        self.assertTrue(is_slice_within_slice(slice(-1000, 15),
                                              slice(None, None)))
        self.assertTrue(is_slice_within_slice(slice(-1000, None),
                                              slice(None, None)))
        self.assertTrue(is_slice_within_slice(slice(None, 15),
                                              slice(None, None)))
        

class TestMaskInsideSlices(unittest.TestCase):
    def test_mask_inside_slices(self):
        slices = [slice(10, 20), slice(30, 40)]
        array = np.ma.arange(50)
        array.mask = np.array([True] * 5 + [False] * 45)
        expected_result = np.ma.arange(50)
        expected_result.mask = np.array([True] * 5 + [False] * 5 + [True] *  10 + [False] * 10 + [True] * 10)
        ma_test.assert_equal(mask_inside_slices(array, slices),
                             expected_result)


class TestMaxContinuousUnmasked(unittest.TestCase):
    def test_max_continuous_unmasked(self):
        data = np.ma.array(range(20),
                           mask=[1,0,1,1,1,0,0,0,0,1,
                                 0,0,0,0,0,0,0,1,1,1])
        _max = max_continuous_unmasked(data)
        # test duration
        self.assertEqual(_max.stop-_max.start, 7)
        self.assertEqual(_max.start, 10)
        self.assertEqual(_max.stop, 17)
        self.assertFalse(np.any(data[_max].mask)) # none should be masked
    
    def test_max_continuous_unmasked_no_mask(self):
        # no mask
        data = np.ma.array(range(20), mask=False)
        _max = max_continuous_unmasked(data)
        self.assertEqual(_max.stop-_max.start, 20)
        self.assertEqual(_max.start, 0)
        self.assertEqual(_max.stop, 20)
        
        # all masked
        data = np.ma.array(range(5), mask=[1,1,1,1,1])
        _max = max_continuous_unmasked(data)
        self.assertEqual(_max, None)
        
        # no data
        data = np.ma.array([])
        _max = max_continuous_unmasked(data, slice(110,120))
        self.assertEqual(_max, None)
        
    def test_max_continuous_unmasked_with_slice(self):
        data = np.ma.array(range(30),
                           mask=[0,1,0,0,0,1,1,1,1,0,
                                 1,1,1,1,1,1,1,0,0,0,
                                 1,1,1,1,1,0,0,1,1,1,])
        _max = max_continuous_unmasked(data, slice(20,30))
        # test duration
        self.assertEqual(_max.stop-_max.start, 2)
        self.assertEqual(_max.start, 25)
        self.assertEqual(_max.stop, 27)
                


class TestMaskOutsideSlices(unittest.TestCase):
    def test_mask_outside_slices(self):
        slices = [slice(10, 20), slice(30, 40)]
        array = np.ma.arange(50)
        array.mask = np.array([False] * 10 + [True] * 5 + [False] * 35)
        expected_result = np.ma.arange(50)
        expected_result.mask = np.array([True] * 15 + [False] * 5 + [True] * 10 + [False] * 10 + [True] * 10)
        ma_test.assert_equal(mask_outside_slices(array, slices),
                             expected_result)
        
        
class TestMaxValue(unittest.TestCase):
    def test_max_value(self):
        array = np.ma.array(range(50,100) + range(100,50,-1))
        i, v = max_value(array)
        self.assertEqual(i, 50)
        self.assertEqual(v, 100)
        
        subslice = slice(80, 90)
        res = max_value(array, subslice)
        self.assertEqual(res.index, 80)
        self.assertEqual(res.value, 70)
        
        neg_step = slice(100,65,-10)
        self.assertRaises(ValueError, max_value, array, neg_step)
        ##self.assertEqual(res, (69, 81)) # you can get this if you use slice.stop!
        
    def test_max_value_non_integer_slices_no_limits(self):
        array = np.ma.arange(5)+10
        i, v, = max_value(array)
        self.assertEqual(i, 4)
        self.assertEqual(v, 14)

    def test_max_value_integer_slices(self):
        array = np.ma.arange(10)+10
        i, v, = max_value(array, slice(2,4))
        self.assertEqual(i, 3)
        self.assertEqual(v, 13)

    def test_max_value_non_integer_upper_edge(self):
        array = np.ma.arange(5)+10
        i, v, = max_value(array, slice(2,3),None,3.7)
        self.assertEqual(i, 3.7)
        self.assertEqual(v, 13.7)

    def test_max_value_non_integer_lower_edge(self):
        array = 20-np.ma.arange(5)
        i, v, = max_value(array, slice(2,3),1.3,None)
        self.assertEqual(i, 1.3)
        self.assertEqual(v, 18.7)

    def test_max_value_slice_mismatch(self):
        array = np.ma.arange(5)+10
        i, v, = max_value(array, slice(100,101))
        self.assertEqual(i, None)
        self.assertEqual(v, None)
        
    def test_max_value_no_edge(self):
        array = np.ma.array(data=[2,3,4,8,9],mask=[0,0,0,1,1])
        i, v = max_value(array, slice(0,3),None,3.5)
        self.assertEqual(i, 2)
        self.assertEqual(v, 4) # Important that end case is ignored.
    
    def test_max_value_all_masked(self):
        array = np.ma.array(data=[0,1,2], mask=[1,1,1])
        i, v = max_value(array)
        self.assertEqual(i, None)
        self.assertEqual(v, None)
        
        
class TestMaxAbsValue(unittest.TestCase):
    def test_max_abs_value(self):
        array = np.ma.array(range(-20,30) + range(10,-41, -1) + range(10))
        self.assertEqual(max_abs_value(array), (100, -40))
        array = array*-1.0
        self.assertEqual(max_abs_value(array), (100, 40))


class TestMergeSources(unittest.TestCase):
    def test_merge_sources_basic(self):
        p1 = np.ma.array([0]*4)
        p2 = np.ma.array([1,2,3,4])
        result = merge_sources(p1, p2)
        expected = np.ma.array([0,1,0,2,0,3,0,4])
        np.testing.assert_array_equal(expected, result)


class TestMergeTwoParameters(unittest.TestCase):
    def test_merge_two_parameters_offset_ordered_forward(self):
        p1 = P(array=[0]*4, frequency=1, offset=0.0)
        p2 = P(array=[1,2,3,4], frequency=1, offset=0.2)
        arr, freq, off = merge_two_parameters(p1, p2)
        self.assertEqual(arr[1], 1.0) # Differs from blend function here.
        self.assertEqual(freq, 2)
        self.assertEqual(off, 0.0)

    def test_merge_two_parameters_offset_ordered_backward(self):
        p1 = P(array=[5,10,7,8], frequency=2, offset=0.5)
        p2 = P(array=[1,2,3,4], frequency=2, offset=0.1)
        arr, freq, off = merge_two_parameters(p1, p2)
        self.assertEqual(arr[3], 10.0)
        self.assertEqual(freq, 4)
        self.assertEqual(off, 0.1)

    def test_merge_two_parameters_assertion_error(self):
        p1 = P(array=[0]*4, frequency=1, offset=0.0)
        p2 = P(array=[1]*4, frequency=2, offset=0.2)
        self.assertRaises(AssertionError, merge_two_parameters, p1, p2)

    def test_merge_two_parameters_array_mismatch_error(self):
        p1 = P(array=[0]*4, frequency=1, offset=0.0)
        p2 = P(array=[1]*3, frequency=2, offset=0.2)
        self.assertRaises(AssertionError, merge_two_parameters, p1, p2)



class TestMinValue(unittest.TestCase):
    def test_min_value(self):
        array = np.ma.array(range(50,100) + range(100,50,-1))
        i, v = min_value(array)
        self.assertEqual(i, 0)
        self.assertEqual(v, 50)
        
        subslice = slice(80, 90)
        res = min_value(array, subslice)
        self.assertEqual(res.index, 89)
        self.assertEqual(res.value, 61)
        
        neg_step = slice(100,65,-10)
        self.assertRaises(ValueError, min_value, array, neg_step)

    def test_min_value_non_integer_slices_no_limits(self):
        array = 10-np.ma.arange(5)
        i, v, = min_value(array)
        self.assertEqual(i, 4)
        self.assertEqual(v, 6)

    def test_min_value_integer_slices(self):
        array = 10-np.ma.arange(10)
        i, v, = min_value(array, slice(2,4))
        self.assertEqual(i, 3)
        self.assertEqual(v, 7)

    def test_min_value_non_integer_upper_edge(self):
        array = 10-np.ma.arange(5)
        i, v, = min_value(array, slice(2,3),None,3.7)
        self.assertEqual(i, 3.7)
        self.assertEqual(v, 6.3)

    def test_min_value_non_integer_lower_edge(self):
        array = np.ma.arange(5)+5
        i, v, = min_value(array, slice(2,3),1.3,None)
        self.assertEqual(i, 1.3)
        self.assertEqual(v, 6.3)

    def test_min_value_slice_mismatch(self):
        array = 10-np.ma.arange(5)
        i, v, = min_value(array, slice(100,101))
        self.assertEqual(i, None)
        self.assertEqual(v, None)


class TestMinimumUnmasked(unittest.TestCase):
    def test_min_unmasked_basic(self):
        a1= np.ma.array(data=[1.1,2.1,3.1,4.1],
                        mask=[True,True,False,False])
        a2= np.ma.array(data=[4.2,3.2,2.2,1.2],
                        mask=[True,False,True,False])
        expected= np.ma.array(data=[99,3.2,3.1,1.2],
                              mask=[True,False,False,False],
                              dtype=float)
        result = minimum_unmasked(a1,a2)
        np.testing.assert_array_equal(expected, result)


class TestBlendTwoParameters(unittest.TestCase):
    def test_blend_two_parameters_p2_before_p1_equal_spacing(self):
        p1 = P(array=[0,0,0,1.0], frequency=1, offset=0.9)
        p2 = P(array=[1,2,3,4.0], frequency=1, offset=0.4)
        arr, freq, off = blend_two_parameters(p1, p2)
        self.assertEqual(arr[1], 0.75)
        self.assertEqual(freq, 2)
        self.assertAlmostEqual(off, 0.4)

    def test_blend_two_parameters_offset_p2_before_p1_unequal_spacing(self):
        p1 = P(array=[5,10,7,8.0], frequency=2, offset=0.1)
        p2 = P(array=[1,2,3,4.0], frequency=2, offset=0.0)
        arr, freq, off = blend_two_parameters(p1, p2)
        self.assertEqual(arr[2], 6)
        self.assertEqual(freq, 4)
        self.assertEqual(off, 0.05)
        
    def test_blend_two_parameters_offset_order_back_low_freq(self):
        p1 = P(array=[5,10,7,8.0], frequency=0.25, offset=0.1)
        p2 = P(array=[1,2,3,4.0], frequency=0.25, offset=0.0)
        arr, freq, off = blend_two_parameters(p1, p2)
        self.assertEqual(arr[2], 6)
        self.assertEqual(freq, 0.5)
        self.assertEqual(off, 0.05)

    def test_blend_two_parameters_assertion_error(self):
        p1 = P(array=[0]*4, frequency=1, offset=0.0)
        p2 = P(array=[1]*4, frequency=2, offset=0.2)
        self.assertRaises(AssertionError, blend_two_parameters, p1, p2)

    def test_blend_two_parameters_array_mismatch_error(self):
        p1 = P(array=[0]*4, frequency=1, offset=0.0)
        p2 = P(array=[1]*3, frequency=2, offset=0.2)
        self.assertRaises(AssertionError, blend_two_parameters, p1, p2)

    def test_blend_two_parameters_param_one_rubbish(self):
        p1 = P(array=[5,10,7,8], frequency=2, offset=0.1, name='First')
        p2 = P(array=[1,2,3,4], frequency=2, offset=0.0, name='Second')
        p1.array = np.ma.masked
        arr, freq, off = blend_two_parameters(p1, p2)
        self.assertEqual(arr[2], 3)
        self.assertEqual(freq, 2)
        self.assertEqual(off, 0.0)
        
    def test_blend_two_parameters_param_two_rubbish(self):
        p1 = P(array=[5,10,7,8], frequency=2, offset=0.1, name='First')
        p2 = P(array=[1,2,3,4], frequency=2, offset=0.0, name='Second')
        p2.array = np.ma.masked
        arr, freq, off = blend_two_parameters(p1, p2)
        self.assertEqual(arr[2], 7)
        self.assertEqual(freq, 2)
        self.assertEqual(off, 0.1)
        
    def test_blend_two_parameters_rejecting_no_change_data(self):
        p1 = P(array=[4.0]*4, frequency=1, offset=0.9)
        p2 = P(array=[1,2,3,4.0], frequency=1, offset=0.4)
        arr, freq, off = blend_two_parameters(p1, p2)
        self.assertEqual(arr[1], 2)
        self.assertEqual(freq, 1)
        self.assertAlmostEqual(off, 0.4)



class TestNormalise(unittest.TestCase):
    def test_normalise_copy(self):
        md = np.ma.array([range(10), range(20,30)])
        res = normalise(md, copy=True)
        self.assertNotEqual(id(res), id(md))
        self.assertEqual(md.max(), 29)
        
        res = normalise(md, copy=False)
        self.assertEqual(id(res), id(md))
        self.assertEqual(md.max(), 1.0)
        
    def test_normalise_two_dims(self):
        # normalise over all axis
        md = np.ma.array([range(10), range(20,30)], dtype=np.float)
        res1 = normalise(md)
        # normalised to max val 30 means first 10 will be below 0.33 and second 10 above 0.66
        ma_test.assert_array_less(res1[0,:], 0.33)
        ma_test.assert_array_less(res1[1,:], 1.1)
        
        # normalise with max value
        md = np.ma.array([range(10), range(20,30)], dtype=np.float)
        res1 = normalise(md, scale_max=40)
        # normalised to max val 40 means first 10 will be below 0.33 and second 10 above 0.66
        ma_test.assert_array_less(res1[0,:], 0.226)
        ma_test.assert_array_less(res1[1,:], 0.776)        
            
        # normalise per axis
        res2 = normalise(md, axis=1)
        # each axis should be between 0 and 1
        self.assertEqual(res2[0,:].max(), 1.0)
        self.assertEqual(res2[1,:].max(), 1.0)
        
        # normalise per on all values across 0 axis
        res3 = normalise(md, axis=0)
        # each axis should be between 0 and 1
        self.assertEqual(res3.shape, (2,10))
        ##self.assertEqual(res3[0,:].max(), 1.0)
        ##self.assertEqual(res3[1,:].max(), 1.0)
        
    def test_normalise_masked(self):
        arr = np.ma.arange(10)
        arr[0] = 1000
        arr[0] = np.ma.masked
        arr[9] = np.ma.masked
        # mask the max value
        # Q: This does not modify the array in place, yet res is not used?
        res = normalise(arr)
        index, value = max_value(arr)
        self.assertEqual(index, 8)
        self.assertEqual(value, 8)


class TestNpMaZerosLike(unittest.TestCase):
    def test_zeros_like_basic(self):
        result = np_ma_zeros_like(np.ma.array([1,2,3]))
        expected = np.ma.array([0,0,0])
        ma_test.assert_array_equal(expected, result)

    def test_zeros_like_from_mask(self):
        result = np_ma_zeros_like(np.ma.array([1,2,3]))
        expected = np.ma.array([0,0,0])
        ma_test.assert_array_equal(expected, result)

    def test_zeros_like_from_masked(self):
        result = np_ma_zeros_like(np.ma.array(data=[1,2,3],mask=[1,0,1]))
        expected = np.ma.array([0,0,0])
        ma_test.assert_array_equal(expected, result)
        
    def test_zeros_like_from_all_masked(self):
        # This was found to be a special case.
        result = np_ma_zeros_like(np.ma.array(data=[1,2,3],mask=[1,1,1]))
        expected = np.ma.array([0,0,0])
        ma_test.assert_array_equal(expected, result)



class TestNpMaOnesLike(unittest.TestCase):
    def test_zeros_like_basic(self):
        result = np_ma_ones_like(np.ma.array([1,2,3]))
        expected = np.ma.array([1,1,1])
        ma_test.assert_array_equal(expected, result)


class TestNpMaMaskedZerosLike(unittest.TestCase):
    def test_masked_zeros_like_basic(self):
        result = np_ma_masked_zeros_like(np.ma.array([1,2,3]))
        np.testing.assert_array_equal(result.data, [0, 0, 0])
        np.testing.assert_array_equal(result.mask, [1, 1, 1])

        
class TestPeakCurvature(unittest.TestCase):
    # Note: The results from the first two tests are in a range format as the
    # artificial data results in multiple maxima.

    def test_peak_curvature_basic(self):
        array = np.ma.array([0]*20+range(20))
        pc = peak_curvature(array)
        self.assertEqual(pc,18.5) 
        #  Very artificial case returns first location of many seconds of
        #  high curvature.

    def test_peak_curvature(self):
        array = np.ma.array([0]*40+range(40))
        pc = peak_curvature(array)
        self.assertGreaterEqual(pc,35)
        self.assertLessEqual(pc,45)
        
    def test_peak_curvature_convex(self):
        array = np.ma.array([0]*40+range(40))*(-1.0)
        pc = peak_curvature(array, curve_sense='Convex')
        self.assertGreaterEqual(pc,35)
        self.assertLessEqual(pc,45)

    def test_peak_curvature_flat_data(self):
        array = np.ma.array([34]*40)
        pc = peak_curvature(array)
        self.assertEqual(pc,None)
        
    def test_peak_curvature_short_flat_data(self):
        array = np.ma.array([34]*4)
        pc = peak_curvature(array)
        self.assertEqual(pc,None)
        
    def test_peak_curvature_bipolar(self):
        array = np.ma.array([0]*40+range(40))
        pc = peak_curvature(array, curve_sense='Bipolar')
        self.assertGreaterEqual(pc,35)
        self.assertLessEqual(pc,45)

    def test_peak_curvature_real_data(self):
        array = np.ma.array([37.9,37.9,37.9,37.9,37.9,38.2,38.2,38.2,38.2,38.8,
                             38.2,38.8,39.1,39.7,40.6,41.5,42.7,43.6,44.5,46,
                             47.5,49.6,52,53.2,54.7,57.4,60.7,61.9,64.3,66.1,
                             69.4,70.6,74.2,74.8])
        pc = peak_curvature(array)
        self.assertGreaterEqual(pc,15.0)
        self.assertLessEqual(pc,15.1)
        
    def test_peak_curvature_with_slice(self):
        array = np.ma.array([0]*20+[10]*20+[0]*20)
        pc = peak_curvature(array, slice(10, 50), curve_sense='Bipolar')
        self.assertEqual(pc, 24.5)

    def test_peak_curvature_slice_backwards(self):
        array = np.ma.array([0]*40+range(40))
        pc = peak_curvature(array, slice(75, 10, -1))
        self.assertEqual(pc, 41.5)

class TestPeakIndex(unittest.TestCase):
    def test_peak_index_no_data(self):
        self.assertRaises(ValueError, peak_index, [])
        
    def test_peak_index_one_sample(self):
        self.assertEqual(peak_index([4]),0)
        
    def test_peak_index_two_samples_rising(self):
        self.assertEqual(peak_index([2,4]),1)
        
    def test_peak_index_two_samples_falling(self):
        self.assertEqual(peak_index([4,2]),0)
        
    def test_peak_index_three_samples_falling(self):
        self.assertEqual(peak_index([6,4,2]),0)
        
    def test_peak_index_three_samples_rising(self):
        self.assertEqual(peak_index([1,2,3]),2)
        
    def test_peak_index_three_samples_with_peak(self):
        self.assertEqual(peak_index([1,2,1]),1)
        
    def test_peak_index_three_samples_trap_linear(self):
        self.assertEqual(peak_index([0,0.0000001,0]),1)
        
    def test_peak_index_real_peak(self):
        peak=np.sin(np.arange(10)/3.)
        self.assertEqual(peak_index(peak),4.7141807866121832)
        
class TestPhaseMasking(unittest.TestCase):
    def test_phase_inside_basic(self):
        # Reminder: create_phase_inside(reference, a, b)
        array = np.ma.arange(8)
        result = create_phase_inside(array, 1.0,0.0,2,5)
        answer = np.ma.array(data = [0,1,2,3,4,5,6,7],
                             mask = [1,1,0,0,0,0,1,1])
        ma_test.assert_masked_array_approx_equal(result, answer)
        
    def test_phase_inside_reversed(self):
        # Reminder: create_phase_inside(reference, a, b)
        array = np.ma.arange(8)
        result = create_phase_inside(array, 1.0,0.1,5,2) # 2,5 > 5,2
        answer = np.ma.array(data = [0,1,2,3,4,5,6,7],
                             mask = [1,1,0,0,0,1,1,1])
        ma_test.assert_masked_array_approx_equal(result, answer)
        
    def test_phase_inside_positive_offset(self):
        # Reminder: create_phase_inside(reference, a, b)
        array = np.ma.arange(8)
        result = create_phase_inside(array, 1.0,0.1,2,5)
        answer = np.ma.array(data = [0,1,2,3,4,5,6,7],
                             mask = [1,1,0,0,0,1,1,1])
        ma_test.assert_masked_array_approx_equal(result, answer)
        
    def test_phase_inside_negative_offset(self):
        # Reminder: create_phase_inside(reference, a, b)
        array = np.ma.arange(8)
        result = create_phase_inside(array, 1.0,-0.1,2,5)
        answer = np.ma.array(data = [0,1,2,3,4,5,6,7],
                             mask = [1,1,1,0,0,0,1,1])
        ma_test.assert_masked_array_approx_equal(result, answer)
        
    def test_phase_inside_low_rate(self):
        # Reminder: create_phase_inside(reference, a, b)
        array = np.ma.arange(8)*4
        result = create_phase_inside(array, 0.25,0.0,12,25)
        answer = np.ma.array(data = [0,4,8,12,16,20,24,28],
                             mask = [1,1,1,0,0,0,0,1])
        ma_test.assert_masked_array_approx_equal(result, answer)
        
    def test_phase_outside_low_rate(self):
        # Reminder: create_phase_inside(reference, a, b)
        array = np.ma.arange(8)*4
        result = create_phase_outside(array, 0.25,0.0,7,21)
        answer = np.ma.array(data = [0,4,8,12,16,20,24,28],
                             mask = [0,0,1,1,1,1,0,0])
        ma_test.assert_masked_array_approx_equal(result, answer)
        
    def test_phase_inside_errors(self):
        # Reminder: create_phase_inside(reference, a, b)
        array = np.ma.arange(8)
        self.assertRaises(ValueError, create_phase_inside, array, 1,0, -1, 5)
        self.assertRaises(ValueError, create_phase_inside, array, 1,0, 10, 5)
        self.assertRaises(ValueError, create_phase_inside, array, 1,0, 2, -1)
        self.assertRaises(ValueError, create_phase_inside, array, 1,0, 2, 11)
    
class TestRateOfChange(unittest.TestCase):
    # 13/4/12 Changed timebase to be full width as this is more logical.
    # Reminder: was: rate_of_change(to_diff, half_width, hz) - half width in seconds.
    # Reminder: is: rate_of_change(to_diff, width) - width in seconds and freq from parameter.
    
    def test_rate_of_change_basic(self):
        sloped = rate_of_change(P('Test', 
                                  np.ma.array([1, 0, -1, 2, 1, 3, 4, 6, 5, 7],
                                              dtype=float), 1), 4)
        answer = np.ma.array(data=[-1.0,-1.0,0.0,0.75,1.25,1.0,1.0,1.0,-1.0,2.0],
                             mask=False)
        ma_test.assert_mask_eqivalent(sloped, answer)
        
    def test_rate_of_change_increased_frequency(self):
        sloped = rate_of_change(P('Test', 
                                  np.ma.array([1, 0, -1, 2, 1, 3, 4, 6, 5, 7],
                                              dtype=float), 2), 4)
        answer = np.ma.array(data=[-2.0,-2.0,6.0,-2.0,1.0,1.75,2.0,4.0,-2.0,4.0],
                             mask=False)
        ma_test.assert_mask_eqivalent(sloped, answer)
        
    def test_rate_of_change_reduced_frequency(self):
        sloped = rate_of_change(P('Test', 
                                  np.ma.array([1, 0, -1, 2, 1, 3, 4, 6, 5, 7],
                                              dtype=float), 0.5), 4)
        answer = np.ma.array(data=[-0.5,-0.5,0.5,0.5,0.25,0.75,0.75,0.25,0.25,1.0],
                             mask=False)
        ma_test.assert_mask_eqivalent(sloped, answer)
        
    def test_rate_of_change_transfer_mask(self):
        sloped = rate_of_change(P('Test', 
                                  np.ma.array(data = [1, 0, -1, 2, 1, 3, 4, 6, 5, 7],dtype=float,
                            mask = [0, 1,  0, 0, 0, 1, 0, 0, 0, 1]), 1), 2)
        answer = np.ma.array(data = [0,-1.0,0,1.0,0,1.5,0,0.5,0,0],
             mask = [True,False,True,False,True,False,True,False,True,True])
        ma_test.assert_mask_eqivalent(sloped, answer)
        
    def test_rate_of_change_half_width_zero(self):
        self.assertRaises(ValueError, 
                          rate_of_change, 
                          P('Test',np.ma.array([0, 1, 0]), 1), 0)
        
    def test_rate_of_change_half_width_negative(self):
        self.assertRaises(ValueError, 
                          rate_of_change, 
                          P('Test',np.ma.array([0, 1, 0]), 1), -2)
        
    def test_rate_of_change_small_values(self):
        sloped = rate_of_change(P('Test',np.ma.arange(10)/100.0, 1), 4)
        answer = np.ma.array(data=[0.01]*10,mask=False)
        ma_test.assert_masked_array_approx_equal(sloped, answer)
        
        
class TestRepairMask(unittest.TestCase):
    def test_repair_mask_basic(self):
        array = np.ma.arange(10)
        array[3] = np.ma.masked
        self.assertTrue(np.ma.is_masked(array[3]))
        array[6:8] = np.ma.masked
        res = repair_mask(array)
        np.testing.assert_array_equal(res.data,range(10))
        # test mask is now unmasked
        self.assertFalse(np.ma.is_masked(res[3]))
        self.assertFalse(np.ma.is_masked(res[4]))
        self.assertFalse(np.ma.is_masked(res[5]))
        self.assertFalse(np.ma.is_masked(res[6]))
        self.assertFalse(np.ma.is_masked(res[7]))
        self.assertFalse(np.ma.is_masked(res[8]))
        
    def test_repair_mask_too_much_invalid(self):
        array = np.ma.arange(20)
        array[4:15] = np.ma.masked
        res = repair_mask(array)
        ma_test.assert_masked_array_approx_equal(res, array)
        
    def test_repair_mask_not_at_start(self):
        array = np.ma.arange(10)
        array[0] = np.ma.masked
        res = repair_mask(array)
        ma_test.assert_masked_array_approx_equal(res, array)
        
    def test_repair_mask_not_at_end(self):
        array = np.ma.arange(10)
        array[9] = np.ma.masked
        res = repair_mask(array)
        ma_test.assert_masked_array_approx_equal(res, array)

    def test_repair_short_sample(self):
        # Very short samples were at one time returned as None, but simply
        # applying the normal "rules" seems more consistent, so this is a
        # test to show that an old function no longer applies.
        array = np.ma.arange(2)
        array[1] = np.ma.masked
        res = repair_mask(array)
        ma_test.assert_masked_array_approx_equal(res, array)


class TestRoundToNearest(unittest.TestCase):
    def test_round_to_nearest(self):
        array = np.ma.array(range(50))
        res = round_to_nearest(array, 5)
        
        self.assertEqual(list(res[:15]), 
                         [0,0,0,5,5,5,5,5,10,10,10,10,10,15,15])
        self.assertEqual(list(res[-7:]),
                         [45]*5 + [50]*2)
        
    def test_round_to_nearest_with_mask(self):
        array = np.ma.array(range(20), mask=[True]*10 + [False]*10)
        res = round_to_nearest(array, 5)
        self.assertEqual(list(np.ma.filled(res, fill_value=-1)),
                         [-1]*10 + [10,10,10,15,15,15,15,15,20,20])


class TestRMSNoise(unittest.TestCase):
    def test_rms_noise_basic(self):
        array = np.ma.array([0,0,1,0,0])
        result = rms_noise(array)
        expected = sqrt(1.5/3.0)
        self.assertAlmostEqual(result, expected)
        
    def test_rms_noise_patent_example(self):
        array = np.ma.array([8,7,6,9,4,8,2,7,5])
        result = rms_noise(array)
        expected = sqrt(107.75/7.0)
        self.assertAlmostEqual(result, expected)
        
    def test_rms_noise_masked(self):
        array = np.ma.array([0,0,0,1,0,0,0])
        array[3]=np.ma.masked
        result = rms_noise(array)
        expected = 0.0
        self.assertAlmostEqual(result, expected)
        
    def test_rms_noise_no_valid_data(self):
        array = np.ma.array([0,0,1,0,0])
        array[2]=np.ma.masked
        result = rms_noise(array)
        expected = None
        self.assertAlmostEqual(result, expected)
        
        
"""
class TestSectionContainsKti(unittest.TestCase):
    def test_valid(self):
        section =  S(items=[Section('first_section', slice(4,6))])
        kti = KTI(items=[KeyTimeInstance(name='More Test', index=5)])
        self.assertTrue(section_contains_kti(section.get_first(), kti))
        
    def test_invalid_for_two_ktis(self):
        section =  S(items=[Section('first_section', slice(4,8))])
        kti = KTI(items=[KeyTimeInstance(name='More Test', index=5),
                         KeyTimeInstance(name='More Test', index=6)])
        self.assertFalse(section_contains_kti(section.get_first(), kti))
        
    def test_invalid_for_no_ktis(self):
        section =  S(items=[Section('first_section', slice(4,8))])
        kti = []
        self.assertFalse(section_contains_kti(section.get_first(), kti))
        
    def test_invalid_for_two_slices(self):
        section =  S(items=[Section('first_section', slice(4,8)),
                            Section('second_section', slice(14,18))])
        kti = KTI(items=[KeyTimeInstance(name='More Test', index=5)])
        self.assertFalse(section_contains_kti(section, kti))
"""             
        
class TestShiftSlice(unittest.TestCase):
    def test_shift_slice(self):
        a = slice(1,3,None)
        b = 10
        self.assertEqual(shift_slice(a,b),slice(11,13,None))

    def test_shift_slice_too_short(self):
        a = slice(3.3,3.4,None)
        b = 6
        self.assertEqual(shift_slice(a,b),None)

    def test_shift_slice_transfer_none(self):
        a = slice(30.3,None)
        b = 3
        self.assertEqual(shift_slice(a,b),slice(33.3,None))

    def test_shift_slice_transfer_none_reversed(self):
        a = slice(None,23.8)
        b = 4.2
        self.assertEqual(shift_slice(a,b),slice(None, 28.0))

    def test_shift_slice_no_shift(self):
        a = slice(2, 5,None)
        self.assertEqual(shift_slice(a,0),a)
        self.assertEqual(shift_slice(a,None),a)


class TestShiftSlices(unittest.TestCase):
    def test_shift_slices(self):
        a = [slice(1,3,None)]
        b = 10
        self.assertEqual(shift_slices(a,b),[slice(11,13,None)])

    def test_shift_slices_incl_none(self):
        a = [slice(1,3,None),None,slice(2,4,2)]
        b = 10
        self.assertEqual(shift_slices(a,b),[slice(11,13,None),slice(12,14,2)])
        
    def test_shift_slices_real_data(self):
        a = [slice(0, 1, None), slice(599, 933, None), 
             slice(1988, 1992, None), slice(2018, 2073, None)]
        b = 548.65
        self.assertEqual(len(shift_slices(a,b)),3)

    def test_shift_slices_no_shift(self):
        a = [slice(4, 7, None), slice(17, 12, -1)]
        self.assertEqual(shift_slices(a,0), a)
        self.assertEqual(shift_slices(a,None), a)

class TestSlicesAbove(unittest.TestCase):
    def test_slices_above(self):
        array = np.ma.concatenate([np.ma.arange(10), np.ma.arange(10)])
        array.mask = [False] * 18 + [True] * 2
        repaired_array, slices = slices_above(array, 5)
        self.assertEqual(slices, [slice(5, 10, None), slice(15, 18, None)])


class TestSlicesBelow(unittest.TestCase):
    def test_slices_below(self):
        array = np.ma.concatenate([np.ma.arange(10), np.ma.arange(10)])
        array.mask = [True] * 2 + [False] * 18
        repaired_array, slices = slices_below(array, 5)
        self.assertEqual(slices, [slice(2, 6, None), slice(10, 16, None)])


class TestSlicesBetween(unittest.TestCase):
    def test_slices_between(self):
        array = np.ma.arange(20)
        array.mask = [True] * 10 + [False] * 10
        repaired_array, slices = slices_between(array, 5, 15)
        self.assertEqual(slices, [slice(10, 15)])

class TestSliceSamples(unittest.TestCase):
    def test_slice_samples(self):
        test_slice=slice(45,47,1)
        self.assertEqual(slice_samples(test_slice), 2)

    def test_slice_samples_backwards(self):
        test_slice=slice(48,45,-1)
        self.assertEqual(slice_samples(test_slice), 3)

    def test_slice_samples_stepping(self):
        test_slice=slice(10,20,4)
        self.assertEqual(slice_samples(test_slice), 3)

    def test_slice_samples_step_none(self):
        test_slice=slice(10,20)
        self.assertEqual(slice_samples(test_slice), 10)

    def test_slice_samples_start_none(self):
        test_slice=slice(None,20)
        self.assertEqual(slice_samples(test_slice), 0)

    def test_slice_samples_stop_none(self):
        test_slice=slice(5,None,20)
        self.assertEqual(slice_samples(test_slice), 0)

class TestSlicesFromTo(unittest.TestCase):
    def test_slices_from_to(self):
        array = np.ma.arange(20)
        array.mask = [True] * 10 + [False] * 10
        # Ascending.
        repaired_array, slices = slices_from_to(array, 5, 15)
        self.assertEqual(slices, [slice(10, 15)])
        # Descending.
        repaired_array, slices = slices_from_to(array, 18, 3)
        self.assertEqual(slices, [])
        array = np.ma.arange(20, 0, -1)
        array.mask = [True] * 10 + [False] * 10
        repaired_array, slices = slices_from_to(array, 18, 3)
        self.assertEqual(slices, [slice(10, 17)])
        
    def test_slices_from_to_landing(self):
        '''
        Common usage it to end in 0 for ...to landing. This test covers this
        specific case.
        '''
        array = np.ma.array([25,20,15,10,5,0,0,0,0])
        _, slices = slices_from_to(array, 17, 0)
        self.assertEqual(slices, [slice(2,5,None)])
        
class TestSlicesOverlap(unittest.TestCase):
    def test_slices_overlap(self):
        # overlap
        first = slice(10,20)
        second = slice(15,25)
        self.assertTrue(slices_overlap(first, second))
        self.assertTrue(slices_overlap(second, first))
        
        # None in slices
        start_none = slice(None, 12)
        self.assertTrue(slices_overlap(first, start_none))
        self.assertFalse(slices_overlap(second, start_none))
        self.assertTrue(slices_overlap(start_none, first))
        self.assertFalse(slices_overlap(start_none, second))
        
        end_none = slice(22,None)
        self.assertFalse(slices_overlap(first, end_none))
        self.assertTrue(slices_overlap(second, end_none))
        self.assertFalse(slices_overlap(end_none, first))
        self.assertTrue(slices_overlap(end_none, second))
        
        both_none = slice(None, None)
        self.assertTrue(slices_overlap(first, both_none))
        self.assertTrue(slices_overlap(second, both_none))
        self.assertTrue(slices_overlap(both_none, first))
        self.assertTrue(slices_overlap(both_none, second))
        
        
        # no overlap
        no_overlap = slice(25,40)
        self.assertFalse(slices_overlap(second, no_overlap))
        self.assertFalse(slices_overlap(no_overlap, first))
        
        # step negative
        self.assertRaises(ValueError, slices_overlap, first, slice(1,2,-1))
        
class TestSlicesOverlay(unittest.TestCase):
    def test_slices_and(self):
        # overlay
        first = [slice(10,20)]
        second = [slice(15,25)]
        self.assertEqual(slices_and(first, second), [slice(15,20)])
        
        # no overlap
        no_overlap = slice(25,40)
        self.assertEqual(slices_and(second, [no_overlap]), [])
        
        # step negative
        self.assertRaises(ValueError, slices_and, first, [slice(1,2,-1)])
        
        # complex with all four permutations
        first = [slice(5,15),slice(20,25),slice(30,40)]
        second = [slice(10,35),slice(45,50)]
        result = [slice(10,15), slice(20,25), slice(30,35)]
        self.assertEqual(slices_and(first,second),result)


class TestSlicesRemoveSmallGaps(unittest.TestCase):
    def test_slice_removal(self):
        slicelist=[slice(1,3), slice(5,7), slice(20,22)]
        newlist=slices_remove_small_gaps(slicelist)
        expected=[slice(1,7), slice(20,22)]
        self.assertEqual(expected, newlist)

    def test_slice_removal_big_time(self):
        slicelist=[slice(1,3), slice(5,7), slice(20,22)]
        newlist=slices_remove_small_gaps(slicelist,time_limit=15)
        expected=[slice(1,22)]
        self.assertEqual(expected, newlist)

    def test_slice_removal_big_freq(self):
        slicelist=[slice(1,3), slice(5,7), slice(20,22)]
        newlist=slices_remove_small_gaps(slicelist,hz=2)
        expected=[slice(1,22)]
        self.assertEqual(expected, newlist)


class TestSlicesNot(unittest.TestCase):
    def test_slices_not_internal(self):
        slice_list = [slice(10,13),slice(16,25)]
        self.assertEqual(slices_not(slice_list), [slice(13,16)])
        
    def test_slices_not_extended(self):
        slice_list = [slice(10,13)]
        self.assertEqual(slices_not(slice_list, begin_at=2, end_at=18), 
                         [slice(2,10),slice(13,18)])
        
    def test_slices_not_to_none(self):
        slice_list = [slice(10,None),slice(2,3)]
        self.assertEqual(slices_not(slice_list),[slice(3,10)])
        
    def test_slices_not_to_none_empty(self):
        slice_list = [slice(10,None)]
        self.assertEqual(slices_not(slice_list),[])
        
    def test_slices_not_from_none_empty(self):
        slice_list = [slice(None,13)]
        self.assertEqual(slices_not(slice_list),[])
        
    def test_slices_not_from_none(self):
        slice_list = [slice(None,13),slice(15,20)]
        self.assertEqual(slices_not(slice_list),[slice(13,15)])
        
    def test_slices_not_null(self):
        self.assertEqual(slices_not(None), [slice(None,None,None)])
        self.assertEqual(slices_not([]), [slice(None,None,None)])
        self.assertEqual(slices_not([slice(4,6)]),[])
        
    def test_slices_misordered(self):
        slice_list = [slice(25,16,-1),slice(10,13)]
        self.assertEqual(slices_not(slice_list), [slice(13,17)])
        slice_list = [slice(1,5,2)]
        # Single point slices get discarded by shift slices function.
        self.assertEqual(slices_not(slice_list), [])

class TestSlicesOr(unittest.TestCase):
    def test_slices_or_with_overlap(self):
        slice_list_a = [slice(10,13)]
        slice_list_b = [slice(16,25)]
        slice_list_c = [slice(20,31)]
        self.assertEqual(slices_or(slice_list_a,
                                   slice_list_b,
                                   slice_list_c),
                         [slice(10,13), slice(16,31)])

    def test_slices_or_lists(self):
        slice_list_a = [slice(10,13), slice(16,25)]
        slice_list_b = [slice(20,31)]
        self.assertEqual(slices_or(slice_list_a,
                                   slice_list_b),
                         [slice(10,13), slice(16,31)])

    def test_slices_or_offset(self):
        slice_list_a = [slice(10,13)]
        self.assertEqual(slices_or(slice_list_a, begin_at = 11),
                         [slice(11, 13)])

    def test_slices_or_truncated(self):
        slice_list_a = [slice(10,13)]
        slice_list_b = [slice(16,25)]
        slice_list_c = [slice(20,31)]
        self.assertEqual(slices_or(slice_list_a,
                                   slice_list_b,
                                   slice_list_c,
                                   end_at = 18),
                         [slice(10,13), slice(16,18)])
        
    def test_slices_or_empty_first_list(self):
        slice_list_a = []
        slice_list_b = [slice(1,3)]
        self.assertEqual(slices_or(slice_list_a, slice_list_b),
                         [slice(1, 3)])
 
    def test_slices_or_one_list(self):
        self.assertEqual(slices_or([slice(1,2)]), [slice(1,2)])


class TestStepValues(unittest.TestCase):
    def test_step_values(self):
        # borrowed from TestSlat
        array = np.ma.array(range(25) + range(-5,0))
        array[1] = np.ma.masked
        array = step_values(array, ( 0, 16, 20, 23))
        self.assertEqual(len(array), 30)
        self.assertEqual(
            list(np.ma.filled(array, fill_value=-999)), 
            [0, -999, 0, 0, 0, 0, 0, 0, 0, 
             16, 16, 16, 16, 16, 16, 16, 16, 16, 16,
             20, 20, 20, 
             23, 23, 23, 
             0, 0, 0, 0, 0])

    def test_step_inital_level(self):
        array = np.ma.arange(9,14,0.6)
        stepped = step_values(array, ( 10, 11, 15))
        self.assertEqual(list(stepped),
                         [10, 10, 10, 11, 11, 11, 11, 15, 15])

        
class TestStraightenHeadings(unittest.TestCase):
    def test_straight_headings(self):
        data = np.ma.array([35.5,29.5,11.3,0.0,348.4,336.8,358.9,2.5,8.1,14.4])
        expected = np.ma.array([35.5,29.5,11.3,0.0,-11.6,-23.2,-1.1,2.5,8.1,14.4])
        np.testing.assert_array_almost_equal(straighten_headings(data),expected)

    def test_straight_headings_starting_masked(self):
        data=np.ma.array(data=[0]*10+[6]*8+[1]*4+[10,5,0,355,350]+[0]*4,
                         mask=[True]*10+[False]*8+[True]*4+[False]*5+[True]*4)
        expected=np.ma.array(data=[0]*10+[6]*8+[0]*4+[10,5,0,-5,-10]+[0]*4,
                         mask=[True]*10+[False]*8+[True]*4+[False]*5+[True]*4)
        ma_test.assert_masked_array_approx_equal(straighten_headings(data), expected)
            

class TestSmoothTrack(unittest.TestCase):
    def test_smooth_track_latitude(self):
        lat = np.ma.array([0,0,0,1,1,1], dtype=float)
        lon = np.ma.zeros(6, dtype=float)
        lat_s, lon_s, cost = smooth_track(lat, lon)
        self.assertLess (cost,26)
        
    def test_smooth_track_longitude(self):
        lon = np.ma.array([0,0,0,1,1,1], dtype=float)
        lat = np.ma.zeros(6, dtype=float)
        lat_s, lon_s, cost = smooth_track(lat, lon)
        self.assertLess (cost,26)
        
    def test_smooth_track_speed(self):
        from time import clock
        lon = np.ma.arange(10000, dtype=float)
        lon = lon%27
        lat = np.ma.zeros(10000, dtype=float)
        start = clock()
        lat_s, lon_s, cost = smooth_track(lat, lon)
        end = clock()      
        print end-start      
        self.assertLess (end-start,1.0)
            
        
class TestSubslice(unittest.TestCase):
    def test_subslice(self):
        # test basic
        orig = slice(2,10)
        new = slice(2, 4)
        res = subslice(orig, new)
        self.assertEqual(res, slice(4, 6))
        fifty = range(50)
        self.assertEqual(fifty[orig][new], fifty[res])
        
        # test basic starting from zero
        orig = slice(2,10)
        new = slice(0, 4)
        res = subslice(orig, new)
        self.assertEqual(res, slice(2, 6))
        fifty = range(50)
        self.assertEqual(fifty[orig][new], fifty[res])
        
        orig = slice(10,20,2)
        new = slice(2, 4, 1)
        res = subslice(orig, new)
        thirty = range(30)
        self.assertEqual(thirty[orig][new], thirty[res])
        self.assertEqual(res, slice(14, 18, 2))
        
        # test step
        orig = slice(100,200,10)
        new = slice(1, 5, 2)
        sub = subslice(orig, new)
        two_hundred = range(0,200)
        self.assertEqual(two_hundred[orig][new], two_hundred[sub])
        self.assertEqual(sub, slice(110, 150, 20))
        
        # test negative step
        orig = slice(200,100,-10)
        new = slice(1, 5, 2)
        sub = subslice(orig, new)
        two_hundred = range(201)
        self.assertEqual(two_hundred[orig][new], two_hundred[sub])
        self.assertEqual(sub, slice(190, 150, -20))
        
        orig = slice(100,200,10)
        new = slice(5, 1, -2)
        sub = subslice(orig, new)
        two_hundred = range(201)
        self.assertEqual(two_hundred[orig][new], two_hundred[sub])
        self.assertEqual(sub, slice(150, 110, -20))
        self.assertEqual(two_hundred[sub], [150, 130]) #fix
        
        # test invalid back step
        orig = slice(0,200,10)
        new = slice(1, 5, -2)
        sub = subslice(orig, new)
        two_hundred = range(201)
        self.assertEqual(two_hundred[orig][new], two_hundred[sub])
        self.assertEqual(two_hundred[sub], []) # invalid returns no data
        self.assertEqual(sub, slice(10, 50, -20))
        
        # test no start
        orig = slice(None,100,10)
        new = slice(5, 1, -2)
        sub = subslice(orig, new)
        two_hundred = range(200)
        self.assertEqual(two_hundred[orig][new], two_hundred[sub])
        self.assertEqual(two_hundred[sub], [50,30])
        self.assertEqual(sub, slice(50, 10, -20))

        orig = slice(0,10,2)
        new = slice(None, 4)
        sub = subslice(orig, new)
        two_hundred = range(5)
        self.assertEqual(two_hundred[orig][new], two_hundred[sub])
        self.assertEqual(two_hundred[sub], [0,2,4]) # also tests outside of range
        self.assertEqual(sub, slice(0, 8, 2))
        
        # test None start and invalid back step
        orig = slice(None,200,10)
        new = slice(1, 5, -2)
        sub = subslice(orig, new)
        two_hundred = range(201)
        self.assertEqual(two_hundred[orig][new], two_hundred[sub])
        self.assertEqual(two_hundred[sub], [])
        self.assertEqual(sub, slice(10, 50, -20))

        # test None at end of second slice
        orig = slice(0,10,2)
        new = slice(1, None)
        sub = subslice(orig, new)
        two_hundred = range(5)
        self.assertEqual(two_hundred[orig][new], two_hundred[sub])
        self.assertEqual(two_hundred[sub], [2,4])
        self.assertEqual(sub, slice(2, 10, 2))
        
        # Actual case from test 6_737_1_RD0001851371
        orig = slice(419, 423, None)
        new = slice(0, None, 1)
        sub = subslice(orig, new)
        self.assertEqual(sub,slice(419,423,None))

        orig = slice(419, 423, None)
        new = slice(0, None, None)
        sub = subslice(orig, new)
        self.assertEqual(sub,slice(419,423,None))

        #TODO: test negative start, stop and step
"""
------------------------------------------------------------
Time functions replaced by index operations for consistency.
------------------------------------------------------------

class TestTimeAtValue(unittest.TestCase):
    
    # Reminder: time_at_value (array, hz, offset, scan_start, scan_end, threshold):

    def test_time_at_value_basic(self):
        array = np.ma.arange(4)
        self.assertEquals (time_at_value(array, 1, 0.0, 0, 3, 1.5), 1.5)
        
    def test_time_at_value_backwards(self):
        array = np.ma.arange(8)
        self.assertEquals (time_at_value(array, 1, 0.0, 6, 2, 2.5), 2.5)

    def test_time_at_value_right_at_start(self):
        array = np.ma.arange(4)
        self.assertEquals (time_at_value(array, 1, 0.0, 1, 3, 1.0), 1.0)
                           
    def test_time_at_value_right_at_end(self):
        array = np.ma.arange(4)
        self.assertEquals (time_at_value(array, 1, 0.0, 1, 3, 3.0), 3.0)
        
    def test_time_at_value_threshold_not_crossed(self):
        array = np.ma.arange(4)
        self.assertEquals (time_at_value(array, 1, 0.0, 0, 3, 7.5), None)
        
    def test_time_at_value_masked(self):
        array = np.ma.arange(4)
        array[1] = np.ma.masked
        self.assertEquals (time_at_value(array, 1, 0.0, 0, 3, 1.5), None)
      
        
class TestTimeAtValueWrapped(unittest.TestCase):
    # Reminder: time_at_value_wrapped(parameter, block, value):
  
    def test_time_at_value_wrapped_basic(self):
        test_param = P('TAVW_param',np.ma.array(range(4),dtype=float),1,0.0)
        test_section = Section('TAVW_section',slice(0,4))
        self.assertEquals(time_at_value_wrapped(test_param,test_section,2.5),2.5)

    def test_time_at_value_wrapped_backwards(self):
        test_param = P('TAVW_param',np.ma.array([0,4,0,4]),1,0.0)
        test_section = Section('TAVW_section',slice(0,4))
        self.assertEquals(time_at_value_wrapped(test_param,test_section,2,'Backwards'),2.5)
------------------------------------------------------------
Time functions replaced by index operations for consistency.
------------------------------------------------------------
"""
        
        
class TestTrackLinking(unittest.TestCase):
    def test_track_linking_basic(self):
        pos = np.ma.array(data=[0]*16,mask=False)
        local = np.ma.arange(16, dtype=float)
        local[0:3]=np.ma.masked
        local[6:10]=np.ma.masked
        local[13:]=np.ma.masked
        local[8:] -= 2.5
        # plot_parameter(local)
        result = track_linking(pos,local)
        expected = np.ma.array(data = [3.0,3.0,3.0,3.0,4.0,5.0,5.5,6.0,
                                       6.5,7.0,7.5,8.5,9.5,9.5,9.5,9.5],
                               mask = False)
        np.testing.assert_array_equal(expected,result)
        # plot_parameter(expected)
        
class TestValueAtTime(unittest.TestCase):

    # Reminder: value_at_time (array, hz, offset, time_index)
    
    def test_value_at_time_basic(self):
        array = np.ma.arange(4)
        self.assertEquals (value_at_time(array, 1, 0.0, 2.5), 2.5)
        
    def test_value_at_time_right_at_start_of_data(self):
        array = np.ma.arange(4) + 22.3
        self.assertEquals (value_at_time(array, 1, 0.0, 0.0), 22.3)
        
    def test_value_at_time_right_at_end_of_data(self):
        array = np.ma.arange(4) + 22.3
        self.assertEquals (value_at_time(array, 1.0, 0.0, 3.0), 25.3)
        
    def test_value_at_time_assertion_just_below_range(self):
        array = np.ma.arange(4)+7.0
        # Note: Frequency and offset selected to go more than one sample period below bottom of range.
        self.assertEquals (value_at_time(array, 1, 0.1, 0.0), 7.0)
        
    def test_value_at_time_with_lower_value_masked(self):
        array = np.ma.arange(4) + 7.4
        array[1] = np.ma.masked
        self.assertEquals (value_at_time(array, 2.0, 0.2, 1.0), 9.4)
        
    def test_value_at_time_with_higher_value_masked(self):
        array = np.ma.arange(4) + 7.4
        array[2] = np.ma.masked
        self.assertEquals (value_at_time(array, 2.0, 0.2, 1.0), 8.4)
        
    def test_value_at_time_with_neither_value_masked(self):
        array = np.ma.arange(4) + 7.4
        array[3] = np.ma.masked
        self.assertEquals (value_at_time(array, 2.0, 0.2, 1.0), 9.0)
        
    def test_value_at_time_with_both_values_masked(self):
        array = np.ma.arange(4) + 7.4
        array[1] = np.ma.masked
        array[2] = np.ma.masked
        self.assertEquals (value_at_time(array, 2.0, 0.2, 1.0), None)


class TestValueAtDatetime(unittest.TestCase):
    @mock.patch('analysis_engine.library.value_at_time')
    def test_value_at_datetime(self, value_at_time):
        array = mock.Mock()
        hz = mock.Mock()
        offset = mock.Mock()
        start_datetime = datetime.now()
        seconds = 20
        value_datetime = start_datetime + timedelta(seconds=seconds)
        value = value_at_datetime(start_datetime, array, hz, offset,
                                  value_datetime)
        value_at_time.assert_called_once_with(array, hz, offset, seconds)
        self.assertEqual(value, value_at_time.return_value)
        
        
class TestValueAtIndex(unittest.TestCase):

    # Reminder: value_at_time (array, index) This function is thoroughly
    # tested by the higher level value_at_time function, so this single test
    # just establishes confidence in the ability to access the lower level
    # function directly.
    
    def test_value_at_index_basic(self):
        array = np.ma.arange(4)
        self.assertEquals (value_at_index(array, 1.5), 1.5)

    def test_value_at_index_just_above_range(self):
        array = np.ma.arange(4)
        self.assertEquals (value_at_index(array, 3.7), 3.0)
        
    def test_value_at_index_just_below_range(self):
        array = np.ma.arange(4)
        self.assertEquals (value_at_index(array, -0.5), 0.0)
        
    def test_value_at_index_masked(self):
        array = np.ma.arange(4)
        array[2]=np.ma.masked
        expected=np.ma.array(1)
        expected 
        self.assertEquals (value_at_index(array, 2), None)


class TestVstackParams(unittest.TestCase):
    def test_vstack_params(self):
        a = P('a', array=np.ma.array(range(0, 10)))
        b = np.ma.array(range(10,20))
        a.array[0] = np.ma.masked
        b[0] = np.ma.masked
        b[-1] = np.ma.masked
        c = None
        ma_test.assert_array_equal(
            np.ma.filled(vstack_params(a), 99), 
            np.array([[99, 1, 2, 3, 4, 5, 6, 7, 8, 9]])
        )
        # test mixed types (Parameter, Masked Array, None)
        ma_test.assert_array_equal(
            np.ma.filled(vstack_params(None, a, b, c), 99),
            np.array([[99,  1,  2,  3,  4,  5,  6,  7,  8,  9],
                      [99, 11, 12, 13, 14, 15, 16, 17, 18, 99]])
        )
        self.assertRaises(ValueError, vstack_params, None, None, None)


#-----------------------------------------------------------------------------
#Tests for Atmospheric and air speed calculations derived from AeroCalc test
#suite. Changes relate to simplification of units and translation to Numpy.
#-----------------------------------------------------------------------------
class TestAlt2Press(unittest.TestCase):
    def test_01(self):

        # Truth values from NASA RP 1046

        Value = alt2press(np.ma.array([5000]))
        Truth = 843.0725884 # mBar
        self.assertAlmostEqual(Value, Truth)

    def test_02(self):

        # Truth values from aerospaceweb

        Value = alt2press(25000)
        Truth = 376.0087326
        self.assertAlmostEqual(Value, Truth, delta = 1e-5)

    def test_03(self):

        # Truth values from aerospaceweb

        Value = alt2press(45000)
        Truth = 147.4755452
        self.assertAlmostEqual(Value, Truth, delta = 1e-5)

    def test_04(self):

        # Truth values from NASA RP 1046

        Value = alt2press(25000*METRES_TO_FEET)
        Truth = 25.492
        # Wide tolerance as we're not going to be using this for 
        # commercial air transport !
        self.assertAlmostEqual(Value, Truth, delta = 1e-0)


class TestAlt2Press_Ratio(unittest.TestCase):

    def test_01(self):
        Value = alt2press_ratio(0)
        self.assertEqual(Value, 1.0)

    def test_02(self):
        
        # Truth values from NASA RP 1046

        Value = alt2press_ratio(-1000)
        Truth = 2193.82 / 2116.22
        self.assertAlmostEqual(Value, Truth, delta = 1e-5)

    def test_03(self):

        # Truth values from NASA RP 1046

        Value = alt2press_ratio(20000*METRES_TO_FEET)
        Truth = 5474.87 / 101325
        self.assertAlmostEqual(Value, Truth, delta = 1e-5)

    def test_04(self):

        # Typical value at 25,000 ft
        # From Aerospace.web
        # ratio = (1 - h/145442)^(5.255876)

        Value = alt2press_ratio(25000)
        Truth = np.power(1.0-25000./145442.,5.255876)
        self.assertAlmostEqual(Value, Truth)

class TestCas2Dp(unittest.TestCase):
    
    # Many AeroCalc tests using different units removed as we are
    # standardising the units for use inside the algorithms.
    # Test 08a added to include alternative Truth value
    # Test 17 added to confirm operation in typical takeoff/landing speeds

    def test_08(self):

        # 244 kt to pa
        # truth value from NASA RP 1046

        Value = cas2dp(244)
        Truth = 99.837
        self.assertAlmostEqual(Value, Truth, delta = 1e-2)

    def test_08a(self):

        # 244 kt to pa
        # truth value from aerospaceweb

        Value = cas2dp(244)
        Truth = 99.8355
        self.assertAlmostEqual(Value, Truth, delta = 1e-3)

    def test_16(self):

        # 1000 kt to pa
        # truth value from NASA RP 1046

        self.assertRaises(ValueError, cas2dp, 1000)

    def test_17(self):

        # 120 kt
        # truth value from aerospaceweb

        Value = cas2dp(120)
        Truth = 23.5351
        self.assertAlmostEqual(Value, Truth, delta = 1e-2)


class TestDp2Cas(unittest.TestCase):

    def test_01(self):

        # Tests low speed and masking supersonic cases in one go.

        # 244 kt in pa
        # truth value from NASA RP 1046

        # 1000 kt in pa
        # truth value from NASA RP 1046

        Value = dp2cas(np.ma.array([99.837, 2490.53]))
        Truth = np.ma.array(data=[244.0, 1000.0], mask=[False,True])
        ma_test.assert_almost_equal(Value,Truth,decimal=2)

class TestDp2Tas(unittest.TestCase):

    def test_01(self):
        # "Null" case to start
        Value = dp2tas(0.0, 0.0, 15.0)
        Truth = 0.0
        self.assertEqual(Value, Truth)

    def test_02(self):
        # Trivial case = 200 KIAS
        Value = dp2tas(66.3355, 20000.0, -24.586)
        Truth = 270.4489
        self.assertAlmostEqual(Value, Truth, delta = 1)
        
    def test_03(self):
        # 200 KIAS at ISA + 20C
        Value = dp2tas(66.3355, 20000.0, -13.4749)
        Truth = 276.4275
        self.assertAlmostEqual(Value, Truth, delta = 1)
        
    def test_04(self):
        # Speed up to 300 KIAS and higher
        Value = dp2tas(153.5471, 30000.0, -44.35)
        Truth = 465.6309
        self.assertAlmostEqual(Value, Truth, delta = 1)

    def test_05(self):
        # Still 300 KIAS but Stratospheric
        Value = dp2tas(153.5469, 45000.0, -56.5)
        Truth = 608.8925
        self.assertAlmostEqual(Value, Truth, delta = 1)
 
class TestMachTat2Sat(unittest.TestCase):

    def test_01(self):

        # Mach 0.5, 15 deg C, K = 0.5
        mach = np.ma.array(data=[0.5, 0.5], mask=[False, True])
        Value = machtat2sat(mach, 15, recovery_factor = 0.5)
        Truth = 7.97195121951
        self.assertAlmostEqual(Value[0], Truth, delta = 1e-5)
        self.assertAlmostEqual(Value.data[1], 1.0, delta = 1e-5)

    
class TestAlt2Sat(unittest.TestCase):

    def test_01(self):

        Value = alt2sat(np.ma.array([0.0, 15000.0, 45000.0]))
        Truth = np.ma.array(data=[15.0, -14.718, -56.5])
        ma_test.assert_almost_equal(Value,Truth)

class Test_dp_over_p2mach(unittest.TestCase):

    def test_01(self):

        Value = dp_over_p2mach(np.ma.array([.52434, .89072, 1.1]))

        # truth values from NASA RP 1046

        Truth = np.ma.array(data=[0.8, 0.999, 1.0], mask=[False, False, True])
        ma_test.assert_almost_equal(Value,Truth, decimal=3)


if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(TestIndexAtValue('test_index_at_value_slice_beyond_top_end_of_data'))
    unittest.TextTestRunner(verbosity=2).run(suite)
