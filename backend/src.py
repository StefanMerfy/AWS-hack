import requests
import os 
import numpy as np
import get_electricity_data
import pandas as pd
from dotenv import load_dotenv
from numpy import random
import math
load_dotenv()

car_range = 99999
car_battery_capacity = 95
starting_charge = 60
def set_range_and_capacity(range, capacity, scharge):
    global car_range
    global car_battery_capacity
    global starting_charge
    car_range = range
    car_battery_capacity = capacity
    starting_charge = scharge

"""
returns list of <=(count) nearby stations to a given lat/long coordinates and count. Only consider those that supply level 2 or 3 chargers.

Returns:
    _type_: list of fuel station dictionaries
"""
def return_nearby_stations(lat: float, long: float, count: int):
    baseurl = 'https://developer.nrel.gov/api/alt-fuel-stations/v1/nearest.json?'
    count1 = math.floor(count/2)
    count2 = math.ceil(count/2)
    query_params1 = 'limit='+str(count1)+'&latitude='+str(lat)+'&longitude='+str(long)+'&status=E&ev_charging_level=2&radius=6.0'
    query_params2 = 'limit='+str(count2)+'&latitude='+str(lat)+'&longitude='+str(long)+'&status=E&ev_charging_level=dc_fast&radius=6.0'
    
    response1 = requests.get(baseurl+query_params1, headers={"X-Api-Key": os.getenv("ALT_FUEL_API")})
    response2 = requests.get(baseurl+query_params2, headers={"X-Api-Key": os.getenv("ALT_FUEL_API")})
    
    if(response1.status_code >= 400 or response2.status_code >= 400):
        print("something went wrong: query 1 status code " + response1.status_code + ", query 2 status code " + response2.status_code)
        return {}

    parsed1 = response1.json()
    parsed2 = response2.json()
    
    parsed1 = parsed1['fuel_stations']
    parsed2 = parsed2['fuel_stations']
    
    df = get_electricity_data.return_avg_electricity()
    features = ['latitude', 'longitude', 'station_name', 'ev_pricing']
    parsed1_arr = []
    parsed2_arr = []
    
    for station in parsed1:
        avg_cost = float(df.loc[df["stateid"] == station['state']]['price'].values[0])
        full_charge_price = random.normal(avg_cost, avg_cost/4)
        if full_charge_price < avg_cost/2.1:
            full_charge_price = 0
        full_charge_price = car_battery_capacity*full_charge_price/100
        
        station['ev_pricing'] =  full_charge_price
        parsed1_arr.append({x: station[x] for x in features})

    for station in parsed2:
        avg_cost = float(df.loc[df["stateid"] == station['state']]['price'].values[0])
        full_charge_price = random.normal(avg_cost, avg_cost/4)
        if full_charge_price < avg_cost/2.1:
            full_charge_price = 0
        full_charge_price = car_battery_capacity*full_charge_price/100
        
        station['ev_pricing'] =  full_charge_price
        parsed2_arr.append({x: station[x] for x in features})
    
    
    return parsed1_arr + parsed2_arr


"""
given all waypoints in a route and the maximum number of stations, returns a list of tuples of a waypoint and its <=(count) closest surrounding charging stations
Returns:
    _type_: list
"""
def get_all_stations_along_route(all_waypoints, count):
    all_stations = []
    for waypoint in all_waypoints[:-1]: 
        nearby_stations = return_nearby_stations(waypoint.lat, waypoint.long, count)
        all_stations.append((waypoint,nearby_stations))
    return all_stations



# Python 3 helper program to calculate Distance Between Two Points on Earth from geeksforgeeks
from math import radians, cos, sin, asin, sqrt
def distance(lat1, lat2, lon1, lon2):
     
    # The math module contains a function named
    # radians which converts from degrees to radians.
    lon1 = radians(lon1)
    lon2 = radians(lon2)
    lat1 = radians(lat1)
    lat2 = radians(lat2)
      
    # Haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
 
    c = 2 * asin(sqrt(a)) 
    
    # Radius of earth in kilometers. Use 3956 for miles
    r = 6371
      
    # calculate the result (km)
    return(c * r)

# pseudocode for reinforcement learning algorithm 

class State:
    def __init__(self, waypoint, station, charge, is_end_node = False):
        self.waypoint = waypoint
        self.station = station
        self.charge = charge
        self.is_end_node= is_end_node

class Qstatus:
    def __init__(self, next_state: State, qval = 0):
        self.qval = qval
        self.next_state = next_state
    def update_Qval(self, qval):
        self.qval = qval



"""
given a state's current charge % and distance, return what % charge is remaining after completing the distance
Return:
    __type__: float
"""
def calculate_new_charge(charge, distance):
    return charge - distance/car_range

"""
given a state, all waypoints, and the list of tuples of a waypoint and its surrounding charging stations, return a list of all reachable states from the current state.
Returns: 
    _type_: list
"""
def get_reachable_states(state: State, all_waypoints, all_stations, charge_levels):
    try: 
        state_waypoint_index = all_waypoints.index(state.waypoint)
    except:
        raise Exception("Could not find associated waypoint index of a ev recharge station.")
    
    reachable = []
    for (waypoint, station_candidates) in all_stations:
        try:
            waypoint_index = all_waypoints.index(waypoint)
            if (waypoint_index <= state_waypoint_index):
                continue
        except:
            raise Exception("Could not find associated waypoint index of a ev recharge station.")
        for station_candidate in station_candidates:
            if calculate_new_charge(state.charge,distance(state.station['latitude'], station_candidate['latitude'], state.station['longitude'], station_candidate['longitude'])) > 0:
                for charge in charge_levels:
                    if calculate_new_charge < charge:
                        reachable.append(State(waypoint, station_candidate, charge))
    
    return reachable

"""
given the list of tuples of a waypoint and its surrounding charging stations, and predetermined charge levels(%), generate the Qdict (Qtable) to record in RL.
each row of the qdict represents the list of same starting state-> all reachable states from that state. There are enough rows for every possible non-end state.
"""
def generate_Qdict(all_stations, all_waypoints, charge_levels=[15,35,55,75]):
    nstates = 0
    q_dict = {}
    end_state = State(all_waypoints[-1], None, 0, is_end_node=True)
    # for each charge level in each station in all_stations (every possible state), generate the list of reachable states. Then, for applicable states, if 
    for waypoint, stations in all_stations:
        for station in stations:
            for charge in charge_levels:
                current_state = State(waypoint, station, charge)
                # if the current state can go to the end state (destination), make that the only choosable next state.
                if calculate_new_charge(current_state.charge, distance(current_state.station['latitude'], end_state.station['latitude'], current_state.station['longitude'], end_state.station['longitude'])) > 0:
                    q_dict[current_state] = [Qstatus(end_state, qval=-1)]
                else: 
                    reachable_states = get_reachable_states(current_state, all_waypoints, all_stations, charge_levels)
                    list_actions = []
                    for state in reachable_states: 
                        list_actions.append(Qstatus(state))
                    if len(list_actions) == 0:
                        continue
                    q_dict[current_state] = list_actions
    q_dict[end_state] = [Qstatus(State(all_waypoints[-1], None, 0, is_end_node=True))] #this should never be read by non-end state states
    return q_dict
        

def calculate_reward(state1, state2):
    w1 = 0.5
    w2 = 1-w1
    distance_between = distance(state1.station['latitude'], state2.station['latitude'], state1.station['longitude'], state2.station['longitude'])
    charging_cost = (state2.charge-(state1.charge-(distance_between/car_range))) * state2.station['ev_pricing']
    reward = (w1 * distance_between+ w2 * charging_cost) / 100

def RL_generate_paths(all_waypoints, all_stations):
    learning_rate = 0.75
    discount_factor = 1.02 # since we are optimizing q-value by minimizing, a slightly > 1 discount factor will gently urge the agent to reach the destination with slight haste
    exploration_prob = 0.2
    epochs = 1500
    
    q_dict = generate_Qdict(all_stations, all_waypoints)
    
    for epoch in range(epochs):
        len_qdict = len(list(q_dict))
        current_state = list(q_dict)[np.random.randint(0, len_qdict)]

        while not current_state.is_end_node:
            next_index = None
            if len(q_dict[current_state]) == 0:
                break
            # choose action to explore a new state or go with the current best. 
            # action is a Qstatus object, holding the current Q(current_state, action) value and the corresponding state.
            # next_index is the index of the action in the list of available actions for current_state to take.
            
            if np.random.rand() < exploration_prob:
                n_actions = len(q_dict[current_state])
                next_index = np.random.randint(0, n_actions)
                action = q_dict[current_state][next_index]  # Explore
            else:
                next_index = min(range(len(q_dict[current_state])), key=lambda i: q_dict[current_state][i].qval)
                action = q_dict[current_state][next_index]  # Exploit
            
            next_state = action.next_state
            reward = None
            
            if next_state.is_end_node:
                reward = action.qval
            else:
                reward = calculate_reward(current_state, next_state)
            
            
            
            next_optimal_val = min([qstatus.qval for qstatus in q_dict[next_state]])
            q_dict[current_state][next_index].qval += learning_rate * (reward + discount_factor * next_optimal_val) - q_dict[current_state][next_index].qval
            current_state = next_state
            

    final_agent = list(q_dict)[0]
    state_list = []
    
    while not final_agent.is_end_node:
        state_list.append[final_agent]
        final_agent_index = min(range(len(q_dict[final_agent])), key=lambda i: q_dict[current_state][i].qval)
        final_agent = q_dict[final_agent][final_agent_index]
    state_list.append[final_agent]
    
    updated_waypoints = []
    station_indexes = []
    recharge_goal = []
    price_list = []
    index = 0
    for i in range(len(all_waypoints)):
        if index < len(state_list):
            if state_list[index].waypoint == all_waypoints[0]:
                updated_waypoints.append(state_list[index].waypoint)
                station_indexes.append(i)
                #this line below basically computes the distance between two consecutive chosen charging stations 
                distance_between = distance(state_list[index-1].station['latitude'], state_list[index].station['latitude'], state_list[index-1].station['longitude'], state_list[index].station['longitude']) if index >= 1 else distance(all_waypoints[0][0], state_list[index].station['latitude'], all_waypoints[0][1], state_list[index].station['longitude'])
                #this line below basically computes the charging cost incurred at each charging station
                charging_cost = (state_list[index].charge-(state_list[index-1].charge-(distance_between/car_range))) * state_list[index].station['ev_pricing'] if index >= 1 else (state_list[index].charge-(starting_charge-distance_between/car_range)) * state_list[index].station['ev_pricing']
                price_list.append(charging_cost)
                recharge_goal.append(state_list[index].charge)
                index = index + 1
            else:
                updated_waypoints.append(all_waypoints[i])
        else:
            updated_waypoints.append(all_waypoints[i])
    
    
    return updated_waypoints, station_indexes, recharge_goal, price_list