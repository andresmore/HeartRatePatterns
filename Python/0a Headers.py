import urllib.request
import wfdb
import psycopg2
from psycopg2.extensions import AsIs

def track_not_exists(cur, subject_id,recordDate,database):
    select_stament = 'select id from waveformFields where subject_id= %s and recorddate = %s and database = %s'
    cur.execute(select_stament,(int(subject_id),recordDate,database))
    return cur.fetchone() is None
def track_subject(cur,subject_id):
    select_stament= 'SELECT id FROM subjectwords WHERE subject_id= %s'
    cur.execute(select_stament,(int(subject_id),))
    return cur.fetchone() is None
def patient_dead(cur,subject_id):
    select_stament= 'SELECT dod FROM patients WHERE subject_id= %s'
    cur.execute(select_stament,(int(subject_id),))
    row = cur.fetchone()
    if(row is None or row[0] is None):
        return False
    else :
        print("row "+str(row))
        return True

conn = psycopg2.connect("dbname=mimic")
cur = conn.cursor()
table = "waveformFields"

cur.execute('''CREATE TABLE IF NOT EXISTS waveformFields
             (id serial PRIMARY KEY,
            comments character varying(255)[],
            fs integer, signame character varying(255)[],
            units character varying(255)[],
            subject_id integer,
            recordDate character varying(255),
            database character varying(50))''')

target_url = "https://physionet.org/physiobank/database/mimic2wdb/matched/RECORDS-waveforms"
data = urllib.request.urlopen(target_url) # it's a file like object and works just like a file
for line in data: # files are iterable
	line = str(line).replace('b\'','').replace('\'','').replace('\\n','')
	splited = line.split("/")
	carpeta,onda = line.split("/")
	subject_id = carpeta.replace('s','')
	recordDate = onda.replace(carpeta+"-","")
	if track_not_exists(cur,subject_id,recordDate,"mimic2") and track_subject(cur,subject_id) and patient_dead(cur,subject_id) :
		print("inserting: ",onda)
		try:
			sig, fields = wfdb.srdsamp(onda,pbdir='mimic2wdb/matched/'+carpeta, sampto=1)
			fields['subject_id'] = subject_id
			fields['recordDate'] = recordDate
			fields['database'] = "mimic2"
			columns = fields.keys()
			values = [fields[column] for column in columns]
			insert_statement = 'insert into '+table+' (%s) values %s'
			cur.execute(insert_statement, (AsIs(','.join(columns)), tuple(values)))
			conn.commit()
			print("inserted: ",onda)
		except ValueError as inst:
    			print("onda vacia")
conn.close()
