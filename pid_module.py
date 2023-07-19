# 把大佬写的魔改了一下，模块化的 pid 真的很爱 （包含了很 nb 的坐标系变换）
import krpc
from math import sin, cos, pi
import time

conn = krpc.connect(name='pid controller')
space_center = conn.space_center # SpaceCenter对象
vessel = space_center.active_vessel # 当前载具
body = vessel.orbit.body # 当前载具所处的天体
vessel.control.sas = True
vessel.control.activate_next_stage()
lat = -0.0972
lon = -74.5577
body_frame = body.reference_frame # 地固系
# 绕y轴旋转-lon度
temp1 = space_center.ReferenceFrame.create_relative(body_frame,
    rotation=(0., sin(-lon / 2. * pi / 180), 0., cos(-lon / 2. * pi / 180)))
# 绕z轴旋转lat度
temp2 = space_center.ReferenceFrame.create_relative(temp1,
    rotation=(0., 0., sin(lat / 2. * pi / 180), cos(lat / 2. * pi / 180)))
# 沿x轴平移
height = body.surface_height(lat, lon) + body.equatorial_radius
target_frame = space_center.ReferenceFrame.create_relative(temp2,
    position=(height, 0., 0.))

# 控制一个数的范围
def clamp(num, limit1, limit2):
    return max(min(num, max(limit1, limit2)), min(limit1, limit2))
# PID控制器
class PID:
    def __init__(self, kp, ki, kd, integral_output_limit = 1):
        self.kp = kp
        self.ki = ki
        self.kd = kd

        self.integral_output_limit = integral_output_limit
        self.integral = 0
        self.error_prev = 0

    def update(self, error, dt):
        # 计算 P 分量
        p = error * self.kp/100
        # 计算 I 分量
        self.integral += error * dt * self.ki/10000
        #self.integral = clamp(self.integral, self.integral_output_limit, -self.integral_output_limit)
        i = self.integral
        # 计算 D 分量
        d = (error - self.error_prev) / dt * self.kd/100
        self.error_prev = error
        # 加起来得到结果
        return p + i + d 
# 在循环开始前初始化一个 PID 控制器
height_pid = PID(kp=2.25, ki=5.5, kd=5)
game_prev_time = space_center.ut # 记录上一帧时间
while (True):
    time.sleep(0.001)
    ut = space_center.ut # 获取游戏内时间
    game_delta_time = ut - game_prev_time # 计算上一帧到这一帧消耗的时间
    if game_delta_time < 0.019: # 如果游戏中还没有经过一个物理帧，不进行计算
        continue
    # 在这里写控制代码
    height = vessel.position(target_frame)[0]
    error = 100 - height
    vessel.control.throttle = height_pid.update(error, game_delta_time)
    clamp(vessel.control.throttle, 0, 1)        # 把油门始终控制在 0 和 1 之间
    # 打印出 dt 和error
    print('dt=%.3f, error=%.2f    ' % (game_delta_time, error), end='\r')
    game_prev_time = ut # 更新上一帧时间记录 
