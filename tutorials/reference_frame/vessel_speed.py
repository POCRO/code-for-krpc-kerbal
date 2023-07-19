import time
import krpc

conn = krpc.connect(name='Vessel speed')
vessel = conn.space_center.active_vessel
obt_frame = vessel.orbit.body.non_rotating_reference_frame      # 轨道速度
srf_frame = vessel.orbit.body.reference_frame                   

while True:
    obt_speed = vessel.flight(obt_frame).speed                  # 轨道速度
    srf_speed = vessel.flight(srf_frame).speed                  # 表面速度
    print('Orbital speed = %.1f m/s, Surface speed = %.1f m/s' %
          (obt_speed, srf_speed))       # 每隔一秒打印一次
    time.sleep(1)