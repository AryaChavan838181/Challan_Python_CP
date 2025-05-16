<?php
// Start session
session_start();

// Include functions and database connection
require_once 'includes/functions.php';

// Prepare variables
$error = '';
$challanDetails = null;
$challans = [];

// Check if form is submitted
if ($_SERVER["REQUEST_METHOD"] == "POST") {
    // Check if challan ID is provided
    if (isset($_POST['challanId']) && !empty($_POST['challanId'])) {
        // Sanitize input
        $challanId = sanitizeInput($_POST['challanId']);
        
        // Get challan details
        $challanDetails = getChallanById($challanId);
        
        if (!$challanDetails) {
            $error = "No challan found with the provided ID.";
        }
    }
    // Check if vehicle number is provided
    elseif (isset($_POST['vehicleNumber']) && !empty($_POST['vehicleNumber'])) {
        // Sanitize input
        $vehicleNumber = sanitizeInput($_POST['vehicleNumber']);
        
        // Get all challans for this vehicle
        $challans = getChallansByVehicleNumber($vehicleNumber);
        
        if (empty($challans)) {
            $error = "No challans found for the provided vehicle number.";
        }
    }
    else {
        $error = "Please provide either a challan ID or vehicle number.";
    }
}
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Challan Details - Traffic Challan Payment System</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="css/style.css">
</head>
<body>
    <!-- Navigation -->
    <?php include 'includes/header.php'; ?>

    <!-- Main Content -->
    <div class="container my-5">
        <div class="row">
            <div class="col-md-12">
                <h2 class="mb-4">Challan Details</h2>
                
                <?php if (!empty($error)): ?>
                    <div class="alert alert-danger">
                        <?php echo $error; ?>
                    </div>
                    <div class="text-center">
                        <a href="index.php" class="btn btn-primary">Go Back</a>
                    </div>
                <?php endif; ?>
                
                <?php if ($challanDetails): ?>
                    <!-- Single Challan Details -->
                    <div class="card mb-4">
                        <div class="card-header bg-primary text-white">
                            <h4 class="mb-0">Challan #<?php echo $challanDetails['challan_id']; ?></h4>
                        </div>
                        <div class="card-body">
                            <div class="row">
                                <div class="col-md-6">
                                    <h5>Violation Details</h5>
                                    <table class="table table-bordered">
                                        <tr>
                                            <th>Vehicle Number</th>
                                            <td><?php echo $challanDetails['numberplate']; ?></td>
                                        </tr>
                                        <tr>
                                            <th>Violation Date</th>
                                            <td><?php echo date('d-M-Y h:i A', strtotime($challanDetails['violation_date'])); ?></td>
                                        </tr>
                                        <tr>
                                            <th>Location</th>
                                            <td><?php echo $challanDetails['location']; ?></td>
                                        </tr>
                                        <tr>
                                            <th>Violation Type</th>
                                            <td><?php echo $challanDetails['violation_type']; ?></td>
                                        </tr>
                                        <tr>
                                            <th>Amount</th>
                                            <td><strong><?php echo formatCurrency($challanDetails['amount']); ?></strong></td>
                                        </tr>
                                        <tr>
                                            <th>Status</th>
                                            <td>
                                                <?php if ($challanDetails['status'] == 'paid'): ?>
                                                    <span class="badge bg-success">Paid</span>
                                                <?php elseif ($challanDetails['status'] == 'pending'): ?>
                                                    <span class="badge bg-warning">Pending</span>
                                                <?php else: ?>
                                                    <span class="badge bg-danger">Unpaid</span>
                                                <?php endif; ?>
                                            </td>
                                        </tr>
                                    </table>
                                </div>
                                <div class="col-md-6">
                                    <h5>Vehicle Owner Details</h5>
                                    <table class="table table-bordered">
                                        <tr>
                                            <th>Owner Name</th>
                                            <td><?php echo $challanDetails['owner_name']; ?></td>
                                        </tr>
                                        <tr>
                                            <th>Email</th>
                                            <td><?php echo $challanDetails['email']; ?></td>
                                        </tr>
                                        <tr>
                                            <th>Phone</th>
                                            <td><?php echo $challanDetails['phone']; ?></td>
                                        </tr>
                                    </table>
                                    
                                    <?php if ($challanDetails['status'] != 'paid'): ?>
                                        <div class="text-center mt-4">
                                            <a href="payment.php?challan=<?php echo $challanDetails['challan_id']; ?>" class="btn btn-success btn-lg">Pay Now</a>
                                        </div>
                                    <?php else: ?>
                                        <div class="text-center mt-4">
                                            <a href="receipt.php?challan=<?php echo $challanDetails['challan_id']; ?>" class="btn btn-info btn-lg">Download Receipt</a>
                                        </div>
                                    <?php endif; ?>
                                </div>
                            </div>
                        </div>
                    </div>

                <?php elseif (!empty($challans)): ?>
                    <!-- Multiple Challans List -->
                    <div class="table-responsive">
                        <table class="table table-striped table-hover">
                            <thead class="table-dark">
                                <tr>
                                    <th>Challan ID</th>
                                    <th>Violation Date</th>
                                    <th>Violation Type</th>
                                    <th>Amount</th>
                                    <th>Status</th>
                                    <th>Action</th>
                                </tr>
                            </thead>
                            <tbody>
                                <?php foreach ($challans as $challan): ?>
                                <tr>
                                    <td><?php echo $challan['challan_id']; ?></td>
                                    <td><?php echo date('d-M-Y h:i A', strtotime($challan['violation_date'])); ?></td>
                                    <td><?php echo $challan['violation_type']; ?></td>
                                    <td><?php echo formatCurrency($challan['amount']); ?></td>
                                    <td>
                                        <?php if ($challan['status'] == 'paid'): ?>
                                            <span class="badge bg-success">Paid</span>
                                        <?php elseif ($challan['status'] == 'pending'): ?>
                                            <span class="badge bg-warning">Pending</span>
                                        <?php else: ?>
                                            <span class="badge bg-danger">Unpaid</span>
                                        <?php endif; ?>
                                    </td>
                                    <td>
                                        <a href="check_challan.php" class="btn btn-sm btn-primary">View Details</a>
                                        
                                        <?php if ($challan['status'] != 'paid'): ?>
                                            <a href="payment.php?challan=<?php echo $challan['challan_id']; ?>" class="btn btn-sm btn-success">Pay</a>
                                        <?php else: ?>
                                            <a href="receipt.php?challan=<?php echo $challan['challan_id']; ?>" class="btn btn-sm btn-info">Receipt</a>
                                        <?php endif; ?>
                                    </td>
                                </tr>
                                <?php endforeach; ?>
                            </tbody>
                        </table>
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
