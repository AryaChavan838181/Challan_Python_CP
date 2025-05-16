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
    $error = "Challan ID is required to generate receipt.";
}

// Define the HTML content for PDF
$html = '';
if ($challanDetails && empty($error)) {
    $html = '
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Payment Receipt</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
            }
            .container {
                width: 100%;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }
            .receipt-header {
                text-align: center;
                padding-bottom: 20px;
                border-bottom: 2px solid #333;
                margin-bottom: 20px;
            }
            .receipt-header h1 {
                margin: 0;
                color: #007bff;
            }
            .receipt-body {
                margin-bottom: 30px;
            }
            .receipt-body table {
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }
            .receipt-body table th, 
            .receipt-body table td {
                padding: 10px;
                border: 1px solid #ddd;
            }
            .receipt-body table th {
                background-color: #f8f9fa;
                text-align: left;
            }
            .receipt-footer {
                text-align: center;
                margin-top: 50px;
                font-size: 12px;
                color: #6c757d;
            }
            .paid-stamp {
                position: absolute;
                top: 180px;
                right: 40px;
                transform: rotate(25deg);
                font-size: 42px;
                color: green;
                border: 4px solid green;
                padding: 8px 12px;
                border-radius: 8px;
                opacity: 0.5;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="receipt-header">
                <h1>Traffic Challan Payment Receipt</h1>
                <p>Official Receipt for Challan Payment</p>
            </div>
            
            <div class="receipt-body">
                <div class="paid-stamp">PAID</div>
                
                <h3>Receipt Details</h3>
                <table>
                    <tr>
                        <th>Challan ID:</th>
                        <td>' . $challanDetails['challan_id'] . '</td>
                        <th>Payment Date:</th>
                        <td>' . date('d-M-Y h:i A', strtotime($challanDetails['payment_date'])) . '</td>
                    </tr>
                    <tr>
                        <th>Vehicle Number:</th>
                        <td>' . $challanDetails['numberplate'] . '</td>
                        <th>Transaction ID:</th>
                        <td>' . $challanDetails['transaction_id'] . '</td>
                    </tr>
                </table>
                
                <h3>Violation Details</h3>
                <table>
                    <tr>
                        <th>Violation Type:</th>
                        <td>' . $challanDetails['violation_type'] . '</td>
                    </tr>
                    <tr>
                        <th>Violation Date:</th>
                        <td>' . date('d-M-Y h:i A', strtotime($challanDetails['violation_date'])) . '</td>
                    </tr>
                    <tr>
                        <th>Location:</th>
                        <td>' . $challanDetails['location'] . '</td>
                    </tr>
                </table>
                
                <h3>Payment Details</h3>
                <table>
                    <tr>
                        <th>Amount Paid:</th>
                        <td>' . formatCurrency($challanDetails['amount']) . '</td>
                    </tr>
                    <tr>
                        <th>Payment Status:</th>
                        <td><strong>PAID</strong></td>
                    </tr>
                </table>
                
                <h3>Vehicle Owner Details</h3>
                <table>
                    <tr>
                        <th>Name:</th>
                        <td>' . $challanDetails['owner_name'] . '</td>
                    </tr>
                    <tr>
                        <th>Email:</th>
                        <td>' . $challanDetails['email'] . '</td>
                    </tr>
                    <tr>
                        <th>Phone:</th>
                        <td>' . $challanDetails['phone'] . '</td>
                    </tr>
                </table>
            </div>
            
            <div class="receipt-footer">
                <p>This is an electronically generated receipt and does not require a physical signature.</p>
                <p>For any queries, please contact the Traffic Police Department.</p>
                <p>&copy; ' . date('Y') . ' Traffic Challan Payment System. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    ';
}

// Check if we should generate PDF or display the HTML page
$generate_pdf = isset($_GET['pdf']) && $_GET['pdf'] == 1;

if ($generate_pdf && !empty($html)) {
    // You would typically use a library like TCPDF or MPDF to generate PDF
    // For now, we'll just show the HTML that would be converted to PDF
    
    // In a real implementation, you'd add code like this:
    /*
    require_once 'vendor/autoload.php';
    
    $mpdf = new \Mpdf\Mpdf();
    $mpdf->WriteHTML($html);
    
    // Output the PDF as download
    $mpdf->Output('challan_receipt_' . $challanId . '.pdf', 'D');
    exit;
    */
    
    // For this example, we'll just set a header to indicate this would be a PDF download
    header('Content-Type: text/html');
    echo $html;
    exit;
}
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Challan Receipt - Traffic Challan Payment System</title>
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
                <h2 class="mb-4 text-center">Challan Payment Receipt</h2>
                
                <?php if (!empty($error)): ?>
                    <div class="alert alert-danger">
                        <?php echo $error; ?>
                    </div>
                    <div class="text-center mb-4">
                        <a href="index.php" class="btn btn-primary">Go Back</a>
                    </div>
                <?php elseif ($challanDetails): ?>
                    <div class="card">
                        <div class="card-header bg-success text-white">
                            <h5 class="mb-0">Receipt for Challan #<?php echo $challanDetails['challan_id']; ?></h5>
                        </div>
                        <div class="card-body">
                            <div class="text-center mb-4">
                                <span class="badge bg-success p-2">PAID</span>
                            </div>
                            
                            <div class="row mb-4">
                                <div class="col-md-6">
                                    <h5>Receipt Details</h5>
                                    <table class="table table-bordered">
                                        <tr>
                                            <th>Challan ID</th>
                                            <td><?php echo $challanDetails['challan_id']; ?></td>
                                        </tr>
                                        <tr>
                                            <th>Vehicle Number</th>
                                            <td><?php echo $challanDetails['numberplate']; ?></td>
                                        </tr>
                                        <tr>
                                            <th>Payment Date</th>
                                            <td><?php echo date('d-M-Y h:i A', strtotime($challanDetails['payment_date'])); ?></td>
                                        </tr>
                                        <tr>
                                            <th>Transaction ID</th>
                                            <td><?php echo $challanDetails['transaction_id']; ?></td>
                                        </tr>
                                    </table>
                                </div>
                                <div class="col-md-6">
                                    <h5>Violation Details</h5>
                                    <table class="table table-bordered">
                                        <tr>
                                            <th>Type</th>
                                            <td><?php echo $challanDetails['violation_type']; ?></td>
                                        </tr>
                                        <tr>
                                            <th>Date</th>
                                            <td><?php echo date('d-M-Y h:i A', strtotime($challanDetails['violation_date'])); ?></td>
                                        </tr>
                                        <tr>
                                            <th>Location</th>
                                            <td><?php echo $challanDetails['location']; ?></td>
                                        </tr>
                                        <tr>
                                            <th>Amount Paid</th>
                                            <td><strong><?php echo formatCurrency($challanDetails['amount']); ?></strong></td>
                                        </tr>
                                    </table>
                                </div>
                            </div>
                            
                            <div class="text-center">
                                <a href="receipt.php?challan=<?php echo $challanDetails['challan_id']; ?>&pdf=1" class="btn btn-primary" target="_blank">
                                    <i class="fas fa-download me-2"></i> Download PDF Receipt
                                </a>
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
