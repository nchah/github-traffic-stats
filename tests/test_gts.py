import unittest
import os
from gts import send_request, store_csv


class GithubTrafficStatsTest(unittest.TestCase):

    def setUp(self):
        self.username = "anthonybloomer"
        self.auth_pair = (self.username, os.environ.get('GITHUB_PASSWORD'))
        self.traffic_headers = {'Accept': 'application/vnd.github.spiderman-preview'}

    def test_send_request(self):
        response = send_request('repos', self.username, self.auth_pair, self.traffic_headers)
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 200)

    def test_store_csv(self):
        response = send_request('traffic', self.username, self.auth_pair, 'github-traffic-stats', self.traffic_headers)
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 200)
        json_response = response.json()
        self.assertTrue('count' in json_response)
        self.assertTrue('uniques' in json_response)
        store_csv('test.csv', json_response, 'github-traffic-stats', 'views')
        cur_dir = os.getcwd()
        file_list = os.listdir(cur_dir)
        has_generated_csv = False
        for f in file_list:
            if 'test.csv' in f:
                has_generated_csv = True
                os.remove(f)
                break
        self.assertTrue(has_generated_csv)
