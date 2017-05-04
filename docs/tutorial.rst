Tutorial
========

Let's assume that you want to use clioc for checking a programming assignment.
The assignment is to write a C program that will get the radius of a circle
from the user, calculate its area and print the result. A simple implementation
could be the following code, which is saved in the file :file:`circle.c`:

.. code-block:: c

   #include <stdio.h>

   int main(int argc, char* argv[]) {
       float radius, area;

       printf("Enter radius of circle: ");
       scanf("%f", &radius);
       area = 3.14159 * radius * radius;
       printf("Area: %f\n", area);
       return 0;
   }

Basics
------

To run clioc, you have to write a test specification file. This specification
consists of a sequence of stages where a stage is a test or a setup operation.
For each stage, the basic information that needs to be supplied is what
command to run and what it should return. For example, if we want to check
whether this source code can be compiled, we can write the following
specification:

.. code-block:: yaml

   - compile:
       run: gcc -c circle.c -o circle.o
       return: 0

This file states that there is only one stage. The name of the stage is
"compile". The command is to run the source code through the gcc compiler,
and that the compiler should exit with the status code 0 (success).

Save this specification in the file :file:`circle.yaml` in the same
directory as the :file:`circle.c` file. Note that the run command requires
that the C file has to be in the current directory. Now, if you run
``clioc circle.yaml``, you see the following output::

   compile .................................. PASSED
   Grade: 0 / 0

This stage will create a :file:`circle.o` file in the current directory
as a result of the run command.

If we assign points to a stage, clioc will print those points in its report
if the stage passes. Also note that we can leave out the ``return: 0``
clause because successful completion is the default anyway:

.. code-block:: yaml

   - compile:
       run: gcc -c circle.c -o circle.o
       points: 10

In this case, the output will be::

   compile .................................. 10 / 10
   Grade: 10 / 10

Blockers
--------

As our next step, let's test whether the compiled object file can be linked.
We add a second stage to our specification:

.. code-block:: yaml

   - compile:
       run: gcc -c circle.c -o circle.o
       points: 10

   - link:
       run: gcc circle.o -o circle
       points: 20

The stages are executed in order and the output becomes::

   compile .................................. 10 / 10
   link ..................................... 20 / 20
   Grade: 30 / 30

But since it doesn't make sense to advance to the link stage if the compile
stage was unsuccessful, we can set the compile stage as a blocker:

.. code-block:: yaml

   - compile:
       run: gcc -c circle.c -o circle.o
       blocker: true
       points: 10

   - link:
       run: gcc circle.o -o circle
       points: 20

Delete the semicolon at the end of the first printf statement and run clioc
again::

   compile .................................. 0 / 10
   Grade: 0 / 30
