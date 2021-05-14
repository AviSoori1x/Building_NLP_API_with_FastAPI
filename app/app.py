#Import the necessary packages and modules.
from fastapi  import FastAPI, File, Query
from pydantic import BaseModel 
from swat import CAS, options
import pandas as pd
import numpy as np
import json
from typing import List
from collections import Counter 
from _config import login 


#For the sample application, store credentials as environmental variables (would not recommend this in production!!)
#Connect to the CAS server and load the required action sets.

#Unpack login credentials from _config.py. Please do not do this in a production scenario. Use a .env file instead or better yet, if on Azure, Azure key vault
host_name, user_name, pass_word = login()

s = CAS(hostname=host_name, protocol='cas', 
            username=user_name, password=pass_word)
s.loadActionSet(actionSet="textMining")
s.loadActionSet(actionSet="sentimentAnalysis")
s.loadactionset('table')

#A function to convert a given list of strings to a CASTable with a unique ID and a text column as required by the text analytics CAS actions
def list_to_castable(text_list, table_name):
    docid = list(range(len(text_list)))
    senti_dict = {'docid' : docid,
                'text' : text_list}
    textpd = pd.DataFrame.from_dict(senti_dict)
    print(textpd)
    s.upload(textpd,casout={'name' : table_name, 'caslib' : 'public','replace' : True})

#A function to generate sentiment scores from text in an in memory CAS Table.
def get_sentiments(table_name, total_rows):
    s.sentimentAnalysis.applySent( casOut={"name":"out_sent", "replace":True}, 
                                docId="docid",
                                table={"name":table_name,'caslib':'public'},
                                text="text" )
    result = s.table.fetch(table={"name":"out_sent"},maxRows =total_rows,  to=total_rows)  
    text = s.table.fetch(table={"name":table_name,'caslib':'public'},maxRows =total_rows,  to=total_rows) 
    text_list = pd.DataFrame(dict(text)['Fetch']).text.to_list()
    result_pd = pd.DataFrame(dict(result)['Fetch'])
    result_pd['text'] = text_list
    result_pd['uid'] = [i for i in range(total_rows)]
    result_pd = result_pd[['_sentiment_','uid', 'text']]
    return result_pd

#A function to generate topic scores from text in an in memory CAS Table
def get_topics(table_name, total_rows, num_topics):
    num_topics = num_topics+1
    s.textMining.tmMine(docId="docid",                                          
    docPro={"name":"docpro", "replace":True, 'caslib' : 'public'},
    documents={"name":table_name, 'caslib' : 'public'},
    k=num_topics,
    nounGroups=False,
    numLabels=5,
    offset={"name":"offset", "replace":True, 'caslib' : 'public'},
    parent={"name":"parent", "replace":True, 'caslib' : 'public'},
    parseConfig={"name":"config", "replace":True, 'caslib' : 'public'},
    reduce=2,
    tagging=True,
    terms={"name":"terms", "replace":True, 'caslib' : 'public'},
    text="text",
    topicDecision=True,
    topics={"name":"topics", "replace":True, 'caslib' : 'public'},
    u={"name":"svdu", "replace":True, 'caslib' : 'public'}  ) 
    topics = s.table.fetch(table={ "name":"topics", 'caslib' : 'public'},maxRows =total_rows,  to=total_rows)
    topic_pd = pd.DataFrame(dict(topics)['Fetch'])
    topic_ids= topic_pd['_TopicId_'].to_list()
    Names = topic_pd['_Name_'].to_list()
    topic_map = {}
    i= 0
    for topic in topic_ids:
        topic_map[str(topic)] = Names[i]
        i+=1
        
    #Assigning each document to the most heavily weighted topic that the process discovered    
    docpro = s.table.fetch(table={ "name":"docpro", 'caslib' : 'public'},maxRows =total_rows,  to=total_rows)  
    docpro = pd.DataFrame(dict(docpro)['Fetch'])
    topics = []
    for i in range(total_rows):
        topics.append(topic_map[docpro.iloc[i][1:num_topics].idxmax().strip('_Col')+'.0'])
    text = s.table.fetch(table={"name":table_name,'caslib':'public'},maxRows =total_rows,  to=total_rows) 
    textpd = pd.DataFrame(dict(text)['Fetch'])
    textpd['topics']= topics
    textpd['uid'] = [i for i in range(total_rows)]
    textpd = textpd[['uid','text','topics']]
    return textpd

# initiate API
app = FastAPI(
    title="SAS Document Explorer",
    description="An NLP API that leverages lower level SAS Viya Text Analytics APIs to perform sentiment classification as well as topic modeling",
    version="0.1")


class InputListParams(BaseModel):
    text_list: List[str] = Query(None)
 
    
    

@app.post('/analyze_text')
def analyze_text(num_topics: int, total_rows: int, table_name: str, verbose: int,params:InputListParams):
    if len(params.text_list)>= total_rows:
        total_rows == total_rows 
    else:
        total_rows = len(params.text_list)
    cas_upload = list_to_castable(params.text_list, table_name)
    sentiments = get_sentiments(table_name, total_rows)
    topics = get_topics(table_name, total_rows, num_topics)
    result = pd.merge(sentiments, topics[['uid','topics']], on='uid', how='left').drop('uid', axis=1)
    #reordering columns 
    result = result[['text','_sentiment_', 'topics']]
    json_string = result.to_json()
    #Give aggregations of sentoiments and topic counts for convenience
    jsonified_result  = json.loads(json_string)
    sentiment_agg = dict(Counter(result._sentiment_.to_list()))
    topic_agg = dict(Counter(result.topics.to_list()))
    jsonified_result['sentiment_agg'] = sentiment_agg
    jsonified_result['topic_agg'] = topic_agg
    if verbose == 0: 
        agg_data = {}
        agg_data['sentiment_agg'] = sentiment_agg
        agg_data['topic_agg'] = topic_agg
        return agg_data
    return jsonified_result
