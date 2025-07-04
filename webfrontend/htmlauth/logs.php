<?php
require_once "loxberry_web.php";
require_once "loxberry_system.php";

$L = LBSystem::readlanguage("language.ini");
$template_title = "Plugin Logs";
$helplink = "http://www.loxwiki.eu:80/x/2wzL";
$helptemplate = "help.html";

// Navigation
$navbar[1]['Name'] = 'Home';
$navbar[1]['URL'] = 'index.php';
$navbar[2]['Name'] = 'Settings';
$navbar[2]['URL'] = 'settings.php';
$navbar[3]['Name'] = 'Logs';
$navbar[3]['URL'] = 'logs.php';
$navbar[3]['active'] = true;

LBWeb::lbheader($template_title, $helplink, $helptemplate);

// Define log paths
$log_dir = "/opt/loxberry/data/plugins/consumption_prediction/";
$log_files = [
    "mqtt_daemon.log" => "MQTT Listener",
    "prediction.log" => "Prediction",
    "train_model.log" => "Model Training",
    "eval.log" => "Model Evaluation ",
    "send_predictions.loh" => "Prediction Sending",

];

$selected_log = $_GET['log'] ?? 'mqtt_daemon.log';
$log_path = realpath($log_dir . basename($selected_log));

// Validate file exists and is within log_dir
$valid = ($log_path && strpos($log_path, realpath($log_dir)) === 0 && file_exists($log_path));
$log_lines = [];

if ($valid) {
    $log_lines = file($log_path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    $log_lines = array_reverse($log_lines); // Newest entries first
     $log_lines = array_slice($log_lines, 0, 500); // Only show the 500 newest lines
}
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <title>Log Viewer</title>
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" />
    <style>
        /* Log viewer styling */
        #log-viewer {
            width: 100%;
            height: 600px;
            overflow-y: scroll;
            border: 1px solid #ccc;
            padding: 10px;
            margin-top: 20px;
            font-family: monospace;
            font-size: 13px;
            background-color: #f9f9f9;
        }

        .log-info {
            color: #000000;
        }

        .log-warning {
            color: #FF9800;
        }

        .log-error {
            color: #F44336;
        }

        .log-info, .log-warning, .log-error {
            padding: 5px 0;
            border-bottom: 1px solid #ddd;
            white-space: pre-wrap;
        }

        .nav-tabs .nav-link.active {
            font-weight: bold;
        }

        /* Refresh link styled as nav-link */
        #refresh-log {
            cursor: pointer;
        }
    </style>
</head>
<body>
<div class="container mt-5">
    <div class="col-lg-10 offset-lg-1">
        <h3 class="mb-4">Log Viewer</h3>

        <!-- Navigation Tabs and Refresh Link -->
        <ul class="nav nav-tabs mb-3">
            <?php foreach ($log_files as $filename => $label): ?>
                <li class="nav-item">
                    <a class="nav-link <?= ($selected_log === $filename) ? 'active' : '' ?>" href="?log=<?= urlencode($filename) ?>">
                        <?= htmlspecialchars($label) ?>
                    </a>
                </li>
            <?php endforeach; ?>
            <li class="nav-item ml-auto">
                <a href="#" id="refresh-log" class="nav-link" title="Refresh Log">Refresh</a>
            </li>
        </ul>

        <!-- Log output box -->
        <div id="log-viewer">
            <?php if ($valid): ?>
                <?php foreach ($log_lines as $line): ?>
                    <?php
                        $logClass = 'log-info';
                        if (stripos($line, '[error]') !== false) {
                            $logClass = 'log-error';
                        } elseif (stripos($line, '[warning]') !== false) {
                            $logClass = 'log-warning';
                        }
                    ?>
                    <div class="<?= $logClass ?>"><?= htmlspecialchars(trim($line)) ?></div>
                <?php endforeach; ?>
            <?php else: ?>
                <div class="text-danger">Log file not found or invalid.</div>
            <?php endif; ?>
        </div>
    </div>
</div>

<script>
    document.getElementById('refresh-log').addEventListener('click', function(event) {
        event.preventDefault();

        // Fetch log content via AJAX
        const params = new URLSearchParams(window.location.search);
        const selectedLog = params.get('log') || 'mqtt_daemon.log';

        fetch('logs.php?log=' + encodeURIComponent(selectedLog) + '&ajax=1')
            .then(response => response.text())
            .then(html => {
                document.getElementById('log-viewer').innerHTML = html;
            })
            .catch(error => {
                alert('Error refreshing log: ' + error);
            });
    });
</script>

<?php LBWeb::lbfooter(); ?>
</body>
</html>

<?php
// Handle AJAX request for refreshing log content
if (isset($_GET['ajax']) && $_GET['ajax'] == 1) {
    if ($valid) {
        foreach ($log_lines as $line) {
            $logClass = 'log-info';
            if (stripos($line, '[error]') !== false) {
                $logClass = 'log-error';
            } elseif (stripos($line, '[warning]') !== false) {
                $logClass = 'log-warning';
            }
            echo '<div class="' . $logClass . '">' . htmlspecialchars(trim($line)) . '</div>';
        }
    } else {
        echo '<div class="text-danger">Log file not found or invalid.</div>';
    }
    exit;
}
?>
