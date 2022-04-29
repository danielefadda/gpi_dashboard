# An interactive dashboard for monitoring and understanding peace through time
## The world news tells us about peace


## Table of contents  
1. [Citing](#Citing)
2. [Abstract](#Abstract) 
3. [Data pre-processing and machine-learning](#Code_pre_mach)
4. [Visualization](#Code_dashboard)
6. [Demonstration of the dashboard](#demonstration_video)

## Citing
<a name="Citing"/>

If you use our code for the dashboard, please cite our paper:

Fadda, D., Pappalardo, L., and Voukelatou, V. (2022). An interactive dashboard for monitoring and understanding peace through time.

`@article{fadda2022dashboard, `<br/>
  `title={ An interactive dashboard for monitoring and understanding peace through time},` <br/>
  `author={Fadda, Daniele, Lappalardo, Luca, and Voukelatou, Vasiliki},` <br/>
 ` year={2022}
} `


## Abstract
<a name="Abstract"/>

Using python language we developed a dashboard, which mainly visualizes a global map with peace fluctuations at a monthly and country level. Between others, the dashboard provides monthly peace fluctuations even up to 6-months-ahead and the determinants of peace over the months. We also provide the corresponding code for reproducing and updating the dashboard.

This work has been supported by EU project H2020 [SoBigData++](https://cordis.europa.eu/project/id/871042) #87104

## Data pre-processing and machine-learning
<a name="Code_pre_mach"/>

This dashboard is created for the visualization of the results of the research paper: Voukelatou, V., Miliou, I., Giannotti, F., & Pappalardo, L. (2022). Understanding peace through the world news https://epjdatascience.springeropen.com/articles/10.1140/epjds/s13688-022-00315-z.
Therefore, the pre-processing and machine learning of the data can be reproduced using the code and the data found in the **folder** called `dashbord` in the github repository of the paper: https://github.com/VickyVouk/GDELT_GPI_SHAP_project. 
The final objective is to create the ETL (``Extract, Transform, Load'') CSV document. This CSV includes all relevant data to load on the dashboard. The CSV includes the official and predicted GPI values and the features that contribute to the predictions. 


## Visualization
<a name="Code_dashboard"/>

To generate the dashboard you need to load the CSV file called `all_countries_for_dashboard.csv` on the `gpi_dasboard.py` file.
You can find the dashboard in the ``web`` folder opening the ``index.html`` file. <br>
An online version of the dashboard can be found in: http://experiments.sobigdata.eu/gpi_prediction/

More details: The python script based on **Altair (a Declarative Visualization library)** loads and manipulates the CSV dataset and creates all the visualization elements of the dashboard. This process does not demand a server to dispatch the data, and it allows a non-expert user to easily develop and update the dashboard . 

## Demonstration of the dashboard
<a name="demonstration_video"/>

A demonstration video of our dashboard can be accessed via: www.youtube

