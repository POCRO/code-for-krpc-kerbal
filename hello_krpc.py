import krpc
# the server's name set at the window of krpc in the game
serverName = 'server_ksp'
# create a krpc connection
conn = krpc.connect(\
    name = serverName,
    address='192.168.1.8',
    rpc_port=50000, 
    stream_port = 50001 )
vessal = conn.space_center.active_vessel
print(vessal.name)  #print the current craft name in the game
# close the krpc connection
conn.close