<?php
// Database Configuration

// Hostinger MySQL Database credentials
$db_host = 'localhost';      // Usually 'localhost' for Hostinger
$db_name = 'traffic_challan'; // Database name
$db_user = 'username';       // Database username - replace with your actual username
$db_pass = 'password';       // Database password - replace with your actual password

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
$email_api_url = "https://thegroup11.com/api/sendmail";
$email_api_key = "dGh1Z3JvdXAxMQ=="; // Replace with your actual API key

// Site Configuration
$site_name = "Traffic Challan Payment System";
$site_url = "https://yourwebsite.com"; // Replace with your actual website URL
?>
