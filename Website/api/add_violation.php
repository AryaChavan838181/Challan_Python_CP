<?php
/**
 * API endpoint for adding new violations
 * This will be called by the camera system when a red light violation is detected
 */

// Headers
header('Content-Type: application/json');

// Include database configuration and functions
require_once '../includes/functions.php';

// Set response array
$response = [
    'success' => false,
    'message' => '',
    'data' => null
];

// Check if this is a POST request
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    $response['message'] = 'Invalid request method. Only POST is allowed.';
    echo json_encode($response);
    exit;
}

// Get the API key from the request
$api_key = isset($_POST['api_key']) ? sanitizeInput($_POST['api_key']) : '';

// Validate API key (this should match the key used by your camera system)
$valid_api_key = 'your_camera_api_key'; // Change this to a secure API key

if ($api_key !== $valid_api_key) {
    $response['message'] = 'Invalid API key';
    echo json_encode($response);
    exit;
}

// Get and validate required parameters
$numberplate = isset($_POST['numberplate']) ? sanitizeInput($_POST['numberplate']) : '';
$location = isset($_POST['location']) ? sanitizeInput($_POST['location']) : '';
$violation_type = isset($_POST['violation_type']) ? sanitizeInput($_POST['violation_type']) : 'Red Light Violation';
$image_data = isset($_POST['image']) ? $_POST['image'] : ''; // Base64 encoded image

if (empty($numberplate)) {
    $response['message'] = 'Number plate is required';
    echo json_encode($response);
    exit;
}

if (empty($location)) {
    $response['message'] = 'Location is required';
    echo json_encode($response);
    exit;
}

// Generate a unique challan ID
$challan_id = generateChallanId();

// Set default amount for the violation
$amount = 1000; // Default amount for red light violation

// Check if the vehicle owner exists in database
try {
    $stmt = $conn->prepare("SELECT * FROM vehicle_owners WHERE numberplate = :numberplate");
    $stmt->bindParam(':numberplate', $numberplate);
    $stmt->execute();
    
    $owner = $stmt->fetch(PDO::FETCH_ASSOC);
    
    if (!$owner) {
        // Owner not found, we'll still create the violation but note that owner info is missing
        $response['message'] = 'Vehicle owner not found in database, violation recorded without owner details.';
    } else {
        $response['message'] = 'Violation recorded successfully.';
    }
    
    // Save the image if provided
    $image_path = null;
    if (!empty($image_data)) {
        $upload_dir = '../uploads/violations/';
        
        // Create directory if it doesn't exist
        if (!file_exists($upload_dir)) {
            mkdir($upload_dir, 0755, true);
        }
        
        // Decode and save the image
        $image_data = str_replace('data:image/jpeg;base64,', '', $image_data);
        $image_data = str_replace('data:image/png;base64,', '', $image_data);
        $image_data = str_replace(' ', '+', $image_data);
        $image_data = base64_decode($image_data);
        
        $image_filename = $challan_id . '.jpg';
        $image_path = $upload_dir . $image_filename;
        
        file_put_contents($image_path, $image_data);
        $image_path = 'uploads/violations/' . $image_filename;
    }
    
    // Insert violation record into database
    $stmt = $conn->prepare("INSERT INTO violations (challan_id, numberplate, violation_date, location, violation_type, amount, status, image_path) 
                            VALUES (:challan_id, :numberplate, NOW(), :location, :violation_type, :amount, 'unpaid', :image_path)");
    
    $stmt->bindParam(':challan_id', $challan_id);
    $stmt->bindParam(':numberplate', $numberplate);
    $stmt->bindParam(':location', $location);
    $stmt->bindParam(':violation_type', $violation_type);
    $stmt->bindParam(':amount', $amount);
    $stmt->bindParam(':image_path', $image_path);
    
    $stmt->execute();
    
    // Send email notification if owner information is available
    if ($owner && isset($owner['email']) && !empty($owner['email'])) {
        $to = $owner['email'];
        $subject = "Traffic Violation Notification - Challan #" . $challan_id;
        
        $message = "Dear " . $owner['owner_name'] . ",\n\n";
        $message .= "We regret to inform you that a traffic violation has been recorded for your vehicle with registration number " . $numberplate . ".\n\n";
        $message .= "Violation Details:\n";
        $message .= "Challan ID: " . $challan_id . "\n";
        $message .= "Violation Type: " . $violation_type . "\n";
        $message .= "Location: " . $location . "\n";
        $message .= "Date and Time: " . date('d-M-Y h:i A') . "\n";
        $message .= "Fine Amount: ₹" . number_format($amount, 2) . "\n\n";
        $message .= "You can view and pay your challan by visiting: " . $site_url . "/payment.php?challan=" . $challan_id . "\n\n";
        $message .= "If you believe this violation has been issued in error, please contact the Traffic Police Department.\n\n";
        $message .= "Thank you,\nTraffic Police Department";
        
        sendEmail($to, $subject, $message);
    }
    
    // Prepare successful response
    $response['success'] = true;
    $response['data'] = [
        'challan_id' => $challan_id,
        'numberplate' => $numberplate,
        'location' => $location,
        'violation_type' => $violation_type,
        'amount' => $amount,
        'date' => date('Y-m-d H:i:s'),
        'owner_found' => ($owner ? true : false)
    ];
    
} catch(PDOException $e) {
    $response['message'] = 'Database error: ' . $e->getMessage();
    error_log('API Error: ' . $e->getMessage());
}

// Output the response
echo json_encode($response);
?>
