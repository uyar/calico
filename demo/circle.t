init
    run = rm -f circle.o circle
    blocker = yes

compile
    points = 0
    run = gcc -c circle.c -o circle.o  # timeout: 2
    blocker = yes

link
    points = 0
    run = gcc circle.o -o circle  # timeout: 2
    blocker = yes

case_1
    points = 10
    chroot = /tmp/x
    run = ./circle
    script
        expect = 'Enter radius(.*?):\s+'  # timeout: 1
        send = '1'
        expect = 'Area: 3.14(\d*)\r\n'    # timeout: 1
        expect = EOF                      # timeout: 1
    return = 0

case_0
    points = 20
    run = ./circle
    script
        expect = 'Enter radius(.*?):\s+'  # timeout: 1
        send = '0'
        expect = 'Area: 0.00(\d*)\r\n'    # timeout: 1
        expect = EOF                      # timeout: 1
    return = 0

case_negative
    points = 30
    run = ./circle
    script
        expect = 'Enter radius(.*?):\s+'  # timeout: 1
        send = '-1'
        expect = EOF                      # timeout: 1
    return = 1

cleanup
    run = rm -f circle.o circle
