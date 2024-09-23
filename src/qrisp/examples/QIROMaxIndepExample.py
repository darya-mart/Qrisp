# imports 
from qrisp.qaoa.problems.maxIndepSetInfrastr import maxIndepSetclCostfct, maxIndepSetCostOp
from qrisp.qiro import QIROProblem, qiro_init_function, qiro_RXMixer, create_maxIndep_replacement_routine, create_maxIndep_cost_operator_reduced
from qrisp import QuantumVariable
import networkx as nx


# First we define a graph via the number of nodes and the QuantumVariable arguments
num_nodes = 13
G = nx.erdos_renyi_graph(num_nodes, 0.4, seed =  107)
qarg = QuantumVariable(G.number_of_nodes())

# set simulator shots
mes_kwargs = {
    #below should be 5k
    "shots" : 5000
    }

# assign the correct new update functions for qiro from above imports
qiro_instance = QIROProblem(G, 
                            replacement_routine=create_maxIndep_replacement_routine, 
                            cost_operator= create_maxIndep_cost_operator_reduced,
                            mixer= qiro_RXMixer,
                            cl_cost_function= maxIndepSetclCostfct,
                            init_function= qiro_init_function
                            )

# We run the qiro instance and get the results!
res_qiro = qiro_instance.run_qiro(qarg=qarg, depth = 3, n_recursions = 2, mes_kwargs = mes_kwargs)
# and also the final graph, that has been adjusted
final_Graph = qiro_instance.problem

# Lets see what the 5 best results are
print("QIRO 5 best results")
maxfive = sorted(res_qiro, key=res_qiro.get, reverse=True)[:5]
costFunc = maxIndepSetclCostfct(G)
for key, val in res_qiro.items():  
    if key in maxfive:
        
        print(key)
        print(costFunc({key:1}))
        

# and compare them with the networkx result of the max_clique algorithm, where we might just see a better result than the heuristical NX algorithm!
print("Networkx solution")
print(nx.approximation.maximum_independent_set(G))
