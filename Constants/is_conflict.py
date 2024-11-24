import psycopg2

class TimetableProcessor:
    def __init__(self, dbname="timetable", user="postgres", password="root", host="localhost", port="5432"):
        self.dbname = dbname
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.conn = None
        self.cursor = None

    def connect_to_database(self):
        try:
            self.conn = psycopg2.connect(
                dbname=self.dbname,
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port
            )
            self.cursor = self.conn.cursor()
            print("Connected to PostgreSQL database!")
        except Exception as e:
            print(f"Error connecting to the database: {e}")
            raise

    def insert_schedule(self, timetable, chromosome_name):
        try:
            for day, sections in timetable.items():
                for section, classes in sections.items():
                    for cls in classes:
                        self.cursor.execute("""
                            INSERT INTO schedule (chromosome, day, section, teacher_id, subject_id, classroom_id, time_slot)
                            VALUES (%s, %s, %s, %s, %s, %s, %s);
                        """, (chromosome_name, day, section, cls['teacher_id'], cls['subject_id'], cls['classroom_id'], cls['time_slot']))
            print(f"Schedule data for {chromosome_name} inserted successfully.")
        except Exception as e:
            self.conn.rollback()  # Rollback if any error occurs
            print(f"Error inserting schedule data: {e}")

    def detect_teacher_conflicts(self):
        self.cursor.execute("""
            SELECT s1.teacher_id, s1.day, s1.time_slot, COUNT(*)
            FROM schedule s1
            JOIN schedule s2
            ON s1.teacher_id = s2.teacher_id
               AND s1.time_slot = s2.time_slot
               AND s1.day = s2.day
               AND s1.chromosome != s2.chromosome
            GROUP BY s1.teacher_id, s1.day, s1.time_slot
            HAVING COUNT(*) > 1;
        """)
        return self.cursor.fetchall()

    def detect_classroom_conflicts(self):
        self.cursor.execute("""
            SELECT s1.classroom_id, s1.day, s1.time_slot, COUNT(*)
            FROM schedule s1
            JOIN schedule s2
            ON s1.classroom_id = s2.classroom_id
               AND s1.time_slot = s2.time_slot
               AND s1.day = s2.day
               AND s1.chromosome != s2.chromosome
            GROUP BY s1.classroom_id, s1.day, s1.time_slot
            HAVING COUNT(*) > 1;
        """)
        return self.cursor.fetchall()

    def truncate_schedule(self):
        self.cursor.execute("TRUNCATE TABLE schedule;")
        self.conn.commit()
        print("Schedule table truncated.")

    def close_connection(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        print("\nDatabase connection closed.")

    def process_schedules(self, timetable1, timetable2):
        try:
            self.connect_to_database()

            # Insert Chromosome data for both timetables
            self.insert_schedule(timetable1, "Week 1")
            self.insert_schedule(timetable2, "Week 2")

            # Check for Teacher Conflicts
            teacher_conflicts = self.detect_teacher_conflicts()

            # Check for Classroom Conflicts
            classroom_conflicts = self.detect_classroom_conflicts()

            # Return both conflicts as a dictionary
            return {
                "teacher_conflicts": teacher_conflicts,
                "classroom_conflicts": classroom_conflicts
            }

        finally:
            # Cleanup and close database connection
            self.truncate_schedule()
            self.close_connection()


# Example Timetables
chromosome1 = {
    "Monday": {
        "A": [
            {"teacher_id": "AP24", "subject_id": "SCS-501", "classroom_id": "R1", "time_slot": "9:00 - 9:55"},
            {"teacher_id": "SP06", "subject_id": "TCS-503", "classroom_id": "R1", "time_slot": "9:55 - 10:50"}
        ],
        "B": [
            {"teacher_id": "RS11", "subject_id": "TMA-502", "classroom_id": "R2", "time_slot": "9:00 - 9:55"}
        ]
    },
     "Tuesday": {
        "A": [
            {"teacher_id": "AP24", "subject_id": "SCS-501", "classroom_id": "R1", "time_slot": "9:00 - 9:55"}
        ],
        
    }
}

chromosome2 = {
    "Monday": {
        "A": [
            {"teacher_id": "AP24", "subject_id": "SCS-501", "classroom_id": "R1", "time_slot": "9:00 - 9:55"},
            {"teacher_id": "DP07", "subject_id": "TCS-503", "classroom_id": "R3", "time_slot": "9:00 - 9:55"}
        ],
        "B": [
            {"teacher_id": "RS11", "subject_id": "TMA-502", "classroom_id": "R2", "time_slot": "11:00 - 1:55"}
        ]
    },
    "Tuesday": {
        "A": [
            {"teacher_id": "DP07", "subject_id": "TCS-503", "classroom_id": "R3", "time_slot": "9:00 - 9:55"}
        ],
        "B": [
            {"teacher_id": "RS11", "subject_id": "TMA-502", "classroom_id": "R2", "time_slot": "9:00 - 9:55"},
            {"teacher_id": "AP24", "subject_id": "SCS-501", "classroom_id": "R1", "time_slot": "9:00 - 9:55"}
        ]
    }
}


# Example Usage
if __name__ == "__main__":
    timetable_processor = TimetableProcessor()
    conflicts = timetable_processor.process_schedules(chromosome1, chromosome2)

    # Display the result
    print("\nTeacher Conflicts:")
    for conflict in conflicts["teacher_conflicts"]:
        print(f"Teacher ID: {conflict[0]}, Day: {conflict[1]}, Time Slot: {conflict[2]}, Conflict Count: {conflict[3]}")

    print("\nClassroom Conflicts:")
    for conflict in conflicts["classroom_conflicts"]:
        print(f"Classroom ID: {conflict[0]}, Day: {conflict[1]}, Time Slot: {conflict[2]}, Conflict Count: {conflict[3]}")
