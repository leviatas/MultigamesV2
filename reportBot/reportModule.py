import psycopg2
import urllib.parse
import os
import logging as log

from reportBot.Models.ReporteModel import ReporteModel

urllib.parse.uses_netloc.append("postgres")
#url = urllib.parse.urlparse('postgres://osawfnidytbmgi:126714f9f3157ee10baa8046e48d287872788c8d1349ddba5dfd2a85de82d2a6@ec2-174-129-192-200.compute-1.amazonaws.com:5432/d79l0ugjdnfiac')
url = urllib.parse.urlparse(os.environ["DATABASE_URL"])



log.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=log.INFO)
logger = log.getLogger(__name__)

def save_report(report : ReporteModel):

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
        query = "select * from reports where report_date = %s and chat_wars_name = %s;"
        cur.execute(query, [report.report_date, report.chat_wars_name])        
        if cur.rowcount > 0:
            # Si esta no se graba y retorno que que ya existe
            return "Ya he grabado un reporte para esa batalla. Gloria a la alianza!!!"
        else:
            
            # def __init__(self, report_date, chat_wars_name, castle, guild, attack, \
            #                 defense, level, experience, gold, stock, lost_hp):

            query = "INSERT INTO reports(report_date, chat_wars_name, castle, guild, attack\
                                        ,defense, player_level, experience, gold, stock, lost_hp) \
                                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) \
                                                 RETURNING report_date;"
            cur.execute(query, (report.report_date, report.chat_wars_name, report.castle, report.guild, report.attack, \
                                report.defense, report.player_level, report.experience, report.gold, report.stock, \
                                    report.lost_hp))
            #log.info(cur.fetchone()[0])
            conn.commit()
            conn.close()
            return "Reporte grabado correctamente. Gloria a la alianza!!!"
    except Exception as e:
        log.info('No se grabo debido al siguiente error: '+str(e))
        conn.rollback()
        conn.close()
        return "Hubo un error grabando el reporte"

def get_reports(report_date = "", chat_wars_name = ""):
    try:
        reportes = []
        conn = psycopg2.connect(
            database=url.path[1:],
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port
        )
        cur = conn.cursor()
        query = "select * from reports where chat_wars_name = %s order by report_date desc;"
        cur.execute(query, [chat_wars_name])
        if cur.rowcount > 0:
            log.info('Encontro resultados')
            # Si esta no se graba y retorno que que ya existe            
            for table in cur.fetchall():
                #bot.send_message(cid, len(str(table)))
                #tabla_str = str(table) 
                #log.info(tabla_str)
                # def __init__(self, report_date, chat_wars_name, castle, guild, attack, \
                # defense, player_level, experience, gold, stock, lost_hp):
                reporte = ReporteModel(table[0], table[1], table[3], table[2],table[4],\
                                        table[5], table[6], table[7], table[8], table[9], table[9])            
                reportes.append(reporte)
            return ["Reportes", reportes]
        else:            
            return ["No hay reportes.", reportes]
        conn.close()
    except Exception as e:
        log.info('No se obtuvo correctamente debido a: '+str(e))
        conn.rollback()
        conn.close()
        return ["Hubo un error obteniendo los reportes avisar a @leviatas", reportes]