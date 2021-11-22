# Profile Pages Final Project Part 2
#### David Corzo 20190432, Ian Jenatz 20190014, Anesveth Maatens 20190339

<br>

## Description
This project contains simple profile pages for users. Each user can fill out a 'form' with their details to fill out a profile page, which is stored in a database. After creating their profile, it is displayed and the user has an option to review and edit their information or search for the name of another user in a search engine. If the user exists, the user's profile page is loaded where you can review the information for this person. 

<br>

## Technologies
* Python as the back-end and Flask to host the app with multiple simple templates made of Bootstrap HTML and CSS.
* Kafka Server to send messages to Logstah containing the records with all relevant data to be stored in the databases.
* Logstash as part of the ELK stack, it sends the records it collects from Kafka Server to Elasticsearch as part of an index and simultaneously to a MySQL database.
* Elasticsearch as a NOSQL database with two nodes and the primary database for the application. The app attempts to first get the specific relevant record from Elasticsearch and only if it fails to collect does the app then check the cache or MySQL database.
* Kibana as a dashboard visualizer for the records stored in Elasticsearch.
* MySQL as a back-up database for the records that are stored in Elastisearch. If ES fails for some reason, MySQL allows the records to never be lost.
* Memecached as a simple Cache used in unison with MySQL to speed up the app's performance when ES fails. The app first checks this ES, then the cache and lastly the MySQL DB, if none of these work then the record does not exist.
* Flask-profiler as a profiler for Flask applications, this profiler does not support Elasticsearch correctly but all requests are still saved.


The combination of technologies make up a project structure represented by the following diagram:
![App Strucure](/projectStructure.jpg)


## Kibana Dashboard
The following is an example of the current Kibana Dashboard and some of the visualizations we found most interesting, Kibana dashboards can be accessed at http://localhost:5601/app/dashboards

![Dashboard Panel 1](/kibana/Dashboard_panel_1.jpeg)
![Dashboard Panel 2](/kibana/Dashboard_panel_2.jpeg)
![Dashboard Panel 3](/kibana/Dashboard_panel_3.jpeg)

## Flask Profiler
The following is an example of the data provided by the Flask Profiler which can be accessed at http://127.0.0.1:5000/flask-profiler

![Flask Profiler Example](/flask-profiler/example.jpg)
![Flask Profiler Example 2](/flask-profiler/example2.jpg)

## Jmeter
The complete jmeter file, along with all screenshots of the tool's analysis of the project both with and without a cache, can be found in the folder titled 'jmeter', to disable the cache for the project, simply change the variable 'cache' to 'False' in the python file ```profiles.py```.

<br>

### JMeter Test Conclusions:
* Non-edit routes such as /login, /profile, and /delete perform much better with a cache than without.
* Edit routes such as /edit and /editbg, that modify cache and the database values directly, perform worse when a cache is available.
* Though the cache did improve the overall speed of the project, the effect was relatively small. The project could theoretically perform worse if users decide to use the edit routes more often than non-edit routes. As such, implementing a cache isn't necessary for a project of this size, but bigger projects could definetly benefit.
* Due to the app's structure, utilizing Elasticsearch is the most performant method compared to Caching or pure MySQL. Caching is the second quickest while having both ES and the Cache disabled is the least performant.
* In the project, we utilize time.sleep() to handle Logstash's asynchronous nature which ultimately harms the app's performance when Elasticsearch fails but assures the best performance when Elasticsearch is functioning correctly.

These conclusions makes sense as the non-edit routes benefit from the speed of accessing a cache over accessing a database, while edit routes suffer from having additional operations to perform (both cache and database). Elasticsearch is still the quickest method however as the app calls time.sleep() less times when it is enabled.

<br>

## Project Requirements

### Packages:
```bash
pip install elasticsearch # Using version 7.15.0

pip install Flask # And all its dependencies

pip install flask-profiler # Using version 1.8.1

pip install python-memcached # Using version 1.59

pip install mysql-connector-python # Using version 8.0.27

pip install kafka-python # Using version 2.0.2
```
### Extra Requirements
This project uses ElasticSearch as a database and Kibana as a metric dashboard. We also utilize Kafka and Logstash, to install and run these, follow these tutorials: 
* Download ElasticSearch: https://www.elastic.co/downloads/elasticsearch
* Download Kibana: https://www.elastic.co/downloads/kibana 
* Download Kafka: https://shaaslam.medium.com/installing-apache-kafka-on-windows-495f6f2fd3c8
* Download Logstash: https://www.elastic.co/guide/en/logstash/current/installing-logstash.html (using Logstash pipelines with output isolator pattern https://www.elastic.co/guide/en/logstash/current/pipeline-to-pipeline.html)

<br>

This project also uses Memcached to store user data in a cache
* Download Memcached (on Windows): https://commaster.net/posts/installing-memcached-windows/ 

<br>

### Please Note
- *This project utilizes two ElasticSearch nodes, one is the master and the other holds replica shards so that data is exactly the same in both nodes, this behaviour can be replicated by unzipping the ElasticSearch zip file twice and running ElasticSearch on two separate terminals*
- *Debug mode must be on to access flask-profiler*
- *We don't ever directly interact with the process of storing records in Elasticsearch or MySQL, this process is handled by sending records to a Kafka Server which is picked up by Logstash who then automatically stores these records into Elasticsearch and MySQL using a user-defined pipelines.yml*

### Logstash Notes
The folowing code is a snippet of pipelines.yml the file we use as instructions for Logstash so that it knows where to receive input and how to send the collected records to Elasticsearch and MySQL:
```yml
# pipelines.yml

- pipeline.id: Kafka-process
  queue.type: persisted
  config.string: |
    input { 
      kafka {
        bootstrap_servers => "127.0.0.1:9092"
        topics => ["users"]
      }
    }
    filter {
      json {
        source => "message"
        remove_field => ["message"]
      }
    }
    output {
      pipeline { 
        send_to => ["ElasticDB", "MysqlDB", "Debugger"] 
      }
    }
- pipeline.id: ElasticDB-process
  queue.type: persisted
  config.string: |
    input { pipeline { address => "ElasticDB" } }
    output {
      elasticsearch {
        hosts => ["127.0.0.1:9200"]
        index => "logstash"
        document_id => "%{username}"
        action => "update"
        doc_as_upsert => true
        #user => "elastic"
        #password => "password"
      }
    }
- pipeline.id: MysqlDB-process
  queue.type: persisted
  config.string: |
    input { pipeline { address => "MysqlDB" } }
    output {
      jdbc {
        driver_jar_path => "C:\Program Files (x86)\MySQL\Connector J 8.0\mysql-connector-java-8.0.27.jar"
        # driver_class => "com.mysql.jdbc.Driver"
        connection_string => "jdbc:mysql://127.0.0.1:3306/profiles?user=admin&password=Datos2-Password123"
        statement => [ "REPLACE INTO users (username, password, profilepic, mood, description, email, firstName, lastName, country, birthday, occupation, relationship_status, mobile_number, phone_number, my_journal, bg) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", "username", "password", "profilepic", "mood", "description", "email", "firstName", "lastName", "country", "birthday", "occupation", "relationship_status", "mobile_number", "phone_number", "my_journal", "bg" ]
      }
    }
- pipeline.id: Terminal-Debugger
  queue.type: persisted
  config.string: |
    input { pipeline { address => "Debugger" } }
    filter {
      mutate {
        remove_field => ["password", "profilepic", "mood", "description", "email", "firstName", "lastName", "country", "birthday", "occupation", "relationship_status", "mobile_number", "phone_number", "my_journal", "bg"]
      }
    }
    output {
      stdout { codec => json }
    }
```