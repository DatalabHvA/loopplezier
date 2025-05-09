# packages
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import shortest_path
import time
import networkx as nx
import joblib


# def probabilitiesMoves(a,s,s_norm,i_c,j_e,g_c,g_min,g_max,tabu,tau, alpha, beta, dist_matrix):
#     # Bepaal naar welke knooppunten een ant kan bewegen en wat de kans is voor elk knooppunt
#     # i_c: huidige node van ant
#     # j_e: eindpunt
#     # g_c: afstand tot nu toe
#     # g_min/gmax: minimale en maximale afstand
#     # tabu: punten die al bezocht zijn
    
#     possibleMoves = np.where(a[:,i_c]<1000)[0]

#     probabilityMoves = np.zeros(len(possibleMoves))
    
#     for i in range(len(possibleMoves)):
#         j = possibleMoves[i]
#         if j in tabu: # al bezocht 
#             probabilityMoves[i] = 0
#         elif dist_matrix[j] + g_c + a[i_c,j] > g_max: # te lange route tot eindpunt
#             probabilityMoves[i] = 0
#         elif j == j_e and g_c + a[i_c,j] < g_min: # te kort om te stoppen
#             probabilityMoves[i] = 0
#         else:
#             probabilityMoves[i] = tau[i_c,j]**alpha * ((s_norm[i_c,j]+0.1)/a[i_c,j])**beta

#     if sum(probabilityMoves) > 0:
#         probabilityMoves /= sum(probabilityMoves)

#     return possibleMoves, probabilityMoves


# def selectMove(probabilities):
#     # trek random item aan de hand van kansverdeling
    
#     rand = np.random.rand(1)
    
#     for i in range(len(probabilities)):
#         if sum(probabilities[:(i+1)]) > rand:
#             index = i 
#             break
    
#     return index



def distanceScoreRoute(a,s,solution):
    # Bereken de adstand en score gegeven een route
    
    distance = 0
    score = 0 
    for i in range(len(solution)-1):
        distance += a[solution[i], solution[i+1]]
        score += s[solution[i], solution[i+1]]
        
    if distance >0:
        score /= distance

    return distance, score

def SelectMove(a,s_norm,i_c,j_e,g_c,g_min,g_max,tabu,tau, alpha, beta, dist_matrix):
    # Bepaal naar welke knooppunten een ant kan bewegen en wat de kans is voor elk knooppunt
    # i_c: huidige node van ant
    # j_e: eindpunt
    # g_c: afstand tot nu toe
    # g_min/gmax: minimale en maximale afstand
    # tabu: punten die al bezocht zijn
    
    possibleMoves = np.where(a[:,i_c]<1000)[0]
    
    len_possibleMoves = len(possibleMoves)

    probabilityMoves = np.zeros(len_possibleMoves)
    
    for i in range(len_possibleMoves):
        j = possibleMoves[i]
        if j in tabu: # al bezocht 
            probabilityMoves[i] = 0
        elif dist_matrix[j] + g_c + a[i_c,j] > g_max: # te lange route tot eindpunt
            probabilityMoves[i] = 0
        elif j == j_e and g_c + a[i_c,j] < g_min: # te kort om te stoppen
            probabilityMoves[i] = 0
        else:
            probabilityMoves[i] = tau[i_c,j]**alpha * ((s_norm[i_c,j])/a[i_c,j])**beta

    if sum(probabilityMoves) > 0:
        probabilityMoves /= sum(probabilityMoves)
    else:
        return -1
    
    rand = np.random.rand(1)
    
    for i in range(len_possibleMoves):
        if sum(probabilityMoves[:(i+1)]) > rand:
            return possibleMoves[i]
        
    # if sum(probabilityMoves) == 0:
    #     print('afstand',g_c)
    #     print('huidig punt',i_c)
    #     print('mogelijke bewegingen',possibleMoves)
    #     print('al geweest',tabu)
    
    return -1


	
# def looproutes_ant_colony_optimization(a,s,s_norm,i_s,j_e,g_min,g_max,n_ants = 200,n_iter = 12,alpha = 0.5,beta =0.5,rho = 0.5,Q3 = 1,paths = []):
#     # ant colony optimization om looproutes te bepalen
#     n = a.shape[0]
    
#     start_time = time.time()
#     # Kortste path van elke route naar eindpunt
#     dist_matrix = shortest_path(csgraph=csr_matrix(a), directed=False, indices=j_e)

#     # initialisatie tau
#     # Voor alle i,j zet tau_ij(0) op 1

#     tau = np.ones((n,n))
#     #"""
#     for i in range(len(paths)):
#         _,score = distanceScoreRoute(a,s,paths[i])
#         for j in range(len(paths[i])-1):
#             tau[paths[i][j],paths[i][j+1]] += Q3*score
#     #"""

#     # beste route bewaren
#     opt_route = []
#     opt_value = 0
#     opt_distance = 0

#     # algoritme
#     for i in range(n_iter):
#         # Zorg dat voor alle ants bijgehouden wordt bij welke nodes ze al zijn geweest.
#         # Ze starten allemaal in het startpunt.
#         tabu = []

#         current_length = np.zeros(n_ants)
#         current_value = np.zeros(n_ants)
#         value_ant = np.zeros(n_ants)

#         for k in range(n_ants):
#             tabu.append([i_s])

#         # aantal ants dat eindpunt hebben bereikt
#         end = 0

#         # alle mieren bewegen over netwerk tot ze eindpunt bereiken of niet meer verder kunnen.
#         while end < n_ants:  
#             for k in range(n_ants):
#                 if tabu[k][-1] != j_e:
#                     possibleMoves, probabilityMoves = probabilitiesMoves(a,s,s_norm,tabu[k][-1],j_e,current_length[k],g_min,g_max,tabu[k],tau, alpha, beta,dist_matrix)
#                     if sum(probabilityMoves) > 0:
#                         move = possibleMoves[selectMove(probabilityMoves)]
#                         current_length[k] += a[tabu[k][-1],move]
#                         current_value[k] += s[tabu[k][-1],move]
#                         tabu[k].append(move)
#                         if move == j_e:
#                             value_ant[k] = current_value[k]/current_length[k]
#                             end += 1
#                     else:
#                         tabu[k].append(j_e)
#                         value_ant[k] = 0
#                         end += 1
#         # update tau   
#         tau *= rho
#         for k in range(n_ants):
#             for i in range(len(tabu[k])-1):
#                 tau[tabu[k][i],tabu[k][i+1]] += Q3*value_ant[k]

#         # beste route bewaren:
#         if max(value_ant) > opt_value:
#             opt_route = tabu[np.argmax(value_ant)]
#             opt_value = max(value_ant)
#             opt_distance = current_length[np.argmax(value_ant)]

#     runtime = time.time()-start_time
    
#     return opt_route, opt_distance, opt_value, runtime

def looproutes_ant_colony_optimization(a,s,i_s,j_e,g_min,g_max,n_ants = 100,n_iter = 100,alpha = 0.5,beta =0.5,rho = 0.5,Q3 = 1,paths = []):
    # ant colony optimization om looproutes te bepalen
    n = a.shape[0]

    # normaliseer s zodat score altijd positief is. 
    s_norm = s.copy()
    s_norm -= np.min(s_norm) - 0.1
    s_norm /= np.max(s_norm)
    
    start_time = time.time()
    # Kortste path van elke route naar eindpunt
    dist_matrix = shortest_path(csgraph=csr_matrix(a), directed=False, indices=j_e)

    # beste route bewaren
    opt_route = []
    opt_value = -10
    opt_distance = 0
    
    # initialisatie tau
    # Voor alle i,j zet tau_ij(0) op 1

    tau = np.ones((n,n))
    
    for i in range(len(paths)):
        distance,score = distanceScoreRoute(a,s,paths[i])
        if score > opt_value: 
            opt_route = paths[i]
            opt_value = score
            opt_distance = distance
        for j in range(len(paths[i])-1):
            tau[paths[i][j],paths[i][j+1]] += Q3*score

    # algoritme
    for i in range(n_iter):
        # print('iter', i)
        # Zorg dat voor alle ants bijgehouden wordt bij welke nodes ze al zijn geweest.
        # Ze starten allemaal in het startpunt.
        tabu = []

        for i in range(n_ants):
            tabu.append([i_s])
        
        current_length = np.zeros(n_ants)
        current_value = np.zeros(n_ants)
        value_ant = np.zeros(n_ants)

        # aantal ants dat eindpunt hebben bereikt
        end = 0

        # alle mieren bewegen over netwerk tot ze eindpunt bereiken of niet meer verder kunnen.
        list_ants = list(range(n_ants))
        while end < n_ants:  
            for k in list_ants:
                #possibleMoves, probabilityMoves = probabilitiesMoves(a,s_norm,tabu[k][-1],j_e,current_length[k],g_min,g_max,tabu[k],tau, alpha, beta,dist_matrix)
                move = SelectMove(a,s_norm,tabu[k][-1],j_e,current_length[k],g_min,g_max,tabu[k],tau,alpha,beta,dist_matrix)
                if move == -1:
                    value_ant[k] = -10
                    list_ants.remove(k)
                    end += 1
                else:
                    #move = possibleMoves[selectMove(probabilityMoves)]
                    # print(move)
                    current_length[k] += a[tabu[k][-1],move]
                    current_value[k] += s[tabu[k][-1],move]
                    tabu[k].append(move)
                    if move == j_e:
                        value_ant[k] = current_value[k]/current_length[k]
                        #print(value_ant)
                        list_ants.remove(k)
                        end += 1
        
        # update tau  
        if min(value_ant)<0:
            value_ant += abs(min(value_ant)) 
            
        tau *= rho
        for k in range(n_ants):
            for i in range(len(tabu[k])-1):
                tau[tabu[k][i],tabu[k][i+1]] += Q3*value_ant[k]

        # beste route bewaren:
        if max(value_ant) > opt_value:
            opt_route = tabu[np.argmax(value_ant)]
            opt_value = max(value_ant)
            opt_distance = current_length[np.argmax(value_ant)]
            
    _,opt_value = distanceScoreRoute(a,s,opt_route)

    runtime = time.time()-start_time
    
    return opt_route, opt_distance, opt_value, runtime

def smallMatrices(a,s,g_max,i_s,j_e):
    # verkleint de matrix adhv maximale afstand, zodat alleen knooppunten 
    # die ook daadwerkelijk bereikt kunnen worden, worden meegenomen.
    
    G_sparse = csr_matrix(a)

    dist_matrix1, predecessors = shortest_path(csgraph=G_sparse, directed=False, indices=i_s, return_predecessors=True)
    dist_matrix2, predecessors = shortest_path(csgraph=G_sparse, directed=False, indices=j_e, return_predecessors=True)

    indices1 = np.where(dist_matrix1<g_max/2)[0]
    indices2 = np.where(dist_matrix2<g_max/2)[0] 
    
    if len(np.intersect1d(indices1,indices2)) > 0:
        indices3 = np.where(dist_matrix1<g_max)[0]
        indices4 = np.where(dist_matrix2<g_max)[0]
        indices = np.union1d(indices1,indices2)
        indices = np.intersect1d(indices,indices3)
        indices = np.intersect1d(indices,indices4)    
        
        a_new = a[indices,:][:,indices]
        s_new = s[indices,:][:,indices]
        i_s_new = int(np.where(indices==i_s)[0])
        j_e_new = int(np.where(indices==j_e)[0])
    else: 
        indices = np.intersect1d(indices1,indices2)
        
        a_new = a[indices,:][:,indices]
        s_new = s[indices,:][:,indices]
        i_s_new = 0
        j_e_new = 0
    
    return a_new, s_new, i_s_new, j_e_new, indices