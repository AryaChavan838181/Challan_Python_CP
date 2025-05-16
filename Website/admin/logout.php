<?php
// Start session
session_start();

// Include functions
require_once '../includes/functions.php';

// Log the logout activity if admin is logged in
if (isset($_SESSION['admin'])) {
    logActivity('logout', "Admin user logout: {$_SESSION['admin']['username']}", $_SESSION['admin']['id']);
}

// Destroy the session
session_destroy();

// Redirect to login page
header("Location: login.php");
exit;
?>
