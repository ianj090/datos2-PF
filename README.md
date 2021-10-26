# Profile Pages Final Project Requirements
## Part 2

### Package Requirements:
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

### Please Note
- *This project utilizes two ElasticSearch nodes, one is the master and the other holds replica shards so that data is exactly the same in both nodes, this behaviour can be replicated by unzipping the ElasticSearch zip file twice and running ElasticSearch on two separate terminals*