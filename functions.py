
import datetime
import time
from datetime import date
 
 
def countdown(end):
    today = date.today()
  #check which date is greater to avoid days output in -ve number
    if (end-today).days > 1:
      return str((end-today).days) + ' dager til sperrefrist: ' + str(end)
    elif (end-today).days == 1:
      return str((end-today).days) + ' dag til sperrefrist: ' + str(end)
    elif (end-today).days == 0:
      return 'Sperrefristen er i dag (22.04.24)'
    elif (end-today).days == -1:
      return str(abs((end-today).days)) + ' dag siden sperrefrist opphørte (22.04.24).'
    else:
      return str(abs((end-today).days)) + ' dager siden sperrefrist opphørte (22.04.24).'
     
 
def right_align(s, props='text-align: right;'):
  return props

def make_asterix(row):
  
  if row['ukr_prikket'] == 'Obs! Inkluderer ikke anonymiserte tall. Se fanen Tallgrunnlag på nettsiden.':
    val = '*'
  else:
    val = ''
  return val