import math 
import time
import krpc

turn_start_altitude = 250
turn_end_altitude = 45000
target_altitude = 150000

conn = krpc.connect(name='Launch into orbit')
vessel = conn.space_center.active_vessel

# 建立遥感数据流
ut = conn.add_stream(getattr, conn.space_center, 'ut')
altitude = conn.add_stream(getattr, vessel.flight(), 'mean_altitude')
apoapsis = conn.add_stream(getattr, vessel.orbit, 'apoapsis_altitude')
stage_2_resources = vessel.resources_in_decouple_stage(stage=2, cumulative=False)
srb_fuel = conn.add_stream(stage_2_resources.amount, 'SolidFuel')  
# 原来就是这里的 SolidFuel 多打了一个空格，这个类就找不到了，所以返回的 srb 燃料容量一直是 0

# 预发射阶段 关闭 sas 和 rcs， 油门拉满
vessel.control.sas = False               
vessel.control.rcs = False
vessel.control.throttle = 1.0

# 倒计时
print('3...')
time.sleep(1)
print('2...')
time.sleep(1)
print('1...')
time.sleep(1)
print('Launch!')
# 发射段，一直循环直到远点达到指定远点并不断监测固推燃料剩余量
# 点火（点燃第一级）
vessel.control.activate_next_stage()
vessel.auto_pilot.engage()
vessel.auto_pilot.target_pitch_and_heading(90, 90)

# 主循环
srbs_separated = False
turn_angle = 0
while True:
    # 重力转弯
    if altitude() > turn_start_altitude and altitude() < turn_end_altitude:
        frac = ((altitude() - turn_start_altitude) /
                (turn_end_altitude - turn_start_altitude))
        new_turn_angle = 90*frac
        if abs(new_turn_angle - turn_angle) > 0.5:
            turn_angle = new_turn_angle
            vessel.auto_pilot.target_pitch_and_heading(90-turn_angle, 90)

    print('srb furel = %.1f' % srb_fuel())           # 测试代码检查 srb 剩余燃料量
    time.sleep(1)

    # 分离固推
    if not srbs_separated:
        if srb_fuel() < 0.1:
            vessel.control.activate_next_stage()
            srbs_separated = True
            print('SRBs separated')
    #if (not srbs_separated) and ( srb_fuel() < 0.1):
    #    vessel.control.activate_next_stage()
    #    srbs_separated = True
    #    print('SRBs seperated!')
    # 判断循环条件   (当远点达到 0.9 目标远点时就结束重力转弯，为变轨做好准备)
    if apoapsis() > target_altitude > 0.9:
        print('Approaching target apoapsis')
        break

#等待变轨，将油门调小，等待飞出大气层
vessel.control.throttle = 0.25 
while apoapsis() < target_altitude:
    pass
print('Target apoaosis reached')
vessel.control.throttle = 0
print('Coasting the atomsphere')
while altitude() < 70500:
    pass

# 准备圆化轨道变轨
print('Planning circularization burn')
mu = vessel.orbit.body.gravitational_parameter
r = vessel.orbit.apoapsis
a1 = vessel.orbit.semi_major_axis  # 半长轴
a2 = r
v1 = math.sqrt(mu*((2/r)-(1/a1)))     # 其实就是靠能量守恒方程直接推出来远点速度
v2 = math.sqrt(mu*((2/r)-(1/a2)))    # 美其名曰 vis-viva 方程
delta_v = v2 - v1
node = vessel.control.add_node(
    ut() + vessel.orbit.time_to_apoapsis, prograde = delta_v
)           # 为点火创建节点

#计算点火时间
F = vessel.available_thrust    # F 是可用喷力 
Isp = vessel.specific_impulse * 9.82        #乘上g0可以把特定脉冲换算成 Isp
#此处公式可见于 https://wiki.kerbalspaceprogram.com/wiki/Specific_impulse#Multiple_engines
m0 = vessel.mass
m1 = m0 / math.exp(delta_v/Isp) # 由齐奥尔科夫斯基公式，这玩意是变轨后航天器质量
flow_rate = F/Isp   # 比冲定义式
burn_time = (m0 - m1) / flow_rate

# 旋转飞船等待循环燃烧，并等待到点火前 5 秒钟
print('Orientating ship for circulation burn')
vessel.auto_pilot.reference_frame = node.reference_frame        # 换到点火点所在坐标系中
vessel.auto_pilot.target_direction = (0,1,0)                    # y 方向是轨道切向
burn_ut = ut() + vessel.orbit.time_to_apoapsis - (burn_time/2.) # 求出标准时间中点火的时间节点
lead_time = 5
conn.space_center.warp_to(burn_ut - lead_time)                  # 加速到点火节点前5秒
# 执行圆化轨道点火
print('Ready to excute burn ')
time_to_apoapsis = conn.add_stream(getattr,vessel.orbit,'time_to_apoapsis')
while time_to_apoapsis() - (burn_time/2) > 0:
    pass
print('Executing burn')
vessel.control.throttle = 1.0   # 油门开满
time.sleep(burn_time - 0.1)
print('Fine turning ')
vessel.control.throttle = 0.05
remaining_burn = conn.add_stream(node.remaining_burn_vector, node.reference_frame)
while remaining_burn()[1] > 0:
    pass
vessel.control.throttle = 0.0
node.remove()                       # 移去点火节点
print('Launch complete')