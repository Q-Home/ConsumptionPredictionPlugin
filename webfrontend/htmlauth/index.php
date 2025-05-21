<?php
require_once "loxberry_web.php";
require_once "loxberry_system.php";

$L = LBSystem::readlanguage("language.ini");
$template_title = "Consumption Prediction";
$helplink = "http://www.loxwiki.eu:80/x/2wzL";
$helptemplate = "help.html";

// Navigation
$navbar[1]['Name'] = 'Home';
$navbar[1]['URL'] = 'index.php';
$navbar[1]['active'] = true;
$navbar[2]['Name'] = 'Settings';
$navbar[2]['URL'] = 'settings.php';
$navbar[3]['Name'] = 'Logs';
$navbar[3]['URL'] = 'logs.php';

LBWeb::lbheader($template_title, $helplink, $helptemplate);

// Check InfluxDB status
function isInfluxDBRunning($host = 'http://loxberry:8086') {
    $url = rtrim($host, '/') . '/health';

    $ch = curl_init($url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_TIMEOUT, 2);
    curl_setopt($ch, CURLOPT_CONNECTTIMEOUT, 2);

    $response = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    return $httpCode === 200;
}

// Check Grafana status
function isGrafanaRunning($host = 'http://loxberry:3000') {
    $ch = curl_init($host);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_TIMEOUT, 2);
    curl_setopt($ch, CURLOPT_CONNECTTIMEOUT, 2);
    curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true); // Follow redirects
    curl_setopt($ch, CURLOPT_USERAGENT, "Mozilla/5.0"); // Some setups block empty user-agents

    $response = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    return $httpCode >= 200 && $httpCode < 400;
}

$influx_ok = isInfluxDBRunning();
$grafana_ok = isGrafanaRunning();
?>

<link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
<style>
    .status-box {
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #ccc;
        background-color: #f8f9fa;
        text-align: center;
        margin-bottom: 30px;
    }

    .status {
        padding: 12px;
        border-radius: 5px;
        font-weight: bold;
        font-size: 18px;
    }

    .status-ok {
        background-color: #d4edda;
        color: #155724;
    }

    .status-error {
        background-color: #f8d7da;
        color: #721c24;
    }

    .button-container {
        margin-bottom: 40px;
    }

    .btn-custom {
        min-width: 250px;
        font-size: 18px;
        padding: 14px 24px;
        margin: 0 auto;
        border-radius: 6px;
        display: inline-block;
    }
    .table td {
        padding: 12px !important; /* Reduce row spacing */
    }

</style>

<div class="container mt-5">
    <table class="table-borderless mx-auto table" style="width: 100%; max-width: 800px;">
        <!-- Row 1: InfluxDB and Grafana -->
        <tr>
            <td style="vertical-align: top; padding: 15px;">
                <div class="status-box text-center">
                    <h4 class="mb-2">InfluxDB Status</h4>
                    <div class="status <?= $influx_ok ? 'status-ok' : 'status-error' ?>">
                        <?= $influx_ok ? 'InfluxDB Found' : 'InfluxDB Not Found' ?>
                    </div>
                    <?php if ($influx_ok): ?>
                        <a href="http://loxberry:8086" target="_blank" class="btn btn-outline-primary mt-3">
                            Open InfluxDB
                        </a>
                    <?php endif; ?>
                </div>
            </td>
            <td style="vertical-align: top; padding: 15px;">
                <div class="status-box text-center">
                    <h4 class="mb-2">Grafana Status</h4>
                    <div class="status <?= $grafana_ok ? 'status-ok' : 'status-error' ?>">
                        <?= $grafana_ok ? 'Grafana Found' : 'Grafana Not Found' ?>
                    </div>
                    <?php if ($grafana_ok): ?>
                        <a href="http://loxberry:3000" target="_blank" class="btn btn-outline-primary mt-3">
                            Open Grafana
                        </a>
                    <?php endif; ?>
                </div>
            </td>
        </tr>

        <!-- Row 2: Train Model Button -->
        <tr>
            <td colspan="2" class="text-center" style="padding: 20px;">
                <button class="btn btn-primary btn-custom" onclick="runTrainModel()">Run Training Model</button>
            </td>
        </tr>

        <!-- Row 3: Prediction Button -->
        <tr>
            <td colspan="2" class="text-center" style="padding: 10px;">
                <button class="btn btn-success btn-custom" onclick="runPrediction()">Run Prediction</button>
            </td>
        </tr>
    </table>
</div>

<script>
    function runTrainModel() {
        var xhr = new XMLHttpRequest();
        xhr.open("GET", "run_script.php?script=train", true);
        xhr.onreadystatechange = function () {
            if (xhr.readyState == 4 && xhr.status == 200) {
                alert("Training model script executed successfully.");
            }
        };
        xhr.send();
    }

    function runPrediction() {
        var xhr = new XMLHttpRequest();
        xhr.open("GET", "run_script.php?script=predict", true);
        xhr.onreadystatechange = function () {
            if (xhr.readyState == 4 && xhr.status == 200) {
                alert("Prediction script executed successfully.");
            }
        };
        xhr.send();
    }
</script>

<?php LBWeb::lbfooter(); ?>
