# 完全自己手写的 pid 高度控制

import krpc
import time
import matplotlib.pyplot as plt
target_hight = 50
conn = krpc.connect( name = 'pid controller')
vessel = conn.space_center.active_vessel
vessel.control.sas = True
vessel.control.activate_next_stage()
ref = vessel.orbit.body.reference_frame
p = 2.25
pi = 5.5
pd = 5
H_list = []                         # 建立一个列表存放每一次循环中的高度以便绘图
e = 1
integ_e = 0                         # 初始化误差和累计误差用于 pid 控制
vessel.control.throttle = 0
while True:
    pos = vessel.position(ref)
    # print('(%.1f %.1f %.1f)' % (pos[0],pos[1],pos[2]))
    # time.sleep(1)           #不停检测并每隔一秒打印当前高度
    e =  vessel.flight().surface_altitude - target_hight - 2.4 # 2.4是该飞船质心高度
    H_list.append(vessel.flight().surface_altitude) 
    integ_e += e 
    div_e = vessel.flight(ref).vertical_speed
    # print('speed is %.1f' %div_e)
    if e != 0:
        vessel.control.throttle = abs(p * e/100 + pi*integ_e/10000 + pd*div_e/100)
        if vessel.control.throttle > 1:
            vessel.control.throttle = 1
    print('hight is %.1f' % e)
    time.sleep(0.1)
    if abs(e) < 0.5 and abs(div_e) < 0.5:
        break

plt.figure(3)       # 绘制高度随时间的变化图
t = [i/10 for i in range(1,len(H_list)+1)]
plt.plot(t ,H_list)
plt.show()