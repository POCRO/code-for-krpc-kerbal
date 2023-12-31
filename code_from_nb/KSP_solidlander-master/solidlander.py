
# 自动定点着陆
# 必须使用solid hover.craft

import krpc
import numpy as np
import time, math, random, sys

import utils


DEBUG_LINES = True
DEBUG_UI = True


conn = krpc.connect(name='controller')
space_center = conn.space_center # SpaceCenter对象
vessel = space_center.active_vessel # 当前载具
body = vessel.orbit.body # 当前载具所处的天体
#vessel.control.sas = False

# lat = -0.0972
# lon = -74.5577
lat = -0.09678
lon = -74.61739
body_frame = body.reference_frame # 地固系

def drawReferenceFrame(frame):
    x_axis = conn.drawing.add_line((10,0,0),(0,0,0), frame)
    x_axis.color = (1, 0, 0)
    x_axis.thickness = 2
    y_axis = conn.drawing.add_line((0,10,0),(0,0,0), frame)
    y_axis.color = (0, 1, 0)
    y_axis.thickness = 2
    z_axis = conn.drawing.add_line((0,0,10),(0,0,0), frame)
    z_axis.color = (0, 0, 1)
    z_axis.thickness = 2

def create_target(body, lat_deg, lon_deg, height_sealevel):
    lat_rad = lat_deg * utils.deg2rad
    lon_rad = lon_deg * utils.deg2rad
    height_cm = height_sealevel + body.equatorial_radius
    target_body_pos = np.array((math.cos(lon_rad) * math.cos(lat_rad), math.sin(lat_rad), math.sin(lon_rad) * math.cos(lat_rad))) * height_cm
    ref_body = body.reference_frame
    return space_center.ReferenceFrame.create_relative(ref_body, position=target_body_pos)

def simulate_final_height(v0, mass, mass_dec_rate, thrust, g):
    m = mass
    h = 0.0
    v = v0
    t = 0.0
    mass_tol = 0.05
    while True:
        # step size
        dt = m * mass_tol / mass_dec_rate
        # 
        acc = g - thrust / m
        vf = v + dt * acc
        if (vf < 0):
            # stop here
            h += v ** 2 / (2 * abs(acc))
            t += v / abs(acc)
            break
        hf = h + v * dt + 0.5 * acc * (dt ** 2)
        mf = m - mass_dec_rate * dt
        v = vf
        h = hf
        m = mf
        t += dt
        #print(f'sim {v:.2f} {h:.2f} {m:.2f} {mass_dec_rate}')
    return h, t


def find_module_by_tag_and_name(vessel, tag, name):
    p = vessel.parts.with_tag(tag)
    if (len(p) == 0):
        print('no part ' + tag)
        return
    p = p[0]
    m = [m for m in p.modules if m.name == name]
    if (len(m) == 0):
        print('no module ' + name)
        print([m.name for m in p.modules])
        return
    m = m[0]
    return m

if (DEBUG_LINES):
    line_l = conn.drawing.add_line((0,0,0),(0,0,0), vessel.reference_frame)
    line_l.color = (1, 0, 0)
    line_r = conn.drawing.add_line((0,0,0),(0,0,0), vessel.reference_frame)
    line_r.color = (1, 0, 0)
    line_c = conn.drawing.add_line((0,0,0),(0,0,0), vessel.reference_frame)
    line_c.color = (1, 1, 0)

# print(hinge_l.fields)
# print(servo_l.fields)


def decouple_input(pitch, yaw, roll, throttle):
    # 正方向： pitch:S yaw:D roll:E

    # 常量：矢量最大偏角
    MAX_TANGENT = np.tan(np.radians(20))
    MAX_ROLL_ANGLE = np.radians(20)

    # 限定throttle
    throttle = utils.clamp(throttle, 0, 1)

    # hinge不能超过180，故yaw方向有上限
    # pitch 可以不受限制，但为了保持一致性还是限制一下
    bias_limit = np.sqrt(1 - throttle ** 2) / MAX_TANGENT
    pitch = utils.clamp(pitch, -bias_limit, bias_limit) 
    yaw = utils.clamp(yaw, -bias_limit, bias_limit)
    roll = utils.clamp(roll, -1, 1)

    # 推力矢量（归一化）
    dst_thrust = utils.v3(-yaw * MAX_TANGENT, 1, pitch * MAX_TANGENT)
    dst_thrust = dst_thrust / np.linalg.norm(dst_thrust) * throttle

    # 解耦合
    roll_angle = roll * MAX_ROLL_ANGLE
    # decompose
    # ====^----> dir
    # \   |   /
    #  \  |  /
    #   \ |-/angle
    #    \|/
    decomp_angle = np.arccos(np.linalg.norm(dst_thrust))
    # 考虑throttle=0特殊处理
    if (throttle < 1e-5):
        decomp_dir = utils.v3(1, 0, 0)
        decomp_dir = utils.rotate_around_axis(decomp_dir, utils.v3(0, 1, 0), roll_angle)
    else:
        decomp_dir = np.cross(dst_thrust, utils.v3(0, 0, 1)) * np.tan(decomp_angle)
        decomp_dir = utils.rotate_around_axis(decomp_dir, dst_thrust, roll_angle)
    dir_l = dst_thrust + decomp_dir
    dir_r = dst_thrust - decomp_dir

    # 解算关节角度
    h_l, s_l = decompose_hinge_angles(dir_l, utils.v3(0, 0, 1))
    h_r, s_r = decompose_hinge_angles(dir_r, utils.v3(0, 0, -1))

    # debug lines
    if (DEBUG_LINES):
        line_l.end = tuple(dir_l * 10)
        line_r.end = tuple(dir_r * 10)
        line_c.end = tuple(dst_thrust * 10)
        #print(dst_thrust)

    # radians to degrees
    return np.degrees((h_l, s_l, h_r, s_r))


def decompose_hinge_angles(vec, hinge_axis):
    vec /= np.linalg.norm(vec)
    hinge_axis /= np.linalg.norm(hinge_axis)
    servo_angle = np.pi / 2 - np.arccos(np.dot(vec, hinge_axis))
    hinge_moving_plane_normal = np.cross(vec, hinge_axis)
    hinge_angle = np.pi - np.arccos(np.dot(hinge_moving_plane_normal, np.cross(utils.v3(0, 1, 0), hinge_axis)))
    return hinge_angle, servo_angle



ref_target_temp = create_target(body, lat, lon, body.surface_height(lat, lon))
ref_surface = vessel.surface_reference_frame
ref_target = space_center.ReferenceFrame.create_hybrid(ref_target_temp, rotation=ref_surface, velocity=ref_target_temp)

#drawReferenceFrame(ref_target)

# 固定命名获取module
# h.l h.r s.l s.r
print('find parts with tag')
hinge_l = find_module_by_tag_and_name(vessel, 'h.l', 'ModuleRoboticServoHinge')
hinge_r = find_module_by_tag_and_name(vessel, 'h.r', 'ModuleRoboticServoHinge')
servo_l = find_module_by_tag_and_name(vessel, 's.l', 'ModuleRoboticRotationServo')
servo_r = find_module_by_tag_and_name(vessel, 's.r', 'ModuleRoboticRotationServo')
print(hinge_l, hinge_r, servo_l, servo_r)


# UI
if (DEBUG_UI):
    canvas = conn.ui.stock_canvas

    # Get the size of the game window in pixels
    screen_size = canvas.rect_transform.size

    # Add a panel to contain the UI elements
    panel = canvas.add_panel()

    # Position the panel on the left of the screen
    rect = panel.rect_transform
    rect.size = (200, 200)
    rect.position = (110-(screen_size[0]/2), 0)

    # Add some text displaying the total engine thrust
    pad = 10
    text = panel.add_text("txt1")
    text.rect_transform.position = (pad, pad)
    text.rect_transform.size = (200 - pad * 2, 200 - pad * 2)
    text.color = (1, 1, 1)
    text.size = 18


# PID
# x & z rotation
ctrl_rot = utils.PIDn(2, kp=1.0, kd=1.0, sd=0.3)
ctrl_roll = utils.PID(kp=1.0, kd=1.0, sd=0.3)

# throttle
des_throttle = 0.7
min_throttle = 0.1
max_throttle = 0.9
throttle_k = 5.0
vel_yz_k = 0.04

#sys.exit(0)
vessel.control.sas = False

game_prev_time = space_center.ut # 记录上一帧时间
while (True):
    time.sleep(0.001)
    ut = space_center.ut # 获取游戏内时间
    game_delta_time = ut - game_prev_time # 计算上一帧到这一帧消耗的时间
    if game_delta_time < 0.019: # 如果游戏中还没有经过一个物理帧，不进行计算
        continue
    
    # data
    pos = utils.v(vessel.position(ref_target))
    vel = utils.v(vessel.velocity(ref_target))
    rot = utils.v(vessel.rotation(ref_target))
    rotation_local2srf = utils.rotation_mat(rot) # 机体系到地面系旋转矩阵
    rotation_srf2local = np.linalg.inv(rotation_local2srf) # 地面系到机体系旋转矩阵
    mass = vessel.mass
    thrust = vessel.available_thrust
    eject_vel = vessel.specific_impulse * 9.806
    g = 9.806

    # control
    if (thrust == 0):
        continue
    
    # throttle

    des_thrust = thrust * des_throttle
    est_drop, est_time = simulate_final_height(-vel[0], mass, thrust / eject_vel, des_thrust, g)
    final_height = pos[0] - est_drop - 1
    throttle = des_throttle - (final_height / max(pos[0], 50)) * throttle_k
    throttle = utils.clamp(throttle, min_throttle, max_throttle)

    if (DEBUG_UI):
        text.content = f'est_t: {est_time:.2f}\nest_h: {final_height: .2f}\n'
    
    # horizontal
    des_vel_yz = utils.clamp_mag(-pos[1:3] / max(2, est_time / 3), 40)
    vel_yz_error = vel[1:3] - des_vel_yz
    target_direction = utils.v3(1, 0, 0)
    target_direction[1:3] = utils.clamp_mag(-vel_yz_error * vel_yz_k, np.tan(np.radians(25)))
    target_roll = 0 if pos[0] < 50 else np.radians(90)

    # directional
    target_direction_local = utils.transform(target_direction, rotation_srf2local)
    pitch_error = utils.angle_around_axis(utils.v3(0, 1, 0), target_direction_local, utils.v3(1, 0, 0))
    yaw_error = utils.angle_around_axis(utils.v3(0, 1, 0), target_direction_local, utils.v3(0, 0, 1))
    pitch, yaw = ctrl_rot.update([pitch_error, yaw_error], game_delta_time)
    # roll
    roll_pointer = utils.transform(utils.v3(0, 0, 1), rotation_local2srf)
    roll_error = (np.arctan2(-roll_pointer[2], roll_pointer[1]) - target_roll + np.pi) % (2 * np.pi) - np.pi
    roll = ctrl_roll.update(roll_error, game_delta_time)

    h_l, s_l, h_r, s_r = decouple_input(pitch, yaw, roll, throttle)
    hinge_l.set_field_float('Target Angle', h_l)
    hinge_r.set_field_float('Target Angle', h_r)
    servo_l.set_field_float('Target Angle', s_l)
    servo_r.set_field_float('Target Angle', s_r)

    vessel.control.pitch = pitch                # 哦哦哦原来这里可以直接控制整个 vessel 的各种角度的啊
    vessel.control.yaw = yaw
    vessel.control.roll = roll
    vessel.control.throttle = throttle
    
    if (pos[0] < 100): # 开起落架
        vessel.control.gear = True
        print(pos[0], est_drop)
    if (pos[0] < 6): # 结束
        hinge_l.set_field_float('Target Angle', 0)
        hinge_r.set_field_float('Target Angle', 0)
        servo_l.set_field_float('Target Angle', 0)
        servo_r.set_field_float('Target Angle', 0)
        break

    print(game_delta_time)
    game_prev_time = ut # 更新上一帧时间记录



