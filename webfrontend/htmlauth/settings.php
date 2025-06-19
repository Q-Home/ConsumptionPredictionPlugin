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

// Load or initialize settings
$settings_file = '/opt/loxberry/data/plugins/consumption_prediction/settings.json';
$defaults = [
    'mqtt_broker' => 'localhost',
    'mqtt_port' => 1883,
    'mqtt_username' => 'loxberry',
    'mqtt_password' => 'loxberry',
    'mqtt_topic_prediction' => 'home/energy/predictions',
    'mqtt_topic_consumption' => 'home/energy/consumption',
    'mqtt_topic_loxone'=> 'home/loxone/logs',
    "mqtt_topic_publish_predictions" =>"home\/energy\/predictions\/publish",
    "loxone_ip" => "192.168.x.x",
    "loxone_username" => "admin",
    "loxone_password"=> "admin",
    "LAT"=> "50.883785",
    "LON"=> "3.424479",
    "PANEL_AREA"=> 10.0,
    "EFFICIENCY"=> 0.20
];
$settings = $defaults;

if (file_exists($settings_file)) {
    $settings = array_merge($defaults, json_decode(file_get_contents($settings_file), true));
}

// Save form submission
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    foreach ($settings as $key => $val) {
        if (isset($_POST[$key])) {
            $settings[$key] = $_POST[$key];
        }
    }
    file_put_contents($settings_file, json_encode($settings, JSON_PRETTY_PRINT));

    // Restart Docker container after saving settings
    $docker_compose_path = '/opt/loxberry/bin/plugins/consumption_prediction'; 
    $output = shell_exec("cd $docker_compose_path && docker compose restart mqtt_daemon 2>&1");

    echo '<div class="alert alert-success text-center">Settings saved successfully. Docker container restarting...</div>';
    #echo '<pre class="bg-light p-3 border rounded">' . htmlspecialchars($output) . '</pre>';
}
?>

<link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">

<div class="container mt-5">
    <div class="col-lg-8 offset-lg-2">
        <h3 class="mb-4">Plugin Configuration</h3>
        <form method="POST">
            <h5>MQTT Settings</h5>
            <div class="form-group">
                <label>Broker</label>
                <input type="text" name="mqtt_broker" class="form-control" value="<?= htmlspecialchars($settings['mqtt_broker']) ?>">
            </div>
            <div class="form-group">
                <label>Port</label>
                <input type="number" name="mqtt_port" class="form-control" value="<?= htmlspecialchars($settings['mqtt_port']) ?>">
            </div>
            <div class="form-group">
                <label>Username</label>
                <input type="text" name="mqtt_username" class="form-control" value="<?= htmlspecialchars($settings['mqtt_username']) ?>">
            </div>
            <div class="form-group">
                <label>Password</label>
                <input type="password" name="mqtt_password" class="form-control" value="<?= htmlspecialchars($settings['mqtt_password']) ?>">
            </div>
            <div class="form-group">
                <label>Topic - Prediction</label>
                <input type="text" name="mqtt_topic_prediction" class="form-control" value="<?= htmlspecialchars($settings['mqtt_topic_prediction']) ?>">
            </div>
            <div class="form-group">
                <label>Topic - Consumption</label>
                <input type="text" name="mqtt_topic_consumption" class="form-control" value="<?= htmlspecialchars($settings['mqtt_topic_consumption']) ?>">
            </div>
            <div class="form-group">
                <label>Topic - Publish Predictions</label>
                <input type="text" name="mqtt_topic_publish_predictions" class="form-control" value="<?= htmlspecialchars($settings['mqtt_topic_publish_predictions']) ?>">
            </div>
            <div class="form-group">
                <label>Topic - Loxone Logs</label>
                <input type="text" name="mqtt_topic_loxone" class="form-control" value="<?= htmlspecialchars($settings['mqtt_topic_loxone']) ?>">
            </div>

            <br>
            <h5>OpenMeteo API</h5>
            <div class="form-group">
                <label>Latitude</label>
                <input type="password" name="LAT" class="form-control" value="<?= htmlspecialchars($settings['LAT']) ?>">
                <label>Longitude</label>
                <input type="password" name="LON" class="form-control" value="<?= htmlspecialchars($settings['LON']) ?>">
                <label>Panel Area (m²)</label>
                <input type="number" name="PANEL_AREA" class="form-control" value="<?= htmlspecialchars($settings['PANEL_AREA']) ?>">
                <label>Efficiency (%)</label>
                <input type="number" name="EFFICIENCY" class="form-control" value="<?= htmlspecialchars($settings['EFFICIENCY']) ?>">
            </div>

            <br>
            <h5>Loxone Settings</h5>
            <div class="form-group">
                <label>IP-address</label>
                <input type="text" name="loxone_ipaddress" class="form-control" value="<?= htmlspecialchars($settings['loxone_ip']) ?>">
                <label>Username</label>
                <input type="password" name="loxone_username" class="form-control" value="<?= htmlspecialchars($settings['loxone_username']) ?>">
                <label>Password</label>
                <input type="password" name="loxone_password" class="form-control" value="<?= htmlspecialchars($settings['loxone_password']) ?>">
                <div class="text-center mt-4">
                    <button type="submit" class="btn btn-primary px-5">Save Settings</button>
                </div>
            </div>
        </form>
    </div>
</div>

<?php LBWeb::lbfooter(); ?>
