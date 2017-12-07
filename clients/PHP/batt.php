<?php
$address="10.50.0.55";
$port="12345";
$msg="battery_level: de:7f:fd:9a:df:78,fd:6c:9a:dc:e2:a8,c7:7e:de:7a:a0:10";

$sock=socket_create(AF_INET,SOCK_STREAM,0) or die("Cannot create a socket");
socket_connect($sock,$address,$port) or die("Could not connect to the socket");
socket_write($sock,$msg);

$read=socket_read($sock,32768);
echo $read;
socket_close($sock);
?>