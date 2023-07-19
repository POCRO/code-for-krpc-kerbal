import matplotlib.pyplot as plt
import numpy as np

dt = 0.02


# sum_err has already been multiplied by ki
def pid(max, min, kp, ki, kd, seek, current, prev_err, sum_err):
    err = seek - current
    P = kp * err
    I = ki * P * dt + sum_err
    D = kd * (err - prev_err) / dt
    bias = P + I + D
    if bias > max:
        bias = max
    if bias < min:
        bias = min
    return bias, err, I


target_x = 0
target_y = 0
target_z = 120

x = 200
y = 500
z = 0

v_x = 0
v_y = 0
v_z = 0

prev_err_x = target_x - x
prev_err_y = target_y - y
prev_err_z = target_z - z

# if you let sum_err = prev_err to make a pre-calculation,
# that's wrong, because the err has not been multiplied by ki.
sum_err_x = 0
sum_err_y = 0
sum_err_z = 0

simulation_limit = 10000
angle_limit = 20
mass = 5e3
max_thrust = 100e3
g = 9.82

x_list = []
y_list = []
z_list = []
i = 0

while (prev_err_x ** 2 + prev_err_y ** 2) > 1 or (v_x ** 2 + v_y ** 2) > 0.01:
    i += 1
    bias_z, prev_err_z, sum_err_z = pid(1, 0, 0.06, 0.02, 0.08, target_z, z, prev_err_z, sum_err_z)
    bias_x, prev_err_x, sum_err_x = pid(angle_limit, -angle_limit, 0.8, 0.001, 2, target_x, x, prev_err_x, sum_err_x)
    bias_y, prev_err_y, sum_err_y = pid(angle_limit, -angle_limit, 0.8, 0.001, 2, target_y, y, prev_err_y, sum_err_y)

    thrust = max_thrust * bias_z
    F_x = np.sin(bias_x / 180 * np.pi) * thrust
    F_y = np.sin(bias_y / 180 * np.pi) * thrust
    F_z = np.sqrt(thrust ** 2 - F_x ** 2 - F_y ** 2) - mass * g

    a_x = F_x / mass
    a_y = F_y / mass
    a_z = F_z / mass

    v_x += a_x * dt
    x += v_x * dt
    x_list.append(x)

    v_y += a_y * dt
    y += v_y * dt
    y_list.append(y)

    v_z += a_z * dt
    z += v_z * dt
    z_list.append(z)

    if i > simulation_limit:
        break


print('x stage1 position:', x_list[-1])
print('y stage1 position:', y_list[-1])
print('z stage1 position:', z_list[-1])
print('x stage1 velocity:', v_x)
print('y stage1 velocity:', v_y)
t = dt * i
print('stage1 convergence time:', t)

target_z = 100
prev_err_z = target_z - z
while prev_err_z ** 2 > 1:
    i += 1
    bias_z, prev_err_z, sum_err_z = pid(1, 0, 0.5, 0., 2, target_z, z, prev_err_z, sum_err_z)

    thrust = max_thrust * bias_z
    F_z = thrust - mass * g
    a_z = F_z / mass

    x += v_x * dt
    x_list.append(x)

    y += v_y * dt
    y_list.append(y)

    v_z += a_z * dt
    z += v_z * dt
    z_list.append(z)

    if i > simulation_limit * 2:
        break

print('x stage2 position:', x_list[-1])
print('y stage2 position:', y_list[-1])
print('z stage2 position:', z_list[-1])
print('z stage2 velocity:', v_z)
t = dt * i
print('stage2 convergence time:', t)

plt.figure(3)
ax = plt.axes(projection='3d')
ax.plot3D(x_list, y_list, z_list)
plt.show()
