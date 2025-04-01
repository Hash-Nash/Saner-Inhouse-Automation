# root@Ubuntu-20:/opt# cat new-api-shasum.py
# cd /opt# cat api-mail.py --> 2.18 --> divya
# Author: Divya
# Date: 10.09.2024
# run: api-mail.py cloud_ip ancor_ip

##############################################################

import requests
import logging
import os
import argparse
import zipfile
import json
import urllib3
from urllib3.exceptions import InsecureRequestWarning
from datetime import datetime, timedelta
import io
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import paramiko  # type: ignore

# Suppress the warnings from urllib3
urllib3.disable_warnings(InsecureRequestWarning)


# Function to read configuration from a file
def read_config(file_path):
    print(f"Reading configuration from {file_path}")
    try:
        with open(file_path, 'r') as file:
            config = json.load(file)
        return config
    except json.JSONDecodeError as e:
        print(f"Error reading configuration file: {e}")
        return None
    except Exception as e:
        print(f"General error: {e}")
        return None


# Read configuration
config_file_path = 'sync-config.txt'
config = read_config(config_file_path)

if config:
    ancor_saml = config.get('ancor_saml')
    # Access other configuration items similarly
    if ancor_saml is None:
        print("Error: 'ancor_saml' key is missing in the configuration file.")
else:
    print("Configuration could not be read.")
    exit(1)

# Command-line argument parsing
parser = argparse.ArgumentParser(description='Sync Configuration Script')
parser.add_argument('cloud_ip', help='IP address of the cloud server')
parser.add_argument('ancor_ip', help='IP address of the ancor server')
args = parser.parse_args()

# Update IPs and URLs based on command-line arguments
config['cloud_ip'] = args.cloud_ip
config['ancor_ip'] = args.ancor_ip
config['ancor_webservice_url'] = f"https://{config['cloud_ip']}/AncorWebService"

# Extract configuration values
ancor_ip = config['ancor_ip']
cloud_ip = config['cloud_ip']
ancor_saml = config['ancor_saml']
ancor_webservice_url = config['ancor_webservice_url']
common_headers = config['common_headers']
api_endpoints = config['api_endpoints']
ancor_user = config['ancor_user']
ancor_pwd = config['ancor_pwd']
cloud_pwd = config['cloud_pwd']
ancor_path = config['ancor_path']
cloud_path = config['cloud_path']
log_path = config['log_path']
folders_shasum = config['folders_shasum']

os.makedirs(log_path, exist_ok=True)

# Unified log setup
logging.basicConfig(level=logging.DEBUG)
pass_logger = logging.getLogger('pass')
error_logger = logging.getLogger('error')

pass_handler = logging.FileHandler(os.path.join(log_path, 'pass.log'))
error_handler = logging.FileHandler(os.path.join(log_path, 'error.log'))

pass_handler.setLevel(logging.DEBUG)
error_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
pass_handler.setFormatter(formatter)
error_handler.setFormatter(formatter)

pass_logger.addHandler(pass_handler)
error_logger.addHandler(error_handler)

assert pass_logger.hasHandlers(), "Pass logger has no handlers"
assert error_logger.hasHandlers(), "Error logger has no handlers"


class APIRequester:
    def webservice_call(self, url="", req_type="POST", headers=None, post_data=None, ssl_verify=True):
        print(f"Making {req_type} request to {url} with headers {headers} and data {post_data}")
        try:
            res_dict = {}
            if ssl_verify not in [True, False]:
                ssl_verify = True

            if req_type.upper() not in ["GET", "POST"]:
                req_type = "GET"

            if not headers:
                headers = {}

            if not post_data:
                post_data = {}

            try:
                if req_type.upper() == "GET":
                    res = requests.get(url, headers=headers, verify=ssl_verify, timeout=10)
                elif req_type.upper() == "POST":
                    res = requests.post(url, headers=headers, data=post_data, verify=ssl_verify)

            except requests.exceptions.ConnectionError:
                error_logger.error(f"Connection refused for ({url})")
                return {}

            if res:
                res_dict.update({"headers": res.headers, "content": res.content,
                                 "status_code": res.status_code, "ok": res.ok,
                                 "res_object": res})
            return res_dict
        except Exception as msg:
            error_logger.error(f"Error while sending/receiving request: {url} - {msg}")
            return {}


def call_api(api_requester, endpoint):
    url = f"{ancor_webservice_url}/{endpoint}?cli=true"
    method = "GET"
    if "post" in endpoint.lower():
        method = "POST"

    print(f"Calling API endpoint {endpoint} with method {method}")
    try:
        response = api_requester.webservice_call(url, req_type=method, headers=common_headers, ssl_verify=False)
        if response:
            status_code = response.get('status_code', 0)
            content = response.get('content', b'')

            # Attempt to decode the content to UTF-8
            try:
                response_data = content.decode('utf-8')
            except UnicodeDecodeError:
                response_data = repr(content)

            # Check if the content is in zip format and handle accordingly
            if content.startswith(b'PK'):
                try:
                    with zipfile.ZipFile(io.BytesIO(content)) as zipf:
                        # Extract the files
                        extracted_files = []
                        for file_info in zipf.infolist():
                            extracted_files.append(file_info.filename)
                            with zipf.open(file_info) as file:
                                response_data = file.read().decode('utf-8', errors='replace')
                                # Optionally, save the extracted files or process them
                                with open(os.path.join(log_path, file_info.filename), 'w') as f:
                                    f.write(response_data)
                except Exception as e:
                    error_logger.error(f"Error unzipping content: {e}")
                    response_data = repr(content)

            if status_code in [200, 300]:
                pass_logger.info(f"API: {endpoint} - Status: {status_code} - Data: {response_data}")
                return {"status": "pass", "endpoint": endpoint, "status_code": status_code, "data": response_data}
            elif status_code in [400, 500]:
                error_logger.error(f"API: {endpoint} - Status: {status_code} - Data: {response_data}")
                return {"status": "fail", "endpoint": endpoint, "status_code": status_code, "data": response_data}
        else:
            error_logger.error(f"API: {endpoint} - No response received")
            return {"status": "fail", "endpoint": endpoint, "status_code": None, "data": "No response"}
    except requests.RequestException as e:
        error_logger.error(f"API: {endpoint} - Exception: {str(e)}")
        return {"status": "fail", "endpoint": endpoint, "status_code": None, "data": str(e)}


api_requester = APIRequester()
api_results = {"pass": [], "fail": []}

print(f"Testing API endpoints...")
for api in api_endpoints:
    print(f"Testing endpoint: {api}")
    result = call_api(api_requester, api)
    if result["status"] == "pass":
        api_results["pass"].append(result)
    else:
        api_results["fail"].append(result)

# Output pass/fail status to console
print(f"API Tests - Pass: {len(api_results['pass'])}, Fail: {len(api_results['fail'])}")

# Create a zip file for each successful API result
for result in api_results['pass']:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary_file = os.path.join(log_path,
                                f'api_result_{result["endpoint"].replace("/", "_").replace("?", "_")}_{timestamp}.txt')
    zip_file_path = os.path.join(log_path,
                                 f'api_result_{result["endpoint"].replace("/", "_").replace("?", "_")}_{timestamp}.zip')

    with open(summary_file, 'w') as f:
        f.write(f"API Endpoint: {result['endpoint']}\n")
        f.write(f"Status Code: {result['status_code']}\n")
        f.write(f"Response Data:\n{result['data']}\n")

    with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(summary_file, os.path.basename(summary_file))

    os.remove(summary_file)

    print(f"API result for endpoint {result['endpoint']} successfully zipped to {zip_file_path}")

    # Get the size of the created zip file
    zip_size = os.path.getsize(zip_file_path)
    print(f"Zip file size: {zip_size} bytes")

    # Store zip file path and size in the result for use in the email body
    result['zip_file_path'] = zip_file_path
    result['zip_size'] = zip_size

# Print the APIs that passed
if api_results['pass']:
    print("\nAPIs that passed:")
    for result in api_results['pass']:
        print(f"Endpoint: {result['endpoint']} - Status Code: {result['status_code']}")
else:
    print("No APIs passed.")

# Print the APIs that failed
if api_results['fail']:
    print("\nAPIs that failed:")
    for result in api_results['fail']:
        print(f"Endpoint: {result['endpoint']} - Status Code: {result['status_code']}")
else:
    print("No APIs failed.")


# Clean up old zip files
def cleanup_old_files(directory, days=7):
    now = datetime.now()
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path) and filename.endswith(".zip"):
            file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            if (now - file_time) > timedelta(days=days):
                os.remove(file_path)
                print(f"Deleted old zip file: {file_path}")


cleanup_old_files(log_path)

# Email configuration
smtp_server = 'smtp.office365.com'
smtp_port = 587
sender_email = 'infra@secpod.com'
receiver_email = 'divya.j@secpod.com'
email_password = 'Jl3c){fwZjFW'
fail_receiver_email = 'sener_qa@secpod.com'
fail_password = 'T9%VU2uvgbYy^v4t'


# Function to send email notification
def send_email(subject, body, to_email, password):
    from_email = sender_email

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(from_email, password)
            server.sendmail(from_email, to_email, msg.as_string())
        print("Email sent successfully")
    except Exception as e:
        error_logger.error(f"Error sending email: {str(e)}")


# Generate the current timestamp for the subject
current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# Prepare the email body with detailed results
email_body = ("Hi Teams,\n\n"
              "API Test Results:\n\n")

# Track file sizes in a dictionary to ensure correct matching
# file_sizes = {}

"""
for result in api_results['pass'] + api_results['fail']:
   # zip_file_path = os.path.join(log_path, f'api_result_{result["endpoint"].replace("/", "_").replace("?", "_")}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip')


    # Check if the zip file exists and calculate its size
    if os.path.isfile(zip_file_path):
        file_size = os.path.getsize(zip_file_path)
        file_sizes[result["endpoint"]] = file_size
    else:
        file_size = 'N/A'
"""

for result in api_results['pass'] + api_results['fail']:
    zip_file_path = result.get('zip_file_path', 'N/A')
    zip_size = result.get('zip_size', 'N/A')

    email_body += (f"Endpoint: {result['endpoint']}\n"
                   f"Status Code: {result['status_code']}\n"
                   f"Zip File Path: {zip_file_path}\n"
                   f"File Size: {zip_size} bytes\n"
                   f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                   f"Ancour IP: {ancor_ip}\n"
                   f"Cloud IP: {cloud_ip}\n\n")

# Ensure 'Regards, QA Team' is added only once at the end of the email body
email_body += "\nRegards,\nQA Team"

# Determine the email subject based on test results
if api_results['fail']:
    email_subject = f"[FAIL] API Sync Test Result - {current_timestamp}"
    # Send email with failure details only
    # send_email(email_subject, email_body, fail_receiver_email, fail_password)
    send_email(email_subject, email_body, receiver_email, email_password)
else:
    email_subject = f"[PASS] API Sync Test Result - {current_timestamp}"
    # Send email with all results
    send_email(email_subject, email_body, receiver_email, email_password)

#########################################################################################################################

# SHA256 checksum check setup

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

results = {"pass": set(), "fail": set()}


def format_and_sort_sha256(content, is_cloud=False):
    if is_cloud:
        content = content.replace('||', '\n').strip('|')
    lines = content.splitlines()
    lines.sort()
    return "\n".join(lines)


def check_shasum_file_exists(ip, password, base_path, folder, is_cloud=False):
    full_path = os.path.join(base_path, folder, "sha256sum.txt")
    command = f"test -f {full_path} && cat {full_path} || echo 'not found'"

    try:
        ssh.connect(ip, username=ancor_user, password=password)
        stdin, stdout, stderr = ssh.exec_command(command)
        result = stdout.read().decode().strip()

        if result != "not found":
            formatted_content = format_and_sort_sha256(result, is_cloud)
            pass_logger.info(f"File exists, formatted, and sorted: {full_path} on {ip}")
            return formatted_content
        else:
            error_logger.error(f"File does not exist: {full_path} on {ip}")
            return None

    except Exception as e:
        error_logger.error(f"Error checking file on {ip}: {str(e)}")
        return None

    finally:
        ssh.close()


def compare_sha256_checksums(folder1, folder2):
    checksum1 = check_shasum_file_exists(ancor_ip, ancor_pwd, ancor_path, folder1)
    checksum2 = check_shasum_file_exists(cloud_ip, cloud_pwd, cloud_path, folder2, is_cloud=True)

    if checksum1 and checksum2:
        if checksum1 == checksum2:
            pass_logger.info(f"SHA256 checksum match for folders {folder1} and {folder2}")
            results["pass"].add(folder1)
        else:
            error_logger.error(f"SHA256 checksum mismatch for folders {folder1} and {folder2}")
            results["fail"].add(folder1)
    else:
        error_logger.error(f"Checksum files missing for folders {folder1} or {folder2}")


# Compare all folders and handle special case for 'conf' and 'conf_sync'
for folder in folders_shasum:
    if folder.endswith('conf'):
        conf_folder = folder
        conf_sync_folder = f"{folder}_sync"
        print(f"Comparing folder: {conf_folder} with {conf_sync_folder}")
        compare_sha256_checksums(conf_folder, conf_sync_folder)
    else:
        print(f"Checking folder: {folder}")
        # Compare the folder directly
        compare_sha256_checksums(folder, folder)

print(f"Checksum Check Results - Pass: {len(results['pass'])}, Fail: {len(results['fail'])}")

if results['pass']:
    print("\nFolders that Passed Checksum Verification:")
    for folder in results['pass']:
        print(f"- {folder}")

if results['fail']:
    print("\nFolders that Failed Checksum Verification:")
    for folder in results['fail']:
        print(f"- {folder}")


# Function to send email notification
def send_email_shasum(subject, body, to_email, password):
    from_email = sender_email

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(from_email, password)
            server.sendmail(from_email, to_email, msg.as_string())
        print("Email sent successfully")
    except Exception as e:
        error_logger.error(f"Error sending email: {str(e)}")


# Generate the current timestamp for the subject
current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# Prepare the email body with detailed results
email_body = ("Hi Teams,\n\n"
              "Sync File Comparison Result:\n\n")

if results['pass']:
    email_body += "Folders that Passed Checksum Verification:\n"
    for folder in results['pass']:
        email_body += f"- {folder}\n"

if results['fail']:
    email_body += "\n[FAIL] Folders that Failed Checksum Verification:\n"
    for folder in results['fail']:
        email_body += f"- {folder}\n"

email_body += (f"\nAncour IP: {ancor_ip}\n"
               f"Cloud IP: {cloud_ip}\n\n"
               "Regards,\n"
               "QA Team")

# Determine the email subject based on test results
if results['fail']:
    email_subject = f"[FAIL] Sync File Comparison Result - {current_timestamp}"
    # Send email with failure details to both recipients
    # send_email_shasum(email_subject, email_body, fail_receiver_email, fail_password)
    send_email_shasum(email_subject, email_body, receiver_email, email_password)
else:
    email_subject = f"[PASS] Sync File Comparison Result - {current_timestamp}"
    # Send email with all results to both recipients
    send_email_shasum(email_subject, email_body, receiver_email, email_password)
