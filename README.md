# Profile Pages Final Project Part 2
#### David Corzo 20190432, Ian Jenatz 20190014, Anesveth Maatens 20190339

<br>

## Description
This project contains simple profile pages for users. Each user can fill out a 'form' with their details to fill out a profile page, which is stored in a database. After creating their profile, it is displayed and the user has an option to review and edit their information or search for the name of another user in a search engine. If the user exists, the user's profile page is loaded where you can review the information for this person. 

<br>

## Kibana Dashboard
The following is an example of the current Kibana Dashboard and some of the visualizations we found most interesting, Kibana dashboards can be accessed at http://localhost:5601/app/dashboards

![Dashboard Panel 1](/kibana/Dashboard_Panel_1.jpeg)
![Dashboard Panel 2](/kibana/Dashboard_Panel_2.jpeg)
![Dashboard Panel 3](/kibana/Dashboard_Panel_3.jpeg)

## Flask Profiler
The following is an example of the data provided by the Flask Profiler which can be accessed at http://127.0.0.1:5000/flask-profiler

![Flask Profiler Example](/flask-profiler/example.jpg)
![Flask Profiler Example 2](/flask-profiler/example2.jpg)

## Jmeter
The complete jmeter file, along with all screenshots of the tool's analysis of the project both with and without a cache, can be found in the folder titled 'jmeter', to disable the cache for the project, simply change the variable 'cache' to 'False' in the python file ```profiles.py```.

<br>

## Project Requirements

### Packages:
```bash
pip install elasticsearch # Using version 7.15.0

pip install Flask # And all its dependencies

pip install flask-profiler # Using version 1.8.1

pip install python-memcached # Using version 1.59
```
### Extra Requirements
This project uses ElasticSearch as a database and Kibana as a metric dashboard, to install and run both of these, follow these tutorials: 
* Download ElasticSearch: https://www.elastic.co/downloads/elasticsearch
* Download Kibana: https://www.elastic.co/downloads/kibana 

<br>

This project also uses Memcached to store user data in a cache
* Download Memcached (on Windows): https://commaster.net/posts/installing-memcached-windows/ 

<br>

### Please Note
- *This project utilizes two ElasticSearch nodes, one is the master and the other holds replica shards so that data is exactly the same in both nodes, this behaviour can be replicated by unzipping the ElasticSearch zip file twice and running ElasticSearch on two separate terminals*
- *Debug mode must be on to access flask-profiler*