import numpy as np
import pandas as pd
import random
import settings1 
import settings2

# settings.init()  
# find Closest number in a list

def closest(lst, K):
	
	return lst[min(range(len(lst)), key = lambda i: abs(lst[i]-K))]
	


def q_learning(MG, chp, deficit, surplus, gbp, gsp, mbp, msp, chp_cost, chp_ratio, total_surplus,total_deficit):
    # rewards = pd.DataFrame(np.zeros((25, 20)))
    Column = 1.0
    Row = 1.0
    learning_rate=0.8
    discount=0.5
    R=0.2
    mbp_max= 8.5
    mbp_min= 4
    #CBE = 11.5
    #eagerness_charge=0.556
    #P_c = 250
    #mbp = 8.5
    #msp = 4
    
    # print("chp ration",chp_ratio)
    p_c = (mbp_max - mbp)/(mbp_max-mbp_min)  # preference to charge ESS/EV
    p_d = (mbp - mbp_min)/(mbp_max-mbp_min)  # preference to discharge ESS/EV
    no_of_states = 20
    no_of_actions = 15
    # gamma = (gbp - mbp) / no_of_states
    # print("pc",p_c)
    # print("pd",p_d)
    # print("gamma:", gamma)
    # Z = [9.225,9.45, 9.675,9.9,10.125,10.35,10.575,10.8,11.025,11.25,11.475,11.7,11.925,12.15,12.375,12.6,12.825,13.05,13.275,13.5]
    Y = []
    Z = []
    # print("Actions2:", Y2)
    # print(Z)
    # print(Y)
    i = 0
    for i in range(no_of_states):         
        a = (1 / no_of_states) * (i+1)
        Z.append(a) 

    for i in range(no_of_actions):
        Y.append(i) 
    # print(Y)
    qtable = pd.DataFrame(0, index=Y, columns=Z) # 1) Initialize Q(s x a) matrix with arbitrary value
    count = pd.DataFrame(0, index=Y, columns=Z)
    qtable_prev = pd.DataFrame(0, index=Y, columns=Z)
    # print(qtable)
    reward = 0.0
    for i in range(settings1.iterate):
        end_of_game = False
        Column = random.choice(Z) # 2.a) Choose an arbitrary state z as initial state
        # print("state=",Column)
        while not end_of_game:
            yr=random.choice(Y) # 2.b.i) Choose an action yr randomly from the set of actions
            # print("yr", yr)
            #print("max")
            maxrow,maxcol = qtable.stack().index[np.argmax(qtable.values)] # 2.b.ii) Choose another action yp such that yp = argmax Q_k-1(z,y)
            yp = float(maxrow)
            #maxcol = float(maxcol)
            
            #print(type(maxrow))
            # print(type(maxcol))
            # print("max", maxrow,maxcol)
            #yp = qtable.at[maxrow,maxcol]
            # print("yp",yp)
            
            # yp=qtable(pd.stack().index[np.argmax(pd.values)])
            # yp=qtable.max(axis={Y,Z})
            epsilon = random.random() # 2.b.iii) Choose a value for epsilon between 0 and 1
            

            # 2.b.iii) select the action yk
            if (epsilon < R):
                yk=yp
            else:
                yk=yr
            # print("yk",yk)
            Row = int(yk)
            # 2.b.iv) receive the reward 
            predicted_stress = maxcol
            # print("MCP=",MCP)
            # print("Row:",Row)
            # print("Column:", Column)
            if MG == 'IND':
                if deficit > 0:
                    MG_stress = deficit / total_deficit
                    bidprice = gbp - (settings1.Y1[Row] * chp_ratio + settings1.Y2[Row] * predicted_stress)- (1 - MG_stress)
                    # print("bidprice:", bidprice)   
                    reward = (settings2.MCP - bidprice) * deficit - ((chp-80) * chp_cost)
                    # reward = (gbp - MCP) * deficit
                elif surplus > 0:
                    MG_stress = surplus / total_surplus
                    askprice = msp + (settings1.Y1[Row] * chp_ratio) + (settings1.Y2[Row] * (1 - predicted_stress))+ (1-MG_stress)
                    reward = (askprice - settings2.MCP) * surplus - ((chp-80) * chp_cost)
                    # # reward = (MCP - gsp) * surplus
            elif MG == 'COM':
                if deficit > 0:
                    MG_stress = deficit / total_deficit
                    bidprice = gbp - ((settings1.Y1[Row] * p_c +settings1. Y2[Row] * predicted_stress) )- (1 - MG_stress)
                    # print("bidprice:", bidprice)   
                    reward = (settings2.MCP - bidprice) * deficit - ((chp-80) * chp_cost)
                    # print("Reward:", reward)
                elif surplus > 0:
                    MG_stress = surplus / total_surplus
                    askprice = msp + (settings1.Y1[Row] * p_d + settings1.Y2[Row] * (1 - predicted_stress))+ (1-MG_stress)
                    reward = (askprice - settings2.MCP) * surplus - ((chp-80) * chp_cost)
            elif MG == 'SD':
                if deficit > 0:
                    MG_stress = deficit / total_deficit
                    bidprice = gbp - (settings1.Y1[Row] * p_c + settings1.Y2[Row] * predicted_stress)- (1 - MG_stress)
                    # print("bidprice:", bidprice)   
                    reward = (settings2.MCP - bidprice) * deficit - ((chp-80) * chp_cost)
                    # reward = (gbp - MCP) * deficit
                elif surplus > 0:
                    MG_stress = surplus / total_surplus
                    askprice = msp + (settings1.Y1[Row] * p_d + settings1.Y2[Row] * (1 - predicted_stress))+ (1-MG_stress)
                    reward = (askprice - settings2.MCP) * surplus - ((chp-80) * chp_cost)
            elif MG == 'CAMP':
                if deficit > 0:
                    MG_stress = deficit / total_deficit
                    bidprice = gbp - ((settings1.Y1[Row] * (p_c + predicted_stress)) + settings1.Y2[Row] * chp_ratio)- (1 - MG_stress)
                    # print("bidprice:", bidpriec)   
                    reward = (settings2.MCP - bidprice) * deficit - ((chp-80) * chp_cost)
                    # reward = (gbp - MCP) * deficit
                elif surplus > 0:
                    MG_stress = surplus / total_surplus
                    askprice = msp + (settings1.Y1[Row] * (p_d + (1 - predicted_stress)) + settings1.Y2[Row] * chp_ratio)+ (1-MG_stress)
                    reward = (askprice - settings2.MCP) * surplus - ((chp-80) * chp_cost)
            else:
                print("WRONG MICROGRID")
            # print("Reward", reward)
            # 2.b.v) Update the Q-matrix 
            # a=(1 - learning_rate) * qtable.at[Row, Column]
            q = ((1 - learning_rate) * qtable.at[Row, Column]) + (learning_rate * (reward + discount * qtable.at[maxrow,maxcol]- qtable.at[Row, Column]))
            # print("q-value", q)
            qtable.at[Row, Column] = q
            # print(qtable_prev.equals(qtable))
            # print("Previuos Qtable", qtable_prev)
            qtable_prev.at[Row, Column] = q
            count.at[Row, Column] = count.at[Row, Column] + 1
            # print("Qtable", qtable)
            learning_rate = 1 / count.at[Row, Column]
            # print("Learning Rate:", learning_rate)
            # print(count)
            
            end_of_game = True
    # else:
    #     print("Q-Table:", qtable)
  
    # average_qtable = [0] * no_of_actions
   
    # average_qtable = qtable.mean(axis=1)
    # # print("avg_qtable", average_qtable)
    # max_value = max(average_qtable)
    # # print("max value:", max_value)
    # # print("average_qtable type:", type(average_qtable))
    # max_index = average_qtable[average_qtable == max_value].index[0]
    # # print("max index:", max_index)
    
    # maxrow,maxcol = qtable.stack().index[np.argmax(qtable.values)]
    # Driver code
    stress = total_surplus / total_deficit
    Final_state = closest(Z, stress)
    Final_action = qtable[Final_state].idxmax()
    
    return Final_action

    
       
    
# a = q_learning('COM', chp = 80, deficit=55, surplus=0.0, gbp=7, gsp=5.7, mbp=3.8, msp=2.8, chp_cost=5.8, pv=0)
# print("Max action:", a)

  