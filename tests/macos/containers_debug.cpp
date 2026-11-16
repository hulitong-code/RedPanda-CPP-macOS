#include <bits/stdc++.h>
int main() {
    std::vector<int> numbers{10, 20, 12};
    std::vector<int> empty;
    std::vector<std::string> words{"red", "panda"};
    std::vector<bool> flags{true, false, true};
    std::vector<std::vector<int>> matrix{{1, 2}, {3, 4}};
    std::list<int> linked{7, 8};
    std::map<int, int> mapping{{1, 10}, {2, 20}};
    std::set<int> unique{4, 5, 6};
    int answer = std::accumulate(numbers.begin(), numbers.end(), 0);
    volatile int stage = 0;
    stage = 1; // CHECK_INITIAL
    numbers.push_back(7);
    stage = 2; // CHECK_GROWN
    numbers.clear();
    stage = 3; // CHECK_EMPTY
    return answer == 42 && stage == 3 ? 0 : 1;
}
