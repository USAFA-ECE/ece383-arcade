<?php
if (!isset($_GET['name'])) {
    die("Error: no bitstream name provided.");
}

$gameFile = basename($_GET['name']); // sanitize
$bitstreamPath = __DIR__ . "/bitstreams/$gameFile"; // local path next to PHP file

if (!file_exists($bitstreamPath)) {
    die("Error: bitstream file not found at $bitstreamPath");
}

$cmd = escapeshellcmd("openFPGALoader -b nexysVideo $bitstreamPath");
$output = shell_exec($cmd . " 2>&1");

echo "<pre>Executed command:\n$cmd\n\nOutput:\n$output</pre>";
?>

