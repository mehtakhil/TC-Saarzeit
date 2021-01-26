from datetime import datetime
import pygame
import time
import pickle
import io
import mfrc522
import signal
import RPi.GPIO as GPIO
import math
import sqlite3
from sqlite3 import Error



# TOTEM  PARAMETERS
TotemDictionary = {
    "Left": ["Dr.Ale", "step2", "step3"],
    "Right": ["step4", "step5"],
    "Upstairs": ["Dr.Akhil"],
    "Downstairs": ["step7"],
    "Straightahead": ["Dr.Fauci"]
}

totem_identifer = 8
SUPERVISOR = False  # boolean that states whether a totem has supervisor privileges
HYPERVISOR = True

####### Constants ###########

wheretheyat = []
size = width, height = 1024, 600
speed = [100, 0]  # one coordinate at the time; random value to start with
black = 0, 0, 0

translate_dir_graph = {
    'Left': [-5, 0],
    'Right': [5, 0],
    'Upstairs': [0, 5],
    'Downstairs': [0, -5]
}

images_dictionary = {
    'Left': [pygame.image.load("/home/pi/Desktop/left_arrow.png"), pygame.image.load('/home/pi/Desktop/left_arrow.png').get_rect()],
    'Right': [pygame.image.load('/home/pi/Desktop/right_arrow.png'), pygame.image.load('/home/pi/Desktop/right_arrow.png').get_rect()],
    'Upstairs': [pygame.image.load('/home/pi/Desktop/walk_up.png'), pygame.image.load('/home/pi/Desktop/walk_up.png').get_rect()],
    'Downstairs': [pygame.image.load('/home/pi/Desktop/walk_down.png'), pygame.image.load('/home/pi/Desktop/walk_down.png').get_rect()]
}

STARTINGBLOCK = 4
INIT_TIME_BLOCK = 5
READER_TIME_BLOCK = 6
READER_IDENTIFIER_BLOCK = 8


"""
Dictionary that translates codes into strings that are used to instantiate badge class. it helps with
the RFID tags
we use number from 0-N for encoding point of interests.
from RFID tag you read a sequence of numbers. using those numbers as a key you can access this encoding dict, retrieve the complete 
list and instantiate the class so you can work with it. 0 works as a stop byte.
The encoding used in the tag is (seen as bytes, comma separates two consecutive bytes): current_step,key1,key2,...,keyN,0
after retrieving, you can create a list and instantiate badge
Now supervisor is able to indirectly to change the first byte within the same functions
"""

Encoding = {  # is the dual of the one aboveEncoding,with search by value on this one, you get the right item

    1: "Dr.Ale",
    2: "Dr.Akhil",
    3: "Dr.Smith",
    4: "Dr.Fauci",
    5: "Dr.Sphan",
    6: "Dr.TC",
    7: "Dr.Mehta",
    8: "Dr.Beatini"
}

Example_enc_service = {
    # encoding dict of each possible service in the hospital (hopefully less than 256, otherwise encoding will go
    # for each doctor
    0: "Electrocardiography",
    1: "general-visit"  # ecc ecc

}
####### Database commands ##########
TIME_ANALYTICS_DATABASE_NAME = 'time_database.db'
sql_create_time_analytics_table = """ CREATE TABLE IF NOT EXISTS TimeAnalytics (
                                identifier integer, 
                                init_date text,
                                init_time text,
                                init_totem text,
                                totem_identifier text,
                                time_diff text,
                                place text,
                                service text
                                ); """


sql_insert_time_data = "INSERT INTO TimeAnalytics VALUES (?,?,?,?,?,?,?,?)"


################# CLASSES and FUNCTIONS #####################


def create_connection(db_file):
    """ create a database connection to a SQLite database """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print(sqlite3.version)
        print("DB connected")
    except Error as e:
        print(e)

    return conn


class Badge:
    def __init__(self, lista):  # has to get a python list. the list comes from the other script
        self.current_step = lista.pop(0)-1  #new encoding, first element of list flags the current_step
        self.encoded_list = lista
        lista = Decode(Encoding,lista)
        self.steps = lista
        self.active_step = lista[self.current_step]  # this declaration assure each instance of the class have its own
        self.messages = str(
            # "Your destination is " + lista[self.current_step]) # to show on screen only if there is something here, e.g. errors
            "Your destination is Dr.Ale")
        if self.steps[0] == "Dr.Fauci":
            self.messages = "You finished your journey!"

    def update_step(self):
        if (self.current_step + 1 >= len(self.steps)):
            self.messages = "You finished your journey!"
            # assert len(self.messages == 2) #it is correct, still it doesn't work
            return
        else:
            self.current_step = self.current_step + 1
            self.active_step = self.steps[self.current_step]
            self.messages = "Your next step is " + self.active_step
        return

    def read_step(self):  #totems will call those two functions
        return self.active_step

    def read_messages(self):
        return self.messages


def Decode(encoding_dict,to_be_decoded):
    """
    function to recover the acutal list from Decoding dict
    :param encoding_dict:
    :param to_be_decoded:
    :return:
    """

    actual_list = list()
    for x in to_be_decoded:  #x is an unsigned
        actual_list.append(encoding_dict[x])    #x, no need for offset reg. inside badge it pops the first element
    return actual_list


def writeWhat(whichblock, datafromme):
    continue_reading = True

    # Capture SIGINT for cleanup when the script is aborted
    def end_read(signal, frame):
        global continue_reading
        print("Ctrl+C captured, ending read.")
        continue_reading = False
        GPIO.cleanup()
        exit()

    # Hook the SIGINT
    signal.signal(signal.SIGINT, end_read)

    # Create an object of the class MFRC522
    MIFAREReader = mfrc522.MFRC522()

    # This loop keeps checking for chips. If one is near it will get the UID and authenticate
    try:

        # Scan for cards
        (status, TagType) = MIFAREReader.MFRC522_Request(MIFAREReader.PICC_REQIDL)
        time.sleep(0.01)

        # If a card is found
        if status == MIFAREReader.MI_OK:
            print("Card detected")

        # Get the UID of the card
        (status, uid) = MIFAREReader.MFRC522_Anticoll()

        # If we have the UID, continue
        if status == MIFAREReader.MI_OK:
            # Print UID
            print("Card read UID: %s,%s,%s,%s" % (uid[0], uid[1], uid[2], uid[3]))

            # This is the default key for authentication
            key = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]

            # Select the scanned tag
            MIFAREReader.MFRC522_SelectTag(uid)
            time.sleep(0.001)

            # Authenticate
            status = MIFAREReader.MFRC522_Auth(MIFAREReader.PICC_AUTHENT1A, whichblock, key, uid)
            print("\n")
            if status != 0:
                return status  # quindi isok !=0 quindi riprovo altrove

            time.sleep(0.001)
            # Check if authenticated
            if status == MIFAREReader.MI_OK:

                # Variable for the data to write
                data = datafromme
                MIFAREReader.MFRC522_Write(whichblock, data)

                print("It now looks like this:")
                # Check to see if it was written
                roba = MIFAREReader.MFRC522_Read(whichblock)
                print(roba)

                # Stop
                MIFAREReader.MFRC522_StopCrypto1()

                # Make sure to stop reading for cards
                continue_reading = False
                global RI  # each of RI means 16 bytes
                RI += 1
                return 0
            else:
                print("Authentication error")


    finally:
        GPIO.cleanup()
        global wheretheyat
        wheretheyat.append(whichblock)
        return 0

def readWhat(whichblock):
    continue_reading = True

    def end_read(signal, frame):
        global continue_reading
        print("Ctrl+C captured, ending read.")
        continue_reading = False
        GPIO.cleanup()
        exit()
        # Hook the SIGINT

    signal.signal(signal.SIGINT, end_read)

    # Create an object of the class MFRC522
    MIFAREReader = mfrc522.MFRC522()
    try:
        while continue_reading:

            # Scan for cards
            (status, TagType) = MIFAREReader.MFRC522_Request(MIFAREReader.PICC_REQIDL)
            roba = []
            # If a card is found
            time.sleep(.001)
            # Get the UID of the card
            (status, uid) = MIFAREReader.MFRC522_Anticoll()

            # If we have the UID, continue
            if status == MIFAREReader.MI_OK:
                # Print UID
                #print("Card read UID: %s,%s,%s,%s" % (uid[0], uid[1], uid[2], uid[3]))
                # This is the default key for authentication
                key = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]

                # Select the scanned tag
                MIFAREReader.MFRC522_SelectTag(uid)
                time.sleep(.001)

                # Authenticate
                status = MIFAREReader.MFRC522_Auth(MIFAREReader.PICC_AUTHENT1A, whichblock, key, uid)

                # Check if authenticated
                if status == MIFAREReader.MI_OK:
                    roba = MIFAREReader.MFRC522_Read(whichblock)

                    # Stop
                    MIFAREReader.MFRC522_StopCrypto1()
                    continue_reading=False
                else:
                    print("Authentication error")
    finally:
        GPIO.cleanup()
        return roba


def searchByValue(dict_search, value):
    items = dict_search.items()
    for item in items:
        for val in item[1]:
            if val == value:
                return item[0]


################# ACTUAL WORK #####################

pygame.init()

screen = pygame.display.set_mode(size)  # from now on the screen shows what i want him to show
im = pygame.image.load("/home/pi/Desktop/intro_ball.gif")  # load in a variable
imrect = im.get_rect()  # pygame function that build a rect object with the same size of the image
imrect.centerx = width / 2
imrect.centery = height / 2

bg = pygame.image.load('/home/pi/Desktop/bgknd.jpg') #suppose same dimension of screen
bg = pygame.transform.scale(bg, size).convert()
bg_if_found = pygame.image.load('/home/pi/Desktop/bgknd.jpg') #suppose same dimension of screen
bg_if_found = pygame.transform.scale(bg_if_found, size).convert()


fonte = pygame.font.SysFont('Tahoma', 50, True, False)

text = fonte.render("Waiting for a valid card to be scanned...",True,black)
text_rect = text.get_rect()
text_rect.centerx = width/2
text_rect.y = 0


MIFAREReader = mfrc522.MFRC522()
while 1:  # main loop, everything in here

#    if (now.hour < 7):  # basically stop processor roughly from 18 to 7
 #       sleeptime = 7 - now.hour
  #      time.sleep(sleeptime * 3600)
   # if now.hour > 20:
    #    sleeptime = 31 - now.hour
     #   time.sleep(sleeptime * 3600)

    """""
    try to acknoweldge card presence
    if no, it sleeps 2 seconds and check again
    """
    #scan
    (status, TagType) = MIFAREReader.MFRC522_Request(MIFAREReader.PICC_REQIDL) #status = zero if detected
    print("Status is " + str(status))

    if status:   #if status != 0, no card is here -> show the appropriate text and keep on
        screen.blit(bg,(0,0))
        screen.blit(text,text_rect) #scrivo che sono in attesa
        pygame.display.flip() #set waiting screen and then wait
        time.sleep(2)
        continue

    """
        if yes, it reads it into a file   . i am here only if status == 0
    """

    BufferIn = bytearray()
    blockAdd = STARTINGBLOCK
    Block = bytearray(readWhat(blockAdd))  #do while analogue SHOULD bE MORE THAN ENOUGH
    keepRead = Block[0]                    #wrong condition. what about currentstep=0? I USE AN OFFSET FOR THE FIRS.
                                           #automatically adjusted in Badge class(i.e. if Block[0]=1 -> when call the constructor
                                           #it will be current_step = 1-1 =0 ok.
    print("The read block " + str(blockAdd) + " is " + str(Block) )
    while keepRead:
        for x in Block:
            if x == 0:
                keepRead=0
                break
            BufferIn.append(x)
        blockAdd = blockAdd+2 if (blockAdd+1-3) %4 == 0 else blockAdd+1
        Block = readWhat(blockAdd)
        print("The read block " + str(blockAdd) + " is " + str(Block) )
    
    """
    Reconstruct badge from BUfferIN
    """
    badge = Badge(BufferIn)        #i pass a list for initialization. Inside the class, it pops and Ddecode. should work fine

    # Read TIME blocks
    init_time_identifier = readWhat(INIT_TIME_BLOCK)
    time_list = readWhat(READER_TIME_BLOCK)
    time_list = [i for i in time_list if i != 0]
    identifier_list = readWhat(READER_IDENTIFIER_BLOCK)
    identifier_list = [i for i in identifier_list if i!=0]
    print("INIT TIME LIST is")
    print(init_time_identifier)
    print("TIME LIST is ")
    print(time_list)
    print("IDENTIFIER list is ")
    print(identifier_list)

    if init_time_identifier[0] == 0:
        service = init_time_identifier[7]
        current_time_identifier = list(map(int, time.strftime("%d, %m, %y, %H,%M,%S", time.localtime()).split(',')))
        current_time_identifier.append(totem_identifer)
        current_time_identifier.append(service)

        for i in range(len(current_time_identifier), 16):
            current_time_identifier.append(0)

        print("INIT TIME WRITTEN BY")
        print(current_time_identifier)
        writeWhat(INIT_TIME_BLOCK, bytes(current_time_identifier))

    else:

        # Write only when different Totem identifier seen
        if len(identifier_list) == 0 and init_time_identifier[6] == totem_identifer:
            print('DO NOTHING')

        elif len(identifier_list) !=0:
            if identifier_list[-1] != totem_identifer:
                initial_time = time.strptime(','.join([str(i) for i in init_time_identifier[:6]]), "%d,%m,%y,%H,%M,%S")
                time_now = time.localtime()
                time_diff_in_secs = time.mktime(time_now) - time.mktime(initial_time)
                time_diff_in_mins = math.ceil(time_diff_in_secs / 60)
                send_time_list = time_list.copy()
                send_time_list.append(time_diff_in_mins)
                send_identifier_list = identifier_list.copy()
                send_identifier_list.append(totem_identifer)

                for i in range(len(send_time_list), 16):
                    send_time_list.append(0)

                for i in range(len(send_identifier_list), 16):
                    send_identifier_list.append(0)

                print("TIME LIST WRITTEN BY")
                print(send_time_list)
                writeWhat(READER_TIME_BLOCK, bytes(send_time_list))

                print("IDENTIFIER LIST WRITTEN BY")
                print(send_identifier_list)
                writeWhat(READER_IDENTIFIER_BLOCK, bytes(send_identifier_list))


        else:

            initial_time = time.strptime(','.join([str(i) for i in init_time_identifier[:6]]), "%d,%m,%y,%H,%M,%S")
            time_now = time.localtime()
            time_diff_in_secs = time.mktime(time_now) - time.mktime(initial_time)
            time_diff_in_mins = math.ceil(time_diff_in_secs/60)
            send_time_list = time_list.copy()
            send_time_list.append(time_diff_in_mins)
            send_identifier_list = identifier_list.copy()
            send_identifier_list.append(totem_identifer)

            for i in range(len(send_time_list), 16):
                send_time_list.append(0)

            for i in range(len(send_identifier_list), 16):
                send_identifier_list.append(0)

            print("TIME LIST WRITTEN BY")
            print(send_time_list)
            writeWhat(READER_TIME_BLOCK, bytes(send_time_list))

            print("IDENTIFIER LIST WRITTEN BY")
            print(send_identifier_list)
            writeWhat(READER_IDENTIFIER_BLOCK, bytes(send_identifier_list))


# init_time_identifier = current_time.append(totem_identifier)
    """
    suactive step is a string that tells us where the patient has to go. I search the key associated with it in the totem and
    save it into direction, later to be displayed
    direction = searchByValue(dict_search=TotemDictionary, value=badge.active_step)
    message = badge.read_messages()  # to be displayed, it's a string. ITS SCOPE IS WHILE
    """
    if SUPERVISOR:

        """
        Script that dialogue with their system, if conditions are met it updates the active step
        """
        badge.update_step()
        """
        writebackthe new badge
        """
        blockAdd = STARTINGBLOCK                 #zero is used for key's own stuff. 1 CONTAINS N. OF BLOCKS to be read. <64 -> fits into 1 byte
        sendData = badge.encoded_list   #i have to prepend
        print("Send data is")
        print(sendData)
        sendData.insert(0,badge.current_step+1)  #prepend the current step and re-insert the Offset. ready to write back
        print(sendData)
        sendBlock = bytearray()
        for j in range(len(sendData)):

            if j % 16 == 0 and j!=0:  # i have to send it, i have 16 objs inn sendBlock
                isok = writeWhat(blockAdd, sendBlock)  # if isok 1 -> do it again. it works with negated logic
                print("Send data sent to blok " + str(blockAdd))
                while isok:
                    blockAdd = (blockAdd + 2) if (blockAdd + 1 - 3) % 4 == 0 else (blockAdd + 1)  # ready for next add
                    isok = writeWhat(blockAdd, sendBlock)  # if isok 1 -> do it again
                blockAdd = (blockAdd + 2) if (blockAdd + 1 - 3) % 4 == 0 else (blockAdd + 1)  # ready for next add
                sendBlock = bytearray()  # counterintuitive but python works like so, clear sendBlock outside loop

            sendBlock.append(sendData[j])  # oss : i have to update blockadd only iff i have 16 elements in sendBlock

        for k in range(len(sendBlock), 16):   #zero padding to 16
            sendBlock.append(0)
        writeWhat(blockAdd,sendBlock)
        print("Send data sent to blok " + str(blockAdd))

    if HYPERVISOR:
        # CONNECT TO TIME ANALYTICS DATABASE
        conn = create_connection(TIME_ANALYTICS_DATABASE_NAME)
        c = conn.cursor()
        c.execute(sql_create_time_analytics_table)
        conn.commit()
        # Read data recoreded and save it to Database
        init_time_identifier = readWhat(INIT_TIME_BLOCK)
        time_list = readWhat(READER_TIME_BLOCK)
        identifier_list = readWhat(READER_IDENTIFIER_BLOCK)


        print("INIT TIME LIST is")
        print(init_time_identifier)
        print("TIME LIST is ")
        print(time_list)
        print("IDENTIFIER list is ")
        print(identifier_list)

        if identifier_list:
            identifier_list = [i for i in identifier_list if i != 0]
            time_list = [i for i in time_list if i != 0]

        if not identifier_list:
            print("Nothing to write to database")
        else:
            print("Writing to local database")
            patient_identifier = 0
            init_date = '-'.join(str(i) for i in init_time_identifier[:3])
            init_time = ':'.join(str(i) for i in init_time_identifier[3:6])
            init_totem = str(init_time_identifier[6])
            service = Example_enc_service[init_time_identifier[7]]
            place = badge.steps[0]
            totem_identifiers = ','.join(str(i) for i in identifier_list)
            time_diff = ','.join(str(i) for i in time_list)
            data_to_write = (patient_identifier, init_date, init_time, init_totem, totem_identifiers, time_diff, place, service)
            print(data_to_write)
            c.execute(sql_insert_time_data, data_to_write)

            conn.commit()
            print("Writing done")
        conn.close() # Close database

### Temporary
    MIFAREReader.MFRC522_StopCrypto1()
    """""
    it has now to display the directions. Later to be better implemented with graphical library
    """

    message = badge.read_messages()  # updated to the new step
    text_indications = fonte.render(message, True, black)  # use fonte, display message embedded in badge
    text_indications_rect = text_indications.get_rect()
    text_indications_rect.centerx = width / 2
    text_indications_rect.y = 0

    if message == "You finished your journey!":
        start = time.time()
        end = start
        while end-start < 8:
            screen.blit(bg_if_found, (0, 0))  # bg sul quale si muove la freccia, rende obsoleto .fill
            screen.blit(text_indications, text_indications_rect)
            pygame.display.flip()  # update the screen
            end = time.time()

    else:

        direction = searchByValue(dict_search=TotemDictionary, value=badge.active_step)    #remember that python is not c++
        speed = translate_dir_graph[direction]  # now i have the correct speed
        chosen_im = images_dictionary[direction]  # has first the image and then the corresponding rect
        chosen_im[1].centerx = width / 2
        chosen_im[1].centery = height / 2  # show it at the middle of the screen

        """
        now i have to move it in a fancy way in the right direction, up to 5 seconds
        and show right message
        """
        text_indications = fonte.render(message,True,black) #use fonte, display message embedded in badge
        text_indications_rect = text_indications.get_rect()
        text_indications_rect.centerx = width/2
        text_indications_rect.y=0
        start = time.time()
        end = start

        while end-start < 8: #it last more or less 5 seconds + last instruction before starting again
            #print("End time is " + str(end - start))
            #time.sleep(.002) # not to make it move too fast,  to be finetuned later
            chosen_im[1].move_ip(speed)
            if chosen_im[1].left < 0 or chosen_im[1].right > width:
                #speed[0] = -speed[0]
                chosen_im[1].centerx = width / 2
                chosen_im[1].centery = height / 2  # show it at the middle of the screen

            if chosen_im[1].top < 0 or chosen_im[1].bottom > height:
                # speed[1] = -speed[1]
                chosen_im[1].centerx = width / 2
                chosen_im[1].centery = height / 2  # show it at the middle of the screen

            """
                    now i have to actually show it
            """

            #screen.fill(black)
            screen.blit(bg_if_found,(0,0)) #bg sul quale si muove la freccia, rende obsoleto .fill
            screen.blit(text_indications,text_indications_rect)
            screen.blit(chosen_im[0],chosen_im[1])  # source,dest -> draw a 'source surface'  onto this surface. i.e. draw berlusconi onto the imrect?
            pygame.display.flip()  # update the screen
            end = time.time() #each iteration i stopwatch the new time so that i can check the condition next

