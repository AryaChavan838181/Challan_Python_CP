<?php
// Include the configuration file
require_once 'config.php';

/**
 * Send email using the provided API
 * 
 * @param string $to Recipient email address
 * @param string $subject Email subject
 * @param string $message Email body content
 * @return bool True if email sent successfully, false otherwise
 */
function sendEmail($to, $subject, $message) {
    global $email_api_url, $email_api_key;
    
    // Build API URL with query parameters
    $url = $email_api_url . "?api_key=" . urlencode($email_api_key) .
           "&to=" . urlencode($to) .
           "&subject=" . urlencode($subject) .
           "&message=" . urlencode($message);
    
    // Initialize cURL session
    $ch = curl_init();
    
    // Set cURL options
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_TIMEOUT, 30);
    
    // Execute cURL session and get the response
    $response = curl_exec($ch);
    
    // Check for errors
    if(curl_errno($ch)) {
        error_log('Email sending failed: ' . curl_error($ch));
        curl_close($ch);
        return false;
    }
    
    // Close cURL session
    curl_close($ch);
    
    // Process the API response
    $result = json_decode($response, true);
    
    // Check if email was sent successfully
    if(isset($result['success']) && $result['success'] === true) {
        return true;
    } else {
        error_log('Email API error: ' . ($result['message'] ?? 'Unknown error'));
        return false;
    }
}

/**
 * Generate a unique challan ID
 * 
 * @return string Unique challan ID
 */
function generateChallanId() {
    // Generate a random string with current timestamp to ensure uniqueness
    $timestamp = time();
    $random = mt_rand(1000, 9999);
    
    // Format: CHN-YYYYMMDD-TIMESTAMP-RANDOM
    $challanId = 'CHN-' . date('Ymd') . '-' . $timestamp . '-' . $random;
    
    return $challanId;
}

/**
 * Sanitize user input to prevent XSS attacks
 * 
 * @param string $data User input data
 * @return string Sanitized data
 */
function sanitizeInput($data) {
    $data = trim($data);
    $data = stripslashes($data);
    $data = htmlspecialchars($data);
    return $data;
}

/**
 * Format currency amounts
 * 
 * @param float $amount Amount to format
 * @return string Formatted amount
 */
function formatCurrency($amount) {
    return '₹ ' . number_format($amount, 2);
}

/**
 * Get challan details by challan ID
 * 
 * @param string $challanId The challan ID to look up
 * @return array|false Challan details array or false if not found
 */
function getChallanById($challanId) {
    global $conn;
    
    try {
        $stmt = $conn->prepare("SELECT v.*, o.owner_name, o.email, o.phone 
                                FROM violations v 
                                JOIN vehicle_owners o ON v.numberplate = o.numberplate 
                                WHERE v.challan_id = :challanId");
        $stmt->bindParam(':challanId', $challanId);
        $stmt->execute();
        
        $result = $stmt->fetch(PDO::FETCH_ASSOC);
        
        if($result) {
            return $result;
        } else {
            return false;
        }
    } catch(PDOException $e) {
        error_log("Error fetching challan: " . $e->getMessage());
        return false;
    }
}

/**
 * Get all challans for a vehicle number
 * 
 * @param string $vehicleNumber The vehicle number to look up
 * @return array Array of challans or empty array if none found
 */
function getChallansByVehicleNumber($vehicleNumber) {
    global $conn;
    
    try {
        $stmt = $conn->prepare("SELECT v.*, o.owner_name, o.email, o.phone 
                                FROM violations v 
                                JOIN vehicle_owners o ON v.numberplate = o.numberplate 
                                WHERE v.numberplate = :vehicleNumber 
                                ORDER BY v.violation_date DESC");
        $stmt->bindParam(':vehicleNumber', $vehicleNumber);
        $stmt->execute();
        
        return $stmt->fetchAll(PDO::FETCH_ASSOC);
    } catch(PDOException $e) {
        error_log("Error fetching challans: " . $e->getMessage());
        return [];
    }
}

/**
 * Update challan status after payment
 * 
 * @param string $challanId The challan ID to update
 * @param string $status New status ('paid', 'pending', 'failed')
 * @param string $transactionId Payment transaction ID (optional)
 * @return bool True if updated successfully, false otherwise
 */
function updateChallanStatus($challanId, $status, $transactionId = null) {
    global $conn;
    
    try {
        $sql = "UPDATE violations SET status = :status";
        
        if($transactionId) {
            $sql .= ", transaction_id = :transactionId, payment_date = NOW()";
        }
        
        $sql .= " WHERE challan_id = :challanId";
        
        $stmt = $conn->prepare($sql);
        $stmt->bindParam(':status', $status);
        $stmt->bindParam(':challanId', $challanId);
        
        if($transactionId) {
            $stmt->bindParam(':transactionId', $transactionId);
        }
        
        return $stmt->execute();
    } catch(PDOException $e) {
        error_log("Error updating challan status: " . $e->getMessage());
        return false;
    }
}

/**
 * Generate Google Pay QR code for payment
 * 
 * @param string $upiId UPI ID to receive payment
 * @param float $amount Payment amount
 * @param string $challanId Challan ID as reference
 * @return string UPI payment link
 */
function generateUpiLink($upiId, $amount, $challanId) {
    $upiLink = "upi://pay?pa=" . urlencode($upiId) .
               "&pn=" . urlencode("Traffic Challan Payment") .
               "&am=" . urlencode($amount) .
               "&cu=INR" .
               "&tn=" . urlencode("Challan Payment: " . $challanId);
    
    return $upiLink;
}

/**
 * Log system activities
 * 
 * @param string $action Action performed
 * @param string $details Additional details
 * @param string $userId User who performed the action (optional)
 * @return void
 */
function logActivity($action, $details, $userId = null) {
    global $conn;
    
    try {
        $stmt = $conn->prepare("INSERT INTO activity_log (action, details, user_id, ip_address) 
                               VALUES (:action, :details, :userId, :ip)");
        $stmt->bindParam(':action', $action);
        $stmt->bindParam(':details', $details);
        $stmt->bindParam(':userId', $userId);
        
        $ip = $_SERVER['REMOTE_ADDR'] ?? 'Unknown';
        $stmt->bindParam(':ip', $ip);
        
        $stmt->execute();
    } catch(PDOException $e) {
        error_log("Error logging activity: " . $e->getMessage());
    }
}
?>
