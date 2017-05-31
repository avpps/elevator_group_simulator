a = ''
import sqlite3
sqlite_file = ''

def create_tables(dbname):
    global a, sqlite_file
    
    a = dbname
    sqlite_file = '{s}.sqlite'.format(s=a)

    table_name1 = 'statPassengers'
    new_column1 = 'destFloor'
    new_column2 = 'arrTime'
    new_column3 = 'depTime'
    new_column4 = 'destTime'

    table_name2 = 'statCars'
    new_column21 = 'capacity'
    new_column22 = 'bypassCapacity'
    new_column23 = 'AINT'
    new_column24 = 'ACLF'

    table_name3 = 'overallStatistics'
    new_column31 = 'AINT'
    new_column32 = 'AWT'
    new_column33 = 'ATTD'
    new_column34 = 'ACLF'
    
    new_field = 'ID'
    field_type = 'INTEGER'
    field_type2 = 'FLOAT'

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    c.execute('CREATE TABLE {tn} ({nf} {ft} PRIMARY KEY, {cn1} {ft}, {cn2} {ft}, {cn3} {ft}, {cn4} {ft})'\
              .format(tn=table_name1, nf=new_field, ft=field_type,
                      cn1=new_column1, cn2=new_column2, cn3=new_column3, cn4=new_column4))

    c.execute('CREATE TABLE {tn} ({nf} {ft} PRIMARY KEY, {cn1} {ft}, {cn2} {ft}, {cn3} {ft}, {cn4} {ft})'\
              .format(tn=table_name2, nf=new_field, ft=field_type,
                      cn1=new_column21, cn2=new_column22, cn3=new_column23, cn4=new_column24))

    c.execute('CREATE TABLE {tn} ({nf} {ft} PRIMARY KEY, {cn1} {ft}, {cn2} {ft}, {cn3} {ft}, {cn4} {ft})'\
              .format(tn=table_name3, nf=new_field, ft=field_type,
                      cn1=new_column31, cn2=new_column32, cn3=new_column33, cn4=new_column34))

    
    conn.commit()
    conn.close()


def add_row_into_passenger_stat(iiID, iidestFloor, iiarrTime, iidepTime, iidestTime):
    table_name = 'statPassengers'
    id_column = 'ID'
    column_name = 'destFloor'
    column_name2 = 'arrTime'
    column_name3 = 'depTime'
    column_name4 = 'destTime'

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    c.execute("INSERT OR IGNORE INTO {tn} ({idf}, {cn}, {cn2}, {cn3}, {cn4}) VALUES ( {iID}, {idestFloor}, {iarrTime}, {idepTime}, {idestTime})"\
              .format(tn=table_name,
                      idf= id_column,
                      cn=column_name,
                      cn2=column_name2,
                      cn3=column_name3,
                      cn4=column_name4,

                      iID = iiID,
                      idestFloor = iidestFloor,
                      iarrTime = iiarrTime,
                      idepTime = iidepTime,
                      idestTime = iidestTime,
                      ))

    conn.commit()
    conn.close()


def add_col_wt_ttd():
    table_name = 'statPassengers'
    id_column = 'ID'
    col_wt = 'WT'
    col_ttd = 'TTD'
    col_type = 'INTEGER'
    new_column2 = 'arrTime'
    new_column3 = 'depTime'
    new_column4 = 'destTime'
    def_val = 0
    
    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    c.execute("ALTER TABLE {tn} ADD COLUMN '{cn}' {ct} DEFAULT '{df}'"\
              .format(tn=table_name, cn=col_wt, ct=col_type, df=def_val))
    c.execute("ALTER TABLE {tn} ADD COLUMN '{cn}' {ct} DEFAULT '{df}'"\
              .format(tn=table_name, cn=col_ttd, ct=col_type, df=def_val))

    c.execute('SELECT {idf} FROM {tn}'.format(idf=id_column, tn=table_name))
    all_id = c.fetchall()

    for i in all_id:
        for j in i:
            c.execute("UPDATE {tn} SET {cn}=({dt}-{at}) WHERE {idf}=({zd})"\
                      .format(tn=table_name, cn=col_wt, idf=id_column, at=new_column2, dt=new_column3, zd=j))
            c.execute("UPDATE {tn} SET {cn}=({dt}-{at}) WHERE {idf}=({zd})"\
                      .format(tn=table_name, cn=col_ttd, idf=id_column, at=new_column2, dt=new_column4, zd=j))
                      

    conn.commit()
    conn.close()

    
def add_row_cars_stat(iID, icapacity, ibypassCapacity, iACLF):
    table_name = 'statCars'
    id_column = 'ID'
    column_name = 'capacity'
    column_name2 = 'bypassCapacity'
    column_name3 = 'ACLF'

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    c.execute("INSERT OR IGNORE INTO {tn} ({idf}, {cn}, {cn2}, {cn3}) VALUES ( {iiID}, {iicapacity}, {iibypassCapacity}, {iiACLF})"\
              .format(tn=table_name, idf= id_column, cn=column_name, cn2=column_name2, cn3=column_name3,
                      iiID=iID, iicapacity=icapacity, iibypassCapacity=ibypassCapacity, iiACLF=iACLF))

    

    conn.commit()
    conn.close()

def create_car_table(carId):
    table_name = 'car{no}'.format(no=carId)
    column_name1 = 'departure'
    column_name2 = 'INT'
    column_name3 = 'load'
    field_type = 'FLOAT'

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    c.execute("CREATE TABLE {tn} ({cn1} {ft} PRIMARY KEY, {cn2} {ft}, {cn3} {ft})"\
              .format(tn=table_name, ft=field_type,
                      cn1=column_name1, cn2=column_name2, cn3=column_name3))

    conn.commit()
    conn.close()

def add_row_car_table(carId, dep, INT, loa):        
    table_name = 'car{no}'.format(no=carId)
    column_name1 = 'departure'
    column_name2 = 'INT'
    column_name3 = 'load'

    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    c.execute("INSERT OR IGNORE INTO {tn} ({cn1}, {cn2}, {cn3}) VALUES ({v1}, {v2}, {v3})"\
              .format(tn=table_name, cn1=column_name1, cn2=column_name2, cn3=column_name3,
                      v1=dep, v2=INT, v3=loa))

    conn.commit()
    conn.close()
              

def summarize():
    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()

    def cars_AINT():
        
        table_name0 = 'statCars'
        column_name01 = 'ID'
        column_name02 = 'AINT'
        c.execute("SELECT {cn} FROM {tn}".format(tn=table_name0, cn=column_name01))
        all_cars = c.fetchall()

        for l in all_cars:
            for car in l:
                table_name1 = 'car{sd}'.format(sd=car)
                column_name11 = 'INT'

                c.execute("SELECT {cn} FROM {tn}".format(tn=table_name1, cn=column_name11))
                all_departures = c.fetchall()
                sum_dep = 0
                for i in all_departures:
                    for j in i:
                        sum_dep += j

                c.execute("UPDATE {tn} SET {cn1}=({val}) WHERE {cn2}=({cid})"\
                          .format(tn=table_name0, cn1=column_name02,
                                  val=sum_dep/len(all_departures),
                                  cn2=column_name01, cid=car))
                conn.commit()

    def overallStatistics_update():
        
        table_name0 = 'overallStatistics'
        column_name00 = 'ID'
        column_name01 = 'AINT'
        column_name02 = 'AWT'
        column_name03 = 'ATTD'
        column_name04 = 'ACLF'

        table_name1 = 'statCars'
        column_name10 = 'ID'
        column_name11 = 'AINT'
        column_name12 = 'ACLF'       

        table_name2 = 'statPassengers'
        column_name20 = 'ID'
        column_name21 = 'WT'
        column_name22 = 'TTD' 

        c.execute("SELECT AVG({cn}) FROM {tn}".format(tn=table_name1, cn=column_name11))
        AINT = c.fetchone()
        c.execute("SELECT AVG({cn}) FROM {tn}".format(tn=table_name1, cn=column_name12))
        ACLF = c.fetchone()
        c.execute("SELECT AVG({cn}) FROM {tn}".format(tn=table_name2, cn=column_name21))
        AWT = c.fetchone()
        c.execute("SELECT AVG({cn}) FROM {tn}".format(tn=table_name2, cn=column_name22))
        ATTD = c.fetchone()

        c.execute("INSERT OR IGNORE INTO {tn} ({cn1}, {cn2}, {cn3}, {cn4}) VALUES ({v1}, {v2}, {v3}, {v4})"\
          .format(tn=table_name0, cn1=column_name01, cn2=column_name02, cn3=column_name03, cn4=column_name04,
                  v1=AINT[0], v2=AWT[0], v3=ATTD[0], v4=ACLF[0]))
        conn.commit()
        

    cars_AINT()
    overallStatistics_update()

   
