<?php
require_once "loxberry_web.php";
require_once "loxberry_system.php";

$L = LBSystem::readlanguage("language.ini");
$template_title = "Consumption Prediction Settings";
$helplink = "http://www.loxwiki.eu:80/x/2wzL";
$helptemplate = "help.html";

// Navigation
$navbar[1]['Name'] = 'Home';
$navbar[1]['URL'] = 'index.php';
$navbar[2]['Name'] = 'Settings';
$navbar[2]['URL'] = 'settings.php';
$navbar[2]['active'] = true;
$navbar[3]['Name'] = 'Logs';
$navbar[3]['URL'] = 'logs.php';

LBWeb::lbheader($template_title, $helplink, $helptemplate);

// File locations
$settings_file = '/opt/loxberry/data/plugins/consumption_prediction/settings.json';
$docker_compose_file = '/opt/loxberry/bin/plugins/consumption_prediction/docker-compose.yml';

// Load files
$settings_contents = file_exists($settings_file) ? file_get_contents($settings_file) : '';
$docker_compose_contents = file_exists($docker_compose_file) ? file_get_contents($docker_compose_file) : '';

// Save form submission
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    if (isset($_POST['settings_json'])) {
        file_put_contents($settings_file, $_POST['settings_json']);
    }
    if (isset($_POST['docker_compose'])) {
        file_put_contents($docker_compose_file, $_POST['docker_compose']);
    }

    // Extract influx port from settings JSON for docker restart
    $settings_array = json_decode($_POST['settings_json'], true);
    $influx_port = $settings_array['influxdb_port'] ?? '8086';

    $docker_compose_path = '/opt/loxberry/bin/plugins/consumption_production';
    $cmd = "cd " . escapeshellarg($docker_compose_path) . 
           " && INFLUX_PORT=" . escapeshellarg($influx_port) . " docker compose up -d 2>&1";
    shell_exec($cmd);

    echo '<div class="alert alert-success text-center">Settings saved successfully. Docker container restarting...</div>';

    // Reload updated content for display after save
    $settings_contents = file_get_contents($settings_file);
    $docker_compose_contents = file_get_contents($docker_compose_file);
}
?>

<link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">

<div class="container mt-5">
    <div class="col-lg-10 offset-lg-1">
        <h3 class="mb-4">Edit Full Settings JSON File</h3>
        <form method="POST">
            <div class="form-group">
                <textarea name="settings_json" class="form-control" rows="20" style="font-family: monospace;"><?= htmlspecialchars($settings_contents) ?></textarea>
            </div>

            <h3 class="mb-4 mt-5">Edit Docker Compose YAML File</h3>
            <div class="form-group">
                <textarea name="docker_compose" class="form-control" rows="30" style="font-family: monospace;"><?= htmlspecialchars($docker_compose_contents) ?></textarea>
            </div>

            <div class="text-center mt-4 mb-5">
                <button type="submit" class="btn btn-primary px-5">Save Settings</button>
            </div>
        </form>
    </div>
</div>

<?php LBWeb::lbfooter(); ?>
