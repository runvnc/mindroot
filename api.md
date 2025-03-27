# MindRoot API Documentation

## Overview

The MindRoot API allows programmatic interaction with AI agents without requiring a full chat session. This document describes the available endpoints and provides usage examples.

## Important Notes regarding the admin UI

1. To use an agent with the `/task` endpoint programmatically, you will need
to make sure the `task_result` command is enabled, and also do NOT enable
commands like `say` or `json_encoded_md` that will wait for the user to reply,
because if the agent chooses to use these commands then the task loop
will halt waiting for input before the agent has finished.

2. The System instructions in the Agent form Instructions field will remain
in effect when you use the `/task` endpoint, 
which specifies the `user` message as it's instructions
field. You do not need to repeat the System Message in an API call, and 
you should make sure there is no conflict in the instructions.
You can optionally remove the System message from the admin UI form
and instead specify all instructions in your API call, 
but this may not be as effective with some models as having some instructions
in the System message.


## Example: cURL

```bash
curl -X POST \
  "http://localhost:8012/task/Assistant?api_key=your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{"instructions":"What is the square root of 256? Show your work."}' \
  --max-time 300
`

## Authentication

All API requests require an API key, which should be included as a query parameter:

```
?api_key=your_api_key_here
```

Contact your system administrator to obtain an API key.

## Endpoints

### Run Task

Executes a task with an agent using the provided instructions.

**URL**: `/task/{agent_name}`

**Method**: `POST`

**Path Parameters**:
- `agent_name` (string, required): The name of the agent to run the task

**Query Parameters**:
- `api_key` (string, required): Your API key for authentication

**Request Body**:
```json
{
  "instructions": "Your instructions or prompt for the agent"
}
```
**Response**:
```json
{
  "status": "ok",
  "results": "The answer is 42",  // Final textual result or report
  "full_results": [...],  // Task trace including all commands output by the agent during the task
  "log_id": "xxxxxxxxx" Session ID of chat log
}
```

**Error Response**:
```json
{
  "status": "error",
  "message": "Error message"
}
```

**Notes**:
- This is a potentially long-running operation
- The server timeout is set to 5 minutes (300 seconds)
- For complex tasks, consider implementing client-side timeout handling

## Example: PHP Client

Here's a simple PHP client that demonstrates how to use the API:

```php
<?php
require 'vendor/autoload.php';

use GuzzleHttp\Client;

$client = new Client(['base_uri' => 'http://localhost:8012', 'timeout' => 300]);

// Get command line options
$options = getopt('', ['trace', 'help']);
$args = array_values(array_filter($argv, fn($arg) => !preg_match('/^--/', $arg) && $arg !== $argv[0]));

if (isset($options['help']) || empty($args)) {
    die("Usage: php mr_api_example.php \"Your instructions here\" [--trace] [--help]\n");
}

$instructions = $args[0];

try {
    $response = $client->post("/task/Assistant", [
        'query' => ['api_key' => getenv('MINDROOT_API_KEY')],
        'json' => ['instructions' => $instructions]
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
```

### Usage

```bash
# Set your API key
export MINDROOT_API_KEY=your_api_key_here

# Install dependencies
composer require guzzlehttp/guzzle

# Run a simple query
php mr_api_example.php "What is the square root of 256? Show your work."

# Run with trace flag to see detailed results
php mr_api_example.php "What is the square root of 256? Show your work." --trace

# Show help message
php mr_api_example.php --help
```

### Example Run and Output

## Simple JSON Example

```bash
[ /x/testmrapi ] > php mr_api_example.php --trace "Please extract any addresses in the following text into JSON format:  Hello, my name is John and I live at 52343 Main St. in Portland."

Output:

Array
(
    [0] => Array
        (
            [street] => 52343 Main St.
            [city] => Portland
        )

)

```

## Prime Numbers Example

Here's an example of running the script with a request to calculate prime numbers:

```bash
[ /x/testmrapi ] > php mr_api_example.php --trace "Please write a program to calculate the first 30 primes and give me just the program output."
```

**Output:**
```
[2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97, 101, 103, 107, 109, 113]

Array
(
    [0] => Array
        (
            [SYSTEM] => Note: tool command results follow, not user replies
            [cmd] => execute_command
            [args] => Array
                (
                    [cmd] => python -c "def is_prime(n):
    if n <= 1:
        return False
    if n <= 3:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True

def first_n_primes(n):
    primes = []
    num = 2
    while len(primes) < n:
        if is_prime(num):
            primes.append(num)
        num += 1
    return primes

# Get the first 30 primes
primes_30 = first_n_primes(30)
print(primes_30)"
                )
            [result] => [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97, 101, 103, 107, 109, 113]
        )
    [1] => Array
        (
            [SYSTEM] => Note: tool command results follow, not user replies
            [cmd] => task_result
            [args] => Array
                (
                    [output] => [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97, 101, 103, 107, 109, 113]
                )
            [result] => 
        )
)
```

``
