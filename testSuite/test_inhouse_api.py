import pytest
from utils import utility_functions
from utils.api_client import APIClient
from utils import config

config = config.Config()


class TestInhouseAPIs:
    test_data_1 = utility_functions.load_test_data(excel_path="resources/InhouseTestCases.xlsx",
                                                 sheet_name="InhouseAPIs")
    test_data_2 = utility_functions.load_test_data(excel_path="resources/InhouseTestCases.xlsx",
                                                   sheet_name="6.3-Inhouse")
    test_data = test_data_1 + test_data_2
    print(test_data)

    @pytest.mark.parametrize("test_description, api_endpoint, ancor_saml, expected_api_response_status, response_type,"
                             "expected_api_response", test_data)
    def test_inhouse_api(self, test_description, api_endpoint, ancor_saml, expected_api_response_status, response_type,
                         expected_api_response):
        print()
        print("*" * 50)
        print(f"Test Description: {test_description}")
        print("*" * 50)
        print()
        url = config.get_cloud_webservice_url + api_endpoint
        print(f"API Endpoint: {url}")
        headers = {"Authorization": f"SAML {ancor_saml}", "User-Agent": "Saner-Inhouse-Automation"}
        response = APIClient.send_request(url=url, method="GET", headers=headers, ssl_verify=False)
        print(f"API Response: {response.text}")
        print("Asserting the API response")
        if "sync" in api_endpoint:
            utility_functions.assert_api_response(response, expected_api_response_status, expected_api_response,
                                                  response_type, sync_type=api_endpoint)
        else:
            utility_functions.assert_api_response(response, expected_api_response_status, expected_api_response,
                                                  response_type)

