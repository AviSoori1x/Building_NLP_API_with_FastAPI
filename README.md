# Building_a_SAS_NLP_API
Building an asynchronous NLP API using FastAPI on low level SAS Viya APIs and containerize for deployment

Assumptions: Access to Viya 3.5+ and VDMML 8.5+, Docker is installed on your machine. In order to run this application, follow the following steps:

The notebook is only present to show you how each of the CAS actions are called to perform the natural language processing processes.

For deploying the microservice follow these steps:

Run the notebook from the first cell to the last. This creates and promotes the analytical base table and the final trained model as an ASTORE in CAS. Now go to the streamlitApp directory with all the files. Dockerfile is here.
Run the following commands at the commandline (I'm assuming you have Docker installed. If not, install Docker!)
First run at the terminal: docker build -f Dockerfile -t app:latest .
Then run: docker run -p 8501:8501 app:latest
Then test out your app at: http://localhost:8501/
Make sure both the model training (notebook) and the connection to the CAS server is to the same host with the permissions to access CAS tables in the global scope.
