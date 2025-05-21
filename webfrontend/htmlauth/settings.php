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
    'mqtt_topic_logs' => 'home/energy/logs',
    'mqtt_topic_loxone'=> 'home/loxone/logs'
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
    echo '<div class="alert alert-success text-center">Settings saved successfully.</div>';
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
                <label>Topic - Logs</label>
                <input type="text" name="mqtt_topic_logs" class="form-control" value="<?= htmlspecialchars($settings['mqtt_topic_logs']) ?>">
            </div>
            <div class="form-group">
                <label>Topic - Loxone Logs</label>
                <input type="text" name="mqtt_topic_loxone" class="form-control" value="<?= htmlspecialchars($settings['mqtt_topic_loxone']) ?>">
            </div>

            <!-- <h5 class="mt-4">InfluxDB Settings</h5>
            <div class="form-group">
                <label>Influx URL</label>
                <input type="text" name="influx_url" class="form-control" value="<?= htmlspecialchars($settings['influx_url']) ?>">
            </div>
            <div class="form-group">
                <label>Influx Org</label>
                <input type="text" name="influx_org" class="form-control" value="<?= htmlspecialchars($settings['influx_org']) ?>">
            </div>
            <div class="form-group">
                <label>Influx Bucket</label>
                <input type="text" name="influx_bucket" class="form-control" value="<?= htmlspecialchars($settings['influx_bucket']) ?>">
            </div>
            <div class="form-group">
                <label>Token File Path</label>
                <input type="text" name="token_file" class="form-control" value="<?= htmlspecialchars($settings['token_file']) ?>">
            </div>

            <h5 class="mt-4">Other</h5>
            <div class="form-group">
                <label>Model File</label>
                <input type="text" name="model_file" class="form-control" value="<?= htmlspecialchars($settings['model_file']) ?>">
            </div> -->

            <div class="text-center">
                <button type="submit" class="btn btn-primary px-5">Save Settings</button>
            </div>
        </form>
    </div>
</div>

<?php LBWeb::lbfooter(); ?>
