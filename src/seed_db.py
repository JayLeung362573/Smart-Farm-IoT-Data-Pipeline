import psycopg2
import os

def seed():
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME", "smart_farm"), 
        user=os.getenv("DB_USER", "postgres"), 
        password=os.getenv("DB_PASSWORD", "3221"), 
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=os.getenv("DB_PORT", "5432")
    )
    cur = conn.cursor()

    # clean up existing metadata to allow new seeding
    cur.execute("TRUNCATE farms, fields, sensors RESTART IDENTITY CASCADE;")

    # Create 1 Farm, 2 Fields, and 500 Sensors
    cur.execute("INSERT INTO farms (owner_name, region) VALUES ('Jiawei Liang', 'Burnaby') RETURNING farm_id;")
    farm_id = cur.fetchone()[0]

    cur.execute("INSERT INTO fields (farm_id, name) VALUES (%s, 'North Field'), (%s, 'South Field') RETURNING field_id;", (farm_id, farm_id))
    field_ids = [row[0] for row in cur.fetchall()]

    for i in range(500):
        f_id = field_ids[0] if i < 250 else field_ids[1]
        cur.execute("INSERT INTO sensors (sensor_id, field_id) VALUES (%s, %s)", (i, f_id))

    conn.commit()
    print("Database seeded with 1 Farm, 2 Fields, and 500 Sensors.")
    cur.close()
    conn.close()

if __name__ == "__main__":
    seed()