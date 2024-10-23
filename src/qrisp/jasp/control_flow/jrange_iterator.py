"""
\********************************************************************************
* Copyright (c) 2023 the Qrisp authors
*
* This program and the accompanying materials are made available under the
* terms of the Eclipse Public License 2.0 which is available at
* http://www.eclipse.org/legal/epl-2.0.
*
* This Source Code may also be made available under the following Secondary
* Licenses when the conditions for such availability set forth in the Eclipse
* Public License, v. 2.0 are satisfied: GNU General Public License, version 2
* with the GNU Classpath Exception which is
* available at https://www.gnu.org/software/classpath/license.html.
*
* SPDX-License-Identifier: EPL-2.0 OR GPL-2.0 WITH Classpath-exception-2.0
********************************************************************************/
"""

import jax.numpy as jnp
class JRangeIterator:
    
    def __init__(self, *args):
        
        # Differentiate between the 3 possible cases of input signature
        
        
        if len(args) == 1:
            # In the case of one input argument, this argument is the stop value
            self.start = None
            self.stop = jnp.asarray(args[0], dtype = "int32")
            self.step = jnp.asarray(1, dtype = "int32")
        elif len(args) == 2:
            
            # In the case of two arguments, the first one is the start value
            # and the second one is the stop value.
            
            # To keep the environment flattening simple, we apply a trick such that we
            # only have to keep the flatten the case where the start value is 0
            
            # For that, we set the stop value to stop minus start.
            # This way we can start the counter always at 0.
            
            # We make up for this by increment the iterator results by start
            # to keep the semantics
            self.start = jnp.asarray(args[0], dtype = "int32")
            self.stop = jnp.asarray(args[1] - args[0], dtype = "int32")
            self.step = jnp.asarray(1, dtype = "int32")
        elif len(args) == 3:
            # Three arguments denote the case of a non-trivial step
            self.start = jnp.asarray(args[0], dtype = "int32")
            self.stop = jnp.asarray(args[1] - args[0], dtype = "int32")
            self.step = jnp.asarray(args[2], dtype = "int32")
            
        
    def __iter__(self):
        self.iteration = 0
        return self
    
    def __next__(self):
        # The idea is now to trace two iterations to capture what values get
        # updated after each iteration.
        # We capture the loop semantics using the JIterationEnvironment.
        # The actual jax loop primitive is then compiled in
        # JIterationEnvironment.jcompile
        
        self.iteration += 1
        if self.iteration == 1:
            from qrisp.environments import JIterationEnvironment
            self.iter_env = JIterationEnvironment()
            # Enter the environment
            self.iter_env.__enter__()
            
            # To avoid creating a new tracer, we use the stop value tracer as
            # a loop index. Note that this is just to capture the loop iteration
            # instructions. The actual compilation to a while primitive happens
            # in JIterationEnvironment.jcompile.
            if self.start is None:
                return self.stop
            else:
                # If we have a non-trivial start value, we increment the counter
                # because in the jcompile method we assume that the counter starts
                # at 0.
                return self.stop + self.start
            
        elif self.iteration == 2:
            # Perform the incrementation
            self.stop += self.step
            
            # Exit the old environment and enter the new one.
            self.iter_env.__exit__(None, None, None)
            self.iter_env.__enter__()
            
            # We add the += 0 here such that a new tracer is produced and
            # send through the code of the second iteration.
            # This is important to catch the error that should arise when
            # the user wants to use the loop index as a carry value.
            self.stop += 0
            
            if self.start is None:
                return self.stop
            else:
                return self.stop + self.start
            
        elif self.iteration == 3:
            self.stop += self.step
            self.iter_env.__exit__(None, None, None)
            raise StopIteration

def jrange(*args):
    """
    .. _jrange:
    
    Performs a loop with a dynamic bound.
    
    .. warning::
        
        Similar to the :ref:`ClControlEnvironment <ClControlEnvironment>`, this feature must not have
        external carry values, implying values computed within the loop can't 
        be used outside of the loop. It is however possible to carry on values 
        from the previous iteration.
    
    .. warning::
        
        Each loop iteration must perform exactly the same instructions - the only
        thing that changes is the loop index
    

    Parameters
    ----------
    stop : int
        The loop index to stop at.

    Examples
    --------
    
    We construct a function that encodes an integer into an arbitrarily sized
    :ref:`QuantumVariable`:
        
    ::
        
        from qrisp import QuantumFloat, control, x
        from qrisp.jasp import jrange, make_jaspr
        
        @qache
        def int_encoder(qv, encoding_int):
            
            for i in jrange(qv.size):
                with control(encoding_int & (1<<i)):
                    x(qv[i])

        def test_f(a, b):
            
            qv = QuantumFloat(a)
            
            int_encoder(qv, b+1)
            
            return measure(qv)
            
        jaspr = make_jaspr(test_f)(1,1)
    
    Test the result:
        
    >>> jaspr(5, 8)
    9
    >>> jaspr(5, 9)
    10
    
    We now give examples that violate the above rules (ie. no carries and changing
    iteration behavior).
    
    To create a loop with carry behavior we simply return the final loop index
    
    ::
        
        @qache
        def int_encoder(qv, encoding_int):
            
            for i in jrange(qv.size):
                with control(encoding_int & (1<<i)):
                    x(qv[i])
            return i
            

        def test_f(a, b):
            
            qv = QuantumFloat(a)
            
            int_encoder(qv, b+1)
            
            return measure(qv)
            
        jaspr = make_jaspr(test_f)(1,1)

    >>> jaspr(5, 8)
    Exception: Found jrange with external carry value
    
    To demonstrate the second kind of illegal behavior, we construct a loop
    that behaves differently on the first iteration:
        
    ::
        
        @qache
        def int_encoder(qv, encoding_int):
            
            flag = True
            for i in jrange(qv.size):
                if flag:
                    with control(encoding_int & (1<<i)):
                        x(qv[i])
                else:
                    x(qv[0])
                flag = False
            
        def test_f(a, b):
            
            qv = QuantumFloat(a)
            
            int_encoder(qv, b+1)
            
            return measure(qv)
            
        jaspr = make_jaspr(test_f)(1,1)

    In this script, ``int_encoder`` defines a boolean flag that changes the 
    semantics of the iteration behavior. After the first iteration the flag
    is set to ``False`` such that the alternate behavior is activated.
    
    >>> jaspr(5, 8)
    Exception: Jax semantics changed during jrange iteration

    """
    if all(isinstance(arg, int) for arg in args):
        return range(*args)
    else:
        return JRangeIterator(*args)
    
