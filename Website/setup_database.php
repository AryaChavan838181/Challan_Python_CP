<?php
/**
 * Database setup script for Traffic Challan System
 * This script creates the necessary tables in the database
 */

// Include the database configuration
require_once 'includes/config.php';

// Set up the database tables
$tables = [];

// Table for vehicle owners
$tables[] = "
CREATE TABLE IF NOT EXISTS vehicle_owners (
    id INT(11) NOT NULL AUTO_INCREMENT,
    numberplate VARCHAR(20) NOT NULL,
    owner_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY (numberplate)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
";

// Table for violations (challans)
$tables[] = "
CREATE TABLE IF NOT EXISTS violations (
    id INT(11) NOT NULL AUTO_INCREMENT,
    challan_id VARCHAR(50) NOT NULL,
    numberplate VARCHAR(20) NOT NULL,
    violation_date DATETIME NOT NULL,
    location VARCHAR(255) NOT NULL,
    violation_type VARCHAR(100) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    status ENUM('paid', 'unpaid', 'pending') NOT NULL DEFAULT 'unpaid',
    image_path VARCHAR(255) NULL,
    transaction_id VARCHAR(100) NULL,
    payment_date DATETIME NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY (challan_id),
    KEY (numberplate)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
";

// Table for admin users
$tables[] = "
CREATE TABLE IF NOT EXISTS admin_users (
    id INT(11) NOT NULL AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL,
    password VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    role ENUM('admin', 'operator') NOT NULL DEFAULT 'operator',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY (username),
    UNIQUE KEY (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
";

// Table for activity log
$tables[] = "
CREATE TABLE IF NOT EXISTS activity_log (
    id INT(11) NOT NULL AUTO_INCREMENT,
    action VARCHAR(100) NOT NULL,
    details TEXT,
    user_id INT(11) NULL,
    ip_address VARCHAR(45) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
";

// Execute each table creation query
$success = true;
$errors = [];

foreach ($tables as $table_sql) {
    try {
        $conn->exec($table_sql);
    } catch (PDOException $e) {
        $success = false;
        $errors[] = $e->getMessage();
    }
}

// Insert default admin user if none exists
$admin_username = getenv('ADMIN_USERNAME') ?: 'admin';
$admin_password = getenv('ADMIN_PASSWORD') ?: 'admin123';

$default_admin_sql = "
INSERT INTO admin_users (username, password, name, email, role)
SELECT '$admin_username', '" . password_hash($admin_password, PASSWORD_DEFAULT) . "', 'Administrator', 'admin@example.com', 'admin'
WHERE NOT EXISTS (SELECT 1 FROM admin_users WHERE username = '$admin_username');
";

try {
    $conn->exec($default_admin_sql);
} catch (PDOException $e) {
    $success = false;
    $errors[] = "Failed to create default admin user: " . $e->getMessage();
}

// Insert sample data (for testing purposes only)
$sample_data = isset($_GET['sample_data']) && $_GET['sample_data'] == '1';

if ($sample_data) {
    // Sample vehicle owners
    $sample_owners = [
        ['MH01AB1234', 'John Doe', 'john@example.com', '9876543210', 'Mumbai, Maharashtra'],
        ['KA02CD5678', 'Jane Smith', 'jane@example.com', '9876543211', 'Bangalore, Karnataka'],
        ['DL03EF9012', 'Bob Johnson', 'bob@example.com', '9876543212', 'Delhi'],
        ['TN04GH3456', 'Alice Brown', 'alice@example.com', '9876543213', 'Chennai, Tamil Nadu'],
        ['GJ05IJ7890', 'Charlie Wilson', 'charlie@example.com', '9876543214', 'Ahmedabad, Gujarat']
    ];
    
    $owner_stmt = $conn->prepare("
        INSERT INTO vehicle_owners (numberplate, owner_name, email, phone, address)
        VALUES (:numberplate, :owner_name, :email, :phone, :address)
        ON DUPLICATE KEY UPDATE
        owner_name = VALUES(owner_name),
        email = VALUES(email),
        phone = VALUES(phone),
        address = VALUES(address)
    ");
    
    foreach ($sample_owners as $owner) {
        try {
            $owner_stmt->bindParam(':numberplate', $owner[0]);
            $owner_stmt->bindParam(':owner_name', $owner[1]);
            $owner_stmt->bindParam(':email', $owner[2]);
            $owner_stmt->bindParam(':phone', $owner[3]);
            $owner_stmt->bindParam(':address', $owner[4]);
            $owner_stmt->execute();
        } catch (PDOException $e) {
            $errors[] = "Failed to insert sample owner data: " . $e->getMessage();
        }
    }
    
    // Sample violations
    $violation_types = ['Red Light Violation', 'Speeding', 'No Parking', 'Wrong Side Driving', 'No Helmet'];
    $locations = ['Main Street Junction', 'Highway Toll Plaza', 'City Center', 'Railway Station Road', 'Market Area'];
    $statuses = ['paid', 'unpaid', 'pending'];
    
    $violation_stmt = $conn->prepare("
        INSERT INTO violations (challan_id, numberplate, violation_date, location, violation_type, amount, status)
        VALUES (:challan_id, :numberplate, :violation_date, :location, :violation_type, :amount, :status)
        ON DUPLICATE KEY UPDATE
        challan_id = VALUES(challan_id)
    ");
    
    for ($i = 1; $i <= 10; $i++) {
        try {
            $challan_id = 'SAMPLE-' . str_pad($i, 6, '0', STR_PAD_LEFT);
            $numberplate = $sample_owners[array_rand($sample_owners)][0];
            $violation_date = date('Y-m-d H:i:s', strtotime('-' . rand(1, 30) . ' days'));
            $location = $locations[array_rand($locations)];
            $violation_type = $violation_types[array_rand($violation_types)];
            $amount = rand(500, 2000);
            $status = $statuses[array_rand($statuses)];
            
            $violation_stmt->bindParam(':challan_id', $challan_id);
            $violation_stmt->bindParam(':numberplate', $numberplate);
            $violation_stmt->bindParam(':violation_date', $violation_date);
            $violation_stmt->bindParam(':location', $location);
            $violation_stmt->bindParam(':violation_type', $violation_type);
            $violation_stmt->bindParam(':amount', $amount);
            $violation_stmt->bindParam(':status', $status);
            
            $violation_stmt->execute();
            
            // Add payment date and transaction ID for paid challans
            if ($status == 'paid') {
                $payment_date = date('Y-m-d H:i:s', strtotime($violation_date . ' +' . rand(1, 5) . ' days'));
                $transaction_id = 'TXN' . rand(100000, 999999);
                
                $update_stmt = $conn->prepare("
                    UPDATE violations 
                    SET payment_date = :payment_date, transaction_id = :transaction_id 
                    WHERE challan_id = :challan_id
                ");
                
                $update_stmt->bindParam(':payment_date', $payment_date);
                $update_stmt->bindParam(':transaction_id', $transaction_id);
                $update_stmt->bindParam(':challan_id', $challan_id);
                
                $update_stmt->execute();
            }
        } catch (PDOException $e) {
            $errors[] = "Failed to insert sample violation data: " . $e->getMessage();
        }
    }
}

// Display result
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Database Setup - Traffic Challan System</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container my-5">
        <div class="row justify-content-center">
            <div class="col-md-8">
                <div class="card">
                    <div class="card-header bg-primary text-white">
                        <h2 class="mb-0">Database Setup</h2>
                    </div>
                    <div class="card-body">
                        <?php if ($success && empty($errors)): ?>
                            <div class="alert alert-success">
                                <h4>Setup Completed Successfully!</h4>
                                <p>All the required tables have been created in the database.</p>
                                <?php if ($sample_data): ?>
                                    <p>Sample data has been inserted for testing purposes.</p>
                                <?php endif; ?>
                            </div>
                            <div>
                                <h5>Created Tables:</h5>
                                <ul>
                                    <li>vehicle_owners - Stores information about vehicle owners</li>
                                    <li>violations - Stores challan and violation details</li>
                                    <li>admin_users - Stores admin user accounts</li>
                                    <li>activity_log - Logs system activities</li>
                                </ul>
                            </div>
                            <div>
                                <h5>Default Admin User:</h5>
                                <ul>
                                    <li>Username: admin</li>
                                    <li>Password: admin123</li>
                                </ul>
                                <p class="text-danger">Please change the default password after first login!</p>
                            </div>
                        <?php else: ?>
                            <div class="alert alert-danger">
                                <h4>Setup Failed!</h4>
                                <p>There were errors during the setup process:</p>
                                <ul>
                                    <?php foreach ($errors as $error): ?>
                                        <li><?php echo $error; ?></li>
                                    <?php endforeach; ?>
                                </ul>
                            </div>
                        <?php endif; ?>
                        
                        <div class="mt-4 text-center">
                            <a href="index.php" class="btn btn-primary">Go to Homepage</a>
                            <?php if ($success && empty($errors) && !$sample_data): ?>
                                <a href="setup_database.php?sample_data=1" class="btn btn-outline-secondary">Add Sample Data</a>
                            <?php endif; ?>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
