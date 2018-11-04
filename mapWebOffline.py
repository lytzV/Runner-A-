from flask import Flask, render_template, request
from implementation import *
import os
import requests
import random
import scrapy
import re



def geocoding(input1,input2):
    radius_in_use=1
    nearest_street=requests.get("http://api.geonames.org/findNearbyStreetsJSON",params={'lat':input1,'lng':input2,'radius':radius_in_use,'username':'lytz'})
    street_cluster=nearest_street.json()['streetSegment']
    #elevation_init=requests.get('https://api.open-elevation.com/api/v1/lookup?locations='+str(input1)+','+str(input2)).json()['results'][0]['elevation']
    #endpoint_cluster=get_lastloc(street_cluster)
    intersections=calculate_intersection(street_cluster)
    final_intersections=eliminate_repeat(intersections)

    return final_intersections

def geocode_with(intersections):
    ultimate_intersections=[]
    for i in intersections:
        input1,input2=i['lat'],i['lng']
        more_intersections=geocoding(input1,input2)
        ultimate_intersections+=more_intersections
    return ultimate_intersections

def calculate_intersection(street_cluster):
    get_nodes(street_cluster)
    intersections=[]
    for first in street_cluster:
        for second in street_cluster:
            first_locs=first['nodes']
            second_locs=second['nodes']
            for i in range(0,len(first_locs)-1):
                for j in range(0,len(second_locs)-1):
                    first_pair=[first_locs[i],first_locs[i+1]]
                    second_pair=[second_locs[j],second_locs[j+1]]
                    if if_intersect(first_pair,second_pair):
                        x,y=intersection_coor(first_pair,second_pair)
                        intersections.append([x,y])
    return intersections
def find_neighbour(intersections):
    neighbour_dict={}
    for i in intersections:
        for j in intersections:
            i_streets=[i['street1'],i['street2']]
            j_streets=[j['street1'],j['street2']]
            for s in i_streets:
                if s in j_streets:
                    loc_i=(float(i['lat']),float(i['lng']))
                    loc_j=(float(j['lat']),float(j['lng']))
                    if(loc_i!=loc_j):
                        if loc_i not in neighbour_dict:
                            neighbour_dict[loc_i]=[loc_j]
                            break
                        else:
                            neighbour_dict[loc_i].append(loc_j)
                            break
    return neighbour_dict
def eliminate_repeat(intersections):
    radius_in_use=1
    new_intersections=[]
    final_intersections=[]
    for i in intersections:
        new_i=requests.get("http://api.geonames.org/findNearestIntersectionJSON",params={'lat':i[0],'lng':i[1],'radius':radius_in_use,'username':'lytz'}).json()['intersection']
        new_intersections.append(new_i)
    prune=lambda x: lambda y:not((x['street1']==y['street1'] and x['street2']==y['street2']) or (x['street1']==y['street2'] and x['street2']==y['street1']))
    while new_intersections:
        final_intersections.append(new_intersections[0])
        new_intersections=list(filter(prune(new_intersections[0]),new_intersections[1:]))
    return final_intersections

def intersection_coor(point_seta,point_setb):
    if point_seta[0][0]-point_seta[1][0]==0:
        if point_setb[0][0]-point_setb[1][0]==0:
            return "Error"
        else:
            k_2=(point_setb[0][1]-point_setb[1][1])/(point_setb[0][0]-point_setb[1][0])
            b_2=point_setb[0][1]-k_2*point_setb[0][0]
            return point_seta[0][0],k_2*point_seta[0][0]+b_2
    if point_setb[0][0]-point_setb[1][0]==0:
        if point_seta[0][0]-point_seta[1][0]==0:
            return "Error"
        else:
            k_2=(point_seta[0][1]-point_seta[1][1])/(point_seta[0][0]-point_seta[1][0])
            b_2=point_seta[0][1]-k_2*point_seta[0][0]
            return point_setb[0][0],k_2*point_setb[0][0]+b_2
    k_1=(point_seta[0][1]-point_seta[1][1])/(point_seta[0][0]-point_seta[1][0])
    b_1=point_seta[0][1]-k_1*point_seta[0][0]
    k_2=(point_setb[0][1]-point_setb[1][1])/(point_setb[0][0]-point_setb[1][0])
    b_2=point_setb[0][1]-k_2*point_setb[0][0]
    try:
        coor_x=(b_2-b_1)/(k_1-k_2)
        coor_y=k_1*coor_x+b_1
        return coor_x,coor_y
    except ZeroDivisionError:
        return "Error"
def if_intersect(point_seta,point_setb):
    if intersection_coor(point_seta,point_setb)=="Error":
        return False
    else:
        x,y=intersection_coor(point_seta,point_setb)
        x_line=(x-point_seta[0][0])*(x-point_seta[1][0])<=0 and (y-point_seta[0][1])*(y-point_seta[1][1])<=0
        y_line=(x-point_setb[0][0])*(x-point_setb[1][0])<=0 and (y-point_setb[0][1])*(y-point_setb[1][1])<=0
        if x_line and y_line:
            return True
        else:
            return False

def get_nodes(street_cluster):
    for street in street_cluster:
        line=street['line']
        list_of_coordinates=line.split(',')
        nodes=[]
        for pairs in list_of_coordinates:
            pairs_split=pairs.split(' ')
            new_pair=[float(pairs_split[1]),float(pairs_split[0])]
            nodes.append(new_pair)
        street['nodes']=nodes
def get_lastloc(street_cluster):
    endpoint_cluster=[]
    for street in street_cluster:
        line=street['line']
        list_of_coordinates=line.split(',')
        last=list_of_coordinates[len(list_of_coordinates)-1].split(' ')
        street['last_coordinate']=[float(last[1]),float(last[0])]
        endpoint_cluster.append(street['last_coordinate'])
    return endpoint_cluster
def calc_intersection_elevation(intersections):
    elevation={}
    for i in intersections:
        elevation[(float(i['lat']),float(i['lng']))]=requests.get('https://api.open-elevation.com/api/v1/lookup?locations='+str(i['lat'])+','+str(i['lng'])).json()['results'][0]['elevation']
    return elevation


#BEGIN PHASE 2
#A* Algorithm
def heuristic(a, b):
    (x1, y1) = a
    (x2, y2) = b
    return abs(x1 - x2) + abs(y1 - y2)

def a_star_search(dict, start, goal):
    frontier = PriorityQueue()
    frontier.put(start, 0)
    came_from = {}
    cost_so_far = {}
    came_from[start] = None
    cost_so_far[start] = 0

    while not frontier.empty():
        current = frontier.get()

        if current == goal:
            break
        for next in dict[current]:
            next_elev=elevation[next]
            curr_elev=elevation[current]
            new_cost = cost_so_far[current] + (next_elev-curr_elev)
            if next not in cost_so_far or new_cost < cost_so_far[next]:
                cost_so_far[next] = new_cost
                priority = new_cost + heuristic(goal, next)
                frontier.put(next, priority)
                came_from[next] = current

    return came_from, cost_so_far
def intersection_coor(point_seta,point_setb):
    if point_seta[0][0]-point_seta[1][0]==0:
        if point_setb[0][0]-point_setb[1][0]==0:
            return "Error"
        else:
            k_2=(point_setb[0][1]-point_setb[1][1])/(point_setb[0][0]-point_setb[1][0])
            b_2=point_setb[0][1]-k_2*point_setb[0][0]
            return point_seta[0][0],k_2*point_seta[0][0]+b_2
    if point_setb[0][0]-point_setb[1][0]==0:
        if point_seta[0][0]-point_seta[1][0]==0:
            return "Error"
        else:
            k_2=(point_seta[0][1]-point_seta[1][1])/(point_seta[0][0]-point_seta[1][0])
            b_2=point_seta[0][1]-k_2*point_seta[0][0]
            return point_setb[0][0],k_2*point_setb[0][0]+b_2
    k_1=(point_seta[0][1]-point_seta[1][1])/(point_seta[0][0]-point_seta[1][0])
    b_1=point_seta[0][1]-k_1*point_seta[0][0]
    k_2=(point_setb[0][1]-point_setb[1][1])/(point_setb[0][0]-point_setb[1][0])
    b_2=point_setb[0][1]-k_2*point_setb[0][0]
    try:
        coor_x=(b_2-b_1)/(k_1-k_2)
        coor_y=k_1*coor_x+b_1
        return coor_x,coor_y
    except ZeroDivisionError:
        return "Error"
def if_intersect(point_seta,point_setb):
    if intersection_coor(point_seta,point_setb)=="Error":
        return False
    else:
        x,y=intersection_coor(point_seta,point_setb)
        x_line=(x-point_seta[0][0])*(x-point_seta[1][0])<=0 and (y-point_seta[0][1])*(y-point_seta[1][1])<=0
        y_line=(x-point_setb[0][0])*(x-point_setb[1][0])<=0 and (y-point_setb[0][1])*(y-point_setb[1][1])<=0
        if x_line and y_line:
            return True
        else:
            return False




def find_path(dict,start,goal):
    a=goal
    while a!=start:
        dic=list(filter(lambda x:(float(x['lat']),float(x['lng']))==a,ultimate_intersections))
        print(a,dic[0]['street1'],dic[0]['street2'])
        print(" |")
        a=dict[a]
    dic=list(filter(lambda x:(float(x['lat']),float(x['lng']))==a,ultimate_intersections))
    print(a,dic[0]['street1'],dic[0]['street2'])


final_intersections=geocoding(40.7127837,-74.0059413)
ultimate_intersections=(geocode_with(final_intersections))+final_intersections
elevation={(40.712001, -74.005292):11,
           (40.712089, -74.00574):12,
           (40.711513, -74.004432):8,
           (40.712089, -74.00574):12,
           (40.711513, -74.004432):8,
           (40.712001, -74.005292):11,
           (40.712003, -74.00609):12,
           (40.712089, -74.00574):12,
           (40.711513, -74.004432):8,
           (40.712001, -74.005292):11,
           (40.711513, -74.004432):8,
           (40.712001, -74.005292):11,
           (40.711008, -74.003615):4,
           (40.712001, -74.005292):11,
           (40.712089, -74.00574):12,
           (40.712003, -74.00609):12,
           (40.711513, -74.004432):8
           }
neighbour_dict=find_neighbour(ultimate_intersections)
goal=[(40.712003, -74.00609),(40.712001, -74.005292),(40.711513, -74.004432),(40.712003, -74.00609)]
start=(40.711008, -74.003615)
dicc=neighbour_dict
cost=[]
for g in goal:
    came_from, cost_so_far = a_star_search(dicc, start, g)
    cost.append([cost_so_far,g])
    print('last cost:',cost_so_far[g])
    find_path(came_from,start,g)
    print('----------------------')
print('Minimum Optimization Cost: ',min([c[g] for [c,g] in cost]))
