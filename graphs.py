import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from adjustText import adjust_text

def plot_shot_dist(dists, outcomes, firstname, lastname):
    """
    Plots the shot distance vs field goals, with seperate bars for made and missed field goals
    """

    plt.figure(figsize = (10,12))

    makes,misses = [],[]

    for i in enumerate(dists):
        if outcomes[i[0]] == 'make':
            makes.append(i[1])
        else:
            misses.append(i[1])

    max_dist = int(max(makes))
    misses = [x for x in misses if x <= max_dist]

    plt.title(firstname + ' ' + lastname + '(2016-2020)')
    plt.ylabel('Number of Shots')
    plt.xlabel('Shot Distance (ft)')
    plt.hist([makes,misses], max_dist, label = ['Makes','Misses'], color = ['g','r'], alpha = 0.5)
    plt.legend(loc = 'best')
    plt.show()

def plot_clutch(data):
    """
    Plots points vs. FG% in clutch time (<=2 minutes left and point discrepency of <=5)
    """

    plt.figure(figsize = (10,12))

    stat_dict = {}

    for i in enumerate(data.Shooter):
        index = i[1].find('-')
        data.at[i[0], 'Shooter'] = i[1][:index-1]

    all_names = np.unique(data.Shooter)
    stat_dict = dict.fromkeys(all_names, [0,0])
    
    for name in all_names:
        fga = data[data.Shooter == name]
        fgm = fga[data.ShotOutcome == 'make'].count()[0]
        fga = fga.count()[0]

        fg_perc = fgm/fga

        stat_dict[name] = [fg_perc, fga]

    percents = []
    fga = []
    texts = []

    for name in all_names:
        if stat_dict[name][1] > 100:
            percents.append(stat_dict[name][0])
            fga.append(stat_dict[name][1])
            texts.append(plt.text(stat_dict[name][0],stat_dict[name][1], name, ha = 'center', va = 'center'))

    plt.title('Clutch FGA vs FG%, >100 clutch shots, (2016-2020)')
    plt.xlabel('FG%')
    plt.ylabel('FGA')
    plt.scatter(percents, fga)
    adjust_text(texts, arrowprops=dict(arrowstyle='->', color='red'))
    plt.show()


def plot_consistency(data):
    """
    Creates a plot of consistency vs. the given stat per game
    """

    plt.figure(figsize = (w,h))

    nms = np.unique(data.name.values)

    stat_dict = dict.fromkeys(nms, [0,0])

    stds = []
    ppgs = []
    texts = []

    for nm in nms:
        stats = pd.Series(data[data.name == nm].to_numpy()[:, 1])
        
        std = pd.Series.std(stats)

        # Put the stats in a dictionary and remove players with 0 STD to avoid divide by zero errors
        if std !=0:
            stat_dict[nm] = [pd.Series.mean(stats), 1/pd.Series.std(stats)]
        else:
            stat_dict[nm] = [pd.Series.mean(stats), -1]

    for nm in nms:
        # Change the number after stat_dict[nm][0]> to have that be the minimum 
        # stat per game displayed on the plot
        if stat_dict[nm][0]>17 and stat_dict[nm][1] > 0:
            ppgs.append(stat_dict[nm][0])
            stds.append(stat_dict[nm][1])
            texts.append(plt.text(stat_dict[nm][0],stat_dict[nm][1], nm, ha = 'center', va = 'center'))

    plt.title('Consistency Rating vs. Points per Game (2012-2018)')
    plt.xlabel('PPG')
    plt.ylabel('Consistency (1/std)')
    plt.scatter(ppgs, stds)
    adjust_text(texts, arrowprops=dict(arrowstyle='->', color='red'))
    plt.show()
