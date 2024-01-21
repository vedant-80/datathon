import pandas as pd
import operator
import math
import seaborn as sns
import numpy as np
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import matplotlib.pyplot as plt

#import dataset
fda_df = pd.read_csv("CAERS_ProductBased.csv")

#remove any null product_name or case_outcome
fda_df.dropna(subset=['PRODUCT', 'CASE_OUTCOME'], inplace=True)

"""
correlate # of suspect cases with products/product codes
correlate # of concomitant cases with products/product codes
correlate symptoms with products/product codes


Bare Bones Subset:
DATE_FDA_FIRST_RECEIVED_REPORT- remove
REPORT_ID - remove
DATE_EVENT - remove
PRODUCT_TYPE - keep
PRODUCT	- keep
PRODUCT_CODE - remove
DESCRIPTION	- remove
PATIENT_AGE	- remove
AGE_UNITS- remove 
SEX	- remove
CASE_MEDDRA_PREFERRED_TERMS/symptoms - keep
CASE_OUTCOME/seriousness - keep


"""

#drop exemptions
fda_df = fda_df.drop(fda_df[fda_df['PRODUCT'] == 'EXEMPTION 4'].index)

#make all products lowercase

fda_df['PRODUCT'] = fda_df['PRODUCT'].str.lower()
fda_df['CASE_OUTCOME'] = fda_df['CASE_OUTCOME'].str.lower()


#create subset of data with product type, product, sympotms, and case outcome
bare_bones_fda = fda_df.drop(columns=["DATE_FDA_FIRST_RECEIVED_REPORT", "DATE_EVENT", "PRODUCT_CODE", "DESCRIPTION", "PATIENT_AGE", "AGE_UNITS", "SEX"])

"""
Types of outcomes:

Death - 1

Life threatening - 2

Hospitalization - 3
Disability - 3
Congenital anomaly - 3
Other serious medical event - 3
Other serious or important medical event - 3

Visited emergency room - 4
Other serious outcome - 4

Visited a healthcare provider - 5
Injury - 5
Allergic reaction - 5
Required intervention - 5
Other outcome (?) - 5

"""



def get_score(outcome):
    outcome = str(outcome)
    if 'death' in outcome:
        return 5
    elif 'life threatening' in outcome:
        return 4
    elif ('hospitalization' or 'disability' or 'congenital anomaly' or 'other serious or important medical event') in outcome:
        return 3
    elif ('visited emergency room' or 'other serious outcome') in outcome:
        return 2
    else:
        return 1


fda_df['SCORE'] = fda_df['CASE_OUTCOME'].apply(get_score)


#converts patient age of decades to years and weeks/months/days to 0 
fda_df.loc[fda_df.AGE_UNITS=='decade(s)', 'PATIENT_AGE'] *= 10
fda_df.loc[fda_df.AGE_UNITS=='week(s)', 'PATIENT_AGE'] *= 0
fda_df.loc[fda_df.AGE_UNITS=='day(s)', 'PATIENT_AGE'] *= 0
fda_df.loc[fda_df.AGE_UNITS=='month(s)', 'PATIENT_AGE'] *= 0

#creates age groups
def age_change(patient_age):
        
    if patient_age >= 65:
        return 'senior'
    elif patient_age >= 36:
        return 'middle age'
    elif patient_age >= 18:
        return 'adults'
    elif patient_age >= 13:
        return 'teens'
    elif patient_age >= 4:
        return 'kids'
    elif math.isnan(patient_age):
        return 'age not available'    
    else:
        return 'infants' 

#change decades to years and everything else (besides years) to infant age
fda_df['AGE_GROUP'] = fda_df['PATIENT_AGE'].apply(age_change)


#making suspect-only subset
fda_suspect_df = fda_df.drop(fda_df[fda_df['PRODUCT_TYPE']=='CONCOMITANT'].index)

#making cocomitant-only subset
fda_concomitant_df = fda_df.drop(fda_df[fda_df['PRODUCT_TYPE']=='SUSPECT'].index)

#combining all concomitant product names with same report ID into the same row
fda_concomitant_df = fda_concomitant_df.groupby('REPORT_ID').agg({
'PRODUCT': lambda x: ', '.join(x)
})   

#merging suspect w/ concomitant to add new column to suspect df
merged_df = pd.merge(fda_suspect_df, fda_concomitant_df, on = 'REPORT_ID', how='left')

#different trials for the graph
#merged_df = merged_df[merged_df['SEX']=='Male']
#merged_df = merged_df[merged_df['SEX']=='Female']
#merged_df = merged_df[merged_df['AGE_GROUP']=='senior']
#merged_df = merged_df[merged_df['AGE_GROUP']=='middle age']
#merged_df = merged_df[merged_df['AGE_GROUP']=='adult']
#merged_df = merged_df[merged_df['AGE_GROUP']=='teens']
#merged_df = merged_df[merged_df['AGE_GROUP']=='kids']
#merged_df = merged_df[merged_df['AGE_GROUP']=='infants']


#makes dictionary of products:number of cases
product_list = merged_df['PRODUCT_x'].tolist()

severity_list = merged_df['SCORE'].tolist()
age_list = merged_df['AGE_GROUP'].tolist()

#create map from products to occurences, etc.
products_dict = {}
severity_dict = {}
age_dict = {}

for index in range(len(product_list)):
    if product_list[index] in products_dict:
        products_dict[product_list[index]] += 1
        severity_dict[product_list[index]] += severity_list[index]
        
    else:
        products_dict[product_list[index]] = 1
        severity_dict[product_list[index]] = severity_list[index]

for item in list(products_dict.keys()):
    if products_dict[item] < 0:
        del products_dict[item]
        del severity_dict[item]

score_avg = {}
for item in products_dict:
    score_avg[item] = severity_dict[item]/products_dict[item]


#map diff metrics from dicts
merged_df['AVG_SCORE'] = merged_df['PRODUCT_x'].map(score_avg)
merged_df['OCCURENCES'] = merged_df['PRODUCT_x'].map(products_dict)

filtered_df = merged_df[merged_df['OCCURENCES'] > 300]

sns.barplot(x='PRODUCT_x', y='OCCURENCES', hue='AGE_GROUP', data=filtered_df)
plt.show()

