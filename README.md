# Traffic Challan Payment System

A comprehensive system for managing traffic violations, sending notifications to vehicle owners, and facilitating online payments.

## Project Overview

This project implements an automated traffic challan system that:

1. Captures traffic violations using cameras (red light violations)
2. Identifies vehicle number plates using image processing
3. Issues challans to vehicle owners
4. Sends email notifications to owners
5. Provides an online payment portal for challan payments
6. Maintains a database of violations and payments
7. Includes an admin dashboard for system management

## System Components

### 1. Camera System (Existing)
- Captures images when a vehicle violates traffic rules
- Uses image processing to extract vehicle number plate
- Sends the captured data to the server API

### 2. Website
- **Public Pages:**
  - Home page with challan lookup functionality
  - Challan details view page
  - Payment processing page using Google Pay QR
  - Payment receipt generation
  
- **Admin Panel:**
  - Dashboard with statistics
  - Violation management
  - Vehicle owner management
  - Reports and analytics

### 3. Database
- Vehicle owners information
- Traffic violations records
- Payment records
- Admin users

## Installation Instructions

### Prerequisites
- PHP 7.4 or higher
- MySQL database
- Web server (Apache/Nginx)
- Hostinger hosting account or similar

### Setup Steps

1. **Upload files to your hosting account:**
   - Upload all files in the `Website` folder to your hosting root directory

2. **Configure database connection:**
   - Edit `includes/config.php` with your database credentials:
     ```php
     $db_host = 'localhost';    // Your database host
     $db_name = 'your_db_name'; // Your database name
     $db_user = 'your_db_user'; // Your database username
     $db_pass = 'your_db_pass'; // Your database password
     ```

3. **Set up the database:**
   - Visit `https://your-domain.com/setup_database.php` in your browser
   - This script will create all the necessary tables
   - You can add sample data by clicking the "Add Sample Data" button

4. **Update email API configuration:**
   - Edit the email API URL and key in `includes/config.php`:
     ```php
     $email_api_url = "https://thegroup11.com/api/sendmail";
     $email_api_key = "dGh1Z3JvdXAxMQ=="; // Your actual API key
     ```

5. **Update UPI payment details:**
   - Edit your UPI ID in `payment.php` file:
     ```php
     $upiId = 'your-upi-id@bank'; // Replace with your actual UPI ID
     ```

6. **Configure API access for camera integration:**
   - Edit `api/add_violation.php` to set your camera API key:
     ```php
     $valid_api_key = 'your_camera_api_key'; // Change this to a secure API key
     ```

## Usage Instructions

### For Vehicle Owners
1. Receive email notification when a violation is detected
2. Click on the payment link in the email or visit the website
3. Enter challan ID or vehicle number to view challan details
4. Process payment using Google Pay by scanning the QR code
5. Enter transaction ID to confirm payment
6. Download receipt for future reference

### For Administrators
1. Log in to the admin panel using default credentials:
   - Username: admin
   - Password: admin123
2. View dashboard with violation statistics
3. Manage violations and vehicle owner information
4. Generate reports and track payment status

### For Camera Integration
To add a new violation from your camera system, make an API call:

```
POST https://your-domain.com/api/add_violation.php

Parameters:
- api_key: your_camera_api_key
- numberplate: MH01AB1234
- location: Junction Name
- violation_type: Red Light Violation
- image: [Base64 encoded image data]
```

## Security Considerations
1. Change the default admin password immediately after installation
2. Use HTTPS for all web traffic
3. Use strong API keys for camera integration
4. Keep database credentials secure

## Support
For issues or support, please contact:

Email: info@trafficchallan.com
Phone: +91 9876543210

---

© 2025 Traffic Challan Payment System. All rights reserved.
