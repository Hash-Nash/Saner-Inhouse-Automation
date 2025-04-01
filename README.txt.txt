# README.TXT

# API Sync Testing Script

This script is designed to test API endpoints, handle responses, generate zip files of the results, and send an email with the results. It also includes functionality to clean up old log files.

Prerequisites:
Python 3.x
Required Python packages: requests, zipfile, io, os, smtplib, email, paramiko

Usage:
To run the script, you need to provide the cloud_ip and ancor_ip as command-line arguments.
--> python3 your_script.py <cloud_ip> <ancor_ip>
--> ex: python3 your_script.py 192.168.1.1 192.168.1.2

Script Functionality:
API Request Handling:

Makes HTTP GET or POST requests to specified API endpoints.
Handles responses including zip files if present.

File Handling:
Saves API responses to text files.
Compresses these files into zip archives.

Email Notification:
Sends an email with the results, including the path and size of the zip files.
Requires SMTP server details and credentials.

Log Management:
Deletes zip files older than 7 days from the log directory.

Configuration:
Before running the script, ensure that the following variables are configured in the script (sync-config.txt):
ancor_ip, cloud_ip, ancor_saml, ancor_webservice_url, common_headers (Content-type, Authorization), api_endpoints, ancor_user, ancor_pwd, cloud_pwd, ancor_path, cloud_path and log_path.

ancor_ip: IP address of the Ancor server.
ancor_pwd: Password for the Ancor server.
ancor_path: Base path on the Ancor server.
cloud_ip: IP address of the Cloud server.
cloud_pwd: Password for the Cloud server.
cloud_path: Base path on the Cloud server.
ancor_user: Username for the Ancor server.
api_endpoints: List of api_endpoints.
pass_logger and error_logger: Logging objects for recording pass and error messages.

# Shsaum Sync Testing Script

This script is designed to connect to remote servers via SSH, check for the existence of SHA256 checksum files, format and sort the checksum data, and compare checksums between two sets of folders. It reports the results of these comparisons, indicating which folders have matching checksums and which do not.


Configuration
Before running the script, update the following variables with your specific details:

ancor_ip: IP address of the Ancor server.
ancor_pwd: Password for the Ancor server.
ancor_path: Base path on the Ancor server.
cloud_ip: IP address of the Cloud server.
cloud_pwd: Password for the Cloud server.
cloud_path: Base path on the Cloud server.
ancor_user: Username for the Ancor server.
folders_shasum: List of folder names to check for SHA256 checksums.
pass_logger and error_logger: Logging objects for recording pass and error messages.

Usage:
To run the script, you need to provide the cloud_ip and ancor_ip as command-line arguments.
--> python3 your_script.py <cloud_ip> <ancor_ip>
--> ex: python3 your_script.py 192.168.1.1 192.168.1.2

format_and_sort_sha256(content, is_cloud=False): Formats and sorts the SHA256 checksum content. Handles different formats based on whether the content is from the cloud.

check_shasum_file_exists(ip, password, base_path, folder, is_cloud=False): Checks if the SHA256 checksum file exists on the remote server. Returns the formatted and sorted checksum content if the file exists; otherwise, logs an error.

compare_sha256_checksums(folder1, folder2): Compares SHA256 checksums between two folders. Logs the result and adds the folder to the appropriate pass or fail set.

Email Notification:
Sends an email with the results, including the path and size of the zip files.
Requires SMTP server details and credentials.




