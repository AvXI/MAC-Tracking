import pandas as pd
from sklearn.cluster import KMeans
import psycopg2
from manuf import manuf

# Load the MAC address data from the database
conn = psycopg2.connect("dbname=mac_address_database user=postgres password=password")
cursor = conn.cursor()
cursor.execute("SELECT * FROM mac_addresses")
mac_data = pd.DataFrame(cursor.fetchall(), columns=['mac_address', 'date', 'user_id'])

# Preprocess the data
mac_data['date'] = pd.to_datetime(mac_data['date'])
mac_data['year'] = mac_data['date'].dt.year
mac_data['month'] = mac_data['date'].dt.month
mac_data['day'] = mac_data['date'].dt.day
mac_data['hour'] = mac_data['date'].dt.hour
mac_data.drop('date', axis=1, inplace=True)

# Add manufacturer information to the data
manuf_parser = manuf.MacParser()
def add_manufacturer(mac):
    try:
        return manuf_parser.get_manuf(mac)
    except:
        return None
mac_data['manufacturer'] = mac_data['mac_address'].apply(lambda x: add_manufacturer(x))

# Cluster the data using KMeans algorithm
X = mac_data[['year', 'month', 'day', 'hour']].values
kmeans = KMeans(n_clusters=5, random_state=42)
kmeans.fit(X)
labels = kmeans.predict(X)
mac_data['label'] = labels

# Save the results back to the database
cursor.execute("CREATE TABLE IF NOT EXISTS mac_address_clusters (mac_address VARCHAR(255), user_id VARCHAR(255), manufacturer VARCHAR(255), label INTEGER)")
for index, row in mac_data.iterrows():
    cursor.execute("INSERT INTO mac_address_clusters (mac_address, user_id, manufacturer, label) VALUES (%s, %s, %s, %s)", (row['mac_address'], row['user_id'], row['manufacturer'], row['label']))
conn.commit()
cursor.close()
conn.close()