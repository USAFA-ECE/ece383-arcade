<?php
// --- Handle backend requests (when the user clicks a game) ---
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['game'])) {
    $game = escapeshellarg($_POST['game']); // sanitize for shell safety

    // Example command — replace this with your real one
    $output = shell_exec("openFPGALoader -b nexysVideo /bitstreams/$game");

    echo "Executed: $game\nOutput:\n$output";
    exit; // stop here so we don't send the HTML
}
?>

<!DOCTYPE html>
<html>
    <Body>
        <h1>List of Games</h1>
        <?php
            $gamesCSV = __DIR__ . '/bitstreams.csv'; 
            $games = [];

            if(($filePointer = fopen($gamesCSV, "r")) !== FALSE){
                $header = fgetcsv($filePointer);
                while(($row = fgetcsv($filePointer)) !== FALSE){
                    $games[] = $row;
                }
                fclose($filePointer);
            } else {
                echo "<p style='color:red;>'Unable to open CSV file.'</p>";
            }
        ?>

        <ul id=gameMenu>
            <?php
            foreach($games as $game){
                $name = htmlspecialchars($game[0]);
                $filename = urlencode($game[1]); // URL-safe
                echo "<li><a href='fpgaloader.php?name=$filename'>$name</a></li>";
            }
            ?>
        </ul>

        


    </Body>
    
</html>