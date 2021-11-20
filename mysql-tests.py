import mysql.connector as mysql # used for connecting to MySQL

# Connect to MySQL Database
db = mysql.connect(
    host = "localhost",
    user = "admin", # Defined when downloading MySQL
    passwd = "Datos2-Password123", # Defined when downloading MySQL
    database = "profiles" # Comment out if db not created yet
)
cursor = db.cursor(dictionary=True, buffered=True) # cursor is used to create queries and read returns

# Create database, not needed if already created
# cursor.execute("CREATE DATABASE profiles")

cursor.execute("SHOW DATABASES") # Lists all dbs, some are created on setup, only use our db created above
databases = cursor.fetchall()
print(databases)

# Create table, not needed if already created
# cursor.execute("""
# CREATE TABLE users(
#     username VARCHAR(250),
#     password VARCHAR(250),
#     profilepic VARCHAR(250),
#     mood VARCHAR(250),
#     description VARCHAR(250),
#     email VARCHAR(250),
#     firstName VARCHAR(250),
#     lastName VARCHAR(250),
#     country VARCHAR(250),
#     birthday VARCHAR(250),
#     occupation VARCHAR(250),
#     relationship_status VARCHAR(250),
#     mobile_number VARCHAR(250),
#     phone_number VARCHAR(250),
#     my_journal VARCHAR(1000),
#     bg VARCHAR(250)
# )
# """) # We pass all vars as strings since they won't be mutated here anyway

#
# cursor.execute("ALTER TABLE users MODIFY username VARCHAR(250) PRIMARY KEY") # Shows all tables in our db
# tables = cursor.fetchall()
# print(tables)

cursor.execute("SHOW TABLES") # Shows all tables in our db
tables = cursor.fetchall()
print(tables)

# cursor.execute("DESCRIBE users") # Shows all tables in our db
# tables = cursor.fetchall()
# print(tables)

print("\nusers")
cursor.execute("SELECT * FROM users") # Shows all tables in our db
records = cursor.fetchall()

count = 0
for record in records:
    print(record)
    count += 1
print("\nAmount of records:", count)



# from kafka import KafkaConsumer # Kafka Server
# import json # used for kafka loading

# TOPIC_NAME = "users" # topic is similar to channel name, says what topic it should send to, logstash listens to the same topic
# KAFKA_SERVER = "127.0.0.1:9092"

# consumer = KafkaConsumer(
#     TOPIC_NAME,
#     bootstrap_servers=KAFKA_SERVER,
#     auto_offset_reset='earliest',
#     enable_auto_commit=True,
#     group_id='my-group',
#     value_deserializer=lambda x: json.loads(x.decode('utf-8')))

# for message in consumer:
#     message = message.value
#     print(message)