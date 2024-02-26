
import datetime
import time

from datetime import date
 
 
def countdown(end):
    today = date.today()
  #check which date is greater to avoid days output in -ve number
    return str((end-today).days) + ' dager til sperrefrist: ' + str(end)
     
 