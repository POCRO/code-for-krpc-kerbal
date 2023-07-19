# the API for krpc
## the api for vessel 
1. g_force   
   The current G force acting on the vessel 
2. mean_altitude  
   The altitude above sea level, in meters. 
3. surface_altitude  
   The altitude above the surface of the body or sea level, whichever is closer, in meters.
4. bedrock_altitude
   The altitude above the surface of the body, in meters.   
# 坐标系
## 三种坐标系（都是左手系）
1. Celestial Body Reference Frame 星球坐标系（地形赤道旋转坐标系） 与坎星固连
   y指向北极点， x指向本初子午线
2. Vessel Orbital Reference Frame 飞船轨道参考系（质心轨道坐标系） 与飞船轨道固连
   y指向轨道切向， x法向向内， z垂直轨道平面向上
3. Vessel Reference Frame 飞船参考系（航天器本体坐标系） 与飞船固连
   y 指向飞船指向，x 指向飞船右边，z 指向飞船下面
4. Surface Reference Frame 地表坐标系
   x 向上，y 向北，z 向东
## 坐标系变换
   SpaceCenter.transform_position()
   SpaceCenter.transform_direction()
   SpaceCenter.transform_rotation()
   SpaceCenter.transform_velocity()