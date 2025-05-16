<?php
// Start session
session_start();

// Include functions and database connection
require_once 'includes/functions.php';

// Initialize variables
$challanDetails = null;
$error = '';

// Check if challan ID is provided
if (isset($_GET['challan']) && !empty($_GET['challan'])) {
    // Sanitize input
    $challanId = sanitizeInput($_GET['challan']);
    
    // Get challan details
    $challanDetails = getChallanById($challanId);
    
    if (!$challanDetails) {
        $error = "Invalid challan ID or challan not found.";
    } elseif ($challanDetails['status'] != 'paid') {
        $error = "This challan has not been paid yet.";
    }
} else {
    $error = "Challan ID is required to view payment details.";
}
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Payment Successful - Traffic Challan Payment System</title>
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
                <?php if (!empty($error)): ?>
                    <div class="alert alert-danger">
                        <?php echo $error; ?>
                    </div>
                    <div class="text-center mb-4">
                        <a href="index.php" class="btn btn-primary">Go Back</a>
                    </div>
                <?php elseif ($challanDetails): ?>
                    <div class="card">
                        <div class="card-body text-center">
                            <div class="mb-4">
                                <i class="fas fa-check-circle text-success" style="font-size: 5rem;"></i>
                                <h1 class="text-success mt-3">Payment Successful!</h1>
                                <p class="lead">Your challan payment has been received and processed successfully.</p>
                            </div>
                            
                            <div class="payment-success p-4 mb-4">
                                <div class="row mb-3">
                                    <div class="col-md-6 text-md-end"><strong>Challan ID:</strong></div>
                                    <div class="col-md-6 text-md-start"><?php echo $challanDetails['challan_id']; ?></div>
                                </div>
                                <div class="row mb-3">
                                    <div class="col-md-6 text-md-end"><strong>Vehicle Number:</strong></div>
                                    <div class="col-md-6 text-md-start"><?php echo $challanDetails['numberplate']; ?></div>
                                </div>
                                <div class="row mb-3">
                                    <div class="col-md-6 text-md-end"><strong>Amount Paid:</strong></div>
                                    <div class="col-md-6 text-md-start"><?php echo formatCurrency($challanDetails['amount']); ?></div>
                                </div>
                                <div class="row mb-3">
                                    <div class="col-md-6 text-md-end"><strong>Transaction ID:</strong></div>
                                    <div class="col-md-6 text-md-start"><?php echo $challanDetails['transaction_id']; ?></div>
                                </div>
                                <div class="row">
                                    <div class="col-md-6 text-md-end"><strong>Payment Date:</strong></div>
                                    <div class="col-md-6 text-md-start"><?php echo date('d-M-Y h:i A', strtotime($challanDetails['payment_date'])); ?></div>
                                </div>
                            </div>
                            
                            <div class="mt-4">
                                <a href="receipt.php?challan=<?php echo $challanDetails['challan_id']; ?>" class="btn btn-primary">Download Receipt</a>
                                <a href="index.php" class="btn btn-secondary ms-2">Back to Home</a>
                            </div>
                        </div>
                    </div>
                <?php endif; ?>
            </div>
        </div>
    </div>

    <!-- Footer -->
    <?php include 'includes/footer.php'; ?>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/js/all.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
    <script src="js/script.js"></script>
</body>
</html>
