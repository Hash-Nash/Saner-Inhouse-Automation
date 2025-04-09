import json


class Config:
    def __init__(self):
        self.config_json_path = "resources/config.json"
        with open(self.config_json_path) as config_file:
            self.config = json.load(config_file)

            self.get_cloud_webservice_url = self.config["cloud_webservice_api_url"]
            self.get_cloud_ip = self.config["cloud_ip"]
            self.get_could_content_files_path = self.config["cloud_content_files_path"]
            self.get_sync_folder_maps = self.config["sync_folder_map"]
            self.get_download_directory_path = self.config["download_directory_path"]
            self.get_cloud_ssh_username = self.config["cloud_ssh_user"]
            self.get_cloud_ssh_password = self.config["cloud_ssh_password"]
