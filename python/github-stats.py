#!/usr/bin/env python

import argparse
import csv
from collections import OrderedDict
import datetime
import getpass
import requests

"""
TODO:
- DONE 2016-09-05: Get all repos optionally
- DONE 2016-09-06: Pretty format JSON response
- DONE 2016-09-30: Save as CSV output

"""
# Globals
current_timestamp = str(datetime.datetime.now().strftime('%Y-%m-%d-%Hh-%Mm'))  # was .strftime('%Y-%m-%d'))
csv_file_name = 'data/' + current_timestamp + '-traffic-stats.csv'


def send_request(resource, auth, repo=None, headers=None):
    """Send request to Github API
    :param resource: string - specify the API to call
    :param auth: tuple - username-password tuple
    :param repo: string - if specified, the specific repository name
    :param headers: dict - if specified, the request headers
    :return: response - GET request response
    """
    if resource == 'traffic':
        # GET /repos/:owner/:repo/traffic/views <- from developer.github.com/v3/repos/traffic/#views
        base_url = 'https://api.github.com/repos/'
        base_url = base_url + auth[0] + '/' + repo + '/traffic/views'
        response = requests.get(base_url, auth=auth, headers=headers)
        return response
    elif resource == 'repos':
        # GET /user/repos <- from developer.github.com/v3/repos/#list-your-repositories
        base_url = 'https://api.github.com/users/'
        base_url = base_url + auth[0] + '/repos'
        response = requests.get(base_url, auth=auth)
        return response


def timestamp_to_utc(timestamp):
    """Convert unix timestamp to UTC date
    :param timestamp: int - the unix timestamp integer
    :return: utc_data - the date in YYYY-MM-DD format
    """
    # deprecated pre-10/31/2016
    timestamp = int(str(timestamp)[0:10])
    utc_date = datetime.datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d')
    # utc_date = timestamp[0:10]
    return utc_date


def json_to_table(repo, json_response):
    """Parse traffic stats in JSON and format into a table
    :param repo: str - the GitHub repository name
    :param json_response: json - the json input
    :return: table: str - for printing on command line
    """
    repo_name = repo
    total_views = str(json_response['count'])
    total_uniques = str(json_response['uniques'])

    dates_and_views = OrderedDict()
    detailed_views = json_response['views']
    for row in detailed_views:
        # utc_date = timestamp_to_utc(int(row['timestamp']))
        utc_date = str(row['timestamp'][0:10])
        dates_and_views[utc_date] = (str(row['count']), str(row['uniques']))

    """Table template
    repo_name
    Date        Views   Unique visitors
    Totals      #       #
    date        #       #
    ...         ...     ...
    """
    table_alt = repo_name + '\n' +\
            '# Total Views:' + '\t' + total_views + '\n' + '# Total Unique:' + '\t' + total_uniques + '\n' +\
            'Date' + '\t\t' + 'Views' + '\t' + 'Unique visitors' + '\n'

    table = repo_name + '\n' +\
            'Date' + '\t\t' + 'Views' + '\t' + 'Unique visitors' + '\n' +\
            'Totals' + '\t\t' + total_views + '\t' + total_uniques + '\n'
    for row in dates_and_views:
        table += row + '\t' + dates_and_views[row][0] + '\t' + dates_and_views[row][1] + '\n'

    return table


def store_csv(repo, json_response):
    """Store the traffic stats as a CSV, with schema:
    repo_name, date, views, unique_visitors

    :param repo: str - the GitHub repository name
    :param json_response: json - the json input
    :return:
    """
    repo_name = repo
    # # Not writing Totals stats into the CSV to maintain normalization
    # total_views = str(json_response['count'])
    # total_uniques = str(json_response['uniques'])

    dates_and_views = OrderedDict()
    detailed_views = json_response['views']
    for row in detailed_views:
        utc_date = timestamp_to_utc(int(row['timestamp']))
        dates_and_views[utc_date] = (str(row['count']), str(row['uniques']))

    # Starting up the CSV, writing the headers in a first pass
    # Check if existing CSV
    try:
        csv_file = open(csv_file_name).readlines()
        if csv_file:
            for i in dates_and_views:
                row = [repo_name, i, dates_and_views[i][0], dates_and_views[i][1]]
                with open(csv_file_name, 'a') as csvfile:
                    csv_writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                    csv_writer.writerow(row)
    except IOError:
        headers = ['repository_name', 'date', 'views', 'unique_visitors']
        with open(csv_file_name, 'a') as csvfile:
            csv_writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow(headers)

        for i in dates_and_views:
            row = [repo_name, i, dates_and_views[i][0], dates_and_views[i][1]]
            with open(csv_file_name, 'a') as csvfile:
                csv_writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                csv_writer.writerow(row)

    return ''


def main(username, repo='*ALL*', save_csv='save_csv'):
    """Query the GitHub Traffic API
    :param username: string - GitHub username
    :param repo: string - GitHub user's repo name or by default 'ALL' repos
    :param save_csv: string - Specify if CSV log should be saved
    :return:
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
            for repo in repos_response:
                repos.append(repo['name'])
            for repo in repos:
                traffic_response = send_request('traffic', auth_pair, repo, traffic_headers)
                traffic_response = traffic_response.json()
                print(json_to_table(repo, traffic_response))
                if save_csv == 'save_csv':
                    store_csv(repo, traffic_response)
    else:
        traffic_response = send_request('traffic', auth_pair, repo, traffic_headers)
        traffic_response = traffic_response.json()
        if traffic_response.get('message'):
            print(traffic_response['message'])
            return 'Code done'
        print(json_to_table(repo, traffic_response))
        if save_csv == 'save_csv':
            store_csv(repo, traffic_response)

    return ''


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('username', help='Github username')
    parser.add_argument('repo', help='User\'s repo')
    parser.add_argument('save_csv', help='Set to "no_csv" if no CSV should be saved')
    args = parser.parse_args()
    main(args.username, args.repo, args.save_csv)

