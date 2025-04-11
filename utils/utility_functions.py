import datetime
import pandas as pd
import json
import zipfile
import os
import io
import pytest
import re
from utils.config import Config
import jsonschema

config = Config()


def load_test_data(excel_path, sheet_name):
    # Load the Excel sheet
    df = pd.read_excel(excel_path, sheet_name=sheet_name, dtype=str)

    # Fill NaN values
    data = df.fillna('')

    # Filter rows where "Test Run" column is set to "yes"
    run_test = data[data["Run Test"].str.lower() == "yes"]

    # Get all columns except "Test Run"
    columns = [col for col in run_test.columns if col != "Run Test"]

    # Generate test data as list of tuples
    test_data = [tuple(row) for row in run_test[columns].values]

    return test_data


def assert_api_response(response, expected_status_code, expected_response, response_type, sync_type=None):
    """
        :param response: The response object from the request.
        :param expected_response:  The expected response from the API.
        :param expected_status_code: The expected status code of the API response.
        :param response_type: The type of response to expect. Supported types are "json","text", "date", "zipfile".
        :param sync_type: The type of sync API. Eg: "syncsqldata", "syncthreatfeed"...etc.
        :return: This method returns True if the assertions passes, otherwise it raises an AssertionError.
        """
    if response:
        assert str(response.status_code) == str(expected_status_code), \
            f"API response status code is not 200. Actual status code: {response.status_code}"
        if response_type == "json":
            response_json = dict(response.json())
            expected_response_json = dict(json.loads(expected_response))
            # Validate the response against the expected JSON schema
            # from jsonschema import validate, ValidationError
            # try:
            #     json_schema = json.loads(open("resources/6_3AncorJsonSchema.json").read())
            #     print(json_schema)
            #     validate(instance=response_json, schema=json_schema)
            #     print("API response is valid against the expected JSON schema")
            # except ValidationError as e:
            #     raise AssertionError(f"JSON schema validation error: {e.message}")
        elif response_type == "text":
            response_text = response.text
            assert response_text == expected_response, \
                f"API response does not match the expected response. Actual response: {response_text}\nExpected " \
                f"response: {expected_response}"
        elif response_type == "date":
            date_pattern = r"^\d{4}-\d{2}-\d{2}$"
            response_date = response.text
            assert re.match(date_pattern, response_date), \
                f"API response is not in YYYY-MM-DD format. Actual response: {response_date}"
            assert response_date == expected_response, \
                f"API response does not match the expected response. Actual response: {response_date}\nExpected " \
                f"response: {expected_response}"
        elif response_type == "boolean":
            response_boolean = response.text
            assert response_boolean in ["true", "false"], \
                f"API response is not a boolean. Actual response: {response_boolean}"
            assert response_boolean == expected_response, \
                f"API response does not match the expected response. Actual response: {response_boolean}\nExpected " \
                f"response: {expected_response}"
        elif response_type == "binary":
            response_binary = response.text
            assert response_binary in ['0', '1'], \
                f"API response is not a binary. Actual response: {response_binary}"
            assert response_binary == expected_response, \
                f"API response does not match the expected response. Actual response: {response_binary}\nExpected " \
                f"response: {expected_response}"
        elif response_type == "zipfile":
            assert response.headers['content-type'] == 'application/zip;charset=utf-8', \
                f"API response is not a zipfile. Actual response: {response.headers['content-type']}"
            content = response.content
            if content.startswith(b'PK'):
                print("API response is a zipfile")
                print("Extracting the zipfile")
                try:
                    with zipfile.ZipFile(io.BytesIO(content)) as zipf:
                        # Extract the files
                        assert zipf.testzip() is None, "Content zip file is corrupted"
                        assert len(zipf.infolist()) == 1, "Content zip file is either empty or contains multiple files"
                        file_name = zipf.infolist()[0].filename
                        assert file_name == expected_response, \
                            "Content zip file does not contain the expected file"
                        print("Reading the extracted file")
                        file_content = zipf.open(file_name).read().decode('utf-8', errors='replace')
                        print(f"Extracted files: {file_name}")
                        # print(f"Extracted file content: {file_content}")
                        print("Mapping file names to their corresponding SHA sums")
                        shasum_map = map_shasum(file_content)
                        # print(f"SHA sums: {shasum_map}")
                        print("Asserting the SHA sums with the cloud server")
                        f = config.get_sync_folder_maps
                        d = f[sync_type]
                        cloud_file_path = os.path.join(config.get_download_directory_path, d + "sha256sum.txt")
                        print(f"Cloud file path: {cloud_file_path}")
                        main_shasum_file = open(cloud_file_path, "r").read()
                        main_shasum_map = map_shasum(main_shasum_file)
                        # print(f"Main SHA sums: {main_shasum_map}")
                        # print(f"Extracted SHA sums: {shasum_map}")
                        assert shasum_map == main_shasum_map, "SHA sums do not match with the cloud server"

                except Exception as e:
                    # print(f"Error unzipping content: {e}")
                    pytest.fail(f"Error while processing the zip file: {e}")
            else:
                raise AssertionError("API response is not a zipfile")

    else:
        raise AssertionError("API response is None")


def map_shasum(shasum_file_content):
    """
    :param shasum_file_content: the shasum content from the sync api content.
    :return: A dictionary mapping the file names to their corresponding SHA sums.
    """
    shasum_map = {}
    if "||" in shasum_file_content:
        parts = shasum_file_content.split("||")
        for parts in parts:
            if parts:
                file_name, shasum = parts.split("=", 1)
                shasum_map[file_name] = shasum
    else:
        parts = shasum_file_content.splitlines()
        for parts in parts:
            if parts:
                file_name, shasum = parts.split("=", 1)
                shasum_map[file_name] = shasum
    return shasum_map
