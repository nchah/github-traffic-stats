#!/usr/bin/env python

import argparse
import csv
import os
from collections import OrderedDict
import datetime
import getpass
import requests


# Globals
current_timestamp = str(datetime.datetime.now().strftime('%Y-%m-%d-%Hh-%Mm'))  # was .strftime('%Y-%m-%d'))
path = os.path.dirname(os.path.abspath(__file__))
top_dir = os.path.split(path)[0]
csv_file_name = top_dir+'/data/' + current_timestamp + '-traffic-stats.csv'


def send_request(resource, auth, repo=None, headers=None):
    """ Send request to specific Github API endpoint
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
    if resource == 'clones':
        # GET /repos/:owner/:repo/traffic/clones <- from developer.github.com/v3/repos/traffic/#clones
        base_url = 'https://api.github.com/repos/'
        base_url = base_url + auth[0] + '/' + repo + '/traffic/clones'
        response = requests.get(base_url, auth=auth, headers=headers)
        return response
    if resource == 'referrers':
        # GET /repos/:owner/:repo/traffic/popular/referrers <- from developer.github.com/v3/repos/traffic/#list-referrers
        base_url = 'https://api.github.com/repos/'
        base_url = base_url + auth[0] + '/' + repo + '/traffic/popular/referrers'
        response = requests.get(base_url, auth=auth, headers=headers)
        return response


def json_to_table(repo, json_response, response_type):
    """ Parse traffic stats in JSON and format into a table
    :param repo: str - the GitHub repository name
    :param json_response: json - the json input
    :param response_type: str - specifies the kind of table to create
    :return: table: str - for printing on command line
    """
    if response_type == 'repos':
        label1 = "Views"
        label2 = "Unique visitors"
    if response_type == 'clones':
        label1 = "Clones"
        label2 = "Unique cloners"

    repo_name = repo
    total_label1 = str(json_response['count'])
    total_uniques = str(json_response['uniques'])

    # If there is granular date-level data
    dates_and_label1 = OrderedDict()
    detailed_label1 = json_response[label1.lower()]  # 'views', 'clones'
    for row in detailed_label1:
        utc_date = str(row['timestamp'][0:10])
        dates_and_label1[utc_date] = (str(row['count']), str(row['uniques']))

    """ Table template
    repo_name
    Date        label1  label2
    Totals      #       #
    date        #       #
    ...         ...     ...
    """
    table = repo_name + '\n' +\
            'Date' + '\t\t' + label1 + '\t' + label2 + '\n' +\
            'Totals' + '\t\t' + total_label1 + '\t' + total_uniques + '\n'
    for row in dates_and_label1:
        table += row + '\t' + dates_and_label1[row][0] + '\t' + dates_and_label1[row][1] + '\n'

    return table


def store_csv(repo, json_response):
    """ Store the traffic stats as a CSV, with schema:
    repo_name, date, views, unique_visitors

    :param repo: str - the GitHub repository name
    :param json_response: json - the json input
    """
    repo_name = repo
    # # Not writing Totals stats into the CSV to maintain normalization
    # total_views = str(json_response['count'])
    # total_uniques = str(json_response['uniques'])

    dates_and_views = OrderedDict()
    detailed_views = json_response['views']
    for row in detailed_views:
        utc_date = str(row['timestamp'][0:10])
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


def main(username, repo='ALL', save_csv='save_csv'):
    """ Run main code logic
    :param username: string - GitHub username
    :param repo: string - GitHub user's repo name or by default 'ALL' repos
    :param save_csv: string - Specify if CSV log should be saved
    """
    username = username.strip()
    repo = repo.strip()
    pw = getpass.getpass('Password:')
    auth_pair = (username, pw)
    traffic_headers = {'Accept': 'application/vnd.github.spiderman-preview'}

    if repo == 'ALL':
        # By default iterate over all repositories
        repos_response = send_request('repos', auth_pair).json()
        # Error handling in case of {'documentation_url': 'https://developer.github.com/v3', 'message': 'Not Found'}
        try:
            if repos_response.get('message'):
                print(repos_response['message'])
                return 'Code done.'
        except AttributeError:
            repos = []
            for repo in repos_response:
                repos.append(repo['name'])
            for repo in repos:
                traffic_response = send_request('traffic', auth_pair, repo, traffic_headers).json()
                print(json_to_table(repo, traffic_response, 'repos'))
                clones_response = send_request('clones', auth_pair, repo, traffic_headers).json()
                print(json_to_table(repo, clones_response, 'clones'))
                # Saving data
                if save_csv == 'save_csv':
                    store_csv(repo, traffic_response)
    else:
        # Or just request 1 repo
        traffic_response = send_request('traffic', auth_pair, repo, traffic_headers).json()
        # Error handling in case of {'documentation_url': 'https://developer.github.com/v3', 'message': 'Not Found'}
        if traffic_response.get('message'):
            print(traffic_response['message'])
            return 'Code done.'
        print(json_to_table(repo, traffic_response, 'repos'))
        clones_response = send_request('clones', auth_pair, repo, traffic_headers).json()
        print(json_to_table(repo, clones_response, 'clones'))
        # Saving data
        if save_csv == 'save_csv':
            store_csv(repo, traffic_response)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('username', help='Github username')
    parser.add_argument('repo', help='User\'s repo')
    parser.add_argument('save_csv', help='Set to "no_csv" if no CSV should be saved')
    args = parser.parse_args()
    main(args.username, args.repo, args.save_csv)
