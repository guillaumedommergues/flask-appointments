# flask-appointments
A simple python-flask web application to take and cancel appointments. Ready to run locally or be deployed on the Google Cloud Platform. Front end is basic bootstrap - needs to be customized. 

## Prerequisites
Python 2.7
```
pip install -t lib -r requirements.txt
```

## Tests
```
python test.py
```

## Deployment
```
gcloud app deploy --project <your-project-name> app.yaml
```

## Concept
A customer goes to the main page of the application, selects the service (product) he is interested in, then the market (location) and date when he'd like to have the appointment. The customer is given several options. When the customer chooses one, he receives a confirmation by text message and the user (employee) an email invitation. 
The users (employees) can view and update their calendars. The managers can view the calendars of their employees. The admin users can change everything. 




