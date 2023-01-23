import psycopg2
import urllib.parse
import os
import logging as log

from reportBot.Models.UserModel import UserModel

urllib.parse.uses_netloc.append("postgres")
#url = urllib.parse.urlparse('postgres://osawfnidytbmgi:126714f9f3157ee10baa8046e48d287872788c8d1349ddba5dfd2a85de82d2a6@ec2-174-129-192-200.compute-1.amazonaws.com:5432/d79l0ugjdnfiac')
url = urllib.parse.urlparse(os.environ["DATABASE_URL"])



log.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=log.INFO)
logger = log.getLogger(__name__)

def save_user(user : UserModel):
    try:
        conn = psycopg2.connect(
            database=url.path[1:],
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port
        )
        cur = conn.cursor()
        #log.info("Searching reports in DB")
        query = "select * from users where id = %s;"
        cur.execute(query, [user.uid])        
        if cur.rowcount > 0:
            # Si esta no se graba y retorno que que ya existe
            conn.close()
            return "Ya existe un jugador con ese id."
        else:            
            query = "INSERT INTO users(id, name) VALUES (%s, %s) RETURNING name;"
            cur.execute(query, (user.uid, user.name))
            conn.commit()
            conn.close()
            return f"Jugador grabado. Id {user.uid} nombre de CW {user.name}"
    except Exception as e:
        log.info('No se grabo debido al siguiente error: '+str(e))
        conn.rollback()
        conn.close()
        return "Hubo un error grabando el usuario"

def get_users(uid = ""):
    try:
        users = []
        conn = psycopg2.connect(
            database=url.path[1:],
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port
        )
        cur = conn.cursor()
        if uid != "":
            query = """select   u.id, 
                                r.chat_wars_name,
                                r.guild, 
                                r.castle,
                                r.attack,
                                r.defense,
                                r.report_date from users u
                        inner join reports r ON u.name = r.chat_wars_name
                        where u.id = %s
                        order by report_date desc
                        limit 1;"""
        else:
            query = """select u.id, h.*
                        from users u
                        inner join
                        (
                                select distinct on (r.chat_wars_name) r.chat_wars_name as name,
                                r.guild, 
                                r.castle,
                                r.attack,
                                r.defense,
                                r.report_date
                                from reports r        
                                order by r.chat_wars_name, r.report_date desc
                        ) h using(name);"""
        cur.execute(query, [uid])
        if cur.rowcount > 0:
            log.info('Encontro resultados')
            # Si esta no se graba y retorno que que ya existe            
            for table in cur.fetchall():
                tabla_str = str(table) 
                #log.info(tabla_str)
                users.append(UserModel(table[0], table[1], table[2], table[3], table[4], table[5], table[6]))
            conn.close()
            return ["Usuarios", users]
        else:
            conn.close()            
            return ["No existe el usuario.", users]        
    except Exception as e:
        log.info('No se obtuvo correctamente debido a: '+str(e))
        conn.rollback()
        conn.close()
        return ["Hubo un error obteniendo el usuario avisar a @leviatas", users]



def get_users_with_missing_last_report(date = ""):
    try:
        log.info(date)
        string_date = date.strftime("%H:%M %d.%m")
        users = []
        conn = psycopg2.connect(
            database=url.path[1:],
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port
        )
        cur = conn.cursor()
        query = "select u.* from users u \
                        where not exists \
                        (select r.report_date from reports r \
                            where r.chat_wars_name = u.name and r.report_date = %s)"
        cur.execute(query, [date])
        if cur.rowcount > 0:
            for table in cur.fetchall():
                #tabla_str = str(table) 
                #log.info(tabla_str)
                users.append(UserModel(table[0], table[1]))
            conn.close()
            return [f"Usuarios que les faltan reportes de batalla {string_date}", users]
        else:
            conn.close()            
            return ["Ya todos mandaron el reporte.", users]        
    except Exception as e:
        log.info('No se obtuvo correctamente debido a: '+str(e))
        #onn.rollback()
        conn.close()
        return ["Hubo un error obteniendo el usuario avisar a @leviatas", users]

def delete_user(user : UserModel):
    try:
        conn = psycopg2.connect(
            database=url.path[1:],
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port
        )
        cur = conn.cursor()
        #log.info("Searching reports in DB")
        query = "select * from users where id = %s;"
        cur.execute(query, [user.uid, user.name])        
        if cur.rowcount > 0:
            # Si esta entonces lo borro
            query = "delete from users where id = %s;"
            cur.execute(query, (user.uid, user.name))
            conn.commit()
            return f"Jugador con Id {user.uid} y nombre de CW {user.name} borrado."
        else:
            return f"El jugador con Id {user.uid} y nombre de CW {user.name} no existe."
    except Exception as e:
        log.info('No se borro debido al siguiente error: '+str(e))
        conn.rollback()
        conn.close()
        return "Hubo un error borrando el usuario"
