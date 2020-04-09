# From-Timed-Automata-to-Timed-Programs
From Timed Automata to Timed Programs

Repository for all of the code used in my final year research project.

The only finished working program is Version 1.
This takes as arguments the CTA notation of the CTA that wish to be implemented.

The CTA notation is as follows: Cta Q = Init q0;q0 z!a(x <= 2) q1;

Where Cta Q = Init q0; defines the name of the automata, Q, and the initial state q0. The identifiers 'Cta' and 'Init' must be in this format.

From that, each transition of the automata is written as: start_state other_automata!/?(time constraint) end_state;
These transitions must be chained together with no spaces after the ;
A transition must have a ! (send) or ? receive.
