init
    run = rm -f circle.o circle
    script
        expect = EOF
    blocker = yes

cleanup
    run = rm -f circle.o circle
    script
        expect = EOF

compile
    run = gcc -c circle.c -o circle.o
    script
        expect = EOF  # timeout: 2
    points = 0
    blocker = yes

link
    run = gcc circle.o -o circle
    script
        expect = EOF  # timeout: 2
    points = 0
    blocker = yes

case_1
    chroot = /tmp/x
    run = ./circle
    script
        expect = 'Enter radius(.*?):\s+'  # timeout: 1
        send   = '1'
        expect = 'Area: 3.14(\d*)\r\n'    # timeout: 1
        expect = EOF                      # timeout: 1
    return = 0
    points = 10

case_0
    run = ./circle
    script
        expect = 'Enter radius(.*?):\s+'  # timeout: 1
        send   = '0'
        expect = 'Area: 0.00(\d*)\r\n'    # timeout: 1
        expect = EOF                      # timeout: 1
    return = 0
    points = 20

case_negative
    run = ./circle
    script
        expect = 'Enter radius(.*?):\s+'  # timeout: 1
        send   = '-1'
        expect = EOF                      # timeout: 1
    return = 1
    points = 30
