#include <stdio.h>

int main(int argc, char* argv[]) {
    float radius, area;

    printf("Enter radius of circle: ");
    scanf("%f", &radius);
    area = 3.14159 * radius * radius;
    printf("Area: %f\n", area);
    return 0;
}
