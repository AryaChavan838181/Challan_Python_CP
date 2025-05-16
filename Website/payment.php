<?php
// Start session
session_start();

// Include functions and database connection
require_once 'includes/functions.php';

// Initialize variables
$challanDetails = null;
$error = '';
$upiLink = '';
$upiId = getenv('UPI_ID') ?: 'your-upi-id@bank'; // Get from environment variables

// Check if challan ID is provided
if (isset($_GET['challan']) && !empty($_GET['challan'])) {
    // Sanitize input
    $challanId = sanitizeInput($_GET['challan']);
    
    // Get challan details
    $challanDetails = getChallanById($challanId);
    
    if (!$challanDetails) {
        $error = "Invalid challan ID or challan not found.";
    } elseif ($challanDetails['status'] == 'paid') {
        $error = "This challan has already been paid.";
    } else {
        // Generate UPI payment link
        $upiLink = generateUpiLink($upiId, $challanDetails['amount'], $challanId);
    }
} else {
    $error = "Challan ID is required to proceed with payment.";
}

// Handle payment confirmation
if ($_SERVER["REQUEST_METHOD"] == "POST" && isset($_POST['confirm_payment'])) {
    $challanId = sanitizeInput($_POST['challan_id']);
    $transactionId = sanitizeInput($_POST['transaction_id']);
    
    if (empty($transactionId)) {
        $error = "Please enter the transaction ID.";
    } else {
        // Update challan status
        $updated = updateChallanStatus($challanId, 'paid', $transactionId);
        
        if ($updated) {
            // Log the activity
            logActivity('payment', "Payment made for challan: $challanId, Transaction ID: $transactionId");
            
            // Redirect to success page
            header("Location: payment_success.php?challan=$challanId");
            exit;
        } else {
            $error = "Failed to process payment. Please try again.";
        }
    }
}
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pay Challan - Traffic Challan Payment System</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="css/style.css">
</head>
<body>
    <!-- Navigation -->
    <?php include 'includes/header.php'; ?>

    <!-- Main Content -->
    <div class="container my-5">
        <div class="row justify-content-center">
            <div class="col-md-8">
                <h2 class="mb-4 text-center">Pay Challan</h2>
                
                <?php if (!empty($error)): ?>
                    <div class="alert alert-danger">
                        <?php echo $error; ?>
                    </div>
                    <div class="text-center mb-4">
                        <a href="index.php" class="btn btn-primary">Go Back</a>
                    </div>
                <?php endif; ?>
                
                <?php if ($challanDetails && empty($error)): ?>
                    <div class="card mb-4">
                        <div class="card-header bg-primary text-white">
                            <h5 class="mb-0">Payment Details</h5>
                        </div>
                        <div class="card-body">
                            <div class="challan-details mb-4">
                                <div class="row">
                                    <div class="col-md-6">
                                        <p><strong>Challan ID:</strong> <?php echo $challanDetails['challan_id']; ?></p>
                                        <p><strong>Vehicle Number:</strong> <?php echo $challanDetails['numberplate']; ?></p>
                                        <p><strong>Violation Date:</strong> <?php echo date('d-M-Y h:i A', strtotime($challanDetails['violation_date'])); ?></p>
                                    </div>
                                    <div class="col-md-6">
                                        <p><strong>Violation Type:</strong> <?php echo $challanDetails['violation_type']; ?></p>
                                        <p><strong>Amount:</strong> <?php echo formatCurrency($challanDetails['amount']); ?></p>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="payment-instructions">
                                <h5>Payment Instructions</h5>
                                <ol>
                                    <li>Scan the QR code below using any UPI app (Google Pay, PhonePe, Paytm, etc.)</li>
                                    <li>Verify the payment details and amount</li>
                                    <li>Complete the payment</li>
                                    <li>Enter the UPI transaction ID below to confirm your payment</li>
                                </ol>
                            </div>
                            
                            <div class="qr-container">
                                <h5>Pay via UPI QR Code</h5>
                                <div class="qr-code">
                                    <!-- Generate QR code using Google Charts API -->
                                    <img src="https://chart.googleapis.com/chart?chs=250x250&cht=qr&chl=<?php echo urlencode($upiLink); ?>" alt="UPI QR Code">
                                </div>
                                <p class="mt-2">Amount: <strong><?php echo formatCurrency($challanDetails['amount']); ?></strong></p>
                                <p>UPI ID: <strong><?php echo $upiId; ?></strong></p>
                            </div>
                            
                            <div class="mt-4">
                                <form action="<?php echo htmlspecialchars($_SERVER["PHP_SELF"]); ?>" method="POST">
                                    <input type="hidden" name="challan_id" value="<?php echo $challanDetails['challan_id']; ?>">
                                    
                                    <div class="mb-3">
                                        <label for="transaction_id" class="form-label">Enter UPI Transaction ID</label>
                                        <input type="text" class="form-control" id="transaction_id" name="transaction_id" required>
                                        <div class="form-text">Enter the transaction ID received after completing the payment</div>
                                    </div>
                                    
                                    <div class="text-center">
                                        <button type="submit" name="confirm_payment" class="btn btn-success btn-lg">Confirm Payment</button>
                                    </div>
                                </form>
                            </div>
                        </div>
                    </div>
                <?php endif; ?>
            </div>
        </div>
    </div>

    <!-- Footer -->
    <?php include 'includes/footer.php'; ?>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
    <script src="js/script.js"></script>
</body>
</html>
