import krpc
from math import sin, cos, pi
import time

def drawReferenceFrame(frame):      # 定义函数绘制建立的坐标系
    x_axis = conn.drawing.add_line((10,0,0),(0,0,0), frame)
    x_axis.color = (1, 0, 0)
    x_axis.thickness = 2
    y_axis = conn.drawing.add_line((0,10,0),(0,0,0), frame)
    y_axis.color = (0, 1, 0)
    y_axis.thickness = 2
    z_axis = conn.drawing.add_line((0,0,10),(0,0,0), frame)
    z_axis.color = (0, 0, 1)
    z_axis.thickness = 2

conn = krpc.connect(name='controller')
space_center = conn.space_center # SpaceCenter对象
vessel = space_center.active_vessel # 当前载具
body = vessel.orbit.body # 当前载具所处的天体 
# 在发射台中心建立坐标系（如果不会的话请看上一篇）：x轴向上，y轴朝北，z轴朝东
# https://www.bilibili.com/read/cv9657892?spm_id_from=333.999.0.0
# 发射台中心坐标系 的经度为经度-74.5577，纬度 -0.0972 
# VAB大楼楼顶停机坪中心点的经度为 -74.61739，纬度为 -0.09678 

lat = -0.09678 
lon = -74.61739
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

while True:
    print('%.1f %.1f %.1f '%vessel.position(target_frame))
    time.sleep(1)
    drawReferenceFrame(target_frame) # 调用上述函数，画出之前建立的着陆点坐标系