#!/usr/bin/env python
# coding: utf-8

# **Final Project - IBM Data Science Certificate**

# Problem description: a group of investors want to build two new shopping centers in Costa Rica's capital San Jose; one in the east side of town and the other one on the west side of town. They define the east as any district inside the greater metropolitan area located east of the central district of San Jose and the west as any district inside the greater metropolitan area west of the central district of San Jose. They don't include the central district in their considerations as it is a very built up area in the heart of town where developing a shopping center is near impossible.
# 
# They want see what types of businesses they need to attract in each area not only to maximize any profits the project might have but also to see if the allocation and design of the shopping centers have to be different in any way.

# In[46]:


import folium
import pandas as pd
import numpy as np
df = pd.read_csv('C:\School\IBM Data Science\Course 9\Data.csv')
sj_map = folium.Map(location = [9.9281, -84.0907], zoom_start = 9)
geojson = 'https://opendata.arcgis.com/datasets/249bc8711c33493a90b292b55ed3abad_0.geojson'
sj_map.choropleth(geo_data = geojson, data = df, columns = ['OBJECTID','GAM'], key_on = 'feature.properties.OBJECTID', fill_color = 'YlGnBu', Legend_name = 'Included Areas for Investigation')
sj_map


# The first map shows the areas that are included in the investigation (thoses shaded in blue).

# **Data to be used:**

# In terms of the data, I will look at the top businesses in each of the districts inside the area and categorize each district into east or west, then I will rate each business type in each sector (east or west). This has to weigh in the positon each business type has in each district and if they even appear in the search or not. This can be done by giving points to each business type, for example if we work with top threes for each district: 3 points to first place, 2 points for second and 1 for third while business types that are not shown get zero points.

# In[35]:


coord = pd.read_csv('C:\School\IBM Data Science\Course 9\Coordinates.csv')


# In[36]:


coord.head()


# In[37]:


coord = coord[coord.GAM != 0]
coord.head()


# In[38]:


for LAT, LON, NOM_PROV, NOM_CANT_1 in zip(coord['LAT'], coord['LONG'], coord['NOM_PROV'], coord['NOM_CANT_1']):
    label = '{}, {}'.format(NOM_CANT_1, NOM_PROV)
    label = folium.Popup(label, parse_html=True)
    folium.CircleMarker(
        [LAT, LON],
        radius=5,
        popup=label,
        color='red',
        fill=True,
        fill_color='#3186cc',
        fill_opacity=0.7,
        parse_html=False).add_to(sj_map)  
    
sj_map


# The points show the coordinates that will be used to search the Foursquare API for businesses. As can be easily seen, even if the blue area sometimes extends to farther areas, the dots tend towards the center as the coordinates represent the main urban areas, this means that we are searching for businesses in important areas and not in remote ones.

# In[40]:


CLIENT_ID = '2TY3MKVBZBKCWR4B0EI1MMCK3NWPJTFNPQ0YKIYMO5A5V51N' # your Foursquare ID
CLIENT_SECRET = 'B23XB004NESNRQTAMWCMY2Z0VH3RYCXEEYY0TTOIYVWTSSMB' # your Foursquare Secret
VERSION = '20180605' # Foursquare API version
LIMIT = 100 # A default Foursquare API limit value

def getNearbyVenues(names, latitudes, longitudes, radius=500):
    
    venues_list=[]
    for name, lat, lng in zip(names, latitudes, longitudes):
        print(name)
            
        # create the API request URL
        url = 'https://api.foursquare.com/v2/venues/explore?&client_id={}&client_secret={}&v={}&ll={},{}&radius={}&limit={}'.format(
            CLIENT_ID, 
            CLIENT_SECRET, 
            VERSION, 
            lat, 
            lng, 
            radius, 
            LIMIT)
            
        # make the GET request
        results = requests.get(url).json()["response"]['groups'][0]['items']
        
        # return only relevant information for each nearby venue
        venues_list.append([(
            name, 
            lat, 
            lng, 
            v['venue']['name'], 
            v['venue']['location']['lat'], 
            v['venue']['location']['lng'],  
            v['venue']['categories'][0]['name']) for v in results])

    nearby_venues = pd.DataFrame([item for venue_list in venues_list for item in venue_list])
    nearby_venues.columns = ['Districts', 
                  'District Latitude', 
                  'District Longitude', 
                  'Venue', 
                  'Venue Latitude', 
                  'Venue Longitude', 
                  'Venue Category']
    
    return(nearby_venues)

gam_venues = getNearbyVenues(names=coord['NOM_CANT_1'],
                                   latitudes=coord['LAT'],
                                   longitudes=coord['LONG']
                                  )
print(gam_venues.shape)
gam_venues.head()


# In[41]:


gam_venues.groupby('Districts').count()


# In[42]:


gam_onehot = pd.get_dummies(gam_venues[['Venue Category']], prefix="", prefix_sep="")

gam_onehot['Districts'] = gam_venues['Districts'] 

fixed_columns = [gam_onehot.columns[-1]] + list(gam_onehot.columns[:-1])
gam_onehot = gam_onehot[fixed_columns]

gam_onehot.head()


# In[43]:


gam_grouped = gam_onehot.groupby('Districts').mean().reset_index()
gam_grouped


# In[52]:


num_top_venues = 3

for hood in gam_grouped['Districts']:
    print("----"+hood+"----")
    temp = gam_grouped[gam_grouped['Districts'] == hood].T.reset_index()
    temp.columns = ['venue','freq']
    temp = temp.iloc[1:]
    temp['freq'] = temp['freq'].astype(float)
    temp = temp.round({'freq': 2})
    print(temp.sort_values('freq', ascending=False).reset_index(drop=True).head(num_top_venues))
    print('\n')


# In[55]:


def return_most_common_venues(row, num_top_venues):
    row_categories = row.iloc[1:]
    row_categories_sorted = row_categories.sort_values(ascending=False)
    
    return row_categories_sorted.index.values[0:num_top_venues]
num_top_venues = 3

indicators = ['st', 'nd', 'rd']

columns = ['Districts']
for ind in np.arange(num_top_venues):
    try:
        columns.append('{}{} Most Common Venue'.format(ind+1, indicators[ind]))
    except:
        columns.append('{}th Most Common Venue'.format(ind+1))

districts_venues_sorted = pd.DataFrame(columns=columns)
districts_venues_sorted['Districts'] = gam_grouped['Districts']

districts_venues_sorted.head()


# In[61]:


for ind in np.arange(gam_grouped.shape[0]):
    districts_venues_sorted.iloc[ind, 1:] = return_most_common_venues(gam_grouped.iloc[ind, :], num_top_venues)

districts_venues_sorted.head(28)


# **THIS IS THE LIST FOR EACH DISTRICT WITH THE TOP 3 VENUES**

# In[65]:


coord.info()


# In[66]:


coord.head(28)


# In[82]:


df["Area"] = ""
for i in range(len(coord['LONG'])):
    if coord.iloc[i,7] < -84.090725:
        coord.iloc[i,8] = 'West'
    else:
        coord.iloc[i,8] = 'East'


# In[83]:


coord.head(27)


# We now have a list of businesses in each district and have defined the area 'code' for each district depending if it's east or west. This concludes the first week of the project. For the next week I expect to present additional descriptive statistics and visualizations for the project and to formalize any conclutions and present any weaknesses found. Furthermore, we will need to use additonal code to condense the data from a district point of view to an area point of view as that is the final objective.

# In[ ]:




