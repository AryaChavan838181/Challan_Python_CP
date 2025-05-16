<?php
// Start session
session_start();

// Check if user is logged in
if (!isset($_SESSION['admin'])) {
    // Redirect to login page
    header("Location: login.php");
    exit;
}

// Include functions and database connection
require_once '../includes/functions.php';

// Get admin info from session
$admin = $_SESSION['admin'];

// Get dashboard statistics
try {
    // Total number of challans
    $stmt = $conn->query("SELECT COUNT(*) as total FROM violations");
    $total_challans = $stmt->fetch(PDO::FETCH_ASSOC)['total'];
    
    // Paid challans
    $stmt = $conn->query("SELECT COUNT(*) as paid FROM violations WHERE status = 'paid'");
    $paid_challans = $stmt->fetch(PDO::FETCH_ASSOC)['paid'];
    
    // Pending/unpaid challans
    $stmt = $conn->query("SELECT COUNT(*) as unpaid FROM violations WHERE status != 'paid'");
    $unpaid_challans = $stmt->fetch(PDO::FETCH_ASSOC)['unpaid'];
    
    // Total revenue collected
    $stmt = $conn->query("SELECT SUM(amount) as revenue FROM violations WHERE status = 'paid'");
    $total_revenue = $stmt->fetch(PDO::FETCH_ASSOC)['revenue'] ?: 0;
    
    // Recent challans
    $stmt = $conn->query("SELECT v.challan_id, v.numberplate, v.violation_date, v.violation_type, v.amount, v.status, o.owner_name 
                         FROM violations v 
                         LEFT JOIN vehicle_owners o ON v.numberplate = o.numberplate 
                         ORDER BY v.violation_date DESC LIMIT 10");
    $recent_challans = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
} catch(PDOException $e) {
    error_log("Dashboard error: " . $e->getMessage());
}
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Dashboard - Traffic Challan Payment System</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <link rel="stylesheet" href="../css/style.css">
</head>
<body>
    <div class="container-fluid">
        <div class="row">
            <!-- Sidebar -->
            <nav id="sidebar" class="col-md-3 col-lg-2 d-md-block bg-dark sidebar collapse">
                <div class="position-sticky pt-3">
                    <div class="text-center mb-4 text-white">
                        <h5>Admin Panel</h5>
                        <p>Welcome, <?php echo $admin['name']; ?></p>
                    </div>
                    <ul class="nav flex-column">
                        <li class="nav-item">
                            <a class="nav-link active text-white" href="dashboard.php">
                                <i class="fas fa-tachometer-alt me-2"></i>
                                Dashboard
                            </a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link text-white" href="violations.php">
                                <i class="fas fa-exclamation-triangle me-2"></i>
                                Violations
                            </a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link text-white" href="owners.php">
                                <i class="fas fa-users me-2"></i>
                                Vehicle Owners
                            </a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link text-white" href="reports.php">
                                <i class="fas fa-chart-bar me-2"></i>
                                Reports
                            </a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link text-white" href="settings.php">
                                <i class="fas fa-cog me-2"></i>
                                Settings
                            </a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link text-white" href="logout.php">
                                <i class="fas fa-sign-out-alt me-2"></i>
                                Logout
                            </a>
                        </li>
                    </ul>
                </div>
            </nav>

            <!-- Main Content -->
            <main class="col-md-9 ms-sm-auto col-lg-10 px-md-4">
                <div class="d-flex justify-content-between flex-wrap flex-md-nowrap align-items-center pt-3 pb-2 mb-3 border-bottom">
                    <h1 class="h2">Dashboard</h1>
                    <div class="btn-toolbar mb-2 mb-md-0">
                        <a href="../index.php" class="btn btn-sm btn-outline-secondary" target="_blank">
                            <i class="fas fa-external-link-alt me-2"></i>
                            View Website
                        </a>
                    </div>
                </div>

                <!-- Stats Cards -->
                <div class="row">
                    <div class="col-md-3 mb-4">
                        <div class="stats-card stats-card-primary p-3">
                            <div class="d-flex justify-content-between align-items-center">
                                <div>
                                    <h6 class="text-uppercase">Total Challans</h6>
                                    <h2 class="mb-0"><?php echo number_format($total_challans); ?></h2>
                                </div>
                                <div class="icon">
                                    <i class="fas fa-file-invoice fa-2x"></i>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3 mb-4">
                        <div class="stats-card stats-card-success p-3">
                            <div class="d-flex justify-content-between align-items-center">
                                <div>
                                    <h6 class="text-uppercase">Paid Challans</h6>
                                    <h2 class="mb-0"><?php echo number_format($paid_challans); ?></h2>
                                </div>
                                <div class="icon">
                                    <i class="fas fa-check-circle fa-2x"></i>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3 mb-4">
                        <div class="stats-card stats-card-danger p-3">
                            <div class="d-flex justify-content-between align-items-center">
                                <div>
                                    <h6 class="text-uppercase">Unpaid Challans</h6>
                                    <h2 class="mb-0"><?php echo number_format($unpaid_challans); ?></h2>
                                </div>
                                <div class="icon">
                                    <i class="fas fa-exclamation-circle fa-2x"></i>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3 mb-4">
                        <div class="stats-card stats-card-warning p-3">
                            <div class="d-flex justify-content-between align-items-center">
                                <div>
                                    <h6 class="text-uppercase">Total Revenue</h6>
                                    <h2 class="mb-0">₹<?php echo number_format($total_revenue); ?></h2>
                                </div>
                                <div class="icon">
                                    <i class="fas fa-rupee-sign fa-2x"></i>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Recent Challans -->
                <div class="row mt-4">
                    <div class="col-12">
                        <div class="card">
                            <div class="card-header">
                                <h5 class="mb-0">Recent Violations</h5>
                            </div>
                            <div class="card-body">
                                <div class="table-responsive">
                                    <table class="table table-striped table-hover">
                                        <thead>
                                            <tr>
                                                <th>Challan ID</th>
                                                <th>Vehicle Number</th>
                                                <th>Owner Name</th>
                                                <th>Violation Date</th>
                                                <th>Violation Type</th>
                                                <th>Amount</th>
                                                <th>Status</th>
                                                <th>Actions</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            <?php foreach ($recent_challans as $challan): ?>
                                            <tr>
                                                <td><?php echo $challan['challan_id']; ?></td>
                                                <td><?php echo $challan['numberplate']; ?></td>
                                                <td><?php echo $challan['owner_name'] ?? 'Unknown'; ?></td>
                                                <td><?php echo date('d-M-Y h:i A', strtotime($challan['violation_date'])); ?></td>
                                                <td><?php echo $challan['violation_type']; ?></td>
                                                <td>₹<?php echo number_format($challan['amount'], 2); ?></td>
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
                                                    <a href="view_challan.php?id=<?php echo $challan['challan_id']; ?>" class="btn btn-sm btn-info">
                                                        <i class="fas fa-eye"></i>
                                                    </a>
                                                    <a href="edit_challan.php?id=<?php echo $challan['challan_id']; ?>" class="btn btn-sm btn-primary">
                                                        <i class="fas fa-edit"></i>
                                                    </a>
                                                </td>
                                            </tr>
                                            <?php endforeach; ?>
                                        </tbody>
                                    </table>
                                </div>
                                <div class="text-end mt-3">
                                    <a href="violations.php" class="btn btn-primary">View All Challans</a>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/js/all.min.js"></script>
    <script src="../js/script.js"></script>
</body>
</html>
