import sys
import pandas as pd
import xml.etree.ElementTree as ET
import datetime
import re
import nltk
import json
import RulesEngine as RU

from IPython.display import display, HTML

DATASET_FILE="data/EMAIL-INBOUND-SIN-CASOS-200.xlsx"
DATASET_NAME='email_19sep_20ene'

RULES_FILE="email_ruleset_1.json"

flag_debug=False

engine1 = RU.RulesEngine( flag_conda = True, name='engine1')
# engine1 = RulesEngine( flag_conda = True )

engine1.ruleset_load( RULES_FILE )
# engine1._debug_()

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

df = pd.read_excel(DATASET_FILE, encoding='utf-8' )
df.rename(columns={u'Interacción: Fecha de creación': 'Recibido', u'Correo electrónico': 'From', u'Interacción: Nombre Interacción': 'Asunto', u'Número coincidencias palabras clave': 'Num_Keywords'}, inplace=True)
df['__CLASIFICADO']=0
df.count()
# df.head()

maxRows=0
if ( maxRows <= 0):
    engine1.set_dataframe(df,DATASET_NAME)
else:
    engine1.set_dataframe(df.head(maxRows),DATASET_NAME)

# IMPORTANT: ADD THE '#RULE' COLUMN!
engine1.my_df['#RULE']=''

engine1.my_df.count()

engine1.evaluate( )

engine1.my_df.groupby(['#RULE']).size()

(100 * engine1.my_df.groupby(['#RULE']).size() / len(engine1.my_df.index))

engine1.my_df.groupby(['#CASE']).size()
