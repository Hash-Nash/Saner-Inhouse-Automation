import paramiko
import os
import pytest

from utils.config import Config

config = Config()


@pytest.fixture(scope="session", autouse=True)
def get_cloud_server_shasum_files(host=config.get_cloud_ip,
                                  username=config.get_cloud_ssh_username,
                                  password=config.get_cloud_ssh_password):
    """
    :param host: Cloud server IP
    :param username: cloud server username
    :param password: cloud server password
    :return: the SHA sum content of the file
    """
    try:

        # Create SSH client
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # Automatically add unknown hosts

        # Connect to the server
        client.connect(hostname=host, username=username, password=password)
        print("Connected to the cloud server")
        # Open an SFTP session
        sftp = client.open_sftp()
        print("Opened an SFTP session")

        os.makedirs(config.get_download_directory_path, exist_ok=True)

        cloud_feed_home_path = config.get_could_content_files_path
        sync_folders_map = config.get_sync_folder_maps
        for sync_type, folder in sync_folders_map.items():
            file_path = cloud_feed_home_path + folder + "/sha256sum.txt"
            print(f"Getting the SHA sum file from the cloud server: {file_path}")

            filename = folder + os.path.basename(file_path)
            local_file_path = os.path.join(config.get_download_directory_path, filename)

            # Download the file
            sftp.get(file_path, local_file_path)
            print(f"Downloaded the SHA sum file to the local path: {local_file_path}")
            # Close connections
        sftp.close()
        client.close()

    except Exception as e:
        print(f"Error while getting the SHA sum file from the cloud server: {e}")
        return None
