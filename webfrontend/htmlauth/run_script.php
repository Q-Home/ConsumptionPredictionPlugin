<?php
if (!isset($_GET['script'])) {
    http_response_code(400);
    echo "No script specified.";
    exit;
}

$script = $_GET['script'];
$basePath = "/opt/loxberry/bin/plugins/consumption_prediction/";

$scripts = [
    "train" => "train_model.py",
    "predict" => "prediction.py"
];

if (!array_key_exists($script, $scripts)) {
    http_response_code(400);
    echo "Invalid script specified.";
    exit;
}

$cmd = escapeshellcmd("/usr/bin/python3 " . $basePath . $scripts[$script] . " > /dev/null 2>&1 &");
exec($cmd);

echo ucfirst($script) . " script started.";
?>
