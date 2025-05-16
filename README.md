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
   - Upload all files in the `Website` folder and the `.env` file to your hosting root directory

2. **Configure environment variables:**
   - Edit the `.env` file with your configuration settings:
     ```
     # Database Configuration
     DB_HOST=localhost
     DB_NAME=traffic_challan
     DB_USER=your_database_username
     DB_PASS=your_database_password

     # Email API Configuration
     EMAIL_API_URL=https://thegroup11.com/api/sendmail
     EMAIL_API_KEY=your_actual_api_key

     # Site Configuration
     SITE_NAME=Traffic Challan Payment System
     SITE_URL=https://yourwebsite.com

     # Camera API Security
     CAMERA_API_KEY=your_camera_api_key

     # UPI Payment Details
     UPI_ID=your-upi-id@bank

     # Admin Default Credentials
     ADMIN_USERNAME=admin
     ADMIN_PASSWORD=your_secure_password
     ```

3. **Set up the database:**
   - Visit `https://your-domain.com/setup_database.php` in your browser
   - This script will create all the necessary tables
   - You can add sample data by clicking the "Add Sample Data" button

4. **Security considerations:**
   - Make sure the `.env` file is not accessible from the web
   - Add `.env` to your `.gitignore` file to avoid committing sensitive information
   - The system is already set up to use these environment variables

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
5. Protect your `.env` file:
   - Make sure it's included in `.gitignore` to avoid accidentally committing it
   - Set proper file permissions (600) so only the web server can read it
   - Ensure it's stored outside of publicly accessible directories when possible
6. Regularly update your passwords and API keys

## Support
For issues or support, please contact:

Email: info@trafficchallan.com
Phone: +91 9876543210

---

© 2025 Traffic Challan Payment System. All rights reserved.
