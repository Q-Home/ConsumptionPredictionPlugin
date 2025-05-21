<?php
require_once "loxberry_web.php";
require_once "loxberry_system.php";

$L = LBSystem::readlanguage("language.ini");
$template_title = "Consumption Prediction";
$helplink = "http://www.loxwiki.eu:80/x/2wzL";
$helptemplate = "help.html";

// Navigation
// Navigation
$navbar[1]['Name'] = 'Home';
$navbar[1]['URL'] = 'index.php';
$navbar[2]['active'] = true;
$navbar[2]['Name'] = 'Consumption';
$navbar[2]['URL'] = 'consumption.php';
$navbar[3]['Name'] = 'Predictions';
$navbar[3]['URL'] = 'prediction.php';
$navbar[4]['Name'] = 'Settings';
$navbar[4]['URL'] = 'settings.php';


LBWeb::lbheader($template_title, $helplink, $helptemplate);

$dbPath = '/opt/loxberry/data/plugins/consumption_prediction/energy_data.sqlite';
$db_ok = file_exists($dbPath);
?>

<link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
<style>
    table {
        width: 100%;
        margin-top: 20px;
        table-layout: fixed;
    }

    th, td {
        text-align: center;
        padding: 10px;
        border: 1px solid #dee2e6;
        word-wrap: break-word;
    }

    th {
        background-color: #f8f9fa;
    }
</style>

<div class="container mt-4">
    <div class="row">
        <div class="col-12">
            <?php if ($db_ok): ?>
                <div class="table-responsive">
                    <h3 class="mb-4">Energy Predictions</h3>
                    <table class="table table-striped table-bordered w-100">
                        <thead><tr><th>Datetime</th><th>Predicted kWh</th></tr></thead>
                        <tbody>
                            <?php
                            try {
                                $pdo = new PDO("sqlite:$dbPath");
                                $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

                                $stmt = $pdo->query("SELECT datetime, predicted_kwh FROM predictions ORDER BY datetime ASC");

                                while ($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
                                    $dt = new DateTime($row['datetime']);
                                    $datetime = $dt->format('d-m-y H:i'); // Format: dd-mm-yy HH:MM
                                    $kwh = htmlspecialchars($row['predicted_kwh']);
                                    echo "<tr><td>$datetime</td><td>$kwh</td></tr>";
                                }
                            } catch (PDOException $e) {
                                echo '<tr><td colspan="2" class="text-danger">Database error: ' . htmlspecialchars($e->getMessage()) . '</td></tr>';
                            }
                            ?>
                        </tbody>
                    </table>
                </div>
            <?php else: ?>
                <div class="alert alert-warning mt-3">No data available – database file not found.</div>
            <?php endif; ?>
        </div>
    </div>
</div>
<?php LBWeb::lbfooter(); ?>