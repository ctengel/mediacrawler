from flask import Flask, render_template,g
app = Flask(__name__)
import FDB

def get_db():
    if 'db' not in g:
        g.db = FDB.DB('bolt://neo4j:test@localhost:7687', ('neo4j', 'test'))
    return g.db

@app.route("/")
def hello():
    return render_template('base.html', imgurl=[i for i in get_db().doit('MATCH (g:Person)-[:ACTS_IN]->(v:Video)<-[:INST_OF]-(j:Instance {type:"image"}) MATCH (v)<-[:INST_OF]-(m:Instance {type:"video"}) RETURN j.url, m.url, g.name ORDER BY g.name')])
