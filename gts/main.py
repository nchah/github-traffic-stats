#!/usr/bin/env python

import argparse
import csv
import os
from collections import OrderedDict
import datetime
import getpass
import requests
import psycopg2

# Globals
current_timestamp = str(datetime.datetime.now().strftime('%Y-%m-%d-%Hh-%Mm'))  # was .strftime('%Y-%m-%d'))
path = os.path.abspath(os.path.dirname(__file__))
csv_file_name = current_timestamp + '-traffic-stats.csv'
csv_file_name_clones = current_timestamp + '-clone-stats.csv'
csv_file_name_referrers = current_timestamp + '-referrer-stats.csv'


def send_request(resource, organization, auth, repo=None):
    """ Send request to specific Github API endpoint
    :param resource: string - specify the API to call
    :param organization: string - specify the repository organization if not owner by username
    :param auth: username:password separated string - if no password specified, interactive dialog used
    :param repo: string - if specified, the specific repository name
    :param headers: dict - if specified, the request headers
    :param params: dict - if specified, the parameters
    :return: response - GET request response, if a tuple then (response, header) responses
    """
    if resource == 'traffic':
        # GET /repos/:owner/:repo/traffic/views <- from developer.github.com/v3/repos/traffic/#views
        base_url = 'https://api.github.com/repos/'
        base_url = base_url + organization + '/' + repo + '/traffic/views'
        response = requests.get(base_url, auth=auth)
        return response
    elif resource == 'repos':
        # GET /user/repos <- from developer.github.com/v3/repos/#list-your-repositories
        base_url = 'https://api.github.com/users/'
        base_url = base_url + organization + '/repos'
        params = {'per_page': '100'}
        response = requests.get(base_url, auth=auth, params=params)
        headers = requests.head(base_url, auth=auth, params=params)
        return (response, headers)
    elif resource == 'clones':
        # GET /repos/:owner/:repo/traffic/clones <- from developer.github.com/v3/repos/traffic/#clones
        base_url = 'https://api.github.com/repos/'
        base_url = base_url + organization + '/' + repo + '/traffic/clones'
        response = requests.get(base_url, auth=auth)
        return response
    elif resource == 'referrers':
        # GET /repos/:owner/:repo/traffic/popular/referrers <- from developer.github.com/v3/repos/traffic/#list-referrers
        base_url = 'https://api.github.com/repos/'
        base_url = base_url + organization + '/' + repo + '/traffic/popular/referrers'
        response = requests.get(base_url, auth=auth)
        return response


def send_request_pagination(url, auth):
    """ Send request to specific Github API endpoint using pagination
    :param url: string - the URL from the "response.links" header
    :param auth: username:password separated string - if no password specified, interactive dialog used
    :param params: dict - if specified, the parameters
    :return: response - a tuple of (response, header) responses
    """
    params = {'per_page': '100'}
    response = requests.get(url, auth=auth, params=params)
    headers = requests.head(url)
    return (response, headers)


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


def store_db(db_config={}, repo='', json_response='', response_type=''):
   """ Store data for a given response into a corresponding table (described in create_table.sql):
   repo_name, date, views, unique_visitors/cloners
   :param db_config: dict - dictionary containing configuration information for database 
   :param repo: str - the GitHub repository name
   :param json_response: json - the json input
   :param response_type: str - 'views', 'clones', ''
   """

   # Connect to database 
   conn = psycopg2.connect(host=db_config['host'], port=db_config['port'], user=db_config['user'], password=db_config['password'], dbname=db_config['dbname']) 
   conn.autocommit = True
   cur = conn.cursor() 


   insert_repo_overview = "INSERT INTO repo_overview(Repo_Name, Result_Type, Uniques, Total) VALUES ('%s', '%s', %s, %s);"
   if response_type == 'views': # send data to `repo_overview` and `repo_visitors`
      __repo_overview_insert(cur, repo, response_type, json_response)
      __repo_views_insert(cur, repo, json_response[response_type])

   elif response_type == 'clones': # send data to `repo_overview` and `repo_clones`
      __repo_overview_insert(cur, repo, response_type, json_response)
      __repo_clones_insert(cur, repo, json_response[response_type])

   else: # send data to `repo_referrals` 
      __insert_repo_referrals(cur, repo, json_response) 

def __repo_overview_insert(cur=None, repo='', response_type='', json_response=None): 
   check_count = "SELECT COUNT(*) FROM repo_overview WHERE create_timestamp=DATE(NOW()) AND Repo_Name='%s' AND Result_Type='%s'" 
   insert_stmt = "INSERT INTO repo_overview(create_timestamp, Repo_Name, Result_Type, Uniques, Total) VALUES (DATE(NOW()), '%s', '%s', %s, %s);" 
   
   cur.execute(check_count % (repo, response_type)) 
   if cur.fetchall()[0][0] == 0:
      cur.execute(insert_stmt % (repo, response_type, json_response['uniques'], json_response['count'])) 
      
def __repo_views_insert(cur=None, repo='', json_response=None): 
   """INSERT data into repo_visitors table if row doesn't already exist 
   :param cur: psql - Connection to the PSQL in order to execute queries 
   :param repo: str - the GitHub repository name
   :param json_response: json - the json input
   """
   check_count = "SELECT COUNT(*) FROM repo_visitors WHERE create_timestamp='%s' AND Repo_Name='%s';"
   insert_stmt = "INSERT INTO repo_visitors(Repo_Name, create_timestamp, Uniques, Total) VALUES %s;"

   for obj in json_response: 
      cur.execute(check_count % (obj['timestamp'], repo))
      if cur.fetchall()[0][0] == 0: 
         insert_row = "\n\t('%s', '%s', %s, %s)" % (repo, obj['timestamp'], obj['uniques'], obj['count'])
         cur.execute(insert_stmt % insert_row)

def __repo_clones_insert(cur=None, repo='', json_response=None):
   """INSERT data into repo_clones table if row doesn't already exist 
   :param cur: psql - Connection to the PSQL in order to execute queries 
   :param repo: str - the GitHub repository name
   :param json_response: json - the json input
   """
   check_count = "SELECT COUNT(*) FROM repo_clones WHERE create_timestamp='%s' AND Repo_Name='%s';"
   insert_stmt = "INSERT INTO repo_clones(Repo_Name, create_timestamp, Uniques, Total) VALUES %s;"

   for obj in json_response: 
      cur.execute(check_count % (obj['timestamp'], repo))
      if cur.fetchall()[0][0] == 0: 
         insert_row = "\n\t('%s', '%s', %s, %s)" % (repo, obj['timestamp'], obj['uniques'], obj['count'])
         cur.execute(insert_stmt % insert_row)

def __insert_data_none_reference(repo, json_response=None)->str: 
   """ Based on repo and info in json_response, generate the rows to be inserted into table:
   repo_name, date, views, unique_visitors/cloners
   :param repo: str - the GitHub repository name
   :param json_response: json - the json input
   :return return_stmt: str - string containing the rows which will be inserted
   """

   return_stmt = ""
   i = 0 
   for obj in json_response:
      if i == len(json_response)-1: 
         return_stmt += "\n\t('%s', '%s', %s, %s);" % (repo, obj['timestamp'], obj['uniques'], obj['count'])
      else: 
         return_stmt += "\n\t('%s', '%s', %s, %s)," % (repo, obj['timestamp'], obj['uniques'], obj['count'])
      i += 1
   return return_stmt

def __insert_repo_referrals(cur=None, repo='', json_response=None): 
   """ Based on repo and info in json_response, generate the rows to be inserted into `repo_referrals`:
   repo_name, views, unique_visitors/cloners
   :param cur: psql - Connection to the PSQL in order to execute queries 
   :param repo: str - the GitHub repository name
   :param json_response: json - the json input
   """

   insert_stmt = "INSERT INTO repo_referrals(Repo_Name, Referral, Uniques, Total) VALUES('%s', '%s', %s, %s)" 
   update_stmt = "UPDATE repo_referrals SET Uniques=%s, Total=%s WHERE Repo_Name='%s' AND Referral='%s'"
   check_stmt = "SELECT COUNT(*) FROM repo_referrals WHERE Repo_Name='%s' AND Referral='%s'"
   for obj in json_response: 
      # Check whether or not a given referral exists 
      check_count = check_stmt % (repo, obj['referrer']) 
      cur.execute(check_count)
      count = cur.fetchall()[0][0]
      if count == 0: # If referral doesn't exists create a new one 
         insert = insert_stmt % (repo, obj['referrer'], obj['uniques'], obj['count'])
      else: # If referral exists update row 
         insert = update_stmt % (obj['uniques'], obj['count'], repo, obj['referrer']) 
      cur.execute(insert) 
 
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('username', help='Github username')
    parser.add_argument('repo', help='User\'s repo', default='ALL', nargs='?')
    parser.add_argument('save_csv', default='save_csv', help='Set to "no_csv" if no CSV should be saved, or "set_db" if data should be saved in database', nargs='?')
    parser.add_argument('-o', '--organization', default=None, help='Github organization')
    parser.add_argument('-print', '--print-screen', default='True', help='Print CSV results to screen', nargs='?') # print output to screen
    # Database config input 
    parser.add_argument('-hp', '--host',  default='127.0.0.1:5432', help='Set database host and port [127.0.0.1:5432]', nargs='?')
    parser.add_argument('-usr', '--db-user', default='root:""', help='Set database user and password [root:""]', nargs='?')
    parser.add_argument('-name', '--db-name',  default='test', help='Set database where data will be stored', nargs='?')
    args = parser.parse_args()
    """ Run main code logic
    :param username: string - GitHub username, or username:password pair
    :param repo: string - GitHub user's repo name or by default 'ALL' repos
    :param save_csv: string - Specify if CSV log should be saved
    :optional:
    param -hp, --host: string - Host and port to the database
    param -usr, --db-user: string - user and password to the database 
    param -name, --db-name: string - database name 
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
    # traffic_headers = {'Accept': 'application/vnd.github.spiderman-preview'}

    # database config info 
    db_config = {'host': args.host.strip().split(":")[0],
                 'port': int(args.host.strip().split(":")[1]),
                 'user': args.db_user.strip().split(":")[0],
                 'password': args.db_user.strip().split(":")[1],
                 'dbname': args.db_name.strip()
                }
    if repo == 'ALL':
        # By default iterate over all repositories
        repos = []
        repos_response = send_request('repos', organization, auth_pair)
        repos_json = repos_response[0]  # 1st element from requests.get()
        # print(repos_json.json())
        repos_links = repos_response[1].links  # 2nd element from requests.head()
        # Error handling in case of {'documentation_url':'https://developer.github.com/v3','message':'Not Found'}
        try:
            err_msg = repos_json.json().get('message')
            print(err_msg)
            return 'Code done.'
        except AttributeError:
            # Add the repos from the first request
            for repo in repos_json.json():
                repos.append(repo['name'])
            while repos_links.get('next'):
                print('Retrieving all repositories...')
                url = repos_links['next']['url']
                repos_response = send_request_pagination(url, auth_pair)
                for repo in repos_response[0].json():
                    repos.append(repo['name'])
                repos_links = repos_response[1].links
            # Iterate over collected repos list:
            #print(len(repos))  # commenting out the next 12 lines, correctly retrieves all org. repos
            for repo in repos:
                traffic_response = send_request('traffic', organization, auth_pair, repo).json()
                clones_response = send_request('clones', organization, auth_pair, repo).json()
                referrers_response = send_request('referrers', organization, auth_pair, repo).json()
                if args.print_screen == 'True': 
                   print(json_to_table(repo, traffic_response, 'traffic'))
                   print(json_to_table(repo, clones_response, 'clones'))
                   print(json_to_table_referrers(repo, referrers_response))
                # Saving data
                if args.save_csv == 'save_csv':
                    store_csv(csv_file_name, repo, traffic_response, 'views')
                    store_csv(csv_file_name_clones, repo, clones_response, 'clones')
                    store_csv_referrers(csv_file_name_referrers, repo, referrers_response)
                elif args.save_csv.strip() == 'set_db':
                    store_db(db_config, repo, traffic_response, 'views')
                    store_db(db_config, repo, clones_response, 'clones')
                    store_dbs(db_configs, repo, referrers_response)

                
    else: 
        # Or just request 1 repo
        traffic_response = send_request('traffic', organization, auth_pair, repo).json()
        # Error handling in case of {'documentation_url': 'https://developer.github.com/v3', 'message': 'Not Found'}
        if traffic_response.get('message'):
            print(traffic_response['message'])
            return 'Code done.'
        clones_response = send_request('clones', organization, auth_pair, repo).json()
        referrers_response = send_request('referrers', organization, auth_pair, repo).json()
        if args.print_screen == 'True': 
           print(json_to_table(repo, traffic_response, 'traffic'))
           print(json_to_table(repo, clones_response, 'clones'))
           print(json_to_table_referrers(repo, referrers_response)) 
        # Saving data
        if args.save_csv == 'save_csv':
            store_csv(csv_file_name, repo, traffic_response, 'views')
            store_csv(csv_file_name_clones, repo, clones_response, 'clones')
            store_csv_referrers(csv_file_name_referrers, repo, referrers_response)
        elif args.save_csv.strip() == 'set_db':
            store_db(db_config, repo, traffic_response, 'views')
            store_db(db_config, repo, clones_response, 'clones')
            store_db(db_config, repo, referrers_response)



if __name__ == '__main__':
    main()
