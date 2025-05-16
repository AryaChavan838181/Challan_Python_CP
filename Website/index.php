<?php
// Start session for potential user login functionality
session_start();
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Traffic Challan Payment System</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="css/style.css">
</head>
<body>
    <!-- Navigation -->
    <?php include 'includes/header.php'; ?>

    <!-- Main Content -->
    <div class="container my-5">
        <div class="row justify-content-center">
            <div class="col-md-8 text-center">
                <h1 class="mb-4">Traffic Violation Challan System</h1>
                <p class="lead">Check and pay your traffic violation challan online</p>
            </div>
        </div>

        <div class="row justify-content-center mt-4">
            <div class="col-md-6">
                <div class="card shadow">
                    <div class="card-body">
                        <h5 class="card-title text-center mb-4">Challan Lookup</h5>
                        <form action="check_challan.php" method="POST">
                            <div class="mb-3">
                                <label for="challanId" class="form-label">Challan Number</label>
                                <input type="text" class="form-control" id="challanId" name="challanId" placeholder="Enter your challan number" required>
                            </div>
                            <button type="submit" class="btn btn-primary w-100">Check Challan Status</button>
                        </form>
                        <hr>
                        <h5 class="text-center mb-4">OR</h5>
                        <form action="check_challan.php" method="POST">
                            <div class="mb-3">
                                <label for="vehicleNumber" class="form-label">Vehicle Number</label>
                                <input type="text" class="form-control" id="vehicleNumber" name="vehicleNumber" placeholder="Enter your vehicle number" required>
                            </div>
                            <button type="submit" class="btn btn-primary w-100">Find Challans</button>
                        </form>
                    </div>
                </div>
            </div>
        </div>

        <div class="row mt-5">
            <div class="col-md-4">
                <div class="card text-center mb-4">
                    <div class="card-body">
                        <h5 class="card-title">Check Challan</h5>
                        <p class="card-text">Enter your challan number or vehicle number to check the status.</p>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card text-center mb-4">
                    <div class="card-body">
                        <h5 class="card-title">Pay Online</h5>
                        <p class="card-text">Pay your challan securely using our online payment options.</p>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card text-center mb-4">
                    <div class="card-body">
                        <h5 class="card-title">Download Receipt</h5>
                        <p class="card-text">Download receipt after successful payment of your challan.</p>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Footer -->
    <?php include 'includes/footer.php'; ?>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
    <script src="js/script.js"></script>
</body>
</html>
