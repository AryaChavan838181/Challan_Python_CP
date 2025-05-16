<?php
// Load environment variables from .env file
function loadEnv($path) {
    if (!file_exists($path)) {
        error_log("Environment file not found: $path");
        return false;
    }

    $lines = file($path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    foreach ($lines as $line) {
        // Skip comments
        if (strpos(trim($line), '#') === 0) {
            continue;
        }

        // Parse env variable
        list($name, $value) = explode('=', $line, 2);
        $name = trim($name);
        $value = trim($value);
        
        // Remove quotes if present
        if (preg_match('/^([\'"])(.*)\1$/', $value, $matches)) {
            $value = $matches[2];
        }
        
        // Set environment variable
        putenv("$name=$value");
        $_ENV[$name] = $value;
        $_SERVER[$name] = $value;
    }
    return true;
}

// Determine the root path and load .env file
$rootPath = dirname(dirname(__DIR__));
$dotEnvPath = $rootPath . '/.env';
loadEnv($dotEnvPath);

// Database Configuration
$db_host = getenv('DB_HOST') ?: 'localhost';
$db_name = getenv('DB_NAME') ?: 'traffic_challan';
$db_user = getenv('DB_USER') ?: 'username';
$db_pass = getenv('DB_PASS') ?: 'password';

// Create database connection
try {
    $conn = new PDO("mysql:host=$db_host;dbname=$db_name", $db_user, $db_pass);
    // Set the PDO error mode to exception
    $conn->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    // Set character set
    $conn->exec("SET NAMES 'utf8'");
} catch(PDOException $e) {
    // Log error instead of displaying it directly (for security)
    error_log("Connection failed: " . $e->getMessage());
    // Display user-friendly error
    die("Database connection failed. Please try again later.");
}

// Email API Configuration
$email_api_url = getenv('EMAIL_API_URL') ?: "https://thegroup11.com/api/sendmail";
$email_api_key = getenv('EMAIL_API_KEY') ?: "dGh1Z3JvdXAxMQ==";

// Site Configuration
$site_name = getenv('SITE_NAME') ?: "Traffic Challan Payment System";
$site_url = getenv('SITE_URL') ?: "https://yourwebsite.com";
?>
