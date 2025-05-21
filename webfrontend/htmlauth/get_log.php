<?php
$log_dir = "/opt/loxberry/data/plugins/consumption_prediction/";
$log_files = ["mqtt_daemon.log", "prediction.log", "train_model.log", "eval.log"];

$selected_log = $_GET['log'] ?? 'mqtt_daemon.log';
$log_path = realpath($log_dir . basename($selected_log));

// Validate
if (!$log_path || strpos($log_path, realpath($log_dir)) !== 0 || !in_array(basename($log_path), $log_files)) {
    http_response_code(400);
    echo "Invalid log file.";
    exit;
}

$lines = file($log_path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
$lines = array_reverse($lines);

header('Content-Type: application/json');
echo json_encode($lines);
