#include <bits/stdc++.h>
int main() {
    int input = 0;
    std::cout << "number: " << std::flush;
    std::cin >> input;
    int answer = input * 2;
    std::cout << "answer: " << answer << '\n';
    return answer == 42 ? 0 : 1;
}
