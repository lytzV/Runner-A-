from flask import Flask, render_template, request
import os
import requests
import random
import scrapy
import re

app = Flask(__name__)
@app.route('/')
def index():
    return '8===D'
@app.route('/geocoding')
def geocoding():
    input1=request.args['input_lat']
    input2=request.args['input_lng']
    #radius=request.args['input_radius']
    radius_in_use=1
    nearest_street=requests.get("http://api.geonames.org/findNearbyStreetsJSON",params={'lat':input1,'lng':input2,'radius':radius_in_use,'username':'lytz'})
    street_cluster=nearest_street.json()['streetSegment']
    #elevation_init=requests.get('https://api.open-elevation.com/api/v1/lookup?locations='+str(input1)+','+str(input2)).json()['results'][0]['elevation']
    #endpoint_cluster=get_lastloc(street_cluster)
    intersections=calculate_intersection(street_cluster)
    final_intersections=eliminate_repeat(intersections)
    ultimate_intersections=[]
    for i in final_intersections:
        input1,input2=i['lat'],i['lng']
        more_intersections=eliminate_repeat(calculate_intersection(requests.get("http://api.geonames.org/findNearbyStreetsJSON",params={'lat':input1,'lng':input2,'radius':radius_in_use,'username':'lytz'}).json()['streetSegment']))
        ultimate_intersections+=more_intersections
    ultimate_intersections+=final_intersections
    neighbour_dict=find_neighbour(ultimate_intersections)
    elevation=calc_intersection_elevation(ultimate_intersections)
    return render_template('mapWeb0.html',intersections=ultimate_intersections,lat='lat',lng='lng',street1='street1',street2='street2',neighbour=neighbour_dict,elevation=elevation)
    """return render_template('mapWeb.html',streets_json=street_cluster,
                        intersection_json=nearest_intersection.json()['intersection'],
                        st1='street1',
                        st2='street2',
                        name=lambda street:street['name'] if street['name'] else 'Namaless Road',
                        distance='distance',
                        last_coordinate='last_coordinate'
                        )"""

@app.route('/inputloc')
def inputloc():
    return render_template('input.html')
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
def calc_elevation(start,street_cluster):
    for street in street_cluster:
        line=street['line']
        list_of_coordinates=line.split(',')
        node_elevation=[]
        for pairs in list_of_coordinates:
            pairs_split=pairs.split(' ')
            new_pair=[float(pairs_split[1]),float(pairs_split[0])]
            elevation_curr=requests.get('https://api.open-elevation.com/api/v1/lookup?locations='+str(new_pair[0])+','+str(new_pair[1])).json()['results'][0]
            node_elevation.append(elevation_curr['elevation']-start)
        street['node_elevation']=node_elevation
if __name__ == '__main__':
    app.run(debug=True)
