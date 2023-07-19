import math 
import time
import krpc

turn_start_altitude = 250
turn_end_altitude = 45000
target_altitude = 150000

conn = krpc.connect(name = 'Launch into orbit')
vessel = conn.space_center.active_vessel

# 建立遥感数据流
ut = conn.add_stream(getattr,conn.space_center, 'ut')
altitude = conn.add_stream(getattr, vessel.flight(),'mean_altitude')
apoapsis = conn.add_stream(getattr,vessel.orbit,'apoapsis_altitude')

stage_1_resources = vessel.resources_in_decouple_stage(stage = 1, cumulative=False)
main_fuel = conn.add_stream(stage_1_resources.amount,'Mainfuel')

stage_2_resources = vessel.resources_in_decouple_stage(stage = 2, cumulative=False)
srb_fuel = conn.add_stream(stage_2_resources.amount,'Solidfuel')

while True:
    print('stage_1 fuel = %.1f' % main_fuel())
    print('stage_2 fuel = %.1f' % srb_fuel())
    time.sleep(1)