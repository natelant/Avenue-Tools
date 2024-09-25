import sqlite3
import pandas as pd
from datetime import datetime, timedelta

def get_plans_data():
    # Connect to the SQLite database
    conn = sqlite3.connect('data/purdue_coordination_diagram.db')

    # SQL query to join plans with phases
    query = """
    SELECT DISTINCT p.*, ph.phase_number, ph.phase_description, ph.location_description
    FROM plans p
    LEFT JOIN phases ph ON p.phase_id = ph.phase_number AND p.location_identifier = ph.location_identifier
    """

    # Read the data into a pandas DataFrame
    df = pd.read_sql_query(query, conn)

    # Close the database connection
    conn.close()

    return df

def get_volume_data():
    # Connect to the SQLite database
    conn = sqlite3.connect('data/purdue_coordination_diagram.db')

    # SQL query to join volume_per_hour with plans, avoiding duplications
    query = """
    SELECT DISTINCT v.phase_id,
           v.location_identifier,
           (SELECT DISTINCT p.plan_description
            FROM plans p
            WHERE v.phase_id = p.phase_id 
              AND v.location_identifier = p.location_identifier
              AND v.timestamp >= p.start 
              AND v.timestamp < p.end
            LIMIT 1) as plan_description,
           (SELECT DISTINCT p.start
            FROM plans p
            WHERE v.phase_id = p.phase_id 
              AND v.location_identifier = p.location_identifier
              AND v.timestamp >= p.start 
              AND v.timestamp < p.end
            LIMIT 1) as start,
           SUM(v.value) / 4 as total_volume
    FROM volume_per_hour v
    GROUP BY v.phase_id, v.location_identifier, plan_description, start
    """

    # Read the data into a pandas DataFrame
    df = pd.read_sql_query(query, conn)

    # Close the database connection
    conn.close()

    return df

def get_raw_volumes():
    # Connect to the SQLite database
    conn = sqlite3.connect('data/purdue_coordination_diagram.db')

    # SQL query to join plans with phases
    query = """
    SELECT DISTINCT v.*
    FROM volume_per_hour v
    """

    # Read the data into a pandas DataFrame
    df = pd.read_sql_query(query, conn)

    # Close the database connection
    conn.close()

    return df

plans_df = get_plans_data()
volumes_df = get_volume_data()
raw_volumes_df = get_raw_volumes()

the_df = pd.merge(plans_df, volumes_df, on=['phase_id', 'location_identifier', 'plan_description', 'start'], how='inner')

# Filter volumes_df for specific criteria
volumes_df = volumes_df[(volumes_df['location_identifier'] == '7642') & 
                         (volumes_df['phase_id'] == 2) & 
                         (volumes_df['plan_description'] == 'Plan 1')]


print(volumes_df.dtypes)
print(volumes_df.head(30))





