# TC-Saarzeit

This repository contains all the delivarables for the Tech Challenge (http://techchallenge.de/) organised by Tech Talents. We are team Saarzeit trying to solve the navigation problem in a hospital. 

We have built an end-to-end solution which contains an appointment scheduling system, NFC based navigation system and a dashboard for data analytics.

File descrprition and script commands (if any):
1. Appointment scheduler : A tkinter based appointment system to create appointment for different departments of hospital. 
Command for running the appointment scheduler: 

`python appointment_scheduler.py`

2. Raspberry Pi : A script for reading and writing NFC tags by connecting the NFC Reader MFRC522 to the Raspberry Pi. 
Running the totem script for NFC navigation. 

`cd Rapsberry_pi`
`python TotemScript.py`

3. Running the dash board application

`cd Analytic_Dashboard`
`python app.py`

4. database.db : SQL database for storing appointment information

5. time_database.db : SQL database for storing time data recorded by the NFC tag.

6. case_design.smt : 3D CAD model of the case for the prototype
