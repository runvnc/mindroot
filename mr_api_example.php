<?php
require 'vendor/autoload.php';

use GuzzleHttp\Client;

$client = new Client(['base_uri' => 'http://localhost:8012', 'timeout' => 300]);

// Extract the first argument that is not --trace for instructions
$instructions = null;
if (count($argv) > 1) {
    foreach (array_slice($argv, 1) as $arg) {
        if ($arg !== '--trace') {
            $instructions = $arg;
            break;
        }
    }
}

if ($instructions === null) {
    die("Error: No instructions provided. Usage: php mr_api_example.php \"Your instructions here\" [--trace]\n");
}

try {
    $response = $client->post("/task/Assistant", [
        'query' => ['api_key' => getenv('MINDROOT_API_KEY') ],
        'json' => ['instructions' => $instructions ]
    ]);
    
    $result = json_decode($response->getBody(), true);

    if ($result['status'] == 'error') {
        echo "Error: " . $result['message'];
    } else {
      print_r($result['results']);

      if (in_array('--trace', $argv)) {
          echo "\n\n";
          print_r($result['full_results']);
      }
    }

} catch (Exception $e) {
    echo "Error: " . $e->getMessage() . "\n";
}
