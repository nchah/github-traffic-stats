#!/usr/bin/env python

import argparse
import getpass
import requests

"""
TODO:
- DONE 2016-09-05: Get all repos optionally
- Pretty format JSON response
- Save as CSV output

"""


def send_request(resource, auth, repo=None, headers=None):
    """Send request to Github API

    resource: string - specify the API to call
    auth: tuple - username-password tuple
    repo: string - if specified, the specific repository name
    headers: dict - if specified, the request headers
    """
    if resource == 'traffic':
        # GET /repos/:owner/:repo/traffic/views <- from developer.github.com/v3/repos/traffic/#views
        base_url = 'https://api.github.com/repos/'
        base_url = base_url + auth[0] + '/' + repo + '/traffic/views'
        response = requests.get(base_url, auth=auth, headers=headers)

    elif resource == 'repos':
        # GET /user/repos <- from developer.github.com/v3/repos/#list-your-repositories
        base_url = 'https://api.github.com/users/'
        base_url = base_url + auth[0] + '/repos'
        response = requests.get(base_url, auth=auth)

    return response


def json_to_table():
    """ """

    return ''


def main(username, repo='ALL'):
    """Query the GitHub Traffic API

    username: string - GitHub username
    repo: string - GitHub user's repo name or by default 'ALL' repos
    """
    username = username.strip()
    repo = repo.strip()
    pw = getpass.getpass('Password:')
    auth_pair = (username, pw)
    traffic_headers = {'Accept': 'application/vnd.github.spiderman-preview'}

    if repo == 'ALL':
        repos_response = send_request('repos', auth_pair)
        repos_response = repos_response.json()
        repos = []
        for i in range(0, len(repos_response)):
            repos.append(repos_response[i]['name'])
        print(repos)

        for repo in repos:
            traffic_response = send_request('traffic', auth_pair, repo, traffic_headers)

    else:
        traffic_response = send_request('traffic', auth_pair, repo, traffic_headers)
        print(traffic_response.json())


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('user', help='Github username')
    parser.add_argument('repo', help='User\'s repo')
    args = parser.parse_args()
    main(args.user, args.repo)

