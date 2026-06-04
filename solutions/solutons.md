# [CF1324E Sleeping Schedule](https://atcoder.jp/contests/abc198/tasks/abc198_d?lang=en)

**思路**：

考虑DP，每次决策只与上一次醒来的时间和这一次睡眠开始时间有关，又因为每次都是睡一天，所以只需要关注睡眠开始时间。

**状态设计**：

$f_{i,j}$ 表示考虑前 $i$ 天，且第 $i$ 天在 $j$ 时开始睡眠的最多好觉次数。

**状态转移**：

考虑是在上次醒来后 $a_i$ 小时还是 $a_i-1$ 小时。

$f_{i,j}=\max(f_{i-1,(j-a_i+h)\%h},f_{i-1,(j-a_i+1+h)\%h})+[l\le j\le r]$。

**初始化**：

所有值初始化为负无穷，$f_{0,0}=0$。

**答案**：

$\max_{i \in [0,h)} f_{n,i}$

**参考代码**：

```CPP
#include<bits/stdc++.h>

using namespace std;

using i64=long long;

const int N=2010;

int f[N][N];
int a[N];
void Showball(){
    int n,h,l,r;
    cin>>n>>h>>l>>r;
    for(int i=1;i<=n;i++) cin>>a[i];

    auto calc=[&](int x){
        return l<=x&&x<=r;
    };

    memset(f,-0x3f,sizeof f);
    f[0][0]=0;

    for(int i=1;i<=n;i++){
        for(int j=0;j<h;j++){
            f[i][j]=max(f[i-1][(j-a[i]+h)%h],f[i-1][(j-a[i]+1+h)%h])+calc(j);
        }
    }

    int ans=0;
    for(int i=0;i<h;i++) ans=max(ans,f[n][i]);

    cout<<ans<<"\n";
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
