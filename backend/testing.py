import requests
import os 
import numpy as np
import get_electricity_data
import pandas as pd
from dotenv import load_dotenv
from numpy import random
import src
load_dotenv()
car_range = 99999 # should be passed in from frontend
car_battery_capacity = 108 #this too 

print(src.return_nearby_stations(39.743078, -105.152278, 1))