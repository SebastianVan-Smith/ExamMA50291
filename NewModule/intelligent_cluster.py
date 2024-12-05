
"""seperation method = starting_point_adjsutment or variance adjustment
with starting point adjustment we can have parameter that is the maximal alowed deviation form the starting points position
wiht variance adjustment we can have a minimum alowed variance for each point

I am going to take the definition fo a well defined cluster to be
 set of objects in which each object is closer (or more similar) 
 to every other object in the cluster than to any object not in the 
 cluster
apparently this is also called the strict definition
there is anoth definition which is that each point has to be closer to the cluster center than any other cluster center
but as it wasnt specified i am going to sue the strict definition

there the distance between each cluster must be more than D/4
where D is the distance between the starting points of the clusters

we can acheive this in two ways:
    1. starting point adjustment
    2. variance adjustment
where starting point adjustment moves the starting points away from eachother 
such that they have minimum separation of D/4 accoring to a user specified variance
and variance adjustment moves the points away from the starting point such that 
the user specified variance is their maximum variance and is scaled
to fit the current distance between each point to a mimimum variance
which if reached will result in "no clustering possible" error


OKAY i just read the quesiton agian and it wants me to use simulate data

icl this is really hard to do with the restrciton that we have to use simulate_data
you get a really really suboptimal solution as all axis for each cluster need to be the same length
e.g for well seperated clusters the radius of points generated by the cluster have to be d/4 where d is the shortest distance between the starting points 
of the cluster and any other cluster starting point 
i cant specify a radius of points i need to specify variance per axis which needed to be bounded bt sqrt((d/4)/numaxis) to guarentee that in the worst case the points are
at most d/4 away from the seed point
but that means i cant for example have a point in a cluster with d/4 distacne form the seed on one axis and 0 on the other 
so the clusters i can generate are actually the smallest hypercube that fits in the hyper sphere of allowed points which is a really bad approximation
which means that as n dim increases the clusters will become infinitely small as the ratio of the hyper cube to hyper sphere goes to 0

if i had to do this without the restriciton of using simulate data it would be the same as my plan above :)

i could do it so that the original points are moved to alowed for the suer specified variacne however they would still have to be changed to normal 
and it isnt very transparant how your data has been manipulated so i thought the variance modificaiton way better
"""


#error handling for imports
try:
    import pandas as pd
    import numpy as np
    from scipy.spatial.distance import cdist
    from cluster_maker import simulate_data
except ImportError as e:
    print(f"Error importing required libraries: {e}")

def create_well_separated_clusters(seed_df, n_points=100, col_specs=None, separation=0, random_state=None):
    """
    Create clusters based on the seed dataframe, adjusting the col spec to ensure they are well separated.
    This approch is suboptimal due to restriciton of having to use simulate_data, please read header of file for more info

    Seperation will be in addition to the minimum distnace needed to satisfy the well seperated condition
    if you want the maximum possible clusters just put a really large variance into the col spec and it will constrain it to the maximum possible variance
    
    Parameters:
        seed_df (pd.DataFrame): DataFrame with numerical representative points (the "seed").
        n_points (int): Number of points to generate per representative.
        col_specs (dict): Column-specific simulation specifications.
        separation (float): Minimum distance between cluster centers.
        random_state (int, optional): Random seed for reproducibility.

    Returns:
        pd.DataFrame: DataFrame containing the simulated data points with well-separated clusters.
    """
    try:
        if not isinstance(seed_df, pd.DataFrame):
            raise TypeError("seed_df must be a pandas DataFrame")
        if seed_df.empty:
            raise ValueError("seed_df must not be an empty DataFrame")
        if not isinstance(n_points, int) or n_points <= 0:
            raise ValueError("n_points must be a positive integer")
        if col_specs is not None and not isinstance(col_specs, dict):
            raise TypeError("col_specs must be a dictionary if provided")
        if not isinstance(separation, (int, float)) or separation < 0:
            raise ValueError("separation must be a positive number")
        if random_state is not None and not isinstance(random_state, int):
            raise TypeError("random_state must be an integer if provided")

        if random_state is not None:
            np.random.seed(random_state)

        # Copy seed_df to avoid modifying the original
        col_specs = col_specs.copy()
        
        #calculate the minimum distance between cluster centers
        distances = cdist(seed_df.values,seed_df.values, metric='euclidean')

        #set the diagonal to inf as we dont care about the distance between the same cluster
        np.fill_diagonal(distances, np.inf)

        #throw error if the additional seperation would make the variance negative to satisfy the condition
        if (np.min(distances)/4) < separation:
            raise ValueError("Clusters are too close together to achieve the desired separation., lower seperation")

        

        #create a maximal r for each cluster based on its min distance to every other cluster /4
        maximal_r = np.min(distances,axis=1)/4 - separation/2 #get the maximal radius for each cluster
        print(F"\nMaximal radius allowed for each cluster to be well seperated: {maximal_r}")
        print(f"\nAs we need to specify the variance per axis we need to take the minimum of this as we cant specify per cluster: {np.min(maximal_r)}")

        maximal_r = np.sqrt(np.min(maximal_r)/len(seed_df.columns)) #divide the maximal r by the number of columns to get the maximal r for each column
        print(f"\nAs we need to specify the variance per axis and cant do a radius for a cluster we need to use the volume of a hyper cube that fits in the hyper sphere of the allowed points, this is: {maximal_r}")
                
        #create colspec for each cluster which is based on the passed through colspec but with the maximal r
        #for each cluster
        print("\nConstraining user given colspec to create well seperated clusters")
        for i,col in enumerate(seed_df.columns):
            #if there is no given col spec for a column then create one with maximal alowed r
            if col not in col_specs:
                col_specs[col] = {'distribution': 'uniform', 'variance': maximal_r}
            else:
                #if there is a given col spec then check if the variance is less than the maximal r
                if col_specs[col]['variance'] > maximal_r:
                    col_specs[col]['variance'] = maximal_r

                #change all distributions to uniform and print that it has been done as with a normal distribution we cant guarentee the points are within the hyper sphere
                if col_specs[col]['distribution'] != 'uniform':
                    col_specs[col]['distribution'] = 'uniform'
                    print(f"col: {col} distribution changed to uniform so to not have points outside of the hyper sphere")
        print("\nThe col spec has been modified to fit the constraints of the problem, the colspec with variance that best matches the input that can generate well seperated data is:\n")
        #print final colspec to see changes that were needed
        print(col_specs)
        return simulate_data(seed_df, n_points, col_specs, random_state)

    
    except (TypeError, ValueError) as e:
        print(f"Error creating well-separated clusters: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

