import os
import json
import src
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from mangum import Mangum
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
handler = Mangum(app)

origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Item(BaseModel):
    count: int
    list_lat: list[float]
    list_long: list[float]



    
@app.get("/")
async def root():
    return {"message": "Hello World"}



@app.get("/return_nearby_charging_stations/")
async def return_nearby_charging_stations(lat: float, long: float, count: int = 5):
    nearby_stations = src.return_nearby_stations(lat, long, count)
    return {"stations": nearby_stations}
    

@app.post("/post_waypoints/")
async def post_waypoints(item: Item):
    
    all_waypoints_lat = item.list_lat
    all_waypoints_long = item.list_long
    all_waypoints = []
    if (len(all_waypoints_lat) != len(all_waypoints_long)):
        raise HTTPException(status_code=403, detail="Coordinate pairs missing items")
    else:
        for i in range(len(all_waypoints_lat)):
            all_waypoints.append((all_waypoints_lat[i],all_waypoints_long[i]))
    
    updated_waypoints, station_indexes, recharge_goal, price_list= src.get_all_stations_along_route(all_waypoints, item.count)
    """
    updated_waypoints- array of sequential waypoints (where some waypoints are substituted for charging stations) to create a new route with
    station_indexes- the indexes of the stations in updated_waypoints 
    recharge_goal- the amount to recharge to at each station
    price_list- the estimated price of each recharge at each station
    """
    return {"updated_waypoints": updated_waypoints, "station_indexes": station_indexes, "recharge_goal": recharge_goal, "price_list": price_list}


# {
#     "count": x 
#     "list_lat": [
#         lat1,
#         lat2,
#         ...
#     ]
#     "list_long": [
#         long1,
#         long2,
#         ...
#     ]
# }