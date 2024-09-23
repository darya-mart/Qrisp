# imports 
from qrisp.qaoa.problems.maxSatInfrastr import maxSatclCostfct, clausesdecoder
from qrisp.qiro import QIROProblem, qiro_init_function, qiro_RXMixer, create_maxSat_replacement_routine, create_maxSat_cost_operator_reduced
from qrisp import QuantumVariable
import matplotlib.pyplot as plt
import networkx as nx

# define the problem according to maxSat encoding
problem = [8 , [[1,2,-3],[1,4,-6], [4,5,6],[1,3,-4],[2,4,5],[1,3,5],[-2,-3,6], [1,7,8], [3,-7,-8], [3,4,8],[4,5,8], [1,2,7]]]
decodedClauses = clausesdecoder( problem)

qarg = QuantumVariable(problem[0])

# set simulator shots
mes_kwargs = {
    #below should be 5k
    "shots" : 5000
    }


# assign cost_function and maxclique_instance, normal QAOA
testCostFun = maxSatclCostfct(problem)

# assign the correct new update functions for qiro from above imports
qiro_instance = QIROProblem(problem = problem,  
                            replacement_routine = create_maxSat_replacement_routine, 
                            cost_operator = create_maxSat_cost_operator_reduced,
                            mixer = qiro_RXMixer,
                            cl_cost_function = maxSatclCostfct,
                            init_function = qiro_init_function
                            )


# We run the qiro instance and get the results!
res_qiro = qiro_instance.run_qiro(qarg=qarg, depth = 3, n_recursions = 2, 
                                  #mes_kwargs = mes_kwargs
                                  )


print("QIRO 5 best results")
maxfive = sorted(res_qiro, key=res_qiro.get, reverse=True)[:5]
for key, val in res_qiro.items():  
    if key in maxfive:
        
        print(key)
        print(testCostFun({key:1}))

# or compare it with the networkx result of the max_clique algorithm...
# or a write brute force solution, this is up to you

# and finally, we print the final clauses!
final_clauses = qiro_instance.problem
print(final_clauses)
