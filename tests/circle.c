#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

int main(int argc, char* argv[]) {
    float radius, area;

    printf("Enter radius of circle: ");
    scanf("%f", &radius);

    if (radius < 0) {
        fprintf(stderr, "Negative radius values are not allowed.\n");
        exit(1);
    }

    area = 3.14159 * radius * radius;
    printf("Area: %f\n", area);
    return 0;
}
