import tkinter as tk
from tkinter import *
from tkinter import ttk
import calendar
import datetime
import time
from tkscrolledframe import ScrolledFrame
import sqlite3
from sqlite3 import Error
import signal
# import RPi.GPIO as GPIO
# import mfrc522


# TOTEM  PARAMETERS

def searchByValue(dict_search, value):
    items = dict_search.items()
    for item in items:
        for val in item[1]:
            if val == value:
                return item[0]


def searchKeyByValue(dict_search, value):
    items = dict_search.items()
    for item in items:
        if value == item[1]:
            return item[0]

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

docs_in_dep = {
    "Cardiology": ["Dr.Ale", "Dr.Akhil"],
    "Neurology": ["Dr.Smith", "Dr.Fauci"],
    "Orthopaedics": ["Dr.Sphan", "Dr.TC"],
    "Pediatrician": ["Dr.Mehta", "Dr.Beatini"]
}

####### Constants #######

RI = 0
LENCTRL = 0
wheretheyat = []
STARTINGBLOCK = 4
INIT_TIME_BLOCK = 5
READER_TIME_BLOCK = 6
READER_IDENTIFIER_BLOCK = 8

days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
retrieve_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

####### Database commands #######

DATABASE_NAME = 'database.db'
sql_create_appointments_table = """ CREATE TABLE IF NOT EXISTS Appointments (
                                identifier integer, 
                                firstname text,
                                surnmae text,
                                number text,
                                time text,
                                date text,
                                disabled integer,
                                sms integer,
                                department text,
                                place text,
                                service text
                                ); """
sql_insert_appointment = "INSERT INTO Appointments VALUES (?,?,?,?,?,?,?,?,?,?,?)"
sql_search_query = "SELECT * FROM Appointments WHERE date=? AND time=? AND place=?"
sql_search_date_query = "SELECT * FROM Appointments WHERE date=?"
sql_all_appointments_query = "SELECT * FROM Appointments ORDER BY date, time"


############## TOTEM BADGE INIT VARIABLES ####################}


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


############### TOTEM BADGE INIT FUNCTIONS #######################
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


def Decode(encoding_dict, to_be_decoded):
    actual_list = list()
    for x in to_be_decoded:  # x is an unsigned
        actual_list.append(encoding_dict[x])  # x, no need for offset reg. inside badge it pops the first element
    return actual_list


class Badge:
    def __init__(self, lista):  # has to get a python list. the list comes from the other script
        self.current_step = lista.pop(0) - 1  # new encoding, first element of list flags the current_step
        self.encoded_list = lista
        lista = Decode(Encoding, lista)
        self.steps = lista
        self.active_step = lista[0]  # this declaration assure each instance of the class have its own
        self.messages = str(
            "Your first step is " + lista[0])  # to show on screen only if there is something here, e.g. errors

    def update_step(self):
        if (self.current_step + 1 >= len(self.steps)):
            self.messages = ["You finished your journey!"]
            # assert len(self.messages == 2) #it is correct, still it doesn't work
            return
        else:
            self.current_step = self.current_step + 1
            self.active_step = self.steps[self.current_step]
            self.messages = ["Your next step is " + self.active_step]
        return

    def read_step(self):  # totems will call those two functions
        return self.active_step

    def read_messages(self):
        return self.messages


############################################################

class calendardoc():

    def __init__(self, root):
        self.parent = root
        self.parent.configure(bg="gray12")
        self.wid = []
        self.cal = calendar.TextCalendar(calendar.SUNDAY)  # from python libs
        self.year = datetime.date.today().year
        self.month = datetime.date.today().month
        self.wid = []

        # self.day_selected = 1
        self.day_selected = datetime.date.today().day

        self.month_selected = self.month
        self.year_selected = self.year

        # self.date_selected = ''
        self.date_selected = str(self.day_selected) + "-" + str(self.month_selected) + "-" + str(self.year_selected)

        self.day_name = ''
        self.selection_btn = None
        self.COLOR_OF_CALENDAR_ARROWS = "dodger blue"
        self.COLOR_OF_CALENDAR_LABEL = "dodger blue"
        self.COLOR_OF_DAY_BUTTONS = "grey74"
        self.parent.geometry("1080x600")

        self.setup(self.year, self.month)

    # Resets the buttons
    def clear(self):
        for w in self.wid[:]:
            w.grid_forget()
            # w.destroy()
            self.wid.remove(w)

    def go_next(self):
        if self.month < 12:
            self.month += 1
        else:
            self.month = 1
            self.year += 1

        # self.selected = (self.month, self.year)
        self.clear()
        self.setup(self.year, self.month)

    def setup(self, y, m):
        # Tkinter creation
        left = tk.Button(self.parent, text='<', command=self.go_prev, bg=self.COLOR_OF_CALENDAR_ARROWS)
        self.wid.append(left)
        left.grid(row=0, column=1)

        header = tk.Label(self.parent, height=2, bg=self.COLOR_OF_CALENDAR_LABEL,
                          text='{}   {}'.format(calendar.month_abbr[m], str(y)))
        self.wid.append(header)
        header.grid(row=0, column=2, columnspan=3)

        right = tk.Button(self.parent, text='>', command=self.go_next, bg=self.COLOR_OF_CALENDAR_ARROWS)
        self.wid.append(right)
        right.grid(row=0, column=5)
        days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        for num, name in enumerate(days):
            t = tk.Label(self.parent, text=name[:3], bg=self.COLOR_OF_CALENDAR_LABEL)
            self.wid.append(t)
            t.grid(row=1, column=num)

        for w, week in enumerate(self.cal.monthdayscalendar(y, m), 2):
            for d, day in enumerate(week):
                if day:
                    d1 = datetime.date(y, m, day)
                    d2 = datetime.date.today()
                    if (d1 >= d2):
                        b = tk.Button(self.parent, width=1, height=1, bg=self.COLOR_OF_DAY_BUTTONS, text=day,
                                      command=lambda day=day: self.selection(day), state=NORMAL, )
                    else:
                        b = tk.Button(self.parent, width=1, height=1, bg=self.COLOR_OF_DAY_BUTTONS, text=day,
                                      command=lambda day=day: self.selection(day), state=DISABLED, )

                    self.wid.append(b)
                    b.grid(row=w, column=d, ipadx=10, ipady=10)

        sep = tk.Label(self.parent, height=1, width=0, bg="gray12", text="")
        self.wid.append(sep)
        sep.grid(row=8, column=0)

        day_idx = calendar.weekday(self.year_selected, self.month_selected, self.day_selected)
        self.day_name = retrieve_days[day_idx]
        self.selection_btn = tk.Label(self.parent, height=2, bg=self.COLOR_OF_CALENDAR_LABEL, text='{} {} {} {}'.format(
            self.day_name, calendar.month_name[self.month_selected], self.day_selected, self.year_selected))
        self.selection_btn.grid(row=9, column=2, columnspan=3)

        show_all_app_btn = tk.Button(self.parent, height=2, bg=self.COLOR_OF_CALENDAR_LABEL, text='Appointments',
                                     command=self.show_all_appointments)
        self.wid.append(show_all_app_btn)
        show_all_app_btn.grid(row=9, column=0, columnspan=2)

        create_appn_btn = tk.Button(self.parent, height=2, bg=self.COLOR_OF_CALENDAR_LABEL, text='Create Appointment',
                                    command=self.choosedep)
        self.wid.append(create_appn_btn)
        create_appn_btn.grid(row=9, column=1, columnspan=2)

        create_tag = tk.Button(self.parent, height=2, bg=self.COLOR_OF_CALENDAR_LABEL, text='Create TAG',
                               command=self.show_appointments)
        self.wid.append(create_tag)
        create_tag.grid(row=9, column=5, columnspan=2)

        footer = tk.Label(self.parent, height=1, width=0, bg="gray12", text="")
        self.wid.append(footer)
        footer.grid(row=10, column=0)

        for col in range(7):
            self.parent.grid_columnconfigure(col, weight=1)
            self.parent.grid_rowconfigure(col, weight=1)

    def show_all_appointments(self):

        showAllAppointments(self)

    def show_appointments(self):
        """Changes the button's color"""

        showAppointments(self.date_selected)

    def go_prev(self):
        if self.month > 1:
            self.month -= 1
        else:
            self.month = 12
            self.year -= 1
        # self.selected = (self.month, self.year)
        self.clear()
        self.setup(self.year, self.month)

    def kill_and_save(self):
        self.parent.destroy()

    def choosedep(self):
        chooseDep(self.day_selected, self.month_selected, self.year_selected)

    def selection(self, day):
        # month_used = self.month
        # year_used = self.year
        # # self.parent.iconify()
        # choosetime(day, month_used, year_used)
        # self.parent.deiconify()
        # self.parent.tkraise()
        # self.day_name = name
        self.month_selected = self.month
        self.year_selected = self.year
        self.day_selected = day

        #
        # sel = tk.Label(self.parent, height=2, bg=self.COLOR_OF_CALENDAR_LABEL, text='')
        # self.wid.append(sel)
        # sel.grid(row=8, column=0, columnspan=7)

        day_idx = calendar.weekday(self.year_selected, self.month_selected, self.day_selected)
        self.day_name = retrieve_days[day_idx]
        # self.selection_btn = tk.Label(self.parent, height=2, bg=self.COLOR_OF_CALENDAR_LABEL, text='{} {} {} {}'.format(
        #     self.day_name, calendar.month_name[self.month_selected], self.day_selected, self.year_selected))
        # self.selection_btn.grid(row=8, column=0, columnspan=7)
        self.selection_btn.configure(text='{} {} {} {}'.format(
            self.day_name, calendar.month_name[self.month_selected], self.day_selected, self.year_selected))

        self.date_selected = str(self.day_selected) + "-" + str(self.month_selected) + "-" + str(self.year_selected)

        # self.parent.iconify()
        # chooseDep(self.day_selected, self.month_selected, self.year_selected)
        # choosetime(self.day_selected, self.month_selected, self.year_selected)
        # self.parent.deiconify()
        # self.parent.tkraise()


class chooseDep():
    def __init__(self, day, month, year):
        self.day_selected = day
        self.month_selected = month
        self.year_selected = year
        self.dep_selected = None
        self.root_ch = tk.Tk()
        self.root_ch.configure(bg="grey12")
        self.root_ch.grid_columnconfigure(0, weight=1)
        # root_ch.grid_rowconfigure(1,weight=1)
        self.label = Label(self.root_ch, text="CHOOSE THE DEPARTMENT TO BE DISPLAYED", fg="black", bg="dodger blue")
        self.label.grid(row=0, pady=30, sticky="nsew")
        self.root_ch.title("CHOOSE YOUR DEPARTMENT")
        self.scroll = Scrollbar(self.root_ch)
        self.lista = tk.Listbox(self.root_ch,
                                bg="gray")  # Use sticky=tk.N+tk.S to stretch the widget vertically but leave it centered horizontally.
        self.lista.configure(yscrollcommand=self.scroll.set)  # dimensioni dovrebbero andare apposto con sticky
        self.lista.insert(END, "Cardiology")
        self.lista.insert(END, "Neurology")
        self.lista.insert(END, "Orthopaedics")
        self.lista.insert(END,
                          "Pediatrician")  # Python lambda functions, also known as anonymous functions, are inline functions that do not have a name.
        # They are created with the lambda keyword. This is part of the functional paradigm built-in Python.
        self.lista.bind('<Double-1>', self.go)
        self.lista.grid(row=1, column=0, sticky="nsew")
        self.select = Button(self.root_ch, text="SELECT", command=self.select, fg="black", bg="dodger blue")
        self.select.grid(row=2, column=0, sticky="n")
        # self.chooseDoc("first floor")
        self.root_ch.mainloop()

    def back(self):
        self.labeldoc.grid_forget()
        # self.buttdoc.grid_remove()
        self.listadoc.grid_forget()
        self.selectdoc.grid_forget()
        self.select['state'] = NORMAL
        self.buttdoc.grid_forget()
        self.scrolldoc.grid_forget()

    def chooseDoc(self):
        self.labeldoc = Label(self.root_ch, text="CHOOSE DOCTOR", fg="black", bg="dodger blue")
        self.labeldoc.grid(row=3, sticky="n", pady=20)
        self.buttdoc = Button(self.root_ch, text="BACK", command=self.back, fg="black", bg="dodger blue")
        self.buttdoc.grid(row=3, sticky="e")

        self.scrolldoc = Scrollbar(self.root_ch)
        self.listadoc = tk.Listbox(self.root_ch,
                                   bg="gray")  # Use sticky=tk.N+tk.S to stretch the widget vertically but leave it centered horizontally.

        self.listadoc.configure(yscrollcommand=self.scrolldoc.set)  # dimensioni dovrebbero andare apposto con sticky
        for x in docs_in_dep[self.dep_selected]:
            self.listadoc.insert(END, x)
        # self.listadoc.insert(END, "TRUMP")
        # self.listadoc.insert(END, "PUTIN")
        # self.listadoc.insert(END, "XI JIPING(?)")
        # self.listadoc.insert(END,"MATTEO RENZI")  # Python lambda functions, also known as anonymous functions, are inline functions that do not have a name.

        self.listadoc.grid(row=4, column=0, sticky="nsew")
        self.selectdoc = Button(self.root_ch, text="SELECT", command=self.selectdoc, fg="black", bg="dodger blue")
        self.selectdoc.grid(row=5, column=0, sticky="n")
        # self.chooseDoc(self.lista.get(self.lista.curselection()))

        self.listadoc.bind('<Double-1>', self.go2)

    def selectdoc(self):
        # self.day_selected = day
        # Doctor or place
        place = self.listadoc.get(self.listadoc.curselection())
        choosetime(self.day_selected, self.month_selected, self.year_selected, self.dep_selected, place, self.root_ch)

    """
        NOW IT HAS TO DISPLAY ANOTHER FRAME ALLTOGETHER
    """

    def go(self, event):
        self.dep_selected = self.lista.get(self.lista.curselection())
        self.chooseDoc()

    def go2(self, event):
        print(self.listadoc.get(self.listadoc.curselection()))
        """
        retrieve data related to that doctor and call the constructor of the next class
        """

    def select(self):
        self.dep_selected = self.lista.get(self.lista.curselection())
        self.select['state'] = DISABLED
        """
        call the other window to be displayed
        """
        self.chooseDoc()  # gli pass


class choosetime():

    def __init__(self, daypassed, monthpassed, yearpassed, department, place, dep_root):

        self.time_root = Tk()
        self.time_root.title("CHOOSE TIME")
        self.time_root.configure(bg="gray12")
        self.day_sel = daypassed
        self.month_sel = monthpassed
        self.year_sel = yearpassed
        self.department = department
        self.place = place
        self.dep_root = dep_root
        self.sf = ScrolledFrame(self.time_root, width=500, height=500, bg="gray12")
        self.sf.configure(bg="gray12")
        self.sf.grid_columnconfigure(1, weight=1)
        self.sf.grid_columnconfigure(0, weight=1)
        self.sf.grid_columnconfigure(2, weight=1)

        self.sf.grid(sticky='n')
        self.inner_frame = self.sf.display_widget(Frame)
        self.inner_frame.configure(bg="grey12")
        # self.la = Label(self.inner_frame, text="tryyyy", fg="black")
        # self.la.grid(row=0)
        # tempbutt = Button(self.inner_frame,command=self.book, text="BOOK, let's pretend this one is free", fg="black")
        # tempbutt.grid(row=0, column=2, ipadx=5, ipady=5, sticky='w')

        """
        I HAVE DAY,MONTH,YEAR (AND DEPARTMENT AND DOCTOR? HOW DO we MANAGE THEM) to access sql
        """
        hour = 8
        for timeslot in range(17):
            date = str(self.day_sel) + "-" + str(self.month_sel) + "-" + str(self.year_sel)
            # retrieved_from_sql = "data if they are nonzero, otherwise empty string"
            c.execute(sql_search_query, (date, hour, self.place))
            retrieved_from_sql = c.fetchall()

            timelab = Label(self.inner_frame, text=str(hour), fg="black", bg="grey")
            timelab.grid(row=timeslot, column=0, sticky='e', ipadx=1)
            print(len(retrieved_from_sql))
            print(date)
            if len(retrieved_from_sql) == 0:  # elimino li zeriz
                templabel = Label(self.inner_frame, text="EMPTY SPOT, READY TO BOOK", fg="white", bg="grey12")
                templabel.grid(row=timeslot, column=1, ipadx=1, sticky='w')

                tempbutt = Button(self.inner_frame, text="BOOK", command=lambda hour=hour: self.book(hour), fg="black",
                                  bg="dodger blue")
                tempbutt.grid(row=timeslot, column=2, ipadx=0, ipady=5, sticky='w')
            else:
                templabel = Label(self.inner_frame, text='Name : ' + retrieved_from_sql[0][1] + ' ' +
                                                         retrieved_from_sql[0][2] + ', cell number : ' +
                                                         retrieved_from_sql[0][3], bg="grey12", fg="white", font="bold")
                templabel.grid(row=timeslot, column=1, ipadx=1, sticky='w')
                # tempbutt = Button(self.inner_frame, command=self.book, text="BOOK, let's pretend this one is free", fg="black")
                # tempbutt.grid(row=timeslot, column=2, ipadx=5, ipady=5, sticky='w')
            hour += 1
        self.time_root.mainloop()

    def book(self, hour):
        Book(self.day_sel, self.month_sel, self.year_sel, hour, self.department, self.place, self.time_root,
             self.dep_root)


class Book():
    def __init__(self, day, month, year, hour, department, place, time_root, dep_root):
        self.bookroot = Tk()
        self.time_root = time_root
        self.dep_root = dep_root
        self.day_sel = day
        self.month_sel = month
        self.year_sel = year
        self.time = hour
        self.department = department
        self.place = place
        self.bookroot.title("BOOK AN APPOINTMENT")
        self.bookroot.configure(bg="grey12")
        self.jac1 = StringVar()
        self.var2 = StringVar()
        self.var3 = StringVar()
        self.disable_btn = BooleanVar()
        self.sms_btn = BooleanVar()
        self.lb1 = Label(self.bookroot, text="NAME", fg="white", bg="grey12", font="bold")
        self.lb1.grid(row=0, column=0, ipadx=10, ipady=10, padx=10)
        self.lb2 = Label(self.bookroot, text="surname", fg="white", bg="grey12", font="bold")
        self.lb2.grid(row=1, column=0, ipadx=10, ipady=10, padx=10)
        self.lb3 = Label(self.bookroot, text="cellphone number ", font="bold", fg="white", bg="grey12")
        self.lb3.grid(row=2, column=0, ipadx=10, ipady=10, padx=10)

        self.disable = Checkbutton(self.bookroot, text="are you disable?", variable=self.disable_btn, onvalue=1,
                                   offvalue=0,
                                   fg="white", command=self.disable, indicatoron=True, font="bold", bg="grey12")
        self.disable.grid(row=3, column=0, ipadx=10, ipady=10, padx=10)

        self.sms = Checkbutton(self.bookroot, text="do you want a sms reminder?", onvalue=1, variable=self.sms_btn,
                               offvalue=0,
                               fg="white", bg="grey12", font="bold", command=self.sms, indicatoron=True)
        self.sms.grid(row=4, column=0, ipadx=0, ipady=0, padx=0)

        self.name_ent = tk.Entry(self.bookroot, textvariable=self.jac1)
        self.surname_ent = Entry(self.bookroot, textvariable=self.var2)
        self.cell_ent = Entry(self.bookroot, textvariable=self.var3)
        self.name_ent.grid(row=0, column=1, padx=10, pady=10)
        self.surname_ent.grid(row=1, column=1, padx=10, pady=10)
        self.cell_ent.grid(row=2, column=1, padx=10, pady=10)

        book = Button(self.bookroot, text="BOOK", command=self.letsbook, bg="dodger blue", fg="black")
        book.grid(row=6, column=0, ipadx=10, ipady=10, padx=10)
        self.bookroot.mainloop()

    def disable(self):
        print(self.disable_btn.get())
        if self.disable_btn.get():
            print("you will receive adeguate informations")
            # print(self.disable_btn.get())
        else:
            print("good for you")
            # print(self.disable_btn.get())

    def letsbook(self):
        date = str(self.day_sel) + "-" + str(self.month_sel) + "-" + str(self.year_sel)
        # Temporary constant service
        service = 'Electrocardiography'
        print(self.sms_btn.get())
        c.execute(sql_insert_appointment, (12, self.name_ent.get(), self.surname_ent.get(), str(self.cell_ent.get()),
                                           self.time, date, self.disable_btn.get(), self.sms_btn.get(), self.department,
                                           self.place, service))
        conn.commit()
        c.execute("SELECT * FROM Appointments")
        data = c.fetchall()
        print(data)
        columns = ['id', 'name', 'surname', 'number', 'date_selected', 'time', 'disable', 'sms', 'department', 'place']
        # appointment_df = pd.DataFrame(list(data), columns=columns)

        # writer = pd.ExcelWriter('foo.xlsx')
        # appointment_df.to_excel(writer, sheet_name='bar')
        # writer.save()

        self.bookroot.destroy()
        self.time_root.destroy()
        self.dep_root.destroy()
        # print(self.name_ent.get())
        # print(len(self.name_ent.get()))

    def sms(self):
        if self.sms_btn.get():
            # print(self.sms_btn.get())
            print("sms")
        else:
            # print(self.sms_btn.get())
            print("NO sms")


class showAllAppointments():

    def getDepartmentInAppointmens(self):

        sql_department_in_appointmens = "SELECT DISTINCT department FROM Appointments"

        c.execute(sql_department_in_appointmens)

        self.Options = [""]
        for row in c.fetchall():
            self.Options.append(row[0])

    def comboClick(self, event=None):
        print('--- callback ---')
        print('var.get():', self.var.get())
        if event:
            print('event.widget.get():', event.widget.get())
            self.department_selected = event.widget.get()

        self.frame_top.destroy()
        self.setup()

    def setup(self):

        self.frame_top = tk.Frame(self.parent, width=640, height=480)
        self.frame_top.pack(side="top", expand=1, fill="both")

        frame_top = self.frame_top
        dep = self.department_selected

        # Create a ScrolledFrame widget
        sf = ScrolledFrame(frame_top, width=620, height=470)
        sf.pack(side="top", expand=1, fill="both")

        # Bind the arrow keys and scroll wheel
        sf.bind_arrow_keys(frame_top)
        sf.bind_scroll_wheel(frame_top)

        frame = sf.display_widget(tk.Frame)

        if (dep == ""):
            c.execute(sql_all_appointments_query)
        else:
            sql_appointment_per_department_query = "SELECT * FROM Appointments WHERE department = '" + dep + "' ORDER BY DATE, TIME"
            c.execute(sql_appointment_per_department_query)

        retrieved_from_sql = c.fetchall()

        for idx, appointment in enumerate(retrieved_from_sql):
            print(appointment)
            #            index = tk.Label(self.inner_frame, text=str(idx + 1), fg="white",bg="grey12")
            #            index.grid(row=idx+2, column=0, sticky='w', ipadx=2)

            d1 = datetime.datetime.strptime(appointment[5], '%d-%m-%Y').date()
            d2 = datetime.date.today()
            if (d1 >= d2):
                fgcolor = "blue"
            else:
                fgcolor = "grey12"

            app_date = tk.Label(frame, text=appointment[5], fg=fgcolor, width=10)
            app_date.grid(row=idx + 2, column=0, sticky='w', ipadx=2)

            app_time = tk.Label(frame, text=appointment[4], fg="grey12", width=5)
            app_time.grid(row=idx + 2, column=1, sticky='w', ipadx=2)

            name = tk.Label(frame, text=appointment[1], fg="grey12", width=10)
            name.grid(row=idx + 2, column=2, ipadx=2, sticky='w')

            surname = tk.Label(frame, text=appointment[2], fg="grey12", width=10)
            surname.grid(row=idx + 2, column=3, ipadx=2, sticky='w')

            cell = tk.Label(frame, text=appointment[3], fg="grey12", width=10)
            cell.grid(row=idx + 2, column=4, ipadx=2, sticky='w')

            department = tk.Label(frame, text=appointment[8], fg="grey12", width=10)
            department.grid(row=idx + 2, column=5, ipadx=2, sticky='w')

            place = tk.Label(frame, text=appointment[9], fg="grey12", width=10)
            place.grid(row=idx + 2, column=6, ipadx=2, sticky='w')

            if appointment[6]:
                disabled_text = 'Yes'
            else:
                disabled_text = 'No'
            disabled = tk.Label(frame, text=disabled_text, fg="grey12", width=5)
            disabled.grid(row=idx + 2, column=7, ipadx=1, sticky='w')

    def __init__(self, date):
        self.parent = Tk()
        self.parent.title = "Appointment List"
        self.parent.configure(bg="gray12")
        self.parent.minsize(800, 400)

        self.parent.rowconfigure(0, minsize=640, weight=1)
        self.parent.columnconfigure(1, minsize=480, weight=1)

        self.department_selected = ""
        self.Options = []

        self.var = tk.StringVar()

        self.getDepartmentInAppointmens()

        frame_header = tk.Frame(self.parent, width=640, height=30)
        frame_header.pack(side="top", expand=1, fill="both")

        header = tk.Label(frame_header, text="Appointments List", fg="black")
        header.grid(row=0, column=3, columnspan=4, sticky='w', ipadx=2)

        header = tk.Label(frame_header, text="Choose Department:", fg="black", width=15)
        header.grid(row=1, column=0, columnspan=2, sticky='w', ipadx=2)

        depCombo = ttk.Combobox(frame_header, textvariable=self.var, value=self.Options)
        depCombo.bind("<<ComboboxSelected>>", self.comboClick)
        depCombo.grid(row=1, column=2, columnspan=3, sticky='w', ipadx=25)

        index = tk.Label(frame_header, text="Date", fg="black", width=10)
        index.grid(row=2, column=0, sticky='w', ipadx=2)
        index = tk.Label(frame_header, text="Time", fg="black", width=5)
        index.grid(row=2, column=1, sticky='w', ipadx=2)
        header = tk.Label(frame_header, text="Name", fg="black", width=10)
        header.grid(row=2, column=2, sticky='w', ipadx=2)
        header = tk.Label(frame_header, text="Surname ", fg="black", width=10)
        header.grid(row=2, column=3, sticky='w', ipadx=2)
        header = tk.Label(frame_header, text="Mobile number", fg="black", width=10)
        header.grid(row=2, column=4, sticky='w', ipadx=2)
        header = tk.Label(frame_header, text="Department", fg="black", width=10)
        header.grid(row=2, column=5, sticky='w', ipadx=2)
        header = tk.Label(frame_header, text="Doctor", fg="black", width=10)
        header.grid(row=2, column=6, sticky='w', ipadx=2)
        header = tk.Label(frame_header, text="Disabled", fg="black", width=5)
        header.grid(row=2, column=7, sticky='w', ipadx=2)

        self.frame_top = None
        self.setup()


class showAppointments():

    def getDepartmentInAppointmens(self):

        sql_department_in_appointmens = "SELECT DISTINCT department FROM Appointments WHERE date = '" + self.date + "'"

        c.execute(sql_department_in_appointmens)

        self.Options = [""]
        for row in c.fetchall():
            self.Options.append(row[0])

    def comboClick(self, event=None):
        print('--- callback ---')
        print('var.get():', self.var.get())
        if event:
            print('event.widget.get():', event.widget.get())
            self.department_selected = event.widget.get()

        self.frame_top.destroy()
        self.setup()

    def setup(self):

        print(self.date)
        self.frame_top = tk.Frame(self.parent, width=640, height=480)
        self.frame_top.pack(side="top", expand=1, fill="both")

        frame_top = self.frame_top
        dep = self.department_selected

        # Create a ScrolledFrame widget
        sf = ScrolledFrame(frame_top, width=620, height=470)
        sf.pack(side="top", expand=1, fill="both")

        # Bind the arrow keys and scroll wheel
        sf.bind_arrow_keys(frame_top)
        sf.bind_scroll_wheel(frame_top)

        frame = sf.display_widget(tk.Frame)

        if (dep == ""):
            c.execute(sql_search_date_query, (self.date,))
        else:
            sql_appointment_per_department_query = "SELECT * FROM Appointments WHERE department = '" + dep + "' AND date = '" + self.date + "' ORDER BY TIME"
            c.execute(sql_appointment_per_department_query)

        retrieved_from_sql = c.fetchall()

        for idx, appointment in enumerate(retrieved_from_sql):
            print(appointment)
            index = tk.Label(frame, text=str(idx + 1), fg="white", bg="grey12", width=5)
            index.grid(row=idx + 2, column=0, sticky='w', ipadx=2)

            #            app_date = tk.Label(frame, text=appointment[5], fg="grey12", width=10)
            #            app_date.grid(row=idx+2, column=0, sticky='w', ipadx=2)

            #            app_time = tk.Label(frame, text=appointment[4], fg="grey12", width=5)
            #            app_time.grid(row=idx+2, column=1, sticky='w', ipadx=2)

            name = tk.Label(frame, text=appointment[1], fg="grey12", width=10)
            name.grid(row=idx + 2, column=1, ipadx=2, sticky='w')

            surname = tk.Label(frame, text=appointment[2], fg="grey12", width=10)
            surname.grid(row=idx + 2, column=2, ipadx=2, sticky='w')

            cell = tk.Label(frame, text=appointment[3], fg="grey12", width=10)
            cell.grid(row=idx + 2, column=3, ipadx=2, sticky='w')

            department = tk.Label(frame, text=appointment[8], fg="grey12", width=10)
            department.grid(row=idx + 2, column=4, ipadx=2, sticky='w')

            place = tk.Label(frame, text=appointment[9], fg="grey12", width=10)
            place.grid(row=idx + 2, column=5, ipadx=2, sticky='w')

            if appointment[6]:
                disabled_text = 'Yes'
            else:
                disabled_text = 'No'
            disabled = tk.Label(frame, text=disabled_text, fg="grey12", width=5)
            disabled.grid(row=idx + 2, column=6, ipadx=1, sticky='w')

            tempbutt = tk.Button(frame, text="WRITE TAG", fg="black", bg="dodger blue",
                                 command=lambda appointment=appointment: self.write_tag(appointment))
            tempbutt.grid(row=idx + 2, column=7, ipadx=0, ipady=5, sticky='w')

    def __init__(self, date):
        self.date = date

        self.parent = Tk()
        self.parent.title = "Appointment List"
        self.parent.configure(bg="gray12")
        self.parent.minsize(800, 400)

        self.parent.rowconfigure(0, minsize=640, weight=1)
        self.parent.columnconfigure(1, minsize=480, weight=1)

        self.department_selected = ""
        self.Options = []

        self.var = tk.StringVar()

        self.getDepartmentInAppointmens()

        frame_header = tk.Frame(self.parent, width=640, height=30)
        frame_header.pack(side="top", expand=1, fill="both")

        header = tk.Label(frame_header, text=self.date + " - Appointments List", fg="black")
        header.grid(row=0, column=3, columnspan=4, sticky='w', ipadx=2)

        header = tk.Label(frame_header, text="Choose Department:", fg="black", width=15)
        header.grid(row=1, column=0, columnspan=2, sticky='w', ipadx=2)

        depCombo = ttk.Combobox(frame_header, textvariable=self.var, value=self.Options)
        depCombo.bind("<<ComboboxSelected>>", self.comboClick)
        depCombo.grid(row=1, column=2, columnspan=3, sticky='w', ipadx=25)

        # index = tk.Label(frame_header, text="Date", fg="black", width=10)
        # index.grid(row=2, column=0, sticky='w', ipadx=2)
        # index = tk.Label(frame_header, text="Time", fg="black", width=5)
        # index.grid(row=2, column=1, sticky='w', ipadx=2)
        index = tk.Label(frame_header, text="", fg="black", width=5)
        index.grid(row=2, column=0, sticky='w', ipadx=2)
        header = tk.Label(frame_header, text="Name", fg="black", width=10)
        header.grid(row=2, column=1, sticky='w', ipadx=2)
        header = tk.Label(frame_header, text="Surname ", fg="black", width=10)
        header.grid(row=2, column=2, sticky='w', ipadx=2)
        header = tk.Label(frame_header, text="Mobile number", fg="black", width=10)
        header.grid(row=2, column=3, sticky='w', ipadx=2)
        header = tk.Label(frame_header, text="Department", fg="black", width=10)
        header.grid(row=2, column=4, sticky='w', ipadx=2)
        header = tk.Label(frame_header, text="Doctor", fg="black", width=10)
        header.grid(row=2, column=5, sticky='w', ipadx=2)
        header = tk.Label(frame_header, text="Disabled", fg="black", width=5)
        header.grid(row=2, column=6, sticky='w', ipadx=2)

        self.setup()

    def write_tag(self, appointment):


        MIFAREReader = mfrc522.MFRC522()
        print(appointment)
        totem_identifier = 6  # This cannot be zero
        destination = appointment[-2]  # appointment is an array, last entry is the ''place'', i.e. the doctor

        destination_enc = searchKeyByValue(Encoding, destination)  # access by value, returns a number
        destination_identifier = destination_enc  # access by key the dec-enc dict(which is the reversal of the other one
        # and finds the right encoding number
        badge = Badge([1, destination_identifier])  # for now we only manage the case only one destination is possible

        time_list = []
        identifier_list = []

        # Time represented as date, month, year, hout, minute, sec ex: [19, 1, 21, 0, 30, 39]
        # current_time = list(map(int, time.strftime("%d, %m, %y, %H,%M,%S", time.localtime()).split(',')))

        # init_time_identifier = current_time.append(totem_identifier)
        init_time_identifier = []
        for i in range(len(identifier_list), 16):
            identifier_list.append(0)

        for i in range(len(time_list), 16):
            time_list.append(0)

        for i in range(len(init_time_identifier), 16):
            init_time_identifier.append(0)
        init_time_identifier[7] = searchKeyByValue(Example_enc_service,appointment[-1])

        try:
            (status, TagType) = MIFAREReader.MFRC522_Request(MIFAREReader.PICC_REQIDL)
            if not status:
                blockAdd = STARTINGBLOCK  # zero is used for key's own stuff. 1 CONTAINS N. OF BLOCKS to be read. <64 -> fits into 1 byte
                sendData = badge.encoded_list  # i have to prepend
                sendData.insert(0,
                                badge.current_step + 1)  # prepend the current step and re-insert the Offset. ready to write back
                sendBlock = bytearray()
                print("Length of sendData is " + str(len(sendData)))
                for j in range(len(sendData)):

                    if (j % 16 == 0 and j != 0):  # i have to send it, i have 16 objs inn sendBlock
                        isok = writeWhat(blockAdd, sendBlock)  # if isok 1 -> do it again. it works with negated logic

                        while isok:
                            blockAdd = (blockAdd + 2) if (blockAdd + 1 - 3) % 4 == 0 else (
                                    blockAdd + 1)  # ready for next add
                            isok = writeWhat(blockAdd, sendBlock)  # if isok 1 -> do it again
                        blockAdd = (blockAdd + 2) if (blockAdd + 1 - 3) % 4 == 0 else (
                                blockAdd + 1)  # ready for next add
                        sendBlock = bytearray()  # counterintuitive but python works like so, clear sendBlock outside loop

                    sendBlock.append(
                        sendData[j])  # oss : i have to update blockadd only iff i have 16 elements in sendBlock

                for k in range(len(sendBlock), 16):  # zero padding to 16
                    sendBlock.append(0)
                print(sendBlock)
                print(blockAdd)
                writeWhat(blockAdd, sendBlock)

                print("WRITTEN IDENTIFIER LIST IN BLOCK " + str(READER_IDENTIFIER_BLOCK))
                writeWhat(READER_IDENTIFIER_BLOCK, bytes(identifier_list))
                print("WRITTEN init  LIST IN BLOCK " + str(INIT_TIME_BLOCK))
                writeWhat(INIT_TIME_BLOCK, bytes(init_time_identifier))
                print("WRITTEN time LIST IN BLOCK " + str(READER_TIME_BLOCK))
                writeWhat(READER_TIME_BLOCK, bytes(time_list))

            print("SO FAR SO GOOD MOTHERFUCKERS")


        finally:
            MIFAREReader.MFRC522_StopCrypto1()
            GPIO.cleanup()
            print(LENCTRL)
            print(RI)  # ne ho uno in + perchè scrivo anche la lunghezza dei dati
            print(wheretheyat)


# ACTUAL CODE
conn = create_connection(DATABASE_NAME)  # Create database connection
c = conn.cursor()
c.execute(sql_create_appointments_table)


root = Tk()
app = calendardoc(root)
conn.commit()

root.mainloop()
conn.close()