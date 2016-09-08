#!/usr/bin/env python

import argparse
from collections import OrderedDict
import datetime
import getpass
import requests

"""
TODO:
- DONE 2016-09-05: Get all repos optionally
- DONE 2016-09-06: Pretty format JSON response
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


def timestamp_to_utc(timestamp):
    """Convert unix timestamp to UTC date
    timestamp: int - the unix timestamp integer
    """
    timestamp = int(str(timestamp)[0:10])
    utc_date = datetime.datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d')
    return utc_date


def json_to_table(repo, json_response):
    """Parse traffic stats in JSON and format into a table
    json_response: json - the json input
    """
    repo_name = repo
    total_views = str(json_response['count'])
    total_uniques = str(json_response['uniques'])

    dates_and_views = OrderedDict()
    detailed_views = json_response['views']
    detailed_views_len = len(detailed_views)
    for i in range(0, detailed_views_len):
        utc_date = timestamp_to_utc(int(detailed_views[i]['timestamp']))
        dates_and_views[utc_date] = (str(detailed_views[i]['count']), str(detailed_views[i]['uniques']))

    """Table template
    repo_name
    2016-09-05  | count | uniques
    date        | #     | #...
    """
    table_alt = repo_name + '\n' +\
            '# Total Views:' + '\t' + total_views + '\n' + '# Total Unique:' + '\t' + total_uniques + '\n' +\
            'Date' + '\t\t' + 'Views' + '\t' + 'Unique visitors' + '\n'

    table = repo_name + '\n' +\
            'Date' + '\t\t' + 'Views' + '\t' + 'Unique visitors' + '\n' +\
            'Totals' + '\t\t' + total_views + '\t' + total_uniques + '\n'
    for i in dates_and_views:
        table += i + '\t' + dates_and_views[i][0] + '\t' + dates_and_views[i][1] + '\n'

    return table


def store_json():
    """ """

    return ''


def main(username, repo='*ALL*'):
    """Query the GitHub Traffic API
    username: string - GitHub username
    repo: string - GitHub user's repo name or by default 'ALL' repos
    """
    username = username.strip()
    repo = repo.strip()
    pw = getpass.getpass('Password:')
    auth_pair = (username, pw)
    traffic_headers = {'Accept': 'application/vnd.github.spiderman-preview'}

    if repo == '*ALL*':
        repos_response = send_request('repos', auth_pair)
        repos_response = repos_response.json()
        try:
            if repos_response.get('message'):
                print(repos_response['message'])
                return 'Code done'
        except AttributeError:
            repos = []
            for i in range(0, len(repos_response)):
                repos.append(repos_response[i]['name'])
            for repo in repos:
                traffic_response = send_request('traffic', auth_pair, repo, traffic_headers)
                traffic_response = traffic_response.json()
                print(json_to_table(repo, traffic_response))

    else:
        traffic_response = send_request('traffic', auth_pair, repo, traffic_headers)
        traffic_response = traffic_response.json()
        if traffic_response.get('message'):
            print(traffic_response['message'])
            return 'Code done'
        print(json_to_table(repo, traffic_response))

    return ''


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('user', help='Github username')
    parser.add_argument('repo', help='User\'s repo')
    args = parser.parse_args()
    main(args.user, args.repo)

