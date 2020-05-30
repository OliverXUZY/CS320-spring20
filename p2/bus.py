## Location
from math import sin, cos, asin, sqrt, pi

def haversine_miles(lat1, lon1, lat2, lon2):
    """Calculates the distance between two points on earth using the
    harversine distance (distance between points on a sphere)
    See: https://en.wikipedia.org/wiki/Haversine_formula

    :param lat1: latitude of point 1
    :param lon1: longitude of point 1
    :param lat2: latitude of point 2
    :param lon2: longitude of point 2
    :return: distance in miles between points
    """
    lat1, lon1, lat2, lon2 = (a/180*pi for a in [lat1, lon1, lat2, lon2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon/2) ** 2
    c = 2 * asin(min(1, sqrt(a)))
    d = 3956 * c
    return d


class Location:
    """Location class to convert lat/lon pairs to
    flat earth projection centered around capitol
    """
    capital_lat = 43.074683
    capital_lon = -89.384261

    def __init__(self, latlon=None, xy=None):
        if xy is not None:
            self.x, self.y = xy
        else:
            # If no latitude/longitude pair is given, use the capitol's
            if latlon is None:
                latlon = (Location.capital_lat, Location.capital_lon)

            # Calculate the x and y distance from the capital
            self.x = haversine_miles(Location.capital_lat, Location.capital_lon,
                                     Location.capital_lat, latlon[1])
            self.y = haversine_miles(Location.capital_lat, Location.capital_lon,
                                     latlon[0], Location.capital_lon)

            # Flip the sign of the x/y coordinates based on location
            if latlon[1] < Location.capital_lon:
                self.x *= -1

            if latlon[0] < Location.capital_lat:
                self.y *= -1

    def dist(self, other):
        """Calculate straight line distance between self and other"""
        return sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)

    def __repr__(self):
        return "Location(xy=(%0.2f, %0.2f))" % (self.x, self.y)
    
    
## BusDay:
import pandas as pd
from zipfile import ZipFile   
from datetime import datetime

class BusDay:
    with ZipFile('mmt_gtfs.zip') as zf:
        with zf.open("calendar.txt") as f:
            calen = pd.read_csv(f)
        with zf.open("trips.txt") as f:
            trips = pd.read_csv(f)
        with zf.open("stop_times.txt") as f:
            stoptimes = pd.read_csv(f)
        with zf.open("stops.txt") as f:
            stops = pd.read_csv(f)  
        
    def __init__(self, datetime):
        self.datetime = datetime
        self.numtime = int(self.datetime.strftime("%Y%m%d"))
        self.day = self.datetime.strftime("%A").lower()
        self.calender = BusDay.calen[BusDay.calen.start_date <= self.numtime]
        self.calender = self.calender[self.calender.end_date >= self.numtime]
        self.calender = self.calender[self.calender[self.day] == 1]
        self.service_ids = list(self.calender['service_id'])
        
        self.triptable = BusDay.trips
        self.triptable = self.triptable[self.triptable.service_id.isin(self.service_ids)].sort_values(by = 'trip_id', ascending = 1)
        
        self.trip_id = self.triptable.trip_id
        self.stoptable = BusDay.stoptimes  ## stoptimes
        self.stoptable = self.stoptable[self.stoptable.trip_id.isin(self.trip_id)].sort_values(by = 'stop_id', ascending = 1) ## table of stoptimes
        
        self.stop_id = self.stoptable.stop_id
        self.stops = BusDay.stops ## info of stops location, no time/trip
        self.stops = self.stops[self.stops.stop_id.isin(self.stop_id)].sort_values(by = 'stop_id', ascending = 1)
        self.stops.loc[:,'wheelchair_boarding'] = self.stops['wheelchair_boarding'].apply(lambda x: True if x==1 else False)
    
    def get_trips(self, route = None):
        # self.triptable = BusDay.trips
        if route != None:
            # self.triptable = self.triptable[self.triptable.service_id.apply(lambda x: True if str(route) in x else False)]
            self.triptable2 = self.triptable[self.triptable.route_short_name == route]
        else:
            self.triptable2 = self.triptable
        
        self.triptable2.loc[:,'bikes_allowed'] = self.triptable2['bikes_allowed'].apply(lambda x: True if x==1 else False)
        self.triptable2 = self.triptable2[['trip_id', 'route_short_name', 'bikes_allowed']].values.tolist()
        def to_Trip_object(item):
            trip_id,route_id,bikes_allowed = item
            return Trip(trip_id,route_id,bikes_allowed)
        
        self.triplist = list(map(to_Trip_object,self.triptable2))
        return self.triplist
    
    def get_stops(self):
        self.stops2 = self.stops[['stop_id', 'stop_lat', 'stop_lon', 'wheelchair_boarding']].values.tolist()
        def to_Stop_object(item):
            stop_id, stop_lat, stop_lon, wheelchair_boarding = item
            Location_object = Location(latlon = (stop_lat, stop_lon))
            return Stop(stop_id,Location_object,wheelchair_boarding)
        self.stopslist = list(map(to_Stop_object, self.stops2))
        return self.stopslist
    
    def get_stops_rect(self, xlim, ylim):
        stops = self.get_stops()
        BSTree = Node(stops)
        return BSTree.range_search(xlim, ylim)
    
    def get_stops_circ(self, loc, radius):
        stops = self.get_stops()
        BSTree = Node(stops)
        xlim = (loc[0] - radius, loc[0] + radius)
        ylim = (loc[1] - radius, loc[1] + radius)
        rec = BSTree.range_search(xlim, ylim)
        center = Location(xy = loc)
        return [stop for stop in rec if center.dist(stop.location_object) <= radius]
    
    def scatter_stops(self, ax):
        stop_df = pd.DataFrame(list(map(lambda item: [item.location_object.x, item.location_object.y, item.wheelchair_boarding],self.get_stops())),
             columns = ['x','y','wheelchair'])
        stop_df[stop_df['wheelchair']].plot.scatter(x = 'x',y = 'y',marker="o", c = 'red', ax = ax, s=2)
        stop_df[~stop_df['wheelchair']].plot.scatter(x = 'x',y = 'y',marker="o", c = '0.7', ax = ax, s=2)
        
    def draw_tree(self, ax):
        stops = self.get_stops()
        BSTree = Node(stops)
        BSTree.draw_tree(ax)
        
    
class Trip:
    def __init__(self, trip_id, route_id, bike_allowed):
        self.trip_id = trip_id
        self.route_id = route_id
        self.bike_allowed = bike_allowed
        
    def __repr__(self):
        return "Trip({}, {}, {})".format(self.trip_id, self.route_id, self.bike_allowed)

class Stop:
    def __init__(self, stop_id, location_object, wheelchair_boarding):
        self.stop_id = stop_id
        self.location_object = location_object
        self.wheelchair_boarding = wheelchair_boarding
    def __repr__(self):
        return "Stop({}, {}, {})".format(self.stop_id, self.location_object, self.wheelchair_boarding)


# from graphviz import Graph, Digraph
class Node:
    def __init__(self, stop_list, ver_split = 1, levels = 0): 
        self.left = None
        self.right = None
        self.ver_split = ver_split
        self.leaf = True   ## added for draw_tree
        if ver_split == 1:
            stop_list.sort(key = lambda stop_obj: stop_obj.location_object.x)
            self.split_val = stop_list[len(stop_list)//2].location_object.x
        else:
            stop_list.sort(key = lambda stop_obj: stop_obj.location_object.y)
            self.split_val = stop_list[len(stop_list)//2].location_object.y
        if levels <= 6:
            #print(stop_list[:len(stop_list)//2],len(stop_list)//2)
            self.left = Node(stop_list[:len(stop_list)//2],  -ver_split, levels + 1)
            self.right = Node(stop_list[len(stop_list)//2:],  -ver_split, levels + 1)  
            self.leaf = False   ## added for draw_tree
        
            
        self.val = stop_list
    '''   
    def to_graphviz(self, g=None):
        if g == None:
            g = Digraph()
            
        # draw self
        g.node(repr(self.val))
    
        for label, child in [("L", self.left), ("R", self.right)]:
            if child != None:
                # draw child, recursively
                child.to_graphviz(g)
                
                # draw edge from self to child
                g.edge(repr(self.val), repr(child.val), label=label)
        return g
    
    def _repr_svg_(self):
        return self.to_graphviz()._repr_svg_()
    '''
    def range_search(self, xlim, ylim, results=None):
        if results == None:
            results = []

        if self.left == None and self.right == None:
            for obj in self.val:
                if xlim[0] <= obj.location_object.x <= xlim[1] and ylim[0] <= obj.location_object.y <= ylim[1]:
                    results.append(obj)
        else:
            lim = xlim if self.ver_split == 1 else ylim
            if lim[0] <= self.split_val:
                self.left.range_search(xlim, ylim, results)
            if lim[1] >= self.split_val:
                self.right.range_search(xlim, ylim, results)
        return results
    
    def draw_tree(self, ax, lw = 10, xlim = None, ylim = None):
        if self.leaf == True:
            return
        xlim = ax.get_xlim() if xlim == None else xlim
        ylim = ax.get_ylim() if ylim == None else ylim
        
        if self.ver_split == 1:
            xlim_left = xlim[0]
            xlim_mid = self.split_val
            xlim_right = xlim[1]
            
            self.left.draw_tree(ax, lw = lw/2, xlim = (xlim_left,xlim_mid),ylim = ylim)
            self.right.draw_tree(ax, lw = lw/2, xlim = (xlim_mid,xlim_right),ylim = ylim)
            ax.plot((self.split_val,self.split_val),ylim,lw=lw, color="purple",zorder=-10)

        else:
            ylim_left = ylim[0]
            ylim_mid = self.split_val
            ylim_right = ylim[1]
            
            self.left.draw_tree(ax, lw = lw/2, xlim = xlim,ylim = (ylim_left,ylim_mid))
            self.right.draw_tree(ax, lw = lw/2, xlim = xlim,ylim = (ylim_mid,ylim_right))
            ax.plot(xlim,(self.split_val,self.split_val),lw = lw, color="purple", zorder=-10)
        
