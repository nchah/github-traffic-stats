github-traffic-stats
====================

.. image:: https://travis-ci.org/nchah/github-traffic-stats.svg?branch=master
    :target: https://travis-ci.org/nchah/github-traffic-stats

Get statistics on web traffic to your GitHub repositories.

Python CLI
----------

Python CLI tool to get web traffic stats on the command line using the
GitHub API.

A few use cases to show why this may be useful.

-  Checking the volume of traffic to all of your repos. Monitor sudden
   spikes in interest or any general patterns.
-  Storing the traffic stats for future reference.
-  Checking how often your code is cloned.

Installation
------------

::

    pip install github_traffic_stats

Dependencies
------------

-  Requests (`kennethreitz/requests`_)

Install the requirements by running: 

::

    pip install -r requirements.txt

There are a number of GitHub `libraries`_ for Python and other
languages, although they may not support the Repository Traffic API
(announced on August 15, 2016).

Usage
-----

::

    usage: gts [-h] username [repo] [save_csv] [-o]
       or: 
    usage: gts [-h] username:password [repo] [save_csv] [-o]

    positional arguments:
      username    Github username
      password    Github password for 'username', or access token
      repo        User's repo
      save_csv    Set to "no_csv" if no CSV should be saved

    optional arguments:
      -h, --help  show this help message and exit
      -o, --organization specify Github organization if different from username
       
Information on `Github Access Tokens`_.

Run
---

Run on the command line with either ``python`` or ``python3``.

::

    $ gts 'nchah' 'github-traffic-stats' 'save_csv'
    Password:* (passwords are hidden)
    > github-traffic-stats - Visitors
    Date        Views   Unique visitors
    Totals      125     36
    2017-07-16  1       1
    2017-07-17  10      2
    2017-07-19  11      4
    2017-07-20  12      5
    2017-07-21  3       3
    2017-07-22  1       1
    2017-07-23  1       1
    2017-07-24  17      6
    2017-07-25  32      5
    2017-07-26  1       1
    2017-07-27  1       1
    2017-07-28  6       4
    2017-07-29  26      5
    2017-07-30  3       1

    > github-traffic-stats - Git clones
    Date        Clones  Unique cloners
    Totals      5       5
    2017-07-17  1       1
    2017-07-24  2       2
    2017-07-26  1       1
    2017-07-29  1       1

    > github-traffic-stats - Referring sites
    Date        Views   Unique visitors
    Totals      44      27
    Google      33      24
    github.c... 11      3


    $ # Or to get stats on all of your repositories
    $ gts 'nchah' 'ALL' 'save_csv'
    Password:* (passwords are hidden)
    
    $ # Or if you are running on an organization repo (for example NREL's SAM repo) as a user with access
    $ gts 'nickdiorio' 'SAM' 'save_csv' -o 'NREL'
    Password:* (passwords are hidden)
    ...

Traffic data stored in CSV files with columns:

::

    repository_name, date, views, unique_visitors

| Separate CSVs are created for each run of the script.
| To merge and only preserve the unique data points, run:

::

    $ bash bash/merge-csv.sh [folder_with_CSVs]

Documentation
-------------

A list of the references used for this project.

-  `GitHub API`_
-  `Preview the Repository Traffic API (August 15, 2016)`_

.. _kennethreitz/requests: https://github.com/kennethreitz/requests
.. _libraries: https://developer.github.com/libraries/
.. _GitHub API: https://developer.github.com/v3/
.. _Preview the Repository Traffic API (August 15, 2016): https://developer.github.com/changes/2016-08-15-traffic-api-preview/
.. _Github Access Tokens: https://help.github.com/articles/creating-a-personal-access-token-for-the-command-line/

