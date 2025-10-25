import pandas as pd
from numpy import asarray
from numpy import savetxt
import csv
from scipy.optimize import linprog
import os


ESS_max=100
EV_max=16
mbp_max= 8.5
mbp_min= 4
n_c = n_d = 0.9
chp_min=80
chp_max=200

# Read csv file into a DataFrame using relative path
# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(script_dir, 'Data_for_Qcode.csv')

# If Data_for_Qcode.csv doesn't exist in current folder, try Energy_data_v7.csv
if not os.path.exists(data_path):
    data_path = os.path.join(script_dir, 'Energy_data_v7.csv')

data = pd.read_csv(data_path)
#------------------------------CALCULATING SURPLUS/DEFICT ENERGY OF ALL 4 MG-------------------------------------------------
def getEnergyData(ESS_EV_Status, i):
    

    gbp=data.loc[i].at["GBP"]
    mbp=data.loc[i].at["MBP"]
    msp=data.loc[i].at["MSP"]
    gsp=data.loc[i].at["GSP"]
    chp_cost=data.loc[i].at["CHP_Cost"]

    p_c = (mbp_max - mbp)/(mbp_max-mbp_min)  # preference to charge ESS
    p_d = (mbp - mbp_min)/(mbp_max-mbp_min)  # preference to discharge ESS 
    print("p_c:", p_c)
    print("p_d:", p_d)
# Reading the CSV file
    load_ind = data.loc[i].at["IL1"]
    pv_ind = data.loc[i].at["IP1"]
    ind1 = industry(load_ind, pv_ind, gbp, mbp, msp, gsp, chp_cost)

    load_ind = data.loc[i].at["IL2"]
    pv_ind = data.loc[i].at["IP2"]
    ind2 = industry(load_ind, pv_ind, gbp, mbp, msp, gsp, chp_cost)

    load_com = data.loc[i].at["CL3"]
    pv_com = data.loc[i].at["CP3"]
    ESS_status = ESS_EV_Status["com1"]
    com3 = community(load_com, pv_com, gbp, mbp, msp, gsp, chp_cost, p_c, p_d, ESS_status)

    load_com = data.loc[i].at["CL4"]
    pv_com = data.loc[i].at["CP4"]
    ESS_status = ESS_EV_Status["com2"]
    com4 = community(load_com, pv_com, gbp, mbp, msp, gsp, chp_cost, p_c, p_d, ESS_status)

    ev_available=data.loc[i].at["EV_Avail"]
    load_sd = data.loc[i].at["SL5"]
    pv_sd = data.loc[i].at["SP5"]  
    EV_status = ESS_EV_Status["sd1"]
    sd5 = singleD(load_sd, pv_sd, gbp, mbp, msp, gsp, chp_cost, p_c, p_d, ev_available, EV_status)   

    load_sd = data.loc[i].at["SL6"]
    pv_sd = data.loc[i].at["SP6"]  
    EV_status = ESS_EV_Status["sd2"]
    sd6 = singleD(load_sd, pv_sd, gbp, mbp, msp, gsp, chp_cost, p_c, p_d, ev_available, EV_status)

    load_sd = data.loc[i].at["SL7"]
    pv_sd = data.loc[i].at["SP7"]  
    EV_status = ESS_EV_Status["sd3"]
    sd7 = singleD(load_sd, pv_sd, gbp, mbp, msp, gsp, chp_cost, p_c, p_d, ev_available, EV_status)

    load_camp = data.loc[i].at["CPL8"]
    pv_camp = data.loc[i].at["CPP8"]  
    ESS_status = ESS_EV_Status["camp"] 
    camp8 = campus(load_camp, pv_camp, gbp, mbp, msp, gsp, chp_cost, p_c, p_d, ESS_status)

    surdef = [i+1] + ind1 + ind2 + com3[0:2] + com4[0:2] + sd5[0:2] + sd6[0:2] + sd7[0:2] + camp8[0:3]
    ESS_EV_Updated= {"com1":com3[2], "com2":com4[2], "sd1":sd5[2], "sd2":sd6[2], "sd3":sd7[2], "camp":camp8[3]}
    # print("Surdef:", surdef)
    
    # Write to Energy_data_v7.csv in the same directory as this script
    output_path = os.path.join(script_dir, 'Energy_data_v7.csv')
    with open(output_path, 'a', newline='') as csvfile:
        writer=csv.writer(csvfile, delimiter=',')
        writer.writerow(surdef)
    
    return ESS_EV_Updated
    # -------------COMMUNITY MG--------------------------------------------------
        # load_com=data.loc[i].at["load_com"]
        # pv_com=data.loc[i].at["PV_com"]
        
def community(load_com, pv_com, gbp, mbp, msp, gsp, chp_cost, p_c, p_d, ESS_com):
        # print("iteration:", i)
    # print("load at community MG:", load_com, "PV:", pv_com)

    
    # print("pc:",p_c,"pd:",p_d)
    ESS_charge_com = ESS_max - ESS_com  # energy needed by ESS to fully charge
    # print("ESS charge", ESS_charge_com)
    deficit_com = 0.0
    surplus_com = 0.0
    if load_com >= pv_com:
        rem_load_com = load_com-pv_com  # remaining load at community MG
        pv_com=0
        deficit_com = rem_load_com
    else:                                   # if load_com < pv_com
        pv_com = pv_com - load_com
        rem_load_com = deficit_com = 0
        # surplus_com = pv_com
        if pv_com > 0:
            if ESS_com < 100:
                
                if pv_com <= (ESS_charge_com * 1.10):
                    ESS_com = ESS_com + (pv_com - (pv_com * 0.10)) 
                    pv_com = 0
                else:
                    ESS_com = ESS_com + (ESS_charge_com * 1.10)
                    pv_com = pv_com - (ESS_charge_com * 1.10)
                    surplus_com = pv_com
            else:
                surplus_com = pv_com
            ESS_charge_com = ESS_max - ESS_com  # energy needed by ESS to fully charge after some portion charged by PV
    if p_c >= 0.5:
        if ESS_com < ESS_max:
            deficit_com = rem_load_com + (ESS_charge_com * 1.10) #deficit at community MG
            ESS_com = ESS_com + ESS_charge_com
    elif p_d >= 0.5:
        if ESS_com > 0:
            if (rem_load_com * 1.10) <= ESS_com:    # if energy at ESS is more than load at community MG             
                deficit_com = 0
                ESS_com = ESS_com - (rem_load_com * 1.10)      # energy at ESS is reduced at community MG
                surplus_com = surplus_com + ESS_com
                ESS_com = 0
            else:                               # if energy at ESS is less than load 
                deficit_com = (rem_load_com * 1.10) - ESS_com 
                ESS_com = 0
    else:
        surplus_com = rem_load_com
    
        # if ESS_com <
        #  100:
        #     if p_c >= 0.5:
        #         deficit_com = rem_load_com + (ESS_charge_com * 1.10) #deficit at community MG
        #         ESS_com = ESS_com + ESS_charge_com
        #     elif p_d >= 0.5:
        #     # if rem_load_com <= ESS_com:    # if energy at ESS is more than load at community MG             
        #         #     deficit_com = 0
        #            # ESS_com = ESS_com - (ESS_com * 0.10) - rem_load_com     # energy at ESS is reduced at community MG
        #         surplus_com = surplus_com + ESS_com
        #         ESS_com = 0
                # else:                               # if energy at ESS is less than load 
                #     deficit_com = rem_load_com - (ESS_com * 0.90) 
                #     ESS_com = 0

    community_energy=[deficit_com,surplus_com, ESS_com]
    # with open('D:\\IIITN\\PhD\\Reinforcement_Learning_implementation\\Community_Energy_data_v3.csv', 'a') as csvfile:
    #     writer=csv.writer(csvfile, delimiter=',')
    #     writer.writerow(community_energy)
    
    # print("remaining load",rem_load_com)
    # print("Community MG status:", community_energy)
    # print("Deficit at community mg:",deficit_com)
    # print("ESS at community mg:",ESS_com)
    return community_energy
    #-----------------INDUSTRY MG--------------------------------------------------------------------   
        # load_ind=data.loc[i].at["load_ind"]
        # pv_ind=data.loc[i].at["PV_ind"]
def industry(load_ind, pv_ind, gbp, mbp, msp, gsp, chp_cost):

    if load_ind >= pv_ind:
        rem_load_ind=load_ind - pv_ind   # remaining load at industry MG
    else:
        rem_load_ind = 0
        pv_ind = pv_ind - load_ind

    obj = [chp_cost, mbp, msp]
    lhs = [[1, 0, 0],[-1, 0, 0]]
    rhs = [chp_max, -chp_min]
    lhs_eq = [[1, 1, -1]]
    rhs_eq = [rem_load_ind]

    bnd = [(80, 200),(0, float('inf')), (0, float('inf'))]

    optim = linprog(c=obj, A_ub=lhs, b_ub=rhs, A_eq=lhs_eq, b_eq=rhs_eq, bounds=bnd, method='simplex')
    e=optim.x
    e_chp_ind=e[0]
    e_ind_deficit=e[1]
    e_ind_surplus=e[2]
    # print("Industry CHP, Deficit, Surplus:", e_chp_ind,e_ind_deficit,e_ind_surplus)
    
    # with open('D:\\IIITN\\PhD\\Reinforcement_Learning_implementation\\Industry_Energy_data_v3.csv', 'a') as csvfile:
    #     writer=csv.writer(csvfile, delimiter=',')
    #     writer.writerow(e)
    # print("Industry MG status:", industry_energy)
    
    industry_energy = [e_chp_ind,e_ind_deficit,e_ind_surplus]
    return industry_energy

#-----------------------------SINGLE-DWELLING MG---------------------------------------------------------------
def singleD(load_sd, pv_sd, gbp, mbp, msp, gsp, chp_cost, p_c, p_d, ev_available, EV_sd):
    # load_sd=data.loc[i].at["load_sd"]
    # ev_available=data.loc[i].at["EV_Avail"]
    rem_load_sd = 0
    if pv_sd > 0:
        if load_sd >= pv_sd:
            rem_load_sd = load_sd - pv_sd   # remaining load at sd MG
            pv_sd = 0
        else:
            rem_load_sd = 0
            pv_sd = pv_sd - load_sd
    else:
        rem_load_sd = load_sd

    EV_charge_sd = EV_max - EV_sd # energy needed by EV to fully charge
    # print("load at sd:", load_sd)
    # print("EV at sd:", EV_sd)

    sd_deficit = rem_load_sd
    sd_surplus = 0

    if ev_available == 1:
        if EV_sd < 16:
                if pv_sd <= (EV_charge_sd * 1.10):
                    EV_sd = EV_sd + (pv_sd - (pv_sd * 0.10)) 
                    pv_sd = 0
                else:
                    EV_sd = EV_sd + (EV_charge_sd * 1.10)
                    pv_sd = pv_sd - (EV_charge_sd * 1.10)
                    sd_surplus = pv_sd
        
        else:
            sd_surplus = pv_sd
        EV_charge_sd = EV_max - EV_sd 
    else:
        sd_surplus = pv_sd
    if ev_available == 1:
        if p_c >= 0.5:
            if EV_sd < 16:
                sd_deficit = load_sd + (EV_charge_sd * 1.10)
                EV_sd = EV_sd + EV_charge_sd
        elif p_d >= 0.5:
            if load_sd <= EV_sd:    # if energy at EV is more than load             
                sd_deficit = 0
                EV_sd = EV_sd - (EV_sd * 0.10) - load_sd     # energy at EV is reduced 
                sd_surplus = EV_sd
                EV_sd = 0 
            else:                               # if energy at EV is less than load 
                sd_deficit = load_sd - (EV_sd * 0.90) 
                EV_sd = 0
        # else:
        #     sd_surplus = load_sd
    # else:
    #     sd_surplus = load_sd

    SD_energy = [sd_deficit,sd_surplus, EV_sd]
    # with open('D:\\IIITN\\PhD\\Reinforcement_Learning_implementation\\Single_Dwelling_Energy_data.csv', 'a') as csvfile:
    #     writer=csv.writer(csvfile, delimiter=',')
    #     writer.writerow(SD_energy)
    # print("Deficit at SD:", sd_deficit)
    # print("EV at sd:", EV_sd)
    # print("SD MG status:", SD_energy)
    return SD_energy
#----------------------------CAMPUS MG-------------------------------------------------------------------------
def campus(load_camp, pv_camp, gbp, mbp, msp, gsp, chp_cost, p_c, p_d, ESS_camp):
# Step 1: Calculating energy from chp, energy_deficit and energy_surplus 
       
    # load_camp=data.loc[i].at["load_camp"]
    # pv_camp=data.loc[i].at["PV_camp"]
    rem_load_camp = load_camp - pv_camp      # remaining load
    # print("Remaining load at campus MG:", rem_load_camp)

    obj = [chp_cost, mbp, msp]
    lhs = [[1, 0, 0],[-1, 0, 0]]
    rhs = [chp_max, -chp_min]
    lhs_eq = [[1, 1, -1]]
    rhs_eq = [rem_load_camp]

    bnd = [(80, 200),(0, float('inf')), (0, float('inf'))]

    optim = linprog(c=obj, A_ub=lhs, b_ub=rhs, A_eq=lhs_eq, b_eq=rhs_eq, bounds=bnd, method='simplex')
    e_camp=optim.x
    chp_camp=e_camp[0]
    camp_deficit=e_camp[1]
    camp_surplus=e_camp[2]
    # print("Campus CHP, Deficit, Surplus:", chp_camp,camp_deficit,camp_surplus)


# Step 2: updating deficit/surplus according to the preference of the ESS to charge/discharge

    ESS_charge_camp = ESS_max - ESS_camp  # energy needed by ESS to fully charge
    # print("ESS charge", ESS_charge_camp)
    # print("pc:",p_c,"pd:",p_d)

    if p_c >= 0.5:
        if camp_surplus > 0:    # then surplus will be first used to charge the ESS
            if camp_surplus > (ESS_charge_camp + (ESS_charge_camp * 0.10)):
                ESS_camp = 100
                camp_surplus = camp_surplus - (camp_surplus * 0.10) - ESS_charge_camp
                ESS_charge_camp = 0
            else:
                if ESS_camp == 100:
                    pass
                elif ESS_camp < 100:
                    ESS_camp = ESS_camp + camp_surplus - (camp_surplus * 0.10)
                    ESS_charge_camp = ESS_max - ESS_camp
                    camp_surplus = 0
                    camp_deficit = ESS_charge_camp * 1.10
                    ESS_camp = 100
                    ESS_charge_camp = 0
        elif camp_deficit > 0:
            camp_deficit = camp_deficit + (ESS_charge_camp * 1.10) #deficit at campus MG
            ESS_camp = ESS_camp + ESS_charge_camp
            #print(camp_deficit)
    elif p_d >= 0.5:
        if camp_deficit < ESS_camp and camp_deficit != 0:    # if energy at ESS is more than deficit at campus MG             
            ESS_camp = ESS_camp - (ESS_camp * 0.10) - camp_deficit     # energy at ESS is reduced
            camp_deficit = 0
            camp_surplus = camp_surplus + ESS_camp  # Remaining ESS is sold, due to eagerness to discharge
            ESS_charge_camp = ESS_max - ESS_camp
        elif camp_deficit == 0:   
            camp_surplus = camp_surplus + ESS_camp
            ESS_camp = 0
            ESS_charge_camp = 100
        elif camp_deficit > ESS_camp:                            
            camp_deficit = camp_deficit - (ESS_camp * 0.90) 
            ESS_camp = 0
            ESS_charge_camp = 100

    # print("Deficit at Campus:",camp_deficit)
    # print("Surplus at Campus:",camp_surplus)
    # print("ESS at campus mg:",ESS_camp)
    # print("ESS Charge:", ESS_charge_camp)
    campus_energy = [chp_camp, camp_deficit, camp_surplus, ESS_camp]
    # with open('D:\\IIITN\\PhD\\Reinforcement_Learning_implementation\\Campus_Energy_data.csv', 'a') as csvfile:
    #     writer=csv.writer(csvfile, delimiter=',')
    #     writer.writerow(campus_energy)
    # print("Campus MG status:", campus_energy)
    return campus_energy 


# ESS_EV_status = {"com1":60, "com2":60, "sd1":8, "sd2":8, "sd3":8, "camp":60 }
# ESS_EV_status = {"com1":0, "com2":0, "sd1":0, "sd2":0, "sd3":0, "camp":0 }
# i=22
# ESS_EV_Updated = getEnergyData(ESS_EV_status, i)
# print("ESS/EV Status:",ESS_EV_Updated)


