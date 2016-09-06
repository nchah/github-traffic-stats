#!/usr/bin/env python

import argparse
import getpass
import requests


def main(username, repo):
    """ """
    username = username.strip()
    repo = repo.strip()
    pw = getpass.getpass('Password:')

    # GET  /repos/:owner/:repo/traffic/views
    base_traffic_url = 'https://api.github.com/repos/'
    traffic_headers = {'Accept': 'application/vnd.github.spiderman-preview'}
    auth = (username, pw)

    traffic_url = base_traffic_url + username + '/' + repo + '/traffic/views'
    r = requests.get(traffic_url, auth=auth, headers=traffic_headers)

    # print r.status_code  # successful 200!
    print r.json()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('user', help='Github username')
    parser.add_argument('repo', help='User\'s repo')
    args = parser.parse_args()
    main(args.user, args.repo)

