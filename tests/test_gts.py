import unittest
import os
import logging
from gts import send_request, store_csv

logging.basicConfig()
logger = logging.getLogger(__file__)


class GithubTrafficStatsTest(unittest.TestCase):

    def setUp(self):
        self.username = os.environ.get('github_username')
        self.password = os.environ.get('github_pass')
        self.auth_pair = (self.username, self.password)
        # self.traffic_headers = {'Accept': 'application/vnd.github.spiderman-preview'}

    def test_send_request(self):
        response = send_request(auth=self.auth_pair, organization=self.username, resource='repos')
        logger.info(response.content)
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 200)

    def test_store_csv(self):
        response = send_request(auth=self.auth_pair, organization=self.username, resource='traffic',
                                repo='github-traffic-stats')
        logger.info(response.content)
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 200)
        json_response = response.json()
        self.assertTrue(len(json_response) > 0)
        self.assertIn('count', json_response)
        self.assertIn('uniques', json_response)
        store_csv(file_path='test.csv', json_response=json_response, repo='github-traffic-stats', response_type='views')
        cur_dir = os.getcwd()
        file_list = os.listdir(cur_dir)
        has_generated_csv = False
        for f in file_list:
            if 'test.csv' in f:
                has_generated_csv = True
                os.remove(f)
                break
        self.assertTrue(has_generated_csv)
