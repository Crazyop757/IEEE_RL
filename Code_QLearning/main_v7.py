def main():
    import numpy as np
    import random
    import pandas as pd
    from numpy import asarray
    from numpy import savetxt
    import csv
    from scipy.optimize import linprog
    import code_v7 as optim
    import Q_Learning_v7 as q
    import settings1
    import settings2
    settings1.init1()
    ESS_EV_status = {"com1":60, "com2":60, "sd1":8, "sd2":8, "sd3":8, "camp":60 }
    i=0
    mbp_max= 8.5
    mbp_min= 4
    while i<24:
        print("Time Slot:", (i+1))
        analysisData = []
        analysisData.append(i+1)
        # ESS_EV_updated = optim.getEnergyData(ESS_EV_status, i)
        # ESS_EV_status = ESS_EV_updated

        # print("Optimization Done!!!!")
        # Read Energy_data_v7.csv from the same directory
        energy_data_path = os.path.join(script_dir, 'Energy_data_v7.csv')
        Energy_data = pd.read_csv(energy_data_path)
        
        # mg = ['community', 'industry', 'single_dwelling', 'campus'] 
        # # read deficit/surplus files into a DataFrame
        def_com1 = 0.0
        sur_com1 = 0.0
        def_com2 = 0.0
        sur_com2 = 0.0
        def_camp = 0.0
        sur_camp = 0.0
        chp_camp = 0.0
        def_ind1 = 0.0
        sur_ind1 = 0.0
        chp_ind1 = 0.0
        def_ind2 = 0.0
        sur_ind2 = 0.0
        chp_ind2 = 0.0
        def_sd1 = 0.0
        sur_sd1 = 0.0
        def_sd2 = 0.0
        sur_sd2 = 0.0
        def_sd3 = 0.0
        sur_sd3 = 0.0
        
            
        
    # j=0
    # for i in mg:
    #     data[i] = pd.read_csv(filenames[j])
    #     print(data[i])
    #     j = j + 1
    
        # Read input data using relative path
        import os
        script_dir = os.path.dirname(os.path.abspath(__file__))
        input_data_path = os.path.join(script_dir, 'Data_for_Qcode.csv')
        
        # If Data_for_Qcode.csv doesn't exist, try Energy_data_v7.csv
        if not os.path.exists(input_data_path):
            input_data_path = os.path.join(script_dir, 'Energy_data_v7.csv')
        
        input_data = pd.read_csv(input_data_path) 
        gbp=input_data.loc[1].at["GBP"]
        mbp=input_data.loc[1].at["MBP"]
        msp=input_data.loc[1].at["MSP"]
        gsp=input_data.loc[1].at["GSP"]
        chp_cost=input_data.loc[i].at["CHP_Cost"]
        ind1_PV = input_data.loc[i].at["IP1"]
        ind2_PV = input_data.loc[i].at["IP2"]
        com3_PV = input_data.loc[i].at["CP3"]
        com4_PV = input_data.loc[i].at["CP4"]
        sd5_PV = input_data.loc[i].at["SP5"]
        sd6_PV = input_data.loc[i].at["SP6"]
        sd7_PV = input_data.loc[i].at["SP7"]
        camp8_PV = input_data.loc[i].at["CPP8"]
        
        p_c = (mbp_max - mbp)/(mbp_max-mbp_min)  # preference to charge ESS/EV
        p_d = (mbp - mbp_min)/(mbp_max-mbp_min)  # preference to discharge ESS/EV 
        analysisData.append(p_c)
        analysisData.append(p_d)
        def_ind1 = Energy_data.loc[i].at["ind_def1"]
        print("ind1 def:",def_ind1)
        sur_ind1 = Energy_data.loc[i].at["ind_sur1"]
        print("ind1 sur:",sur_ind1)
        chp_ind1 = Energy_data.loc[i].at["ind_chp1"]
        def_ind2 = Energy_data.loc[i].at["ind_def2"]
        print("ind2 def:",def_ind2)
        sur_ind2 = Energy_data.loc[i].at["ind_sur2"]
        chp_ind2 = Energy_data.loc[i].at["ind_chp2"]
        def_com1 = Energy_data.loc[i].at["com_def3"]
        print("com1 def:",def_com1)
        sur_com1 = Energy_data.loc[i].at["com_sur3"]
        def_com2 = Energy_data.loc[i].at["com_def4"]
        print("com2 def:",def_com2)
        sur_com2 = Energy_data.loc[i].at["com_sur4"]
        def_sd1 = Energy_data.loc[i].at["sd_def5"]
        print("sd1 def:",def_sd1)
        sur_sd1 = Energy_data.loc[i].at["sd_sur5"]
        def_sd2 = Energy_data.loc[i].at["sd_def6"]
        print("sd2 def:",def_sd2)
        sur_sd2 = Energy_data.loc[i].at["sd_sur6"]
        def_sd3 = Energy_data.loc[i].at["sd_def7"]
        print("sd3 def:",def_sd3)
        sur_sd3 = Energy_data.loc[i].at["sd_sur7"]
        def_camp = Energy_data.loc[i].at["camp_def8"]
        print("camp def:",def_camp)
        sur_camp = Energy_data.loc[i].at["camp_sur8"]
        chp_camp = Energy_data.loc[i].at["camp_chp8"]
        NoOfBuyers = 0
        NoOfSellers = 0
        MG_stress = 0
        bid = []
        ask = []
        bid.append(i+1)
        ask.append(i+1)
        bid.append("Bid")
        ask.append("Ask")
        total_surplus = sur_camp + sur_com1 + sur_com2 + sur_ind1 + sur_ind2 + sur_sd1 + sur_sd2 + sur_sd3
        total_deficit = def_camp + def_com1 + def_com2 + def_ind1 + def_ind2 + def_sd1 + def_sd2 + def_sd3
        print("Total Deficit:",total_deficit)
        print("Total Surplus:",total_surplus)
        if total_surplus == 0:
            print("SORRY !!! YOU NEED TO BUY ENERGY FROM UTILITY GRID")
        else:
            if total_surplus >= total_deficit:
                print("NO AUCTION !!!")
            else:
                settings2.init2()
                analysisData.append(settings2.MCP)
                stress = total_surplus / total_deficit
                analysisData.append(stress)
                # print("stress=", stress)
                chp_ratio = chp_ind1 / (chp_ind1 + ind1_PV)
                analysisData.append(chp_ratio)
                # print("ind1 chp_ratio", chp_ratio)
                index = q.q_learning('IND',chp_ind1, def_ind1, sur_ind1, gbp, gsp, mbp, msp, chp_cost, chp_ratio, total_surplus, total_deficit)
                alpha1 = settings1.Y1[index]
                alpha2 = settings1.Y2[index]
                # print("alpha1:",alpha1)
                # print("alpha2:",alpha2)
                analysisData.append(alpha1)
                analysisData.append(alpha2)
                if def_ind1 > 0:
                    MG_stress = def_ind1 / total_deficit
                    bidprice1 = gbp - (alpha1 * chp_ratio + alpha2 * (1-stress)) - (1 - MG_stress)
                    bid.append(bidprice1)
                    ask.append(0)
                    # print("Bid price of buyer MG1:", bidprice1)
                    analysisData.append(bidprice1)
                    analysisData.append(0)
                    NoOfBuyers = NoOfBuyers + 1
                elif sur_ind1 > 0:
                    MG_stress = sur_ind1 / total_surplus
                    askprice1 = msp + (alpha1 * chp_ratio) + (alpha2 * (1-stress)) + (1-MG_stress)
                    ask.append(askprice1)
                    bid.append(0)
                    analysisData.append(0)
                    analysisData.append(askprice1)
                    # print("Bid price of seller MG1:", askprice1)
                    NoOfSellers = NoOfSellers + 1
                else:
                    print("MG1 not participating in energy trading")
                    bid.append(0)
                    ask.append(0)
                    analysisData.append(0)
                    analysisData.append(0)

                chp_ratio = chp_ind2 / (chp_ind2 + ind2_PV)
                # print("ind2 chp_ratio", chp_ratio)
                analysisData.append(chp_ratio)
                index = q.q_learning('IND', chp_ind2, def_ind2, sur_ind2, gbp, gsp, mbp, msp, chp_cost, chp_ratio, total_surplus, total_deficit)
                alpha1 = settings1.Y1[index]
                alpha2 = settings1.Y2[index]
                # print("alpha1:",alpha1)
                # print("alpha2:",alpha2)
                analysisData.append(alpha1)
                analysisData.append(alpha2)
                if def_ind2 > 0:
                    MG_stress = def_ind2 / total_deficit
                    bidprice2 = gbp - (alpha1 * chp_ratio + alpha2 * (1-stress)) - (1 - MG_stress)
                    # print("Bid price of buyer MG2:", bidprice2)
                    NoOfBuyers = NoOfBuyers + 1
                    bid.append(bidprice2)
                    ask.append(0)
                    analysisData.append(bidprice2)
                    analysisData.append(0)
                elif sur_ind2 > 0:
                    MG_stress = sur_ind2 / total_surplus
                    askprice2 = msp + (alpha1 * chp_ratio) + (alpha2 * (1 - stress)) + (1 - MG_stress)
                    # print("Bid price of seller MG2:", askprice2)
                    NoOfSellers = NoOfSellers + 1
                    ask.append(askprice2)
                    bid.append(0)
                    analysisData.append(0)
                    analysisData.append(askprice2)

                else:
                    print("MG2 not participating in energy trading")
                    bid.append(0)
                    ask.append(0)
                    analysisData.append(0)
                    analysisData.append(0)
                index = q.q_learning('COM', 0, def_com1, sur_com1, gbp, gsp, mbp, msp, 0, 0, total_surplus, total_deficit)
                alpha1 = settings1.Y1[index]
                alpha2 = settings1.Y2[index]
                # print("alpha1:",alpha1)
                # print("alpha2:",alpha2)
                analysisData.append(alpha1)
                analysisData.append(alpha2)
                if def_com1 > 0:
                    MG_stress = def_com1 / total_deficit
                    bidprice3 = gbp - ((alpha1 * p_c + alpha2 * (1-stress) )) - (1 - MG_stress)
                    # print("Bid price of buyer MG3:", bidprice3) 
                    NoOfBuyers = NoOfBuyers + 1
                    bid.append(bidprice3)
                    ask.append(0)
                    analysisData.append(bidprice3)
                    analysisData.append(0)
                elif sur_com1 > 0:
                    MG_stress = sur_com1 / total_surplus
                    askprice3 = msp + (alpha1 * p_d + alpha2 * (1 - stress)) + (1 - MG_stress)
                    # print("Bid price of seller MG3:", askprice3) 
                    NoOfSellers = NoOfSellers + 1
                    ask.append(askprice3)
                    bid.append(0)
                    analysisData.append(0)
                    analysisData.append(askprice3)
                else:
                    print("MG3 not participating in energy trading")
                    bid.append(0)
                    ask.append(0)
                    analysisData.append(0)
                    analysisData.append(0)
                index = q.q_learning('COM', 0, def_com2, sur_com2, gbp, gsp, mbp, msp, 0, 0, total_surplus, total_deficit)
                alpha1 = settings1.Y1[index]
                alpha2 = settings1.Y2[index]
                # print("alpha1:",alpha1)
                # print("alpha2:",alpha2)
                analysisData.append(alpha1)
                analysisData.append(alpha2)
                if def_com2 > 0:
                    MG_stress = def_com2 / total_deficit
                    bidprice4 = gbp - ((alpha1 * p_c + alpha2 * (1-stress) ) ) - (1 - MG_stress)
                    # print("Bid price of buyer MG4:", bidprice4)
                    NoOfBuyers = NoOfBuyers + 1
                    bid.append(bidprice4)
                    ask.append(0)
                    analysisData.append(bidprice4)
                    analysisData.append(0)
                elif sur_com2 > 0:
                    MG_stress = sur_com2 / total_surplus
                    askprice4 = msp + (alpha1 * p_d + alpha2 * (1 - stress)) + (1 - MG_stress)
                    # print("Bid price of seller MG4:", askprice4)
                    NoOfSellers = NoOfSellers + 1
                    ask.append(askprice4)
                    bid.append(0)
                    analysisData.append(0)
                    analysisData.append(askprice4)
                else:
                    print("MG4 not participating in energy trading")
                    bid.append(0)
                    ask.append(0)
                    analysisData.append(0)
                    analysisData.append(0)
                index = q.q_learning('SD', 0, def_sd1, sur_sd1, gbp, gsp, mbp, msp, 0, 0, total_surplus, total_deficit)
                alpha1 = settings1.Y1[index]
                alpha2 = settings1.Y2[index]
                # print("alpha1:",alpha1)
                # print("alpha2:",alpha2)
                analysisData.append(alpha1)
                analysisData.append(alpha2)
                if def_sd1 > 0:
                    MG_stress = def_sd1 / total_deficit
                    bidprice5 = gbp - (alpha1 * p_c + alpha2 * (1-stress)) - (1 - MG_stress)
                    # print("Bid price of buyer MG5:", bidprice5) 
                    NoOfBuyers = NoOfBuyers + 1
                    bid.append(bidprice5)
                    ask.append(0)
                    analysisData.append(bidprice5)
                    analysisData.append(0)
                elif sur_sd1 > 0:
                    MG_stress = sur_sd1 / total_surplus
                    askprice5 = msp + (alpha1 * p_d + alpha2 * (1 - stress)) + (1 - MG_stress)
                    # print("Bid price of seller MG5:", askprice5)
                    NoOfSellers = NoOfSellers + 1 
                    ask.append(askprice5)
                    bid.append(0)
                    analysisData.append(0)
                    analysisData.append(askprice5)
                else:
                    print("MG5 not participating in energy trading")
                    bid.append(0)
                    ask.append(0)
                    analysisData.append(0)
                    analysisData.append(0)
                index = q.q_learning('SD', 0, def_sd2, sur_sd2, gbp, gsp, mbp, msp, 0, 0, total_surplus, total_deficit)
                alpha1 = settings1.Y1[index]
                alpha2 = settings1.Y2[index]
                # print("alpha1:",alpha1)
                # print("alpha2:",alpha2)
                analysisData.append(alpha1)
                analysisData.append(alpha2)
                if def_sd2 > 0:
                    MG_stress = def_sd2 / total_deficit
                    bidprice6 = gbp - (alpha1 * p_c + alpha2 * (1-stress)) - (1 - MG_stress)
                    # print("Bid price of buyer MG6:", bidprice6)
                    NoOfBuyers = NoOfBuyers + 1
                    bid.append(bidprice6)
                    ask.append(0)
                    analysisData.append(bidprice6)
                    analysisData.append(0)
                elif sur_sd2 > 0:
                    MG_stress = sur_sd2 / total_surplus
                    askprice6 = msp + (alpha1 * p_d + alpha2 * (1 - stress)) + (1 - MG_stress)
                    # print("Bid price of seller MG6:", askprice6)
                    NoOfSellers = NoOfSellers + 1
                    ask.append(askprice6)
                    bid.append(0)
                    analysisData.append(0)
                    analysisData.append(askprice6)
                else:
                    print("MG6 not participating in energy trading")
                    bid.append(0)
                    ask.append(0)
                    analysisData.append(0)
                    analysisData.append(0)
                index = q.q_learning('SD', 0, def_sd3, sur_sd3, gbp, gsp, mbp, msp, 0, 0,total_surplus, total_deficit)
                alpha1 = settings1.Y1[index]
                alpha2 = settings1.Y2[index]
                # print("alpha1:",alpha1)
                # print("alpha2:",alpha2)
                analysisData.append(alpha1)
                analysisData.append(alpha2)
                if def_sd3 > 0:
                    MG_stress = def_sd3 / total_deficit
                    bidprice7 = gbp - (alpha1 * p_c + alpha2 * (1-stress)) - (1 - MG_stress)
                    # print("Bid price of buyer MG7:", bidprice7)
                    NoOfBuyers = NoOfBuyers + 1
                    bid.append(bidprice7)
                    ask.append(0)
                    analysisData.append(bidprice7)
                    analysisData.append(0)
                elif sur_sd3 > 0:
                    MG_stress = sur_sd3 / total_surplus
                    askprice7 = msp + (alpha1 * p_d + alpha2 * (1 - stress)) + (1 - MG_stress)
                    # print("Bid price of seller MG7:", askprice7)
                    NoOfSellers = NoOfSellers + 1
                    ask.append(askprice7)
                    bid.append(0)
                    analysisData.append(0)
                    analysisData.append(askprice7)
                else:
                    print("MG7 not participating in energy trading")
                    bid.append(0)
                    ask.append(0)
                    analysisData.append(0)
                    analysisData.append(0)
                chp_ratio = chp_camp / (chp_camp + camp8_PV)
                analysisData.append(chp_ratio)
                # print("CAMP chp_ratio", chp_ratio)
                index = q.q_learning('CAMP', chp_camp, def_camp, sur_camp, gbp, gsp, mbp, msp, chp_cost, chp_ratio,total_surplus, total_deficit)
                alpha1 = settings1.Y1[index]
                alpha2 = settings1.Y2[index]
                # print("alpha1:",alpha1)
                # print("alpha2:",alpha2)
                analysisData.append(alpha1)
                analysisData.append(alpha2)
                if def_camp > 0:
                    MG_stress = def_camp / total_deficit
                    bidprice8 = gbp - ((alpha1 * (p_c + (1-stress))) + alpha2 * chp_ratio) - (1 - MG_stress)
                    # print("Bid price of buyer MG8:", bidprice8)
                    NoOfBuyers = NoOfBuyers + 1
                    bid.append(bidprice8)
                    ask.append(0)
                    analysisData.append(bidprice8)
                    analysisData.append(0)
                elif sur_camp > 0:
                    MG_stress = sur_camp / total_surplus
                    askprice8 = msp + (alpha1 * (p_d + (1 - stress)) + alpha2 * chp_ratio) + (1 - MG_stress)
                    # print("Bid price of seller MG8:", askprice8)
                    NoOfSellers = NoOfSellers + 1
                    ask.append(askprice8)
                    bid.append(0)
                    analysisData.append(0)
                    analysisData.append(askprice8)
                else:
                    print("MG8 not participating in energy trading")
                    bid.append(0)
                    ask.append(0)
                    analysisData.append(0)
                    analysisData.append(0)
                
                # Write output files to the same directory
                bidask_path = os.path.join(script_dir, 'bidAsk_v7.csv')
                analysis_path = os.path.join(script_dir, 'AnalysisOfImplementation_v7.csv')
                
                with open(bidask_path, 'a', newline='') as csvfile:
                    writer=csv.writer(csvfile, delimiter=',')
                    writer.writerow(bid)
                    writer.writerow(ask)
                with open(analysis_path, 'a', newline='') as csvfile:
                    writer=csv.writer(csvfile, delimiter=',')
                    writer.writerow(analysisData)
            print("Total No. of Buyers:", NoOfBuyers)
            print("Total No. of Sellers:", NoOfSellers)       
        i = i + 1
        
         

       
        

if __name__ == "__main__":
    main()
