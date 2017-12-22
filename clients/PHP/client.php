<!doctype html>
<html>
<head>
<meta charset="UTF-8">
<title>BLE-Presence PHP Client</title>
</head>

<body>
<?php
$password = htmlspecialchars($_POST["password"]);
$address = htmlspecialchars($_POST["address"]);
$port = htmlspecialchars($_POST["port"]);
//$msg="beacon_data";
$msg = htmlspecialchars($_POST["msg"]);
$order = htmlspecialchars($_POST["order"]);

if ($password == "5225"){
	$sock=socket_create(AF_INET,SOCK_STREAM,0) or die("Cannot create a socket");
	socket_connect($sock,$address,$port) or die("Could not connect to the socket");
	socket_write($sock,$msg);

	$data='';
	$chunk='';

	while(true){
		$chunk = socket_read($sock,4096);
		if (!$chunk) {
			socket_close($sock);
			break; 
			}
		$data .= $chunk;
	}

	//THIS IS COMMENTED OUT BECAUSE NOW WE HAVE A DIFFERENT APPROACH:
	//echo $data;
}

?>
<h1>BLE-Presence PHP Client</h1>
<form action=<?php echo htmlspecialchars($_SERVER["PHP_SELF"]); ?> method="post">&nbsp;
  <label for="password">Client Password:</label>
  <input name="password" type="text" id="password" <?php if ($password !== '' ) { echo 'value="'.$password.'"'; }?> >
	
  <label for="address">Server IP:</label>
  <input name="address" type="text" id="address" <?php if ($address !== '' ) { echo 'value="'.$address.'"'; }?> >
  
  <label for="port">Port:</label>
  <input name="port" type="text" id="port" <?php if ($port !== '' ) { echo 'value="'.$port.'"'; } else { echo 'value="12345"'; } ?> >
	
  <label for="msg">Message to send:</label>
  <input name="msg" type="text" id="msg" <?php if ($msg !== '' ) { echo 'value="'.$msg.'"'; } else { echo 'value="beacon_data"'; } ?> >
  <label for="order">Order:</label>
  <select name="order" id="order">
	<option value="RAW"<?php if ($order == 'RAW' ) { echo ' selected="selected"'; }?>>Just raw data</option>
    <option value="UPDATE"<?php if ($order == 'UPDATE' ) { echo ' selected="selected"'; }?>>Last update (last heard first)</option>
    <option value="RSSI"<?php if ($order == 'RSSI' ) { echo ' selected="selected"'; }?>>RSSI signal (strongest first)</option>
  </select>

  <input type="submit" name="submit" id="submit" value="Invia/Aggiorna">
</form>
<hr>
	<?php
	if ($order == "RAW" and $data !== ""){ 
		echo $data;
		}
	
	if ($order == "UPDATE" and $data !== ""){
		$result_string = substr($data, 1, -1);
		$result_string = str_replace("(","",$result_string);
		$items = explode("), ", $result_string);
		foreach ($items as $item) {
    		$bucket = explode("', ['", $item);
            $BLE_MAC = str_replace("'","",$bucket[0]);
			$ble_data = explode("', '", $bucket[1]);
            $BLE_RSSI = $ble_data[0];
			$BLE_TIME = str_replace("']","",$ble_data[1]);
			$BLE_TIME = str_replace(")","",$BLE_TIME);
			echo $BLE_MAC." RSSI: ".round(((100 - abs($BLE_RSSI))*100)/74)." TIMESTAMP: ".$BLE_TIME."<br>";
			}		
		}
	?>
</body>
</html>