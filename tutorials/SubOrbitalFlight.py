import time
import krpc
conn = krpc.connect(name='Sub-orbital flight')

vessel = conn.space_center.active_vessel
# 发射前设定
vessel.auto_pilot.target_pitch_and_heading(90, 90) # 设定航向角为90度
vessel.auto_pilot.engage()                      # 进入自动驾驶
vessel.control.throttle = 1                     # 油门开到最大
time.sleep(1)                                   # 缓冲一秒再继续发射

print('Launch!')
vessel.control.activate_next_stage()            # 激活下一级，相当于按下点火
# 控制固推分离
fuel_amount = conn.get_call(vessel.resources.amount, 'SolidFuel') #获取固推燃料剩余量
expr = conn.krpc.Expression.less_than(
    conn.krpc.Expression.call(fuel_amount),
    conn.krpc.Expression.constant_float(0.1)) # 创建比较表达式 判断剩余燃料是否小于 0.1 
event = conn.krpc.add_event(expr) # 定义事件为分离做好准备，当事件为 true 的时候发生事件
with event.condition:
    event.wait()                 # 当事件一直是假的时候就等待，这一事件仍未结束
print('Booster separation')     # 固推分离 ！
vessel.control.activate_next_stage()    #启动下一级

## 进行重力转弯

mean_altitude = conn.get_call(getattr, vessel.flight(), 'mean_altitude') # flight 变量中含有各种飞行参数
expr = conn.krpc.Expression.greater_than(
    conn.krpc.Expression.call(mean_altitude),  # 创建比较表达式 判断高度是否大于 10 km
    conn.krpc.Expression.constant_double(10000))
event = conn.krpc.add_event(expr)
with event.condition:                           # 当事件一直假的时候就一直 wait
    event.wait()

print('Gravity turn')   # 执行重力转弯
vessel.auto_pilot.target_pitch_and_heading(60, 90) # 保持 heading不变继续向西，但倾角改成 60 度
# 远点制动
apoapsis_altitude = conn.get_call(getattr, vessel.orbit, 'apoapsis_altitude')
expr = conn.krpc.Expression.greater_than(
    conn.krpc.Expression.call(apoapsis_altitude),
    conn.krpc.Expression.constant_double(100000))   # 创建比较表达式 判断高度是否大于 100 km
event = conn.krpc.add_event(expr)
with event.condition:
    event.wait()                                     # 当事件一直假的时候就一直 wait

print('Launch stage separation')        # 船舰分离
vessel.control.throttle = 0             # 关闭油门
time.sleep(1)                           #等待一秒
vessel.control.activate_next_stage()    #激活下一级
vessel.auto_pilot.disengage()           #关闭自动驾驶

srf_altitude = conn.get_call(getattr, vessel.flight(), 'surface_altitude')
expr = conn.krpc.Expression.less_than(
    conn.krpc.Expression.call(srf_altitude),
    conn.krpc.Expression.constant_double(5000))
event = conn.krpc.add_event(expr)       #在高度大于 5km 时wait
with event.condition:
    event.wait()

vessel.control.activate_next_stage()     # 当高度低于 5km 时开伞

while vessel.flight(vessel.orbit.body.reference_frame).vertical_speed < -0.1:
    print('Altitude = %.1f meters' % vessel.flight().surface_altitude)
    time.sleep(1)           #不停检测并每隔一秒打印当前高度
print('Landed!')            # 成功着陆！
