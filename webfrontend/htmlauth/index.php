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
$navbar[2]['Name'] = 'Consumption';
$navbar[2]['URL'] = 'consumption.php';
$navbar[3]['Name'] = 'Predictions';
$navbar[3]['URL'] = 'prediction.php';

LBWeb::lbheader($template_title, $helplink, $helptemplate);

$dbPath = '/opt/loxberry/data/plugins/consumption_prediction/energy_data.sqlite';
$db_ok = file_exists($dbPath);
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
        margin: 10px;
        border-radius: 6px;
    }
</style>

<div class="container mt-5">
    <div class="col-lg-8 offset-lg-2">
        <!-- Status Box -->
        <div class="status-box text-center">
            <h4 class="mb-2">Prediction Database Status</h4>
            <div class="status <?= $db_ok ? 'status-ok' : 'status-error' ?>">
                <?= $db_ok ? 'Database Found' : 'Database Missing' ?>
            </div>
        </div>

        <!-- Buttons -->
        <div class="text-center button-container">
            <button class="btn btn-primary btn-custom" onclick="runTrainModel()">Run Training Model</button>
            <button class="btn btn-success btn-custom" onclick="runPrediction()">Run Prediction</button>
        </div>
    </div>
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
