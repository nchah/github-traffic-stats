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
path = os.path.abspath(os.path.dirname(__file__))
csv_file_name = current_timestamp + '-traffic-stats.csv'
csv_file_name_clones = current_timestamp + '-clone-stats.csv'
csv_file_name_referrers = current_timestamp + '-referrer-stats.csv'


def send_request(resource, organization, auth, repo=None, headers=None):
    """ Send request to specific Github API endpoint
    :param resource: string - specify the API to call
    :param organization: string - specify the repository organization if not owner by username
    :param auth: username:password separated string - if no password specified, interactive dialog used
    :param repo: string - if specified, the specific repository name
    :param headers: dict - if specified, the request headers
    :return: response - GET request response
    """
    if resource == 'traffic':
        # GET /repos/:owner/:repo/traffic/views <- from developer.github.com/v3/repos/traffic/#views
        base_url = 'https://api.github.com/repos/'
        base_url = base_url + organization + '/' + repo + '/traffic/views'
        response = requests.get(base_url, auth=auth, headers=headers)
        return response
    elif resource == 'repos':
        # GET /user/repos <- from developer.github.com/v3/repos/#list-your-repositories
        base_url = 'https://api.github.com/users/'
        base_url = base_url + organization + '/repos'
        response = requests.get(base_url, auth=auth)
        return response
    elif resource == 'clones':
        # GET /repos/:owner/:repo/traffic/clones <- from developer.github.com/v3/repos/traffic/#clones
        base_url = 'https://api.github.com/repos/'
        base_url = base_url + organization + '/' + repo + '/traffic/clones'
        response = requests.get(base_url, auth=auth, headers=headers)
        return response
    elif resource == 'referrers':
        # GET /repos/:owner/:repo/traffic/popular/referrers <- from developer.github.com/v3/repos/traffic/#list-referrers
        base_url = 'https://api.github.com/repos/'
        base_url = base_url + organization + '/' + repo + '/traffic/popular/referrers'
        response = requests.get(base_url, auth=auth, headers=headers)
        return response


def json_to_table(repo, json_response, response_type):
    """ Parse traffic stats in JSON and format into a table
    :param repo: str - the GitHub repository name
    :param json_response: json - the json input
    :param response_type: str - specifies the kind of table to create
    :return: table: str - for printing on command line
    """
    if response_type == 'traffic':
        label0 = "Visitors"
        label1 = "Views"
        label2 = "Unique visitors"
    if response_type == 'clones':
        label0 = "Git clones"
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
    # Set the table
    table = '> ' + repo_name + ' - ' + label0 + '\n' +\
            'Date' + '\t\t' + label1 + '\t' + label2 + '\n' +\
            'Totals' + '\t\t' + total_label1 + '\t' + total_uniques + '\n'
    # Add rows to the table
    for row in dates_and_label1:
        table += row + '\t' + dates_and_label1[row][0] + '\t' + dates_and_label1[row][1] + '\n'

    return table


def json_to_table_referrers(repo, json_response):
    """ Parse traffic stats in JSON and format into a table
    :param repo: str - the GitHub repository name
    :param json_response: json - the json input
    :return: table: str - for printing on command line
    """
    repo_name = repo
    total_count = 0
    total_uniques = 0

    # If there is granular date-level data
    refs = OrderedDict()
    for row in json_response:
        referrer = row['referrer']
        refs[referrer] = (str(row['count']), str(row['uniques']))
        total_count += row['count']
        total_uniques += row['uniques']
    """ Table template
    repo_name
    Date        Count   Uniques
    Totals      #       #
    site        #       #
    ...         ...     ...
    """
    # Set the table
    table = '> ' + repo_name + ' - Referring sites' + '\n' +\
            'Date' + '\t\t' + 'Views' + '\t' + 'Unique visitors' + '\n' +\
            'Totals' + '\t\t' + str(total_count) + '\t' + str(total_uniques) + '\n'
    # Add rows to the table
    for row in refs:
        # Note: The referring website can sometimes be quite lengthy
        # so the output for this part can get buggy depending on your terminal
        if len(row) >= 8:
            table += '%.8s...\t%s\t%s \n' % (row, refs[row][0], refs[row][1])
        else:
            table += '%.8s\t\t%s\t%s \n' % (row, refs[row][0], refs[row][1])

    return table


def store_csv_referrers(file_path, repo, json_response):
    """ Store the traffic stats as a CSV, with schema:
    repo_name, site, views, unique_visitors
    :param file_path: str - path to store CSV
    :param repo: str - the GitHub repository name
    :param json_response: json - the json input
    """
    repo_name = repo
    sites_and_views = OrderedDict()
    for row in json_response:
        site = row['referrer']
        sites_and_views[site] = (str(row['count']), str(row['uniques']))
    # Starting up the CSV, writing the headers in a first pass
    # Check if existing CSV
    try:
        csv_file = open(file_path).readlines()
        if csv_file:
            for i in sites_and_views:
                row = [repo_name, i, sites_and_views[i][0], sites_and_views[i][1]]
                with open(file_path, 'a') as csvfile:
                    csv_writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                    csv_writer.writerow(row)
    except IOError:
        headers = ['repository_name', 'site', 'views', 'unique_visitors/cloners']
        with open(file_path, 'a') as csvfile:
            csv_writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow(headers)

        for i in sites_and_views:
            row = [repo_name, i, sites_and_views[i][0], sites_and_views[i][1]]
            with open(file_path, 'a') as csvfile:
                csv_writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                csv_writer.writerow(row)


def store_csv(file_path, repo, json_response, response_type):
    """ Store the traffic stats as a CSV, with schema:
    repo_name, date, views, unique_visitors/cloners
    :param file_path: str - path to store CSV
    :param repo: str - the GitHub repository name
    :param json_response: json - the json input
    :param response_type: str - 'views', 'clones', ''
    """
    repo_name = repo
    # # Not writing Totals stats into the CSV to maintain normalization
    # total_views = str(json_response['count'])
    # total_uniques = str(json_response['uniques'])

    dates_and_views = OrderedDict()
    detailed_views = json_response[response_type]  # 'views', 'clones'
    for row in detailed_views:
        utc_date = str(row['timestamp'][0:10])
        dates_and_views[utc_date] = (str(row['count']), str(row['uniques']))

    # Starting up the CSV, writing the headers in a first pass
    # Check if existing CSV
    try:
        csv_file = open(file_path).readlines()
        if csv_file:
            for i in dates_and_views:
                row = [repo_name, i, dates_and_views[i][0], dates_and_views[i][1]]
                with open(file_path, 'a') as csvfile:
                    csv_writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                    csv_writer.writerow(row)
    except IOError:
        headers = ['repository_name', 'date', response_type.lower(), 'unique_visitors/cloners']
        with open(file_path, 'a') as csvfile:
            csv_writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow(headers)

        for i in dates_and_views:
            row = [repo_name, i, dates_and_views[i][0], dates_and_views[i][1]]
            with open(file_path, 'a') as csvfile:
                csv_writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                csv_writer.writerow(row)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('username', help='Github username')
    parser.add_argument('repo', help='User\'s repo', default='ALL', nargs='?')
    parser.add_argument('save_csv', default='save_csv', help='Set to "no_csv" if no CSV should be saved', nargs='?')
    parser.add_argument('-o', '--organization', default=None, help='Github organization')
    args = parser.parse_args()
    """ Run main code logic
    :param username: string - GitHub username, or username:password pair
    :param repo: string - GitHub user's repo name or by default 'ALL' repos
    :param save_csv: string - Specify if CSV log should be saved
    :optional:
	param -o, --organization: string - GitHub organization (if different from username)
    """

    str = args.username.strip()
    sub = str.split(':', 1 )
    len_sub = len(sub)

    username = sub[0].strip()
    if len_sub > 1:
        pw = sub[1].strip()
    else :
        pw = getpass.getpass('Password:')

    repo = args.repo.strip()
    organization = username
    if args.organization != None:
        organization = args.organization.strip()

    auth_pair = (username, pw)
    traffic_headers = {'Accept': 'application/vnd.github.spiderman-preview'}

    if repo == 'ALL':
        # By default iterate over all repositories
        repos_response = send_request('repos', organization, auth_pair).json()
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
                traffic_response = send_request('traffic', organization, auth_pair, repo, traffic_headers).json()
                print(json_to_table(repo, traffic_response, 'traffic'))
                clones_response = send_request('clones', organization, auth_pair, repo, traffic_headers).json()
                print(json_to_table(repo, clones_response, 'clones'))
                referrers_response = send_request('referrers', organization, auth_pair, repo, traffic_headers).json()
                print(json_to_table_referrers(repo, referrers_response))
                # Saving data
                if args.save_csv == 'save_csv':
                    store_csv(csv_file_name, repo, traffic_response, 'views')
                    store_csv(csv_file_name_clones, repo, clones_response, 'clones')
                    store_csv_referrers(csv_file_name_referrers, repo, referrers_response)
    else:
        # Or just request 1 repo
        traffic_response = send_request('traffic', organization, auth_pair, repo, traffic_headers).json()
        # Error handling in case of {'documentation_url': 'https://developer.github.com/v3', 'message': 'Not Found'}
        if traffic_response.get('message'):
            print(traffic_response['message'])
            return 'Code done.'
        print(json_to_table(repo, traffic_response, 'traffic'))
        clones_response = send_request('clones', organization, auth_pair, repo, traffic_headers).json()
        print(json_to_table(repo, clones_response, 'clones'))
        referrers_response = send_request('referrers', organization, auth_pair, repo, traffic_headers).json()
        print(json_to_table_referrers(repo, referrers_response))
        # Saving data
        if args.save_csv == 'save_csv':
            store_csv(csv_file_name, repo, traffic_response, 'views')
            store_csv(csv_file_name_clones, repo, clones_response, 'clones')
            store_csv_referrers(csv_file_name_referrers, repo, referrers_response)


if __name__ == '__main__':
    main()
