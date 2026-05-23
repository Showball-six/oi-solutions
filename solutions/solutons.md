## [ABC198_D Send More Money](https://atcoder.jp/contests/abc198/tasks/abc198_d?lang=en)

**思路**：

首先，如果出现的字符种类超过 $10$ 一定是无解的。把出现的字符按照字典序编号，最多只有 $10$ 种字符，我们通过全排列，枚举每个字母所代表的数字，进而求出每个字符串表示的数字，验证数字是否合法即可。

**参考代码**：

```CPP
#include<bits/stdc++.h>

using namespace std;

using i64=long long;

void Showball(){
    string s1,s2,s3;
    cin>>s1>>s2>>s3;


    set<char> st;
    for(auto c:s1) st.insert(c);
    for(auto c:s2) st.insert(c);
    for(auto c:s3) st.insert(c);

    if(st.size()>10) return cout<<"UNSOLVABLE",void();

    map<char,int> mp;
    int rk=0;
    for(auto c:st) mp[c]=rk++;

    vector<int> p(10);
    iota(p.begin(),p.end(),0);

    i64 n1=0,n2=0,n3=0;
    auto check=[&](vector<int> p){
        for(auto c:s1) n1=n1*10+p[mp[c]];
        for(auto c:s2) n2=n2*10+p[mp[c]];
        for(auto c:s3) n3=n3*10+p[mp[c]];

        if(!p[mp[s1[0]]]||!p[mp[s2[0]]]||!p[mp[s3[0]]]) return false;
        return n1+n2==n3;    
    };

    do{
        n1=0,n2=0,n3=0;
        if(check(p)) return cout<<n1<<"\n"<<n2<<"\n"<<n3,void();
    }while(next_permutation(p.begin(),p.end()));

    cout<<"UNSOLVABLE";
}
int main(){
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int t=1;
    //cin>>t;

    while(t--){
      Showball();
    }

    return 0;
}
```
