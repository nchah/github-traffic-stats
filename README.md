# github-traffic-stats

Get statistics on web traffic to your GitHub repositories.

This can be useful for monitoring the level of attention your GitHub repositories are receiving 

## Python CLI

Python CLI tool to get web traffic stats on the command line using the GitHub API.

### Dependencies

- Requests ([kennethreitz/requests](https://github.com/kennethreitz/requests))

There are a number of GitHub [libraries](https://developer.github.com/libraries/) for Python and other languages, although they may not support the Repository Traffic API (announced on August 15, 2016).

### Run

Run on the command line with either `python` or `python3`.

```
$ python python/github-stats.py 'nchah' 'github-traffic-stats'
Password:* (passwords are hidden)
github-traffic-stats
Date        Views   Unique visitors
Totals      146     64
2016-09-01  1       1
2016-09-05  1       1
2016-09-06  8       1
2016-09-07  5       1
2016-09-08  85      44
2016-09-09  22      9
2016-09-10  6       4
2016-09-11  6       4
2016-09-12  11      6
2016-09-13  1       1
...
*2016-08-08 traffic spikes after post on /r/coolgithubprojects

or
$ python python/github-stats.py 'nchah' '*ALL*'
Password:* (passwords are hidden)
...

```



## Documentation

A list of the references used for this project.

- [GitHub API](https://developer.github.com/v3/)
- [Preview the Repository Traffic API (August 15, 2016)](https://developer.github.com/changes/2016-08-15-traffic-api-preview/)

