# Building_a_SAS_NLP_API
Building an asynchronous NLP API using FastAPI on low level SAS Viya APIs and containerize for deployment

Assumptions: Access to Viya 3.5+ and VDMML 8.5+, Docker is installed on your machine. In order to run this application, follow the following steps:

The notebook is only present to show you how each of the CAS actions are called to perform the natural language processing processes. Feel free to run it on any Viya instance with the above conditions are met.

For deploying the microservice follow these steps:

Download the files of this repo to your local environment
cd into the higherlevel directory 
Then run the two followong commands at the terminal 

docker build -t myimage .        

docker run -d --name mycontainer -p 80:80 myimage

Then go to:
http://127.0.0.1:80/docs

Then test out the API and/or build an application on it/ integrate with an existing application!

Also please note that the list of strings passed int he body of the request should be divoid of any escape characters and should be enclosed in double quotation marks to be conformant with json formatting. For your convenience, use the following python code to create this list of strings from the text column of your dataframe. In this snippet, the dataframe is assigned to a variable 'df' and the text column in 'df' is 'text'.

strs = df.text.to_list()[:1000] /n
strs = ["'{}'".format(str(item).replace("\"", " ")) for item in strs]
