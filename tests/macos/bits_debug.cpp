#include <bits/stdc++.h>
using namespace std;
int main() {
    vector<int> values{3, 1, 2};
    string label = "panda";
    sort(values.begin(), values.end());
    int total = accumulate(values.begin(), values.end(), 0);
    cout << label << ": " << total << '\n';
    return total == 6 ? 0 : 1;
}
